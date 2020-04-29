# -*- coding: utf-8 -*-

import unittest
from oss2.models import *
from unittests.common import *


class TestModels(unittest.TestCase):
    def test_parse_range_str(self):
        resp = do4body('', 0, body='')
        get_obj_result = GetObjectResult(resp)

        content_range = 'bytes 0-128/1024'
        range_data = get_obj_result._parse_range_str(content_range)
        self.assertEqual(range_data[0], 0)
        self.assertEqual(range_data[1], 128)
