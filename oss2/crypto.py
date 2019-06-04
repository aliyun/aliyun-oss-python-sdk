# -*- coding: utf-8 -*-

"""
oss2.encryption
~~~~~~~~~~~~~~

该模块包含了客户端加解密相关的函数和类。
"""
import json
from functools import partial

from oss2.utils import b64decode_from_string, b64encode_as_string
from . import utils
from .compat import to_string, to_bytes, to_unicode
from .exceptions import OssError, ClientError, OpenApiFormatError, OpenApiServerError
from .headers import *
from .models import _hget

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from requests.structures import CaseInsensitiveDict

from aliyunsdkcore import client
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkcore.http import protocol_type, format_type, method_type
from aliyunsdkkms.request.v20160120 import ListKeysRequest, GenerateDataKeyRequest, DecryptRequest, EncryptRequest

import os
import hashlib
import abc


class ContentCryptoMaterial(object):
    def __init__(self, cipher, wrap_alg, encrypted_key=None, encrypted_start=None, mat_desc=None):
        self.cipher = cipher
        self.wrap_alg = wrap_alg
        self.encrypted_key = encrypted_key
        self.encrypted_start = encrypted_start
        self.mat_desc = mat_desc
        self.encrypted_magic_number_hmac = None

    def to_object_meta(self, headers=None, multipart_context=None):
        if not isinstance(headers, CaseInsensitiveDict):
            headers = CaseInsensitiveDict(headers)

        if 'content-md5' in headers:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_UNENCRYPTED_CONTENT_MD5] = headers['content-md5']
            del headers['content-md5']

        if 'content-length' in headers:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_UNENCRYPTED_CONTENT_LENGTH] = headers['content-length']
            del headers['content-length']

        headers[OSS_CLIENT_SIDE_ENCRYPTION_KEY] = b64encode_as_string(self.encrypted_key)
        headers[OSS_CLIENT_SIDE_ENCRYPTION_START] = b64encode_as_string(self.encrypted_start)
        headers[OSS_CLIENT_SIDE_ENCRYPTION_CEK_ALG] = self.cipher.ALGORITHM
        headers[OSS_CLIENT_SIDE_ENCRYPTION_WRAP_ALG] = self.wrap_alg
        if self.encrypted_magic_number_hmac:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_MAGIC_NUMBER_HMAC] = b64encode_as_string(
                self.encrypted_magic_number_hmac)

        # multipart file build header
        if multipart_context and multipart_context.data_size and multipart_context.part_size:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_DATA_SIZE] = str(multipart_context.data_size)
            headers[OSS_CLIENT_SIDE_ENCRYPTION_PART_SIZE] = str(multipart_context.part_size)

        return headers

    def from_object_meta(self, headers):
        if DEPRECATED_CLIENT_SIDE_ENCRYPTION_KEY in headers:
            deprecated = True

        if deprecated:
            self.encrypted_key = _hget(headers, DEPRECATED_CLIENT_SIDE_ENCRYPTION_KEY)
            self.encrypted_start = _hget(headers, DEPRECATED_CLIENT_SIDE_ENCRYPTION_START)
            self.wrap_alg = _hget(headers, DEPRECATED_CLIENT_SIDE_ENCRYPTION_WRAP_ALG)
            self.mat_desc = _hget(headers, DEPRECATED_CLIENT_SIDE_ENCRYTPION_MATDESC)
        else:
            self.encrypted_key = _hget(headers, OSS_CLIENT_SIDE_ENCRYPTION_KEY)
            self.encrypted_start = _hget(headers, OSS_CLIENT_SIDE_ENCRYPTION_START)
            self.wrap_alg = _hget(headers, OSS_CLIENT_SIDE_ENCRYPTION_WRAP_ALG)
            self.mat_desc = _hget(headers, OSS_CLIENT_SIDE_ENCRYTPION_MATDESC)
            if self.wrap_alg == RSA_WRAP_ALGORITHM:
                self.encrypted_magic_number_hmac = _hget(headers, OSS_CLIENT_SIDE_ENCRYPTION_MAGIC_NUMBER_HMAC)


class BaseCryptoProvider(metaclass=abc.ABCMeta):
    """CryptoProvider 基类，提供基础的数据加密解密adapter

    """

    def __init__(self, cipher=None):
        self.cipher = cipher
        self.wrap_alg = None
        self.mat_desc = None

    def get_key(self):
        return self.cipher.get_key()

    def get_start(self):
        return self.cipher.get_start()

    def make_encrypt_adapter(self, stream, cipher):
        return utils.make_cipher_adapter(stream, partial(self.cipher.encrypt, cipher))

    def make_decrypt_adapter(self, stream, cipher, discard=0):
        return utils.make_cipher_adapter(stream, partial(self.cipher.decrypt, cipher), discard)

    @abc.abstractmethod
    def decrypt_encrypted_key(self, encrypted_key):
        pass

    @abc.abstractmethod
    def decrypt_encrypted_start(self, encrypted_start):
        pass

    def adjust_range(self, start, end):
        return self.cipher.adjust_range(start, end)

    def create_content_material(self):
        plain_key = self.get_key()
        encrypted_key = self.__encrypt_data(plain_key)
        plain_start = self.get_start()
        encrypted_start = self.__encrypt_data(to_bytes(str(plain_start)))
        wrap_alg = self.wrap_alg
        mat_desc = self.mat_desc
        cipher = self.cipher.__class__(plain_key, plain_start)

        return ContentCryptoMaterial(cipher, encrypted_key, encrypted_start, wrap_alg, mat_desc)

    @abc.abstractmethod
    def __encrypt_data(self, data):
        pass

    @abc.abstractmethod
    def __decrypt_data(self, data):
        pass


