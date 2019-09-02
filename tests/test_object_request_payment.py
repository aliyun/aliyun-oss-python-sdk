# -*- coding: utf-8 -*-

import oss2
from .common import *
from oss2.headers import OSS_REQUEST_PAYER, OSS_OBJECT_TAGGING
from oss2.models import PAYER_REQUESTER, PartInfo, Tagging, TaggingRule
from oss2 import determine_part_size, SizedFileAdapter
import base64
import os


class TestObjectRequestPayment(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)
        policy_text = ''
        policy_text += '{'
        policy_text += '"Version":"1",'
        policy_text += '"Statement":[{'
        policy_text += '"Action":["oss:*"],'
        policy_text += '"Effect":"Allow",'
        policy_text += '"Principal":["{0}"],'.format(OSS_PAYER_UID)
        policy_text += '"Resource": ["acs:oss:*:*:{0}","acs:oss:*:*:{0}/*"]'.format(OSS_BUCKET)
        policy_text += '}]}'
        self.bucket.put_bucket_policy(policy_text)

        # Enable bucket request payment
        result = self.bucket.put_bucket_request_payment(PAYER_REQUESTER)
        self.assertEqual(result.status, 200)

        self.payer_bucket = oss2.Bucket(oss2.Auth(OSS_PAYER_ID, OSS_PAYER_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    def test_put_object(self):
        key = 'requestpayment-test-put-object'
        content = 'test-content'

        # Put object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.put_object, key, content)

        # Put object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.put_object(key, content, headers=headers)
        self.assertEqual(result.status, 200)

        self.bucket.delete_object(key)

    def test_get_object(self):
        key = 'requestpayment-test-get-object'
        content = 'test-content'

        self.bucket.put_object(key, content)

        # Get object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.get_object, key)

        # Put object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.get_object(key, headers=headers)
        self.assertEqual(result.status, 200)

        self.bucket.delete_object(key)

    def test_delete_object(self):
        key = 'requestpayment-test-delete-object'
        content = 'test-content'

        self.bucket.put_object(key, content)

        # Delete object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.delete_object, key)

        # Delete object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.delete_object(key, headers=headers)
        self.assertEqual(result.status, 204)

    def test_batch_delete_object(self):
        key1 = 'requestpayment-test-batch-delete-object1'
        key2 = 'requestpayment-test-batch-delete-object2'
        content = 'test-content'

        objects = [key1, key2]

        self.bucket.put_object(key1, content)
        self.bucket.put_object(key2, content)

        # Delete objects without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.batch_delete_objects, objects)

        # Delete objects with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.batch_delete_objects(objects, headers=headers)
        self.assertEqual(result.status, 200)

    def test_apend_object(self):
        key = 'requestpayment-test-apend-object'
        content1 = '123'
        content2 = '456'

        self.bucket.append_object(key, 0, content1)

        # Append object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.append_object, key, 3, content2)

        # Append object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.append_object(key, 3,  content2, headers=headers)
        self.assertEqual(result.status, 200)

        self.bucket.delete_object(key)

    def test_put_object_acl(self):
        key = 'requestpayment-test-put-object-acl'
        content = '123'
        acl = oss2.OBJECT_ACL_PUBLIC_READ

        self.bucket.put_object(key, content)

        # Put object acl without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.put_object_acl, key, acl)

        # Put object acl with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        self.payer_bucket.put_object_acl(key, acl, headers=headers)

        # Check
        result = self.bucket.get_object_acl(key)
        self.assertEqual(result.acl, acl)

        self.bucket.delete_object(key)

    def test_get_object_acl(self):
        key = 'requestpayment-test-get-object-acl'
        content = '123'
        acl = oss2.OBJECT_ACL_PUBLIC_READ

        self.bucket.put_object(key, content)
        self.bucket.put_object_acl(key, acl)

        # Get object acl without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.get_object_acl, key)

        # Get object acl with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.get_object_acl(key, headers=headers)
        self.assertEqual(result.acl, acl)

        self.bucket.delete_object(key)

    def test_put_symlink(self):
        target_object = 'requestpayment-test-put-symlink-object'
        symlink = 'requestpayment-test-put-symlink-symlink'
        content = '123'

        self.bucket.put_object(target_object, content)

        # Put symlink without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.put_symlink, target_object, symlink)

        # Put symlink with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.put_symlink(target_object, symlink, headers=headers)
        self.assertEqual(result.status, 200)

        self.bucket.delete_object(target_object)
        self.bucket.delete_object(symlink)

    def test_get_symlink(self):
        target_object = 'requestpayment-test-get-symlink-object'
        symlink = 'requestpayment-test-get-symlink-symlink'
        content = '123'

        self.bucket.put_object(target_object, content)
        self.bucket.put_symlink(target_object, symlink)

        # Gett symlink without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.put_symlink, target_object, symlink)

        # Get symlink with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.get_symlink(symlink, headers=headers)
        self.assertEqual(result.target_key, target_object)

        self.bucket.delete_object(target_object)
        self.bucket.delete_object(symlink)

    def test_copy_object(self):
        src_object_name = 'requestpayment-test-copy-object-src'
        dest_object_name = 'requestpayment-test-copy-object-dest'
        content = '123'
        bucket_name = self.bucket.bucket_name

        self.bucket.put_object(src_object_name, content)

        # Copy object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.copy_object, bucket_name, 
                        src_object_name, dest_object_name)

        # Copy object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.copy_object(bucket_name, src_object_name, dest_object_name, headers=headers)
        self.assertEqual(result.status, 200)

        self.bucket.delete_object(src_object_name)
        self.bucket.delete_object(dest_object_name)

    def test_upload_part(self):
        key = 'requestpayment-test-upload-part-object'
        filename = key + '.txt'
        content = b'1' * 1024 * 1024

        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"

        content = random_bytes(1024 * 1024)

        with open(filename, 'wb') as f:
            f.write(content)

        total_size = os.path.getsize(filename)
        # Set part size
        part_size = determine_part_size(total_size, preferred_size=(100*1024))

        # Init multipart without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.init_multipart_upload, key)

        # Init multipart with payer setting, should be successful.
        upload_id = self.payer_bucket.init_multipart_upload(key, headers=headers).upload_id
        parts = []

        # Upload part without payer setting, should be failed.
        with open(filename, 'rb') as fileobj:
            part_number = 1
            num_to_upload = part_size
            self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.upload_part, key, upload_id, part_number,
                                            SizedFileAdapter(fileobj, num_to_upload))

        # Upload part with payer setting, should be successful.
        with open(filename, 'rb') as fileobj:
            part_number = 1
            offset = 0
            while offset < total_size:
                num_to_upload = min(part_size, total_size - offset)
                result = self.payer_bucket.upload_part(key, upload_id, part_number,
                                            SizedFileAdapter(fileobj, num_to_upload), headers=headers)
                parts.append(PartInfo(part_number, result.etag))

                offset += num_to_upload
                part_number += 1

        # Complete multipart upload without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.complete_multipart_upload, key, upload_id, parts)

        # Complete multipart upload with payer setting, should be successful.
        result = self.payer_bucket.complete_multipart_upload(key, upload_id, parts, headers=headers)
        self.assertEqual(result.status, 200)

        self.bucket.delete_object(key)
        os.remove(filename)

    def test_upload_part_copy(self):
        src_object_name = 'requestpayment-test-upload-part-copy-src'
        dest_object_name = 'requestpayment-test-upload-part-copy-dest'
        content = b'a' * 1024 * 1024

        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"

        self.bucket.put_object(src_object_name, content)        

        # Get src object size
        head_info = self.bucket.head_object(src_object_name)
        total_size = head_info.content_length
        self.assertEqual(total_size, 1024 * 1024)

        # Set part size
        part_size = determine_part_size(total_size, preferred_size=(100*1024))

        upload_id = self.payer_bucket.init_multipart_upload(dest_object_name, headers=headers).upload_id
        parts = []

        # Upload part copy without payer setting, should be failed.
        part_number = 1
        offset = 0
        num_to_upload = min(part_size, total_size - offset)
        end = offset + num_to_upload - 1;
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.upload_part_copy, self.payer_bucket.bucket_name, 
                            src_object_name, (offset, end), dest_object_name, upload_id, part_number)

        # Upload part copy with payer setting, should be successful.
        part_number = 1
        offset = 0
        while offset < total_size:
            num_to_upload = min(part_size, total_size - offset)
            end = offset + num_to_upload - 1;
            result = self.payer_bucket.upload_part_copy(self.payer_bucket.bucket_name, src_object_name, (offset, end), 
                                dest_object_name, upload_id, part_number, headers=headers)

            parts.append(PartInfo(part_number, result.etag))

            offset += num_to_upload
            part_number += 1

        # Complete multipart upload with payer setting, should be successful.
        result = self.payer_bucket.complete_multipart_upload(dest_object_name, upload_id, parts, headers=headers)

        self.bucket.delete_object(src_object_name)
        self.bucket.delete_object(dest_object_name)

    def test_resumable_upload(self):
        small_object = 'requestpayment-test-resumable-upload-small-object'
        big_object = 'requestpayment-test-resumable-upload-big-object'

        # Create tmp file smaller than multipart_threshold
        file_name = self._prepare_temp_file_with_size(150 * 1024)

        # Resumale upload small object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, oss2.resumable_upload, self.payer_bucket, small_object, file_name, 
                        multipart_threshold=(200*1024), num_threads=2, part_size=(100*1024))

        # Resumale upload small object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = oss2.resumable_upload(self.payer_bucket, small_object, file_name, 
                        multipart_threshold=(200*1024), num_threads=2, part_size=(100*1024), headers=headers)
        self.assertEqual(result.status, 200)
        self.bucket.delete_object(small_object)

        # Start big file test
        # Create big file bigger than multipart_threshold
        file_name = self._prepare_temp_file_with_size(11 *1024 * 1024)

        # Resumale upload big object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, oss2.resumable_upload, self.payer_bucket, big_object, file_name, 
                        multipart_threshold=(200*1024), num_threads=2, part_size=(100*1024))

        # Resumale upload big object with payer setting and tagging setting, should be successful.
        key1 = 'key1'
        value1 = 'value2'

        key2 = 'key2'
        value2 = 'value2'

        tag_str = key1 + '=' + value1
        tag_str += '&' + key2 + '=' + value2

        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        headers[OSS_OBJECT_TAGGING] = tag_str
        result = oss2.resumable_upload(self.payer_bucket, big_object, file_name, 
                    multipart_threshold=(200*1024), num_threads=2, part_size=(100*1024), headers=headers)
        self.assertEqual(result.status, 200)

        # Check object size
        head_info = self.bucket.head_object(big_object)
        total_size = head_info.content_length
        self.assertEqual(total_size, (11 * 1024 * 1024))

        # Check tagging
        result = self.bucket.get_object_tagging(big_object)
        self.assertEqual(2, result.tag_set.len())
        tagging_rule = result.tag_set.tagging_rule
        self.assertEqual(value1, tagging_rule[key1])
        self.assertEqual(value2, tagging_rule[key2])

        self.bucket.delete_object(big_object)

    def test_resumable_down(self):
        small_object = 'requestpayment-test-resumable-down-small-object'
        content1 = b'a' * (150 * 1024)
        big_object = 'requestpayment-test-resumable-down-big-object'
        content2 = b'a' * (500 * 1024)
        file_name = small_object + '.txt'

        self.bucket.put_object(small_object, content1)
        self.bucket.put_object(big_object, content2)

        # Resumale down small object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.ServerError, oss2.resumable_download, self.payer_bucket, small_object, file_name, 
                    multiget_threshold=(200*1024), num_threads=2, part_size=(1024*1024))

        # Resumale down small object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        oss2.resumable_download(self.payer_bucket, small_object, file_name, 
                    multiget_threshold=(200*1024), num_threads=2, part_size=(1024*1024), headers=headers)

        # Check file size
        file_size = os.stat(file_name).st_size
        self.assertEqual(file_size, (150*1024))

        os.remove(file_name)
        self.bucket.delete_object(small_object)

        file_name = big_object + '.txt'

        # Resumale down big object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.ServerError, oss2.resumable_download, self.payer_bucket, big_object, file_name, 
                    multiget_threshold=(200*1024), num_threads=2, part_size=(1024*1024))

        # Resumale down big object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        oss2.resumable_download(self.payer_bucket, big_object, file_name, 
                    multiget_threshold=(200*1024), num_threads=2, part_size=(1024*1024), headers=headers)

        # Check file size
        file_size = os.stat(file_name).st_size
        self.assertEqual(file_size, (500*1024))

        os.remove(file_name)
        self.bucket.delete_object(big_object)

    def test_resumable_down1(self):
        key = 'requestpayment-test-resumable-down-object'
        content = b'a' * (2 * 1024 * 1024)
        file_name = key + '.txt'

        self.bucket.put_object(key, content)

        # Resumale down object smaller than multiget_threshold without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.ServerError, oss2.resumable_download, self.payer_bucket, key, file_name, 
                    multiget_threshold=(3*1024*1024), num_threads=2, part_size=(100*1024))

        # Resumale down object smaller than multiget_threshold with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        oss2.resumable_download(self.payer_bucket, key, file_name, 
                    multiget_threshold=(3*1024*1024), num_threads=2, part_size=(100*1024), headers=headers)

        # Check file size
        file_size = os.stat(file_name).st_size
        self.assertEqual(file_size, (2*1024*1024))

        os.remove(file_name)

        # Resumale down object bigger than multiget_threshold without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.ServerError, oss2.resumable_download, self.payer_bucket, key, file_name, 
                    multiget_threshold=(500*1024), num_threads=2, part_size=(100*1024))

        # Resumale down object bigger than multiget_threshold with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        oss2.resumable_download(self.payer_bucket, key, file_name, 
                    multiget_threshold=(500*1024), num_threads=2, part_size=(100*1024), headers=headers)

        # Check file size
        file_size = os.stat(file_name).st_size
        self.assertEqual(file_size, (2*1024*1024))

        os.remove(file_name)
        self.bucket.delete_object(key)

    def test_head_object(self):
        key = 'requestpayment-test-head-object'
        content = '123'

        self.bucket.put_object(key, content)

        # Head object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.ServerError, self.payer_bucket.head_object, key)

        # Head object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.head_object(key, headers=headers)
        self.assertEqual(result.status, 200)

        self.bucket.delete_object(key)

    def test_get_object_meta(self):
        key = 'requestpayment-test-get-object-meta'
        content = '123'

        self.bucket.put_object(key, content)

        # Get object meta without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.get_object_meta, key)

        # Get object meta with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.get_object_meta(key, headers=headers)
        self.assertEqual(result.status, 200)

        self.bucket.delete_object(key)

    def test_dose_exists_object(self):
        key = 'requestpayment-test-dose-exist-object'
        content = 'test-content'

        self.bucket.put_object(key, content)

        # Test dose exist object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.object_exists, key)

        # Test dose exist object with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        is_exist = self.payer_bucket.object_exists(key, headers=headers)
        self.assertEqual(is_exist, True)

        self.bucket.delete_object(key)

    def test_update_object_meta(self):
        key = 'requestpayment-test-update-object-meta'
        content = 'test-content'

        self.bucket.put_object(key, content)

        headers = dict()
        headers['Content-Type'] = 'whatever'
        # Test dose exist object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.update_object_meta, key, headers=headers)

        # Test dose exist object with payer setting, should be successful.
        headers[OSS_REQUEST_PAYER] = 'requester'
        self.payer_bucket.update_object_meta(key, headers=headers)

        self.bucket.delete_object(key)

    def test_restore_object(self):
        key = 'requestpayment-test-restore-object'
        content = 'test-content'
        headers = dict()
        headers['x-oss-storage-class'] = oss2.BUCKET_STORAGE_CLASS_ARCHIVE

        # Check object's storage class
        self.bucket.put_object(key, content, headers)
        meta = self.bucket.head_object(key)
        self.assertEqual(meta.resp.headers['x-oss-storage-class'], oss2.BUCKET_STORAGE_CLASS_ARCHIVE)

        # Restore object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.restore_object, key)

        # Check object's storage class
        self.bucket.put_object(key, content, headers)
        meta = self.bucket.head_object(key)
        self.assertEqual(meta.resp.headers['x-oss-storage-class'], oss2.BUCKET_STORAGE_CLASS_ARCHIVE)

        # Restore object with payer setting, should be successful.
        headers=dict()
        headers[OSS_REQUEST_PAYER] = 'requester'
        self.payer_bucket.restore_object(key, headers=headers)

        self.bucket.delete_object(key)

    def test_abort_multipart_upload(self):
        key = 'requestpayment-abort-multipart-upload'
        
        upload_id = self.bucket.init_multipart_upload(key).upload_id

        # Abort multipart without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.abort_multipart_upload, key, upload_id)

        # Abort multipartwith payer setting, should be successful.
        headers=dict()
        headers[OSS_REQUEST_PAYER] = 'requester'
        result = self.payer_bucket.abort_multipart_upload(key, upload_id, headers=headers)
        self.assertEqual(result.status, 204)

    def test_process_object(self):
        key = "test-process-object.jpg"
        result = self.bucket.put_object_from_file(key, "tests/example.jpg")
        self.assertEqual(result.status, 200)
        dest_key = "test-process-object-dest.jpg"
        
        process = "image/resize,w_100|sys/saveas,o_{0},b_{1}".format(
            oss2.compat.to_string(base64.urlsafe_b64encode(oss2.compat.to_bytes(dest_key))),
            oss2.compat.to_string(base64.urlsafe_b64encode(oss2.compat.to_bytes(self.bucket.bucket_name))))

        # Process object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.process_object, key, process)

        # Process object with payer setting, should be successful.
        headers=dict()
        headers[OSS_REQUEST_PAYER] = 'requester'
        result = self.payer_bucket.process_object(key, process, headers=headers)
        self.assertEqual(result.status, 200)

        result = self.bucket.object_exists(dest_key)
        self.assertEqual(result, True)

        self.bucket.delete_object(key)
        self.bucket.delete_object(dest_key)

    def test_object_tagging(self):
        key = 'requestpayment-test-put-get-delete-object-tagging'
        content = 'test-content'

        self.bucket.put_object(key, content)

        rule = TaggingRule()
        rule.add('key1', 'value1')
        rule.add('key2', 'value2')
        tagging = Tagging(rule)

        # Put object tagging without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.put_object_tagging, key, tagging)

        # Put object tagging with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.put_object_tagging(key, tagging, headers=headers)
        self.assertEqual(result.status, 200)

        # Get object tagging without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.get_object_tagging, key)

        # Get object tagging with payer setting, should be successful.

        result = self.payer_bucket.get_object_tagging(key, headers=headers)
        self.assertEqual(len(result.tag_set.tagging_rule), 2)

        # Delete object tagging without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.delete_object_tagging, key)

        # Delete object tagging with payer setting, should be successful.
        result = self.payer_bucket.delete_object_tagging(key, headers=headers)
        self.assertEqual(result.status, 204)

        self.bucket.delete_object(key)

    def test_list_objects(self):
        # List object without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.list_objects)

        # List objects with payer setting, should be successful.
        headers=dict()
        headers[OSS_REQUEST_PAYER] = 'requester'
        result = self.payer_bucket.list_objects(headers=headers)
        self.assertEqual(result.status, 200)

    def test_list_parts(self):
        key = 'requestpayment-list-parts'

        upload_id = self.bucket.init_multipart_upload(key).upload_id

        # Abort multipart without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.list_parts, key, upload_id)

        # Abort multipartwith payer setting, should be successful.
        headers=dict()
        headers[OSS_REQUEST_PAYER] = 'requester'
        result = self.payer_bucket.list_parts(key, upload_id, headers=headers)
        self.assertEqual(result.status, 200)

    def test_list_mulitpart_uploads(self):
        # List multipart uploads without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.list_multipart_uploads)

        # List multipart uploads with payer setting, should be successful.
        headers=dict()
        headers[OSS_REQUEST_PAYER] = 'requester'
        result = self.payer_bucket.list_multipart_uploads(headers=headers)
        self.assertEqual(result.status, 200)

    def test_object_iterator(self):
        # ObjectIterator without payer setting, should be failed.
        access_err_flag = False
        try:
            obj_iter = oss2.ObjectIterator(self.payer_bucket)
            for obj in obj_iter:
                pass
        except oss2.exceptions.AccessDenied:
            access_err_flag = True

        self.assertEqual(access_err_flag, True)

        # ObjectIterator with payer setting, should be failed.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        obj_iter = oss2.ObjectIterator(self.payer_bucket, headers=headers)
        for obj in obj_iter:
            pass

    def test_multipart_iterator(self):
        # MultipartUploadIterator without payer setting, should be failed.
        access_err_flag = False
        try:
            up_iter = oss2.MultipartUploadIterator(self.payer_bucket)
            for up in up_iter:
                pass
        except oss2.exceptions.AccessDenied:
            access_err_flag = True

        self.assertEqual(access_err_flag, True)

        # MultipartUploadIterator with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        up_iter = oss2.MultipartUploadIterator(self.payer_bucket, headers=headers)
        for up in up_iter:
            pass

    def test_object_upload_iterator(self):
        key = 'requestpayment-test-object-upload-iterator'
        content = 'test-content'
        self.bucket.put_object(key, content)

        # ObjectUploadIterator without payer setting, should be failed.
        access_err_flag = False
        try:
            up_iter = oss2.ObjectUploadIterator(self.payer_bucket, key)
            for up in up_iter:
                pass
        except oss2.exceptions.AccessDenied:
            access_err_flag = True

        self.assertEqual(access_err_flag, True)

        # ObjectUploadIterator with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        up_iter = oss2.ObjectUploadIterator(self.payer_bucket, key, headers=headers)
        for up in up_iter:
            pass

        self.bucket.delete_object(key)

    def test_part_iterator(self):
        key = 'requestpayment-test-object-upload-iterator'
        upload_id = self.bucket.init_multipart_upload(key).upload_id

        # PartIterator without payer setting, should be failed.
        access_err_flag = False
        try:
            up_iter = oss2.PartIterator(self.payer_bucket, key, upload_id)
            for up in up_iter:
                pass
        except oss2.exceptions.AccessDenied:
            access_err_flag = True

        self.assertEqual(access_err_flag, True)

        # PartIterator with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        up_iter = oss2.PartIterator(self.payer_bucket, key, upload_id, headers=headers)
        for up in up_iter:
            pass
    

if __name__ == '__main__':
    unittest.main()