import unittest
import string
import random
import oss
import os
import logging

from oss.exceptions import NoSuchKey

OSS_ID = os.getenv("OSS_TEST_ACCESS_KEY_ID")
OSS_SECRET = os.getenv("OSS_TEST_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_TEST_ENDPOINT")
OSS_BUCKET = os.getenv("OSS_TEST_BUCKET")

logging.basicConfig(level=logging.DEBUG)


def random_string(n):
    return ''.join(random.choice(string.letters) for i in xrange(n))


class TestObject(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestObject, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    def test_object(self):
        object_name = random_string(12)
        content = random_string(1024)

        result = self.bucket.put_object(object_name, content)
        result = self.bucket.get_object(object_name)
        self.assertEqual(result.read(), content)

        self.bucket.delete_object(object_name)

        self.assertRaises(NoSuchKey, self.bucket.get_object, object_name)

    def test_list_objects(self):
        result = self.bucket.list_objects()
        self.assertEqual(result.status, 200)

if __name__ == '__main__':
    unittest.main()