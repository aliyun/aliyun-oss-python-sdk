# -*- coding: utf-8 -*-

import unittest
import oss2


class TestUtils(unittest.TestCase):
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
