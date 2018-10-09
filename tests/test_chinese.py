# -*- coding: utf-8 -*-

import unittest
import sys
import oss2

from oss2 import to_bytes, to_string

from common import *


class TestChinese(OssTestCase):
    def test_unicode_content(self):
        key = self.random_key()
        content = u'几天后，阿里巴巴为侄子和马尔佳娜举行了隆重的婚礼。'

        self.bucket.put_object(key, content)
        self.assertEqual(self.bucket.get_object(key).read(), content.encode('utf-8'))

    def test_put_get_list_delete(self):
        for key in ['中文!@#$%^&*()-=文件\x0C-1.txt', u'中文!@#$%^&*()-=文件\x0C-1.txt']:
            content = '中文内容'

            self.bucket.put_object(key, content)
            self.assertEqual(self.bucket.get_object(key).read(), to_bytes(content))

            self.assertTrue(to_string(key) in list(info.key for info in oss2.ObjectIterator(self.bucket, prefix='中文')))

            self.bucket.delete_object(key)

    def test_batch_delete_objects(self):
        for key in ['中文!@#$%^&*()-=文件\x0C-2.txt', u'中文!@#$%^&*()-=文件\x0C-3.txt', '<hello>']:
            content = '中文内容'

            self.bucket.put_object(key, content)
            result = self.bucket.batch_delete_objects([key])
            self.assertEqual(result.deleted_keys[0], to_string(key))

            self.assertTrue(not self.bucket.object_exists(key))

    def test_local_file(self):
        key = self.random_key('文件!@#$%^&*()-=\x0D\x0E\x7F名')
        content = random_bytes(32) + u'内容\x0D\x0E\7F是中文\x01'.encode('utf-8')

        self.bucket.put_object(key, content)

        key2 = random_string(16)

        self.bucket.get_object_to_file(key, '中文本地文件名.txt')
        self.bucket.put_object_from_file(key2, '中文本地文件名.txt')

        self.assertEqual(self.bucket.get_object(key2).read(), content)

        os.remove(u'中文本地文件名.txt')

    def test_get_symlink(self):
        key = '中文!@#$%^&*()-=文件\x0C-1.txt'
        symlink = u'中文!@#$%^&*()-=文件\x0C-2.txt'
        content = '中文内容'
        
        self.bucket.put_object(key, content)
        self.bucket.put_symlink(key, symlink)
        
        result = self.bucket.get_symlink(symlink)
        self.assertEqual(result.target_key, key)

class TestHttp20OverChinese(TestChinese):
    """
        当环境变量使用oss2.HTTP11时，则重新设置为HTTP20, 再运行TestChinese，反之亦然
    """
    def __init__(self, *args, **kwargs):
        super(TestHttp20OverChinese, self).__init__(*args, **kwargs)

    def setUp(self):
        if os.getenv('OSS_TEST_HTTP_VERSION') == oss2.HTTP_VERSION_11:
            os.environ['OSS_TEST_HTTP_VERSION'] = oss2.HTTP_VERSION_20
        else:
            os.environ['OSS_TEST_HTTP_VERSION'] = oss2.HTTP_VERSION_11
        super(TestHttp20OverChinese, self).setUp()

    def tearDown(self):
        if os.getenv('OSS_TEST_HTTP_VERSION') == oss2.HTTP_VERSION_11:
            os.environ['OSS_TEST_HTTP_VERSION'] = oss2.HTTP_VERSION_20
        else:
            os.environ['OSS_TEST_HTTP_VERSION'] = oss2.HTTP_VERSION_11
        super(TestHttp20OverChinese, self).tearDown()

if __name__ == '__main__':
    unittest.main()
