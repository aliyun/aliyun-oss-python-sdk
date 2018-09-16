# -*- coding: utf-8 -*-

import unittest
import oss2


class TestResumable(unittest.TestCase):
    def test_determine_part_size(self):
        self.assertEqual(oss2.determine_part_size(oss2.defaults.part_size + 1), oss2.defaults.part_size)

        self.assertEqual(oss2.determine_part_size(1), 1)
        self.assertEqual(oss2.determine_part_size(1, oss2.defaults.part_size+1), 1)

        n = 10000
        size = (oss2.defaults.part_size + 1) * n
        part_size = oss2.determine_part_size(size)

        self.assertTrue(n * part_size <= size)
        self.assertTrue(oss2.defaults.part_size < part_size)


if __name__ == '__main__':
    unittest.main()
