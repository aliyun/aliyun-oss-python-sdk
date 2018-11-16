# -*- coding: utf-8 -*-


import datetime

from common import *
from oss2 import to_string


class TestBucket(OssTestCase):
    def test_bucket(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        service = oss2.Service(auth, OSS_ENDPOINT)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.bucket_name in
                          (b.name for b in
                           service.list_buckets(prefix=bucket.bucket_name).buckets))

        key = 'a.txt'
        bucket.put_object(key, 'content')

        self.assertRaises(oss2.exceptions.BucketNotEmpty, bucket.delete_bucket)

        bucket.delete_object(key)
        bucket.delete_bucket()

        wait_meta_sync()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_bucket_with_storage_class(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE, oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_IA))

        service = oss2.Service(auth, OSS_ENDPOINT)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.bucket_name in
                          (b.name for b in
                           service.list_buckets(prefix=bucket.bucket_name).buckets))

        key = 'a.txt'
        bucket.put_object(key, 'content')

        self.assertRaises(oss2.exceptions.BucketNotEmpty, bucket.delete_bucket)

        objects = bucket.list_objects()
        self.assertEqual(1, len(objects.object_list))
        self.assertEqual(objects.object_list[0].storage_class, 'IA')

        bucket.delete_object(key)
        bucket.delete_bucket()

        wait_meta_sync()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_acl(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())

        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ)
        bucket.create_bucket()

        self.retry_assert(lambda: bucket.get_bucket_acl().acl == oss2.BUCKET_ACL_PUBLIC_READ)

        bucket.put_bucket_acl(oss2.BUCKET_ACL_PRIVATE)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.get_bucket_acl().acl == oss2.BUCKET_ACL_PRIVATE)

        bucket.put_bucket_acl(oss2.BUCKET_ACL_PUBLIC_READ_WRITE)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.get_bucket_acl().acl == oss2.BUCKET_ACL_PUBLIC_READ_WRITE)

        bucket.delete_bucket()

    def test_logging(self):
        other_bucket = oss2.Bucket(self.bucket.auth, OSS_ENDPOINT, random_string(63).lower())
        other_bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        def same_logging(bucket_logging, target_bucket, target_prefix):
            return bucket_logging.target_bucket == target_bucket and bucket_logging.target_prefix == target_prefix

        for prefix in [u'日志+/', 'logging/', '日志+/']:
            other_bucket.put_bucket_logging(oss2.models.BucketLogging(self.bucket.bucket_name, prefix))
            wait_meta_sync()

            self.retry_assert(lambda: same_logging(other_bucket.get_bucket_logging(),
                                                   self.bucket.bucket_name,
                                                   to_string(prefix)))

        other_bucket.delete_bucket_logging()
        other_bucket.delete_bucket_logging()

        self.retry_assert(lambda: same_logging(other_bucket.get_bucket_logging(), '', ''))

        other_bucket.delete_bucket()

    def test_website(self):
        key = self.random_key('/')
        content = random_bytes(32)

        self.bucket.put_object('index.html', content)

        # 设置index页面和error页面
        self.bucket.put_bucket_website(oss2.models.BucketWebsite('index.html', 'error.html'))
        wait_meta_sync()

        def same_website(website, index, error):
            return website.index_file == index and website.error_file == error

        # 验证index页面和error页面
        self.retry_assert(lambda: same_website(self.bucket.get_bucket_website(), 'index.html', 'error.html'))

        # 验证读取目录会重定向到index页面
        result = self.bucket.get_object(key)
        self.assertEqual(result.read(), content)

        self.bucket.delete_object('index.html')

        # 中文
        for index, error in [('index+中文.html', 'error.中文'), (u'index+中文.html', u'error.中文')]:
            self.bucket.put_bucket_website(oss2.models.BucketWebsite(index, error))
            self.retry_assert(lambda: same_website(self.bucket.get_bucket_website(), to_string(index), to_string(error)))

        # 关闭静态网站托管模式
        self.bucket.delete_bucket_website()
        self.bucket.delete_bucket_website()

        self.assertRaises(oss2.exceptions.NoSuchWebsite, self.bucket.get_bucket_website)

    @staticmethod
    def same_lifecycle(orig_rule, bucket):
        try:
            rules = bucket.get_bucket_lifecycle().rules
        except oss2.exceptions.NoSuchLifecycle:
            return False

        if not rules:
            return False

        rule_got = rules[0]
        if orig_rule.id != rule_got.id:
            return False

        if to_string(orig_rule.prefix) != rule_got.prefix:
            return False

        if orig_rule.status != rule_got.status:
            return False

        if orig_rule.expiration.days != rule_got.expiration.days:
            return False

        if orig_rule.expiration.date != rule_got.expiration.date:
            return False

        return True

    def test_lifecycle_days(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        for prefix in ['中文前缀+/', '', u'中文前缀+/']:
            rule = LifecycleRule(random_string(10), prefix,
                                 status=LifecycleRule.ENABLED,
                                 expiration=LifecycleExpiration(days=356))
            lifecycle = BucketLifecycle([rule])

            self.bucket.put_bucket_lifecycle(lifecycle)
            self.retry_assert(lambda: self.same_lifecycle(rule, self.bucket))

        self.bucket.delete_bucket_lifecycle()
        self.bucket.delete_bucket_lifecycle()

        self.assertRaises(oss2.exceptions.NoSuchLifecycle, self.bucket.get_bucket_lifecycle)

    def test_put_lifecycle_days_less_than_transition_days(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=3))

        rule.storage_transitions = [oss2.models.StorageTransition(days=4, storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_lifecycle, BucketLifecycle([rule]))

    def test_put_lifecycle_invalid_transitions(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=6))
        # 转储为ARCHIVE的天数小于转储为IA
        rule.storage_transitions = [oss2.models.StorageTransition(days=5,
                                                                  storage_class=oss2.BUCKET_STORAGE_CLASS_IA),
                                    oss2.models.StorageTransition(days=2,
                                                                  storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE)]
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_lifecycle, BucketLifecycle([rule]))

        # 转储为IA(天数大于object过期时间)
        rule.storage_transitions = [oss2.models.StorageTransition(days=7,
                                                                  storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_lifecycle, BucketLifecycle([rule]))

        # 转储为STANDARD
        rule.storage_transitions = [oss2.models.StorageTransition(days=5,
                                                                  storage_class=oss2.BUCKET_STORAGE_CLASS_STANDARD)]
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_lifecycle, BucketLifecycle([rule]))

    def test_lifecycle_date(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2016, 12, 25)))
        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        self.retry_assert(lambda: self.same_lifecycle(rule, self.bucket))

        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_created_before_date(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 25)))
        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        self.retry_assert(lambda: self.same_lifecycle(rule, self.bucket))

        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_abort_multipart_upload_days(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, AbortMultipartUpload

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 25)))

        rule.abort_multipart_upload = AbortMultipartUpload(days=356)

        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        self.retry_assert(lambda: self.same_lifecycle(rule, self.bucket))

        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(356, result.rules[0].abort_multipart_upload.days)

        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_abort_multipart_upload_date(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, AbortMultipartUpload

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 25)))
        rule.abort_multipart_upload = AbortMultipartUpload(created_before_date=datetime.date(2016, 12, 20))

        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)

        wait_meta_sync()
        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(datetime.date(2016, 12, 20), result.rules[0].abort_multipart_upload.created_before_date)

        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_storage_transitions_mixed(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 25)))

        rule.storage_transitions = [StorageTransition(days=356, storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        lifecycle = BucketLifecycle([rule])

        self.assertRaises(oss2.exceptions.InvalidRequest, self.bucket.put_bucket_lifecycle, lifecycle)

    def test_lifecycle_storage_transitions_days(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=357))

        rule.storage_transitions = [StorageTransition(days=356, storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        wait_meta_sync()
        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(1, len(result.rules[0].storage_transitions))
        self.assertEqual(356, result.rules[0].storage_transitions[0].days)

        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_storage_transitions_more_days(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=357))

        rule.storage_transitions = [StorageTransition(days=355, storage_class=oss2.BUCKET_STORAGE_CLASS_IA),
                                    StorageTransition(days=356, storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE)]

        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        wait_meta_sync()
        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(2, len(result.rules[0].storage_transitions))
        if result.rules[0].storage_transitions[0].storage_class == oss2.BUCKET_STORAGE_CLASS_IA:
            self.assertEqual(355, result.rules[0].storage_transitions[0].days)
            self.assertEqual(356, result.rules[0].storage_transitions[1].days)
            self.assertEqual(oss2.BUCKET_STORAGE_CLASS_ARCHIVE, result.rules[0].storage_transitions[1].storage_class)
        else:
            self.assertEqual(356, result.rules[0].storage_transitions[0].days)
            self.assertEqual(356, result.rules[0].storage_transitions[1].days)
            self.assertEqual(oss2.BUCKET_STORAGE_CLASS_IA, result.rules[0].storage_transitions[1].storage_class)
        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_storage_transitions_date(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 25)))
        rule.storage_transitions = [StorageTransition(created_before_date=datetime.date(2016, 12, 20),
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        wait_meta_sync()
        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(1, len(result.rules[0].storage_transitions))
        self.assertEqual(datetime.date(2016, 12, 20), result.rules[0].storage_transitions[0].created_before_date)

        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_all_without_object_expiration(self):
        from oss2.models import LifecycleRule, BucketLifecycle, AbortMultipartUpload, StorageTransition

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED)

        rule.abort_multipart_upload = AbortMultipartUpload(days=356)
        rule.storage_transitions = [StorageTransition(days=356, storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        wait_meta_sync()
        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(356, result.rules[0].abort_multipart_upload.days)
        self.assertEqual(1, len(result.rules[0].storage_transitions))
        self.assertEqual(356, result.rules[0].storage_transitions[0].days)

        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_all(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, AbortMultipartUpload, StorageTransition

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=357))

        self.assertRaises(oss2.exceptions.ClientError,
                          LifecycleExpiration, days=356, created_before_date=datetime.date(2016, 12, 25))

        self.assertRaises(oss2.exceptions.ClientError,
                          AbortMultipartUpload, days=356, created_before_date=datetime.date(2016, 12, 25))

        self.assertRaises(oss2.exceptions.ClientError,
                          StorageTransition, days=356, created_before_date=datetime.date(2016, 12, 25))

        rule.abort_multipart_upload = AbortMultipartUpload(days=356)
        rule.storage_transitions = [StorageTransition(days=356, storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)

        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(356, result.rules[0].abort_multipart_upload.days)
        self.assertEqual(1, len(result.rules[0].storage_transitions))
        self.assertEqual(356, result.rules[0].storage_transitions[0].days)

        self.bucket.delete_bucket_lifecycle()

    def test_cors(self):
        rule = oss2.models.CorsRule(allowed_origins=['*'],
                                    allowed_methods=['HEAD', 'GET'],
                                    allowed_headers=['*'],
                                    max_age_seconds=1000)
        cors = oss2.models.BucketCors([rule])

        self.bucket.put_bucket_cors(cors)
        wait_meta_sync()

        cors_got = self.bucket.get_bucket_cors()
        rule_got = cors_got.rules[0]

        self.assertEqual(rule.allowed_origins, rule_got.allowed_origins)
        self.assertEqual(rule.allowed_methods, rule_got.allowed_methods)
        self.assertEqual(rule.allowed_headers, rule_got.allowed_headers)
        self.assertEqual(rule.max_age_seconds, rule_got.max_age_seconds)

        self.bucket.delete_bucket_cors()
        self.bucket.delete_bucket_cors()
        wait_meta_sync()
        self.assertRaises(oss2.exceptions.NoSuchCors, self.bucket.get_bucket_cors)

    def test_bucket_stat(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        service = oss2.Service(auth, OSS_ENDPOINT)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.bucket_name in (b.name for b in
                                                         service.list_buckets(prefix=bucket.bucket_name).buckets))

        key = 'a.txt'
        bucket.put_object(key, 'content')
        wait_meta_sync()

        result = bucket.get_bucket_stat()
        self.assertEqual(1, result.object_count)
        self.assertEqual(0, result.multi_part_upload_count)
        self.assertEqual(7, result.storage_size_in_bytes)

        bucket.delete_object(key)
        bucket.delete_bucket()

        wait_meta_sync()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_bucket_info(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())

        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.get_bucket_info)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        service = oss2.Service(auth, OSS_ENDPOINT)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.bucket_name in (b.name for b in
                                                         service.list_buckets(prefix=bucket.bucket_name).buckets))
        result = bucket.get_bucket_info()
        self.assertEqual(result.name, bucket.bucket_name)
        self.assertEqual(result.storage_class, oss2.BUCKET_STORAGE_CLASS_STANDARD)
        self.assertTrue(len(result.creation_date) > 0)
        self.assertTrue(len(result.intranet_endpoint) > 0)
        self.assertTrue(len(result.extranet_endpoint) > 0)
        self.assertTrue(len(result.owner.id) > 0)
        self.assertEqual(result.acl.grant, oss2.BUCKET_ACL_PRIVATE)
        bucket.delete_bucket()

        wait_meta_sync()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_referer(self):
        referers = ['http://hello.com', 'mibrowser:home', '中文+referer', u'中文+referer']
        config = oss2.models.BucketReferer(True, referers)

        self.bucket.put_bucket_referer(config)
        wait_meta_sync()

        result = self.bucket.get_bucket_referer()

        self.assertTrue(result.allow_empty_referer)
        self.assertEqual(sorted(to_string(r) for r in referers), sorted(to_string(r) for r in result.referers))

    def test_location(self):
        result = self.bucket.get_bucket_location()
        self.assertTrue(result.location)

    def test_malformed_xml(self):
        xml_input = '''<This is a bad xml></bad as I am>'''
        self.assertRaises(oss2.exceptions.MalformedXml, self.bucket.put_bucket_lifecycle, xml_input)

    def test_invalid_argument(self):
        rule = oss2.models.CorsRule(allowed_origins=['*'],
                                    allowed_methods=['HEAD', 'GET'],
                                    allowed_headers=['*'],
                                    max_age_seconds=-1)
        cors = oss2.models.BucketCors([rule])

        try:
            self.bucket.put_bucket_cors(cors)
        except oss2.exceptions.InvalidArgument as e:
            self.assertEqual(e.name, 'MaxAgeSeconds')
            self.assertEqual(e.value, '-1')

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
            wait_meta_sync()

            resp = self.bucket._get_bucket_config(oss2.Bucket.REFERER)
            result = oss2.models.GetBucketRefererResult(resp)
            oss2.xml_utils.parse_get_bucket_referer(result, resp.read())

            self.assertEqual(result.allow_empty_referer, True)
            self.assertEqual(result.referers[0], to_string(u'阿里云'))


if __name__ == '__main__':
    unittest.main()
