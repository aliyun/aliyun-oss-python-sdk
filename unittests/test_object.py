# -*- coding: utf-8 -*-

import unittest
import tempfile
import os

import oss2

from functools import partial
from oss2 import to_string
from mock import patch

from common import *


def do4put_object(req, timeout, req_info=None, data_type=None):
    return do4put(req, timeout,
                  in_headers={'ETag': '"E5831D5EBC7AAF5D6C0D20259FE141D2"'},
                  req_info=req_info,
                  data_type=data_type)


def do4append(req, timeout, next_position=0, req_info=None, data_type=None):
    resp = r4append(next_position)

    if req_info:
        req_info.req = req
        req_info.resp = resp
        req_info.size = get_length(req.data)
        req_info.data = read_data(req.data, data_type)

    return resp


def do4body(req, timeout,
            req_info=None,
            data_type=DT_BYTES,
            status=200,
            body=None,
            content_type=None):
    if content_type:
        headers = {'Content-Type': content_type}
    else:
        headers = None

    resp = r4get(body, in_headers=headers, in_status=status)

    if req_info:
        req_info.req = req
        req_info.size = get_length(req.data)
        req_info.data = read_data(req.data, data_type)
        req_info.resp = resp

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


class TestObject(unittest.TestCase):
    def setUp(self):
        self.previous = -1
        self.temp_files = []

    def tearDown(self):
        for temp_file in self.temp_files:
            os.remove(temp_file)

    def tempname(self):
        random_name = random_string(16)
        self.temp_files.append(random_name)

        return random_name

    def make_tempfile(self, content):
        fd, pathname = tempfile.mkstemp(suffix='test-upload')

        os.write(fd, content)
        os.close(fd)

        self.temp_files.append(pathname)
        return pathname

    def progress_callback(self, bytes_consumed, total_bytes):
        self.assertTrue(bytes_consumed <= total_bytes)
        self.assertTrue(bytes_consumed > self.previous)

        self.previous = bytes_consumed

    @patch('oss2.Session.do_request')
    def test_head(self, do_request):
        size = 1024
        resp = r4head(size)
        do_request.return_value = resp

        result = bucket().head_object('fake-key')

        self.assertEqual(result.content_length, size)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, resp.headers['x-oss-request-id'])
        self.assertEqual(result.object_type, 'Normal')
        self.assertEqual(result.content_type, resp.headers['Content-Type'])
        self.assertEqual(result.etag, resp.headers['ETag'].strip('"'))
        self.assertEqual(result.last_modified, MTIME)

    @patch('oss2.Session.do_request')
    def test_object_exists(self, do_request):
        do_request.return_value = r4head(0, in_status=304)
        self.assertTrue(bucket().object_exists('fake-key'))

        body = '''<?xml version="1.0" encoding="UTF-8"?>
        <Error>
            <Code>NoSuchKey</Code>
            <Message>The specified key does not exist.</Message>
            <RequestId>566B6C3D6086505A0CFF0F68</RequestId>
            <HostId>fake-bucket.oss-cn-hangzhou.aliyuncs.com</HostId>
            <Key>fake-key</Key>
        </Error>'''
        do_request.auto_spec = True
        do_request.side_effect = partial(do4body, status=404, body=body, content_type='application/xml')

        self.assertTrue(not bucket().object_exists('fake-key'))

    @patch('oss2.Session.do_request')
    def test_get(self, do_request):
        size = 1023
        resp = r4get(random_bytes(size))
        do_request.return_value = resp

        result = bucket().get_object('fake-key')

        self.assertEqual(result.read(), resp.body)
        self.assertEqual(result.content_length, size)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, resp.headers['x-oss-request-id'])
        self.assertEqual(result.object_type, 'Normal')
        self.assertEqual(result.content_type, resp.headers['Content-Type'])
        self.assertEqual(result.etag, resp.headers['ETag'].strip('"'))
        self.assertEqual(result.last_modified, MTIME)

    @patch('oss2.Session.do_request')
    def test_get_with_progress(self, do_request):
        size = 1024 * 1024 + 1
        resp = r4get(random_bytes(size))
        do_request.return_value = resp

        self.previous = -1
        result = bucket().get_object('fake-key', progress_callback=self.progress_callback)
        content = read_file(result)

        self.assertEqual(self.previous, size)
        self.assertEqual(len(content), size)
        self.assertEqual(content, resp.body)

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
