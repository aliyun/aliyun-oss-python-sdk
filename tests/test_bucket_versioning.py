# -*- coding: utf-8 -*-


import datetime
import json

from .common import *
from oss2 import to_string


class TestBucketVersioning(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)
        self.endpoint = "http://oss-ap-south-1.aliyuncs.com"

    def test_bucket_versioning_wrong(self):

        from oss2.models import BucketVersioningConfig
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-bucket-versioning-wrong"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        config = BucketVersioningConfig()

        self.assertRaises(oss2.exceptions.MalformedXml, 
                bucket.put_bucket_versioning, config)

        config.status = "Disabled"
        self.assertRaises(oss2.exceptions.MalformedXml, 
                bucket.put_bucket_versioning, config)

    def test_bucket_versioning(self):

        from oss2.models import BucketVersioningConfig

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-versioning"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)

        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.get_bucket_info)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        result = bucket.get_bucket_versioning()
        
        self.assertTrue(result.status is None)

        config = BucketVersioningConfig()

        config.status = oss2.BUCKET_VERSIONING_ENABLE 
        result = bucket.put_bucket_versioning(config)
        self.assertEqual(int(result.status)/100, 2)
        
        wait_meta_sync()

        result = bucket.get_bucket_info()
        self.assertEqual(result.bucket_encryption_rule.sse_algorithm, None)
        self.assertEqual(result.versioning_status, 'Enabled')

        config.status = oss2.BUCKET_VERSIONING_SUSPEND 
        result = bucket.put_bucket_versioning(config)
        self.assertEqual(int(result.status)/100, 2)

        bucket.delete_bucket()

    def test_list_object_versions_wrong(self):
        from oss2.models import BucketVersioningConfig

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-list-object-versions-wrong"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)

        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.get_bucket_info)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        config = BucketVersioningConfig()

        config.status = "Enabled"
        result = bucket.put_bucket_versioning(config)
        self.assertEqual(int(result.status)/100, 2)

        result = bucket.put_object("test", "test1")
        self.assertEqual(int(result.status)/100, 2)
        versionid1 = result.versionid
        
        result = bucket.put_object("test", "test2")
        self.assertEqual(int(result.status)/100, 2)
        versionid2 = result.versionid

        self.assertRaises(oss2.exceptions.InvalidArgument, 
                bucket.list_object_versions, prefix=1025*'a')

        self.assertRaises(oss2.exceptions.InvalidArgument, 
                bucket.list_object_versions, key_marker=1025*'a')

        self.assertRaises(oss2.exceptions.InvalidArgument, 
                bucket.list_object_versions, versionid_marker=1025*'a')

        self.assertRaises(oss2.exceptions.InvalidArgument, 
                bucket.list_object_versions, delimiter=1025*'a')

        self.assertRaises(oss2.exceptions.InvalidArgument, 
                bucket.list_object_versions, max_keys=1001)

        result = bucket.list_object_versions()
        self.assertEqual(len(result.versions), 2)
        self.assertEqual(result.versions[0].versionid, versionid2)
        self.assertEqual(result.versions[1].versionid, versionid1)
        self.assertEqual(len(result.delete_marker), 0)

        bucket.delete_object("test", {"versionId": versionid1})
        bucket.delete_object("test", {"versionId": versionid2})

        bucket.delete_bucket()

    def test_list_object_versions_truncated(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-list-object-versions-truncated"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        config = BucketVersioningConfig()
        config.status = 'Enabled'

        result = bucket.put_bucket_versioning(config)

        wait_meta_sync()

        result = bucket.get_bucket_info()

        self.assertEqual(int(result.status)/100, 2)
        self.assertEqual(result.bucket_encryption_rule.sse_algorithm, None)
        self.assertEqual(result.versioning_status, "Enabled")

        for i in range(0, 50):
            bucket.put_object("test", "test"+str(i))

        loop_time = 0
        next_key_marker = ''
        next_version_marker = ''
        delete_versions = []

        while True:

            result = bucket.list_object_versions(max_keys=20, key_marker=next_key_marker, versionid_marker=next_version_marker)
            self.assertTrue(len(result.versions) > 0)
            self.assertTrue(len(result.delete_marker) == 0)
            version_list = BatchDeleteObjectVersionList()
            for item in result.versions:
                version_list.append(BatchDeleteObjectVersion(item.key, item.versionid))
            delete_versions.append(version_list)
            
            if result.is_truncated:
                next_key_marker = result.next_key_marker
                next_version_marker = result.next_versionid_marker
            else:
                break

            loop_time += 1
            if loop_time > 12:
                self.assertFalse(True, "loop too much times, break")
        
        for item in delete_versions:
            result = bucket.delete_object_versions(item)

        try:
            bucket.delete_bucket()
        except:
            self.assertFalse(True, "should not get a exception")

if __name__ == '__main__':
    unittest.main()
