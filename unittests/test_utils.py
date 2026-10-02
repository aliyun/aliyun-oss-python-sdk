# -*- coding: utf-8 -*-

import unittest
import io
import oss2
from oss2.utils import *


class TestUtils(unittest.TestCase):
    def test_progress_adapter_short_reads(self):
        class ShortReader(io.BytesIO):
            def read(self, size=-1):
                return super(ShortReader, self).read(min(size, 3))

        progress = []
        data = b'0123456789'
        adapter = make_progress_adapter(
            ShortReader(data), lambda consumed, total: progress.append((consumed, total)),
            size=len(data))
        chunks = []
        while True:
            chunk = adapter.read(4)
            if not chunk:
                break
            chunks.append(chunk)
        self.assertEqual(b''.join(chunks), data)
        self.assertEqual(progress, [(3, 10), (6, 10), (9, 10), (10, 10)])

    def test_progress_adapter_premature_eof(self):
        progress = []
        adapter = make_progress_adapter(
            io.BytesIO(b'abc'), lambda consumed, total: progress.append((consumed, total)),
            size=10)
        self.assertEqual(adapter.read(10), b'abc')
        self.assertEqual(adapter.read(10), b'')
        self.assertEqual(progress, [(3, 10), (3, 10)])

    def test_aes_ctr_is_block_aligned(self):
        cipher = AESCTRCipher()
        start = 1024
        is_aligned = cipher.is_block_aligned(start)
        self.assertTrue(is_aligned)

        start = 1025
        is_aligned = cipher.is_block_aligned(start)
        self.assertFalse(is_aligned)
        
    def test_aes_ctr_calc_offset(self):
        cipher = AESCTRCipher()
        start = 1024
        cout_offset = cipher.calc_offset(start)
        self.assertEqual(cout_offset, start / 16)

        start = 1025
        self.assertRaises(ClientError, cipher.calc_offset, start)

    def test_acs_ctr_is_valid_part_size(self):
        cipher = AESCTRCipher()
        self.assertFalse(cipher.is_valid_part_size(1, 1024*1024*100))
        self.assertFalse(cipher.is_valid_part_size(1024 * 100 + 1, 1024*1024*100))
        self.assertFalse(cipher.is_valid_part_size(1024 * 100, 1024*1024*1024))
        self.assertTrue(cipher.is_valid_part_size(1024 * 100, 1024*1024*100))

    def test_acs_ctr_determine_part_size(self):
        cipher = AESCTRCipher()
        self.assertEqual(cipher.determine_part_size(1024*100*100000), 1024*1024*10)
        self.assertEqual(cipher.determine_part_size(1024*100*100000 - 1), 1024*1024*10)
        self.assertEqual(cipher.determine_part_size(1024*100*99), 1024*1024*10)

        self.assertEqual(cipher.determine_part_size(1024*100*1000, 1024*100), 1024*100)
        self.assertEqual(cipher.determine_part_size(1024*100*1000, 1024*100-1), 1024*100)
        self.assertEqual(cipher.determine_part_size(1024*100*10000, 1024), 1024*1024*10)

        oss2.defaults.part_size = 1024*1024 - 1
        self.assertEqual(cipher.determine_part_size(1024 * 1024 * 1000), 1024 * 1024)


if __name__ == '__main__':
    unittest.main()
