# -*- coding: utf-8 -*-

from .common import *
import oss2
from oss2 import models


class TestCryptoMultipart(OssTestCase):
    def test_crypto_init_multipart_with_out_data_size(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key()

        # upload_context is none
        self.assertRaises(oss2.exceptions.ClientError, crypto_bucket.init_multipart_upload, key)

        # data_size is none
        part_size = 1024 * 100
        context = models.MultipartUploadCryptoContext(part_size=part_size)
        self.assertRaises(oss2.exceptions.ClientError, crypto_bucket.init_multipart_upload, key, upload_context=context)

    def test_crypto_init_multipart_invalid_part_size(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key()

        data_size = 1024 * 100
        part_size = random.randint(1, 15) + 1024 * 100
        context = models.MultipartUploadCryptoContext(data_size, part_size)

        # not align to block_size
        self.assertRaises(oss2.exceptions.ClientError, crypto_bucket.init_multipart_upload, key, upload_context=context)

        # part size is small than 100*1024
        part_size = random.randint(1, 1024 * 100 - 1)
        context.part_size = part_size
        self.assertRaises(oss2.exceptions.ClientError, crypto_bucket.init_multipart_upload, key, upload_context=context)

    # 测试不指定part_size的情况，由接口指定part_size
    def test_crypto_init_multipart_with_out_part_size(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key()
        data_size = 1024 * 100

        # init multipart without part_size
        context = models.MultipartUploadCryptoContext(data_size)
        init_result = crypto_bucket.init_multipart_upload(key, upload_context=context)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id
        abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)

    def test_crypto_abort_multipart(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key()
        content = random_bytes(100 * 1024)

        data_size = 1024 * 100
        part_size = 1024 * 100

        context = models.MultipartUploadCryptoContext(data_size, part_size)
        init_result = crypto_bucket.init_multipart_upload(key, upload_context=context)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id

        upload_result = crypto_bucket.upload_part(key, upload_id, 1, content, upload_context=context)
        self.assertTrue(upload_result.status == 200)
        self.assertTrue(upload_result.crc is not None)

        abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)

    def test_crypto_multipart_upload_basic(self):
        for upload_contexts_flag in [False, False]:
            crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
            key = self.random_key()
            content_1 = random_bytes(200 * 1024)
            content_2 = random_bytes(200 * 1024)
            content_3 = random_bytes(100 * 1024)
            content = [content_1, content_2, content_3]
            do_md5 = random.choice((True, False))

            parts = []
            data_size = 1024 * 500
            part_size = 1024 * 200

            context = models.MultipartUploadCryptoContext(data_size, part_size)
            init_result = crypto_bucket.init_multipart_upload(key, upload_context=context)
            self.assertTrue(init_result.status == 200)
            upload_id = init_result.upload_id

            for i in range(3):
                if do_md5:
                    headers = {'Content-Md5': oss2.utils.content_md5(content[i])}
                else:
                    headers = None
                upload_result = crypto_bucket.upload_part(key, upload_id, i + 1, content[i], headers=headers,
                                                          upload_context=context)
                parts.append(oss2.models.PartInfo(i + 1, upload_result.etag, size=len(content[i]),
                                                  part_crc=upload_result.crc))
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

    def test_upload_part_copy_from_crypto_source(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        src_object = self.random_key()
        dst_object = src_object + '-dest'

        content = random_bytes(300 * 1024)

        # 上传源文件
        crypto_bucket.put_object(src_object, content)

        # upload part copy到目标文件
        # upload_id = self.bucket.init_multipart_upload(dst_object).upload_id
        # self.assertRaises(oss2.exceptions.NotImplemented, self.bucket.upload_part_copy, self.bucket.bucket_name,
        # src_object, (0, 100 * 1024 - 1), dst_object, upload_id, 1)
        # abort_result = self.bucket.abort_multipart_upload(dst_object, upload_id)
        # self.assertTrue(abort_result.status == 204)

        data_size = len(content)
        part_size = 100 * 1024
        context = models.MultipartUploadCryptoContext(data_size, part_size)
        upload_id = crypto_bucket.init_multipart_upload(dst_object, upload_context=context).upload_id
        self.assertRaises(oss2.exceptions.ClientError, crypto_bucket.upload_part_copy,
                          crypto_bucket.bucket_name,
                          src_object, (0, 100 * 1024 - 1), dst_object, upload_id, 1)

        abort_result = crypto_bucket.abort_multipart_upload(dst_object, upload_id)
        self.assertTrue(abort_result.status == 204)

    def test_crypto_multipart_concurrency(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key1 = self.random_key()
        key1_content_1 = random_bytes(100 * 1024)
        key1_content_2 = random_bytes(100 * 1024)
        key1_content_3 = random_bytes(100 * 1024)
        key1_content = [key1_content_1, key1_content_2, key1_content_3]

        key1_parts = []
        key1_data_size = 1024 * 300
        key1_part_size = 1024 * 100

        context1 = models.MultipartUploadCryptoContext(key1_data_size, key1_part_size)
        key1_init_result = crypto_bucket.init_multipart_upload(key1, upload_context=context1)
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

        context2 = models.MultipartUploadCryptoContext(key2_data_size, key2_part_size)
        key2_init_result = crypto_bucket.init_multipart_upload(key2, upload_context=context2)
        self.assertTrue(key2_init_result.status == 200)
        key2_upload_id = key2_init_result.upload_id

        for i in range(3):
            key1_upload_result = crypto_bucket.upload_part(key1, key1_upload_id, i + 1, key1_content[i],
                                                           upload_context=context1)
            key1_parts.append(oss2.models.PartInfo(i + 1, key1_upload_result.etag,
                                                   part_crc=key1_upload_result.crc))
            self.assertTrue(key1_upload_result.status == 200)
            self.assertTrue(key1_upload_result.crc is not None)

            key2_upload_result = crypto_bucket.upload_part(key2, key2_upload_id, i + 1, key2_content[i],
                                                           upload_context=context2)
            key2_parts.append(oss2.models.PartInfo(i + 1, key2_upload_result.etag, size=len(key2_content[i]),
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

    '''
    def test_crypto_upload_invalid_part_content(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key()
        content_invalid = random_bytes(random.randint(1, 100 * 1024 - 1))

        data_size = 250 * 1024 - 1
        part_size = 1024 * 100

        init_result = crypto_bucket.init_multipart_upload(key, data_size, part_size)
        self.assertTrue(init_result.status == 200)
        upload_id = init_result.upload_id

        # invalid part size
        self.assertRaises(oss2.exceptions.InvalidEncryptionRequest, crypto_bucket.upload_part, key, upload_id, 1,
                          content_invalid)

        abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)
    '''

    '''
    def test_crypto_upload_invalid_last_part_content(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
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
    '''

    '''
    def test_crypto_upload_invalid_part_number(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
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
    '''

    '''
    def test_crypto_complete_multipart_miss_parts(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
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
                oss2.models.PartInfo(i + 1, upload_result.etag, size=len(content[i]), part_crc=upload_result.crc))
            self.assertTrue(upload_result.status == 200)
            self.assertTrue(upload_result.crc is not None)

        self.assertRaises(oss2.exceptions.InvalidEncryptionRequest, crypto_bucket.complete_multipart_upload,
                          key,
                          upload_id, parts)

        abort_result = crypto_bucket.abort_multipart_upload(key, upload_id)
        self.assertTrue(abort_result.status == 204)
    '''

    '''
    def test_crypto_list_parts(self):
        crypto_bucket = random.choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
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
    '''
