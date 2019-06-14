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

from .common import OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK, OSS_STS_ID, OSS_STS_ARN, OSS_STS_KEY
from aliyunsdksts.request.v20150401 import AssumeRoleRequest


class TestCrypto(unittests.common.OssTestCase):
    def test_rsa_basic(self):
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        crypto = LocalRsaProvider(dir='./', key='rsa-test', passphrase='1234')

        with patch.object(oss2.utils, 'random_aes256_key', return_value=unittests.common.fixed_aes_key, autospect=True):
            with patch.object(oss2.utils, 'random_counter', return_value=unittests.common.fixed_aes_start, autospect=True):
                crypto.get_key()
                crypto.get_start()
                header = crypto.build_header()
                self.assertEqual(unittests.common.fixed_aes_key, crypto.decrypt_oss_meta_data(header, 'x-oss-meta-oss-crypto-key'))
                self.assertEqual(unittests.common.fixed_aes_start, crypto.decrypt_oss_meta_data(header, 'x-oss-meta-oss-crypto-start', lambda x:int(x)))
                self.assertEqual(None, crypto.decrypt_oss_meta_data(header, '1231'))

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

    def test_rsa_with_error_parameter(self):
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        crypto = LocalRsaProvider(dir='./', key='rsa-test', passphrase='1234')

        self.assertRaises(ClientError, LocalRsaProvider, dir='./', key='rsa-test')

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')


    def test_rsa_adapter(self):
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        content = b'1234'*10

        rsa = LocalRsaProvider(dir='./', key='rsa-test', passphrase='1234')
        key = rsa.get_key()
        start = rsa.get_start()
        adapter = rsa.make_encrypt_adapter(content, key, start)
        encrypt_content = adapter.read()
        self.assertNotEqual(content, encrypt_content)

        adapter1 = rsa.make_decrypt_adapter(encrypt_content, key, start)
        self.assertEqual(content, adapter1.read())

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

    def test_AES(self):
        cipher = AESCipher()

        content = unittests.common.random_bytes(1024 * 1024 - 1)

        encrypted_content = cipher.encrypt(content)

        self.assertNotEqual(content, encrypted_content)

        cipher1 = AESCipher(key=cipher.key, start=cipher.start)
        self.assertEqual(content, cipher1.decrypt(encrypted_content))

    def test_kms_basic(self):
        if oss2.compat.is_py33:
            return

        id, key, token = self.get_sts()

        kms = AliKMSProvider(id, key, OSS_REGION, OSS_CMK, token, passphrase='1234')

        plain_key = kms.get_key()
        iv = kms.get_start()
        header = kms.build_header()
        self.assertEqual(plain_key, kms.decrypt_oss_meta_data(header, 'x-oss-meta-oss-crypto-key'))
        self.assertEqual(iv, kms.decrypt_oss_meta_data(header, 'x-oss-meta-oss-crypto-start', lambda x: int(x)))
        self.assertEqual(None, kms.decrypt_oss_meta_data(header, '1231'))

    def test_kms_with_error_parameter(self):
        if oss2.compat.is_py3:
            return

        def assertKmsFuncRaises(kms, error=OpenApiServerError):
            self.assertRaises(error, kms.get_key)
            self.assertRaises(error, kms._AliKMSProvider__encrypt_data, '123')
            self.assertRaises(error, kms._AliKMSProvider__decrypt_data, '123')
            self.assertRaises(error, kms._AliKMSProvider__generate_data_key)
            self.assertRaises(error, kms.decrypt_oss_meta_data, {'123': '456'}, '123')

        kms = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK)
        plain_key = kms.get_key()

        kms_with_passphrase = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK, passphrase='1234')
        plain_key1 = kms_with_passphrase.get_key()
        self.assertRaises(OpenApiServerError, kms_with_passphrase._AliKMSProvider__decrypt_data, plain_key)
        self.assertRaises(OpenApiServerError, kms._AliKMSProvider__decrypt_data, plain_key1)

        kms_with_error_regin = AliKMSProvider(OSS_ID, OSS_SECRET, "123", OSS_CMK)
        assertKmsFuncRaises(kms_with_error_regin, error=ClientError)

        kms_with_error_cmk = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, '123')
        assertKmsFuncRaises(kms_with_error_cmk)

        kms_with_error_id = AliKMSProvider('123', OSS_SECRET, OSS_REGION, OSS_CMK)
        assertKmsFuncRaises(kms_with_error_id)

        kms_with_error_secret = AliKMSProvider(OSS_ID, '123', OSS_REGION, OSS_CMK)
        assertKmsFuncRaises(kms_with_error_secret)

        self.assertRaises(ClientError, AliKMSProvider, OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK, cipher=object)

    def test_kms_with_error_response(self):
        if oss2.compat.is_py33:
            return

        kms = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK)

        with patch.object(oss2.AliKMSProvider, '_AliKMSProvider__do', return_value={'Plaintext': '123', 'CiphertextBlob': '123'},
                          autospect=True):
            self.assertRaises(OpenApiFormatError, kms.get_key)

        with patch.object(client.AcsClient, 'do_action_with_exception', return_value='12iof..3', autospect=True):
            self.assertRaises(OpenApiFormatError, kms.get_key)
            self.assertRaises(OpenApiFormatError, kms._AliKMSProvider__encrypt_data, '123')
            self.assertRaises(OpenApiFormatError, kms._AliKMSProvider__decrypt_data, '123')
            self.assertRaises(OpenApiFormatError, kms._AliKMSProvider__generate_data_key)
            self.assertRaises(OpenApiFormatError, kms.decrypt_oss_meta_data, {'1231': '1234'}, '1231')

    def test_kms_adapter(self):
        if oss2.compat.is_py33:
            return

        content = b'1234'*10

        kms = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK)
        key = kms.get_key()
        start = kms.get_start()
        adapter = kms.make_encrypt_adapter(content, key, start)
        encrypt_content = adapter.read()
        self.assertNotEqual(content, encrypt_content)

        adapter1 = kms.make_decrypt_adapter(encrypt_content, key, start)
        self.assertEqual(content, adapter1.read())

    def get_sts(self):
        clt = client.AcsClient(OSS_STS_ID, OSS_STS_KEY, OSS_REGION)
        req = AssumeRoleRequest.AssumeRoleRequest()

        req.set_accept_format('json')
        req.set_RoleArn(OSS_STS_ARN)
        req.set_RoleSessionName('oss-python-sdk-example')

        body = clt.do_action_with_exception(req)

        j = json.loads(oss2.to_unicode(body))

        return j['Credentials']['AccessKeyId'], j['Credentials']['AccessKeySecret'], j['Credentials']['SecurityToken']
