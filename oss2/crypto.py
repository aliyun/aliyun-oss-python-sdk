# -*- coding: utf-8 -*-

"""
oss2.encryption
~~~~~~~~~~~~~~

该模块包含了客户端加解密相关的函数和类。
"""
import json

from oss2.utils import b64decode_from_string, b64encode_as_string
from . import utils
from .compat import to_string, to_bytes, to_unicode
from .exceptions import OssError, ClientError, FormatError, OpenApiServerError

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from aliyunsdkcore import client
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkcore.http import protocol_type, format_type, method_type
from aliyunsdkkms.request.v20160120 import ListKeysRequest, GenerateDataKeyRequest, DecryptRequest, EncryptRequest

import os

_AES_GCM = 'AES/GCM/NoPadding'

_LOCAL_RSA_TMP_DIR = '.py-oss-rsa'


class LocalRsaProvider():
    PUB_KEY_FILE = '.public_key.pem'
    PRIV_KEY_FILE = '.private_key.pem'

    def __init__(self, dir=None, key='default', passphrase=None):

        self.dir = dir or os.path.join(os.path.expanduser('~'), _LOCAL_RSA_TMP_DIR)

        utils.makedir_p(self.dir)

        priv_key_full_path = os.path.join(self.dir, key + self.PRIV_KEY_FILE)
        pub_key_full_path = os.path.join(self.dir, key + self.PUB_KEY_FILE)

        if os.path.exists(priv_key_full_path) and os.path.exists(pub_key_full_path):
            with open(priv_key_full_path, 'rb') as f:
                self.__decrypt_obj = PKCS1_OAEP.new(RSA.importKey(f.read(), passphrase=passphrase))

            with open(pub_key_full_path, 'rb') as f:
                self.__encrypt_obj = PKCS1_OAEP.new(RSA.importKey(f.read(), passphrase=passphrase))

        else:
            private_key = RSA.generate(2048)
            public_key = private_key.publickey()

            self.__encrypt_obj = PKCS1_OAEP.new(public_key)
            self.__decrypt_obj = PKCS1_OAEP.new(private_key)

            with open(priv_key_full_path, 'wb') as f:
                f.write(private_key.exportKey(passphrase=passphrase))

            with open(pub_key_full_path, 'wb') as f:
                f.write(public_key.exportKey(passphrase=passphrase))

        self.key = None
        self.iv = None

    def build_header(self, headers=None):
        headers = headers or {}
        if 'content-md5' in headers:
            headers['x-oss-meta-unencrypted-content-md5'] = headers['content-md5']
            del headers['content-md5']

        if 'content-length' in headers:
            headers['x-oss-meta-unencrypted-content-length'] = headers['content-length']
            del headers['content-length']

        headers['x-oss-meta-oss-crypto-key'] = b64encode_as_string(self.__encrypt_obj.encrypt(self.key))
        headers['x-oss-meta-oss-crypto-start'] = b64encode_as_string(self.__encrypt_obj.encrypt(to_bytes(str(self.iv))))
        headers['x-oss-meta-oss-cek-alg'] = _AES_GCM
        headers['x-oss-meta-oss-wrap-alg'] = 'rsa'

        self.key = None
        self.iv = None

        return headers

    def get_key(self):
        self.key = utils.random_aes256_key()
        return self.key

    def get_iv(self):
        self.iv = utils.random_counter()
        return self.iv

    def decrypt_oss_meta_data(self, headers, key, conv=lambda x:x):
        try:
            return conv(self.__decrypt_obj.decrypt(utils.b64decode_from_string(headers[key])))
        except:
            return None


class AliKMSProvider():

    def __init__(self, access_key_id, access_key_secret, region, cmkey, sts_token = None, passphrase=None):

        self.cmkey = cmkey
        self.sts_token = sts_token
        self.context = '{"x-passphrase":"' + passphrase + '"}' if passphrase else ''
        self.clt = client.AcsClient(access_key_id, access_key_secret, region)

        self.encrypted_key = None
        self.iv = None

    def build_header(self, headers=None):
        headers = headers or {}
        if 'content-md5' in headers:
            headers['x-oss-meta-unencrypted-content-md5'] = headers['content-md5']
            del headers['content-md5']

        if 'content-length' in headers:
            headers['x-oss-meta-unencrypted-content-length'] = headers['content-length']
            del headers['content-length']

        headers['x-oss-meta-oss-crypto-key'] = self.encrypted_key
        headers['x-oss-meta-oss-crypto-start'] = self.__encrypt_data(to_bytes(str(self.iv)))
        headers['x-oss-meta-oss-cek-alg'] = _AES_GCM
        headers['x-oss-meta-oss-wrap-alg'] = 'kms'

        self.encrypted_key = None
        self.iv = None

        return headers

    def get_key(self):
        plain_key, self.encrypted_key = self.__generate_data_key()
        return plain_key

    def get_iv(self):
        self.iv = utils.random_counter()
        return self.iv

    def __generate_data_key(self):
        req = GenerateDataKeyRequest.GenerateDataKeyRequest()

        req.set_accept_format(format_type.JSON)
        req.set_method(method_type.POST)

        req.set_KeyId(self.cmkey)
        req.set_KeySpec('AES_256')
        req.set_NumberOfBytes(32)
        req.set_EncryptionContext(self.context)
        if self.sts_token:
            req.set_STSToken(self.sts_token)

        resp = self.__do(req)

        return b64decode_from_string(resp['Plaintext']), resp['CiphertextBlob']

    def __encrypt_data(self, data):
        req = EncryptRequest.EncryptRequest()

        req.set_accept_format(format_type.JSON)
        req.set_method(method_type.POST)
        req.set_KeyId(self.cmkey)
        req.set_Plaintext(data)
        req.set_EncryptionContext(self.context)
        if self.sts_token:
            req.set_STSToken(self.sts_token)

        resp = self.__do(req)

        return resp['CiphertextBlob']

    def __decrypt_data(self, data):
        req = DecryptRequest.DecryptRequest()

        req.set_accept_format(format_type.JSON)
        req.set_method(method_type.POST)
        req.set_CiphertextBlob(data)
        req.set_EncryptionContext(self.context)
        if self.sts_token:
            req.set_STSToken(self.sts_token)

        resp = self.__do(req)
        return resp['Plaintext']

    def __do(self, req):

        try:
            body = self.clt.do_action_with_exception(req)

            return json.loads(to_unicode(body))
        except ServerException as e:
            raise OpenApiServerError(e.http_status, e.request_id, e.message, e.error_code)
        except ClientException as e:
            raise ClientError(e.message)
        except (ValueError, TypeError) as e:
            raise FormatError('Json Error: ' + body)

    def decrypt_oss_meta_data(self, headers, key, conv=lambda x: x):
        try:
            if key == 'x-oss-meta-oss-crypto-key':
                return conv(b64decode_from_string(self.__decrypt_data(headers[key])))
            else:
                return conv(self.__decrypt_data(headers[key]))
        except OssError as e:
            raise e
        except:
            return None