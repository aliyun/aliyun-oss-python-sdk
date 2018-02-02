# -*- coding: utf-8 -*-
import json
import unittest
import os

from aliyunsdkcore import client

import oss2
import unittests
from oss2 import LocalRsaProvider, AliKMSProvider
from oss2.utils import AESCipher, silently_remove
from oss2.exceptions import OpenApiServerError, FormatError, ClientError
from mock import patch

from common import OSS_ID, OSS_SECRET, OSS_REGION, OSS_CMK, OSS_STS_ID, OSS_STS_ARN, OSS_STS_KEY
from aliyunsdksts.request.v20150401 import AssumeRoleRequest


class TestCrypto(unittests.common.OssTestCase):
    def test_rsa_basic(self):
        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

        crypto = LocalRsaProvider(dir='./', key='rsa-test', passphrase='1234')

        with patch.object(oss2.utils, 'random_aes256_key', return_value=unittests.common.fixed_aes_key, autospect=True):
            with patch.object(oss2.utils, 'random_counter', return_value=unittests.common.fixed_aes_start, autospect=True):
                crypto.get_key()
                crypto.get_iv()
                header = crypto.build_header()
                self.assertEqual(unittests.common.fixed_aes_key, crypto.decrypt_oss_meta_data(header, 'x-oss-meta-oss-crypto-key'))
                self.assertEqual(unittests.common.fixed_aes_start, crypto.decrypt_oss_meta_data(header, 'x-oss-meta-oss-crypto-start', lambda x:int(x)))
                self.assertEqual(None, crypto.decrypt_oss_meta_data(header, '1231'))

        silently_remove('./rsa-test.public_key.pem')
        silently_remove('./rsa-test.private_key.pem')

    def test_AES(self):
        cipher = AESCipher()

        content = unittests.common.random_bytes(1024 * 1024 - 1)

        encrypted_cont = cipher.encrypt(content)

        self.assertNotEqual(content, encrypted_cont)

        cipher1 = AESCipher(key=cipher.key, start=cipher.start)
        self.assertEqual(content, cipher1.decrypt(encrypted_cont))

    def test_kms_basic(self):
        if oss2.compat.is_py2:
            id, key, token = self.get_sts()

            kms = AliKMSProvider(id, key, OSS_REGION, OSS_CMK, token, passphrase='1234')

            plain_key = kms.get_key()
            iv = kms.get_iv()
            header = kms.build_header()
            self.assertEqual(plain_key, kms.decrypt_oss_meta_data(header, 'x-oss-meta-oss-crypto-key'))
            self.assertEqual(iv, kms.decrypt_oss_meta_data(header, 'x-oss-meta-oss-crypto-start', lambda x: int(x)))
            self.assertEqual(None, kms.decrypt_oss_meta_data(header, '1231'))

    def test_kms_raise(self):
        if oss2.compat.is_py2:

            kms = AliKMSProvider(OSS_ID, OSS_SECRET, OSS_REGION, '123')

            self.assertRaises(OpenApiServerError, kms.get_key)
            self.assertRaises(OpenApiServerError, kms._AliKMSProvider__encrypt_data, '123')
            self.assertRaises(OpenApiServerError, kms._AliKMSProvider__decrypt_data, '123')
            self.assertRaises(OpenApiServerError, kms._AliKMSProvider__generate_data_key)
            self.assertRaises(OpenApiServerError, kms.decrypt_oss_meta_data, {'123':'456'}, '123')

            class FakeReq:
                def set_accept_format(self, format):
                    pass

            self.assertRaises(ClientError, kms._AliKMSProvider__do, FakeReq())

            with patch.object(oss2.AliKMSProvider, '_AliKMSProvider__do', return_value={'Plaintext': '123', 'CiphertextBlob': '123'},
                              autospect=True):
                self.assertRaises(FormatError, kms.get_key)

            with patch.object(client.AcsClient, 'do_action_with_exception', return_value='12iof..3', autospect=True):
                self.assertRaises(FormatError, kms.get_key)

    def get_sts(self):
        clt = client.AcsClient(OSS_STS_ID, OSS_STS_KEY, OSS_REGION)
        req = AssumeRoleRequest.AssumeRoleRequest()

        req.set_accept_format('json')
        req.set_RoleArn(OSS_STS_ARN)
        req.set_RoleSessionName('oss-python-sdk-example')

        body = clt.do_action_with_exception(req)

        j = json.loads(oss2.to_unicode(body))

        return j['Credentials']['AccessKeyId'], j['Credentials']['AccessKeySecret'], j['Credentials']['SecurityToken']
