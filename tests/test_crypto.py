# -*- coding: utf-8 -*-
import json
import unittest
import os

from aliyunsdkcore import client

import oss2
import unittests
from oss2 import LocalRsaProvider, AliKMSProvider, RsaProvider, compat
from oss2.utils import AESCipher, silently_remove
from oss2.exceptions import OpenApiServerError, OpenApiFormatError, ClientError
from mock import patch

from .common import OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK_REGION, OSS_CMK, OSS_STS_ID, OSS_STS_ARN, OSS_STS_KEY, random_string, \
    key_pair, key_pair_compact
from aliyunsdksts.request.v20150401 import AssumeRoleRequest
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
import random


class TestCrypto(unittests.common.OssTestCase):
    # 测试初始化LocalRsaProvider时未初始化cipher，此时应该抛出异常
    def test_rsa_provider_init_cipher_is_none(self):
        self.assertRaises(ClientError, LocalRsaProvider, dir='./', key='rsa-test', cipher=None)
        self.assertRaises(ClientError, RsaProvider, key_pair=key_pair, cipher=None)

    # 测试当keys不存在时, local_rsa_provider会创建一个默认的密钥对
    def test_rsa_provider_init_keys_not_exist(self):
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')
        provider = LocalRsaProvider(dir='./', key='rsa-test')
        self.assertTrue(os.path.exists('./rsa-test.public_key.pem'))
        self.assertTrue(os.path.exists('./rsa-test.private_key.pem'))
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

    # 测试keys内容不是对称rsa密钥时，初始化LocalRsaProvider时抛出异常
    def test_rsa_provider_init_invalid_keys(self):
        private_key = RSA.generate(2048)
        public_key = private_key.publickey()
        # 这个地方修改private_key的内容
        private_key = random_string(2048)

        with open('./rsa-test.private_key.pem', 'wb') as f:
            f.write(oss2.to_bytes(private_key))

        with open('./rsa-test.public_key.pem', 'wb') as f:
            f.write(public_key.exportKey())

        self.assertRaises(ClientError, LocalRsaProvider, dir='./', key='rsa-test')
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        self.assertRaises(ClientError, RsaProvider, key_pair={'private_key': private_key, 'public_key': public_key})

    # 测试当keys存在时，使用错误的passpass初始化LocalRsaProvider时抛出异常
    def test_rsa_provider_init_invalid_passphrase(self):
        private_key = RSA.generate(2048)
        public_key = private_key.publickey()
        passphrase = random_string(6)
        invalid_passphrase = random_string(8)

        with open('./rsa-test.private_key.pem', 'wb') as f:
            f.write(private_key.exportKey(passphrase=passphrase))

        with open('./rsa-test.public_key.pem', 'wb') as f:
            f.write(public_key.exportKey(passphrase=passphrase))

        self.assertRaises(ClientError, LocalRsaProvider, dir='./', key='rsa-test', passphrase=invalid_passphrase)
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        private_key_str = RsaKey.exportKey(private_key, passphrase=passphrase)
        public_key_str = RsaKey.exportKey(public_key, passphrase=passphrase)

        self.assertRaises(ClientError, RsaProvider,
                          key_pair={'private_key': private_key_str, 'public_key': public_key_str},
                          passphrase=invalid_passphrase)

    # 测试基本key, start加/解密
    def test_rsa_provider_basic(self):
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        provider = LocalRsaProvider(dir='./', key='rsa-test', passphrase=random_string(8))
        self.assertEqual(provider.wrap_alg, "RSA/NONE/OAEPWithSHA-1AndMGF1Padding")
        self.assertEqual(provider.cipher.alg, "AES/CTR/NoPadding")
        plain_key = provider.get_key()
        self.assertEqual(len(plain_key), provider.cipher.key_len)
        plain_iv = provider.get_iv()

        with patch.object(oss2.utils, 'random_key', return_value=plain_key, autospect=True):
            with patch.object(oss2.utils, 'random_iv', return_value=plain_iv, autospect=True):
                content_crypto_material = provider.create_content_material()
                self.assertFalse(content_crypto_material.is_unencrypted())
                decrypted_key = provider.decrypt_encrypted_key(content_crypto_material.encrypted_key)
                decrypted_iv = provider.decrypt_encrypted_iv(content_crypto_material.encrypted_iv)
                self.assertEqual(plain_key, decrypted_key)
                self.assertEqual(plain_iv, decrypted_iv)

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        provider = RsaProvider(key_pair=key_pair, passphrase=random_string(8))
        self.assertEqual(provider.wrap_alg, "RSA/NONE/PKCS1Padding")
        self.assertEqual(provider.cipher.alg, "AES/CTR/NoPadding")
        plain_key = provider.get_key()
        self.assertEqual(len(plain_key), provider.cipher.key_len)
        plain_iv = provider.get_iv()

        with patch.object(oss2.utils, 'random_key', return_value=plain_key, autospect=True):
            with patch.object(oss2.utils, 'random_iv', return_value=plain_iv, autospect=True):
                content_crypto_material = provider.create_content_material()
                self.assertFalse(content_crypto_material.is_unencrypted())
                decrypted_key = provider.decrypt_encrypted_key(content_crypto_material.encrypted_key)
                decrypted_iv = provider.decrypt_encrypted_iv(content_crypto_material.encrypted_iv)
                self.assertEqual(plain_key, decrypted_key)
                self.assertEqual(plain_iv, decrypted_iv)

    # 测试使用不同的rsa keys的provider
    def test_local_rsa_provider_diff_keys(self):
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')
        silently_remove('./rsa-test-diff.public_key.pem')
        silently_remove('./rsa-test-diff.private_key.pem')

        provider = LocalRsaProvider(dir='./', key='rsa-test')
        provider_diff = LocalRsaProvider(dir='./', key='rsa-test-diff')

        plain_key = provider.get_key()
        plain_iv = provider.get_iv()

        with patch.object(oss2.utils, 'random_key', return_value=plain_key, autospect=True):
            with patch.object(oss2.utils, 'random_iv', return_value=plain_iv, autospect=True):
                content_crypto_material = provider.create_content_material()
                self.assertFalse(content_crypto_material.is_unencrypted())
                self.assertRaises(ClientError, provider_diff.decrypt_encrypted_key,
                                  content_crypto_material.encrypted_key)
                self.assertRaises(ClientError, provider_diff.decrypt_encrypted_iv,
                                  content_crypto_material.encrypted_iv)

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')
        silently_remove('./rsa-test-diff.public_key.pem')
        silently_remove('./rsa-test-diff.private_key.pem')

        provider = RsaProvider(key_pair=key_pair)
        provider_diff = RsaProvider(key_pair=key_pair_compact)

        plain_key = provider.get_key()
        plain_iv = provider.get_iv()

        with patch.object(oss2.utils, 'random_key', return_value=plain_key, autospect=True):
            with patch.object(oss2.utils, 'random_iv', return_value=plain_iv, autospect=True):
                content_crypto_material = provider.create_content_material()
                self.assertFalse(content_crypto_material.is_unencrypted())
                self.assertRaises(ClientError, provider_diff.decrypt_encrypted_key,
                                  content_crypto_material.encrypted_key)
                self.assertRaises(ClientError, provider_diff.decrypt_encrypted_iv,
                                  content_crypto_material.encrypted_iv)

    def test_rsa_provider_adapter(self):
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        provider = LocalRsaProvider(dir='./', key='rsa-test')
        content = b'a' * random.randint(1, 100) * 1024
        content_crypto_material = provider.create_content_material()
        plain_key = provider.decrypt_encrypted_key(content_crypto_material.encrypted_key)
        plain_iv = provider.decrypt_encrypted_iv(content_crypto_material.encrypted_iv)
        cipher = content_crypto_material.cipher

        stream_encrypted = provider.make_encrypt_adapter(content, cipher)
        encrypted_content = stream_encrypted.read()
        # reset cipher
        cipher.initialize(plain_key, plain_iv)
        stream_decrypted = provider.make_decrypt_adapter(encrypted_content, cipher)
        self.assertEqual(content, stream_decrypted.read())

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        provider = RsaProvider(key_pair)
        content = b'b' * random.randint(1, 100) * 1024
        content_crypto_material = provider.create_content_material()
        plain_key = provider.decrypt_encrypted_key(content_crypto_material.encrypted_key)
        plain_iv = provider.decrypt_encrypted_iv(content_crypto_material.encrypted_iv)
        cipher = content_crypto_material.cipher

        stream_encrypted = provider.make_encrypt_adapter(content, cipher)
        encrypted_content = stream_encrypted.read()
        # reset cipher
        cipher.initialize(plain_key, plain_iv)
        stream_decrypted = provider.make_decrypt_adapter(encrypted_content, cipher)
        self.assertEqual(content, stream_decrypted.read())

    # 测试初始化AliKMSProvider时未初始化cipher，此时应该抛出异常
    def test_ali_kms_provider_init_cipher_is_none(self):
        id, key, token = self.get_sts()
        self.assertRaises(ClientError, AliKMSProvider, access_key_id=id, access_key_secret=key, region=OSS_REGION,
                          cmk_id=OSS_CMK, cipher=None)

    # 测试基本key, start加/解密
    def test_ali_kms_provider_basic(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_CMK_REGION, OSS_CMK, passphrase=random_string(8))
        self.assertEqual(provider.wrap_alg, "KMS/ALICLOUD")
        self.assertEqual(provider.cipher.alg, "AES/CTR/NoPadding")
        plain_key, encrypted_key = provider.get_key()
        plain_iv = provider.get_iv()

        with patch('oss2.AliKMSProvider.get_key', return_value=[plain_key, encrypted_key]):
            with patch.object(oss2.utils, 'random_iv', return_value=plain_iv, autospect=True):
                content_crypto_material = provider.create_content_material()
                self.assertFalse(content_crypto_material.is_unencrypted())
                decrypted_key = provider.decrypt_encrypted_key(content_crypto_material.encrypted_key)
                decrypted_iv = provider.decrypt_encrypted_iv(content_crypto_material.encrypted_iv)
                self.assertEqual(plain_key, decrypted_key)
                self.assertEqual(plain_iv, decrypted_iv)

    # 测试使用不同的passphrase解析加密key和start抛出异常
    def test_ali_kms_provider_diff_passphrase(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_CMK_REGION, OSS_CMK, passphrase=random_string(6))
        plain_key, encrypted_key = provider.get_key()
        encrypted_iv = provider.get_iv()

        provider_diff = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_CMK_REGION, OSS_CMK, passphrase=random_string(8))
        self.assertRaises(OpenApiServerError, provider_diff.decrypt_encrypted_key, encrypted_key)
        self.assertRaises(OpenApiServerError, provider_diff.decrypt_encrypted_iv, encrypted_iv)

    # 测试使用不同的region解析加密key和start时抛出异常
    def test_ali_kms_provider_invalid_region(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_CMK_REGION, OSS_CMK)
        plain_key, encrypted_key = provider.get_key()
        encrypted_iv = provider.get_iv()

        region_list = ['cn-hangzhou', 'cn-shanghai', 'cn-qingdao', 'cn-beijing', 'cn-zhangjiakou',
                       'cn-huhehaote', 'cn-shenzhen', 'cn-hongkong', 'us-west-1', 'us-east-1',
                       'ap-southeast-1', 'ap-southeast-2', 'ap-southeast-3', 'ap-southeast-5',
                       'ap-northeast-1', 'ap-south-1', 'eu-central-1', 'eu-west-1', 'me-east-1']

        if OSS_REGION in region_list:
            region_list.remove(OSS_REGION)

        region_num = len(region_list)
        invalid_region = region_list[random.randint(0, region_num - 1)]

        provider_invalid = AliKMSProvider(OSS_ID, OSS_SECRET, invalid_region, OSS_CMK)
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key, encrypted_key)
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key, encrypted_iv)

    # 测试使用不同的ak解析加密key和start的值时抛出异常
    def test_ali_kms_provider_invalid_ak(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_CMK_REGION, OSS_CMK)
        plain_key, encrypted_key = provider.get_key()
        encrypted_iv = provider.get_iv()

        invalid_secret = random_string(len(OSS_SECRET))
        provider_invalid = AliKMSProvider(OSS_ID, invalid_secret, OSS_CMK_REGION, OSS_CMK)
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key, encrypted_key)
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key, encrypted_iv)

        invald_id = random_string(len(OSS_ID))
        provider_invalid = AliKMSProvider(invald_id, OSS_SECRET, OSS_CMK_REGION, OSS_CMK)
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key, encrypted_key)
        self.assertRaises(OpenApiServerError, provider_invalid.decrypt_encrypted_key, encrypted_iv)

    # 测试kms服务返回错误的情况
    def test_ali_kms_with_error_response(self):
        if oss2.compat.is_py33:
            return

        kms = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_CMK_REGION, OSS_CMK)

        # 模拟返回的数据格式不对，不是正确的json格式字符串
        plain_key = random_string(32)
        encrypted_key = random_string(32)
        return_value = "{'Plaintext': %s, 'CiphertextBlob': %s}" % (plain_key, encrypted_key)
        with patch.object(client.AcsClient, 'do_action_with_exception', return_value=return_value, autospect=True):
            self.assertRaises(OpenApiFormatError, kms.get_key)

    def test_ali_kms_provider_adapter(self):
        provider = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_CMK_REGION, OSS_CMK)
        content = b'a' * random.randint(1, 100) * 1024
        content_crypto_material = provider.create_content_material()

        plain_key = provider.decrypt_encrypted_key(content_crypto_material.encrypted_key)
        plain_iv = provider.decrypt_encrypted_iv(content_crypto_material.encrypted_iv)
        cipher = content_crypto_material.cipher

        stream_encrypted = provider.make_encrypt_adapter(content, cipher)
        encrypted_content = stream_encrypted.read()
        # reset cipher
        cipher.initialize(plain_key, plain_iv)
        stream_decrypted = provider.make_decrypt_adapter(encrypted_content, cipher)
        self.assertEqual(content, stream_decrypted.read())

        # 使用不同的content crypto material
        content_crypto_material_diff = provider.create_content_material()
        plain_key = provider.decrypt_encrypted_key(content_crypto_material_diff.encrypted_key)
        plain_iv = provider.decrypt_encrypted_iv(content_crypto_material_diff.encrypted_iv)
        cipher = content_crypto_material_diff.cipher

        stream_encrypted_diff = provider.make_encrypt_adapter(content, cipher)
        encrypted_content_diff = stream_encrypted_diff.read()
        self.assertNotEqual(encrypted_content_diff, encrypted_content)
        # reset cipher
        cipher.initialize(plain_key, plain_iv)
        stream_decrypted_diff = provider.make_decrypt_adapter(encrypted_content_diff, cipher)
        self.assertEqual(content, stream_decrypted_diff.read())

    def get_sts(self):
        clt = client.AcsClient(OSS_STS_ID, OSS_STS_KEY, OSS_REGION)
        req = AssumeRoleRequest.AssumeRoleRequest()

        req.set_accept_format('json')
        req.set_RoleArn(OSS_STS_ARN)
        req.set_RoleSessionName('oss-python-sdk-example')

        body = clt.do_action_with_exception(req)

        j = json.loads(compat.to_unicode(body))

        return j['Credentials']['AccessKeyId'], j['Credentials']['AccessKeySecret'], j['Credentials'][
            'SecurityToken']
