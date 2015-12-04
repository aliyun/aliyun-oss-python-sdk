# -*- coding: utf-8 -*-

import unittest
import sys
import oss2

from oss2 import to_bytes

from common import *


class TestChinese(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestChinese, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)
        self.bucket.create_bucket()

    def test_unicode(self):
        key = random_string(16)
        content = u'几天后，阿里巴巴为侄子和马尔佳娜举行了隆重的婚礼。'

        self.bucket.put_object(key, content)
        self.assertEqual(self.bucket.get_object(key).read(), content.encode('utf-8'))

    if sys.version_info >= (3, 0):
        def test_put_get_list_delete(self):
            key = '中文文件\x0C-1.txt'
            content = '中文内容'

            self.bucket.put_object(key, content)
            self.assertEqual(self.bucket.get_object(key).read(), to_bytes(content))

            self.assertTrue(key in list(info.key for info in oss2.ObjectIterator(self.bucket, prefix='中文')))

            self.bucket.delete_object(key)

        def test_batch_delete_objects(self):
            key = '中文文件\x0C-2.txt'
            content = '中文内容'

            self.bucket.put_object(key, content)
            self.bucket.batch_delete_objects([key])

            self.assertTrue(not self.bucket.object_exists(key))
    else:
        def test_put_get_list_delete(self):
            key = '中文文件\x0C-1.txt'
            content = '中文内容'

            self.bucket.put_object(key, content)
            self.assertEqual(self.bucket.get_object(key).read(), content)
            self.assertTrue(key in list(info.key for info in oss2.ObjectIterator(self.bucket, prefix='中文')))

            self.bucket.delete_object(key)

        def test_batch_delete_objects(self):
            key = '中文文件\x0C-2.txt'
            content = '中文内容'
            self.bucket.put_object(key, content)
            self.bucket.batch_delete_objects([key])

            self.assertTrue(not self.bucket.object_exists(key))

    def test_append(self):
        key = random_string(16) + '文件\x0D\x0E\x7F名'
        content = random_bytes(32) + u'内容\x0D\x0E\7F是中文\x01'.encode('utf-8')

        self.bucket.append_object(key, 0, content)
        self.assertEqual(self.bucket.get_object(key).read(), content)

        self.bucket.delete_object(key + 'extra')
        self.bucket.batch_delete_objects([key])

    def test_local_file(self):
        key = random_string(16) + '文件\x0D\x0E\x7F名'
        content = random_bytes(32) + u'内容\x0D\x0E\7F是中文\x01'.encode('utf-8')

        self.bucket.put_object(key, content)

        key2 = random_string(16)

        self.bucket.get_object_to_file(key, '中文本地文件名.txt')
        self.bucket.put_object_from_file(key2, '中文本地文件名.txt')

        self.assertEqual(self.bucket.get_object(key2).read(), content)

        os.remove(u'中文本地文件名.txt')