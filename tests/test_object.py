# -*- coding: utf-8 -*-

import unittest
import requests

import oss
from oss.exceptions import NoSuchKey, PositionNotEqualToLength
from common import *


class TestObject(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestObject, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    def test_object(self):
        object_name = random_string(12) + '.js'
        content = random_bytes(1024)

        result = self.bucket.put_object(object_name, content)

        result = self.bucket.get_object(object_name)
        self.assertEqual(result.read(), content)
        self.assertEqual(result.headers['content-type'], 'application/javascript')

        result = self.bucket.head_object(object_name)
        self.assertEqual(int(result.headers['content-length']), len(content))

        self.bucket.delete_object(object_name)

        self.assertRaises(NoSuchKey, self.bucket.get_object, object_name)

    def test_anonymous(self):
        object_name = random_string(12)
        content = random_bytes(512)

        # 设置bucket为public-read，并确认可以上传和下载
        self.bucket.put_bucket_acl('public-read-write')

        b = oss.Bucket(oss.AnonymousAuth(), OSS_ENDPOINT, OSS_BUCKET)
        b.put_object(object_name, content)
        result = b.get_object(object_name)
        self.assertEqual(result.read(), content)

        # 测试sign_url
        url = b.sign_url('GET', object_name, 100)
        resp = requests.get(url)
        self.assertEqual(content, resp.content)

        # 设置bucket为private，并确认上传和下载都会失败
        self.bucket.put_bucket_acl('private')

        self.assertRaises(oss.exceptions.AccessDenied, b.put_object, object_name, content)
        self.assertRaises(oss.exceptions.AccessDenied, b.get_object, object_name)

    def test_range_get(self):
        object_name = random_string(12)
        content = random_bytes(1024)

        self.bucket.put_object(object_name, content)

        result = self.bucket.get_object(object_name, range=(500, None))
        self.assertEqual(result.read(), content[500:])

        result = self.bucket.get_object(object_name, range=(None, 199))
        self.assertEqual(result.read(), content[-199:])

        result = self.bucket.get_object(object_name, range=(3, 3))
        self.assertEqual(result.read(), content[3:4])

    def test_list_objects(self):
        result = self.bucket.list_objects()
        self.assertEqual(result.status, 200)

    def test_batch_delete_objects(self):
        object_list = []
        for i in range(0, 5):
            object_name = random_string(12)
            object_list.append(object_name)

            self.bucket.put_object(object_name, random_string(64))

        result = self.bucket.batch_delete_objects(object_list)
        self.assertEqual(sorted(object_list), sorted(result.object_list))

        for object in object_list:
            self.assertTrue(not self.bucket.object_exists(object))

    def test_batch_delete_objects_chinese(self):
        object_name = '中文对象\x0C.txt'
        self.bucket.put_object(object_name, '中文内容')
        self.bucket.batch_delete_objects([object_name])

        self.assertTrue(not self.bucket.object_exists(object_name))

    def test_append_object(self):
        object_name = random_string(12)
        content1 = random_bytes(512)
        content2 = random_bytes(128)

        result = self.bucket.append_object(object_name, 0, content1)
        self.assertEqual(result.next_position, len(content1))

        try:
            self.bucket.append_object(object_name, 0, content2)
        except PositionNotEqualToLength as e:
            self.assertEqual(e.next_position, len(content1))
        else:
            self.assertTrue(False)

        result = self.bucket.append_object(object_name, len(content1), content2)
        self.assertEqual(result.next_position, len(content1) + len(content2))

        self.bucket.delete_object(object_name)

    def test_private_download_url(self):
        for object_name in [random_string(12), '中文对象名']:
            content = random_bytes(42)

            self.bucket.put_object(object_name, content)
            url = self.bucket.sign_url('GET', object_name, 60)

            resp = requests.get(url)
            self.assertEqual(content, resp.content)

    def test_copy_object(self):
        source_object_name = random_string(12)
        target_object_name = random_string(13)
        content = random_bytes(36)

        self.bucket.put_object(source_object_name, content)
        self.bucket.copy_object(self.bucket.bucket_name, source_object_name, target_object_name)

        result = self.bucket.get_object(target_object_name)
        self.assertEqual(content, result.read())

    def test_object_acl(self):
        object_name = random_string(12)
        content = random_bytes(32)

        self.bucket.put_object(object_name, content)
        self.assertEqual(self.bucket.get_object_acl(object_name).acl, 'default')

        self.bucket.put_object_acl(object_name, 'private')
        self.assertEqual(self.bucket.get_object_acl(object_name).acl, 'private')

        self.bucket.delete_object(object_name)

    def test_object_exists(self):
        object_name = random_string(12)

        self.assertTrue(not self.bucket.object_exists(object_name))

        self.bucket.put_object(object_name, "hello world")
        self.assertTrue(self.bucket.object_exists(object_name))

    def test_user_meta(self):
        object_name = random_string(12)

        self.bucket.put_object(object_name, 'hello', headers={'x-oss-meta-key1': 'value1',
                                                              'X-Oss-Meta-Key2': 'value2'})

        headers = self.bucket.get_object(object_name).headers
        self.assertEqual(headers['x-oss-meta-key1'], 'value1')
        self.assertEqual(headers['x-oss-meta-key2'], 'value2')

if __name__ == '__main__':
    unittest.main()