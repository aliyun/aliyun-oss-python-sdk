# -*- coding: utf-8 -*-

import random
import string
import unittest
import tempfile
import os
import httplib
import io
import functools

from xml.dom import minidom

import oss2

DT_NONE = 0
DT_BYTES = 1
DT_FILE = 2

CHUNK_SIZE = 8192

BUCKET_NAME = 'my-bucket'


def random_string(n):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(n))


def random_bytes(n):
    return oss2.to_bytes(random_string(n))


def bucket():
    return oss2.Bucket(oss2.Auth('fake-access-key-id', 'fake-access-key-secret'),
                                  'http://oss-cn-hangzhou.aliyuncs.com', BUCKET_NAME)


def service():
    return oss2.Service(oss2.Auth('fake-access-key-id', 'fake-access-key-secret'),
                        'http://oss-cn-hangzhou.aliyuncs.com')


class RequestInfo(object):
    def __init__(self):
        self.req = None
        self.data = None
        self.resp = None
        self.size = None


MTIME_STRING = 'Fri, 11 Dec 2015 13:01:41 GMT'
MTIME = 1449838901
REQUEST_ID = '566AB62EB06147681C283D73'
ETAG = '7AE1A589ED6B161CAD94ACDB98206DA6'

RAW_ETAG = '"' + ETAG + '"'


def merge_headers(dst, src):
    if not src:
        return

    for k, v in src.items():
        dst[k] = v


def r4delete(in_status=204, in_headers=None):
    headers = oss2.CaseInsensitiveDict({
        'Server': 'AliyunOSS',
        'Date': 'Fri, 11 Dec 2015 11:40:31 GMT',
        'Content-Length': '0',
        'Connection': 'keep-alive',
        'x-oss-request-id': REQUEST_ID
    })

    merge_headers(headers, in_headers)
    return MockResponse(in_status, headers, b'')


def r4head(length, in_status=200, in_headers=None):
    headers = oss2.CaseInsensitiveDict({
        'Server': 'AliyunOSS',
        'Date': 'Fri, 11 Dec 2015 11:40:31 GMT',
        'Content-Type': 'application/javascript',
        'Content-Length': str(length),
        'Connection': 'keep-alive',
        'Vary': 'Accept-Encoding',
        'x-oss-request-id': REQUEST_ID,
        'Accept-Ranges': 'bytes',
        'ETag': RAW_ETAG,
        'Last-Modified': MTIME_STRING,
        'x-oss-object-type': 'Normal'
    })

    merge_headers(headers, in_headers)

    return MockResponse(in_status, headers, b'')


def r4get(body, in_status=200, in_headers=None):
    resp = r4head(len(body), in_status=in_status, in_headers=in_headers)
    resp.body = body

    return resp


def r4put(in_status=200, in_headers=None):
    headers = oss2.CaseInsensitiveDict({
        'Server': 'AliyunOSS',
        'Date': 'Fri, 11 Dec 2015 11:40:30 GMT',
        'Content-Length': '0',
        'Connection': 'keep-alive',
        'x-oss-request-id': REQUEST_ID
    })

    merge_headers(headers, in_headers)

    return MockResponse(in_status, headers, b'')


def r4copy():
    body = '''
    <?xml version="1.0" encoding="UTF-8"?>
    <CopyObjectResult>
        <ETag>"{0}"</ETag>
        <LastModified>2015-12-12T00:36:29.000Z</LastModified>
    </CopyObjectResult>
    '''.format(RAW_ETAG)

    headers = oss2.CaseInsensitiveDict({
        'Server': 'AliyunOSS',
        'Date': 'Fri, 11 Dec 2015 11:40:30 GMT',
        'Content-Length': len(body),
        'Connection': 'keep-alive',
        'x-oss-request-id': REQUEST_ID,
        'ETag': RAW_ETAG
    })

    return MockResponse(200, headers, body)


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


class NonlocalObject(object):
    def __init__(self, value):
        self.var = value


def make_do4body(req_infos=None, body_list=None):
    if req_infos is None:
        req_infos = [None] * len(body_list)

    i = NonlocalObject(0)

    def do4body_func(req, timeout):
        result = do4body(req, timeout,
                         req_info=req_infos[i.var],
                         body=body_list[i.var])
        i.var += 1
        return result

    return do4body_func


