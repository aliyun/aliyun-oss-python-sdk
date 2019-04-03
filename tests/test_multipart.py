# -*- coding: utf-8 -*-

import unittest
import oss2
from oss2.utils import calc_obj_crc_from_parts

from common import *

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

        self.assertRaises(oss2.exceptions.InvalidDigest, self.bucket.upload_part, key, upload_id, 1, content, headers=headers)

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
                                              (100*1024, None), dst_object, upload_id, 2)
        parts.append(oss2.models.PartInfo(2, result.etag))

        self.bucket.complete_multipart_upload(dst_object, upload_id, parts)

        # 验证
        content_got = self.bucket.get_object(dst_object).read()
        self.assertEqual(len(content_got), len(content))
        self.assertEqual(content_got, content)

    def do_crypto_multipart_internal(self, do_md5, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key = self.random_key()
        content_1 = random_bytes(100 * 1024)
        content_2 = random_bytes(100 * 1024)
        content_3 = random_bytes(100 * 1024)
        content = [content_1, content_2, content_3]

        parts = []
        data_size = 1024 * 300
        part_size = 1024 * 100

        init_result = bucket.init_multipart_upload(key, data_size, part_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        crypto_multipart_context = init_result.crypto_multipart_context

        self.assertEqual(crypto_multipart_context.data_size, 1024 * 300)
        self.assertEqual(crypto_multipart_context.part_size, 1024 * 100)

        for i in range(3):
            if do_md5:
                headers = {'Content-Md5': oss2.utils.content_md5(content[i])}
            else:
                headers = None
            upload_result = bucket.upload_part(key, upload_id, i+1, content[i], crypto_multipart_context, headers=headers)
            parts.append(oss2.models.PartInfo(i+1, upload_result.etag, size = part_size, part_crc = upload_result.crc))
            self.assertTrue(upload_result.status == 200)
            self.assertTrue(upload_result.crc is not None)

        complete_result = bucket.complete_multipart_upload(key, upload_id, parts)
        self.assertTrue(complete_result.status == 200)

        get_result_range_1 = bucket.get_object(key, byte_range=(0, 102399))
        self.assertTrue(get_result_range_1.status == 206)
        content_got_1 = get_result_range_1.read()
        self.assertEqual(content_1, content_got_1)

        get_result_range_2 = bucket.get_object(key, byte_range=(102400, 204799))
        self.assertTrue(get_result_range_2.status == 206)
        content_got_2 = get_result_range_2.read()
        self.assertEqual(content_2, content_got_2)

        get_result_range_3 = bucket.get_object(key, byte_range=(204800, 307199))
        self.assertTrue(get_result_range_3.status == 206)
        content_got_3 = get_result_range_3.read()
        self.assertEqual(content_3, content_got_3)

        get_result = bucket.get_object(key)
        self.assertTrue(get_result.status == 200)
        content_got = get_result.read()
        self.assertEqual(content_1, content_got[0:102400])
        self.assertEqual(content_2, content_got[102400:204800])
        self.assertEqual(content_3, content_got[204800:307200])

    def do_crypto_abort_multipart(self, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key = self.random_key()
        content = random_bytes(100 * 1024)

        data_size = 1024 * 100
        part_size = 1024 * 100

        init_result = bucket.init_multipart_upload(key, data_size, part_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        crypto_multipart_context = init_result.crypto_multipart_context

        upload_result = bucket.upload_part(key, upload_id, 1, content, crypto_multipart_context)
        self.assertTrue(upload_result.status == 200)
        self.assertTrue(upload_result.crc is not None)

        abort_result = bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)

    def do_crypto_list_parts(self, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key = self.random_key()
        content = random_bytes(100 * 1024)

        data_size = 1024 * 300
        part_size = 1024 * 100

        init_result = bucket.init_multipart_upload(key, data_size, part_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        crypto_multipart_context = init_result.crypto_multipart_context

        upload_result = bucket.upload_part(key, upload_id, 1, content, crypto_multipart_context)
        self.assertTrue(upload_result.status == 200)
        self.assertTrue(upload_result.crc is not None)

        list_result = bucket.list_parts(key, upload_id)
        self.assertTrue(list_result.status == 200)
        crypto_multipart_context_new = list_result.crypto_multipart_context

        self.assertEqual(crypto_multipart_context_new.crypto_key, crypto_multipart_context.crypto_key)
        self.assertEqual(crypto_multipart_context_new.crypto_start, crypto_multipart_context.crypto_start)
        self.assertEqual(crypto_multipart_context_new.data_size, crypto_multipart_context.data_size)
        self.assertEqual(crypto_multipart_context_new.part_size, crypto_multipart_context.part_size)

        abort_result = bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)

    def do_crypto_init_multipart_invalid_parameter(self, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key = self.random_key()
        content = random_bytes(100 * 1024)

        data_size = 1024 * 100
        part_size = 1

        #init multipart with invalid part_size
        self.assertRaises(oss2.exceptions.ClientError, bucket.init_multipart_upload, key, data_size, part_size=part_size)

        #init multipart without part_size
        init_result = bucket.init_multipart_upload(key, data_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        crypto_multipart_context = init_result.crypto_multipart_context
        part_size = crypto_multipart_context.part_size;
        self.assertEqual(part_size, 100*1024)

        abort_result = bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)

    def do_crypto_upload_invalid_part_content(self, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key = self.random_key()
        content_1 = random_bytes(100 * 1024)
        content_2 = random_bytes(100 * 1024)
        content_3 = random_bytes(50 * 1024)
        content = [content_1, content_2, content_3]
        content_invalid = random_bytes(100 * 1024 - 1)

        parts = []
        data_size = 1024 * 250
        part_size = 1024 * 100

        init_result = bucket.init_multipart_upload(key, data_size, part_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        crypto_multipart_context = init_result.crypto_multipart_context

        self.assertRaises(oss2.exceptions.InvalidArgument, bucket.upload_part, key, upload_id, 1, content_invalid, crypto_multipart_context)

        abort_result = bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)

    def do_crypto_upload_invalid_last_part_content(self, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key = self.random_key()
        content_1 = random_bytes(100 * 1024)
        content_2 = random_bytes(100 * 1024)
        content_3 = random_bytes(50 * 1024)
        content = [content_1, content_2, content_3]
        content_invalid = random_bytes(100 * 1024 - 1)

        parts = []
        data_size = 1024 * 250
        part_size = 1024 * 100

        init_result = bucket.init_multipart_upload(key, data_size, part_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        crypto_multipart_context = init_result.crypto_multipart_context

        for i in range(2):
            upload_result = bucket.upload_part(key, upload_id, i+1, content[i], crypto_multipart_context)
            parts.append(oss2.models.PartInfo(i+1, upload_result.etag, size = part_size, part_crc = upload_result.crc))
            self.assertTrue(upload_result.status == 200)
            self.assertTrue(upload_result.crc is not None)

        self.assertRaises(oss2.exceptions.InvalidArgument, bucket.upload_part, key, upload_id, 3, content_invalid, crypto_multipart_context)

        abort_result = bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)

    def do_crypto_upload_invalid_part_number(self, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key = self.random_key()
        content_1 = random_bytes(100 * 1024)
        content_2 = random_bytes(100 * 1024)
        content_3 = random_bytes(50 * 1024)
        content = [content_1, content_2, content_3]

        parts = []
        data_size = 1024 * 250
        part_size = 1024 * 100

        init_result = bucket.init_multipart_upload(key, data_size, part_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        crypto_multipart_context = init_result.crypto_multipart_context

        self.assertRaises(oss2.exceptions.InvalidArgument, bucket.upload_part, key, upload_id, 4, content_1, crypto_multipart_context)

        abort_result = bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)

    def do_crypto_complete_multipart_miss_parts(self, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key = self.random_key()
        content_1 = random_bytes(100 * 1024)
        content_2 = random_bytes(100 * 1024)
        content_3 = random_bytes(50 * 1024)
        content = [content_1, content_2, content_3]

        parts = []
        data_size = 1024 * 250
        part_size = 1024 * 100

        init_result = bucket.init_multipart_upload(key, data_size, part_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        crypto_multipart_context = init_result.crypto_multipart_context

        for i in range(2):
            upload_result = bucket.upload_part(key, upload_id, i+1, content[i], crypto_multipart_context)
            parts.append(oss2.models.PartInfo(i+1, upload_result.etag, size = part_size, part_crc = upload_result.crc))
            self.assertTrue(upload_result.status == 200)
            self.assertTrue(upload_result.crc is not None)

        self.assertRaises(oss2.exceptions.UnexpectedClientEncryptionPartsList, bucket.complete_multipart_upload, key, upload_id, parts)

        abort_result = bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)

    def do_crypto_resume_upload_after_loss_context(self, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key = self.random_key()
        content_1 = random_bytes(100 * 1024)
        content_2 = random_bytes(100 * 1024)
        content_3 = random_bytes(100 * 1024)
        content = [content_1, content_2, content_3]

        parts = []
        data_size = 1024 * 300
        part_size = 1024 * 100

        init_result = bucket.init_multipart_upload(key, data_size, part_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        crypto_multipart_context = init_result.crypto_multipart_context

        upload_result = bucket.upload_part(key, upload_id, 1, content[0], crypto_multipart_context)
        parts.append(oss2.models.PartInfo(1, upload_result.etag, size = part_size, part_crc = upload_result.crc))
        self.assertTrue(upload_result.status == 200)
        self.assertTrue(upload_result.crc is not None)

        list_result = bucket.list_parts(key, upload_id)
        self.assertTrue(list_result.status == 200)
        crypto_multipart_context_new_1 = list_result.crypto_multipart_context

        upload_result = bucket.upload_part(key, upload_id, 2, content[1], crypto_multipart_context_new_1)
        parts.append(oss2.models.PartInfo(2, upload_result.etag, size = part_size, part_crc = upload_result.crc))
        self.assertTrue(upload_result.status == 200)
        self.assertTrue(upload_result.crc is not None)

        list_result = bucket.list_parts(key, upload_id)
        self.assertTrue(list_result.status == 200)
        crypto_multipart_context_new_2 = list_result.crypto_multipart_context

        upload_result = bucket.upload_part(key, upload_id, 3, content[2], crypto_multipart_context_new_2)
        parts.append(oss2.models.PartInfo(3, upload_result.etag, size = part_size, part_crc = upload_result.crc))
        self.assertTrue(upload_result.status == 200)
        self.assertTrue(upload_result.crc is not None)

        complete_result = bucket.complete_multipart_upload(key, upload_id, parts)
        self.assertTrue(complete_result.status == 200)

        get_result_range_1 = bucket.get_object(key, byte_range=(0, 102399))
        self.assertTrue(get_result_range_1.status == 206)
        content_got_1 = get_result_range_1.read()
        self.assertEqual(content_1, content_got_1)

        get_result_range_2 = bucket.get_object(key, byte_range=(102400, 204799))
        self.assertTrue(get_result_range_2.status == 206)
        content_got_2 = get_result_range_2.read()
        self.assertEqual(content_2, content_got_2)

        get_result_range_3 = bucket.get_object(key, byte_range=(204800, 307199))
        self.assertTrue(get_result_range_3.status == 206)
        content_got_3 = get_result_range_3.read()
        self.assertEqual(content_3, content_got_3)

        get_result = bucket.get_object(key)
        self.assertTrue(get_result.status == 200)
        content_got = get_result.read()
        self.assertEqual(content_1, content_got[0:102400])
        self.assertEqual(content_2, content_got[102400:204800])
        self.assertEqual(content_3, content_got[204800:307200])

    def do_upload_part_copy_from_crypto_source(self, bucket, crypto_bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        src_object = self.random_key()
        dst_object = self.random_key()

        content = random_bytes(200 * 1024)

        # 上传源文件
        crypto_bucket.put_object(src_object, content)

        # part copy到目标文件
        parts = []
        upload_id = bucket.init_multipart_upload(dst_object).upload_id

        self.assertRaises(oss2.exceptions.NotImplemented, bucket.upload_part_copy, self.bucket.bucket_name,
                          src_object, (0, 100 * 1024 - 1), dst_object, upload_id, 1)

        abort_result = bucket.abort_multipart_upload(dst_object, upload_id)
        self.assertTrue(abort_result.status == 204)

    def do_crypto_multipart_concurrent(self, bucket, is_kms=False):
        if is_py33 and is_kms:
            return

        key1 = self.random_key()
        key1_content_1 = random_bytes(100 * 1024)
        key1_content_2 = random_bytes(100 * 1024)
        key1_content_3 = random_bytes(100 * 1024)
        key1_content = [key1_content_1, key1_content_2, key1_content_3]

        key1_parts = []
        key1_data_size = 1024 * 300
        key1_part_size = 1024 * 100

        key1_init_result = bucket.init_multipart_upload(key1, key1_data_size, key1_part_size)
        self.assertTrue(key1_init_result.status == 200)
        key1_upload_id = key1_init_result.upload_id
        key1_crypto_multipart_context = key1_init_result.crypto_multipart_context

        self.assertEqual(key1_crypto_multipart_context.data_size, 1024 * 300)
        self.assertEqual(key1_crypto_multipart_context.part_size, 1024 * 100)

        key2 = self.random_key()
        key2_content_1 = random_bytes(200 * 1024)
        key2_content_2 = random_bytes(200 * 1024)
        key2_content_3 = random_bytes(100 * 1024)
        key2_content = [key2_content_1, key2_content_2, key2_content_3]

        key2_parts = []
        key2_data_size = 1024 * 500
        key2_part_size = 1024 * 200

        key2_init_result = bucket.init_multipart_upload(key2, key2_data_size, key2_part_size)
        self.assertTrue(key2_init_result.status == 200)
        key2_upload_id = key2_init_result.upload_id
        key2_crypto_multipart_context = key2_init_result.crypto_multipart_context

        self.assertEqual(key2_crypto_multipart_context.data_size, 1024 * 500)
        self.assertEqual(key2_crypto_multipart_context.part_size, 1024 * 200)

        for i in range(3):
            key1_upload_result = bucket.upload_part(key1, key1_upload_id, i+1, key1_content[i], key1_crypto_multipart_context)
            key1_parts.append(oss2.models.PartInfo(i+1, key1_upload_result.etag, size = key1_part_size, part_crc = key1_upload_result.crc))
            self.assertTrue(key1_upload_result.status == 200)
            self.assertTrue(key1_upload_result.crc is not None)

            key2_upload_result = bucket.upload_part(key2, key2_upload_id, i+1, key2_content[i], key2_crypto_multipart_context)
            key2_parts.append(oss2.models.PartInfo(i+1, key2_upload_result.etag, size = key2_part_size, part_crc = key2_upload_result.crc))
            self.assertTrue(key2_upload_result.status == 200)
            self.assertTrue(key2_upload_result.crc is not None)

        key1_complete_result = bucket.complete_multipart_upload(key1, key1_upload_id, key1_parts)
        self.assertTrue(key1_complete_result.status == 200)

        key1_get_result = bucket.get_object(key1)
        self.assertTrue(key1_get_result.status == 200)
        key1_content_got = key1_get_result.read()
        self.assertEqual(key1_content_1, key1_content_got[0:102400])
        self.assertEqual(key1_content_2, key1_content_got[102400:204800])
        self.assertEqual(key1_content_3, key1_content_got[204800:307200])

        key2_complete_result = bucket.complete_multipart_upload(key2, key2_upload_id, key2_parts)
        self.assertTrue(key2_complete_result.status == 200)

        key2_get_result = bucket.get_object(key2)
        self.assertTrue(key2_get_result.status == 200)
        key2_content_got = key2_get_result.read()
        self.assertEqual(key2_content_1, key2_content_got[0:204800])
        self.assertEqual(key2_content_2, key2_content_got[204800:409600])
        self.assertEqual(key2_content_3, key2_content_got[409600:512000])

    def test_rsa_crypto_multipart(self):
        self.do_crypto_multipart_internal(False, self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_upload_part_content_md5_good(self):
        self.do_crypto_multipart_internal(True, self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_abort_multipart(self):
        self.do_crypto_abort_multipart(self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_list_parts(self):
        self.do_crypto_list_parts(self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_init_multipart_invalid_parameter(self):
        self.do_crypto_init_multipart_invalid_parameter(self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_upload_invalid_part_content(self):
        self.do_crypto_upload_invalid_part_content(self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_upload_invalid_last_part_content(self):
        self.do_crypto_upload_invalid_last_part_content(self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_upload_invalid_part_number(self):
        self.do_crypto_upload_invalid_part_number(self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_complete_multipart_miss_parts(self):
        self.do_crypto_complete_multipart_miss_parts(self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_resume_upload_after_loss_context(self):
        self.do_crypto_resume_upload_after_loss_context(self.rsa_crypto_bucket, is_kms=False)

    def test_upload_part_copy_from_rsa_crypto_source(self):
        self.do_upload_part_copy_from_crypto_source(self.bucket, self.rsa_crypto_bucket, is_kms=False)

    def test_rsa_crypto_multipart_concurrent(self):
        self.do_crypto_multipart_concurrent(self.rsa_crypto_bucket, is_kms=False)

    def test_kms_crypto_multipart(self):
        self.do_crypto_multipart_internal(False, self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_upload_part_content_md5_good(self):
        self.do_crypto_multipart_internal(True, self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_abort_multipart(self):
        self.do_crypto_abort_multipart(self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_list_parts(self):
        self.do_crypto_list_parts(self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_init_multipart_invalid_parameter(self):
        self.do_crypto_init_multipart_invalid_parameter(self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_upload_invalid_part_content(self):
        self.do_crypto_upload_invalid_part_content(self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_upload_invalid_last_part_content(self):
        self.do_crypto_upload_invalid_last_part_content(self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_upload_invalid_part_number(self):
        self.do_crypto_upload_invalid_part_number(self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_complete_multipart_miss_parts(self):
        self.do_crypto_complete_multipart_miss_parts(self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_resume_upload_after_loss_context(self):
        self.do_crypto_resume_upload_after_loss_context(self.kms_crypto_bucket, is_kms=True)

    def test_upload_part_copy_from_kms_crypto_source(self):
        self.do_upload_part_copy_from_crypto_source(self.bucket, self.kms_crypto_bucket, is_kms=True)

    def test_kms_crypto_multipart_concurrent(self):
        self.do_crypto_multipart_concurrent(self.rsa_crypto_bucket, is_kms=True)

if __name__ == '__main__':
    unittest.main()
