# -*- coding: utf-8 -*-
import json
import unittest
import os

from aliyunsdkcore import client

import oss2
import unittests
from oss2 import LocalRsaProvider, AliKMSProvider
from oss2.utils import AESCipher, silently_remove
from oss2.exceptions import OpenApiServerError, OpenApiFormatError, ClientError
from mock import patch

from common import OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK, OSS_STS_ID, OSS_STS_ARN, OSS_STS_KEY, random_string
from aliyunsdksts.request.v20150401 import AssumeRoleRequest
from Crypto.PublicKey import RSA
import random


class TestCrypto(unittests.common.OssTestCase):
    # 测试初始化LocalRsaProvider时未初始化cipher，此时应该抛出异常
    def test_local_rsa_provider_init_cipher_is_none(self):
        self.assertRaises(ClientError, LocalRsaProvider, dir='./', key='rsa-test', cipher=None)

    # 测试当keys不存在时，未设置gen_keys时，初始化LocalRsaProvider时抛出异常
    def test_local_rsa_provider_init_keys_not_exist(self):
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')
        self.assertRaises(ClientError, LocalRsaProvider, dir='./', key='rsa-test')

    # 测试keys内容不是对称rsa密钥时，初始化LocalRsaProvider时抛出异常
    def test_local_rsa_provider_init_invalid_keys(self):
        private_key = RSA.generate(2048)
        public_key = private_key.publickey()
        # 这个地方修改private_key的内容
        private_key = random_string(2048)

        with open('./rsa-test.private_key.pem', 'wb') as f:
            f.write(private_key)

        with open('./rsa-test.public_key.pem', 'wb') as f:
            f.write(public_key.exportKey())

        self.assertRaises(ClientError, LocalRsaProvider, dir='./', key='rsa-test')
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

    # 测试当keys存在时，使用错误的passpass初始化LocalRsaProvider时抛出异常
    def test_local_rsa_provider_init_invalid_passphrase(self):
        private_key = RSA.generate(2048)
        public_key = private_key.publickey()
        passphrase = random_string(6)
        invalid_passphrase = random_string(8)

        with open('./rsa-test.private_key.pem', 'wb') as f:
            f.write(private_key.exportKey(passphrase=passphrase))

        with open('./rsa-test.public_key.pem', 'wb') as f:
            f.write(public_key.exportKey(passphrase=passphrase))

        self.assertRaise(ClientError, LocalRsaProvider, dir='./', key='rsa-test', passphrase=invalid_passphrase)
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

    # 测试基本key, start加/解密
    def test_local_rsa_provider_basic(self):
        provider = LocalRsaProvider(dir='./', key='rsa-test', gen_keys=True, passphrase=random_string(8))
        self.assertEqual(provider.wrap_alg, "rsa")
        self.assertEqual(provider.cipher.alg, "AES/CTR/NoPadding")
        plain_key = provider.get_key()
        self.assertEqual(len(plain_key), provider.cipher.key_len)
        plain_start = provider.get_start()
        self.assertTrue(1 <= plain_start <= 10)

        with patch.object(oss2.utils, 'random_aes_256_key', return_value=plain_key, autospect=True):
            with patch.object(oss2.utils, 'random_counter', return_value=plain_start, autospect=True):
                content_crypto_material = provider.create_content_material()
                self.assertFalse(content_crypto_material.is_invalid())
                decrypted_key = provider.decrypt_encrypted_key(content_crypto_material.encrypted_start)
                decrypted_start = provider.decrypt_encrypted_start(content_crypto_material.encrypted_key)
                self.assertEqual(plain_key, decrypted_key)
                self.assertEqual(plain_start, decrypted_start)

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

    # 测试使用不同的rsa keys的provider
    def test_local_rsa_provider_diff_keys(self):
        provider = LocalRsaProvider(dir='./', key='rsa-test', gen_keys=True)
        provider_diff = LocalRsaProvider(dir='./', key='rsa-test-diff', gen_keys=True)
        self.assertRaises(ClientError, provider.check_magic_number_hmac, provider_diff.encryption_magic_number_hmac)

        plain_key = provider.get_key()
        plain_start = provider.get_start()

        with patch.object(oss2.utils, 'random_aes_256_key', return_value=plain_key, autospect=True):
            with patch.object(oss2.utils, 'random_counter', return_value=plain_start, autospect=True):
                content_crypto_material = provider.create_content_material()
                self.assertFalse(content_crypto_material.is_invalid())
                decrypted_key_diff = provider_diff.decrypt_encrypted_key(content_crypto_material.encrypted_start)
                decrypted_start_diff = provider_diff.decrypt_encrypted_start(content_crypto_material.encrypted_key)
                self.assertNotEqual(plain_key, decrypted_key_diff)
                self.assertNotEqual(plain_start, decrypted_start_diff)

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')
        silently_remove('./rsa-test-diff.public_key.pem')
        silently_remove('./rsa-test-diff.private_key.pem')

    def test_local_rsa_provider_adapter(self):
        provider = LocalRsaProvider(dir='./', key='rsa-test', gen_keys=True)
        content = b'a' * random.randint(1, 100) * 1024
        content_crypto_material = provider.create_content_material()

        stream_encrypted = provider.make_encrypt_adapter(content, content_crypto_material.cipher)
        stream_decrypted = provider.make_decrypt_adapter(stream_encrypted, content_crypto_material.cipher)
        self.assertEqual(content, stream_decrypted.read())

        discard = random.randint(1, 15)
        stream_decrypted = provider.make_decrypt_adapter(stream_encrypted, content_crypto_material.cipher,
                                                         discard=discard)
        self.assertEqual(content[discard:], stream_decrypted)

        # 使用不同的content crypto material
        content_crypto_material_diff = provider.create_content_material()
        stream_encrypted_diff = provider.make_encrypt_adapter(content, content_crypto_material_diff.cipher)
        self.assertNotEqual(stream_encrypted_diff, stream_encrypted)
        stream_decrypted_diff = provider.make_decrypt_adapter(stream_encrypted, content_crypto_material_diff.cipher)
        self.assertEqual(content, stream_decrypted_diff.read())

        discard = random.randint(1, 15)
        stream_decrypted = provider.make_decrypt_adapter(stream_encrypted_diff, content_crypto_material_diff.cipher,
                                                         discard=discard)
        self.assertEqual(content[discard:], stream_decrypted)

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

    # 测试初始化AliKMSProvider时未初始化cipher，此时应该抛出异常
    def test_ali_kms_provider_init_cipher_is_none(self):
        id, key, token = self.get_sts()
        self.assertRaises(ClientError, AliKMSProvider, access_key_id=id, access_key_secret=key, region=OSS_REGION,
                          cmk_id=OSS_CMK, cipher=None)

    # 测试基本key, start加/解密
    def test_ali_kms_provider_basic(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK, passphrase=random_string(8))
        self.assertEqual(provider.wrap_alg, "rsa")
        self.assertEqual(provider.cipher.alg, "AES/CTR/NoPadding")
        plain_key, encrypted_key = provider.get_key()
        plain_start = provider.get_start()

        with patch('oss2.AliKMSProvider.get_key', return_value=(plain_key, encrypted_key)):
            with patch.object(oss2.utils, 'random_counter', return_value=plain_start, autospect=True):
                content_crypto_material = provider.create_content_material()
            self.assertFalse(content_crypto_material.is_invalid())
            decrypted_key = provider.decrypt_encrypted_key(content_crypto_material.encrypted_start)
            decrypted_start = provider.decrypt_encrypted_start(content_crypto_material.encrypted_key)
            self.assertEqual(plain_key, decrypted_key)
            self.assertEqual(plain_start, decrypted_start)

    # 测试使用不同的passphrase解析加密key和start抛出异常
    def test_ali_kms_provider_diff_passphrase(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK, passphrase=random_string(6))
        plain_key, encrypted_key = provider.get_key()
        encrypted_start = provider.get_start()

        provider_diff = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK, passphrase=random_string(8))
        self.assertRaises(OpenApiServerError, provider_diff.decrypt_encrypted_key(encrypted_key))
        self.assertRaises(OpenApiServerError, provider_diff.decrypt_encrypted_key(encrypted_start))

    # 测试使用不同的region解析加密key和start时抛出异常
    def test_ali_kms_provider_invalid_region(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK)
        plain_key, encrypted_key = provider.get_key()
        encrypted_start = provider.get_start()

        region_list = ['oss-cn-hangzhou', 'oss-cn-shanghai', 'oss-cn-qingdao', 'oss-cn-beijing', 'oss-cn-zhangjiakou',
                       'oss-cn-huhehaote', 'oss-cn-shenzhen', 'oss-cn-hongkong', 'oss-us-west-1', 'oss-us-east-1',
                       'oss-ap-southeast-1', 'oss-ap-southeast-2', 'oss-ap-southeast-3', 'oss-ap-southeast-5',
                       'oss-ap-northeast-1', 'oss-ap-south-1', 'oss-eu-central-1', 'oss-eu-west-1', 'oss-me-east-1']

        if OSS_REGION in region_list:
            region_list.remove(OSS_REGION)

        region_num = len(region_list)
        invalid_region = region_list[random.randint(0, region_num - 1)]

        provider_invalid = AliKMSProvider(OSS_ID, OSS_SECRET, invalid_region, OSS_CMK)
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key(encrypted_key))
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key(encrypted_start))

    # 测试使用不同的ak解析加密key和start的值时抛出异常
    def test_ali_kms_provider_invalid_ak(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK)
        plain_key, encrypted_key = provider.get_key()
        encrypted_start = provider.get_start()

        invalid_secret = random_string(len(OSS_SECRET))
        provider_invalid = AliKMSProvider(OSS_ID, invalid_secret, OSS_REGION, OSS_CMK)
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key(encrypted_key))
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key(encrypted_start))

        invald_id = random_string(len(OSS_ID))
        provider_invalid = AliKMSProvider(invald_id, OSS_SECRET, OSS_REGION, OSS_CMK)
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key(encrypted_key))
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key(encrypted_start))

    # 测试kms服务返回错误的情况
    def test_kms_with_error_response(self):
        if oss2.compat.is_py33:
            return

        kms = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK)

        # 模拟返回的数据格式不对，不是正确的json格式字符串
        plain_key = random_string(32)
        ecrypted_key = random_string(32)
        with patch.object(client.AcsClient, 'do_action_with_exception',
                          return_value="{'Plaintext': {0}, 'CiphertextBlob': {1}}".format(plain_key, ecrypted_key),
                          autospect=True):
            self.assertRaises(OpenApiFormatError, kms.get_key)

    def test_local_rsa_provider_adapter(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK)
        content = b'a' * random.randint(1, 100) * 1024
        content_crypto_material = provider.create_content_material()

        stream_encrypted = provider.make_encrypt_adapter(content, content_crypto_material.cipher)
        stream_decrypted = provider.make_decrypt_adapter(stream_encrypted, content_crypto_material.cipher)
        self.assertEqual(content, stream_decrypted.read())

        discard = random.randint(1, 15)
        stream_decrypted = provider.make_decrypt_adapter(stream_encrypted, content_crypto_material.cipher,
                                                         discard=discard)
        self.assertEqual(content[discard:], stream_decrypted)

        # 使用不同的content crypto material
        content_crypto_material_diff = provider.create_content_material()
        stream_encrypted_diff = provider.make_encrypt_adapter(content, content_crypto_material_diff.cipher)
        self.assertNotEqual(stream_encrypted_diff, stream_encrypted)
        stream_decrypted_diff = provider.make_decrypt_adapter(stream_encrypted, content_crypto_material_diff.cipher)
        self.assertEqual(content, stream_decrypted_diff.read())

        discard = random.randint(1, 15)
        stream_decrypted = provider.make_decrypt_adapter(stream_encrypted_diff, content_crypto_material_diff.cipher,
                                                         discard=discard)
        self.assertEqual(content[discard:], stream_decrypted)

    def get_sts(self):
        clt = client.AcsClient(OSS_STS_ID, OSS_STS_KEY, OSS_REGION)
        req = AssumeRoleRequest.AssumeRoleRequest()

        req.set_accept_format('json')
        req.set_RoleArn(OSS_STS_ARN)
        req.set_RoleSessionName('oss-python-sdk-example')

        body = clt.do_action_with_exception(req)

        j = json.loads(oss2.to_unicode(body))

        return j['Credentials']['AccessKeyId'], j['Credentials']['AccessKeySecret'], j['Credentials']['SecurityToken']
