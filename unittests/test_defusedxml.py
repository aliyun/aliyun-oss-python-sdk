# -*- coding: utf-8 -*-

from mock import patch
from unittests.common import *
import xml.etree.ElementTree as ElementTree
from defusedxml.ElementTree import DTDForbidden
from oss2.exceptions import ResponseParseError
from oss2.xml_utils import _defused_element_tree_from_string


class TestDefausedxml(OssTestCase):

    def test_compare_xml_defusedxml(self):
        doctype_body = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE test [
<!ENTITY test_xxe \"HELLO\">
]>
<Root><name>&test_xxe;</name></Root>'''

        # parse by xml library
        root = ElementTree.fromstring(doctype_body)
        name = root.find("name").text
        self.assertEqual('HELLO', name)

        # parse by sdk method
        try:
            root = _defused_element_tree_from_string(doctype_body)
            self.assertFalse(True)
        except DTDForbidden as e:
            pass


    @patch('oss2.Session.do_request')
    def test_parse_200ok_response_with_dtd(self, do_request):
        request_text = '''GET /?stat= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:41 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Pt0DtPQ/FODOGs5y0yTIVctRcok='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Type: application/xml
Content-Length: 96
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0

<?xml version="1.0" encoding="UTF-8"?>
<BucketStat> 
    <Storage>472594058</Storage> 
    <ObjectCount>666</ObjectCount> 
    <MultipartUploadCount>992</MultipartUploadCount> 
</BucketStat>'''

        req_info = mock_response(do_request, response_text)
        result = bucket().get_bucket_stat()
        self.assertRequest(req_info, request_text)
        self.assertEqual(result.storage_size_in_bytes, 472594058)
        self.assertEqual(result.object_count, 666)
        self.assertEqual(result.multi_part_upload_count, 992)

        # test error response
        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Type: application/xml
Content-Length: 96
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0

<?xml version="1.0" encoding="UTF-8"?>
<BucketStat> 
    <Storage>472594058</Error> 
    <ObjectCount>666</ObjectCount> 
    <MultipartUploadCount>992</MultipartUploadCount> 
</BucketStat>'''

        try:
            req_info = mock_response(do_request, response_text)
            result = bucket().get_bucket_stat()
            self.assertFalse(True)
        except ResponseParseError as e:
            self.assertEqual("ResponseParseError", e.code)

        # test sdk parse xml vulnerability.
        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:42 GMT
Content-Type: application/xml
Content-Length: 96
Connection: keep-alive
x-oss-request-id: 566B6BDD68248CE14F729DC0

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE test [
]>
<BucketStat> 
    <Storage>472594058</Storage> 
    <ObjectCount>666</ObjectCount> 
    <MultipartUploadCount>992</MultipartUploadCount> 
</BucketStat>'''

        try:
            req_info = mock_response(do_request, response_text)
            result = bucket().get_bucket_stat()
            self.assertFalse(True)
        except ResponseParseError as e:
            self.assertEqual("DefusedXmlException", e.code)

    @patch('oss2.Session.do_request')
    def test_error_response(self, do_request):
        request_text = '''GET /sbowspxjhmccpmesjqcwagfw?objectMeta HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:37:17 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:wopWcmMd/70eNKYOc9M6ZA21yY8='''

        dtd_response_text = '''HTTP/1.1 404 Not Found
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:37:17 GMT
Content-Type: application/xml
Content-Length: 287
Connection: keep-alive
x-oss-request-id: 566B6C3D6086505A0CFF0F68

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE test [
]>
<Error>
  <Code>NoSuchKey</Code>
  <Message>The specified key does not exist.</Message>
  <RequestId>566B6C3D6086505A0CFF0F68</RequestId>
  <HostId>ming-oss-share.oss-cn-hangzhou.aliyuncs.com</HostId>
  <Key>sbowspxjhmccpmesjqcwagfw</Key>
</Error>'''

        req_info = mock_response(do_request, dtd_response_text)
        self.assertTrue(not bucket().object_exists('sbowspxjhmccpmesjqcwagfw'))
        self.assertRequest(req_info, request_text)


if __name__ == '__main__':
    unittest.main()
