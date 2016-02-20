# -*- coding: utf-8 -*-

import oss2

from functools import partial
from mock import patch

from common import *

UPLOAD_ID = '97BD544A65DB46F9A8735C93917A960F'


class TestMultipart(OssTestCase):
    @patch('oss2.Session.do_request')
    def test_init(self, do_request):
        payload = '''HTTP/1.1 200 OK
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

        req_info = mock_do_request(do_request, payload)

        result = bucket().init_multipart_upload('uosvelpvgjwtxaciqtxoplnx')

        self.assertEqual(req_info.req.params['uploads'], '')
        self.assertUrlWithKey(req_info.req.url, 'uosvelpvgjwtxaciqtxoplnx')

        self.assertEqual(result.upload_id, '97BD544A65DB46F9A8735C93917A960F')

    @patch('oss2.Session.do_request')
    def test_upload_part(self, do_request):
        payload = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:59 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BEF6078C0E44874A4AD
ETag: "DF1F9DE8F39BDE03716AC8D425589A5A"'''

        content = random_bytes(1024 * 1024 + 1)
        req_info = mock_do_request(do_request, payload, data_type=DT_BYTES)

        result = bucket().upload_part('tmmzgvvmsgesihfo', '41337E94168A4E6F918C3D6CAAFADCCD', 3, content)

        self.assertEqual(req_info.data, content)
        self.assertEqual(req_info.req.params['partNumber'], '3')
        self.assertEqual(req_info.req.params['uploadId'], '41337E94168A4E6F918C3D6CAAFADCCD')
        self.assertUrlWithKey(req_info.req.url, 'tmmzgvvmsgesihfo')

        self.assertEqual(result.etag, 'DF1F9DE8F39BDE03716AC8D425589A5A')

    @patch('oss2.Session.do_request')
    def test_upload_part_copy(self, do_request):
        payload = '''HTTP/1.1 200 OK
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

        req_info = mock_do_request(do_request, payload)

        result = bucket().upload_part_copy('fake-src-bucket', 'fake-src-key', (0, 102399), 'fake-target-key', 'fake-upload-id', 1)

        self.assertEqual(req_info.req.headers['x-oss-copy-source'], '/fake-src-bucket/fake-src-key')
        self.assertEqual(req_info.req.headers['x-oss-copy-source-range'], 'bytes=0-102399')

        self.assertEqual(result.etag, '4DE8075FB607DF4D13FBC480EA488EFA')
        self.assertEqual(result.request_id, '566B6C09D5A340D61A73D677')

    @patch('oss2.Session.do_request')
    def test_complete(self, do_request):
        from oss2.models import PartInfo

        parts = list()
        parts.append(PartInfo(1, '4DE8075FB607DF4D13FBC480EA488EFA'))
        parts.append(PartInfo(2, 'AF947EC157726CEA88ED83B3C989063B'))

        payload = '''HTTP/1.1 200 OK
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

        req_info = mock_do_request(do_request, payload, data_type=DT_BYTES)

        result = bucket().complete_multipart_upload('pasncdoyuvuvuiyewfsobdwn', '65484B78EF3846298B8E2DC1643F8F37', parts)

        self.assertEqual(req_info.req.method, 'POST')
        self.assertEqual(req_info.req.params['uploadId'], '65484B78EF3846298B8E2DC1643F8F37')
        self.assertUrlWithKey(req_info.req.url, 'pasncdoyuvuvuiyewfsobdwn')

        expected = b'''<CompleteMultipartUpload><Part><PartNumber>1</PartNumber><ETag>"4DE8075FB607DF4D13FBC480EA488EFA"</ETag></Part>''' + \
        b'''<Part><PartNumber>2</PartNumber><ETag>"AF947EC157726CEA88ED83B3C989063B"</ETag></Part></CompleteMultipartUpload>'''
        self.assertXmlEqual(expected, req_info.data)

        self.assertEqual(result.etag, '1C787C506EABFB9B45EAAA8DB039F4B2-2')

    @patch('oss2.Session.do_request')
    def test_abort(self, do_request):
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4delete, req_info=req_info)

        bucket().abort_multipart_upload('fake-key', UPLOAD_ID)

        self.assertEqual(req_info.req.params['uploadId'], UPLOAD_ID)

