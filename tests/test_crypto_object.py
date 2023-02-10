# -*- coding: utf-8 -*-

import calendar
import base64
from random import choice

from oss2.exceptions import (ClientError, NotFound, NoSuchKey)
from oss2 import RsaProvider
from oss2 import http
from oss2 import headers

from .common import *
from .test_object import now
from oss2.compat import to_bytes


class TestCryptoObject(OssTestCase):
    # test cases for CryptoBucket
    def test_crypto_bucket_init_user_agent(self):
        crypto_bucket = self.rsa_crypto_bucket
        http_headers = None
        http_headers = http.CaseInsensitiveDict(http_headers)
        crypto_bucket._init_user_agent(http_headers)
        self.assertEqual(http_headers['User-Agent'], crypto_bucket.user_agent)

        user_agent = self.random_key()
        http_headers['User-Agent'] = user_agent
        crypto_bucket._init_user_agent(http_headers)
        self.assertEqual(http_headers['User-Agent'], user_agent + '/' + headers.OSS_ENCRYPTION_CLIENT)

    # 测试使用普通的Bucket读取加密的的对象数据
    def test_crypto_get_encrypted_object_with_bucket(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])

        key = self.random_key('.js')
        content = random_bytes(1024)

        self.assertRaises(NotFound, self.bucket.head_object, key)

        lower_bound = now() - 60 * 16
        upper_bound = now() + 60 * 16

        def assert_result(result):
            self.assertEqual(result.content_length, len(content))
            self.assertEqual(result.content_type, 'application/javascript')
            self.assertEqual(result.object_type, 'Normal')

            self.assertTrue(result.last_modified > lower_bound)
            self.assertTrue(result.last_modified < upper_bound)

            self.assertTrue(result.etag)

        crypto_bucket.put_object(key, content)

        get_result = self.bucket.get_object(key)
        self.assertNotEqual(get_result.read(), content)
        assert_result(get_result)
        self.assertTrue(get_result.client_crc is not None)
        self.assertTrue(get_result.server_crc is not None)
        self.assertTrue(get_result.client_crc == get_result.server_crc)

        head_result = crypto_bucket.head_object(key)
        assert_result(head_result)

        self.assertEqual(get_result.last_modified, head_result.last_modified)
        self.assertEqual(get_result.etag, head_result.etag)

        crypto_bucket.delete_object(key)
        self.assertRaises(NoSuchKey, crypto_bucket.get_object, key)

    # 测试CryptoBucket普通put、get、delete、head等功能
    def test_crypto_object_basic(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])

        key = self.random_key('.js')
        content = random_bytes(1024)

        self.assertRaises(NotFound, self.bucket.head_object, key)

        lower_bound = now() - 60 * 16
        upper_bound = now() + 60 * 16

        def assert_result(result):
            self.assertEqual(result.content_length, len(content))
            self.assertEqual(result.content_type, 'application/javascript')
            self.assertEqual(result.object_type, 'Normal')

            self.assertTrue(result.last_modified > lower_bound)
            self.assertTrue(result.last_modified < upper_bound)

            self.assertTrue(result.etag)

        crypto_bucket.put_object(key, content)

        get_result = crypto_bucket.get_object(key)
        self.assertEqual(get_result.read(), content)
        assert_result(get_result)
        self.assertTrue(get_result.client_crc is not None)
        self.assertTrue(get_result.server_crc is not None)
        self.assertTrue(get_result.client_crc == get_result.server_crc)

        head_result = crypto_bucket.head_object(key)
        assert_result(head_result)

        self.assertEqual(get_result.last_modified, head_result.last_modified)
        self.assertEqual(get_result.etag, head_result.etag)

        crypto_bucket.delete_object(key)
        self.assertRaises(NoSuchKey, crypto_bucket.get_object, key)

    def test_crypto_progress(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        stats = {'previous': -1}

        def progress_callback(bytes_consumed, total_bytes):
            self.assertTrue(bytes_consumed <= total_bytes)
            self.assertTrue(bytes_consumed > stats['previous'])
            stats['previous'] = bytes_consumed

        key = self.random_key()
        content = random_bytes(2 * 1024 * 1024)

        # 上传内存中的内容
        stats = {'previous': -1}
        crypto_bucket.put_object(key, content, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 下载到文件
        stats = {'previous': -1}
        filename = random_string(12) + '.txt'
        crypto_bucket.get_object_to_file(key, filename, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 上传本地文件
        stats = {'previous': -1}
        crypto_bucket.put_object_from_file(key, filename, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 下载到本地，采用iterator语法
        stats = {'previous': -1}
        result = crypto_bucket.get_object(key, progress_callback=progress_callback)
        content_got = b''
        for chunk in result:
            content_got += chunk
        self.assertEqual(stats['previous'], len(content))
        self.assertEqual(content, content_got)

        os.remove(filename)

    # 测试CryptoBucket range get功能
    def test_crypto_range_get(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key()
        content = random_bytes(1024)

        crypto_bucket.put_object(key, content)

        get_result = crypto_bucket.get_object(key, byte_range=(None, None))
        self.assertEqual(get_result.read(), content)

        range_start = random.randint(0, 1024)
        get_result = crypto_bucket.get_object(key, byte_range=(range_start, None))
        self.assertEqual(get_result.read(), content[range_start:])

        # CryptoBucket由于需要range get的start值与block_size对齐，这种情况下不支持range_start为None的这种情况
        range_end = random.randint(0, 1024)
        self.assertRaises(ClientError, crypto_bucket.get_object, key, byte_range=(None, range_end))

        range_start = random.randint(0, 512)
        range_end = range_start + random.randint(0, 512)
        get_result = crypto_bucket.get_object(key, byte_range=(range_start, range_end))
        self.assertEqual(get_result.read(), content[range_start:range_end + 1])

    # 测试使用Bucket类的实例读取CryptoBucket类实例上传的对象
    def test_get_crypto_object_by_nomal_bucket(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.js')
        content = random_bytes(1024)

        self.assertRaises(NotFound, crypto_bucket.head_object, key)

        result = crypto_bucket.put_object(key, content)
        self.assertTrue(result.status == 200)

        # self.assertRaises(ClientError, self.bucket.get_object, key)
        result = self.bucket.get_object(key)
        content_raw = result.read()
        self.assertEqual(len(content), len(content_raw))
        self.assertNotEqual(content, content_raw)

    # 测试使用CryptoBucket类读取Bucket类实例上传的对象
    def test_get_normal_object_by_crypto_bucket(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.js')
        content = random_bytes(1024)

        self.assertRaises(NotFound, self.bucket.head_object, key)

        result = self.bucket.put_object(key, content)
        self.assertTrue(result.status == 200)

        get_result = crypto_bucket.get_object(key)
        self.assertEqual(get_result.read(), content)

    def test_crypto_get_object_with_url(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.js')
        content = random_bytes(1024)

        result = crypto_bucket.put_object(key, content)
        self.assertTrue(result.status == 200)

        url = crypto_bucket.sign_url('GET', key, 3600)
        get_result = crypto_bucket.get_object_with_url(sign_url=url)
        self.assertEqual(get_result.read(), content)

    def test_crypto_put_object_with_url(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.js')
        content = random_bytes(1024)

        url = crypto_bucket.sign_url('PUT', key, 3600)
        self.assertRaises(ClientError, crypto_bucket.put_object_with_url, url, content)

    def test_crypto_get_object_and_process(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.jpg')
        result = crypto_bucket.put_object_from_file(key, "tests/example.jpg")
        self.assertTrue(result.status == 200)

        process = "image/resize,w_100"
        self.assertRaises(ClientError, crypto_bucket.get_object, key, process=process)

    def test_crypto_get_object_with_url_and_process(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.jpg')
        result = crypto_bucket.put_object_from_file(key, "tests/example.jpg")
        self.assertTrue(result.status == 200)

        params = {oss2.Bucket.PROCESS: "image/resize,w_100"}
        url = crypto_bucket.sign_url('GET', key, 3600, params=params)
        self.assertRaises(ClientError, crypto_bucket.get_object_with_url, url)

    # 测试使用CryptoBucket类的append接口, 此时应该抛出异常
    def test_crypto_append_object(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.log')

        self.assertRaises(NotFound, crypto_bucket.head_object, key)
        self.assertRaises(ClientError, crypto_bucket.append_object, key, 0, random_string(1024))

    def test_crypto_create_select_object_meta(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key(".csv")
        result = crypto_bucket.put_object_from_file(key, 'tests/sample_data.csv')
        self.assertTrue(result.status == 200)

        self.assertRaises(ClientError, crypto_bucket.create_select_object_meta, key)

    def test_crypto_select_object(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key(".csv")
        result = crypto_bucket.put_object_from_file(key, 'tests/sample_data.csv')
        self.assertTrue(result.status == 200)

        sql = "select Year, StateAbbr, CityName, PopulationCount from ossobject where CityName != ''"
        self.assertRaises(ClientError, crypto_bucket.select_object, key, sql)

    def test_crypto_process_object(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.jpg')
        result = crypto_bucket.put_object_from_file(key, "tests/example.jpg")
        self.assertTrue(result.status == 200)

        dest_key = key[0:len(key) - 4] + '_dest.jpg'
        process = "image/resize,w_100|sys/saveas,o_{0},b_{1}".format(
            oss2.compat.to_string(base64.urlsafe_b64encode(oss2.compat.to_bytes(dest_key))),
            oss2.compat.to_string(base64.urlsafe_b64encode(oss2.compat.to_bytes(crypto_bucket.bucket_name))))
        self.assertRaises(ClientError, crypto_bucket.process_object, key, process)

    # 测试CryptoBucket类的Copy方法
    def test_copy_crypto_object(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.js')
        content = random_bytes(1024)

        self.assertRaises(NotFound, crypto_bucket.head_object, key)

        headers = {'content-md5': oss2.utils.md5_string(content),
                   'content-length': str(len(content))}
        result = crypto_bucket.put_object(key, content, headers=headers)
        self.assertTrue(result.status == 200)

        target_key = key + "_target"
        result = crypto_bucket.copy_object(crypto_bucket.bucket_name, key, target_key)
        self.assertTrue(result.status == 200)

        def assert_result(result):
            self.assertEqual(result.content_length, len(content))
            self.assertEqual(result.content_type, 'application/javascript')
            self.assertEqual(result.object_type, 'Normal')
            self.assertTrue(result.etag)

        get_result = crypto_bucket.get_object(target_key)
        self.assertEqual(get_result.read(), content)
        assert_result(get_result)
        self.assertTrue(get_result.client_crc is not None)
        self.assertTrue(get_result.server_crc is not None)
        self.assertTrue(get_result.client_crc == get_result.server_crc)

    def test_crypto_object_incorrect_description(self):
        private_key_1 = RSA.generate(1024)
        public_key_1 = private_key_1.publickey()
        passphrase_1 = random_string(6)
        private_key_str_1 = RsaKey.exportKey(private_key_1, passphrase=passphrase_1)
        public_key_str_1 = RsaKey.exportKey(public_key_1, passphrase=passphrase_1)
        mat_desc_1 = {'key1': 'value1'}
        provider_1 = RsaProvider(key_pair={'private_key': private_key_str_1, 'public_key': public_key_str_1},
                                 passphrase=passphrase_1, mat_desc=mat_desc_1)
        crypto_bucket_1 = oss2.CryptoBucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT,
                                            self.OSS_BUCKET, crypto_provider=provider_1)
        private_key_2 = RSA.generate(2048)
        public_key_2 = private_key_2.publickey()
        passphrase_2 = random_string(6)
        private_key_str_2 = RsaKey.exportKey(private_key_2, passphrase=passphrase_2)
        public_key_str_2 = RsaKey.exportKey(public_key_2, passphrase=passphrase_2)
        mat_desc_2 = {'key2': 'value2'}
        provider_2 = RsaProvider(key_pair={'private_key': private_key_str_2, 'public_key': public_key_str_2},
                                 passphrase=passphrase_2, mat_desc=mat_desc_2)
        crypto_bucket_2 = oss2.CryptoBucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT,
                                            self.OSS_BUCKET, crypto_provider=provider_2)
        key = self.random_key('.js')
        content = random_bytes(1024)
        crypto_bucket_1.put_object(key, content)
        self.assertRaises(ClientError, crypto_bucket_2.get_object, key)

        # 口令未设置
        encryption_materials = oss2.EncryptionMaterials(mat_desc_1, key_pair={'private_key': private_key_str_1,
                                                                              'public_key': public_key_str_1})
        provider_2.add_encryption_materials(encryption_materials)
        self.assertRaises(ClientError, crypto_bucket_2.get_object, key)

        encryption_materials = oss2.EncryptionMaterials(mat_desc_1, key_pair={'private_key': private_key_str_1,
                                                                              'public_key': public_key_str_1},
                                                        passphrase=passphrase_1)
        provider_2.add_encryption_materials(encryption_materials)
        get_result = crypto_bucket_2.get_object(key)
        self.assertEqual(get_result.read(), content)

    def test_put_object_chunked(self):
        class FakeFileObj(object):
            def __init__(self, data, size):
                self.data = to_bytes(data)
                self.offset = 0
                self.size = size

            def read(self, amt=None):
                if self.offset >= self.size:
                    return to_bytes('')

                if amt is None or amt < 0:
                    bytes_to_read = self.size - self.offset
                else:
                    bytes_to_read = min(amt, self.size - self.offset)

                content = self.data[self.offset:self.offset + bytes_to_read]

                self.offset += bytes_to_read

                return content

        object_name = 'test-put-file-like-object-chunked'

        count = 1
        while count <= 100:
            count += 1
            cnt = random.randint(count, 1024)
            data = FakeFileObj(b'a' * cnt, count)
            self.rsa_crypto_bucket.put_object(object_name + str(count) + '.txt', data)
            get_result = self.rsa_crypto_bucket.get_object(object_name + str(count) + '.txt')
            self.assertEqual(get_result.read(), b'a' * count)


    '''
    # 测试CryptoBucket类的Copy方法, 并使用"REPLACE"模式修改meta
    def test_copy_crypto_object_with_replace_meta(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key('.js')
        content = random_bytes(1024)

        self.assertRaises(NotFound, crypto_bucket.head_object, key)

        result = crypto_bucket.put_object(key, content)
        self.assertTrue(result.status == 200)

        meta_key = random_string(8)
        meta_value = random_string(16)

        target_key = key + "_target"
        headers = {'content-md5': oss2.utils.md5_string(content),
                   'content-length': str(len(content)),
                   'x-oss-metadata-directive': 'REPLACE',
                   'x-oss-meta-' + meta_key: meta_value}
        result = crypto_bucket.copy_object(crypto_bucket.bucket_name, key, target_key, headers=headers)
        self.assertTrue(result.status == 200)

        def assert_result(result):
            self.assertEqual(result.headers['x-oss-meta-' + meta_key], meta_value)
            self.assertEqual(result.content_length, len(content))
            self.assertEqual(result.content_type, 'application/javascript')
            self.assertEqual(result.object_type, 'Normal')
            self.assertTrue(result.etag)

        get_result = crypto_bucket.get_object(target_key)
        self.assertEqual(get_result.read(), content)
        assert_result(get_result)
        self.assertTrue(get_result.client_crc is not None)
        self.assertTrue(get_result.server_crc is not None)
        self.assertTrue(get_result.client_crc == get_result.server_crc)

    # 测试CryptoBucket类的Copy方法，修改加密元数据抛出异常
    def test_copy_crypto_object_with_replace_encryption_meta(self):
        crypto_bucket = choice([self.rsa_crypto_bucket, self.kms_crypto_bucket])
        key = self.random_key()
        dest_key = key + "-dest"

        content = random_bytes(1024)

        self.assertRaises(NotFound, crypto_bucket.head_object, key)

        result = crypto_bucket.put_object(key, content)
        self.assertTrue(result.status == 200)

        # replace mode, will raise excepiton InvalidEncryptionRequest
        headers = {'content-md5': oss2.utils.md5_string(content),
                   'content-length': str(len(content)),
                   'x-oss-metadata-directive': 'REPLACE',
                   'x-oss-meta-client-side-encryption-key': random_string(16)}
        self.assertRaises(oss2.exceptions.InvalidEncryptionRequest, crypto_bucket.copy_object,
                          self.bucket.bucket_name, key, dest_key, headers=headers)

        # copy mode, will ignore
        headers = {'content-md5': oss2.utils.md5_string(content),
                   'content-length': str(len(content)),
                   'x-oss-meta-client-side-encryption-key': random_string(16)}
        result = crypto_bucket.copy_object(crypto_bucket.bucket_name, key, dest_key, headers=headers)
        self.assertTrue(result.status == 200)

        result = crypto_bucket.get_object(key)
        self.assertEqual(result.read(), content)
    '''
