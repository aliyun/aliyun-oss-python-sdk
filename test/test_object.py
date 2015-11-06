import unittest
import logging

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
        content = random_string(1024)

        result = self.bucket.put_object(object_name, content)

        result = self.bucket.get_object(object_name)
        self.assertEqual(result.read(), content)
        self.assertEqual(result.headers['content-type'], 'application/javascript')

        self.bucket.delete_object(object_name)

        self.assertRaises(NoSuchKey, self.bucket.get_object, object_name)

    def test_list_objects(self):
        result = self.bucket.list_objects()
        self.assertEqual(result.status, 200)

    def test_batch_delete_objects(self):
        object_list = []
        for i in xrange(0, 5):
            object_name = random_string(12)
            object_list.append(object_name)

            self.bucket.put_object(object_name, random_string(64))

        result = self.bucket.batch_delete_objects(object_list)
        self.assertEqual(sorted(object_list), sorted(result.object_list))

    def test_append_object(self):
        object_name = random_string(12)
        content1 = random_string(512)
        content2 = random_string(128)

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

if __name__ == '__main__':
    unittest.main()