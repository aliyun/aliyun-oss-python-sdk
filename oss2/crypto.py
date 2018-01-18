# -*- coding: utf-8 -*-

"""
oss2.encryption
~~~~~~~~~~~~~~

该模块包含了客户端加解密相关的函数和类。
"""
from . import utils
from .compat import to_string, to_bytes

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

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

        headers['x-oss-meta-oss-crypto-key'] = utils.b64encode_as_string(self.__encrypt_obj.encrypt(self.key))
        headers['x-oss-meta-oss-crypto-start'] = utils.b64encode_as_string(self.__encrypt_obj.encrypt(to_bytes(str(self.iv))))
        headers['x-oss-meta-oss-cek-alg'] = _AES_GCM

        return headers

    def get_key(self):
        self.key = utils.random_aes256_key()
        return self.key

    def get_iv(self):
        self.iv = utils.random_counter()
        return self.iv

    def get_oss_meta_data(self, headers, key):
        try:
            return self.__decrypt_obj.decrypt(utils.b64decode_from_string(headers[key]))
        except:
            return None
