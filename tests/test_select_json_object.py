# -*- coding: utf-8 -*-
import requests
import filecmp
import calendar
import json
import re
import sys

from oss2.exceptions import (ClientError, RequestError, NoSuchBucket,
                             NotFound, NoSuchKey, Conflict, PositionNotEqualToLength, ObjectNotAppendable, SelectOperationFailed,SelectOperationClientError)
from .common import *

if sys.version_info[0] > 2:
    # py3k
    def _open(file):
        return open(file, 'r', encoding='utf-8')
else:
    # py2
    def _open(file):
        return open(file, 'r')

def now():
    return int(calendar.timegm(time.gmtime()))

def  select_call_back(consumed_bytes, total_bytes =  None):
	print('Consumed Bytes:'  +  str(consumed_bytes) +  '\n')

class SelectJsonObjectTestHelper(object):
    def __init__(self, bucket):
        self.bucket = bucket
        self.scannedSize = 0

    def select_call_back(self, consumed_bytes, total_bytes = None):
        self.scannedSize = consumed_bytes

    def test_select_json_object(self, testCase, sql, input_format):
        is_gzip = False
        if input_format['Json_Type'] == 'DOCUMENT':
            if 'CompressionType' in input_format and input_format['CompressionType'] == 'GZIP':
                key = "sample_json.json.gz"
                local_file = 'tests/sample_json.json.gz'
                is_gzip = True
            else:
                key = "sample_json.json"
                local_file = 'tests/sample_json.json'
        else:
            key = 'sample_json_lines.json'
            local_file = 'tests/sample_json_lines.json'

        result = self.bucket.put_object_from_file(key, local_file)
        
        #set OutputrecordDelimiter with ',' to make json load the result correctly
        input_format['OutputRecordDelimiter'] = ','

        if (input_format['Json_Type'] == 'LINES'):
            result = self.bucket.create_select_object_meta(key, {'Json_Type':'LINES'})

        result = self.bucket.head_object(key)
        file_size = result.content_length

        result = self.bucket.select_object(key, sql, self.select_call_back, input_format)
        content = b''
        for chunk in result:
            content += chunk
        
        testCase.assertEqual(result.status, 206, result.request_id)
        testCase.assertTrue(len(content) > 0)

        if 'SplitRange' not in input_format and 'LineRange' not in input_format and is_gzip is False:
            testCase.assertEqual(self.scannedSize, file_size)

        return content

    def test_select_json_object_invalid_request(self, testCase, sql, input_format):
        if input_format['Json_Type'] == 'DOCUMENT':
            key = "sample_json.json"
            local_file = 'tests/sample_json.json'
        else:
            key = 'sample_json_lines.json'
            local_file = 'tests/sample_json_lines.json'

        result = self.bucket.put_object_from_file(key, local_file)
        if (input_format['Json_Type'] == 'LINES'):
            result = self.bucket.create_select_object_meta(key, input_format)

        file_size = result.content_length

        try:
            result = self.bucket.select_object(key, sql, None, input_format)
            testCase.assertEqual(result.status, 400)
        except oss2.exceptions.ServerError as e:
            testCase.assertEqual(e.status, 400)

