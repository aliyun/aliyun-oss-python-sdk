# -*- coding: utf-8 -*-

import unittest
import datetime
import time
import oss2

from common import *
from oss2 import to_string


class TestBucket(OssTestCase):
    def test_bucket(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        service = oss2.Service(auth, OSS_ENDPOINT)
        result = service.list_buckets()
        next(b for b in result.buckets if b.name == bucket.bucket_name)

        key = 'a.txt'
        bucket.put_object(key, 'content')

        self.assertRaises(oss2.exceptions.BucketNotEmpty, bucket.delete_bucket)

        bucket.delete_object(key)
        bucket.delete_bucket()

        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_acl(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())

        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ)
        result = bucket.get_bucket_acl()
        self.assertEqual(result.acl, oss2.BUCKET_ACL_PUBLIC_READ)

        # 不带参数的create_bucket不会改变Bucket ACL
        bucket.create_bucket()
        self.assertEqual(result.acl, oss2.BUCKET_ACL_PUBLIC_READ)

        bucket.put_bucket_acl(oss2.BUCKET_ACL_PRIVATE)
        time.sleep(1)

        result = bucket.get_bucket_acl()
        self.assertEqual(result.acl, oss2.BUCKET_ACL_PRIVATE)

        self.bucket.put_bucket_acl(oss2.BUCKET_ACL_PUBLIC_READ_WRITE)
        result = self.bucket.get_bucket_acl()
        time.sleep(1)

        self.assertEqual(result.acl, oss2.BUCKET_ACL_PUBLIC_READ_WRITE)

        bucket.delete_bucket()

    def test_logging(self):
        other_bucket = oss2.Bucket(self.bucket.auth, OSS_ENDPOINT, random_string(63).lower())
        other_bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        for prefix in ['logging/', u'日志+/', '日志+/']:
            other_bucket.put_bucket_logging(oss2.models.BucketLogging(self.bucket.bucket_name, prefix))
            time.sleep(1)

            result = other_bucket.get_bucket_logging()
            self.assertEqual(result.target_bucket, self.bucket.bucket_name)
            self.assertEqual(result.target_prefix, to_string(prefix))

        other_bucket.delete_bucket_logging()
        other_bucket.delete_bucket_logging()

        result = other_bucket.get_bucket_logging()
        self.assertEqual(result.target_bucket, '')
        self.assertEqual(result.target_prefix, '')

        other_bucket.delete_bucket()

    def test_website(self):
        key = self.random_key('/')
        content = random_bytes(32)

        self.bucket.put_object('index.html', content)

        # 设置index页面和error页面
        self.bucket.put_bucket_website(oss2.models.BucketWebsite('index.html', 'error.html'))
        time.sleep(1)

        # 验证index页面和error页面
        website = self.bucket.get_bucket_website()
        self.assertEqual(website.index_file, 'index.html')
        self.assertEqual(website.error_file, 'error.html')

        # 验证读取目录会重定向到index页面
        result = self.bucket.get_object(key)
        self.assertEqual(result.read(), content)

        self.bucket.delete_object('index.html')

        # 中文
        for index, error in [('index+中文.html', 'error.中文'), (u'index+中文.html', u'error.中文')]:
            self.bucket.put_bucket_website(oss2.models.BucketWebsite(index, error))
            time.sleep(1)

            website = self.bucket.get_bucket_website()
            self.assertEqual(website.index_file, to_string(index))
            self.assertEqual(website.error_file, to_string(error))

        # 关闭静态网站托管模式
        self.bucket.delete_bucket_website()
        self.bucket.delete_bucket_website()

        # 再次关闭报错
        self.assertRaises(oss2.exceptions.NoSuchWebsite, self.bucket.get_bucket_website)

    def test_lifecycle_days(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        for prefix in ['', '中文前缀+/', u'中文前缀+/']:
            rule = LifecycleRule(random_string(10), prefix,
                                 status=LifecycleRule.DISABLED,
                                 expiration=LifecycleExpiration(days=356))
            lifecycle = BucketLifecycle([rule])

            self.bucket.put_bucket_lifecycle(lifecycle)
            time.sleep(1)

            rule_got = self.bucket.get_bucket_lifecycle().rules[0]

            self.assertEqual(rule.id, rule_got.id)
            self.assertEqual(to_string(rule.prefix), rule_got.prefix)
            self.assertEqual(rule.status, rule_got.status)

            self.assertEqual(rule_got.expiration.days, 356)
            self.assertEqual(rule_got.expiration.date, None)

        self.bucket.delete_bucket_lifecycle()
        self.bucket.delete_bucket_lifecycle()

        self.assertRaises(oss2.exceptions.NoSuchLifecycle, self.bucket.get_bucket_lifecycle)

    def test_lifecycle_date(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.DISABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2100, 12, 25)))
        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        time.sleep(1)

        rule_got = self.bucket.get_bucket_lifecycle().rules[0]

        self.assertEqual(rule_got.expiration.days, None)
        self.assertEqual(rule_got.expiration.date, datetime.date(2100, 12, 25))

        self.bucket.delete_bucket_lifecycle()

    def test_cors(self):
        rule = oss2.models.CorsRule(allowed_origins=['*'],
                                    allowed_methods=['HEAD', 'GET'],
                                    allowed_headers=['*'],
                                    max_age_seconds=1000)
        cors = oss2.models.BucketCors([rule])

        self.bucket.put_bucket_cors(cors)
        time.sleep(2)

        cors_got = self.bucket.get_bucket_cors()
        rule_got = cors_got.rules[0]

        self.assertEqual(rule.allowed_origins, rule_got.allowed_origins)
        self.assertEqual(rule.allowed_methods, rule_got.allowed_methods)
        self.assertEqual(rule.allowed_headers, rule_got.allowed_headers)
        self.assertEqual(rule.max_age_seconds, rule_got.max_age_seconds)

        self.bucket.delete_bucket_cors()
        self.bucket.delete_bucket_cors()

        self.assertRaises(oss2.exceptions.NoSuchCors, self.bucket.get_bucket_cors)

    def test_referer(self):
        referers = ['http://hello.com', 'mibrowser:home', '中文+referer', u'中文+referer']
        config = oss2.models.BucketReferer(True, referers)

        self.bucket.put_bucket_referer(config)
        time.sleep(1)

        result = self.bucket.get_bucket_referer()

        self.assertTrue(result.allow_empty_referer)
        self.assertEqual(sorted(to_string(r) for r in referers), sorted(result.referers))

    def test_location(self):
        result = self.bucket.get_bucket_location()
        self.assertTrue(result.location)

    def test_xml_input_output(self):
        xml_input1 = '''<?xml version="1.0" encoding="UTF-8"?>
                        <RefererConfiguration>
                          <AllowEmptyReferer>true</AllowEmptyReferer>
                          <RefererList>
                             <Referer>阿里云</Referer>
                          </RefererList>
                        </RefererConfiguration>'''
        xml_input2 = u'''<?xml version="1.0" encoding="UTF-8"?>
                         <RefererConfiguration>
                           <AllowEmptyReferer>true</AllowEmptyReferer>
                           <RefererList>
                             <Referer>阿里云</Referer>
                           </RefererList>
                         </RefererConfiguration>'''

        for input in [xml_input1, xml_input2]:
            self.bucket.put_bucket_referer(input)
            time.sleep(1)

            resp = self.bucket._get_bucket_config(oss2.Bucket.REFERER)
            result = oss2.models.GetBucketRefererResult(resp)
            oss2.xml_utils.parse_get_bucket_referer(result, resp.read())

            self.assertEqual(result.allow_empty_referer, True)
            self.assertEqual(result.referers[0], to_string(u'阿里云'))


if __name__ == '__main__':
    unittest.main()