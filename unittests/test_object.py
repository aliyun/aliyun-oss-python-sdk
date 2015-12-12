import unittest
import random
import string
import functools
import oss2

from mock import patch


def random_string(n):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(n))


def random_bytes(n):
    return oss2.to_bytes(random_string(n))


class MockResponse(object):
    def __init__(self, status, headers, body):
        self.status = status
        self.headers = oss2.CaseInsensitiveDict(headers)
        self.body = body

        self.offset = 0

    def read(self, amt=None):
        if self.offset >= len(self.body):
            return ''

        if amt is None:
            end = len(self.body)
        else:
            end = min(len(self.body), self.offset + amt)

        content = self.body[self.offset:end]
        self.offset = end
        return content


    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        return self.read(8192)


_MTIME_STRING = 'Fri, 11 Dec 2015 13:01:41 GMT'
_MTIME = 1449838901


def merge_headers(dst, src):
    if not src:
        return

    for k, v in src:
        dst[k] = v


def r4delete(in_status=204, in_headers=None):
    headers = oss2.CaseInsensitiveDict({
        'Server': 'AliyunOSS',
        'Date': 'Fri, 11 Dec 2015 11:40:31 GMT',
        'Content-Length': '0',
        'Connection': 'keep-alive',
        'x-oss-request-id': '566AB62EB06147681C283D73'
    })

    merge_headers(headers, in_headers)
    return MockResponse(in_status, headers, b'')


def r4head(length, in_status=200, in_headers=None):
    body = random_bytes(length)
    headers = oss2.CaseInsensitiveDict({
        'Server': 'AliyunOSS',
        'Date': 'Fri, 11 Dec 2015 11:40:31 GMT',
        'Content-Type': 'application/javascript',
        'Content-Length': str(length),
        'Connection': 'keep-alive',
        'Vary': 'Accept-Encoding',
        'x-oss-request-id': '566AB62EB06147681C283D73',
        'Accept-Ranges': 'bytes',
        'ETag': '"E5831D5EBC7AAF5D6C0D20259FE141D2"',
        'Last-Modified': _MTIME_STRING,
        'x-oss-object-type': 'Normal'
    })

    merge_headers(headers, in_headers)

    return MockResponse(in_status, headers, body)


def r4get(length, in_status=200, in_headers=None):
    resp = r4head(length, in_status, in_headers)
    resp.body = random_bytes(length)

    return resp

_BT_BYTES = 0
_BT_FILE = 1

_CHUNK_SIZE = 8192


def read_file(fileobj):
    result = b''

    while True:
        content = fileobj.read(_CHUNK_SIZE)
        if content:
            result += content
        else:
            return result


def do4put(req, timeout, body_dict=None, data_type=None):
    if data_type == _BT_BYTES:
        body_dict['data'] = req.data
    elif data_type == _BT_FILE:
        body_dict['data'] = read_file(req.data)

    return r4put()


def r4put(in_status=200, in_headers=None):
    headers = oss2.CaseInsensitiveDict({
        'Server': 'AliyunOSS',
        'Date': 'Fri, 11 Dec 2015 11:40:30 GMT',
        'Content-Length': '0',
        'Connection': 'keep-alive',
        'x-oss-request-id': '566AB62E9C30F8552526DADF',
        'ETag': '"E5831D5EBC7AAF5D6C0D20259FE141D2"'
    })

    merge_headers(headers, in_headers)

    return MockResponse(in_status, headers, b'')


def bucket():
    return oss2.Bucket(oss2.Auth('fake-access-key-id', 'fake-access-key-secret'),
                                  'http://oss-cn-hangzhou.aliyuncs.com', 'my-bucket')


class TestObject(unittest.TestCase):
    def setUp(self):
        self.previous = -1

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
        self.assertEqual(result.last_modified, _MTIME)

    @patch('oss2.Session.do_request')
    def test_get(self, do_request):
        size = 1023
        resp = r4get(size)
        do_request.return_value = resp

        result = bucket().get_object('fake-key')

        self.assertEqual(result.read(), resp.body)
        self.assertEqual(result.content_length, size)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, resp.headers['x-oss-request-id'])
        self.assertEqual(result.object_type, 'Normal')
        self.assertEqual(result.content_type, resp.headers['Content-Type'])
        self.assertEqual(result.etag, resp.headers['ETag'].strip('"'))
        self.assertEqual(result.last_modified, _MTIME)

    @patch('oss2.Session.do_request')
    def test_get_with_progress(self, do_request):
        size = 1024 * 1024 + 1
        resp = r4get(size)
        do_request.return_value = resp

        self.previous = -1
        result = bucket().get_object('fake-key', progress_callback=self.progress_callback)
        content = read_file(result)

        self.assertEqual(self.previous, size)
        self.assertEqual(len(content), size)
        self.assertEqual(content, resp.body)

    @patch('oss2.Session.do_request')
    def test_put_result(self, do_request):
        resp = r4put()
        do_request.return_value = resp

        result = bucket().put_object('fake-key', b'dummy content')

        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, resp.headers['x-oss-request-id'])
        self.assertEqual(result.etag, resp.headers['ETag'].strip('"'))

    @patch('oss2.Session.do_request')
    def test_put_bytes(self, do_request):
        content = random_bytes(1024 * 1024 - 1)
        body_dict = {}

        do_request.auto_spec = True
        do_request.side_effect = functools.partial(do4put, body_dict=body_dict, data_type=_BT_BYTES)

        bucket().put_object('fake-key', content)

        self.assertEqual(content, body_dict['data'])

    @patch('oss2.Session.do_request')
    def test_put_bytes_with_progress(self, do_request):
        self.previous = -1

        content = random_bytes(1024 * 1024 - 1)
        body_dict = {}

        do_request.auto_spec = True
        do_request.side_effect = functools.partial(do4put, body_dict=body_dict, data_type=_BT_FILE)

        bucket().put_object('fake-key', content, progress_callback=self.progress_callback)

        self.assertEqual(self.previous, len(content))
        self.assertEqual(len(content), len(body_dict['data']))
        self.assertEqual(content, body_dict['data'])

    @patch('oss2.Session.do_request')
    def test_delete(self, do_request):
        resp = r4delete()
        do_request.return_value = resp

        result = bucket().delete_object('fake-key')

        self.assertEqual(result.request_id, resp.headers['x-oss-request-id'])
        self.assertEqual(result.status, 204)