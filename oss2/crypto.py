# -*- coding: utf-8 -*-

"""
oss2.encryption
~~~~~~~~~~~~~~

该模块包含了客户端加解密相关的函数和类。
"""
import abc
import hashlib
import json
import os
from functools import partial

import six
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from aliyunsdkcore import client
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkcore.http import format_type, method_type
from aliyunsdkkms.request.v20160120 import GenerateDataKeyRequest, DecryptRequest, EncryptRequest

from . import models
from utils import b64decode_from_string
from . import utils
from .compat import to_bytes, to_unicode
from .exceptions import ClientError, OpenApiFormatError, OpenApiServerError


@six.add_metaclass(abc.ABCMeta)
class BaseCryptoProvider(object):
    """CryptoProvider 基类，提供基础的数据加密解密adapter

    """

    def __init__(self, cipher=None):
        self.cipher = cipher
        self.wrap_alg = None
        self.mat_desc = None

    @abc.abstractmethod
    def get_key(self):
        pass

    def get_start(self):
        return self.cipher.get_start()

    def make_encrypt_adapter(self, stream, cipher):
        return utils.make_cipher_adapter(stream, partial(cipher.encrypt))

    def make_decrypt_adapter(self, stream, cipher, discard=0):
        return utils.make_cipher_adapter(stream, partial(cipher.decrypt), discard)

    @abc.abstractmethod
    def decrypt_encrypted_key(self, encrypted_key):
        pass

    @abc.abstractmethod
    def decrypt_encrypted_start(self, encrypted_start):
        pass

    def adjust_range(self, start, end):
        return self.cipher.adjust_range(start, end)

    @abc.abstractmethod
    def create_content_material(self):
        pass


_LOCAL_RSA_TMP_DIR = '.oss-local-rsa'
RSA_WRAP_ALGORITHM = 'rsa'
KMS_WRAP_ALGORITHM = 'kms'


@six.add_metaclass(abc.ABCMeta)
class LocalRsaProvider(BaseCryptoProvider):
    """使用本地RSA加密数据密钥。

        :param str dir: 本地RSA公钥私钥存储路径
        :param str key: 本地RSA公钥私钥名称前缀
        :param str passphrase: 本地RSA公钥私钥密码
        :param class cipher: 数据加密，默认aes256，用户可自行实现对称加密算法，需符合AESCipher注释规则
    """

    DEFAULT_PUB_KEY_SUFFIX = '.public_key.pem'
    DEFAULT_PRIV_KEY_SUFFIX = '.private_key.pem'
    # "Hello, OSS!"
    MAGIC_NUMBER = '56AAD346-F0899BFE-8BDD02C0-6BBE511E'

    def __init__(self, dir=None, key='', passphrase=None, cipher=utils.AESCTRCipher(),
                 pub_key_suffix=DEFAULT_PUB_KEY_SUFFIX, private_key_suffix=DEFAULT_PRIV_KEY_SUFFIX, gen_keys=False):
        super(LocalRsaProvider, self).__init__(cipher=cipher)

        self.wrap_alg = RSA_WRAP_ALGORITHM
        keys_dir = dir or os.path.join(os.path.expanduser('~'), _LOCAL_RSA_TMP_DIR)

        priv_key_path = os.path.join(keys_dir, key + private_key_suffix)
        pub_key_path = os.path.join(keys_dir, key + pub_key_suffix)
        try:
            if os.path.exists(priv_key_path) and os.path.exists(pub_key_path):
                with open(priv_key_path, 'rb') as f:
                    self.__decrypt_obj = PKCS1_OAEP.new(RSA.importKey(f.read(), passphrase=passphrase))

                with open(pub_key_path, 'rb') as f:
                    self.__encrypt_obj = PKCS1_OAEP.new(RSA.importKey(f.read(), passphrase=passphrase))

                # In this place, to check the rsa keys are ok
                encryption_magic_number = self.__encrypt_obj.encrypt(self.MAGIC_NUMBER)
                magic_number = self.__decrypt_obj.decrypt(encryption_magic_number)

                if magic_number != self.MAGIC_NUMBER:
                    raise ClientError('The public and private keys do not match')

            else:
                if not gen_keys:
                    raise ClientError('The file path of private key or public key is not exist')

                private_key = RSA.generate(2048)
                public_key = private_key.publickey()

                self.__encrypt_obj = PKCS1_OAEP.new(public_key)
                self.__decrypt_obj = PKCS1_OAEP.new(private_key)

                utils.makedir_p(keys_dir)
                with open(priv_key_path, 'wb') as f:
                    f.write(private_key.exportKey(passphrase=passphrase))

                with open(pub_key_path, 'wb') as f:
                    f.write(public_key.exportKey(passphrase=passphrase))
                encryption_magic_number = self.__encrypt_data(self.MAGIC_NUMBER)

            sha256 = hashlib.sha256()
            sha256.update(encryption_magic_number)
            self.encryption_magic_number_hmac = sha256.hexdigest()
        except (ValueError, TypeError, IndexError) as e:
            raise ClientError(str(e))

    def get_key(self):
        return self.cipher.get_key()

    def decrypt_encrypted_key(self, encrypted_key):
        return self.__decrypt_data(encrypted_key)

    def decrypt_encrypted_start(self, encrypted_start):
        return self.__decrypt_data(encrypted_start)

    def create_content_material(self):
        plain_key = self.get_key()
        encrypted_key = self.__encrypt_data(plain_key)
        plain_start = self.get_start()
        encrypted_start = self.__encrypt_data(to_bytes(str(plain_start)))
        cipher = self.cipher
        wrap_alg = self.wrap_alg
        mat_desc = self.mat_desc
        cipher.initialize(plain_key, plain_start)

        content_crypto_material = models.ContentCryptoMaterial(cipher, wrap_alg, encrypted_key, encrypted_start,
                                                               mat_desc)
        content_crypto_material.encrypted_magic_number_hmac = self.encryption_magic_number_hmac
        return content_crypto_material

    def check_magic_number_hmac(self, magic_number_hmac):
        if magic_number_hmac != self.encryption_magic_number_hmac:
            raise ClientError("The hmac of magic number is inconsistent, please check the RSA keys pair")

    def __encrypt_data(self, data):
        return self.__encrypt_obj.encrypt(data)

    def __decrypt_data(self, data):
        return self.__decrypt_obj.decrypt(data)


