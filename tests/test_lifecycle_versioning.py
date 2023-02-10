# -*- coding: utf-8 -*-


import datetime
import json

from .common import *
from oss2 import to_string
from oss2.models import (BucketVersioningConfig,
                         TaggingRule,
                         Tagging,
                         LifecycleRule,
                         AbortMultipartUpload,
                         BucketLifecycle,
                         LifecycleExpiration,
                         StorageTransition,
                         NoncurrentVersionStorageTransition,
                         NoncurrentVersionExpiration)


class TestLifecycleVersioning(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)
        self.endpoint = OSS_ENDPOINT

    def test_lifecycle_without_versioning(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-lifecycle-without-versioning"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)
        wait_meta_sync()

        rule1 = LifecycleRule('rule1', 'tests/',
                    status=LifecycleRule.ENABLED,
                    expiration=LifecycleExpiration(days=3))

        rule2 = LifecycleRule('rule2', 'logging-',
                    status=LifecycleRule.ENABLED,
                    expiration=LifecycleExpiration(created_before_date=datetime.date(2020, 12, 12)))

        rule3 = LifecycleRule('rule3', 'tests1/',
                    status=LifecycleRule.ENABLED,
                    abort_multipart_upload=AbortMultipartUpload(days=3))

        rule4 = LifecycleRule('rule4', 'logging1-',
                    status=LifecycleRule.ENABLED,
                    abort_multipart_upload=AbortMultipartUpload(created_before_date=datetime.date(2020, 12, 12)))

        tagging_rule = TaggingRule()
        tagging_rule.add('test_key1', 'test_value1')
        tagging_rule.add('test_key2', 'test_value2')
        tagging = Tagging(tagging_rule)
        rule5 = LifecycleRule('rule5', 'logging2-',
                      status=LifecycleRule.ENABLED,
                      storage_transitions=
                      [StorageTransition(days=100, storage_class=oss2.BUCKET_STORAGE_CLASS_IA), 
                       StorageTransition(days=356, storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE)],
                      tagging = tagging)
        
        lifecycle = BucketLifecycle([rule1, rule2, rule3, rule4, rule5])

        bucket.put_bucket_lifecycle(lifecycle)

        lifecycle = bucket.get_bucket_lifecycle()
        self.assertEquals(5, len(lifecycle.rules))

        bucket.delete_bucket()

    def test_lifecycle_versioning(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-lifecycle-versioning"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)
        wait_meta_sync()

        rule = LifecycleRule('rule1', 'test-prefix',
                      status=LifecycleRule.ENABLED,
                      expiration=LifecycleExpiration(expired_detete_marker=True),
                      noncurrent_version_expiration = NoncurrentVersionExpiration(30),
                      noncurrent_version_sotrage_transitions = 
                            [NoncurrentVersionStorageTransition(12, oss2.BUCKET_STORAGE_CLASS_IA),
                             NoncurrentVersionStorageTransition(20, oss2.BUCKET_STORAGE_CLASS_ARCHIVE)])

        lifecycle = BucketLifecycle([rule])

        bucket.put_bucket_lifecycle(lifecycle)

        lifecycle = bucket.get_bucket_lifecycle()
        self.assertEquals(1, len(lifecycle.rules))
        self.assertEqual('rule1', lifecycle.rules[0].id)
        self.assertEqual('test-prefix', lifecycle.rules[0].prefix)
        self.assertEquals(LifecycleRule.ENABLED, lifecycle.rules[0].status)
        self.assertEquals(True, lifecycle.rules[0].expiration.expired_detete_marker)
        self.assertEquals(30, lifecycle.rules[0].noncurrent_version_expiration.noncurrent_days)
        self.assertEquals(2, len(lifecycle.rules[0].noncurrent_version_sotrage_transitions))
        bucket.delete_bucket()
        
    def test_lifecycle_veriong_wrong(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-lifecycle-versioning-wrong"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)
        wait_meta_sync()
        # days and expired_detete_marker cannot both exsit.
        self.assertRaises(oss2.exceptions.ClientError, LifecycleExpiration, days=10, expired_detete_marker=True)

        rule = LifecycleRule('rule1', 'test-prefix',
                      status=LifecycleRule.ENABLED,
                      expiration=LifecycleExpiration(expired_detete_marker=True),
                      noncurrent_version_expiration = NoncurrentVersionExpiration(30),
                      noncurrent_version_sotrage_transitions = 
                            [NoncurrentVersionStorageTransition(20, oss2.BUCKET_STORAGE_CLASS_IA),
                             NoncurrentVersionStorageTransition(12, oss2.BUCKET_STORAGE_CLASS_ARCHIVE)])

        lifecycle = BucketLifecycle([rule])

        # Archive transition days < IA transition days
        self.assertRaises(oss2.exceptions.InvalidArgument, bucket.put_bucket_lifecycle, lifecycle)

        bucket.delete_bucket()


if __name__ == '__main__':
    unittest.main()
