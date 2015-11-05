import unittest
import oss
import logging

from common import *


class TestBucket(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestBucket, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    def test_bucket_iterator(self):
        service = oss.Service(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)
        self.assertTrue(OSS_BUCKET in (b.name for b in oss.BucketIterator(service)))

    def test_bucket(self):
        auth = oss.Auth(OSS_ID, OSS_SECRET)
        bucket = oss.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())

        bucket.create_bucket('private')

        service = oss.Service(auth, OSS_ENDPOINT)
        result = service.list_buckets()
        next(b for b in result.buckets if b.name == bucket.bucket_name)

        bucket.delete_bucket()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()