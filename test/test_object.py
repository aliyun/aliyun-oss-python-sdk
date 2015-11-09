# -*- coding: utf-8 -*-

import unittest
import logging
import requests

import oss
from oss.exceptions import NoSuchKey, PositionNotEqualToLength
from common import *

logging.basicConfig(level=logging.DEBUG)


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

if __name__ == '__main__':
    unittest.main()