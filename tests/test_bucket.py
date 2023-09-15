# -*- coding: utf-8 -*-


import datetime
import json
from oss2.headers import *
from .common import *
from oss2 import to_string


class TestBucket(OssTestCase):
    def test_bucket(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-bucket"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

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
        bucket_name = self.OSS_BUCKET + "-test-storage-class"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

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

    def test_bucket_with_data_redundancy_type(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-redundancy-type"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

        # LRS
        bucketConfig = oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_IA, oss2.BUCKET_DATA_REDUNDANCY_TYPE_LRS)
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE, bucketConfig)
        wait_meta_sync()
        
        result = bucket.get_bucket_info()
        self.assertEqual(oss2.BUCKET_DATA_REDUNDANCY_TYPE_LRS, result.data_redundancy_type)
        bucket.delete_bucket()

        # ZRS
        bucketConfig = oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_IA, oss2.BUCKET_DATA_REDUNDANCY_TYPE_ZRS)
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE, bucketConfig)
        wait_meta_sync()
        
        result = bucket.get_bucket_info()
        self.assertEqual(oss2.BUCKET_DATA_REDUNDANCY_TYPE_ZRS, result.data_redundancy_type)
        bucket.delete_bucket()

    def test_acl(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-acl"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ)

        self.retry_assert(lambda: bucket.get_bucket_acl().acl == oss2.BUCKET_ACL_PUBLIC_READ)

        bucket.put_bucket_acl(oss2.BUCKET_ACL_PRIVATE)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.get_bucket_acl().acl == oss2.BUCKET_ACL_PRIVATE)

        bucket.put_bucket_acl(oss2.BUCKET_ACL_PUBLIC_READ_WRITE)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.get_bucket_acl().acl == oss2.BUCKET_ACL_PUBLIC_READ_WRITE)

        bucket.delete_bucket()

    def test_logging(self):
        bucket_name = self.OSS_BUCKET + "-test-logging"
        other_bucket = oss2.Bucket(self.bucket.auth, OSS_ENDPOINT, bucket_name)
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

    def test_lifecycle_overlap(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2016, 12, 25)))
        lifecycle = BucketLifecycle([rule])

        rule2 = LifecycleRule(random_string(10), '中文前缀/2',
                              status=LifecycleRule.ENABLED,
                              expiration=LifecycleExpiration(date=datetime.date(2016, 12, 25)))
        lifecycle.rules.append(rule2)

        headers = dict()
        headers[OSS_ALLOW_ACTION_OVERLAP] = 'true'
        self.bucket.put_bucket_lifecycle(lifecycle, headers)
        self.retry_assert(lambda: self.same_lifecycle(rule, self.bucket))

        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_overlap_exception(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle

        rule = LifecycleRule(random_string(10), '前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(date=datetime.date(2016, 12, 25)))
        lifecycle = BucketLifecycle([rule])

        rule2 = LifecycleRule(random_string(10), '前缀/2',
                              status=LifecycleRule.ENABLED,
                              expiration=LifecycleExpiration(date=datetime.date(2016, 12, 25)))
        lifecycle.rules.append(rule2)
        try:
            self.bucket.put_bucket_lifecycle(lifecycle)
        except oss2.exceptions.OssError as e:
            self.assertEqual(e.message, 'Overlap for same action type Expiration')
        self.bucket.delete_bucket_lifecycle()

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

        self.assertTrue(result.rules[0].tagging is None)

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
        
        self.assertTrue(result.rules[0].tagging is None)

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

        self.assertTrue(result.rules[0].tagging is None)

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
        self.assertTrue(result.rules[0].tagging is None)
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
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 20)))
        rule.storage_transitions = [StorageTransition(created_before_date=datetime.date(2016, 12, 25),
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        wait_meta_sync()
        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(1, len(result.rules[0].storage_transitions))
        self.assertEqual(datetime.date(2016, 12, 25), result.rules[0].storage_transitions[0].created_before_date)

        self.assertTrue(result.rules[0].tagging is None)

        self.bucket.delete_bucket_lifecycle()

    def test_lifecycle_object_tagging(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition, Tagging, TaggingRule

        rule = LifecycleRule(random_string(10), 'aaaaaaaaaaa/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 20)))
        rule.storage_transitions = [StorageTransition(created_before_date=datetime.date(2016, 12, 25),
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        tagging_rule = TaggingRule()
        tagging_rule.add('test_key', 'test_value')
        tagging = Tagging(tagging_rule)

        rule.tagging = tagging

        lifecycle = BucketLifecycle([rule])

        self.bucket.put_bucket_lifecycle(lifecycle)
        wait_meta_sync()
        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(1, len(result.rules[0].storage_transitions))
        self.assertEqual(datetime.date(2016, 12, 25), result.rules[0].storage_transitions[0].created_before_date)

        self.assertEqual(1, result.rules[0].tagging.tag_set.len())
        self.assertEqual('test_value', result.rules[0].tagging.tag_set.tagging_rule['test_key'])

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

    def test_lifecycle_object_tagging_exceptions_wrong_key(self):

        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition, Tagging, TaggingRule

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 20)))
        rule.storage_transitions = [StorageTransition(created_before_date=datetime.date(2016, 12, 25),
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        tagging = Tagging()
        
        tagging.tag_set.tagging_rule[129*'a'] = 'test'

        rule.tagging = tagging

        lifecycle = BucketLifecycle([rule])
        
        try:
            # do not return error,but the lifecycle rule doesn't take effect
            result = self.bucket.put_bucket_lifecycle(lifecycle)
        except oss2.exceptions.OssError:
            self.assertFalse(True, "put lifecycle with tagging should fail ,but success")
        
        del tagging.tag_set.tagging_rule[129*'a']

        tagging.tag_set.tagging_rule['%&'] = 'test'
        lifecycle.rules[0].tagging = tagging 
        try:
            # do not return error,but the lifecycle rule doesn't take effect
            result = self.bucket.put_bucket_lifecycle(lifecycle)
            self.assertFalse(True, "put lifecycle with tagging should fail ,but success")
        except oss2.exceptions.OssError:
            pass

    def test_lifecycle_object_tagging_exceptions_wrong_value(self):

        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition, Tagging, TaggingRule

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 20)))
        rule.storage_transitions = [StorageTransition(created_before_date=datetime.date(2016, 12, 25),
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        tagging = Tagging()
        
        tagging.tag_set.tagging_rule['test'] = 257*'a'

        rule.tagging = tagging

        lifecycle = BucketLifecycle([rule])
        
        try:
            # do not return error,but the lifecycle rule doesn't take effect
            result = self.bucket.put_bucket_lifecycle(lifecycle)
        except oss2.exceptions.OssError:
            self.assertFalse(True, "put lifecycle with tagging should fail ,but success")

        tagging.tag_set.tagging_rule['test'] = ')%'
        rule.tagging = tagging
        lifecycle = BucketLifecycle([rule])
        try:
            # do not return error,but the lifecycle rule doesn't take effect
            result = self.bucket.put_bucket_lifecycle(lifecycle)
            self.assertFalse(True, "put lifecycle with tagging should fail ,but success")
        except oss2.exceptions.OssError:
            pass
    def test_lifecycle_object_tagging_exceptions_too_much_rules(self):

        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition, Tagging, TaggingRule

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(created_before_date=datetime.date(2016, 12, 20)))
        rule.storage_transitions = [StorageTransition(created_before_date=datetime.date(2016, 12, 25),
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        tagging = Tagging()
        for i in range(1, 20):
            key='test_key_'+str(i)
            value='test_value_'+str(i)
            tagging.tag_set.tagging_rule[key]=value

        
        rule.tagging = tagging

        lifecycle = BucketLifecycle([rule])
        
        try:
            # do not return error,but the lifecycle rule doesn't take effect
            result = self.bucket.put_bucket_lifecycle(lifecycle)
        except oss2.exceptions.OssError:
            self.assertFalse(True, "put lifecycle with tagging should fail ,but success")

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
        bucket_name = self.OSS_BUCKET + "-test-stat"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

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

    def test_bucket_stat_all_param(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-stat-all"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        service = oss2.Service(auth, OSS_ENDPOINT)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.bucket_name in (b.name for b in
                                                         service.list_buckets(prefix=bucket.bucket_name).buckets))

        key = 'b.txt'
        bucket.put_object(key, 'content')
        wait_meta_sync()

        result = bucket.get_bucket_stat()
        self.assertEqual(1, result.object_count)
        self.assertEqual(0, result.multi_part_upload_count)
        self.assertEqual(7, result.storage_size_in_bytes)
        self.assertEqual(0, result.live_channel_count)
        self.assertIsNotNone(result.last_modified_time)
        self.assertEqual(7, result.standard_storage)
        self.assertEqual(1, result.standard_object_count)
        self.assertEqual(0, result.infrequent_access_storage)
        self.assertEqual(0, result.infrequent_access_real_storage)
        self.assertEqual(0, result.infrequent_access_object_count)
        self.assertEqual(0, result.archive_storage)
        self.assertEqual(0, result.archive_real_storage)
        self.assertEqual(0, result.archive_object_count)
        self.assertEqual(0, result.cold_archive_storage)
        self.assertEqual(0, result.cold_archive_real_storage)
        self.assertEqual(0, result.cold_archive_object_count)

        bucket.delete_object(key)
        bucket.delete_bucket()

        wait_meta_sync()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_bucket_info(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-info"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

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
        self.assertIsNotNone(result.data_redundancy_type)
        self.assertIsNotNone(result.comment)
        self.assertEqual(result.bucket_encryption_rule.sse_algorithm, None)
        self.assertEqual(result.versioning_status, None)
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

    def test_black_referer(self):
        referers = ['http://hello.com', 'mibrowser:home', '中文+referer', u'中文+referer']
        black_referers = ['http://hello2.com', 'mibrowser2:home', '中文2+referer', u'中文2+referer']
        allow_empty_referer = True
        allow_truncate_query_string = True

        # black referer 1
        config = oss2.models.BucketReferer(allow_empty_referer, referers, allow_truncate_query_string)
        self.bucket.put_bucket_referer(config)
        wait_meta_sync()

        result = self.bucket.get_bucket_referer()
        self.assertTrue(result.allow_empty_referer)
        self.assertTrue(result.allow_truncate_query_string)
        self.assertEqual(sorted(to_string(r) for r in referers), sorted(to_string(r) for r in result.referers))

        # black referer 2
        allow_empty_referer = False
        allow_truncate_query_string = False
        config = oss2.models.BucketReferer(allow_empty_referer, referers, allow_truncate_query_string, black_referers)
        self.bucket.put_bucket_referer(config)
        wait_meta_sync()

        result = self.bucket.get_bucket_referer()
        self.assertFalse(result.allow_empty_referer)
        self.assertFalse(result.allow_truncate_query_string)
        self.assertEqual(sorted(to_string(r) for r in referers), sorted(to_string(r) for r in result.referers))
        self.assertEqual(sorted(to_string(r) for r in black_referers), sorted(to_string(r) for r in result.black_referers))

        # black referer 3
        config = oss2.models.BucketReferer(allow_empty_referer, referers, black_referers=None)
        self.bucket.put_bucket_referer(config)
        wait_meta_sync()

        result = self.bucket.get_bucket_referer()
        self.assertFalse(result.allow_empty_referer)
        self.assertEqual(True, result.allow_truncate_query_string)
        self.assertEqual(sorted(to_string(r) for r in referers), sorted(to_string(r) for r in result.referers))
        self.assertEqual([], result.black_referers)

        # black referer 4
        config = oss2.models.BucketReferer(allow_empty_referer, referers, black_referers=[])
        self.bucket.put_bucket_referer(config)
        wait_meta_sync()

        result = self.bucket.get_bucket_referer()
        self.assertFalse(result.allow_empty_referer)
        self.assertEqual(True, result.allow_truncate_query_string)
        self.assertEqual(sorted(to_string(r) for r in referers), sorted(to_string(r) for r in result.referers))
        self.assertEqual([], result.black_referers)

    def test_location(self):
        result = self.bucket.get_bucket_location()
        self.assertTrue(result.location)

    def test_bucket_encryption_wrong(self):

        from oss2.models import ServerSideEncryptionRule

        self.assertRaises(oss2.exceptions.NoSuchServerSideEncryptionRule, self.bucket.get_bucket_encryption)

        rule = ServerSideEncryptionRule()
        rule.sse_algorithm = oss2.SERVER_SIDE_ENCRYPTION_AES256
        rule.kms_master_keyid = "test"

        self.assertRaises(oss2.exceptions.InvalidArgument,
                self.bucket.put_bucket_encryption, rule)

        rule.sse_algorithm = "random"
        rule.kms_master_keyid = ""
        self.assertRaises(oss2.exceptions.InvalidEncryptionAlgorithmError,
                self.bucket.put_bucket_encryption, rule)

        rule.sse_algorithm = oss2.SERVER_SIDE_ENCRYPTION_KMS 
        rule.kms_master_keyid = ""
        result = self.bucket.put_bucket_encryption(rule)
        self.assertEqual(int(result.status)/100, 2)

        rule.kms_master_keyid = None
        result = self.bucket.put_bucket_encryption(rule)
        self.assertEqual(int(result.status)/100, 2)

        result = self.bucket.get_bucket_encryption()
        self.assertEqual(result.sse_algorithm, oss2.SERVER_SIDE_ENCRYPTION_KMS)
        self.assertTrue(result.kms_master_keyid is None)

        result = self.bucket.delete_bucket_encryption()

        rule.sse_algorithm = oss2.SERVER_SIDE_ENCRYPTION_KMS
        rule.kms_master_keyid = "test_wrong"

        result = self.bucket.put_bucket_encryption(rule)
        self.assertEqual(int(result.status)/100, 2)

        result = self.bucket.get_bucket_encryption()
        self.assertEqual(result.sse_algorithm, oss2.SERVER_SIDE_ENCRYPTION_KMS)
        self.assertEqual(result.kms_master_keyid, "test_wrong")

        result = self.bucket.delete_bucket_encryption()

        self.assertEqual(int(result.status), 204)

    def test_bucket_encryption(self):

        from oss2.models import ServerSideEncryptionRule

        rule = ServerSideEncryptionRule()

        # AES256
        rule.sse_algorithm = oss2.SERVER_SIDE_ENCRYPTION_AES256
        rule.kms_master_keyid = ""

        result = self.bucket.put_bucket_encryption(rule)
        self.assertEqual(int(result.status)/100, 2)
    
        wait_meta_sync()

        result = self.bucket.get_bucket_info()
        self.assertEqual(result.bucket_encryption_rule.sse_algorithm, 'AES256')
        self.assertTrue(result.bucket_encryption_rule.kms_master_keyid is None)

        result = self.bucket.put_object("test", "test")
        self.assertEqual(int(result.status)/100, 2)
        
        result = self.bucket.get_object("test")
        self.assertEqual(int(result.status)/100, 2)

        self.assertEqual(b'test', result.read())

        result = self.bucket.delete_bucket_encryption()
        self.assertEqual(int(result.status), 204)

        # KMS
        rule.sse_algorithm = oss2.SERVER_SIDE_ENCRYPTION_KMS
        rule.kms_master_keyid = "123"

        result = self.bucket.put_bucket_encryption(rule)
        self.assertEqual(int(result.status)/100, 2)
    
        wait_meta_sync()

        result = self.bucket.get_bucket_info()
        self.assertEqual(result.bucket_encryption_rule.sse_algorithm, 'KMS')
        self.assertEqual(result.bucket_encryption_rule.kms_master_keyid, '123')

        result = self.bucket.delete_bucket_encryption()
        self.assertEqual(int(result.status), 204)

    def test_bucket_tagging(self):
        
        from oss2.models import Tagging, TaggingRule

        rule = TaggingRule()
        self.assertRaises(oss2.exceptions.ClientError, rule.add, 129*'a', 'test')
        self.assertRaises(oss2.exceptions.ClientError, rule.add, 'test', 257*'a')
        self.assertRaises(oss2.exceptions.ClientError, rule.add, None, 'test')
        self.assertRaises(oss2.exceptions.ClientError, rule.add, '', 'test')
        self.assertRaises(KeyError, rule.delete, 'not_exist')

        tagging = Tagging()
        tagging.tag_set.tagging_rule['%@abc'] = 'abc'
        tagging.tag_set.tagging_rule['123++'] = '++123%'

        try:
            result = self.bucket.put_bucket_tagging(tagging)
        except oss2.exceptions.OssError:
            self.assertFalse(True, 'should not get exception')
            pass

        result = self.bucket.get_bucket_tagging()
        tag_rule = result.tag_set.tagging_rule
        self.assertEqual(2, len(tag_rule))
        self.assertEqual('abc', tag_rule['%@abc'])
        self.assertEqual('++123%', tag_rule['123++'])

        result = self.bucket.delete_bucket_tagging()
        self.assertEqual(int(result.status), 204)

    def test_list_bucket_with_tagging(self):

        from oss2.models import Tagging, TaggingRule

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        service = oss2.Service(auth, OSS_ENDPOINT)

        bucket_name1 = self.OSS_BUCKET + "-test-with-tagging-1"
        bucket1 = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name1)

        bucket1.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        bucket_name2 = self.OSS_BUCKET + "-test-with-tagging-2"
        bucket2 = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name2)

        bucket2.create_bucket(oss2.BUCKET_ACL_PRIVATE)
        
        wait_meta_sync()

        rule = TaggingRule()
        rule.add('tagging_key_test_test1', 'value1')
        rule.add('tagging_key_test1', 'value1')

        tagging1 = Tagging(rule)
        try:
            result = bucket1.put_bucket_tagging(tagging1)
        except oss2.exceptions.OssError:
            self.assertFalse(True, 'should not get exception')
            pass

        rule = TaggingRule()
        rule.add('tagging_key2', 'value2')

        tagging2 = Tagging(rule)
        try:
            result = bucket2.put_bucket_tagging(tagging2)
        except oss2.exceptions.OssError:
            self.assertFalse(True, 'should not get exception')
            pass
        
        params = {}
        params['tag-key'] = 'tagging_key_test_test1'
        params['tag-value'] = 'value1'

        result = service.list_buckets(params=params)
        self.assertEqual(1, len(result.buckets))

        result = service.list_buckets()
        self.assertTrue(len(result.buckets) > 1)

        bucket1.delete_bucket()
        bucket2.delete_bucket()

    def test_bucket_policy(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-policy"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.get_bucket_info)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        service = oss2.Service(auth, OSS_ENDPOINT)
        wait_meta_sync()
        self.assertRaises(oss2.exceptions.NoSuchBucketPolicy, bucket.get_bucket_policy)

        policy=dict()
        policy["Version"] = "1"
        policy["Statement"] = []
        statement = dict()
        statement["Action"] = ["oss:PutObject"]
        statement["Effect"] = "Allow"
        statement["Resource"] = ["acs:oss:*:*:*/*"]
        policy["Statement"].append(statement)
        
        self.bucket.put_bucket_policy(json.dumps(policy))
        wait_meta_sync()

        result = self.bucket.get_bucket_policy()

        policy_json = json.loads(result.policy) 
        
        self.assertEqual(len(policy["Statement"]), len(policy_json["Statement"]))
        self.assertEqual(policy["Version"], policy_json["Version"])

        policy_resource = policy["Statement"][0]["Resource"][0]
        policy_json_resource = policy_json["Statement"][0]["Resource"][0]
        self.assertEqual(policy_resource, policy_json_resource)
        
        result = self.bucket.delete_bucket_policy()
        self.assertEqual(int(result.status)//100, 2)
        bucket.delete_bucket()

    def test_bucket_storage_capacity(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        # test default storage capacity
        result = bucket.get_bucket_storage_capacity()
        self.assertEqual(result.storage_capacity, -1)

        #test set default capacity value -1
        user_qos = oss2.models.BucketUserQos(-1)
        bucket.set_bucket_storage_capacity(user_qos)
        result = bucket.get_bucket_storage_capacity()
        self.assertEqual(result.storage_capacity, -1)

        #set neagetive value other than -1
        user_qos = oss2.models.BucketUserQos(-2)
        self.assertRaises(oss2.exceptions.InvalidArgument, bucket.set_bucket_storage_capacity, user_qos) 

        #set positive value
        user_qos = oss2.models.BucketUserQos(100)
        resp = bucket.set_bucket_storage_capacity(user_qos)
        result = bucket.get_bucket_storage_capacity()
        self.assertEqual(result.storage_capacity, 100)

        bucket.delete_bucket()

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


    def test_bucket_lifecycle_not(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition, LifecycleFilter, FilterNot, FilterNotTag

        not_prefix = '中文前缀/not-prefix'
        key = 'key-arg'
        value = 'value-arg'
        not_prefix2 = '中文前缀/not-prefix2'
        not_tag = FilterNotTag(key, value)
        filter_not = FilterNot(not_prefix, not_tag)
        filter_not2 = FilterNot(not_prefix2, not_tag)
        filter = LifecycleFilter([filter_not])
        # Open it after multiple not nodes are supported
        # filter = LifecycleFilter([filter_not, filter_not2])

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=356),
                             filter=filter)
        rule.storage_transitions = [StorageTransition(days=355,
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE),
                                    StorageTransition(days=352,
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        lifecycle = BucketLifecycle([rule])

        put_result = self.bucket.put_bucket_lifecycle(lifecycle)
        self.assertEqual(put_result.status, 200)

        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(2, len(result.rules[0].storage_transitions))
        self.assertEqual(355, result.rules[0].storage_transitions[0].days)
        self.assertEqual(352, result.rules[0].storage_transitions[1].days)
        self.assertEqual(result.rules[0].filter.filter_not[0].prefix, not_prefix)
        self.assertEqual(result.rules[0].filter.filter_not[0].tag.key, key)
        self.assertEqual(result.rules[0].filter.filter_not[0].tag.value, value)

    def test_bucket_lifecycle_filter_object_size_than(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition, LifecycleFilter
        filter = LifecycleFilter(object_size_greater_than=203,object_size_less_than=311)

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=356),
                             filter=filter)
        rule.storage_transitions = [StorageTransition(days=355,
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE),
                                    StorageTransition(days=352,
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        lifecycle = BucketLifecycle([rule])

        put_result = self.bucket.put_bucket_lifecycle(lifecycle)
        self.assertEqual(put_result.status, 200)

        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(2, len(result.rules[0].storage_transitions))
        self.assertEqual(355, result.rules[0].storage_transitions[0].days)
        self.assertEqual(352, result.rules[0].storage_transitions[1].days)
        self.assertEqual(result.rules[0].filter.object_size_greater_than, 203)
        self.assertEqual(result.rules[0].filter.object_size_less_than, 311)

    def test_bucket_lifecycle_not_prefix(self):
        from oss2.models import LifecycleExpiration, LifecycleRule, BucketLifecycle, StorageTransition, LifecycleFilter, FilterNot, FilterNotTag

        not_prefix = '中文前缀/not-prefix'
        key = 'key-arg'
        value = 'value-arg'
        not_prefix2 = '中文前缀/not-prefix2'
        not_tag = FilterNotTag(key, value)
        filter_not = FilterNot(not_prefix)
        filter_not2 = FilterNot(not_prefix2, not_tag)
        filter = LifecycleFilter([filter_not])

        # Open it after multiple not nodes are supported
        # filter = LifecycleFilter([filter_not, filter_not2])

        rule = LifecycleRule(random_string(10), '中文前缀/',
                             status=LifecycleRule.ENABLED,
                             expiration=LifecycleExpiration(days=356),
                             filter=filter)
        rule.storage_transitions = [StorageTransition(days=355,
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE),
                                    StorageTransition(days=352,
                                                      storage_class=oss2.BUCKET_STORAGE_CLASS_IA)]

        lifecycle = BucketLifecycle([rule])

        put_result = self.bucket.put_bucket_lifecycle(lifecycle)
        self.assertEqual(put_result.status, 200)

        result = self.bucket.get_bucket_lifecycle()
        self.assertEqual(1, len(result.rules))
        self.assertEqual(2, len(result.rules[0].storage_transitions))
        self.assertEqual(355, result.rules[0].storage_transitions[0].days)
        self.assertEqual(352, result.rules[0].storage_transitions[1].days)
        self.assertEqual(result.rules[0].filter.filter_not[0].prefix, not_prefix)
        # Open it after multiple not nodes are supported
        # self.assertEqual(result.rules[0].filter.filter_not[1].prefix, not_prefix2)
        # self.assertEqual(result.rules[0].filter.filter_not[1].tag.key, key)
        # self.assertEqual(result.rules[0].filter.filter_not[1].tag.value, value)


    def test_bucket_tagging_with_specify_label(self):

        from oss2.models import Tagging

        tagging = Tagging()
        tagging.tag_set.tagging_rule['%@abc'] = 'abc'
        tagging.tag_set.tagging_rule['123++'] = '++123%'
        tagging.tag_set.tagging_rule['test'] = 'abc'

        try:
            result = self.bucket.put_bucket_tagging(tagging)
        except oss2.exceptions.OssError:
            self.assertFalse(True, 'should not get exception')
            pass

        result = self.bucket.get_bucket_tagging()
        tag_rule = result.tag_set.tagging_rule
        self.assertEqual(3, len(tag_rule))
        self.assertEqual('abc', tag_rule['%@abc'])
        self.assertEqual('++123%', tag_rule['123++'])

        params = dict()
        params['tagging'] = "%@abc"
        result = self.bucket.delete_bucket_tagging(params=params)
        self.assertEqual(int(result.status), 204)


        params2 = dict()
        params2['aa'] = "%@abc"
        params2['tagging'] = "test"
        result = self.bucket.delete_bucket_tagging(params=params2)
        self.assertEqual(int(result.status), 204)

        result2 = self.bucket.get_bucket_tagging()
        tag_rule = result2.tag_set.tagging_rule
        self.assertEqual(1, len(tag_rule))

    def test_bucket_header_KMS_SM4(self):
        from oss2.headers import (OSS_SERVER_SIDE_ENCRYPTION, OSS_SERVER_SIDE_ENCRYPTION_KEY_ID,
                                  OSS_SERVER_SIDE_DATA_ENCRYPTION, OSS_CANNED_ACL)
        auth = oss2.Auth(OSS_ID, OSS_SECRET)

        bucket_name = self.OSS_BUCKET + "-test-1"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ)

        bucket_info = bucket.get_bucket_info()
        self.assertEqual(oss2.BUCKET_ACL_PUBLIC_READ, bucket_info.acl.grant)
        self.assertEqual(oss2.BUCKET_ACL_PUBLIC_READ, bucket_info.acl.grant)
        bucket.delete_bucket()

        bucket_name = self.OSS_BUCKET + "-test-2"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ_WRITE, oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_IA))

        bucket_info2 = bucket.get_bucket_info()
        self.assertEqual(oss2.BUCKET_ACL_PUBLIC_READ_WRITE, bucket_info2.acl.grant)
        self.assertEqual(oss2.BUCKET_STORAGE_CLASS_IA, bucket_info2.storage_class)
        bucket.delete_bucket()

        bucket_name = self.OSS_BUCKET + "-test-kms-sm4"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        headers =dict()
        headers[OSS_SERVER_SIDE_ENCRYPTION] = "KMS"
        headers[OSS_SERVER_SIDE_DATA_ENCRYPTION] = "SM4"
        headers[OSS_SERVER_SIDE_ENCRYPTION_KEY_ID] = "9468da86-3509-4f8d-a61e-6eab1eac"
        headers[OSS_CANNED_ACL] = oss2.BUCKET_ACL_PRIVATE

        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ, oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_IA), headers)
        bucket_info3 = bucket.get_bucket_info()

        self.assertEqual(oss2.BUCKET_ACL_PUBLIC_READ, bucket_info3.acl.grant)
        self.assertEqual(oss2.BUCKET_STORAGE_CLASS_IA, bucket_info3.storage_class)
        self.assertEqual("SM4", bucket_info3.bucket_encryption_rule.kms_data_encryption)
        self.assertEqual("9468da86-3509-4f8d-a61e-6eab1eac", bucket_info3.bucket_encryption_rule.kms_master_keyid)
        self.assertEqual("KMS", bucket_info3.bucket_encryption_rule.sse_algorithm)

    def test_bucket_header_SSE_KMS(self):
        from oss2.headers import (OSS_SERVER_SIDE_ENCRYPTION, OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-kms"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

        headers =dict()
        headers[OSS_SERVER_SIDE_ENCRYPTION] = "KMS"
        headers[OSS_SERVER_SIDE_ENCRYPTION_KEY_ID] = "9468da86-3509-4f8d-a61e-6eab1eac"

        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ, oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_IA), headers)
        bucket_info3 = bucket.get_bucket_info()

        self.assertEqual(oss2.BUCKET_ACL_PUBLIC_READ, bucket_info3.acl.grant)
        self.assertEqual(oss2.BUCKET_STORAGE_CLASS_IA, bucket_info3.storage_class)
        self.assertEqual("9468da86-3509-4f8d-a61e-6eab1eac", bucket_info3.bucket_encryption_rule.kms_master_keyid)
        self.assertEqual("KMS", bucket_info3.bucket_encryption_rule.sse_algorithm)

    def test_bucket_header_SM4(self):
        from oss2.headers import (OSS_SERVER_SIDE_ENCRYPTION)
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-sm4"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

        headers =dict()
        headers[OSS_SERVER_SIDE_ENCRYPTION] = "SM4"

        bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ, oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_IA), headers)
        bucket_info3 = bucket.get_bucket_info()

        self.assertEqual(oss2.BUCKET_ACL_PUBLIC_READ, bucket_info3.acl.grant)
        self.assertEqual(oss2.BUCKET_STORAGE_CLASS_IA, bucket_info3.storage_class)
        self.assertEqual("SM4", bucket_info3.bucket_encryption_rule.sse_algorithm)


    def test_bucket_with_group_id(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        service = oss2.Service(auth, OSS_ENDPOINT)

        # By getting_ bucket_ Information to obtain resource_ group_ id
        bucket_info = self.bucket.get_bucket_info()

        headers = dict()
        headers['x-oss-resource-group-id'] = bucket_info.resource_group_id
        result = service.list_buckets(prefix='oss-python-sdk-', max_keys=10, headers=headers)
        self.assertEqual(bucket_info.resource_group_id, result.buckets[0].resource_group_id)

    def test_list_buckets_with_region_list(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        service = oss2.Service(auth, OSS_ENDPOINT)
        params = {}
        params['regionList']=''
        result = service.list_buckets(params=params)
        self.assertEqual(200, result.status)
        self.assertTrue(result.buckets.__len__() > 0)

    def test_bucket_path_style(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, self.OSS_BUCKET)
        bucket2 = oss2.Bucket(auth, OSS_ENDPOINT, self.OSS_BUCKET, is_path_style=True)

        service = oss2.Service(auth, OSS_ENDPOINT)
        service2 = oss2.Service(auth, OSS_ENDPOINT, is_path_style=True)

        try:
            result = bucket.get_bucket_acl()
            self.assertEqual(200, result.status)
            self.assertEqual('private', result.acl)

            bucket2.get_bucket_acl()
        except oss2.exceptions.OssError as e:
            self.assertEqual(e.code, 'SecondLevelDomainForbidden')

        try:
            params = {}
            params['regionList']=''
            result = service.list_buckets(params=params)
            self.assertEqual(200, result.status)
            self.assertTrue(result.buckets.__len__() > 0)

            service2.list_buckets(params=params)
        except oss2.exceptions.OssError as e:
            self.assertEqual(e.code, 'SecondLevelDomainForbidden')


if __name__ == '__main__':
    unittest.main()
