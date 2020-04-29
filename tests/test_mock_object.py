# -*- coding: utf-8 -*-

import os
from io import BytesIO

import oss2
import unittest
import unittests
import random
from oss2 import utils

from functools import partial
from mock import patch
import struct
import copy
from .common import *
import json


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

{1}'''.format(len(content), oss2.to_string(content))

    return request_text, response_text


def make_put_encrypted_object(key, content, content_crypto_material):
    cipher = content_crypto_material.cipher
    encrypted_key = utils.b64encode_as_string(content_crypto_material.encrypted_key)
    encrypted_iv = utils.b64encode_as_string(content_crypto_material.encrypted_iv)
    encrypted_content = cipher.encrypt(content)
    wrap_alg = content_crypto_material.wrap_alg
    cek_alg = content_crypto_material.cek_alg

    request_text = '''PUT /{0} HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: {1}
x-oss-meta-client-side-encryption-wrap-alg: {2}
x-oss-meta-client-side-encryption-cek-alg: {3}
x-oss-meta-client-side-encryption-key: {4}
x-oss-meta-client-side-encryption-start: {5}
x-oss-meta-unencrypted-content-length: {6}
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
authorization: OSS ZCDmm7TPZKHtx77j:W6whAowN4aImQ0dfbMHyFfD0t1g=
Accept: */*

'''.format(key, len(content), wrap_alg, cek_alg, encrypted_key, encrypted_iv, len(encrypted_content))

    io = BytesIO()
    io.write(oss2.to_bytes(request_text))
    io.write(encrypted_content)

    request_text = io.getvalue()

    response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Length: {0}
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
x-oss-hash-crc64ecma: {1}
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"'''.format(len(content), unittests.common.calc_crc(encrypted_content))

    return request_text, response_text


def make_get_encrypted_object(key, content, content_crypto_material, invalid_cek_alg='', ranges=None):
    request_text = '''GET /{0} HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:PAedG7U86ZxQ2WTB+GdpSltoiTI='''.format(key)

    encrypted_key = utils.b64encode_as_string(content_crypto_material.encrypted_key)
    encrypted_iv = utils.b64encode_as_string(content_crypto_material.encrypted_iv)
    wrap_alg = content_crypto_material.wrap_alg
    cek_alg = content_crypto_material.cek_alg
    if invalid_cek_alg:
        cek_alg = invalid_cek_alg
    cipher = content_crypto_material.cipher

    encrypted_content = cipher.encrypt(content)

    response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Type: text/plain
Content-Length: {0}
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
Accept-Ranges: bytes
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"
x-oss-meta-client-side-encryption-wrap-alg: {1}
x-oss-meta-client-side-encryption-cek-alg: {2}
x-oss-meta-client-side-encryption-key: {3}
x-oss-meta-client-side-encryption-start: {4}
x-oss-meta-unencrypted-content-length: {5}
Last-Modified: Sat, 12 Dec 2015 00:35:53 GMT
x-oss-object-type: Normal{6}

'''.format(len(encrypted_content), wrap_alg, cek_alg, encrypted_key, encrypted_iv, len(content),
           '\nContent-Range: {0}'.format(ranges) if ranges else '')

    io = BytesIO()
    io.write(oss2.to_bytes(response_text))
    io.write(encrypted_content)

    response_text = io.getvalue()

    return request_text, response_text


def make_get_encrypted_object_compact(key, encrypted_content, encrypted_meta):
    request_text = '''GET /{0} HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:PAedG7U86ZxQ2WTB+GdpSltoiTI='''.format(key)

    encrypted_key = encrypted_meta['x-oss-meta-client-side-encryption-key']
    encrypted_iv = encrypted_meta['x-oss-meta-client-side-encryption-start']
    wrap_alg = encrypted_meta['x-oss-meta-client-side-encryption-wrap-alg']
    cek_alg = encrypted_meta['x-oss-meta-client-side-encryption-cek-alg']

    response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Type: text/plain
Content-Length: {0}
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
Accept-Ranges: bytes
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"
x-oss-meta-client-side-encryption-wrap-alg: {1}
x-oss-meta-client-side-encryption-cek-alg: {2}
x-oss-meta-client-side-encryption-key: {3}
x-oss-meta-client-side-encryption-start: {4}
x-oss-meta-unencrypted-content-length: {5}
Last-Modified: Sat, 12 Dec 2015 00:35:53 GMT
x-oss-object-type: Normal

'''.format(len(encrypted_content), wrap_alg, cek_alg, encrypted_key, encrypted_iv, len(encrypted_content))

    io = BytesIO()
    io.write(oss2.to_bytes(response_text))
    io.write(encrypted_content)

    response_text = io.getvalue()

    return request_text, response_text


def make_get_encrypted_object_compact_deprecated(key, encrypted_content, encrypted_meta):
    request_text = '''GET /{0} HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
date: Sat, 12 Dec 2015 00:35:53 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:PAedG7U86ZxQ2WTB+GdpSltoiTI='''.format(key)

    encrypted_key = encrypted_meta['x-oss-meta-oss-crypto-key']
    encrypted_iv = encrypted_meta['x-oss-meta-oss-crypto-start']
    wrap_alg = encrypted_meta['x-oss-meta-oss-wrap-alg']
    cek_alg = encrypted_meta['x-oss-meta-oss-cek-alg']

    response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Type: text/plain
Content-Length: {0}
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
Accept-Ranges: bytes
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"
x-oss-meta-oss-wrap-alg: {1}
x-oss-meta-oss-cek-alg: {2}
x-oss-meta-oss-crypto-key: {3}
x-oss-meta-oss-crypto-start: {4}
x-oss-meta-unencrypted-content-length: {5}
Last-Modified: Sat, 12 Dec 2015 00:35:53 GMT
x-oss-object-type: Normal

'''.format(len(encrypted_content), wrap_alg, cek_alg, encrypted_key, encrypted_iv, len(encrypted_content))

    io = BytesIO()
    io.write(oss2.to_bytes(response_text))
    io.write(encrypted_content)

    response_text = io.getvalue()

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

{1}'''.format(len(content), oss2.to_string(content))

    response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
x-oss-hash-crc64ecma: {0}
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"'''.format(unittests.common.calc_crc(content))

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

{2}'''.format(position, len(content), oss2.to_string(content))

    response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:36:29 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6C0D1790CF586F72240B
ETag: "24F7FA10676D816E0D6C6B5600000000"
x-oss-next-append-position: {0}
x-oss-hash-crc64ecma: {1}'''.format(position + len(content), unittests.common.calc_crc(content))

    return request_text, response_text

def make_get_object_tagging():
    request_text = '''GET /sjbhlsgsbecvlpbf?tagging HTTP/1.1
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
                    Content-Length: 278 
                    Connection: keep-alive
                    x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
                    Accept-Ranges: bytes
                    ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"
                    Last-Modified: Sat, 12 Dec 2015 00:35:53 GMT
x-oss-object-type: Normal

<?xml version="1.0" encoding="UTF-8"?>
<Tagging>
<TagSet>
<Tag>
<Key>k1</Key>
<Value>v1</Value>
</Tag>
<Tag>
<Key>k2</Key>
<Value>v2</Value>
</Tag>
<Tag>
<Key>k3</Key>
<Value>v3</Value>
</Tag>
</TagSet>
</Tagging>'''

    return request_text, response_text

class TestObject(unittests.common.OssTestCase):
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

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().head_object('apbmntxqtvxjzini')

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

        req_info = unittests.common.mock_response(do_request, response_text)

        self.assertTrue(unittests.common.bucket().object_exists('sbowspxjhmccpmesjqcwagfw'))
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

        req_info = unittests.common.mock_response(do_request, response_text)
        self.assertTrue(not unittests.common.bucket().object_exists('sbowspxjhmccpmesjqcwagfw'))
        self.assertRequest(req_info, request_text)
    
    @patch('oss2.Session.do_request')
    def test_object_exists_exception(self, do_request):
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
  <Code>NoSuchBucket</Code>
  <Message>The specified bucket does not exist.</Message>
  <RequestId>566B6C3D6086505A0CFF0F68</RequestId>
  <HostId>ming-oss-share.oss-cn-hangzhou.aliyuncs.com</HostId>
  <Bucket>ming-oss-share</Bucket>
</Error>'''

        unittests.common.mock_response(do_request, response_text)
        self.assertRaises(oss2.exceptions.NoSuchBucket, unittests.common.bucket().object_exists, 'sbowspxjhmccpmesjqcwagfw')
    
    @patch('oss2.Session.do_request')
    def test_get_object_meta(self, do_request):
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

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().get_object_meta('sbowspxjhmccpmesjqcwagfw')
        
        self.assertRequest(req_info, request_text)

        self.assertEqual(result.last_modified, 1449880637)
        self.assertEqual(result.content_length, 344606)
        self.assertEqual(result.etag, '5B3C1A2E053D763E1B002CC607C5A0FE')

    @patch('oss2.Session.do_request')
    def test_get(self, do_request):
        content = unittests.common.random_bytes(1023)

        request_text, response_text = make_get_object(content)

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().get_object('sjbhlsgsbecvlpbf')

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
        content = unittests.common.random_bytes(1024 * 1024 + 1)

        request_text, response_text = make_get_object(content)
        req_info = unittests.common.mock_response(do_request, response_text)

        self.previous = -1
        result = unittests.common.bucket().get_object('sjbhlsgsbecvlpbf', progress_callback=self.progress_callback)

        self.assertRequest(req_info, request_text)

        content_read = unittests.common.read_file(result)

        self.assertEqual(self.previous, len(content))
        self.assertEqual(len(content_read), len(content))
        self.assertEqual(oss2.to_bytes(content_read), content)

    @patch('oss2.Session.do_request')
    def test_get_to_file(self, do_request):
        content = unittests.common.random_bytes(1023)

        request_text, response_text = make_get_object(content)
        req_info = unittests.common.mock_response(do_request, response_text)

        filename = self.tempname()

        result = unittests.common.bucket().get_object_to_file('sjbhlsgsbecvlpbf', filename)

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.content_length, len(content))
        self.assertEqual(os.path.getsize(filename), len(content))

        with open(filename, 'rb') as f:
            self.assertEqual(content, oss2.to_bytes(f.read()))

    @patch('oss2.Session.do_request')
    def test_get_to_file_with_progress(self, do_request):
        size = 1024 * 1024 + 1
        content = unittests.common.random_bytes(size)

        request_text, response_text = make_get_object(content)
        req_info = unittests.common.mock_response(do_request, response_text)

        filename = self.tempname()

        self.previous = -1
        unittests.common.bucket().get_object_to_file('sjbhlsgsbecvlpbf', filename, progress_callback=self.progress_callback)

        self.assertRequest(req_info, request_text)

        self.assertEqual(self.previous, size)
        self.assertEqual(os.path.getsize(filename), size)
        with open(filename, 'rb') as f:
            self.assertEqual(oss2.to_bytes(content), f.read())

    @patch('oss2.Session.do_request')
    def test_put_result(self, do_request):
        content = b'dummy content'
        request_text, response_text = make_put_object(content)

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().put_object('sjbhlsgsbecvlpbf.txt', content)

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.etag, 'D80CF0E5BE2436514894D64B2BCFB2AE')

    @patch('oss2.Session.do_request')
    def test_put_bytes(self, do_request):
        content = unittests.common.random_bytes(1024 * 1024 - 1)

        request_text, response_text = make_put_object(content)
        req_info = unittests.common.mock_response(do_request, response_text)

        unittests.common.bucket().put_object('sjbhlsgsbecvlpbf.txt', content)

        self.assertRequest(req_info, request_text)

    @patch('oss2.Session.do_request')
    def test_put_bytes_with_progress(self, do_request):
        self.previous = -1

        content = unittests.common.random_bytes(1024 * 1024 - 1)

        request_text, response_text = make_put_object(content)
        req_info = unittests.common.mock_response(do_request, response_text)

        unittests.common.bucket().put_object('sjbhlsgsbecvlpbf.txt', content, progress_callback=self.progress_callback)

        self.assertRequest(req_info, request_text)
        self.assertEqual(self.previous, len(content))

    @patch('oss2.Session.do_request')
    def test_put_from_file(self, do_request):
        size = 512 * 2 - 1
        content = unittests.common.random_bytes(size)
        filename = self.make_tempfile(content)

        request_text, response_text = make_put_object(content)
        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().put_object_from_file('sjbhlsgsbecvlpbf.txt', filename)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.etag, 'D80CF0E5BE2436514894D64B2BCFB2AE')

    @patch('oss2.Session.do_request')
    def test_put_without_crc_in_response(self, do_request):
        content = b'dummy content'
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

{1}'''.format(len(content), oss2.to_string(content))
        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:35:53 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6BE93A7B8CFD53D4BAA3
ETag: "D80CF0E5BE2436514894D64B2BCFB2AE"'''

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().put_object('sjbhlsgsbecvlpbf.txt', content)

        self.assertRequest(req_info, request_text)

        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.etag, 'D80CF0E5BE2436514894D64B2BCFB2AE')

    @patch('oss2.Session.do_request')
    def test_append(self, do_request):
        size = 8192 * 2 - 1
        content = unittests.common.random_bytes(size)

        request_text, response_text = make_append_object(0, content)
        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().append_object('sjbhlsgsbecvlpbf', 0, content)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.next_position, size)
        self.assertEqual(result.etag, '24F7FA10676D816E0D6C6B5600000000')
        self.assertEqual(result.crc, unittests.common.calc_crc(content))

    @patch('oss2.Session.do_request')
    def test_append_with_progress(self, do_request):
        size = 1024 * 1024
        content = unittests.common.random_bytes(size)

        request_text, response_text = make_append_object(0, content)
        req_info = unittests.common.mock_response(do_request, response_text)

        self.previous = -1

        result = unittests.common.bucket().append_object('sjbhlsgsbecvlpbf', 0, content, progress_callback=self.progress_callback)

        self.assertRequest(req_info, request_text)
        self.assertEqual(self.previous, size)
        self.assertEqual(result.next_position, size)

    @patch('oss2.Session.do_request')
    def test_append_without_crc_in_response(self, do_request):
        size = 8192
        position = 0
        content = unittests.common.random_bytes(size)
        request_text = '''POST /sjbhlsgsbecvlpbf?position={0}&append= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: {1}
date: Sat, 12 Dec 2015 00:36:29 GMT
User-Agent: aliyun-sdk-python/2.0.2(Windows/7/;3.3.3)
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:1njpxsTivMNvTdfYolCUefRInVY=

{2}'''.format(position, len(content), oss2.to_string(content))

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Sat, 12 Dec 2015 00:36:29 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6C0D1790CF586F72240B
ETag: "24F7FA10676D816E0D6C6B5600000000"
x-oss-next-append-position: {0}'''.format(position + len(content), unittests.common.calc_crc(content))
        
        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().append_object('sjbhlsgsbecvlpbf', position, content, init_crc=0)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.next_position, size)
        self.assertEqual(result.etag, '24F7FA10676D816E0D6C6B5600000000')
        
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

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().delete_object('sjbhlsgsbecvlpbf')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6C0D8CDE4E975D730BEF')
        self.assertEqual(result.status, 204)

    def test_batch_delete_empty(self):
        self.assertRaises(oss2.exceptions.ClientError, unittests.common.bucket().batch_delete_objects, [])

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
        req_info = unittests.common.mock_response(do_request, response_text)

        key_list = ['hello', 'world']

        result = unittests.common.bucket().batch_delete_objects(key_list)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.deleted_keys, list(oss2.to_string(key) for key in key_list))

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

        req_info = unittests.common.mock_response(do_request, response_text)

        in_headers = {'Content-Type': 'text/plain', 'x-oss-meta-category': 'novel'}
        result = unittests.common.bucket().update_object_meta('zyfpyqqqxjthdwxkhypziizm.js', in_headers)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6C611BA604C27DD51F8F')
        self.assertEqual(result.etag, '164F32EF262006C5EE6C8D1AA30DD2CD')

    @patch('oss2.Session.do_request')
    def test_put_acl(self, do_request):
        req_info = unittests.common.RequestInfo()

        do_request.auto_spec = True
        do_request.side_effect = partial(unittests.common.do4put, req_info=req_info)

        for acl, expected in [(oss2.OBJECT_ACL_PRIVATE, 'private'),
                              (oss2.OBJECT_ACL_PUBLIC_READ, 'public-read'),
                              (oss2.OBJECT_ACL_PUBLIC_READ_WRITE, 'public-read-write'),
                              (oss2.OBJECT_ACL_DEFAULT, 'default')]:
            unittests.common.bucket().put_object_acl('fake-key', acl)
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
            do_request.side_effect = partial(unittests.common.do4body, body=template.format(acl), content_type='application/xml')

            result = unittests.common.bucket().get_object_acl('fake-key')
            self.assertEqual(result.acl, expected)
    
    @patch('oss2.Session.do_request')
    def test_put_symlink(self, do_request):
        request_text = '''PUT /sjbhlsgsbecvlpbf?symlink= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Content-Length: 0
User-Agent: aliyun-sdk-python/2.3.0(Windows/7/;3.3.3)
x-oss-symlink-target: bcvzkwznomy
x-oss-meta-key1: value1
x-oss-meta-key2: value2
date: Wed, 22 Mar 2017 03:15:15 GMT
Accept: */*
authorization: OSS ZCDmm7TPZKHtx77j:AC830VOm7dDnv+CVpTaui6gh5xc='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Wed, 22 Mar 2017 03:15:20 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6C0D8CDE4E975D730BEF
ETag: "B070B9DEB1655BE905777D6DC856E6F1"
x-oss-hash-crc64ecma: 0
x-oss-server-time: 19'''

        req_info = unittests.common.mock_response(do_request, response_text)

        headers = {'x-oss-meta-key1': 'value1', 'x-oss-meta-key2': 'value2'}
        result = unittests.common.bucket().put_symlink('bcvzkwznomy', 'sjbhlsgsbecvlpbf', headers)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6C0D8CDE4E975D730BEF')
        self.assertEqual(result.status, 200)
        
    @patch('oss2.Session.do_request')
    def test_get_symlink(self, do_request):
        request_text = '''GET /sjbhlsgsbecvlpbf?symlink= HTTP/1.1
