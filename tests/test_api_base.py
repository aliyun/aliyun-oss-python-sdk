# -*- coding: utf-8 -*-

import unittest
import oss2
import socket
import sys

from .common import *


class TestApiBase(OssTestCase):
    if OSS_CNAME:
        def test_cname_bucket(self):
            bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_CNAME, self.OSS_BUCKET, is_cname=True)
            bucket.get_bucket_acl()

        def test_cname_object(self):
            bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_CNAME, self.OSS_BUCKET, is_cname=True)
            bucket.put_object('hello.txt', 'hello world')

    def test_https(self):
        bucket_name = random_string(63)
        bucket = oss2.Bucket(oss2.AnonymousAuth(), OSS_ENDPOINT.replace('http://', 'https://'), bucket_name)
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.get_object, 'hello.txt')

    # 只是为了测试，请不要用IP访问OSS，除非你是在VPC环境下。
    def test_ip(self):
        bucket_name = random_string(63)
        ip = socket.gethostbyname(OSS_ENDPOINT.replace('https://', '').replace('http://', ''))

        bucket = oss2.Bucket(oss2.AnonymousAuth(), ip, bucket_name)
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.get_object, 'hello.txt')

    def test_invalid_bucket_name(self):
        bucket_name = random_string(64)
        self.assertRaises(oss2.exceptions.ClientError, oss2.Bucket, oss2.AnonymousAuth(), OSS_ENDPOINT, bucket_name)

    def test_check_endpoint1(self):
        from oss2.api import _normalize_endpoint

        endpoint = 'www.aliyuncs.com'
        oss2.Bucket(oss2.AnonymousAuth(), endpoint, 'test-bucket')

    def test_check_endpoint(self):
        from oss2.api import _normalize_endpoint

        endpoint = 'www.aliyuncs.com/?x=123#segemnt '
        oss2.Bucket(oss2.AnonymousAuth(), endpoint, 'test-bucket')
        normalized_endpoint = _normalize_endpoint(endpoint)
        self.assertEqual('http://www.aliyuncs.com', normalized_endpoint)

        endpoint = 'http://www.aliyuncs.com/?x=123#segemnt '
        oss2.Bucket(oss2.AnonymousAuth(), endpoint, 'test-bucket')
        normalized_endpoint = _normalize_endpoint(endpoint)
        self.assertEqual('http://www.aliyuncs.com', normalized_endpoint)

        endpoint = 'http://192.168.1.1:3182/?x=123#segemnt '
        oss2.Bucket(oss2.AnonymousAuth(), endpoint, 'test-bucket')
        normalized_endpoint = _normalize_endpoint(endpoint)
        self.assertEqual('http://192.168.1.1:3182', normalized_endpoint)

        endpoint = 'http://www.aliyuncs.com:80/?x=123#segemnt '
        oss2.Bucket(oss2.AnonymousAuth(), endpoint, 'test-bucket')
        normalized_endpoint = _normalize_endpoint(endpoint)
        self.assertEqual('http://www.aliyuncs.com:80', normalized_endpoint)

        endpoint = 'https://www.aliyuncs.com:443/?x=123#segemnt'
        oss2.Bucket(oss2.AnonymousAuth(), endpoint, 'test-bucket')
        normalized_endpoint = _normalize_endpoint(endpoint)
        self.assertEqual('https://www.aliyuncs.com:443', normalized_endpoint)

        endpoint = 'https://www.aliyuncs.com:443'
        oss2.Bucket(oss2.AnonymousAuth(), endpoint, 'test-bucket')
        normalized_endpoint = _normalize_endpoint(endpoint)
        self.assertEqual('https://www.aliyuncs.com:443', normalized_endpoint)

        self.assertRaises(oss2.exceptions.ClientError, oss2.Bucket, oss2.AnonymousAuth(), OSS_ENDPOINT + '\\',
                          'test-bucket')

    def test_whitespace(self):
        bucket = oss2.Bucket(oss2.Auth(OSS_ID, ' ' + OSS_SECRET + ' '), OSS_ENDPOINT, self.OSS_BUCKET)
        bucket.get_bucket_acl()

        bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), ' ' + OSS_ENDPOINT + ' ', self.OSS_BUCKET)
        bucket.get_bucket_acl()

        bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, ' ' + self.OSS_BUCKET + ' ')
        bucket.get_bucket_acl()

    if sys.version_info >= (3, 3):
        def test_user_agent(self):
            app = 'fantastic-tool'

            assert_found = False
            def do_request(session_self, req, timeout):
                if assert_found:
                    self.assertTrue(req.headers['User-Agent'].find(app) >= 0)
                else:
                    self.assertTrue(req.headers['User-Agent'].find(app) < 0)

                raise oss2.exceptions.ClientError('intentional')

            from unittest.mock import patch
            with patch.object(oss2.Session, 'do_request', side_effect=do_request, autospec=True):
                # 不加 app_name
                assert_found = False
                self.assertRaises(oss2.exceptions.ClientError, self.bucket.get_bucket_acl)

                service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)
                self.assertRaises(oss2.exceptions.ClientError, service.list_buckets)

                # 加app_name
                assert_found = True
                bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, self.OSS_BUCKET,
                                     app_name=app)
                self.assertRaises(oss2.exceptions.ClientError, bucket.get_bucket_acl)

                service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT,
                                       app_name=app)
                self.assertRaises(oss2.exceptions.ClientError, service.list_buckets)


if __name__ == '__main__':
    unittest.main()