# -*- coding: utf-8 -*-

import os
import oss2

from functools import partial
from oss2 import to_string
from mock import patch

from unittests.common import *


def make_get_object(content):
        request_text = '''GET /sjbhlsgsbecvlpbf HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:PAedG7U86ZxQ2WTB+GdpSltoiTI='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Type: text/plain
Content-Length: {0}
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
Accept-Ranges: bytes
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"
Last-Modified: Sat, 12 Dec 2015 00:35:53 GMT
x-oss-object-type: Normal

{1}'''.format(len(content), to_string(content))

        return request_text, response_text


def make_put_object(content):
    request_text = '''PUT /sjbhlsgsbecvlpbf.txt HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Type: text/plain
Content-Length: {0}
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
authorization: OSS ZCDmm7TPZKHtx77j:W6whAowN4aImQ0dfbMHyFfD0t1g=
Accept: */*

{1}'''.format(len(content), to_string(content))

    response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
x-oss-hash-crc64ecma: {0}
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"'''.format(calc_crc(content))

    return request_text, response_text


def make_append_object(position, content):
    request_text = '''POST /sjbhlsgsbecvlpbf?position={0}&append= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: {1}
date: Sat, 12 Dec 2015 00:36:29 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:1njpxsTivMNvTdfYolCUefRInVY=

{2}'''.format(position, len(content), to_string(content))

    response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:36:29 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6C0D1790CF586F72240B
ETag: "24F7FA10676D816E0D6C6B5600000000"
x-oss-next-append-position: {0}
x-oss-hash-crc64ecma: {1}'''.format(position + len(content), calc_crc(content))

    return request_text, response_text


class TestObject(OssTestCase):
    @patch('oss2.Session.do_request')
    def test_head(self, do_request):
        request_text = '''HEAD /apbmntxqtvxjzini HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:55 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:Q05CWxpclrtNnUWHY5wS10fhFk0='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:55 GMT