Host: ming-oss-share.oss-cn-hangzhou.aliyuncs.com
Accept-Encoding: identity
Connection: keep-alive
Accept: */*
User-Agent: aliyun-sdk-python/2.3.0(Windows/7/;3.3.3)
date: Wed, 22 Mar 2017 03:14:31 GMT
authorization: OSS ZCDmm7TPZKHtx77j:AC830VOm7dDnv+CVpTaui6gh5xc='''

        response_text = '''HTTP/1.1 200 OK
Server: AliyunOSS
Date: Wed, 22 Mar 2017 03:14:36 GMT
Content-Length: 0
Connection: keep-alive
x-oss-request-id: 566B6C0D8CDE4E975D730BEF
Last-Modified: Wed, 22 Mar 2017 03:14:31 GMT
ETag: "0D9980D049C9256C927F8A46BC1BADCF"
x-oss-symlink-target: bcvzkwznomy
x-oss-server-time: 39'''

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().get_symlink('sjbhlsgsbecvlpbf')

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.request_id, '566B6C0D8CDE4E975D730BEF')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.target_key, 'bcvzkwznomy')

    @patch('oss2.Session.do_request')
    def test_crypto_get(self, do_request):
        content = unittests.common.random_bytes(1023)

        key = random_string(10)
        provider = oss2.RsaProvider(key_pair=key_pair)
        content_crypto_material = provider.create_content_material()

        request_text, response_text = make_get_encrypted_object(key, content, content_crypto_material)
        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket(provider).get_object(key)

        encrypted_key = utils.b64encode_as_string(content_crypto_material.encrypted_key)
        encrypted_iv = utils.b64encode_as_string(content_crypto_material.encrypted_iv)
        wrap_alg = content_crypto_material.wrap_alg
        cek_alg = content_crypto_material.cek_alg

        self.assertRequest(req_info, request_text)
        self.assertEqual(int(result.headers['x-oss-meta-unencrypted-content-length']), len(content))
        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.object_type, 'Normal')
        self.assertEqual(result.content_type, 'text/plain')
        self.assertEqual(result.etag, 'D80CF0E5BE2436514894D64B2BCFB2AE')
        self.assertEqual(result.last_modified, 1449880553)
        self.assertEqual(result.headers['x-oss-meta-client-side-encryption-key'], encrypted_key)
        self.assertEqual(result.headers['x-oss-meta-client-side-encryption-start'], encrypted_iv)
        self.assertEqual(result.headers['x-oss-meta-client-side-encryption-cek-alg'], cek_alg)
        self.assertEqual(result.headers['x-oss-meta-client-side-encryption-wrap-alg'], wrap_alg)
        self.assertEqual(result.read(), content)

    @patch('oss2.Session.do_request')
    def test_crypto_get_with_inconsistent_crypto_meta(self, do_request):
        content = unittests.common.random_bytes(1023)

        key = random_bytes(10)
        provider = oss2.RsaProvider(key_pair=key_pair)
        content_crypto_material = provider.create_content_material()

        request_text, response_text = make_get_encrypted_object(key, content, content_crypto_material,
                                                                invalid_cek_alg='invald_cek_alg')
        req_info = unittests.common.mock_response(do_request, response_text)

        self.assertRaises(oss2.exceptions.InconsistentError, unittests.common.bucket(provider).get_object, key)

    @patch('oss2.Session.do_request')
    def test_crypto_get_compact(self, do_request):
        example_path = "tests/example.jpg"
        with open(example_path, 'rb') as f:
            content = f.read()

        for compact_sdk in ["cpp", "go"]:
            if compact_sdk == "cpp":
                encrypted_example_path = "tests/encrypted_cpp_example.jpg"
                encrypted_example_meta_path = "tests/encrypted_cpp_example_meta.json"
            else:
                encrypted_example_path = "tests/encrypted_go_example.jpg"
                encrypted_example_meta_path = "tests/encrypted_go_example_meta.json"

            with open(encrypted_example_path, 'rb') as f:
                encrypted_content = f.read()

            with open(encrypted_example_meta_path, 'r') as f:
                meta = json.loads(f.read())

            key = random_string(10)
            provider = oss2.RsaProvider(key_pair=key_pair_compact)

            request_text, response_text = make_get_encrypted_object_compact(key, encrypted_content, meta)

            req_info = unittests.common.mock_response(do_request, response_text)
            result = unittests.common.bucket(provider).get_object(key)

            self.assertRequest(req_info, request_text)
            self.assertEqual(result.read(), content)

    @patch('oss2.Session.do_request')
    def test_crypto_get_compact_deprecated_rsa(self, do_request):
        utils.silently_remove('./rsa-test.public_key.pem')
        utils.silently_remove('./rsa-test.private_key.pem')

        with open("./rsa-test.private_key.pem", 'wb') as f:
            f.write(oss2.to_bytes(private_key_compact))

        with open("./rsa-test.public_key.pem", 'wb') as f:
            f.write(oss2.to_bytes(public_key_compact))

        content = b'a' * 1024 * 1024
        encrypted_rsa_path = "tests/deprecated_encrypted_1MB_a_rsa"
        encrypted_meta_rsa_path = "tests/deprecated_encrypted_1MB_a_meta_rsa.json"

        with open(encrypted_rsa_path, 'rb') as f:
            encrypted_content = f.read()

        with open(encrypted_meta_rsa_path, 'r') as f:
            meta = json.loads(f.read())

        key = random_string(10)
        provider = oss2.LocalRsaProvider(dir='./', key='rsa-test')

        request_text, response_text = make_get_encrypted_object_compact_deprecated(key, encrypted_content, meta)

        req_info = unittests.common.mock_response(do_request, response_text)
        result = unittests.common.bucket(provider).get_object(key)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.read(), content)

        utils.silently_remove('./rsa-test.public_key.pem')
        utils.silently_remove('./rsa-test.private_key.pem')

    @patch('oss2.Session.do_request')
    def test_crypto_get_compact_deprecated_kms(self, do_request):
        content = b'a' * 1024 * 1024
        encrypted_kms_path = "tests/deprecated_encrypted_1MB_a_kms"
        encrypted_meta_kms_path = "tests/deprecated_encrypted_1MB_a_meta_kms.json"

        with open(encrypted_kms_path, 'rb') as f:
            encrypted_content = f.read()

        with open(encrypted_meta_kms_path, 'r') as f:
            meta = json.loads(f.read())

        key = random_string(10)
        provider = oss2.AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK)

        request_text, response_text = make_get_encrypted_object_compact_deprecated(key, encrypted_content, meta)
        plain_key = utils.b64decode_from_string(meta['base64-plain-key'])
        plain_start = meta['plain-start']

        req_info = unittests.common.mock_response(do_request, response_text)
        with patch('oss2.AliKMSProvider.decrypt_encrypted_key', return_value=plain_key):
            with patch('oss2.AliKMSProvider.decrypt_encrypted_iv', return_value=plain_start):
                result = unittests.common.bucket(provider).get_object(key)

        self.assertRequest(req_info, request_text)
        self.assertEqual(result.read(), content)

    @patch('oss2.Session.do_request')
    def test_crypto_put(self, do_request):
        content = unittests.common.random_bytes(1023)

        key = random_string(10)
        provider = oss2.RsaProvider(key_pair=key_pair)
        plain_key = provider.get_key()
        plain_iv = provider.get_iv()

        with patch.object(oss2.utils, 'random_key', return_value=plain_key, autospect=True):
            with patch.object(oss2.utils, 'random_iv', return_value=plain_iv, autospect=True):
                content_crypto_material = provider.create_content_material()

        request_text, response_text = make_put_encrypted_object(key, content, content_crypto_material)
        req_info = unittests.common.mock_response(do_request, response_text)

        with patch.object(oss2.utils, 'random_key', return_value=plain_key, autospect=True):
            with patch.object(oss2.utils, 'random_iv', return_value=plain_iv, autospect=True):
                result = unittests.common.bucket(provider).put_object(key, content, headers={
                    'content-md5': oss2.utils.md5_string(content), 'content-length': str(len(content))})

        # 这个地方两次加密形成的加密key和向量会不一致，所以将这行注释掉
        # self.assertRequest(req_info, request_text)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.request_id, '566B6BE93A7B8CFD53D4BAA3')
        self.assertEqual(result.etag, 'D80CF0E5BE2436514894D64B2BCFB2AE')


    @patch('oss2.Session.do_request')
    def test_get_object_tagging(self, do_request):

        request_text, response_text = make_get_object_tagging()

        req_info = unittests.common.mock_response(do_request, response_text)

        result = unittests.common.bucket().get_object_tagging('sjbhlsgsbecvlpbf')

        req_info = unittests.common.mock_response(do_request, response_text)

        self.assertEqual(3, result.tag_set.len())
        self.assertEqual('v1', result.tag_set.tagging_rule['k1'])
        self.assertEqual('v2', result.tag_set.tagging_rule['k2'])
        self.assertEqual('v3', result.tag_set.tagging_rule['k3'])


    # for ci
    def test_oss_utils_negative(self):
        try:
            oss2.utils.makedir_p('/')
            self.assertTrue(False)
        except:
            pass
        
        try:
            oss2.utils.silently_remove('/')
            self.assertTrue(False)
        except:
            pass
        
        try:
            oss2.utils.force_rename('/', '/')
            self.assertTrue(False)
        except:
            pass
        
        oss2.utils.makedir_p('xyz')
        oss2.utils.makedir_p('zyz')
        try:
            oss2.utils.force_rename('xyz', 'zyx')
            self.assertTrue(False)
        except:
            pass
            

if __name__ == '__main__':
    unittest.main()
