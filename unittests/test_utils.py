# -*- coding: utf-8 -*-

import unittest
from oss2.utils import *


class TestUtils(unittest.TestCase):
    def test_is_multiple_sizeof_encrypt_block(self):
        byte_range_start = 1024
        is_multiple = is_multiple_sizeof_encrypt_block(byte_range_start)
        self.assertTrue(is_multiple)

        byte_range_start = 1025
        is_multiple = is_multiple_sizeof_encrypt_block(byte_range_start)
        self.assertFalse(is_multiple)
        
    def test_calc_aes_ctr_offset_by_data_offset(self):
        byte_range_start = 1024
        cout_offset = calc_aes_ctr_offset_by_data_offset(byte_range_start)
        self.assertEqual(cout_offset, 1024 / 16)