class AliKMSProvider(BaseCryptoProvider):
    """使用aliyun kms服务加密数据密钥。kms的详细说明参见
        https://help.aliyun.com/product/28933.html?spm=a2c4g.11186623.3.1.jlYT4v
        此接口在py3.3下暂时不可用，详见
        https://github.com/aliyun/aliyun-openapi-python-sdk/issues/61

        :param str access_key_id: 可以访问kms密钥服务的access_key_id
        :param str access_key_secret: 可以访问kms密钥服务的access_key_secret
        :param str region: kms密钥服务地区
        :param str cmkey: 用户主密钥
        :param str sts_token: security token，如果使用的是临时AK需提供
        :param str passphrase: kms密钥服务密码
        :param class cipher: 数据加密，默认aes256，当前仅支持默认实现
    """

    def __init__(self, access_key_id, access_key_secret, region, cmk_id, sts_token=None, passphrase=None,
                 cipher=utils.AESCTRCipher()):

        if not isinstance(cipher, utils.AESCTRCipher):
            raise ClientError('AliKMSProvider only support AES256 cipher')

        super(AliKMSProvider, self).__init__(cipher=cipher)
        self.wrap_alg = KMS_WRAP_ALGORITHM
        self.custom_master_key_id = cmk_id
        self.sts_token = sts_token
        self.context = '{"x-passphrase":"' + passphrase + '"}' if passphrase else ''
        self.kms_client = client.AcsClient(access_key_id, access_key_secret, region)

    def get_key(self):
        plain_key, encrypted_key = self.__generate_data_key()
        return plain_key, encrypted_key

    def decrypt_encrypted_key(self, encrypted_key):
        return b64decode_from_string(self.__decrypt_data(encrypted_key))

    def decrypt_encrypted_start(self, encrypted_start):
        return self.__decrypt_data(encrypted_start)

    def create_content_material(self):
        plain_key, encrypted_key = self.get_key()
        plain_start = self.get_start()
        encrypted_start = self.__encrypt_data(to_bytes(str(plain_start)))
        cipher = self.cipher
        wrap_alg = self.wrap_alg
        mat_desc = self.mat_desc
        cipher.initialize(plain_key, plain_start)

        content_crypto_material = models.ContentCryptoMaterial(cipher, wrap_alg, encrypted_key, encrypted_start,
                                                               mat_desc)
        return content_crypto_material

    def __generate_data_key(self):
        req = GenerateDataKeyRequest.GenerateDataKeyRequest()

        req.set_accept_format(format_type.JSON)
        req.set_method(method_type.POST)

        req.set_KeyId(self.custom_master_key_id)
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
        req.set_KeyId(self.custom_master_key_id)
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
            body = self.kms_client.do_action_with_exception(req)
            return json.loads(to_unicode(body))
        except ServerException as e:
            raise OpenApiServerError(e.http_status, e.request_id, e.message, e.error_code)
        except ClientException as e:
            raise ClientError(e.message)
        except (ValueError, TypeError) as e:
            raise OpenApiFormatError('Json Error: ' + str(e))
