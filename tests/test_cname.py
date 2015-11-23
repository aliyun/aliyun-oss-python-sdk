# -*- coding: utf-8 -*-

import unittest
import oss
import logging

from common import *

logging.basicConfig(level=logging.DEBUG)


class TestBucket(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestBucket, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_CNAME, OSS_BUCKET, is_cname=True)

    if OSS_CNAME:
        def test_bucket(self):
            self.bucket.get_bucket_acl()

        def test_object(self):
            self.bucket.put_object('hello.txt', 'hello world')

if __name__ == '__main__':
    unittest.main()