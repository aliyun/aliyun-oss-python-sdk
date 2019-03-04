# -*- coding: utf-8 -*-

import random
import string
import unittest
import tempfile
import os
import io
import functools
import re

import xml
from xml.dom import minidom

import shutil

import oss2

DT_NONE = 0
DT_BYTES = 1
DT_FILE = 2

CHUNK_SIZE = 8192

BUCKET_NAME = 'ming-oss-share'


def random_string(n):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(n))


def random_bytes(n):
    return oss2.to_bytes(random_string(n))


def bucket(crypto_provider=None):
    if crypto_provider:
        return oss2.CryptoBucket(oss2.Auth('fake-access-key-id', 'fake-access-key-secret'),
                       'http://oss-cn-hangzhou.aliyuncs.com', BUCKET_NAME,
                       crypto_provider=crypto_provider)
    else:
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


def is_string_type(obj):
    if oss2.compat.is_py2:
        return isinstance(obj, (str, bytes, unicode))
    else:
        return isinstance(obj, (str, bytes))


def do4response(req, timeout, req_info=None, payload=None):
    if req_info:
        req_info.req = req

        if req.data is None:
            req_info.data = b''
            req_info.size = 0
        elif is_string_type(req.data):
            req_info.data = oss2.to_bytes(req.data)
            req_info.size = len(req_info.data)
        else:
            req_info.data = read_data(req.data, DT_FILE)
            req_info.size = get_length(req.data)

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


def calc_crc(data):
    crc = oss2.utils.Crc64()
    crc.update(data)
    return crc.crc


class MockSocket(object):
    def __init__(self, payload):
        self._file = io.BytesIO(payload)

    def makefile(self, *args, **kwargs):
        return self._file


def mock_response(do_request, payload):
    req_info = RequestInfo()

    do_request.auto_spec = True
    do_request.side_effect = functools.partial(do4response, req_info=req_info, payload=payload)

    return req_info


class MockResponse(object):
    def __init__(self, status, headers, body):
        self.status = status
        self.headers = oss2.CaseInsensitiveDict(headers)
        self.body = oss2.to_bytes(body)
        self.request_id = headers.get('x-oss-request-id', '')

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


def query_to_params(query):
    params = {}
    for kv_pair in query.split('&'):
        kv = kv_pair.split('=', 1)
        if len(kv) == 2:
            params[kv[0]] = kv[1]
        else:
            params[kv[0]] = ''

    return params


def head_fields_to_headers(head_fields):
    headers = oss2.CaseInsensitiveDict()
    for header_kv in head_fields:
        kv = header_kv.split(':', 1)
        if len(kv) == 2:
            headers[kv[0].strip()] = kv[1].strip()
        else:
            headers[kv[0].strip()] = ''

    return headers


class MockRequest(object):
    def __init__(self, request_text):
        if isinstance(request_text, bytes):
            fields = re.split(b'\n\n', request_text, 1)
        else:
            fields = re.split('\n\n', request_text, 1)
        head_fields = re.split('\n', oss2.to_string(fields[0]))
        request_line_fields = head_fields[0].split()

        uri_query_fields = request_line_fields[1].split('?')
        if len(uri_query_fields) == 2:
            self.params = query_to_params(uri_query_fields[1])
        else:
            self.params = {}

        if len(fields) == 2:
            self.body = oss2.to_bytes(fields[1])
        else:
            self.body = b''

        self.method = request_line_fields[0]
        self.headers = head_fields_to_headers(head_fields[1:])
        self.url = 'http://' + self.headers['host'] + uri_query_fields[0]


class MockResponse2(object):
    def __init__(self, response_text):
        if isinstance(response_text, bytes):
            fields = re.split(b'\n\n', response_text, 1)
        else:
            fields = re.split('\n\n', response_text, 1)
        head_fields = re.split('\n', oss2.to_string(fields[0]))
        response_line_fields = head_fields[0].split(' ', 2)

        self.status = int(response_line_fields[1])
        self.headers = head_fields_to_headers(head_fields[1:])
        self.request_id = self.headers.get('x-oss-request-id', '')

        if len(fields) == 2:
            self.body = oss2.to_bytes(fields[1])
        else:
            self.body = b''

        self.__io = io.BytesIO(self.body)

    def read(self, amt=None):
        return self.__io.read(amt)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        return self.read(8192)


def _is_xml(content):
    try:
        minidom.parseString(content)
    except xml.parsers.expat.ExpatError:
        return False
    else:
        return True


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

        dest = os.path.join(os.path.expanduser('~'), oss2.crypto._LOCAL_RSA_TMP_DIR)

        oss2.utils.makedir_p(dest)
        shutil.copy('tests/oss-test.private_key.pem', dest)
        shutil.copy('tests/oss-test.public_key.pem', dest)

    def tearDown(self):
        for temp_file in self.temp_files:
            os.remove(temp_file)

    def tempname(self):
        random_name = random_string(16)
        self.temp_files.append(random_name)

        return random_name

    def make_tempfile(self, content):
        fd, pathname = tempfile.mkstemp(suffix='test-upload')

        os.write(fd, oss2.to_bytes(content))
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
        a = a.translate(None, b'\r\n')
        b = b.translate(None, b'\r\n')

        normalized_a = minidom.parseString(oss2.to_bytes(a)).toxml(encoding='utf-8')
        normalized_b = minidom.parseString(oss2.to_bytes(b)).toxml(encoding='utf-8')

        self.assertEqual(normalized_a, normalized_b)

    def assertUrlWithKey(self, url, key):
        self.assertEqual('http://my-bucket.oss-cn-hangzhou.aliyuncs.com/' + key, url)

    def assertRequest(self, req_info, request_text):
        req = req_info.req

        expected = MockRequest(request_text)

        self.assertEqual(req.method, expected.method)
        self.assertEqual(req.url, expected.url)

        for k, v in expected.params.items():
            self.assertTrue(k in req.params)
            self.assertEqual(req.params[k], v)

        if 'Content-Type' in expected.headers:
            self.assertEqual(req.headers.get('Content-Type'), expected.headers['Content-Type'])

        for k, v in expected.headers.items():
            if k.startswith('x-oss-'):
                self.assertEqual(req.headers.get(k), expected.headers[k])

        if _is_xml(expected.body):
            self.assertXmlEqual(req_info.data, expected.body)
        else:
            self.assertEqual(len(req_info.data), len(expected.body))
            self.assertEqual(req_info.data, expected.body)


fixed_aes_key = b'1' * 32
fixed_aes_start = 1

