# -*- coding: utf-8 -*-

import unittest
import oss2
import logging
import socket

from common import *

logging.basicConfig(level=logging.DEBUG)


class TestBucket(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestBucket, self).__init__(*args, **kwargs)

    if OSS_CNAME:
        def test_cname_bucket(self):
            bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_CNAME, OSS_BUCKET, is_cname=True)
            bucket.get_bucket_acl()

        def test_cname_object(self):
            bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_CNAME, OSS_BUCKET, is_cname=True)
            bucket.put_object('hello.txt', 'hello world')

    def test_https(self):
        bucket_name = random_string(63)
        bucket = oss2.Bucket(oss2.AnonymousAuth(), 'https://oss-cn-hangzhou.aliyuncs.com', bucket_name)
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.get_object, 'hello.txt')

    # 只是为了测试，请不要用IP访问OSS，除非你是在VPC环境下。
    def test_ip(self):
        bucket_name = random_string(63)
        ip = socket.gethostbyname('oss-cn-hangzhou.aliyuncs.com')

        bucket = oss2.Bucket(oss2.AnonymousAuth(), ip, bucket_name)
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.get_object, 'hello.txt')

    def test_invalid_bucket_name(self):
        bucket_name = random_string(64)
        bucket = oss2.Bucket(oss2.AnonymousAuth(), 'http://oss-cn-hangzhou.aliyuncs.com', bucket_name)
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.get_object, 'hello.txt')

    def test_whitespace(self):
        bucket = oss2.Bucket(oss2.Auth(OSS_ID, ' ' + OSS_SECRET + ' '), OSS_ENDPOINT, OSS_BUCKET)
        self.assertTrue(bucket.bucket_exists())

        bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), ' ' + OSS_ENDPOINT + ' ', OSS_BUCKET)
        self.assertTrue(bucket.bucket_exists())

if __name__ == '__main__':
    unittest.main()