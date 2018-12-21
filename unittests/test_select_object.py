# -*- coding: utf-8 -*-

import os

import oss2
import sys
import struct

from functools import partial
from oss2 import to_string
from mock import patch
from oss2 import xml_utils
from oss2 import utils
from oss2.exceptions import SelectOperationClientError
from oss2.exceptions import InconsistentError
from oss2.exceptions import SelectOperationFailed
from oss2.exceptions import ClientError

from unittests.common import *



class ContiniousFrame(object):
    _CONTINIOUS_FRAME_TYPE=8388612
    _DATA_FRAME_TYPE = 8388609
    _END_FRAME_TYPE = 8388613
    _META_END_FRAME_TYPE = 8388614
    _JSON_META_END_FRAME_TYPE = 8388615
    _HEAD_CHECK_SUM = 0
    def __init__(self, offset, payload = None, payload_length = 8, frame_type = 8388612):
         self.offset = offset
         self.payload_length = payload_length
         self.frame_type =  frame_type | 0x1000000
         if (payload is None):
            self.payload = struct.pack('!Q', offset)
         else:
            self.payload = struct.pack('!Q', offset) + payload
    
    def header_str(self):
         return struct.pack('!III', self.frame_type, self.payload_length, ContiniousFrame._HEAD_CHECK_SUM)

    def to_bytes(self):
         header = self.header_str()
         crc32 = utils.Crc32()
         crc32.update(self.payload)
         checksum_calc = struct.pack('!I', crc32.crc)
         return header + self.payload + checksum_calc
    
class DataFrame(ContiniousFrame):
    
     def __init__(self, offset, data):
         super(DataFrame, self).__init__(offset, data, len(data) + 8, ContiniousFrame._DATA_FRAME_TYPE)
         self.data = data
    
class EndFrame(ContiniousFrame):
    
    def __init__(self, offset, scanned_size, status, error = b''):
        super(EndFrame, self).__init__(offset, struct.pack('!QI', scanned_size, status) + error, len(error) + 20, ContiniousFrame._END_FRAME_TYPE)
        self.scanned_size = scanned_size
        self.status = status
        self.error = error

class EndMetaFrame(ContiniousFrame):
    def __init__(self, offset, scannedsize, status, splits, rows, cols, error):
        super(EndMetaFrame, self).__init__(offset, struct.pack('!QIIQI', scannedsize, status, splits, rows, cols) + error, 36 + len(error), ContiniousFrame._META_END_FRAME_TYPE)
        self.scanned_size = scannedsize
        self.status = status
        self.splits = splits
        self.rows = rows
        self.cols = cols

class EndJsonMetaFrame(ContiniousFrame):
    def __init__(self, offset, scannedsize, status, splits, rows, error):
        super(EndJsonMetaFrame, self).__init__(offset, struct.pack('!QIIQ', scannedsize, status, splits, rows) + error, 32 + len(error), ContiniousFrame._JSON_META_END_FRAME_TYPE)
        self.scanned_size = scannedsize
        self.status = status
        self.splits = splits
        self.rows = rows

def generate_data(resp_content, output_raw, error = b'', status = 206, simulate_bad_crc = False):
    if output_raw:
        return to_string(resp_content)
    else:
        continiousFrame = ContiniousFrame(100)
        dataFrame = DataFrame(len(resp_content), resp_content)
        frameStr = dataFrame.to_bytes()
        if (simulate_bad_crc):
            frameStr = frameStr[0:len(frameStr)-2] + b'X'  # 'X' is the character that does not exist in the content

        endFrame = EndFrame(len(resp_content), len(resp_content), status, error)

        return continiousFrame.to_bytes() + frameStr + endFrame.to_bytes()

def generate_head_data(scanned_size, splits, rows, cols = None, error = b'', status = 200):
    continiousFrame = ContiniousFrame(100)
    if cols is not None:
        endFrame = EndMetaFrame(scanned_size, scanned_size, status, splits, rows, cols, error)
    else:
        endFrame = EndJsonMetaFrame(scanned_size, scanned_size, status, splits, rows, error)
    return continiousFrame.to_bytes() + endFrame.to_bytes()

