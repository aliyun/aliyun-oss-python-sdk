# -*- coding: utf-8 -*-

import unittest
import oss


class TestUtils(unittest.TestCase):
    def test_is_ip(self):
        self.assertTrue(oss.utils.is_ip_or_localhost('1.2.3.4'))
        self.assertTrue(oss.utils.is_ip_or_localhost('localhost'))

        self.assertTrue(not oss.utils.is_ip_or_localhost('-1.2.3.4'))
        self.assertTrue(not oss.utils.is_ip_or_localhost('1.256.1.2'))
        self.assertTrue(not oss.utils.is_ip_or_localhost('一.二.三.四'))
