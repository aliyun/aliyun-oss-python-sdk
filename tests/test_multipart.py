# -*- coding: utf-8 -*-

import unittest
import oss2
from oss2.utils import calc_obj_crc_from_parts

from common import *


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

    def do_crypto_multipart_internal(self, do_md5, bucket):
        key = self.random_key()
        content = random_bytes(100 * 1024)

        parts = []
        data_size = 1024 * 100
        part_size = 1024 * 100

        res = bucket.init_multipart_upload_securely(key, data_size, part_size)
        upload_id = res.upload_id

        multipart_contexts_len = len(bucket.multipart_upload_contexts)
        self.assertEqual(multipart_contexts_len, 1)

        if do_md5:
            headers = {'Content-Md5': oss2.utils.content_md5(content)}
        else:
            headers = None

        result = bucket.upload_part_securely(key, upload_id, 1, content)
        parts.append(oss2.models.PartInfo(1, result.etag, size = part_size, part_crc = result.crc))
        self.assertTrue(result.crc is not None)

        context_uploaded_parts_len = len(bucket.multipart_upload_contexts[upload_id].uploaded_parts)
        self.assertEqual(context_uploaded_parts_len, 1)

        complete_result = bucket.complete_multipart_upload_securely(key, upload_id, parts)

        multipart_contexts_len = len(bucket.multipart_upload_contexts)
        self.assertEqual(multipart_contexts_len, 0)

        object_crc = calc_obj_crc_from_parts(parts)
        self.assertTrue(complete_result.crc is not None)
        self.assertEqual(object_crc, result.crc)

        result = bucket.get_object(key)
        self.assertEqual(content, result.read())

    def do_crypto_abort_internal(self, bucket):
        key = self.random_key()
        content = random_bytes(100 * 1024)

        data_size = 1024 * 100
        part_size = 1024 * 100

        res = bucket.init_multipart_upload_securely(key, data_size, part_size)
        upload_id = res.upload_id

        result = bucket.upload_part_securely(key, upload_id, 1, content)

        bucket.abort_multipart_upload_securely(key, upload_id)

        multipart_contexts_len = len(bucket.multipart_upload_contexts)
        self.assertEqual(multipart_contexts_len, 0)

    def do_crypto_list_parts_internal(self, bucket):
        key = self.random_key()
        content = random_bytes(100 * 1024)

        data_size = 1024 * 100
        part_size = 1024 * 100

        res = bucket.init_multipart_upload_securely(key, data_size, part_size)
        upload_id = res.upload_id

        bucket.upload_part_securely(key, upload_id, 1, content)

        res = bucket.list_parts_securely(key, upload_id)
        self.assertEqual(len(res.parts), 1)
        self.assertEqual(res.parts[0].part_number, 1)

        bucket.abort_multipart_upload_securely(key, upload_id)

    def test_rsa_crypto_multipart(self):
        self.do_crypto_multipart_internal(False, self.rsa_crypto_bucket)

    def test_rsa_crypto_upload_part_content_md5_good(self):
        self.do_crypto_multipart_internal(True, self.rsa_crypto_bucket)

    def test_rsa_crypto_abort(self):
        self.do_crypto_abort_internal(self.rsa_crypto_bucket)

    def test_rsa_crypto_list_parts(self):
        self.do_crypto_list_parts_internal(self.rsa_crypto_bucket)

    def test_kms_crypto_multipart(self):
        self.do_crypto_multipart_internal(False, self.kms_crypto_bucket)

    def test_kms_crypto_upload_part_content_md5_good(self):
        self.do_crypto_multipart_internal(True, self.kms_crypto_bucket)

    def test_kms_crypto_abort(self):
        self.do_crypto_abort_internal(self.kms_crypto_bucket)

    def test_kms_crypto_list_parts(self):
        self.do_crypto_list_parts_internal(self.kms_crypto_bucket)

if __name__ == '__main__':
    unittest.main()
