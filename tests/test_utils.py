# -*- coding: utf-8 -*-

import unittest

import oss2
from oss2.exceptions import make_exception

import os
import sys
import tempfile

from common import *


is_py2 = (sys.version_info[0] == 2)
is_py3 = (sys.version_info[0] == 3)


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)
        self.bucket.create_bucket()

    def test_is_ip(self):
        self.assertTrue(oss2.utils.is_ip_or_localhost('1.2.3.4'))
        self.assertTrue(oss2.utils.is_ip_or_localhost('localhost'))

        self.assertTrue(not oss2.utils.is_ip_or_localhost('-1.2.3.4'))
        self.assertTrue(not oss2.utils.is_ip_or_localhost('1.256.1.2'))
        self.assertTrue(not oss2.utils.is_ip_or_localhost('一.二.三.四'))

    def test_is_valid_bucket_name(self):
        self.assertTrue(oss2.is_valid_bucket_name('abc'))
        self.assertTrue(oss2.is_valid_bucket_name('hello-world'))

        self.assertTrue(not oss2.is_valid_bucket_name('HELLO'))
        self.assertTrue(not oss2.is_valid_bucket_name('hello_world'))
        self.assertTrue(not oss2.is_valid_bucket_name('hello-'))
        self.assertTrue(not oss2.is_valid_bucket_name('-hello'))

    def test_compat(self):
        # from unicode
        u = u'中文'

        self.assertEqual(u, oss2.to_unicode(u))
        self.assertEqual(u.encode('utf-8'), oss2.to_bytes(u))

        if is_py2:
            self.assertEqual(u.encode('utf-8'), oss2.to_string(u))

        if is_py3:
            self.assertEqual(u, oss2.to_string(u))

        # from bytes
        b = u.encode('utf-8')

        self.assertEqual(b.decode('utf-8'), oss2.to_unicode(b))
        self.assertEqual(b, oss2.to_bytes(b))

        if is_py2:
            self.assertEqual(b, oss2.to_string(b))

        if is_py3:
            self.assertEqual(b.decode('utf-8'), oss2.to_string(b))

    def test_makedir_p(self):
        tempdir = tempfile.gettempdir()

        dirpath = os.path.join(tempdir, random_string(10))

        oss2.utils.makedir_p(dirpath)
        os.path.isdir(dirpath)

        # recreate same dir should not issue an error
        oss2.utils.makedir_p(dirpath)

    def __fake_response(self, status, error_body):
        key = random_string(16)

        self.bucket.put_object(key, oss2.to_bytes(error_body))
        resp = self.bucket.get_object(key).resp
        resp.status = status

        return resp

    def test_make_exception(self):
        body = 'bad body'
        e = make_exception(self.__fake_response(400, body))
        self.assertTrue(isinstance(e, oss2.exceptions.ServerError))
        self.assertEqual(e.status, 400)
        self.assertEqual(e.body, oss2.to_bytes(body))

        body = '<Error><Code>NoSuchKey</Code><Message>中文和控制字符&#12;</Message></Error>'
        e = make_exception(self.__fake_response(404, body))
        self.assertTrue(isinstance(e, oss2.exceptions.NoSuchKey))
        self.assertEqual(e.status, 404)
        self.assertEqual(e.code, 'NoSuchKey')