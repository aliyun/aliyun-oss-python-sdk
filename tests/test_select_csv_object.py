# -*- coding: utf-8 -*-
import requests
import filecmp
import calendar
import csv
import re

from oss2.exceptions import (ClientError, RequestError, NoSuchBucket,
                             NotFound, NoSuchKey, Conflict, PositionNotEqualToLength, ObjectNotAppendable, SelectOperationFailed, SelectOperationClientError)
from common import *

def now():
    return int(calendar.timegm(time.gmtime()))

class SelectCsvObjectTestHelper(object):
    def __init__(self, bucket):
        self.bucket = bucket
        self.scannedSize = 0

    def select_call_back(self, consumed_bytes, total_bytes = None):
        self.scannedSize = consumed_bytes

    def test_select_csv_object(self, testCase, sql, line_range = None):
        key = "city_sample_data.csv"
        result = self.bucket.put_object_from_file(key, 'tests/sample_data.csv')
        result = self.bucket.create_select_object_meta(key)
        result = self.bucket.head_object(key)
        file_size = result.content_length
        input_format = {'CsvHeaderInfo' : 'Use'}
        if (line_range is not None):
            input_format['LineRange'] = line_range

        result = self.bucket.select_object(key, sql, self.select_call_back, input_format)
        content = b''
        for chunk in result:
            content += chunk
        
        print(result.request_id)
        testCase.assertEqual(result.status, 206, result.request_id)
        testCase.assertTrue(len(content) > 0)

        if line_range is None:
            testCase.assertEqual(self.scannedSize, file_size)

        self.bucket.delete_object(key)
        return content

    def test_select_csv_object_invalid_request(self, testCase, sql, line_range = None):
        key = "city_sample_data.csv"
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv')

        result = self.bucket.create_select_object_meta(key)
        file_size = result.content_length

        input_format = {'CsvHeaderInfo' : 'Use'}
        if (line_range is not None):
            input_format['Range'] = line_range

        try:
            result = self.bucket.select_object(key, sql, None, input_format)
            testCase.assertEqual(result.status, 400)
        except oss2.exceptions.ServerError as e:
            testCase.assertEqual(e.status, 400)
        
        self.bucket.delete_object(key)