Content-Type: application/octet-stream
Content-Length: 10
Connection: keep-alive
x-oss-request-id: 566B6BEBD4C05B21E97261B0
Accept-Ranges: bytes
ETag: "0CF031A5EB9351746195B20B86FD3F68"
Last-Modified: Sat, 12 Dec 2015 00:35:54 GMT
x-oss-object-type: Normal'''

        req_info = mock_response(do_request, response_text)

        result = bucket().head_object('apbmntxqtvxjzini')

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.content_length, 10)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, '566B6BEBD4C05B21E97261B0')
        self.assertEqual(result.object_type, 'Normal')
        self.assertEqual(result.content_type, 'application/octet-stream')
        self.assertEqual(result.etag, '0CF031A5EB9351746195B20B86FD3F68')
        self.assertEqual(result.last_modified, 1449880554)

    @patch('oss2.Session.do_request')
    def test_object_exists_true(self, do_request):
        request_text = '''GET /sbowspxjhmccpmesjqcwagfw?objectMeta HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:37:17 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:wopWcmMd/70eNKYOc9M6ZA21yY8='''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6C3D010B7A4314D2253D
Date: Sat, 12 Dec 2015 00:37:17 GMT
ETag: "5B3C1A2E053D763E1B002CC607C5A0FE"
Last-Modified: Sat, 12 Dec 2015 00:37:17 GMT
Content-Length: 344606
Connection: keep-alive
Server: AliyunOSS'''

        req_info = mock_response(do_request, response_text)

        self.assertTrue(bucket().object_exists('sbowspxjhmccpmesjqcwagfw'))
        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_object_exists_false(self, do_request):
        request_text = '''GET /sbowspxjhmccpmesjqcwagfw?objectMeta HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:37:17 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:wopWcmMd/70eNKYOc9M6ZA21yY8='''     

        response_text = '''HTTP/1.1 404 Not Found
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:37:17 GMT
Content-Type: application/xml
Content-Length: 287
Connection: keep-alive
x-oss-request-id: 566B6C3D6086505A0CFF0F68

<?xml version="1.0" encoding="UTF-8"?>
<Error>
  <Code>NoSuchKey</Code>
  <Message>The specified key does not exist.</Message>
  <RequestId>566B6C3D6086505A0CFF0F68</RequestId>
  <HostId>ming-oss-share.oss-cn-hangzhou.aliyuncs.com</HostId>
  <Key>sbowspxjhmccpmesjqcwagfw</Key>
</Error>'''

        req_info = mock_response(do_request, response_text)
        self.assertTrue(not bucket().object_exists('sbowspxjhmccpmesjqcwagfw'))
        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_get(self, do_request):
        content = random_bytes(1023)

        request_text, response_text = make_get_object(content)

        req_info = mock_response(do_request, response_text)

        result = bucket().get_object('sjbhlsgsbecvlpbf')

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.read(), content)
        self.assertEqual(result.content_length, len(content))
        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.object_type, 'Normal')
        self.assertEqual(result.content_type, 'text/plain')
        self.assertEqual(result.etag, 'D80CF0E5BE2436514894D64B2BCFB2AE')
        self.assertEqual(result.last_modified, 1449880553)

    @patch('oss2.Session.do_request')
    def test_get_with_query_parameter(self, do_request):
        request_text = '''GET /sjbhlsgsbecvlpbf?response-content-type=override-content-type HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:PAedG7U86ZxQ2WTB+GdpSltoiTI='''

        response_text = '''HTTP/1.1 200 OK
x-oss-request-id: 566B6C3D010B7A4314D2253D
Date: Sat, 12 Dec 2015 00:37:17 GMT
ETag: "5B3C1A2E053D763E1B002CC607C5A0FE"
Last-Modified: Sat, 12 Dec 2015 00:37:17 GMT
Content-Length: 344606
Content-Type: override-content-type
Connection: keep-alive
Server: AliyunOSS'''

        req_info = mock_response(do_request, response_text)

        query_params = {'response-content-type': 'override-content-type'}

        result = bucket().get_object('sjbhlsgsbecvlpbf', params=query_params)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.content_type, 'override-content-type')

    @patch('oss2.Session.do_request')
    def test_get_with_progress(self, do_request):
        content = random_bytes(1024 * 1024 + 1)

        request_text, response_text = make_get_object(content)
        req_info = mock_response(do_request, response_text)

        self.previous = -1
        result = bucket().get_object('sjbhlsgsbecvlpbf', progress_callback=self.progress_callback)

        self.assertRequest(req_info, request_text)

        content_read = read_file(result)

        self.assertEqual(self.previous, len(content))
        self.assertEqual(len(content_read), len(content))
        self.assertEqual(content_read, oss2.to_bytes(content))

    @patch('oss2.Session.do_request')
    def test_get_to_file(self, do_request):
        content = random_bytes(1023)

        request_text, response_text = make_get_object(content)
        req_info = mock_response(do_request, response_text)

        filename = self.tempname()

        result = bucket().get_object_to_file('sjbhlsgsbecvlpbf', filename)

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.content_length, len(content))
        self.assertEqual(os.path.getsize(filename), len(content))

        with open(filename, 'rb') as f:
            self.assertEqual(content, f.read())

    @patch('oss2.Session.do_request')
    def test_get_to_file_with_query_parameter(self, do_request):
        content = random_bytes(1023)

        request_text = '''GET /sjbhlsgsbecvlpbf?response-content-type=override-content-type HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:PAedG7U86ZxQ2WTB+GdpSltoiTI='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Type: override-content-type
Content-Length: {0}
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
Accept-Ranges: bytes
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"
Last-Modified: Sat, 12 Dec 2015 00:35:53 GMT
x-oss-object-type: Normal

{1}'''.format(len(content), to_string(content))

        req_info = mock_response(do_request, response_text)

        filename = self.tempname()
        query_params = {'response-content-type': 'override-content-type'}

        result = bucket().get_object_to_file('sjbhlsgsbecvlpbf', filename, params=query_params)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.content_type, 'override-content-type')

    @patch('oss2.Session.do_request')
    def test_get_to_file_with_progress(self, do_request):
        size = 1024 * 1024 + 1
        content = random_bytes(size)

        request_text, response_text = make_get_object(content)
        req_info = mock_response(do_request, response_text)

        filename = self.tempname()

        self.previous = -1
        bucket().get_object_to_file('sjbhlsgsbecvlpbf', filename, progress_callback=self.progress_callback)

        self.assertRequest(req_info, request_text)

        self.assertEqual(self.previous, size)
        self.assertEqual(os.path.getsize(filename), size)
        with open(filename, 'rb') as f:
            self.assertEqual(oss2.to_bytes(content), f.read())

    @patch('oss2.Session.do_request')
    def test_put_result(self, do_request):
        content = b'dummy content'
        request_text, response_text = make_put_object(content)

        req_info = mock_response(do_request, response_text)

        result = bucket().put_object('sjbhlsgsbecvlpbf.txt', content)

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.etag, 'D80CF0E5BE2436514894D64B2BCFB2AE')

    @patch('oss2.Session.do_request')
    def test_put_bytes(self, do_request):
        content = random_bytes(1024 * 1024 - 1)

        request_text, response_text = make_put_object(content)
        req_info = mock_response(do_request, response_text)

        bucket().put_object('sjbhlsgsbecvlpbf.txt', content)

        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_put_bytes_with_progress(self, do_request):
        self.previous = -1

        content = random_bytes(1024 * 1024 - 1)

        request_text, response_text = make_put_object(content)
        req_info = mock_response(do_request, response_text)

        bucket().put_object('sjbhlsgsbecvlpbf.txt', content, progress_callback=self.progress_callback)

        self.assertRequest(req_info, request_text)
        self.assertEqual(self.previous, len(content))

    @patch('oss2.Session.do_request')
    def test_put_from_file(self, do_request):
        size = 512 * 2 - 1
        content = random_bytes(size)
        filename = self.make_tempfile(content)

        request_text, response_text = make_put_object(content)
        req_info = mock_response(do_request, response_text)

        result = bucket().put_object_from_file('sjbhlsgsbecvlpbf.txt', filename)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.etag, 'D80CF0E5BE2436514894D64B2BCFB2AE')

    @patch('oss2.Session.do_request')
    def test_append(self, do_request):
        size = 8192 * 2 - 1
        content = random_bytes(size)

        request_text, response_text = make_append_object(0, content)
        req_info = mock_response(do_request, response_text)

        result = bucket().append_object('sjbhlsgsbecvlpbf', 0, content, init_crc=0)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.next_position, size)
        self.assertEqual(result.etag, '24F7FA10676D816E0D6C6B5600000000')
        self.assertEqual(result.crc, calc_crc(content))

    @patch('oss2.Session.do_request')
    def test_append_without_crc(self, do_request):
        size = 8192 * 2 - 1
        content = random_bytes(size)

        request_text, response_text = make_append_object(0, content)
        req_info = mock_response(do_request, response_text)

        result = bucket().append_object('sjbhlsgsbecvlpbf', 0, content)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.next_position, size)
        self.assertEqual(result.etag, '24F7FA10676D816E0D6C6B5600000000')
        self.assertEqual(result.crc, calc_crc(content))

    @patch('oss2.Session.do_request')
    def test_append_with_progress(self, do_request):
        size = 1024 * 1024
        content = random_bytes(size)

        request_text, response_text = make_append_object(0, content)
        req_info = mock_response(do_request, response_text)

        self.previous = -1

        result = bucket().append_object('sjbhlsgsbecvlpbf', 0, content, 
                                        progress_callback=self.progress_callback,
                                        init_crc=0)

        self.assertRequest(req_info, request_text)
        self.assertEqual(self.previous, size)
        self.assertEqual(result.next_position, size)

    @patch('oss2.Session.do_request')
    def test_delete(self, do_request):
        request_text = '''DELETE /sjbhlsgsbecvlpbf HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 0
date: Sat, 12 Dec 2015 00:36:29 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:AC830VOm7dDnv+CVpTaui6gh5xc='''

        response_text = '''HTTP/1.1 204 No Content
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:36:29 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6C0D8CDE4E975D730BEF'''

        req_info = mock_response(do_request, response_text)

        result = bucket().delete_object('sjbhlsgsbecvlpbf')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6C0D8CDE4E975D730BEF')
        self.assertEqual(result.status, 204)

    def test_batch_delete_empty(self):
        self.assertRaises(oss2.exceptions.ClientError, bucket().batch_delete_objects, [])

    @patch('oss2.Session.do_request')
    def test_batch_delete(self, do_request):
        request_text = '''POST /?delete=&encoding-type=url HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 100
Content-MD5: zsbG45tEj+StFBFghUllvw==
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:tc4g/qgaHwQ+CoI828v2zFCHj2E=

<Delete><Quiet>false</Quiet><Object><Key>hello</Key></Object><Object><Key>world</Key></Object></Delete>'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Type: application/xml
Content-Length: 383
Connection: keep-alive
x-oss-request-id: 566B6BE9229E6BA1F6F538DE

<?xml version="1.0" encoding="UTF-8"?>
<DeleteResult>
<EncodingType>url</EncodingType>
<Deleted>
    <Key>hello</Key>
</Deleted>
<Deleted>
    <Key>world</Key>
</Deleted>
</DeleteResult>'''
        req_info = mock_response(do_request, response_text)

        key_list = ['hello', 'world']

        result = bucket().batch_delete_objects(key_list)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.deleted_keys, list(to_string(key) for key in key_list))

    @patch('oss2.Session.do_request')
    def test_copy_object(self, do_request):
        request_text = '''PUT /zyfpyqqqxjthdwxkhypziizm.js HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Content-Length: 0
x-oss-copy-source: /ming-oss-share/zyfpyqqqxjthdwxkhypziizm.js
x-oss-meta-category: novel
Content-Type: text/plain
Connection: keep-alive
date: Sat, 12 Dec 2015 00:37:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
authorization: OSS ZCDmm7TPZKHtx77j:azW764vWaOVYhJLdhw4sEntNYP4=
Accept: */*'''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:37:53 GMT
Content-Type: application/xml
Content-Length: 184
Connection: keep-alive
x-oss-request-id: 566B6C611BA604C27DD51F8F
ETag: "164F32EF262006C5EE6C8D1AA30DD2CD"

