# -*- coding: utf-8 -*-

import unittest
import requests
import filecmp
import os
import sys
import oss

from oss.exceptions import NoSuchKey, PositionNotEqualToLength
from oss.compat import to_string, to_bytes

from common import *


class TestChinese(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestChinese, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    if sys.version_info >= (3, 0):
        def test_put_get_list_delete(self):
            object_name = '中文对象\x0C-1.txt'
            content = '中文内容'

            self.bucket.put_object(object_name, content)
            self.assertEqual(self.bucket.get_object(object_name).read(), to_bytes(content))

            self.assertTrue(object_name in list(info.name for info in oss.iterators.ObjectIterator(self.bucket, prefix='中文')))

            self.bucket.delete_object(object_name)

        def test_batch_delete_objects(self):
            object_name = '中文对象\x0C-2.txt'
            content = '中文内容'

            self.bucket.put_object(object_name, content)
            self.bucket.batch_delete_objects([object_name])

            self.assertTrue(not self.bucket.object_exists(object_name))
    else:
        def test_put_get_list_delete(self):
            object_name = '中文对象\x0C-1.txt'
            content = '中文内容'

            self.bucket.put_object(object_name, content)
            self.assertEqual(self.bucket.get_object(object_name).read(), content)
            self.assertTrue(object_name in list(info.name for info in oss.iterators.ObjectIterator(self.bucket, prefix='中文')))

            self.bucket.delete_object(object_name)

        def test_batch_delete_objects(self):
            object_name = '中文对象\x0C-2.txt'
            content = '中文内容'
            self.bucket.put_object(object_name, content)
            self.bucket.batch_delete_objects([object_name])

            self.assertTrue(not self.bucket.object_exists(object_name))
