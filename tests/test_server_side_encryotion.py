# -*- coding: utf-8 -*-

from .common import *
from oss2.models import ServerSideEncryptionRule, PartInfo
from oss2 import (SERVER_SIDE_ENCRYPTION_KMS, SERVER_SIDE_ENCRYPTION_AES256,
                  SERVER_SIDE_ENCRYPTION_SM4, KMS_DATA_ENCRYPTION_SM4)
from oss2.headers import (OSS_SERVER_SIDE_ENCRYPTION, OSS_SERVER_SIDE_ENCRYPTION_KEY_ID,
                          OSS_SERVER_SIDE_DATA_ENCRYPTION)
from oss2 import determine_part_size, SizedFileAdapter


class TestSSEDataEncryption(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)
        self.endpoint = OSS_ENDPOINT

    def test_put_bucket_encryption(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-put-bucket-encryption"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        # set SM4
        rule = ServerSideEncryptionRule()
        rule.sse_algorithm = oss2.SERVER_SIDE_ENCRYPTION_SM4
        bucket.put_bucket_encryption(rule)

        result = bucket.get_bucket_encryption()
        self.assertEqual(SERVER_SIDE_ENCRYPTION_SM4, result.sse_algorithm)
        self.assertIsNone(result.kms_master_keyid)
        self.assertIsNone(result.kms_data_encryption)

        bucket_info = bucket.get_bucket_info()
        rule = bucket_info.bucket_encryption_rule
        self.assertEqual(SERVER_SIDE_ENCRYPTION_SM4, rule.sse_algorithm)
        self.assertIsNone(result.kms_master_keyid)
        self.assertIsNone(result.kms_data_encryption)

        # set KMS and data SM4, and none kms_key_id.
        rule = ServerSideEncryptionRule()
        rule.sse_algorithm = SERVER_SIDE_ENCRYPTION_KMS
        rule.kms_data_encryption = KMS_DATA_ENCRYPTION_SM4
        bucket.put_bucket_encryption(rule)

        result = bucket.get_bucket_encryption()
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, result.sse_algorithm)
        self.assertIsNone(result.kms_master_keyid)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, result.kms_data_encryption)

        bucket_info = bucket.get_bucket_info()
        rule = bucket_info.bucket_encryption_rule
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, rule.sse_algorithm)
        self.assertIsNone(rule.kms_master_keyid)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, rule.kms_data_encryption)

        # set KMS and SM4, and has kms key id
        rule = ServerSideEncryptionRule()
        rule.sse_algorithm = SERVER_SIDE_ENCRYPTION_KMS
        rule.kms_master_keyid = '123'
        rule.kms_data_encryption = KMS_DATA_ENCRYPTION_SM4
        bucket.put_bucket_encryption(rule)

        result = bucket.get_bucket_encryption()
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, result.sse_algorithm)
        self.assertEqual('123', result.kms_master_keyid)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, result.kms_data_encryption)

        bucket_info = bucket.get_bucket_info()
        rule = bucket_info.bucket_encryption_rule
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, rule.sse_algorithm)
        self.assertEqual('123', rule.kms_master_keyid)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, rule.kms_data_encryption)

        # set AES256 and data encryption is not none
        rule = ServerSideEncryptionRule()
        rule.sse_algorithm = SERVER_SIDE_ENCRYPTION_AES256
        rule.kms_data_encryption = KMS_DATA_ENCRYPTION_SM4
        bucket.put_bucket_encryption(rule)

        result = bucket.get_bucket_encryption()
        self.assertEqual(SERVER_SIDE_ENCRYPTION_AES256, result.sse_algorithm)
        self.assertIsNone(result.kms_master_keyid)
        self.assertIsNone(result.kms_data_encryption)

        bucket_info = bucket.get_bucket_info()
        rule = bucket_info.bucket_encryption_rule
        self.assertEqual(SERVER_SIDE_ENCRYPTION_AES256, rule.sse_algorithm)
        self.assertIsNone(rule.kms_master_keyid)
        self.assertIsNone(rule.kms_data_encryption)

        # set SM4 and data encryption is not none
        rule = ServerSideEncryptionRule()
        rule.sse_algorithm = SERVER_SIDE_ENCRYPTION_SM4
        rule.kms_data_encryption = KMS_DATA_ENCRYPTION_SM4
        bucket.put_bucket_encryption(rule)

        result = bucket.get_bucket_encryption()
        self.assertEqual(SERVER_SIDE_ENCRYPTION_SM4, result.sse_algorithm)
        self.assertIsNone(result.kms_master_keyid)
        self.assertIsNone(result.kms_data_encryption)

        bucket_info = bucket.get_bucket_info()
        rule = bucket_info.bucket_encryption_rule
        self.assertEqual(SERVER_SIDE_ENCRYPTION_SM4, rule.sse_algorithm)
        self.assertIsNone(result.kms_master_keyid)
        self.assertIsNone(result.kms_data_encryption)

    def inner_put_object_with_encryption(self, bucket, object_name, data, sse_algorithm, data_algorithm):
        headers = dict()
        if sse_algorithm:
            headers[OSS_SERVER_SIDE_ENCRYPTION] = sse_algorithm
        if data_algorithm:
            headers[OSS_SERVER_SIDE_DATA_ENCRYPTION] = data_algorithm

        result = bucket.put_object(object_name, data, headers=headers)

        ret_sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
        ret_data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
        ret_kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        return ret_sse_algo, ret_data_algo, ret_kms_key_id


    def test_put_object_with_encryption(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-put-object-data-encryption"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        object_name = 'test-put-object-none-encryption'
        data = b'a'
        sse_algo, data_algo, key_id = self.inner_put_object_with_encryption(bucket, object_name, data, None, None)
        self.assertIsNone(sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNone(key_id)

        object_name = 'test-put-object-kms'
        sse_algo, data_algo, key_id = self.inner_put_object_with_encryption(bucket, object_name, data, SERVER_SIDE_ENCRYPTION_KMS, None)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNotNone(key_id)

        object_name = 'test-put-object-aes'
        sse_algo, data_algo, key_id = self.inner_put_object_with_encryption(bucket, object_name, data, SERVER_SIDE_ENCRYPTION_AES256, None)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_AES256, sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNone(key_id)

        object_name = 'test-put-object-sm4'
        sse_algo, data_algo, key_id = self.inner_put_object_with_encryption(bucket, object_name, data, SERVER_SIDE_ENCRYPTION_SM4, None)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_SM4, sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNone(key_id)

        object_name = 'test-put-object-kms-sm4'
        sse_algo, data_algo, key_id = self.inner_put_object_with_encryption(bucket, object_name, data, SERVER_SIDE_ENCRYPTION_KMS, KMS_DATA_ENCRYPTION_SM4)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, sse_algo)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, data_algo)
        self.assertIsNotNone(key_id)

        object_name = 'test-put-object-aes256-sm4'
        sse_algo, data_algo, key_id = self.inner_put_object_with_encryption(bucket, object_name, data, SERVER_SIDE_ENCRYPTION_AES256, KMS_DATA_ENCRYPTION_SM4)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_AES256, sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNone(key_id)

        object_name = 'test-put-object-sm4-sm4'
        sse_algo, data_algo, key_id = self.inner_put_object_with_encryption(bucket, object_name, data, SERVER_SIDE_ENCRYPTION_SM4, KMS_DATA_ENCRYPTION_SM4)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_SM4, sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNone(key_id)

        object_name = 'test-put-object-none-sm4'
        sse_algo, data_algo, key_id = self.inner_put_object_with_encryption(bucket, object_name, data, None, KMS_DATA_ENCRYPTION_SM4)
        self.assertIsNone(sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNone(key_id)

    def inner_append_object_with_encryption(self, bucket, object_name, position, data, sse_algorithm, data_algorithm):
        headers = dict()
        if sse_algorithm:
            headers[OSS_SERVER_SIDE_ENCRYPTION] = sse_algorithm
        if data_algorithm:
            headers[OSS_SERVER_SIDE_DATA_ENCRYPTION] = data_algorithm

        result = bucket.append_object(object_name, position, data, headers=headers)
        ret_sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
        ret_data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
        ret_kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        return ret_sse_algo, ret_data_algo, ret_kms_key_id

    def test_append_object_with_encryption(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-append-object-data-encryption"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        # first append
        object_name = 'test-append'
        sse_algo, data_algo, key_id = self.inner_append_object_with_encryption(bucket, object_name, 0, '123', SERVER_SIDE_ENCRYPTION_KMS, None)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNotNone(key_id)
        kms_key_id = key_id

        # second append with none algorithm
        sse_algo, data_algo, key_id = self.inner_append_object_with_encryption(bucket, object_name, 3, '456', None, None)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNotNone(key_id)
        self.assertEqual(kms_key_id, key_id)

        # third append with other algorithm
        sse_algo, data_algo, key_id = self.inner_append_object_with_encryption(bucket, object_name, 6, '789', SERVER_SIDE_ENCRYPTION_AES256, None)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNotNone(key_id)
        self.assertEqual(kms_key_id, key_id)

    def test_multipart_upload(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-multipart-upload-data-encryption"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        key = 'data-encryption-test-upload-part-object'
        filename = self._prepare_temp_file_with_size(1024 * 1024)

        headers = dict()
        headers[OSS_SERVER_SIDE_ENCRYPTION] = SERVER_SIDE_ENCRYPTION_KMS
        headers[OSS_SERVER_SIDE_DATA_ENCRYPTION] = KMS_DATA_ENCRYPTION_SM4

        total_size = os.path.getsize(filename)
        # Set part size
        part_size = determine_part_size(total_size, preferred_size=(100*1024))

        # Init multipart with encryption headers.
        result = bucket.init_multipart_upload(key, headers=headers)
        ret_sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
        ret_data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
        ret_kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, ret_sse_algo)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, ret_data_algo)
        self.assertIsNotNone(ret_kms_key_id)

        kms_key_id = ret_kms_key_id
        upload_id = result.upload_id
        parts = []

        # Upload part with the encyrption headers will be failed.
        headers = dict()
        headers[OSS_SERVER_SIDE_ENCRYPTION] = SERVER_SIDE_ENCRYPTION_KMS
        headers[OSS_SERVER_SIDE_DATA_ENCRYPTION] = KMS_DATA_ENCRYPTION_SM4
        with open(filename, 'rb') as fileobj:
            part_number = 1
            num_to_upload = part_size
            self.assertRaises(oss2.exceptions.InvalidArgument, bucket.upload_part, key, upload_id, part_number,
                                            SizedFileAdapter(fileobj, num_to_upload), headers=headers)

        # Upload part with none encryption headers.
        with open(filename, 'rb') as fileobj:
            part_number = 1
            offset = 0
            while offset < total_size:
                num_to_upload = min(part_size, total_size - offset)

                result = bucket.upload_part(key, upload_id, part_number,
                                            SizedFileAdapter(fileobj, num_to_upload))

                parts.append(PartInfo(part_number, result.etag))

                offset += num_to_upload
                part_number += 1

                ret_sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
                ret_data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
                ret_kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
                self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, ret_sse_algo)
                self.assertEqual(KMS_DATA_ENCRYPTION_SM4, ret_data_algo)
                self.assertEqual(kms_key_id, ret_kms_key_id)

        # Complete multipart upload with encryption headers.
        self.assertRaises(oss2.exceptions.InvalidArgument, bucket.complete_multipart_upload, key, upload_id, parts, headers=headers)

        # Complete multipart upload with none encryption headers.
        result = bucket.complete_multipart_upload(key, upload_id, parts)
        self.assertEqual(result.status, 200)
        ret_sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
        ret_data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
        ret_kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, ret_sse_algo)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, ret_data_algo)
        self.assertEqual(kms_key_id, ret_kms_key_id)

        bucket.delete_object(key)


    def test_resumable_uoload(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-resumable-upload-data-encryption"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        small_object = 'requestpayment-test-resumable-upload-small-object'
        big_object = 'requestpayment-test-resumable-upload-big-object'

        # Create tmp file smaller than multipart_threshold
        file_name = self._prepare_temp_file_with_size(150 * 1024)

        # Resumale upload small object
        headers = dict()
        headers[OSS_SERVER_SIDE_ENCRYPTION] = SERVER_SIDE_ENCRYPTION_KMS
        headers[OSS_SERVER_SIDE_DATA_ENCRYPTION] = KMS_DATA_ENCRYPTION_SM4
        result = oss2.resumable_upload(bucket, small_object, file_name,
                                       multipart_threshold=(200 * 1024), num_threads=2, part_size=(100 * 1024),
                                       headers=headers)
        ret_sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
        ret_data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
        ret_kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, ret_sse_algo)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, ret_data_algo)
        self.assertIsNotNone(ret_kms_key_id)
        self.assertEqual(result.status, 200)
        bucket.delete_object(small_object)

        # Start big file test
        # Create big file bigger than multipart_threshold
        file_name = self._prepare_temp_file_with_size(11 * 1024 * 1024)

        headers = dict()
        headers[OSS_SERVER_SIDE_ENCRYPTION] = SERVER_SIDE_ENCRYPTION_KMS
        headers[OSS_SERVER_SIDE_DATA_ENCRYPTION] = KMS_DATA_ENCRYPTION_SM4
        result = oss2.resumable_upload(bucket, big_object, file_name,
                                       multipart_threshold=(200 * 1024), num_threads=2, part_size=(100 * 1024),
                                       headers=headers)

        self.assertEqual(result.status, 200)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, ret_sse_algo)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, ret_data_algo)
        self.assertIsNotNone(ret_kms_key_id)
        self.assertEqual(result.status, 200)
        bucket.delete_object(big_object)

    def test_copy_object(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-copy-object-data-encryption"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        object_name = 'test-copy-object-src'
        data = b'a' * 1024
        user_header_key = 'x-oss-meta-user1'
        user_header_value = 'user_value'

        headers = dict()
        headers[user_header_key] = user_header_value
        headers[OSS_SERVER_SIDE_ENCRYPTION] = SERVER_SIDE_ENCRYPTION_KMS
        headers[OSS_SERVER_SIDE_DATA_ENCRYPTION] = KMS_DATA_ENCRYPTION_SM4

        result = bucket.put_object(object_name, data, headers=headers)
        sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
        data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
        kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, sse_algo)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, data_algo)
        self.assertIsNotNone(kms_key_id)

        result = bucket.head_object(object_name)
        sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
        data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
        kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        ret_value = result.headers.get(user_header_key)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_KMS, sse_algo)
        self.assertEqual(KMS_DATA_ENCRYPTION_SM4, data_algo)
        self.assertIsNotNone(kms_key_id)
        self.assertEqual(user_header_value, ret_value)

        #  test normal copy objects
        dest_name = 'test-copy-object-dest'
        bucket.copy_object(bucket_name, object_name, dest_name)

        result = bucket.head_object(dest_name)
        ret_sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
        ret_data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
        ret_kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        self.assertIsNone(ret_sse_algo)
        self.assertIsNone(ret_data_algo)
        self.assertIsNone(ret_kms_key_id)

        # test copy object with specified encryption headers
        headers = dict()
        headers[user_header_key] = user_header_value
        headers[OSS_SERVER_SIDE_ENCRYPTION] = SERVER_SIDE_ENCRYPTION_AES256
        bucket.copy_object(bucket_name, object_name, dest_name, headers=headers)

        result = bucket.head_object(dest_name)
        sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
        data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
        kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
        self.assertEqual(SERVER_SIDE_ENCRYPTION_AES256, sse_algo)
        self.assertIsNone(data_algo)
        self.assertIsNone(kms_key_id)


if __name__ == '__main__':
    unittest.main()
