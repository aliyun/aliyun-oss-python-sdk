# -*- coding: utf-8 -*-

import oss2
import unittest
import unittests

from functools import partial
from mock import patch


class TestMultipart(unittests.common.OssTestCase):
    @patch('oss2.Session.do_request')
    def test_init(self, do_request):
        request_text = '''POST /uosvelpvgjwtxaciqtxoplnx?uploads= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 0
date: Sat, 12 Dec 2015 00:35:55 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:2OVoUTO7rFeeGlpXH9M6ZMuh7d8=
'''
        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:55 GMT
Content-Type: application/xml
Content-Length: 232
Connection: keep-alive
x-oss-request-id: 566B6BEB1BA604C27DD43805

<?xml version="1.0" encoding="UTF-8"?>
<InitiateMultipartUploadResult>
  <Bucket>ming-oss-share</Bucket>
  <Key>uosvelpvgjwtxaciqtxoplnx</Key>
  <UploadId>97BD544A65DB46F9A8735C93917A960F</UploadId>
</InitiateMultipartUploadResult>
'''

        req_info = unittests.common.mock_response(do_request, response_text)
        result = unittests.common.bucket().init_multipart_upload('uosvelpvgjwtxaciqtxoplnx')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.upload_id, '97BD544A65DB46F9A8735C93917A960F')

    @patch('oss2.Session.do_request')
    def test_upload_part(self, do_request):
        content = unittests.common.random_bytes(1024)

        request_text = '''PUT /tmmzgvvmsgesihfo?partNumber=3&uploadId=41337E94168A4E6F918C3D6CAAFADCCD HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 1024
date: Sat, 12 Dec 2015 00:35:59 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:3+h0rLBaA3gPrM4iZoFSyQZn2ts=

{0}'''.format(oss2.to_string(content))

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:59 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BEF6078C0E44874A4AD
x-oss-hash-crc64ecma: {0}
ETag: "DF1F9DE8F39BDE03716AC8D425589A5A"'''.format(unittests.common.calc_crc(content))

        req_info = unittests.common.mock_response(do_request, response_text)
        result = unittests.common.bucket().upload_part('tmmzgvvmsgesihfo', '41337E94168A4E6F918C3D6CAAFADCCD', 3, content)

        self.assertRequest(req_info, request_text)
        self.assertEqual(req_info.data, content)

        self.assertEqual(result.etag, 'DF1F9DE8F39BDE03716AC8D425589A5A')
        
    @patch('oss2.Session.do_request')
    def test_upload_part_without_crc_in_response(self, do_request):
        content = unittests.common.random_bytes(1024)

        request_text = '''PUT /tmmzgvvmsgesihfo?partNumber=3&uploadId=41337E94168A4E6F918C3D6CAAFADCCD HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 1024
date: Sat, 12 Dec 2015 00:35:59 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:3+h0rLBaA3gPrM4iZoFSyQZn2ts=

{0}'''.format(oss2.to_string(content))

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:59 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BEF6078C0E44874A4AD
ETag: "DF1F9DE8F39BDE03716AC8D425589A5A"'''

        req_info = unittests.common.mock_response(do_request, response_text)
        result = unittests.common.bucket().upload_part('tmmzgvvmsgesihfo', '41337E94168A4E6F918C3D6CAAFADCCD', 3, content)

        self.assertRequest(req_info, request_text)
        self.assertEqual(req_info.data, content)

        self.assertEqual(result.etag, 'DF1F9DE8F39BDE03716AC8D425589A5A')
        
    @patch('oss2.Session.do_request')
    def test_upload_part_copy(self, do_request):
        request_text = '''PUT /pasncdoyuvuvuiyewfsobdwn?partNumber=1&uploadId=65484B78EF3846298B8E2DC1643F8F37 HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
