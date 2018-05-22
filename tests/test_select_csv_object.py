# -*- coding: utf-8 -*-

import requests
import filecmp
import calendar
import csv
import re

from oss2.exceptions import (ClientError, RequestError, NoSuchBucket,
                             NotFound, NoSuchKey, Conflict, PositionNotEqualToLength, ObjectNotAppendable, SelectOperationFailed)
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
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv')

        result = self.bucket.create_select_object_meta(key)
        file_size = result.content_length

        input_format = {'CsvHeaderInfo' : 'Use'}
        if (line_range is not None):
            input_format['LineRange'] = line_range

        result = self.bucket.select_object(key, sql, self.select_call_back, input_format)
        content = b''
        for chunk in result:
            content += chunk
        
        testCase.assertEqual(result.status, 206)
        testCase.assertGreater(len(content), 0)

        if line_range is None:
            testCase.assertEqual(self.scannedSize, file_size)

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
        select_data = b''

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
            select_data = ("{:.4f}".format(avg) + "," + str(max) + "," + "{:.1f}".format(sum) + '\n').encode('utf-8');
            
            self.assertEqual(select_data, content)

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
        content = helper.test_select_csv_object(self, "select Year,StateAbbr, CityName, Short_Question_Text from ossobject where data_value > 14.8 and data_value_unit = '%' or Measure like '%18 Years' and Category = 'Unhealthy Behaviors' or high_confidence_limit > 70.0 ")
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
                        line += '\n'.encode('utf-8')
                        select_data += line
        
            self.assertEqual(select_data, content)

    def test_select_csv_object_invalid_sql(self):
        helper = SelectCsvObjectTestHelper(self.bucket) 

        helper.test_select_csv_object_invalid_request(self, "select * from ossobject where avg(cast(year as int)) > 2016")
        helper.test_select_csv_object_invalid_request(self, "")
        helper.test_select_csv_object_invalid_request(self, "select year || CityName from ossobject")
        helper.test_select_csv_object_invalid_request(self, "select * from ossobject group by CityName")
        helper.test_select_csv_object_invalid_request(self, "select * from ossobject oss join s3object s3 on oss.CityName = s3.CityName")

    def test_select_csv_object_with_invalid_data(self):
        key = "city_sample_data.csv"
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

            self.assertTrue(len(content) > 0)

if __name__ == '__main__':
    unittest.main()
