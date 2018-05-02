# -*- coding: utf-8 -*-
import requests
import filecmp
import calendar
import csv
import re

from oss2.exceptions import (ClientError, RequestError, NoSuchBucket,
                             NotFound, NoSuchKey, Conflict, PositionNotEqualToLength, ObjectNotAppendable)
from common import *


def now():
    return int(calendar.timegm(time.gmtime()))

class TestSelectCsvObjectHelper(object):
    def __init__(self, bucket):
        self.bucket = bucket

    def test_select_csv_object(self, testCase, sql, line_range = None):
        key = "city_sample_data.csv"
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv')
        result = self.bucket.head_csv_object(key)
        file_size = result.content_length
        input_format = {'FileHeaderInfo' : 'Use'}
        result = self.bucket.select_csv_object(key, sql, line_range, None, input_format)
        content = b''
        for chunk in result:
            content += chunk
        #print(content)
        testCase.assertEqual(result.status, 206)
        testCase.assertGreater(len(content), 0)
        testCase.assertEqual(result.total_bytes_to_scan, file_size)
        return content

    def test_select_csv_object_invalid_request(self, testCase, sql, line_range = None):
        key = "city_sample_data.csv"
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv')
        result = self.bucket.head_csv_object(key)
        file_size = result.content_length
        input_format = {'FileHeaderInfo' : 'Use'}
        try:
            result = self.bucket.select_csv_object(key, sql, line_range, None, input_format)
            testCase.assertEqual(result.status, 400)
        except oss2.exceptions.ServerError as e:
            testCase.assertEqual(e.status, 400)

class TestSelectCsvObject(OssTestCase):
    def test_select_csv_object_not_empty_city(self):
        helper = TestSelectCsvObjectHelper(self.bucket)
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
        helper = TestSelectCsvObjectHelper(self.bucket) 
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
        helper = TestSelectCsvObjectHelper(self.bucket) 
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
        helper = TestSelectCsvObjectHelper(self.bucket) 
        content = helper.test_select_csv_object(self, "select avg(cast(year as int)), max(cast(year as int)), min(cast(year as int)) from ossobject where year = 2015")
        self.assertEqual(content, b'2015,2015,2015\n')
    
    def test_select_csv_object_float_aggregation(self):
        helper = TestSelectCsvObjectHelper(self.bucket) 
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
        helper = TestSelectCsvObjectHelper(self.bucket) 
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
        helper = TestSelectCsvObjectHelper(self.bucket) 
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
        helper = TestSelectCsvObjectHelper(self.bucket) 
        helper.test_select_csv_object_invalid_request(self, "select * from ossobject where avg(cast(year as int)) > 2016")
        helper.test_select_csv_object_invalid_request(self, "")
        helper.test_select_csv_object_invalid_request(self, "select year || CityName from ossobject")
        helper.test_select_csv_object_invalid_request(self, "select * from ossobject group by CityName")
        helper.test_select_csv_object_invalid_request(self, "select * from ossobject oss join s3object s3 on oss.CityName = s3.CityName")

if __name__ == '__main__':
    unittest.main()