def do4response(req, timeout, req_info=None, data_type=DT_NONE, payload=None):
    if req_info:
        req_info.req = req

        if data_type != DT_NONE:
            req_info.size = get_length(req.data)
            req_info.data = read_data(req.data, data_type)

    return MockResponse2(payload)


def do4put(req, timeout, in_headers=None, req_info=None, data_type=DT_BYTES):
    resp = r4put(in_headers=in_headers)

    if req_info:
        req_info.req = req
        req_info.resp = resp
        req_info.size = get_length(req.data)
        req_info.data = read_data(req.data, data_type)

    return resp


def do4delete(req, timeout, in_headers=None, req_info=None):
    resp = r4delete(204, in_headers)
    if req_info:
        req_info.req = req
        req_info.resp = resp

    return resp


def do4put_object(req, timeout, req_info=None, data_type=DT_BYTES):
    return do4put(req, timeout,
                  in_headers={'ETag': '"E5831D5EBC7AAF5D6C0D20259FE141D2"'},
                  req_info=req_info,
                  data_type=data_type)


def do4copy(req, timeout, req_info=None):
    resp = r4copy()

    if req_info:
        req_info.req = req
        req_info.resp = resp
        req_info.size = get_length(req.data)
        req_info.data = read_data(req.data, DT_BYTES)

    return resp


def read_file(fileobj):
    result = b''

    while True:
        content = fileobj.read(CHUNK_SIZE)
        if content:
            result += content
        else:
            return result


def read_data(data, data_type):
    if data_type == DT_BYTES:
        return data
    elif data_type == DT_FILE:
        return read_file(data)
    else:
        raise RuntimeError('wrong data type: {0}'.format(data_type))


def get_length(data):
    try:
        return len(data)
    except TypeError:
        return None


class MockSocket(object):
    def __init__(self, payload):
        self._file = io.BytesIO(payload)

    def makefile(self, *args, **kwargs):
        return self._file


class MockResponse2(object):
    def __init__(self, http_payload):
        resp = httplib.HTTPResponse(MockSocket(oss2.to_bytes(http_payload)))
        resp.begin()

        self.status = resp.status
        self.headers = oss2.CaseInsensitiveDict(resp.getheaders())

        self._resp = resp

    def read(self, amt=None):
        return self._resp.read(amt)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        return self.read(8192)


def mock_do_request(do_request, payload, data_type=DT_NONE):
    req_info = RequestInfo()

    do_request.auto_spec = True
    do_request.side_effect = functools.partial(do4response, req_info=req_info, payload=payload, data_type=data_type)

    return req_info


class MockResponse(object):
    def __init__(self, status, headers, body):
        self.status = status
        self.headers = oss2.CaseInsensitiveDict(headers)
        self.body = oss2.to_bytes(body)

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


class OssTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(OssTestCase, self).__init__(*args, **kwargs)
        self.default_connect_timeout = oss2.defaults.connect_timeout
        self.default_request_retries = oss2.defaults.request_retries
        self.default_multipart_threshold = oss2.defaults.multipart_threshold
        self.default_part_size = oss2.defaults.part_size

    def setUp(self):
        oss2.defaults.connect_timeout = self.default_connect_timeout
        oss2.defaults.request_retries = self.default_request_retries
        oss2.defaults.multipart_threshold = self.default_multipart_threshold
        oss2.defaults.part_size = self.default_part_size

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

    def assertSortedListEqual(self, a, b, key=None):
        self.assertEqual(sorted(a, key=key), sorted(b, key=key))

    def assertXmlEqual(self, a, b):
        normalized_a = minidom.parseString(oss2.to_bytes(a)).toxml(encoding='utf-8')
        normalized_b = minidom.parseString(oss2.to_bytes(b)).toxml(encoding='utf-8')

        self.assertEqual(normalized_a, normalized_b)

    def assertUrlWithKey(self, url, key):
        self.assertEqual('http://my-bucket.oss-cn-hangzhou.aliyuncs.com/' + key, url)
