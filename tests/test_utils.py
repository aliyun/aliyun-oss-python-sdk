# -*- coding: utf-8 -*-

import unittest

import oss2
from oss2.exceptions import make_exception

import os
import sys
import tempfile
import requests

from common import *

import logging


is_py2 = (sys.version_info[0] == 2)
is_py3 = (sys.version_info[0] == 3)


class TestUtils(OssTestCase):
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
        key = self.random_key()

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

    def test_len(self):
        adapter = oss2.utils.SizedFileAdapter('ss', 2500000000)
        self.assertEqual(requests.utils.super_len(adapter), 2500000000)

        adapter = oss2.utils._BytesAndFileAdapter('ss', size=2500000000)
        self.assertEqual(requests.utils.super_len(adapter), 2500000000)

    def test_adapter_composition(self):
        def progress_callback(consumed_bytes, total_bytes):
            pass

        crc_adapter = oss2.utils.make_crc_adapter('sss')
        progress_adapter = oss2.utils.make_progress_adapter(crc_adapter, progress_callback)

        self.assertEqual(progress_adapter.len, 3)

    def test_default_logger_basic(self):
        # verify default logger
        self.assertEqual(oss2.defaults.get_logger(), logging.getLogger())

        # verify custom logger
        custom_logger = logging.getLogger('oss2')
        oss2.defaults.logger = custom_logger

        self.assertEqual(oss2.defaults.get_logger(), custom_logger)

    def test_default_logger_put(self):
        custom_logger = logging.getLogger('oss2')
        oss2.defaults.logger = custom_logger

        custom_logger.addHandler(logging.StreamHandler(sys.stdout))
        custom_logger.setLevel(logging.DEBUG)

        key = self.random_key()

        self.bucket.put_object(key, 'abc')
        resp = self.bucket.get_object(key).resp

        self.assertEqual(b'abc', resp.read())


if __name__ == '__main__':
    unittest.main()