_LOCAL_RSA_TMP_DIR = '.oss-local-rsa'
RSA_WRAP_ALGORITHM = 'rsa'
KMS_WRAP_ALGORITHM = 'kms'


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

    def __init__(self, dir=None, key='', passphrase=None, cipher=utils.AESCTRCipher,
                 pub_key_suffix=DEFAULT_PUB_KEY_SUFFIX, private_key_suffix=DEFAULT_PRIV_KEY_SUFFIX, generate=False):
        super(LocalRsaProvider, self).__init__(cipher=cipher)

        self.wrap_alg = self.RSA_WRAP_ALGORITHM
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
                if not generate:
                    raise ClientError('The file path of private key or public key is not exist')

                private_key = RSA.generate(2048)
                public_key = private_key.publickey()

                self.__encrypt_obj = PKCS1_OAEP.new(public_key)
                self.__decrypt_obj = PKCS1_OAEP.new(private_key)

                utils.makedir_p(self.dir)
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

    '''
    def decrypt_encryption_meta(self, headers, key):
        try:
            if key.lower() in [OSS_CLIENT_SIDE_ENCRYPTION_KEY.lower(), DEPRECATED_CLIENT_SIDE_ENCRYPTION_KEY.lower(),
                               OSS_CLIENT_SIDE_ENCRYPTION_START.lower(),
                               DEPRECATED_CLIENT_SIDE_ENCRYPTION_START.lower()]:
                return self.__decrypt_data(utils.b64decode_from_string(headers[key]))
            else:
                return headers[key]
        except:
            return None
    '''

    def decrypt_encrypted_key(self, encrypted_key):
        return self.__decrypt_data(utils.b64decode_from_string(encrypted_key))

    def decrypt_encrypted_start(self, encrypted_start):
        return self.__decrypt_data(encrypted_start)

    def check_magic_number_hmac(self, magic_number_hmac):
        if magic_number_hmac != b64encode_as_string(self.encryption_magic_number_hmac):
            raise ClientError("The hmac of magic number is inconsistent, please check the RSA keys pair")

    def create_content_material(self):
        content_crypto_material = super(LocalRsaProvider, self).create_content_material()
        content_crypto_material.encrypted_magic_number_hmac = self.encryption_magic_number_hmac
        return content_crypto_material

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
                 cipher=utils.AESCTRCipher):

        if not issubclass(cipher, utils.AESCipher):
            raise ClientError('AliKMSProvider only support AES256 cipher')

        super(AliKMSProvider, self).__init__(cipher=cipher, wrap_alg=KMS_WRAP_ALGORITHM)
        self.custom_master_key_id = cmk_id
        self.sts_token = sts_token
        self.context = '{"x-passphrase":"' + passphrase + '"}' if passphrase else ''
        self.kms_client = client.AcsClient(access_key_id, access_key_secret, region)

        self.encrypted_key = None

    def add_encryption_meta(self, headers=None, multipart_context=None):
        if not isinstance(headers, CaseInsensitiveDict):
            headers = CaseInsensitiveDict(headers)

        if 'content-md5' in headers:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_UNENCRYPTED_CONTENT_MD5] = headers['content-md5']
            del headers['content-md5']

        if 'content-length' in headers:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_UNENCRYPTED_CONTENT_LENGTH] = headers['content-length']
            del headers['content-length']

        headers[OSS_CLIENT_SIDE_ENCRYPTION_KEY] = self.encrypted_key
        headers[OSS_CLIENT_SIDE_ENCRYPTION_START] = self.__encrypt_data(to_bytes(str(self.plain_start)))
        headers[OSS_CLIENT_SIDE_ENCRYPTION_CEK_ALG] = self.cipher.ALGORITHM
        headers[OSS_CLIENT_SIDE_ENCRYPTION_WRAP_ALG] = 'kms'

        # multipart file build header
        if multipart_context:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_DATA_SIZE] = str(multipart_context.data_size)
            headers[OSS_CLIENT_SIDE_ENCRYPTION_PART_SIZE] = str(multipart_context.part_size)

        self.encrypted_key = None
        self.plain_start = None

        return headers

    def get_key(self):
        plain_key, self.encrypted_key = self.__generate_data_key()
        return plain_key

    def decrypt_encrypted_key(self, encrypted_key):
        return self.__decrypt_data(encrypted_key)

    def decrypt_encrypted_start(self, encrypted_start):
        return self.__decrypt_data(encrypted_start)

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
