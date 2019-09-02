# -*- coding: utf-8 -*-


import datetime
import json

from .common import *
from oss2 import to_string


class TestObjectVersioning(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)
        self.endpoint = "http://oss-ap-south-1.aliyuncs.com"

    def test_resumable_download_with_version(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-resumable-download-with-version"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        config = BucketVersioningConfig()
        config.status = 'Enabled'

        result = bucket.put_bucket_versioning(config)

        wait_meta_sync()

        key = "test_resumable_download_with_version-object"
        content_version1 = random_bytes(5*1024)
        content_version2 = random_bytes(5*1024*1024)

        # Put object version1
        result = bucket.put_object(key, content_version1)
        versionid1 = result.versionid

        # Put object version2
        result = bucket.put_object(key, content_version2)
        versionid2 = result.versionid

        # Resumable download object verison1, and check file length.
        filename = self.random_filename()
        oss2.resumable_download(bucket, key, filename, params={'versionId':versionid1})
        self.assertFileContent(filename, content_version1)

        # Resumable download object verison2, and check file length.
        filename = self.random_filename()
        oss2.resumable_download(bucket, key, filename, params={'versionId':versionid2})
        self.assertFileContent(filename, content_version2)

        version_list = BatchDeleteObjectVersionList()
        version_list.append(BatchDeleteObjectVersion(key, versionid1))
        version_list.append(BatchDeleteObjectVersion(key, versionid2))

        result = bucket.delete_object_versions(version_list)
        self.assertTrue(len(result.delete_versions) == 2)

        bucket.delete_bucket()

    def test_multipart_with_versionging(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList
        from oss2.utils import calc_obj_crc_from_parts

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-multipart-with-versionging"
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
        

        key = self.random_key()
        content = random_bytes(128 * 1024)

        parts = []
        upload_id = bucket.init_multipart_upload(key).upload_id

        headers = {'Content-Md5': oss2.utils.content_md5(content)}

        result = bucket.upload_part(key, upload_id, 1, content, headers=headers)
        parts.append(oss2.models.PartInfo(1, result.etag, size=len(content), part_crc=result.crc))
        self.assertTrue(result.crc is not None)

        complete_result = bucket.complete_multipart_upload(key, upload_id, parts)

        object_crc = calc_obj_crc_from_parts(parts)
        self.assertTrue(complete_result.crc is not None)
        self.assertEqual(object_crc, result.crc)
        self.assertTrue(complete_result.versionid is not None)

        bucket.delete_object(key, params={'versionId': complete_result.versionid})

        try:
            bucket.delete_bucket()
        except:
            self.assertFalse(True, "should not get a exception")

    def test_upload_part_copy_with_versioning(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-upload-part-copy-with-versioning"
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

        src_object = self.random_key()
        dst_object = self.random_key()

        content = random_bytes(200 * 1024)
        content2 = random_bytes(200 * 1024)

        # 上传源文件 version1
        put_result1 = bucket.put_object(src_object, content)
        self.assertTrue(put_result1.versionid is not None)
        versionid1 = put_result1.versionid

        # 上传源文件 version2
        put_result2 = bucket.put_object(src_object, content2)
        self.assertTrue(put_result2.versionid is not None)
        versionid2 = put_result2.versionid

        # part copy到目标文件
        parts = []
        upload_id = bucket.init_multipart_upload(dst_object).upload_id

        result = bucket.upload_part_copy(bucket_name, src_object,
                                              (0, 100 * 1024 - 1), dst_object, upload_id, 1)
        parts.append(oss2.models.PartInfo(1, result.etag))

        result = bucket.upload_part_copy(bucket_name, src_object,
                        (100*1024, None), dst_object, upload_id, 2, params={'versionId': versionid1})

        parts.append(oss2.models.PartInfo(2, result.etag))

        complete_result = bucket.complete_multipart_upload(dst_object, upload_id, parts)

        # 验证
        content_got = bucket.get_object(dst_object).read()
        self.assertEqual(len(content_got), len(content))
        self.assertTrue(content_got != content)

        version_list = BatchDeleteObjectVersionList()
        version_list.append(BatchDeleteObjectVersion(key=src_object, versionid=versionid1))
        version_list.append(BatchDeleteObjectVersion(key=src_object, versionid=versionid2))
        version_list.append(BatchDeleteObjectVersion(key=dst_object, versionid=complete_result.versionid))

        self.assertTrue(version_list.len(), 3)

        result = bucket.delete_object_versions(version_list)

        try:
            bucket.delete_bucket()
        except:
            self.assertFalse(True, "should not get a exception")

    def test_put_symlink_with_version(self):

        from oss2.models import BucketVersioningConfig

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-put-symlink-with-version"
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

        result = bucket.put_object("test", "test")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid = result.versionid
        object_version = result.versionid

        params = dict()
        params['versionId'] = result.versionid

        result = bucket.put_symlink("test", "test_link")
        self.assertEqual(int(result.status)/100, 2)

        params['versionId'] = result.versionid
        result = bucket.get_symlink("test_link", params=params)
        self.assertEqual(int(result.status)/100, 2)

        result = bucket.delete_object("test_link")
        self.assertEqual(int(result.status), 204)
        self.assertTrue(result.versionid != '')
        delete_marker_versionid = result.versionid

        try:
            result = bucket.get_symlink("test_link")
        except oss2.exceptions.NotFound:
            pass

        self.assertEqual(result.delete_marker, True)

        result = bucket.delete_object("test_link", params=params)
        self.assertEqual(int(result.status), 204)

        params['versionId'] = delete_marker_versionid
        result = bucket.delete_object("test_link", params=params)
        self.assertEqual(int(result.status), 204)

        params['versionId'] = object_version 
        result = bucket.delete_object("test", params=params)
        self.assertEqual(int(result.status), 204)

        bucket.delete_bucket()

    def test_put_object_tagging_with_versioning(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import Tagging

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-put-object-tagging-version"
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

        result = bucket.put_object("test", "test1")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid1 = result.versionid
        
        result = bucket.put_object("test", "test2")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid2 = result.versionid

        self.assertTrue(versionid1 != versionid2)

        tagging = Tagging()

        tagging.tag_set.add('k1', 'v1')
        tagging.tag_set.add('+++', ':::')
        
        # put object tagging without version
        result = bucket.put_object_tagging("test", tagging)
        self.assertEqual(int(result.status)/100, 2)

        params = dict()
        params['versionId'] = versionid2

        result = bucket.get_object_tagging("test", params=params)
        self.assertEqual(int(result.status)/100, 2)

        rule = result.tag_set.tagging_rule

        self.assertEqual('v1', rule['k1'])
        self.assertEqual(':::', rule['+++'])

        tagging = Tagging()

        tagging.tag_set.add('k2', 'v2')
        tagging.tag_set.add(':::', '+++')

        params['versionId'] = versionid1

        # put object tagging with version
        result = bucket.put_object_tagging("test", tagging, params=params)
        self.assertEqual(int(result.status)/100, 2)

        result = bucket.get_object_tagging("test", params=params)
        self.assertEqual(int(result.status)/100, 2)

        rule = result.tag_set.tagging_rule

        self.assertEqual('v2', rule['k2'])
        self.assertEqual('+++', rule[':::'])
    
        result = bucket.delete_object_tagging("test", params=params) 
        self.assertEqual(int(result.status), 204)

        params['versionId'] = versionid2

        result = bucket.delete_object_tagging("test", params=params) 
        self.assertEqual(int(result.status), 204)


        result = bucket.delete_object("test")
        self.assertEqual(int(result.status), 204)
        delete_marker_versionid = result.versionid
        self.assertTrue(delete_marker_versionid is not None)

        params['versionId'] = versionid2

        try:
            result = bucket.get_object("test", params=params)
            self.assertFalse(True)
        except:
            pass

        # delete 'DELETE' mark
        bucket.delete_object("test", params={'versionId': delete_marker_versionid})

        bucket.delete_object("test", params={'versionId': versionid1})
        bucket.delete_object("test", params={'versionId': versionid2})

        bucket.delete_bucket()

    def test_batch_delete_same_object_multi_version(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-batch-delete-version"
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
        
        # put version 1
        result = bucket.put_object("test", "test1")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid1 = result.versionid

        # put version 2
        result = bucket.put_object("test", "test2")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid2 = result.versionid

        version_list = BatchDeleteObjectVersionList()
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid1))
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid2))

        self.assertTrue(version_list.len(), 2)

        result = bucket.delete_object_versions(version_list)

        self.assertTrue(len(result.delete_versions) == 2)
        self.assertTrue(result.delete_versions[0].versionid == versionid1 
                or result.delete_versions[0].versionid == versionid2)
        self.assertTrue(result.delete_versions[1].versionid == versionid1 
                or result.delete_versions[1].versionid == versionid2)

        result = bucket.delete_object_versions(version_list)

        try:
            bucket.delete_bucket()
        except:
            self.assertFalse(True, "should not get a exception")

    def test_batch_delete_objects_multi_version(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-batch-delete-objects-version"
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
        
        # put "test" version 1
        result = bucket.put_object("test", "test1")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid1 = result.versionid

        # put "test" version 2
        result = bucket.put_object("test", "test2")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid2 = result.versionid

        # put "foo" version 1 
        result = bucket.put_object("foo", "bar")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid2 = result.versionid

        result = bucket.list_object_versions()
        self.assertTrue(result.is_truncated == False)
        self.assertTrue(result.key_marker == '')
        self.assertTrue(result.versionid_marker == '')
        self.assertTrue(result.next_key_marker == '')
        self.assertTrue(result.next_versionid_marker == '')
        self.assertTrue(result.name == bucket_name)
        self.assertTrue(result.prefix == '')
        self.assertTrue(result.delimiter == '')
        self.assertTrue(len(result.delete_marker) == 0)
        self.assertTrue(len(result.versions) == 3)
        self.assertTrue(result.versions[0].key == "foo")
        self.assertTrue(result.versions[1].key == "test")

        # batch delete without version
        key_list = []
        key_list.append("foo")
        key_list.append("test")

        result = bucket.batch_delete_objects(key_list)

        self.assertTrue(len(result.delete_versions) == 2)
        self.assertTrue(len(result.deleted_keys) == 2)
        self.assertTrue(result.delete_versions[0].delete_marker == True)
        self.assertTrue(result.delete_versions[1].delete_marker == True)

        result = bucket.list_object_versions()
        self.assertTrue(result.is_truncated == False)
        self.assertTrue(result.key_marker == '')
        self.assertTrue(result.versionid_marker == '')
        self.assertTrue(result.next_key_marker == '')
        self.assertTrue(result.next_versionid_marker == '')
        self.assertTrue(result.prefix == '')
        self.assertTrue(result.delimiter == '')
        self.assertTrue(len(result.delete_marker) == 2)
        self.assertTrue(len(result.versions) == 3)
        self.assertTrue(result.versions[0].key == "foo")
        self.assertTrue(result.versions[1].key == "test")

        version_list = BatchDeleteObjectVersionList()
        version_list.append(BatchDeleteObjectVersion(result.delete_marker[0].key, result.delete_marker[0].versionid))
        version_list.append(BatchDeleteObjectVersion(result.delete_marker[1].key, result.delete_marker[1].versionid))
        version_list.append(BatchDeleteObjectVersion(result.versions[0].key, result.versions[0].versionid))
        version_list.append(BatchDeleteObjectVersion(result.versions[1].key, result.versions[1].versionid))
        version_list.append(BatchDeleteObjectVersion(result.versions[2].key, result.versions[2].versionid))

        result = bucket.delete_object_versions(version_list)

        self.assertTrue(len(result.delete_versions) == 5)

        
        try:
            bucket.delete_bucket()
        except:
            self.assertFalse(True, "should not get a exception")

    def test_get_object_meta_with_version(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-get-object-meta-version"
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
        
        # put "test" version 1
        result = bucket.put_object("test", "test1")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid1 = result.versionid

        # put "test" version 2
        result = bucket.put_object("test", "test2")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid2 = result.versionid

        try:
            result_exception = bucket.get_object_meta("test", params={"versionId": None})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        try:
            result_normal = bucket.get_object_meta("test", params={"versionId": ''})
            self.assertFalse(True, "should get a exception")
        except:
            pass


        result1 = bucket.get_object_meta("test", params={"versionId": versionid1})
        result2 = bucket.get_object_meta("test", params={"versionId": versionid2})

        self.assertTrue(result1.versionid == versionid1)
        self.assertTrue(result2.versionid == versionid2)
        self.assertTrue(result1.content_length == result2.content_length)

        version_list = BatchDeleteObjectVersionList()
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid1))
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid2))

        self.assertTrue(version_list.len(), 2)

        result = bucket.delete_object_versions(version_list)

        try:
            bucket.delete_bucket()
        except:
            self.assertFalse(True, "should not get a exception")

    def test_object_acl_with_version(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-object-acl-version"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        # put "test"
        result = bucket.put_object("test_no_version", "test1")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid is None)

        result = bucket.get_object_acl("test_no_version")

        bucket.delete_object("test_no_version")

        config = BucketVersioningConfig()
        config.status = 'Enabled'

        result = bucket.put_bucket_versioning(config)

        wait_meta_sync()

        result = bucket.get_bucket_info()

        self.assertEqual(int(result.status)/100, 2)
        self.assertEqual(result.bucket_encryption_rule.sse_algorithm, None)
        self.assertEqual(result.versioning_status, "Enabled")
        
        # put "test" version 1
        result = bucket.put_object("test", "test1")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid1 = result.versionid

        # put "test" version 2
        result = bucket.put_object("test", "test2")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid2 = result.versionid
    
        try:
            result_exception = bucket.put_object_acl("test", oss2.OBJECT_ACL_DEFAULT, 
                    params={'versionId': 'IllegalVersion'})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        try:
            result_exception = bucket.put_object_acl("test", oss2.OBJECT_ACL_DEFAULT, 
                    params={'versionId': ''})
            self.assertFalse(True, "should get a exception")
        except:
            pass

    
        try:
            result_exception = bucket.get_object_acl("test", params={'versionId': 'IllegalVersion'})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        try:
            result_exception = bucket.get_object_acl("test", params={'versionId': ''})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        result = bucket.get_object_acl("test", params={"versionId": versionid2})
        self.assertEqual(result.acl, oss2.OBJECT_ACL_DEFAULT)

        result = bucket.put_object_acl("test", oss2.OBJECT_ACL_PUBLIC_READ, params={"versionId": versionid2})
        self.assertEqual(int(result.status)/100, 2)

        result = bucket.get_object_acl("test", params={"versionId": versionid2})
        self.assertEqual(result.acl, oss2.OBJECT_ACL_PUBLIC_READ)

        version_list = BatchDeleteObjectVersionList()
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid1))
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid2))

        self.assertTrue(version_list.len(), 2)

        result = bucket.delete_object_versions(version_list)

        try:
            bucket.delete_bucket()
        except:
            self.assertFalse(True, "should not get a exception")

    def test_head_object_with_version(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-head-object-version"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        # put "test" version 1
        result = bucket.put_object("test_no_version", "test")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid is None)

        try:
            result_exception = bucket.head_object("test_no_version", params={"versionId": "IllegalVersion"})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        bucket.delete_object("test_no_version")

        config = BucketVersioningConfig()
        config.status = 'Enabled'

        result = bucket.put_bucket_versioning(config)

        wait_meta_sync()

        result = bucket.get_bucket_info()

        self.assertEqual(int(result.status)/100, 2)
        self.assertEqual(result.bucket_encryption_rule.sse_algorithm, None)
        self.assertEqual(result.versioning_status, "Enabled")
        
        # put "test" version 1
        result = bucket.put_object("test", "test1")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid1 = result.versionid

        # put "test" version 2
        headers = {}
        headers['x-oss-storage-class'] = oss2.BUCKET_STORAGE_CLASS_ARCHIVE
        result = bucket.put_object("test", "test2", headers=headers)
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid2 = result.versionid

        try:
            result_exception = bucket.head_object("test", params={"versionId": None})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        try:
            result_normal = bucket.head_object("test", params={"versionId": ''})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        try:
            result_exception = bucket.head_object("test_no_version", params={"versionId": "IllegalVersion"})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        try:
            result_exception = bucket.head_object("test", 
                    params={"versionId": "CAEQJhiBgIDVmYrr1RYiIGE5ZmUxMjViZDIwYjQwY2I5ODA1YWIxNmIyNDNjYjk4"})
            self.assertFalse(True, "should get a exception")
        except:
            pass


        result1 = bucket.head_object("test", params={"versionId": versionid1})

        result2 = bucket.head_object("test", params={"versionId": versionid2})

        result3 = bucket.head_object("test")
        self.assertEqual(result2.versionid, result3.versionid)

        self.assertEqual(result1.object_type, result2.object_type)
        self.assertEqual(result1.content_type, result2.content_type)
        self.assertEqual(result1.content_length, result2.content_length)
        self.assertTrue(result1.etag != result2.etag)

        delete_result = bucket.delete_object("test")
        delete_marker_versionid = delete_result.versionid

        try:
            result3 = bucket.head_object("test", params={'versionId': delete_marker_versionid})
            self.assertFalse(True, "should get a exception, but not")
        except:
            pass

        version_list = BatchDeleteObjectVersionList()
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid1))
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid2))
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=delete_marker_versionid))

        self.assertTrue(version_list.len(), 3)

        result = bucket.delete_object_versions(version_list)

        try:
            bucket.delete_bucket()
        except:
            self.assertFalse(True, "should not get a exception")

    def test_copy_object_with_version(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-copy-object-version"
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
        
        # put "test" version 1
        result = bucket.put_object("test", "test1")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid1 = result.versionid

        # put "test" version 2
        result = bucket.put_object("test", "test2")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid2 = result.versionid

        try:
            result_exception = bucket.copy_object(bucket_name, 
                    "test", "test_copy_wrong", params={"versionId": None})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        try:
            result_exception = bucket.copy_object(bucket_name, 
                    "test", "test_copy_wrong", params={"versionId": ''})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        try:
            result_exception = bucket.copy_object(bucket_name, 
                    "test", "test_copy_wrong", params={"versionId": 'NotExistVersionID'})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        result = bucket.copy_object(bucket_name, "test", "test_copy", params={'versionId': versionid1})

        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        copy_versionid = result.versionid

        version_list = BatchDeleteObjectVersionList()
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid1))
        version_list.append(BatchDeleteObjectVersion(key="test", versionid=versionid2))
        version_list.append(BatchDeleteObjectVersion(key="test_copy", versionid=copy_versionid))

        self.assertTrue(version_list.len(), 3)

        result = bucket.delete_object_versions(version_list)

        try:
            bucket.delete_bucket()
        except:
            self.assertFalse(True, "should not get a exception")

    def test_delete_object_with_version(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-delete-object-version"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        # put "test" version 1
        result = bucket.put_object("test_no_version", "test")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid is None)

        try:
            result_exception = bucket.head_object("test_no_version", params={"versionId": "IllegalVersion"})
            self.assertFalse(True, "should get a exception")
        except:
            pass
        
        try:
            bucket.delete_object("test_no_version", params={"versionId": None})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        try:
            bucket.delete_object("test_no_version", params={"versionId": ""})
            self.assertFalse(True, "should get a exception")
        except:
            pass

        bucket.delete_object("test_no_version")

        config = BucketVersioningConfig()
        config.status = 'Enabled'

        result = bucket.put_bucket_versioning(config)

        wait_meta_sync()

        result = bucket.get_bucket_info()

        self.assertEqual(int(result.status)/100, 2)
        self.assertEqual(result.bucket_encryption_rule.sse_algorithm, None)
        self.assertEqual(result.versioning_status, "Enabled")
        
        # put "test" version 1
        result = bucket.put_object("test", "test1")
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid1 = result.versionid

        # put "test" version 2
        headers = {}
        headers['x-oss-storage-class'] = oss2.BUCKET_STORAGE_CLASS_ARCHIVE
        result = bucket.put_object("test", "test2", headers=headers)
        self.assertEqual(int(result.status)/100, 2)
        self.assertTrue(result.versionid != "")
        versionid2 = result.versionid

        bucket.delete_object("test", params={'versionId': versionid1})
        bucket.delete_object("test", params={'versionId': versionid2})
        bucket.delete_bucket()

    def test_restore_object_with_version(self):

        from oss2.models import BucketVersioningConfig

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-restore-object-version"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE, oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_ARCHIVE))

        service = oss2.Service(auth, OSS_ENDPOINT)

        config = BucketVersioningConfig()
        config.status = 'Enabled'

        result = bucket.put_bucket_versioning(config)

        wait_meta_sync()

        self.retry_assert(lambda: bucket.bucket_name in (b.name for b in
                                                         service.list_buckets(prefix=bucket.bucket_name).buckets))

        key = 'a.txt'
        result = bucket.put_object(key, 'content_version1')
        self.assertEqual(202, bucket.restore_object(key).status)
        version1 = result.versionid

        result = bucket.put_object(key, 'content_version2')
        version2 = result.versionid

        result = bucket.restore_object(key, params={'versionId': version2})
        self.assertEqual(202, result.status)

        bucket.delete_object(key, params={'versionId': version1})
        bucket.delete_object(key, params={'versionId': version2})
        bucket.delete_bucket()


if __name__ == '__main__':
    unittest.main()