def make_select_object(sql, resp_content, req_params = None, output_raw = False, simulate_bad_frame = False, simulate_bad_crc = False, status = 206, error = b''):
    req_body = xml_utils.to_select_object(sql, req_params)
    process_type = 'csv'
    if (req_params is not None and 'Json_Type' in req_params):
        process_type = 'json'

    request_text = '''POST /select-test.txt?x-oss-process={2}/select HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: {0}
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
authorization: OSS ZCDmm7TPZKHtx77j:W6whAowN4aImQ0dfbMHyFfD0t1g=
Accept: */*

{1}'''.format(len(req_body), to_string(req_body), process_type)
    resp_body = generate_data(resp_content, output_raw, simulate_bad_crc=simulate_bad_crc, status=status, error = error)
    if (simulate_bad_frame):
        resp_body = resp_content

    response_text = '''HTTP/1.1 206 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Length: {0}
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"
x-oss-select-output-raw:{1}

'''.format(len(resp_body), str(output_raw).lower())

    if (sys.version_info[0] == 3 and type(resp_body).__name__ == 'str'):
        resp_body = str.encode(resp_body)

    return request_text, str.encode(response_text) + resp_body

def make_head_object(req_params, scanned_size, splits, rows, cols, status, error):
    req_body = xml_utils.to_get_select_object_meta(req_params)
    process_type = 'csv'
    if (req_params is not None and 'Json_Type' in req_params):
        process_type = 'json'

    request_text = '''POST /select-test.txt?x-oss-process={2}/meta HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: {0}
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
authorization: OSS ZCDmm7TPZKHtx77j:W6whAowN4aImQ0dfbMHyFfD0t1g=
Accept: */*


{1}'''.format(len(req_body), to_string(req_body), process_type)

    resp_body = generate_head_data(scanned_size, splits, rows, cols, error, status)
    response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Length: {0}
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"

