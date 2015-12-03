# -*- coding: utf-8 -*-

import unittest
import sys
import oss

from oss import to_bytes

from common import *


class TestChinese(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestChinese, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    def test_unicode(self):
        key = random_string(16)
        content = u'几天后，阿里巴巴为侄子和马尔佳娜举行了隆重的婚礼。'

        self.bucket.put_object(key, content)
        self.assertEqual(self.bucket.get_object(key).read(), content.encode('utf-8'))

    if sys.version_info >= (3, 0):
        def test_put_get_list_delete(self):
            key = '中文对象\x0C-1.txt'
            content = '中文内容'

            self.bucket.put_object(key, content)
            self.assertEqual(self.bucket.get_object(key).read(), to_bytes(content))

            self.assertTrue(key in list(info.key for info in oss.ObjectIterator(self.bucket, prefix='中文')))

            self.bucket.delete_object(key)

        def test_batch_delete_objects(self):
            key = '中文对象\x0C-2.txt'
            content = '中文内容'

            self.bucket.put_object(key, content)
            self.bucket.batch_delete_objects([key])

            self.assertTrue(not self.bucket.object_exists(key))
    else:
        def test_put_get_list_delete(self):
            key = '中文对象\x0C-1.txt'
            content = '中文内容'

            self.bucket.put_object(key, content)
            self.assertEqual(self.bucket.get_object(key).read(), content)
            self.assertTrue(key in list(info.key for info in oss.ObjectIterator(self.bucket, prefix='中文')))

            self.bucket.delete_object(key)

        def test_batch_delete_objects(self):
            key = '中文对象\x0C-2.txt'
            content = '中文内容'
            self.bucket.put_object(key, content)
            self.bucket.batch_delete_objects([key])

            self.assertTrue(not self.bucket.object_exists(key))