class TestSelectJsonObject(OssTestCase):
    
    def test_select_json_document_democrat_senators(self):
        print("test_select_json_document_democrat_senators")
        helper = SelectJsonObjectTestHelper(self.bucket)
        input_format = {'Json_Type':'DOCUMENT', 'CompressionType':'None'}
        content = helper.test_select_json_object(self, "select * from ossobject.objects[*] where party = 'Democrat'", input_format)
        
        content = content[0:len(content)-1] #remove the last ','
        content = b"[" + content + b"]"  #make json parser happy
        result = json.loads(content.decode('utf-8'))

        result_index = 0
        with _open('tests/sample_json.json') as json_file:
            data = json.load(json_file)
            for row in data['objects']:
                if row['party'] == 'Democrat':
                    self.maxDiff = None
                    self.assertEqual(result[result_index], row, str(result_index))
                    result_index += 1
       
    def test_select_json_lines_democrat_senators(self):
        print("test_select_json_lines_democrat_senators")
        helper = SelectJsonObjectTestHelper(self.bucket)
        input_format = {'Json_Type':'LINES'}
        content = helper.test_select_json_object(self, "select * from ossobject where party = 'Democrat'", input_format)
        
        content = content[0:len(content)-1] #remove the last ','
        content = b"[" + content + b"]"  #make json parser happy
        result = json.loads(content.decode('utf-8'))

        result2 = []
        with _open('tests/sample_json.json') as json_file:
            data = json.load(json_file)
            for row in data['objects']:
                if row['party'] == 'Democrat':
                    result2.append(row)
            
            self.assertEqual(result, result2)
    
    def test_select_json_object_like(self):
        print("test_select_json_object_like")
        helper = SelectJsonObjectTestHelper(self.bucket)
        select_params = {'Json_Type':'LINES'}
        content = helper.test_select_json_object(self, "select person.firstname, person.lastname from ossobject where person.birthday like '1959%'", select_params)
        content = content[0:len(content)-1] #remove the last ','
        content = b"[" + content + b"]"  #make json parser happy
        result = json.loads(content.decode('utf-8'))

        index = 0
        with _open('tests/sample_json.json') as json_file:
            data = json.load(json_file)
            for row in data['objects']:
                select_row = {}
                if row['person']['birthday'].startswith('1959'): 
                        select_row['firstname'] = row['person']['firstname']
                        select_row['lastname'] = row['person']['lastname']
                        self.assertEqual(result[index], select_row)
                        index += 1

    def test_select_gzip_json_object_like(self):
        print("test_select_gzip_json_object_like")
        helper = SelectJsonObjectTestHelper(self.bucket)
        select_params = {'Json_Type':'DOCUMENT', 'CompressionType':'GZIP'}
        content = helper.test_select_json_object(self, "select person.firstname, person.lastname from ossobject.objects[*]  where person.birthday like '1959%'", select_params)
        content = content[0:len(content)-1] #remove the last ','
        content = b"[" + content + b"]"  #make json parser happy
        result = json.loads(content.decode('utf-8'))

        index = 0
        with _open('tests/sample_json.json') as json_file:
            data = json.load(json_file)
            for row in data['objects']:
                select_row = {}
                if row['person']['birthday'].startswith('1959'): 
                        select_row['firstname'] = row['person']['firstname']
                        select_row['lastname'] = row['person']['lastname']
                        self.assertEqual(result[index], select_row)
                        index += 1

    def test_select_json_object_with_output_raw(self):
        key = "test_select_json_object_with_output_raw"
        content = "{\"key\":\"abc\"}"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'OutputRawData':'true', 'Json_Type':'DOCUMENT'}
        result = self.bucket.select_object(key, "select key from ossobject", None, select_params)
        content = b''
        for chunk in result:
            content += chunk
        
        self.assertEqual(content, '{\"key\":\"abc\"}\n'.encode('utf-8'))

    def test_select_json_object_with_crc(self):
        key = "test_select_json_object_with_crc"
        content = "{\"key\":\"abc\"}\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'EnablePayloadCrc':True, 'Json_Type':'DOCUMENT'}
        result = self.bucket.select_object(key, "select * from ossobject where true", None, select_params)
        content = result.read()
        
        self.assertEqual(content, '{\"key\":\"abc\"}\n'.encode('utf-8'))

    def test_select_json_object_with_skip_partial_data(self):
        key = "test_select_json_object_with_skip_partial_data"
        content = "{\"key\":\"abc\"},{\"key2\":\"def\"}"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'SkipPartialDataRecord':'false', 'Json_Type':'LINES', 'MaxSkippedRecordsAllowed':100}
        result = self.bucket.select_object(key, "select key from ossobject", None, select_params)
        content = b''
        try:
            for chunk in result:
                content += chunk
        except oss2.exceptions.ServerError:
            print("expected error occurs")
        
        self.assertEqual(content, '{\"key\":\"abc\"}\n{}\n'.encode('utf-8'))
    
    def test_select_json_object_with_invalid_parameter(self):
        key = "test_select_json_object_with_invalid_parameter"
        content = "{\"key\":\"abc\"}\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'EnablePayloadCrc':True, 'Json_Type':'DOCUMENT', 'unsupported_param':True}

        try:
            self.bucket.select_object(key, "select * from ossobject where true", None, select_params)
            self.assertFalse(True, 'expected error did not occur')
        except SelectOperationClientError:
            print("expected error occurs")

    def test_create_json_meta_with_invalid_parameter(self):
        key = "test_create_json_meta_with_invalid_parameter"
        content = "{\"key\":\"abc\"}\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'EnablePayloadCrc':True, 'Json_Type':'DOCUMENT'}

        try:
            self.bucket.create_select_object_meta(key,select_params)
            self.assertFalse(True, 'expected error did not occur')
        except SelectOperationClientError:
            print("expected error occurs")

    def test_create_json_object_meta_invalid_request2(self):
        key = "sample_json.json"
        self.bucket.put_object_from_file(key, 'tests/sample_json.json')
        format = {'Json_Type':'invalid', 'CompressionType':'None', 'OverwriteifExists':'True'}
        try:
            self.bucket.create_select_object_meta(key, format)
            self.assertFalse(True, "expected error did not occur")
        except SelectOperationClientError:
            print("expected error occured")

    def test_select_json_object_line_range(self):
        print("test_select_json_object_line_range")
        helper = SelectJsonObjectTestHelper(self.bucket) 

        select_params = {'LineRange' : (10, 50), 'Json_Type':'LINES'}
        content = helper.test_select_json_object(self, "select person.firstname as aaa as firstname, person.lastname, extra from ossobject'", select_params)
        content = content[0:len(content)-1] #remove the last ','
        content = b"[" + content + b"]"  #make json parser happy
        result = json.loads(content.decode('utf-8'))

        result_index = 0
        result2 = []
        with _open('tests/sample_json.json') as json_file:
            data = json.load(json_file)
            index = 0
            for row in data['objects']:
                select_row = {}
                if index >= 10 and index < 50:
                    select_row['firstname'] = row['person']['firstname']
                    select_row['lastname'] = row['person']['lastname']
                    select_row['extra'] = row['extra']
                    self.assertEqual(result[result_index], select_row)
                    result_index += 1
                elif index >= 50:
                    break
                index += 1
        
    def test_select_json_object_int_aggregation(self):
        print("test_select_json_object_int_aggregation")
        helper = SelectJsonObjectTestHelper(self.bucket) 
        select_params = {'Json_Type': 'DOCUMENT'}
        content = helper.test_select_json_object(self, "select avg(cast(person.cspanid as int)), max(cast(person.cspanid as int)), min(cast(person.cspanid as int)) from ossobject.objects[*] where person.cspanid = 1011723", select_params)
        self.assertEqual(content, b'{\"_1\":1011723,\"_2\":1011723,\"_3\":1011723},')
    
    def test_select_json_object_float_aggregation(self):
        print("test_select_json_object_float_aggregation")
        helper = SelectJsonObjectTestHelper(self.bucket) 
        select_params = {'Json_Type': 'DOCUMENT'}
        content = helper.test_select_json_object(self, "select avg(cast(person.cspanid as double)), max(cast(person.cspanid as double)), min(cast(person.cspanid as double)) from ossobject.objects[*]", select_params)
        print(content)
        
    def test_select_json_object_concat(self):
        print("test_select_json_object_concat")
        helper = SelectJsonObjectTestHelper(self.bucket) 
        select_params = {'Json_Type': 'DOCUMENT'}
        content = helper.test_select_json_object(self, "select person from ossobject.objects[*] where (person.firstname || person.lastname) = 'JohnKennedy'", select_params)
        content = content[0:len(content)-1] #remove the last ','
        content = b"[" + content + b"]"  #make json parser happy
        result = json.loads(content.decode('utf-8'))

        result_index = 0
        with _open('tests/sample_json.json') as json_file:
            data = json.load(json_file)
            for row in data['objects']:
                if row['person']['firstname'] == 'John' and row['person']['lastname'] == 'Kennedy' :
                    self.assertEqual(result[result_index]['person'], row['person'])
                    result_index += 1
       
    def test_select_json_object_complicate_condition(self):
        print("test_select_json_object_complicate_condition")
        helper = SelectJsonObjectTestHelper(self.bucket) 
        select_params = {'Json_Type' : 'LINES'}
        content = helper.test_select_json_object(self, "select person.firstname, person.lastname, congress_numbers from ossobject where startdate > '2017-01-01' and senator_rank = 'junior' or state = 'CA' and party = 'Republican' ", select_params)
        content = content[0:len(content)-1] #remove the last ','
        content = b"[" + content + b"]"  #make json parser happy
        result = json.loads(content.decode('utf-8'))

        result_index = 0
        with _open('tests/sample_json.json') as json_file:
            data = json.load(json_file)
            for row in data['objects']:
                if row['startdate'] > '2017-01-01' and row['senator_rank'] == 'junior' or row['state'] == 'CA' and row['party'] == 'Republican':
                    self.assertEqual(result[result_index]['firstname'], row['person']['firstname'])
                    self.assertEqual(result[result_index]['lastname'], row['person']['lastname'])
                    self.assertEqual(result[result_index]['congress_numbers'], row['congress_numbers'])
                    result_index += 1
    
    def test_select_json_object_invalid_sql(self):
        print("test_select_json_object_invalid_sql")
        helper = SelectJsonObjectTestHelper(self.bucket) 

        select_params = {'Json_Type':'LINES'}
        helper.test_select_json_object_invalid_request(self, "select * from ossobject where avg(cast(person.birthday as int)) > 2016", select_params)
        helper.test_select_json_object_invalid_request(self, "", select_params)
        helper.test_select_json_object_invalid_request(self, "select person.lastname || person.firstname from ossobject", select_params)
        helper.test_select_json_object_invalid_request(self, "select * from ossobject group by person.firstname", select_params)
        helper.test_select_json_object_invalid_request(self, "select * from ossobject order by _1", select_params)
        helper.test_select_json_object_invalid_request(self, "select * from ossobject oss join s3object s3 on oss.CityName = s3.CityName", select_params)
    
    def test_select_json_object_with_invalid_data(self):
        print("test_select_json_object_with_invalid_data")
        key = "invalid_json.json"
        self.bucket.put_object_from_file(key, 'tests/invalid_sample_data.csv')
        input_format = {'Json_Type' : 'DOCUMENT'}

        try:
            result = self.bucket.select_object(key, "select _1 from ossobject.objects[*]", None, input_format)
            self.assertFalse(True, "expect to raise exception")
        except oss2.exceptions.ServerError:
            print("Got the exception. Ok.")
    
    def test_select_json_object_none_range(self):
        print("test_select_json_object_none_range")
        key = "sample_json.json"
        self.bucket.put_object_from_file(key, 'tests/sample_json.json')
        select_params = {'Json_Type':'LINES'}
        self.bucket.create_select_object_meta(key, select_params)

        input_formats = [
                            { 'SplitRange' : (None, None) },
                            { 'LineRange' : (None, None) },
                            {'SplitRange' : None },
                            {'LineRange' : None }
                        ]

        for input_format in input_formats:
            input_format['Json_Type'] = 'LINES'
            result = self.bucket.select_object(key, "select * from ossobject", None, input_format)
            content = b''
            for chunk in result:
                content += chunk

            self.assertTrue(len(content) > 0)

    def test_select_json_object_parse_num_as_string(self):
        key = "test_select_json_object_parse_num_as_string"
        self.bucket.put_object(key, b"{\"a\":123456789.123456789}")
        result = self.bucket.select_object(key, "select a from ossobject where cast(a as decimal) = 123456789.1234567890", None, select_params={'ParseJsonNumberAsString': 'true', 'Json_Type':'DOCUMENT'})
        content = b''
        for chunk in result:
            content += chunk
        self.assertEqual(content, b"{\"a\":123456789.123456789}\n")
    
if __name__ == '__main__':
    unittest.main()