x-oss-copy-source: /ming-oss-share/pasncdoyuvuvmgqtkchhuosw
Content-Length: 0
x-oss-copy-source-range: bytes=0-102399
date: Sat, 12 Dec 2015 00:36:25 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:wbO3Klw0f6pMPy2lBDZqNtgZ9EY='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:36:26 GMT
Content-Type: application/xml
Content-Length: 180
Connection: keep-alive
x-oss-request-id: 566B6C09D5A340D61A73D677
Content-Range: bytes 0-102399/204800
ETag: "4DE8075FB607DF4D13FBC480EA488EFA"

<?xml version="1.0" encoding="UTF-8"?>
<CopyPartResult>
  <LastModified>2015-12-12T00:36:26.000Z</LastModified>
  <ETag>"4DE8075FB607DF4D13FBC480EA488EFA"</ETag>
</CopyPartResult>'''

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().upload_part_copy('ming-oss-share', 'pasncdoyuvuvmgqtkchhuosw', (0, 102399),
                                           'pasncdoyuvuvuiyewfsobdwn', '65484B78EF3846298B8E2DC1643F8F37', 1)

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.etag, '4DE8075FB607DF4D13FBC480EA488EFA')
        self.assertEqual(result.request_id, '566B6C09D5A340D61A73D677')

    @patch('oss2.Session.do_request')
    def test_complete(self, do_request):
        from oss2.models import PartInfo

        parts = list()
        parts.append(PartInfo(1, '4DE8075FB607DF4D13FBC480EA488EFA'))
        parts.append(PartInfo(2, 'AF947EC157726CEA88ED83B3C989063B'))

        request_text = '''POST /pasncdoyuvuvuiyewfsobdwn?uploadId=65484B78EF3846298B8E2DC1643F8F37 HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 223
date: Sat, 12 Dec 2015 00:36:26 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:TgjWAumJAl8dDr0yqWHOyqqwrd0=

<CompleteMultipartUpload><Part><PartNumber>1</PartNumber><ETag>"4DE8075FB607DF4D13FBC480EA488EFA"</ETag></Part><Part><PartNumber>2</PartNumber><ETag>"AF947EC157726CEA88ED83B3C989063B"</ETag></Part></CompleteMultipartUpload>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:36:26 GMT
Content-Type: application/xml
Content-Length: 327
Connection: keep-alive
x-oss-request-id: 566B6C0A05200A20B174994F
ETag: "1C787C506EABFB9B45EAAA8DB039F4B2-2"

<?xml version="1.0" encoding="UTF-8"?>
<CompleteMultipartUploadResult>
  <Location>http://ming-oss-share.oss-cn-hangzhou.aliyuncs.com/pasncdoyuvuvuiyewfsobdwn</Location>
  <Bucket>ming-oss-share</Bucket>
  <Key>pasncdoyuvuvuiyewfsobdwn</Key>
  <ETag>"1C787C506EABFB9B45EAAA8DB039F4B2-2"</ETag>
</CompleteMultipartUploadResult>'''

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().complete_multipart_upload('pasncdoyuvuvuiyewfsobdwn', '65484B78EF3846298B8E2DC1643F8F37', parts)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.etag, '1C787C506EABFB9B45EAAA8DB039F4B2-2')

    @patch('oss2.Session.do_request')
    def test_abort(self, do_request):
        request_text = '''DELETE /uosvelpvgjwtxaciqtxoplnx?uploadId=97BD544A65DB46F9A8735C93917A960F HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 0
date: Sat, 12 Dec 2015 00:35:56 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:anUcRNyx/g9BxU8xplJHn2BcRvQ='''

        response_text = '''HTTP/1.1 204 No Content
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:56 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BEC1BA604C27DD438F8'''

        req_info = unittests.common.mock_response(do_request, response_text)
        unittests.common.bucket().abort_multipart_upload('uosvelpvgjwtxaciqtxoplnx', '97BD544A65DB46F9A8735C93917A960F')

        self.assertRequest(req_info, request_text)