class TestSelectCsvObject(OssTestCase):
    def test_select_csv_object_not_empty_city(self):
        helper = SelectCsvObjectTestHelper(self.bucket)
        content = helper.test_select_csv_object(self, "select Year, StateAbbr, CityName, PopulationCount from ossobject where CityName != ''")
       
        with open('tests/sample_data.csv') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            select_data = b''
            for row in spamreader:
                line = b''
                if row['CityName'] != '':
                        line += row['Year'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['StateAbbr'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['CityName'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['PopulationCount'].encode('utf-8')
                        line += '\n'.encode('utf-8')
                        select_data += line
            
            self.assertEqual(select_data, content)
    
    def test_select_csv_object_like(self):
        helper = SelectCsvObjectTestHelper(self.bucket) 
        content = helper.test_select_csv_object(self, "select Year, StateAbbr, CityName, Short_Question_Text from ossobject where Measure like '%blood pressure%Years'")

        with open('tests/sample_data.csv') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            select_data = b''
            matcher = re.compile('^.*blood pressure.*Years$')

            for row in spamreader:
                line = b''
                if matcher.match(row['Measure']):
                        line += row['Year'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['StateAbbr'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['CityName'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['Short_Question_Text'].encode('utf-8')
                        line += '\n'.encode('utf-8')
                        select_data += line
            
            self.assertEqual(select_data, content)
        
    def test_select_csv_object_line_range(self):
        helper = SelectCsvObjectTestHelper(self.bucket) 
        content = helper.test_select_csv_object(self, "select Year,StateAbbr, CityName, Short_Question_Text from ossobject'", (0, 50))

        with open('tests/sample_data.csv') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            select_data = b''
            count = 0
            for row in spamreader:
                if count < 50:
                    line = b''
                    line += row['Year'].encode('utf-8')
                    line += ','.encode('utf-8')
                    line += row['StateAbbr'].encode('utf-8')
                    line += ','.encode('utf-8')
                    line += row['CityName'].encode('utf-8')
                    line += ','.encode('utf-8')
                    line += row['Short_Question_Text'].encode('utf-8')
                    line += '\n'.encode('utf-8')
                    select_data += line 
                else:
                    break
                count += 1
            
            self.assertEqual(select_data, content)
    
    def test_select_csv_object_int_aggregation(self):
        helper = SelectCsvObjectTestHelper(self.bucket) 
        content = helper.test_select_csv_object(self, "select avg(cast(year as int)), max(cast(year as int)), min(cast(year as int)) from ossobject where year = 2015")
        self.assertEqual(content, b'2015,2015,2015\n')
    
    def test_select_csv_object_float_aggregation(self):
        helper = SelectCsvObjectTestHelper(self.bucket) 
        content = helper.test_select_csv_object(self, "select avg(cast(data_value as double)), max(cast(data_value as double)), sum(cast(data_value as double)) from ossobject")
        # select_data = b''

        with open('tests/sample_data.csv') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            sum = 0.0
            avg = 0.0
            line_count = 0
            max = 0.0
            for row in spamreader:
                if len(row['Data_Value']) > 0 :
                    val = float(row['Data_Value'])
                    if val > max:
                        max = val
                
                    sum += val
                    line_count += 1
            
            avg = sum/line_count
            # select_data = ("{0:.4f}".format(avg) + "," + str(max) + "," + "{0:.1f}".format(sum) + '\n').encode('utf-8')
            aggre_results = content.split(b',')
            avg_result = float(aggre_results[0])
            max_result = float(aggre_results[1])
            sum_result = float(aggre_results[2])
            self.assertEqual(avg, avg_result)
            self.assertEqual(max, max_result)
            self.assertEqual(sum, sum_result)

    def test_select_csv_object_concat(self):
        helper = SelectCsvObjectTestHelper(self.bucket) 
        content = helper.test_select_csv_object(self, "select Year,StateAbbr, CityName, Short_Question_Text from ossobject where (data_value || data_value_unit) = '14.8%'")
        select_data = b''

        with open('tests/sample_data.csv') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in spamreader:
                line = b''
                if row['Data_Value_Unit'] == '%' and row['Data_Value'] == '14.8' :
                        line += row['Year'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['StateAbbr'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['CityName'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['Short_Question_Text'].encode('utf-8')
                        line += '\n'.encode('utf-8')
                        select_data += line
        
            self.assertEqual(select_data, content)

    def test_select_csv_object_complicate_condition(self):
        helper = SelectCsvObjectTestHelper(self.bucket) 
        content = helper.test_select_csv_object(self, "select Year,StateAbbr, CityName, Short_Question_Text, data_value, data_value_unit, category, high_confidence_limit from ossobject where data_value > 14.8 and data_value_unit = '%' or Measure like '%18 Years' and Category = 'Unhealthy Behaviors' or high_confidence_limit > 70.0 ")
        select_data = b''

        matcher = re.compile('^.*18 Years$')
        with open('tests/sample_data.csv') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in spamreader:
                line = b''
                if len(row['Data_Value']) > 0 and float(row['Data_Value']) > 14.8 and row['Data_Value_Unit'] == '%' or matcher.match(row['Measure']) and row['Category'] == 'Unhealthy Behaviors' or len(row['High_Confidence_Limit']) > 0 and float(row['High_Confidence_Limit']) > 70.0 :
                        line += row['Year'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['StateAbbr'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['CityName'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['Short_Question_Text'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['Data_Value'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['Data_Value_Unit'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['Category'].encode('utf-8')
                        line += ','.encode('utf-8')
                        line += row['High_Confidence_Limit'].encode('utf-8')
                        line += '\n'.encode('utf-8')
                        select_data += line
            self.assertEqual(select_data, content)
    
    def test_select_csv_object_invalid_sql(self):
        helper = SelectCsvObjectTestHelper(self.bucket) 

        helper.test_select_csv_object_invalid_request(self, "select * from ossobject where avg(cast(year as int)) > 2016")
        helper.test_select_csv_object_invalid_request(self, "")
        helper.test_select_csv_object_invalid_request(self, "select year || CityName from ossobject")
        helper.test_select_csv_object_invalid_request(self, "select * from ossobject group by CityName")
        helper.test_select_csv_object_invalid_request(self, "select * from ossobject order by _1")
        helper.test_select_csv_object_invalid_request(self, "select * from ossobject oss join s3object s3 on oss.CityName = s3.CityName")

    def test_select_csv_object_with_invalid_data(self):
        key = "invalid_city_sample_data.csv"
        self.bucket.put_object_from_file(key, 'tests/invalid_sample_data.csv')
        input_format = {'CsvHeaderInfo' : 'Use'}
        result = self.bucket.select_object(key, "select _1 from ossobject", None, input_format)
        content = b''

        try:
            for chunk in result:
                content += chunk
            self.assertFalse(True, "expect to raise exception")
        except SelectOperationFailed:
            print("Got the exception. Ok.")
        self.bucket.delete_object(key)

    def test_select_csv_object_into_file(self):
        key = "city_sample_data.csv"
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv')
        input_format = {'CsvHeaderInfo' : 'None',
                        'CommentCharacter' : '#',
                        'RecordDelimiter' : '\n',
                        'FieldDelimiter' : ',',
                        'QuoteCharacter' : '"',
                        'SplitRange' : (0, None)
                        }
        output_file = 'tests/sample_data_out.csv'

        head_csv_params = {  
                            'RecordDelimiter' : '\n',
                            'FieldDelimiter' : ',',
                            'QuoteCharacter' : '"',
                            'OverwriteIfExists': True}

        self.bucket.create_select_object_meta(key, head_csv_params)

        self.bucket.select_object_to_file(key, output_file, "select * from ossobject", None, input_format)
        f1 = open('tests/sample_data.csv')
        content1 = f1.read()
        f1.close()

        f2 = open(output_file)
        content2 = f2.read()
        f2.close()

        os.remove(output_file)
        self.assertEqual(content1, content2)
        self.bucket.delete_object(key)

    def test_select_gzip_csv_object_into_file(self):
        key = "city_sample_data.csv.gz"
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv.gz')
        input_format = {'CsvHeaderInfo' : 'None',
                        'CommentCharacter' : '#',
                        'RecordDelimiter' : '\n',
                        'FieldDelimiter' : ',',
                        'QuoteCharacter' : '"',
                        'CompressionType' : 'GZIP'
                        }
        output_file = 'tests/sample_data_out.csv'

        self.bucket.select_object_to_file(key, output_file, "select * from ossobject", None, input_format)
        f1 = open('tests/sample_data.csv')
        content1 = f1.read()
        f1.close()

        f2 = open(output_file)
        content2 = f2.read()
        f2.close()

        os.remove(output_file)
        self.assertEqual(content1, content2)
        self.bucket.delete_object(key)

    def test_select_csv_object_none_range(self):
        key = "city_sample_data.csv"
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv')
        self.bucket.create_select_object_meta(key)

        input_formats = [
                            { 'SplitRange' : (None, None) },
                            { 'LineRange' : (None, None) },
                            {'SplitRange' : None },
                            {'LineRange' : None }
                        ]

        for input_format in input_formats:
            result = self.bucket.select_object(key, "select * from ossobject", None, input_format)
            content = b''
            for chunk in result:
                content += chunk

            if len(content) <= 0 :
                self.bucket.delete_object(key)
            self.assertTrue(len(content) > 0)
        self.bucket.delete_object(key)
    
    def test_select_csv_object_with_output_delimiters(self):
        key = "test_select_csv_object_with_output_delimiters"
        content = "abc,def\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'OutputRecordDelimiter':'\r\n', 'OutputFieldDelimiter':'|'}
        result = self.bucket.select_object(key, "select _1, _2 from ossobject", None, select_params)
        content = b''
        for chunk in result:
            content += chunk
        
        self.assertEqual(content, 'abc|def\r\n'.encode('utf-8'))
        self.bucket.delete_object(key)

    def test_select_csv_object_with_crc(self):
        key = "test_select_csv_object_with_crc"
        content = "abc,def\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'EnablePayloadCrc':'true'}
        result = self.bucket.select_object(key, "select * from ossobject", None, select_params)
        content = b''
        for chunk in result:
            content += chunk
        
        self.assertEqual(content, 'abc,def\n'.encode('utf-8'))
        self.bucket.delete_object(key)
    
    def test_select_csv_object_with_skip_partial_data(self):
        key = "test_select_csv_object_with_skip_partial_data"
        content = "abc,def\nefg\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'SkipPartialDataRecord':'true'}
        result = self.bucket.select_object(key, "select _1, _2 from ossobject", None, select_params)
        content = b''
        try:
            for chunk in result:
                content += chunk
        except SelectOperationFailed:
            print("expected error occurs")
        
        self.assertEqual(content, 'abc,def\n'.encode('utf-8'))
        self.bucket.delete_object(key)

    def test_select_csv_object_with_output_raw(self):
        key = "test_select_csv_object_with_output_raw"
        content = "abc,def\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'OutputRawData':'true'}
        result = self.bucket.select_object(key, "select _1 from ossobject", None, select_params)
        content = b''
        for chunk in result:
            content += chunk
        
        self.assertEqual(content, 'abc\n'.encode('utf-8'))
        self.bucket.delete_object(key)
    
    def test_select_csv_object_with_keep_columns(self):
        key = "test_select_csv_object_with_keep_columns"
        content = "abc,def\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'KeepAllColumns':'true'}
        result = self.bucket.select_object(key, "select _1 from ossobject", None, select_params)
        content = b''
        for chunk in result:
            content += chunk
        
        self.assertEqual(content, 'abc,\n'.encode('utf-8'))
        self.bucket.delete_object(key)
    
    def test_select_csv_object_with_output_header(self):
        key = "test_select_csv_object_with_output_header"
        content = "name,job\nabc,def\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'OutputHeader':'true', 'CsvHeaderInfo':'Use'}
        result = self.bucket.select_object(key, "select name from ossobject", None, select_params)
        content = b''
        for chunk in result:
            content += chunk
        
        self.assertEqual(content, 'name\nabc\n'.encode('utf-8'))
        self.bucket.delete_object(key)
    
    def test_select_csv_object_with_invalid_parameters(self):
        key = "test_select_csv_object_with_invalid_parameters"
        content = "name,job\nabc,def\n"
        self.bucket.put_object(key, content.encode('utf_8'))
        select_params = {'OutputHeader123':'true', 'CsvHeaderInfo':'Use'}
        try:
            result = self.bucket.select_object(key, "select name from ossobject", None, select_params)
            content = b''
            for chunk in result:
                content += chunk
            
            self.bucket.delete_object(key)
            self.assertEqual(content, 'abc\n'.encode('utf-8'))
        except SelectOperationClientError:
            self.bucket.delete_object(key)
            print("expected error")
    
if __name__ == '__main__':
    unittest.main()
