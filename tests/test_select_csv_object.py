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


class TestSelectCsvObject(OssTestCase):
    def test_select_csv_object_empty_string(self):
        key = "city_sample_data.csv"
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv')
        self.bucket.head_csv_object(key)
        input_format = {'FileHeaderInfo' : 'Use'}
        result = self.bucket.select_csv_object(key, "select Year, StateAbbr, CityName, PopulationCount from ossobject where CityName != ''", None, None, input_format)
        content = b''
        for chunk in result:
            content += chunk
        #print(content)
        self.assertEqual(result.status, 206)
        self.assertGreater(len(content), 0)

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
        key = "city_sample_data.csv"
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv')
        self.bucket.head_csv_object(key)
        input_format = {'FileHeaderInfo' : 'Use'}
        result = self.bucket.select_csv_object(key, "select Year, StateAbbr, CityName, Short_Question_Text from ossobject where Measure like '%blood pressure%Years'", None, None, input_format)
        content = b''
        for chunk in result:
            content += chunk
        #print(content)
        self.assertEqual(result.status, 206)
        self.assertGreater(len(content), 0)

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
        key = "city_sample_data.csv"
        self.bucket.put_object_from_file(key, 'tests/sample_data.csv')
        self.bucket.head_csv_object(key)
        input_format = {'FileHeaderInfo' : 'Use'}
        result = self.bucket.select_csv_object(key, "select Year,StateAbbr, CityName, Short_Question_Text from ossobject'", (0, 50), None, input_format)
        content = b''
        for chunk in result:
            content += chunk
        #print(content)
        self.assertEqual(result.status, 206)
        self.assertGreater(len(content), 0)

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

if __name__ == '__main__':
    unittest.main()