<?xml version="1.0" encoding="UTF-8"?>
<CopyObjectResult>
  <ETag>"164F32EF262006C5EE6C8D1AA30DD2CD"</ETag>
  <LastModified>2015-12-12T00:37:53.000Z</LastModified>
</CopyObjectResult>'''

        req_info = mock_response(do_request, response_text)

        in_headers = {'Content-Type': 'text/plain', 'x-oss-meta-category': 'novel'}
        result = bucket().update_object_meta('zyfpyqqqxjthdwxkhypziizm.js', in_headers)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6C611BA604C27DD51F8F')
        self.assertEqual(result.etag, '164F32EF262006C5EE6C8D1AA30DD2CD')

    @patch('oss2.Session.do_request')
    def test_put_acl(self, do_request):
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4put, req_info=req_info)

        for acl, expected in [(oss2.OBJECT_ACL_PRIVATE, 'private'),
                              (oss2.OBJECT_ACL_PUBLIC_READ, 'public-read'),
                              (oss2.OBJECT_ACL_PUBLIC_READ_WRITE, 'public-read-write'),
                              (oss2.OBJECT_ACL_DEFAULT, 'default')]:
            bucket().put_object_acl('fake-key', acl)
            self.assertEqual(req_info.req.headers['x-oss-object-acl'], expected)

    @patch('oss2.Session.do_request')
    def test_get_acl(self, do_request):
        template = '''<?xml version="1.0" encoding="UTF-8"?>
        <AccessControlPolicy>
          <Owner>
            <ID>1047205513514293</ID>
            <DisplayName>1047205513514293</DisplayName>
          </Owner>
          <AccessControlList>
            <Grant>{0}</Grant>
          </AccessControlList>
        </AccessControlPolicy>
        '''

        for acl, expected in [(oss2.OBJECT_ACL_PRIVATE, 'private'),
                              (oss2.OBJECT_ACL_PUBLIC_READ, 'public-read'),
                              (oss2.OBJECT_ACL_PUBLIC_READ_WRITE, 'public-read-write'),
                              (oss2.OBJECT_ACL_DEFAULT, 'default')]:
            do_request.auto_spec = True
            do_request.side_effect = partial(do4body, body=template.format(acl), content_type='application/xml')

            result = bucket().get_object_acl('fake-key')
            self.assertEqual(result.acl, expected)


if __name__ == '__main__':
    unittest.main()