'''.format(len(resp_body))

    return request_text, str.encode(response_text) + resp_body

def callback(offset, length):
    print(offset)
    print(length)

class SelectCaseHelper(object):
    def create_meta(self, tester, do_request, head_params = None, error = b'', status = 200):
        scanned_size = 10000
        splits = 100
        rows = 1000
        cols = 20

        if (head_params is not None and 'Json_Type' in head_params):
            req, resp = make_head_object(head_params, scanned_size, splits, rows, None, status, error)
        else:
            req, resp = make_head_object(head_params, scanned_size, splits, rows, cols, status, error)

        req_info = mock_response(do_request, resp)

        result = bucket().create_select_object_meta('select-test.txt', head_params)

        tester.assertRequest(req_info, req)
        tester.assertEqual(result.rows, rows)
        tester.assertEqual(result.splits, splits)
        tester.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
    
    def select(self, tester, do_request, callback = None, select_params = None, byte_range = None):
        sql = "select * from ossobject limit 10"
        resp_content = b'a,b,c,d,e,f,,n,g,l,o,p'
        if select_params is not None and 'Json_Type' in select_params:
            if select_params['Json_Type'] == 'DOCUMENT':
                resp_content = b'{contacts:[{\"firstName\":\"John\", \"lastName\":\"Smith\"}]}'
            else:
                resp_content = b'{\"firstName\":\"John\", \"lastName\":\"Smith\"}' 

        output_raw = False

        if (select_params is not None and 'OutputRawData' in select_params and select_params['OutputRawData']):
            output_raw = True
        req, resp = make_select_object(sql, resp_content, select_params, output_raw)

        req_info = mock_response(do_request, resp)

        result = bucket().select_object('select-test.txt', sql, callback, select_params, byte_range)

        tester.assertEqual(result.status, 206)
        tester.assertRequest(req_info, req)
        
        if (result.status//100 == 2):
            content = result.read()
            tester.assertEqual(content, resp_content)

class TestSelectObject(OssTestCase):
    
    @patch('oss2.Session.do_request')
    def test_create_csv_meta_with_none_params(self, do_request):
        head_params = None
        helper = SelectCaseHelper()
        helper.create_meta(self, do_request, head_params)
    
    @patch('oss2.Session.do_request')
    def test_create_csv_meta_with_params(self, do_request):
        head_params = {'RecordDelimiter':'\n', 'FieldDelimiter':',', 'QuoteCharacter':'"', 'CompressionType':'None', 'OverwriteIfExists':'True'}
        helper = SelectCaseHelper()
        helper.create_meta(self, do_request, head_params)

    @patch('oss2.Session.do_request')
    def test_select_csv(self, do_request):
        sql = "select * from ossobject limit 10"
        resp_content = b'a,b,c,d,e,f,,n,g,l,o,p'
        req, resp = make_select_object(sql, resp_content)

        req_info = mock_response(do_request, resp)

        result = bucket().select_object('select-test.txt', sql, None)

        self.assertEqual(result.status, 206)
        self.assertRequest(req_info, req)
        
        content = b''
        for chunk in result:
            content += chunk
        
        self.assertEqual(content, resp_content)
    
    @patch('oss2.Session.do_request')
    def test_select_csv_next(self, do_request):
        sql = "select * from ossobject limit 10"
        resp_content = b'a,b,c,d,e,f,,n,g,l,o,p'
        req, resp = make_select_object(sql, resp_content)

        req_info = mock_response(do_request, resp)

        result = bucket().select_object('select-test.txt', sql, None)

        self.assertEqual(result.status, 206)
        self.assertRequest(req_info, req)
        
        content = b''
        result_iter = iter(result)
        content = next(result_iter)
        
        self.assertEqual(content, resp_content)

    @patch('oss2.Session.do_request')
    def test_select_csv_read(self, do_request):
        helper = SelectCaseHelper()
        helper.select(self, do_request)
    
    @patch('oss2.Session.do_request')
    def test_select_csv_read_with_params(self, do_request):
        select_params = {'CsvHeaderInfo':'Use', 'CommentCharacter':'#', 'RecordDelimiter':'\n', 'OutputRecordDelimiter':'\n',
                         'FieldDelimiter':',', 'OutputFieldDelimiter':',', 'QuoteCharacter':'"', 'SplitRange':[0,10], 'CompressionType':'GZIP',
                         'KeepAllColumns':True, 'OutputRawData':False, 'EnablePayloadCrc':True, 'OutputHeader':False, 'SkipPartialDataRecord':False}
        helper = SelectCaseHelper()
        helper.select(self, do_request, None, select_params)
    
    @patch('oss2.Session.do_request')
    def test_select_csv_read_output_raw(self, do_request):
        select_params = {'OutputRawData':True}
        helper = SelectCaseHelper()
        helper.select(self, do_request, None, select_params)

    @patch('oss2.Session.do_request')
    def test_select_csv_with_bad_response(self, do_request):
        sql = "select * from ossobject limit 10"
        resp_content = b'a,b,c,d,e,f,,n,g,l,o,p'
       
        req, resp = make_select_object(sql, resp_content, simulate_bad_frame=True)

        req_info = mock_response(do_request, resp)

        try:
            result = bucket().select_object('select-test.txt', sql)
            result.read()
            self.assertFalse(True, "expect SelectOperationClientError")
        except SelectOperationClientError:
            pass

    @patch('oss2.Session.do_request')
    def test_select_csv_with_bad_crc(self, do_request):
        sql = "select * from ossobject limit 10"
        resp_content = b'a,b,c,d,e,f,,n,g,l,o,p'
        select_params = {'EnablePayloadCrc':True}

        req, resp = make_select_object(sql, resp_content, simulate_bad_crc=True)

        req_info = mock_response(do_request, resp)

        try:
            result = bucket().select_object('select-test.txt', sql, None, select_params)
            result.read()
            self.assertFalse(True, "expect InconsistentError")
        except InconsistentError:
            pass

    @patch('oss2.Session.do_request')
    def test_select_csv_with_callback(self, do_request):
        helper = SelectCaseHelper()
        helper.select(self, do_request, callback)
    
    @patch('oss2.Session.do_request')
    def test_select_csv_with_error(self, do_request):
        sql = "select * from ossobject limit 10"
        resp_content = b'a,b,c,d,e,f,,n,g,l,o,p'
        select_params = {'EnablePayloadCrc':True}

        req, resp = make_select_object(sql, resp_content, status=400, error = b"test error")

        req_info = mock_response(do_request, resp)

        try:
            result = bucket().select_object('select-test.txt', sql, None, select_params)
            result.read()
            self.assertFalse(True, "expect SelectOperationFailed")
        except SelectOperationFailed as errorException:
            self.assertEqual(errorException.status, 400)
            self.assertEqual(errorException.message, b'test error')
    
    @patch('oss2.Session.do_request')
    def test_head_csv_with_error(self, do_request):
        head_params = None
        helper = SelectCaseHelper()
        try:
            helper.create_meta(self, do_request, head_params, b'InvalidCsvLine.error code:invalid csv', 400)
            self.assertFalse(True, "expect SelectOperationFailed")
        except SelectOperationFailed as errorException:
            self.assertEqual(errorException.status, 400)
            self.assertEqual(errorException.message, b'error code:invalid csv')
            self.assertEqual(errorException.code, b'InvalidCsvLine')
    
    @patch('oss2.Session.do_request')
    def test_select_json_read_with_params(self, do_request):
        select_params = {'CompressionType':'GZIP',
                         'OutputRawData':False, 'EnablePayloadCrc':True, 'OutputRecordDelimiter':',\n', 'SkipPartialDataRecord':False, 'MaxSkippedRecordsAllowed':100, 'Json_Type':'DOCUMENT'}
        helper = SelectCaseHelper()
        helper.select(self, do_request, None, select_params)

    @patch('oss2.Session.do_request')
    def test_select_json_read_with_line_range(self, do_request):
        select_params = {'LineRange':[0,10], 'CompressionType':'None',
                         'OutputRawData':True, 'EnablePayloadCrc':False, 'OutputRecordDelimiter':',\n', 'SkipPartialDataRecord':True, 'MaxSkippedRecordsAllowed':100, 'Json_Type':'LINES'}
        helper = SelectCaseHelper()
        helper.select(self, do_request, None, select_params)

    @patch('oss2.Session.do_request')
    def test_select_json_read_with_split_range(self, do_request):
        select_params = {'SplitRange':[0,10], 'CompressionType':'None',
                         'OutputRawData':True, 'EnablePayloadCrc':False, 'OutputRecordDelimiter':',\n', 'SkipPartialDataRecord':True, 'MaxSkippedRecordsAllowed':100, 'Json_Type':'LINES',
                         'ParseJsonNumberAsString':False}
        helper = SelectCaseHelper()
        helper.select(self, do_request, None, select_params)

    @patch('oss2.Session.do_request')
    def test_select_json_read_with_invalid_parameters(self, do_request):
        select_params = {'SplitRangeXXXX':[0,10]}
        helper = SelectCaseHelper()
        try:
            helper.select(self, do_request, None, select_params)
            helper.assertFalse()
        except SelectOperationClientError:
            print("expected error")

    @patch('oss2.Session.do_request')
    def test_create_json_meta_with_params(self, do_request):
        head_params = {'OverwriteIfExists':'True', 'Json_Type':'LINES','CompressionType':'NONE'}
        helper = SelectCaseHelper()
        helper.create_meta(self, do_request, head_params)

    @patch('oss2.Session.do_request')
    def test_create_json_meta_with_params2(self, do_request):
        head_params = {'OverwriteIfExists':'True', 'Json_Type':'DOCUMENT'}
        helper = SelectCaseHelper()
        try:
            helper.create_meta(self, do_request, head_params)
            helper.assertFalse()
        except SelectOperationClientError:
            print("expected error")

    @patch('oss2.Session.do_request')
    def test_range_select(self, do_request):
        byte_range = [0,9]
        select_params = {}
        helper = SelectCaseHelper()
        try:
            helper.select(self, do_request, None, select_params, byte_range)
            helper.assertFalse()
        except ClientError:
            print("expected error")
        
        select_params = {'AllowQuotedRecordDelimiter':False}
        helper.select(self, do_request, None, select_params, byte_range)

        select_params['AllowQuotedRecordDelimiter'] = True 
        try:
            helper.select(self, do_request, None, select_params, byte_range)
            helper.assertFalse()
        except ClientError:
            print("expected error")
        
        try:
            helper.select(self, do_request, None, None, byte_range)
            helper.assertFalse()
        except ClientError:
            print("expected error")

if __name__ == '__main__':
    unittest.main()
