# -*- coding: utf-8 -*-

import unittest
import oss2
from oss2.utils import calc_obj_crc_from_parts

from common import *
from oss2.headers import OSS_OBJECT_TAGGING, OSS_OBJECT_TAGGING_COPY_DIRECTIVE
from oss2.compat import urlunquote, urlquote

from oss2.compat import is_py2, is_py33


class TestMultipart(OssTestCase):
    def do_multipart_internal(self, do_md5):
        key = self.random_key()
        content = random_bytes(128 * 1024)

        parts = []
        upload_id = self.bucket.init_multipart_upload(key).upload_id

        if do_md5:
            headers = {'Content-Md5': oss2.utils.content_md5(content)}
        else:
            headers = None

        result = self.bucket.upload_part(key, upload_id, 1, content, headers=headers)
        parts.append(oss2.models.PartInfo(1, result.etag, size=len(content), part_crc=result.crc))
        self.assertTrue(result.crc is not None)

        complete_result = self.bucket.complete_multipart_upload(key, upload_id, parts)

        object_crc = calc_obj_crc_from_parts(parts)
        self.assertTrue(complete_result.crc is not None)
        self.assertEqual(object_crc, result.crc)

        result = self.bucket.get_object(key)
        self.assertEqual(content, result.read())

    def test_multipart(self):
        self.do_multipart_internal(False)

    def test_upload_part_content_md5_good(self):
        self.do_multipart_internal(True)

    def test_upload_part_content_md5_bad(self):
        key = self.random_key()
        content = random_bytes(128 * 1024)

        parts = []
        upload_id = self.bucket.init_multipart_upload(key).upload_id

        # construct a bad Content-Md5 by using 'content + content's Content-Md5
        headers = {'Content-Md5': oss2.utils.content_md5(content + content)}

        self.assertRaises(oss2.exceptions.InvalidDigest, self.bucket.upload_part, key, upload_id, 1, content,
                          headers=headers)

    def test_progress(self):
        stats = {'previous': -1}

        def progress_callback(bytes_consumed, total_bytes):
            self.assertTrue(bytes_consumed <= total_bytes)
            self.assertTrue(bytes_consumed > stats['previous'])

            stats['previous'] = bytes_consumed

        key = self.random_key()
        content = random_bytes(128 * 1024)

        upload_id = self.bucket.init_multipart_upload(key).upload_id
        self.bucket.upload_part(key, upload_id, 1, content, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        self.bucket.abort_multipart_upload(key, upload_id)

    def test_upload_part_copy(self):
        src_object = self.random_key()
        dst_object = self.random_key()

        content = random_bytes(200 * 1024)

        # 上传源文件
        self.bucket.put_object(src_object, content)

        # part copy到目标文件
        parts = []
        upload_id = self.bucket.init_multipart_upload(dst_object).upload_id

        result = self.bucket.upload_part_copy(self.bucket.bucket_name, src_object,
                                              (0, 100 * 1024 - 1), dst_object, upload_id, 1)
        parts.append(oss2.models.PartInfo(1, result.etag))

        result = self.bucket.upload_part_copy(self.bucket.bucket_name, src_object,
                                              (100 * 1024, None), dst_object, upload_id, 2)
        parts.append(oss2.models.PartInfo(2, result.etag))

        self.bucket.complete_multipart_upload(dst_object, upload_id, parts)

        # 验证
        content_got = self.bucket.get_object(dst_object).read()
        self.assertEqual(len(content_got), len(content))
        self.assertEqual(content_got, content)

    def test_init_multipart_with_object_tagging_exceptions(self):
        key = self.random_key()

        headers = dict()
        # wrong key
        tag_str = '=a&b=a'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass

        # wrong key
        long_str = 129 * 'a'
        tag_str = long_str + '=b&b=a'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass

        # wrong value
        tag_str = 'a=&b=c'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
        except oss2.exceptions.OssError:
            self.assertFalse(True, 'should get a exception')

        # wrong value
        long_str = 257 * 'a'
        tag_str = 'a=' + long_str + '&b=a'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass

        # dup kv
        tag_str = 'a=b&a=b&a=b'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass

        # max+1 kv pairs
        tag_str = 'a1=b1&a2=b2&a3=b4&a4=b4&a5=b5&a6=b6&a7=b7&a8=b8&a9=b9&a10=b10&a11=b11&a12=b12'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass

    def test_multipart_with_object_tagging(self):

        key = self.random_key()
        content = random_bytes(128 * 1024)

        tag_str = ''

        tag_key1 = urlquote('+:/')
        tag_value1 = urlquote('.-')
        tag_str = tag_key1 + '=' + tag_value1

        tag_ke2 = urlquote(' + ')
        tag_value2 = urlquote(u'中文'.encode('UTF-8'))
        tag_str += '&' + tag_ke2 + '=' + tag_value2

        headers = dict()
        headers[OSS_OBJECT_TAGGING] = tag_str

        parts = []
        upload_id = self.bucket.init_multipart_upload(key, headers=headers).upload_id

        headers = {'Content-Md5': oss2.utils.content_md5(content)}

        result = self.bucket.upload_part(key, upload_id, 1, content, headers=headers)
        parts.append(oss2.models.PartInfo(1, result.etag, size=len(content), part_crc=result.crc))
        self.assertTrue(result.crc is not None)

        complete_result = self.bucket.complete_multipart_upload(key, upload_id, parts)

        object_crc = calc_obj_crc_from_parts(parts)
        self.assertTrue(complete_result.crc is not None)
        self.assertEqual(object_crc, result.crc)

        result = self.bucket.get_object(key)
        self.assertEqual(content, result.read())

        result = self.bucket.get_object_tagging(key)

        self.assertEqual(2, result.tag_set.len())
        self.assertEqual('.-', result.tag_set.tagging_rule['+:/'])
        self.assertEqual('中文', result.tag_set.tagging_rule[' + '])

        result = self.bucket.delete_object_tagging(key)

    def test_multipart_with_versionging(self):

        from oss2.models import BucketVersioningConfig
        from oss2.models import BatchDeleteObjectVersion
        from oss2.models import BatchDeleteObjectVersionList

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = random_string(63).lower()
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        config = BucketVersioningConfig()
        config.status = 'Enabled'

        result = bucket.put_bucket_versioning(config)

        wait_meta_sync()

        result = bucket.get_bucket_info()

        self.assertEqual(int(result.status) / 100, 2)
        self.assertEqual(result.bucket_encryption_rule.ssealgorithm, None)
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
        bucket_name = random_string(63).lower()
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        wait_meta_sync()

        config = BucketVersioningConfig()
        config.status = 'Enabled'

        result = bucket.put_bucket_versioning(config)

        wait_meta_sync()

        result = bucket.get_bucket_info()

        self.assertEqual(int(result.status) / 100, 2)
        self.assertEqual(result.bucket_encryption_rule.ssealgorithm, None)
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
                                         (100 * 1024, None), dst_object, upload_id, 2, params={'versionId': versionid1})

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

    def test_crypto_multipart_upload(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = self.random_key()
            content_1 = random_bytes(200 * 1024)
            content_2 = random_bytes(200 * 1024)
            content_3 = random_bytes(100 * 1024)
            content = [content_1, content_2, content_3]
            do_md5 = random.choice((True, False))

            parts = []
            data_size = 1024 * 500
            part_size = 1024 * 200

            init_result = crypto_bucket.init_multipart_upload(key, data_size, part_size)
            self.assertTrue(init_result.status == 200)
            upload_id = init_result.upload_id

            for i in range(3):
                if do_md5:
                    headers = {'Content-Md5': oss2.utils.content_md5(content[i])}
                else:
                    headers = None
                upload_result = crypto_bucket.upload_part(key, upload_id, i + 1, content[i], headers=headers)
                parts.append(
                    oss2.models.PartInfo(i + 1, upload_result.etag, part_crc=upload_result.crc))
                self.assertTrue(upload_result.status == 200)
                self.assertTrue(upload_result.crc is not None)

            complete_result = crypto_bucket.complete_multipart_upload(key, upload_id, parts)
            self.assertTrue(complete_result.status == 200)

            get_result_range_1 = crypto_bucket.get_object(key, byte_range=(0, 204799))
            self.assertTrue(get_result_range_1.status == 206)
            content_got_1 = get_result_range_1.read()
            self.assertEqual(content_1, content_got_1)

            get_result_range_2 = crypto_bucket.get_object(key, byte_range=(204800, 409599))
            self.assertTrue(get_result_range_2.status == 206)
            content_got_2 = get_result_range_2.read()
            self.assertEqual(content_2, content_got_2)

            get_result_range_3 = crypto_bucket.get_object(key, byte_range=(409600, 511999))
            self.assertTrue(get_result_range_3.status == 206)
            content_got_3 = get_result_range_3.read()
            self.assertEqual(content_3, content_got_3)

            get_result = crypto_bucket.get_object(key)
            self.assertTrue(get_result.status == 200)
            content_got = get_result.read()
            self.assertEqual(content_1, content_got[0:204800])
            self.assertEqual(content_2, content_got[204800:409600])
            self.assertEqual(content_3, content_got[409600:512000])

    def test_crypto_abort_multipart(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = self.random_key()
            content = random_bytes(100 * 1024)

            data_size = 1024 * 100
            part_size = 1024 * 100

            init_result = crypto_bucket.init_multipart_upload(key, data_size, part_size)
            self.assertTrue(init_result.status == 200)
            upload_id = init_result.upload_id

            upload_result = crypto_bucket.upload_part(key, upload_id, 1, content)
            self.assertTrue(upload_result.status == 200)
            self.assertTrue(upload_result.crc is not None)

            abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
            self.assertTrue(abort_result.status == 204)

    def test_crypto_list_parts(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = self.random_key()
            content = random_bytes(100 * 1024)

            data_size = 1024 * 300
            part_size = 1024 * 100

            init_result = crypto_bucket.init_multipart_upload(key, data_size, part_size)
            self.assertTrue(init_result.status == 200)
            upload_id = init_result.upload_id

            upload_result = crypto_bucket.upload_part(key, upload_id, 1, content)
            self.assertTrue(upload_result.status == 200)
            self.assertTrue(upload_result.crc is not None)

            list_result = crypto_bucket.list_parts(key, upload_id)
            self.assertTrue(list_result.status == 200)

            self.assertEqual(data_size, list_result.client_encryption_data_size)
            self.assertEqual(part_size, list_result.client_encryption_part_size)

            abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
            self.assertTrue(abort_result.status == 204)

    def test_crypto_init_multipart_invalid_part_size(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = self.random_key()

            data_size = 1024 * 100
            part_size = random.randint(1, 15) + 1024 * 100

            # not align to block_size
            self.assertRaises(oss2.exceptions.ClientError, crypto_bucket.init_multipart_upload, key, data_size,
                              part_size=part_size)

            # part size is small than 100*1024
            part_size = random.randint(1, 1024 * 100 - 1)
            self.assertRaises(oss2.exceptions.ClientError, crypto_bucket.init_multipart_upload, key, data_size,
                              part_size=part_size)

    # 测试不指定part_size的情况，由接口指定part_size
    def test_crypto_init_multipart_with_out_part_size(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = self.random_key()
            data_size = 1024 * 100

            # init multipart without part_size
            init_result = crypto_bucket.init_multipart_upload(key, data_size)
            self.assertTrue(init_result.status == 200)
            upload_id = init_result.upload_id
            abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
            self.assertTrue(abort_result.status == 204)

    def test_crypto_upload_invalid_part_content(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = self.random_key()
            content_invalid = random_bytes(random.randint(1, 100 * 1024 - 1))

            data_size = 1024 * 250
            part_size = 1024 * 100

            init_result = crypto_bucket.init_multipart_upload(key, data_size, part_size)
            self.assertTrue(init_result.status == 200)
            upload_id = init_result.upload_id

            # invalid part size
            self.assertRaises(oss2.exceptions.InvalidEncryptionRequest, crypto_bucket.upload_part, key, upload_id, 1,
                              content_invalid)

            abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
            self.assertTrue(abort_result.status == 204)

    def test_crypto_upload_invalid_last_part_content(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = self.random_key()
            content_1 = random_bytes(100 * 1024)
            content_2 = random_bytes(100 * 1024)
            content_3 = random_bytes(50 * 1024)
            content = [content_1, content_2, content_3]
            content_invalid = content_3[0:random.randint(1, 50 * 1024 - 1)]

            parts = []
            data_size = 1024 * 250
            part_size = 1024 * 100

            init_result = crypto_bucket.init_multipart_upload(key, data_size, part_size)
            self.assertTrue(init_result.status == 200)
            upload_id = init_result.upload_id

            for i in range(2):
                upload_result = crypto_bucket.upload_part(key, upload_id, i + 1, content[i])
                parts.append(
                    oss2.models.PartInfo(i + 1, upload_result.etag, part_crc=upload_result.crc))
                self.assertTrue(upload_result.status == 200)
                self.assertTrue(upload_result.crc is not None)

            self.assertRaises(oss2.exceptions.InvalidEncryptionRequest, crypto_bucket.upload_part, key, upload_id, 3,
                              content_invalid)

            abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
            self.assertTrue(abort_result.status == 204)

    def test_crypto_upload_invalid_part_number(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = self.random_key()
            content_1 = random_bytes(100 * 1024)

            data_size = 1024 * 250
            part_size = 1024 * 100
            invalid_part_num = random.randint(4, 100)

            init_result = crypto_bucket.init_multipart_upload(key, data_size, part_size)
            self.assertTrue(init_result.status == 200)
            upload_id = init_result.upload_id

            self.assertRaises(oss2.exceptions.InvalidEncryptionRequest, crypto_bucket.upload_part, key, upload_id,
                              invalid_part_num, content_1)

            abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
            self.assertTrue(abort_result.status == 204)

    def test_crypto_complete_multipart_miss_parts(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = self.random_key()
            content_1 = random_bytes(100 * 1024)
            content_2 = random_bytes(100 * 1024)
            content_3 = random_bytes(50 * 1024)
            content = [content_1, content_2, content_3]

            parts = []
            data_size = 1024 * 250
            part_size = 1024 * 100

            init_result = crypto_bucket.init_multipart_upload(key, data_size, part_size)
            self.assertTrue(init_result.status == 200)
            upload_id = init_result.upload_id

            for i in range(2):
                upload_result = crypto_bucket.upload_part(key, upload_id, i + 1, content[i])
                parts.append(
                    oss2.models.PartInfo(i + 1, upload_result.etag, part_crc=upload_result.crc))
                self.assertTrue(upload_result.status == 200)
                self.assertTrue(upload_result.crc is not None)

            self.assertRaises(oss2.exceptions.InvalidEncryptionRequest, crypto_bucket.complete_multipart_upload,
                              key,
                              upload_id, parts)

            abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
            self.assertTrue(abort_result.status == 204)

    def test_upload_part_copy_from_crypto_source(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            src_object = self.random_key()
            dst_object = src_object + '-dest'

            content = random_bytes(300 * 1024)

            # 上传源文件
            crypto_bucket.put_object(src_object, content)

            # upload part copy到目标文件
            upload_id = self.bucket.init_multipart_upload(dst_object).upload_id
            self.assertRaises(oss2.exceptions.NotImplemented, self.bucket.upload_part_copy, self.bucket.bucket_name,
                              src_object, (0, 100 * 1024 - 1), dst_object, upload_id, 1)
            abort_result = self.bucket.abort_multipart_upload(dst_object, upload_id)
            self.assertTrue(abort_result.status == 204)

            data_size = len(content)
            part_size = 1024
            upload_id = crypto_bucket.init_multipart_upload(dst_object, part_size, data_size).upload_id
            self.assertRaises(oss2.exceptions.ClientError, crypto_bucket.upload_part_copy,
                              crypto_bucket.bucket_name,
                              src_object, (0, 100 * 1024 - 1), dst_object, upload_id, 1)

            abort_result = crypto_bucket.abort_multipart_upload(dst_object, upload_id)
            self.assertTrue(abort_result.status == 204)

    def test_crypto_multipart_concurrent(self):
        for crypto_bucket in [self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key1 = self.random_key()
            key1_content_1 = random_bytes(100 * 1024)
            key1_content_2 = random_bytes(100 * 1024)
            key1_content_3 = random_bytes(100 * 1024)
            key1_content = [key1_content_1, key1_content_2, key1_content_3]

            key1_parts = []
            key1_data_size = 1024 * 300
            key1_part_size = 1024 * 100

            key1_init_result = crypto_bucket.init_multipart_upload(key1, key1_data_size, key1_part_size)
            self.assertTrue(key1_init_result.status == 200)
            key1_upload_id = key1_init_result.upload_id

            key2 = self.random_key()
            key2_content_1 = random_bytes(200 * 1024)
            key2_content_2 = random_bytes(200 * 1024)
            key2_content_3 = random_bytes(100 * 1024)
            key2_content = [key2_content_1, key2_content_2, key2_content_3]

            key2_parts = []
            key2_data_size = 1024 * 500
            key2_part_size = 1024 * 200

            key2_init_result = crypto_bucket.init_multipart_upload(key2, key2_data_size, key2_part_size)
            self.assertTrue(key2_init_result.status == 200)
            key2_upload_id = key2_init_result.upload_id

            for i in range(3):
                key1_upload_result = crypto_bucket.upload_part(key1, key1_upload_id, i + 1, key1_content[i])
                key1_parts.append(oss2.models.PartInfo(i + 1, key1_upload_result.etag,
                                                       part_crc=key1_upload_result.crc))
                self.assertTrue(key1_upload_result.status == 200)
                self.assertTrue(key1_upload_result.crc is not None)

                key2_upload_result = crypto_bucket.upload_part(key2, key2_upload_id, i + 1, key2_content[i])
                key2_parts.append(oss2.models.PartInfo(i + 1, key2_upload_result.etag,
                                                       part_crc=key2_upload_result.crc))
                self.assertTrue(key2_upload_result.status == 200)
                self.assertTrue(key2_upload_result.crc is not None)

            key1_complete_result = crypto_bucket.complete_multipart_upload(key1, key1_upload_id, key1_parts)
            self.assertTrue(key1_complete_result.status == 200)

            key1_get_result = crypto_bucket.get_object(key1)
            self.assertTrue(key1_get_result.status == 200)
            key1_content_got = key1_get_result.read()
            self.assertEqual(key1_content_1, key1_content_got[0:102400])
            self.assertEqual(key1_content_2, key1_content_got[102400:204800])
            self.assertEqual(key1_content_3, key1_content_got[204800:307200])

            key2_complete_result = crypto_bucket.complete_multipart_upload(key2, key2_upload_id, key2_parts)
            self.assertTrue(key2_complete_result.status == 200)

            key2_get_result = crypto_bucket.get_object(key2)
            self.assertTrue(key2_get_result.status == 200)
            key2_content_got = key2_get_result.read()
            self.assertEqual(key2_content_1, key2_content_got[0:204800])
            self.assertEqual(key2_content_2, key2_content_got[204800:409600])
            self.assertEqual(key2_content_3, key2_content_got[409600:512000])


if __name__ == '__main__':
    unittest.main()
