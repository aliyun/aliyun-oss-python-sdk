# -*- coding: utf-8 -*-

import os

import oss2

from functools import partial
from oss2 import to_string
from mock import patch

from common import *


def do4append(req, timeout, next_position=0, req_info=None, data_type=None):
    resp = r4append(next_position)

    if req_info:
        req_info.req = req
        req_info.resp = resp
        req_info.size = get_length(req.data)
        req_info.data = read_data(req.data, data_type)

    return resp


def r4append(next_position, in_status=200, in_headers=None):
    headers = oss2.CaseInsensitiveDict({
        'Server': 'AliyunOSS',
        'Date': 'Fri, 11 Dec 2015 11:40:30 GMT',
        'Content-Length': '0',
        'Connection': 'keep-alive',
        'x-oss-request-id': '566AB62E9C30F8552526DADF',
        'ETag': '"24F7FA10676D816E0D6C6B5600000000"',
        'x-oss-next-append-position': str(next_position),
        'x-oss-hash-crc64ecma': '7962765905601689380'
    })

    merge_headers(headers, in_headers)

    return MockResponse(in_status, headers, b'')


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
        request_text = '''GET /sbowspxjhmccpmesjqcwagfw HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
if-modified-since: Sun, 13 Dec 2015 00:37:17 GMT
date: Sat, 12 Dec 2015 00:37:17 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:wopWcmMd/70eNKYOc9M6ZA21yY8='''

        response_text = '''HTTP/1.1 304 Not Modified
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:37:17 GMT
Content-Type: application/octet-stream
Connection: keep-alive
x-oss-request-id: 566B6C3D010B7A4314D2253D
Accept-Ranges: bytes
ETag: "5EB63BBBE01EEED093CB22BB8F5ACDC3"
Last-Modified: Sat, 12 Dec 2015 00:37:17 GMT
x-oss-object-type: Normal'''

        req_info = mock_response(do_request, response_text)

        self.assertTrue(bucket().object_exists('sbowspxjhmccpmesjqcwagfw'))
        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_object_exists_false(self, do_request):
        request_text = '''GET /sbowspxjhmccpmesjqcwagfw HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
if-modified-since: Sun, 13 Dec 2015 00:37:17 GMT
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
    def test_get_with_progress(self, do_request):
        content = random_bytes(1024 * 1024 + 1)

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

        req_info = mock_response(do_request, response_text)

        self.previous = -1
        result = bucket().get_object('sjbhlsgsbecvlpbf', progress_callback=self.progress_callback)

        self.assertRequest(req_info, request_text)

        content_read = read_file(result)

        self.assertEqual(self.previous, len(content))
        self.assertEqual(len(content_read), len(content))
        self.assertEqual(content_read, content)

    @patch('oss2.Session.do_request')
    def test_get_to_file(self, do_request):
        size = 1023
        resp = r4get(random_bytes(size))
        do_request.return_value = resp

        filename = self.tempname()

        result = bucket().get_object_to_file('key', filename)

        self.assertEqual(result.request_id, resp.headers['x-oss-request-id'])
        self.assertEqual(result.content_length, size)
        self.assertEqual(os.path.getsize(filename), size)

        with open(filename, 'rb') as f:
            self.assertEqual(resp.body, f.read())

    @patch('oss2.Session.do_request')
    def test_get_to_file_with_progress(self, do_request):
        size = 1024 * 1024 + 1
        resp = r4get(random_bytes(size))
        do_request.return_value = resp

        filename = self.tempname()

        self.previous = -1
        bucket().get_object_to_file('fake-key', filename, progress_callback=self.progress_callback)

        self.assertEqual(self.previous, size)
        self.assertEqual(os.path.getsize(filename), size)
        with open(filename, 'rb') as f:
            self.assertEqual(resp.body, f.read())

    @patch('oss2.Session.do_request')
    def test_put_result(self, do_request):
        resp = r4put(in_headers={'ETag': '"E5831D5EBC7AAF5D6C0D20259FE141D2"'})
        do_request.return_value = resp

        result = bucket().put_object('fake-key', b'dummy content')

        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, resp.headers['x-oss-request-id'])
        self.assertEqual(result.etag, resp.headers['ETag'].strip('"'))

    @patch('oss2.Session.do_request')
    def test_put_bytes(self, do_request):
        content = random_bytes(1024 * 1024 - 1)
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4put_object, req_info=req_info, data_type=DT_BYTES)

        bucket().put_object('fake-key', content)

        self.assertEqual(content, req_info.data)

    @patch('oss2.Session.do_request')
    def test_put_bytes_with_progress(self, do_request):
        self.previous = -1

        content = random_bytes(1024 * 1024 - 1)
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4put, req_info=req_info, data_type=DT_FILE)

        bucket().put_object('fake-key', content, progress_callback=self.progress_callback)

        self.assertEqual(self.previous, len(content))
        self.assertEqual(len(content), len(req_info.data))
        self.assertEqual(content, req_info.data)

    @patch('oss2.Session.do_request')
    def test_put_from_file(self, do_request):
        size = 512 * 2 - 1
        content = random_bytes(size)
        filename = self.make_tempfile(content)

        req_info = RequestInfo()
        do_request.auto_spec = True
        do_request.side_effect = partial(do4put, req_info=req_info, data_type=DT_FILE)

        result = bucket().put_object_from_file('fake-key', filename)
        self.assertEqual(result.request_id, req_info.resp.headers['x-oss-request-id'])
        self.assertEqual(content, req_info.data)

    @patch('oss2.Session.do_request')
    def test_append(self, do_request):
        size = 8192 * 2 - 1
        content = random_bytes(size)

        do_request.return_value = r4append(size)

        result = bucket().append_object('fake-key', 0, content)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.next_position, size)

    @patch('oss2.Session.do_request')
    def test_append_with_progress(self, do_request):
        size = 1024 * 1024
        content = random_bytes(size)

        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4append, next_position=size, req_info=req_info, data_type=DT_FILE)

        self.previous = -1
        bucket().append_object('fake-key', 0, content, progress_callback=self.progress_callback)
        self.assertEqual(self.previous, size)

    @patch('oss2.Session.do_request')
    def test_delete(self, do_request):
        resp = r4delete()
        do_request.return_value = resp

        result = bucket().delete_object('fake-key')

        self.assertEqual(result.request_id, resp.headers['x-oss-request-id'])
        self.assertEqual(result.status, 204)

    def test_batch_delete_empty(self):
        self.assertRaises(oss2.exceptions.ClientError, bucket().batch_delete_objects, [])

    @patch('oss2.Session.do_request')
    def test_batch_delete(self, do_request):
        body = '''<?xml version="1.0" encoding="UTF-8"?>
        <DeleteResult>
        <EncodingType>url</EncodingType>
        <Deleted>
            <Key>%E4%B8%AD%E6%96%87%21%40%23%24%25%5E%26%2A%28%29-%3D%E6%96%87%E4%BB%B6%0C-2.txt</Key>
        </Deleted>
        <Deleted>
            <Key>%E4%B8%AD%E6%96%87%21%40%23%24%25%5E%26%2A%28%29-%3D%E6%96%87%E4%BB%B6%0C-3.txt</Key>
        </Deleted>
        <Deleted>
            <Key>%3Chello%3E</Key>
        </Deleted>
        </DeleteResult>
        '''

        do_request.auto_spec = True
        do_request.side_effect = partial(do4body, body=body, content_type='application/xml')

        key_list = ['中文!@#$%^&*()-=文件\x0C-2.txt', u'中文!@#$%^&*()-=文件\x0C-3.txt', '<hello>']

        result = bucket().batch_delete_objects(key_list)
        self.assertEqual(result.deleted_keys, list(to_string(key) for key in key_list))

    @patch('oss2.Session.do_request')
    def test_copy_object(self, do_request):
        req_info = RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(do4copy, req_info=req_info)

        in_headers = {'Content-Type': 'text/plain', 'x-oss-meta-key': 'value'}
        result = bucket().update_object_meta('fake-key.js', in_headers)

        self.assertEqual(req_info.req.headers['x-oss-copy-source'], '/' + BUCKET_NAME + '/fake-key.js')
        self.assertEqual(req_info.req.headers['Content-Type'], 'text/plain')
        self.assertEqual(req_info.req.headers['x-oss-meta-key'], 'value')

        self.assertEqual(result.request_id, REQUEST_ID)
        self.assertEqual(result.etag, ETAG)

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