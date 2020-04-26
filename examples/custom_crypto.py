# -*- coding: utf-8 -*-

import os

import oss2
from oss2.crypto import BaseCryptoProvider
from oss2.utils import b64encode_as_string, b64decode_from_string, to_bytes
from oss2.headers import *

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from requests.structures import CaseInsensitiveDict

# 以下代码展示了用户自行提供加密算法进行客户端文件加密上传下载的用法，如下载文件、上传文件等，
# 注意在客户端加密的条件下，oss暂不支持文件分片上传下载操作。
# 本例提供了本地非对称加密密钥的加密器CustomCryptoProvider 和用于数据对称加密的FakeCrypto

# 自定义CryptoProvider

class FakeCrypto:
    """FakeCrypto 加密实现，用户自行提供的一种对称加密算法。
        :param str key: 对称加密数据密钥
        :param str start: 对称加密初始随机值
    .. note::
        用户可自行实现对称加密算法，需服务如下规则：
        1、提供对称加密算法名，ALGORITHM
        2、提供静态方法，返回加密密钥和初始随机值（若算法不需要初始随机值，也需要提供），类型为
        3、提供加密解密方法
    """
    ALGORITHM = "userdefine"

    @staticmethod
    def get_key():
        return 'fake_key'

    @staticmethod
    def get_iv():
        return 'fake_start'

    def __init__(self, key=None, start=None, count=None):
        pass

    def encrypt(self, raw):
        return raw

    def decrypt(self, enc):
        return enc


class FakeAsymmetric:
    def __int__(self):
        pass

    def get_public_key(self):
        return

    def get_private_key(self):
        return

    def encrypt(self, data):
        return data

    def decrypt(self, data):
        return data

class CustomCryptoProvider(BaseCryptoProvider):
    """使用本地自定义FakeAsymmetric加密数据密钥。数据使用公钥加密，私钥解密
        :param class cipher: 数据加密，FakeCrypto
    """

    def __init__(self, cipher=FakeCrypto):
        super(CustomCryptoProvider, self).__init__(cipher=cipher)

        self.public_key = FakeAsymmetric()
        self.private_key = self.public_key


    def build_header(self, headers=None, multipart_context=None):
        if not isinstance(headers, CaseInsensitiveDict):
            headers = CaseInsensitiveDict(headers)

        if 'content-md5' in headers:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_UNENCRYPTED_CONTENT_MD5] = headers['content-md5']
            del headers['content-md5']

        if 'content-length' in headers:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_UNENCRYPTED_CONTENT_LENGTH] = headers['content-length']
            del headers['content-length']

        headers[OSS_CLIENT_SIDE_ENCRYPTION_KEY] = b64encode_as_string(self.public_key.encrypt(self.plain_key))
        headers[OSS_CLIENT_SIDE_ENCRYPTION_START] = b64encode_as_string(self.public_key.encrypt(to_bytes(str(self.plain_iv))))
        headers[OSS_CLIENT_SIDE_ENCRYPTION_CEK_ALG] = self.cipher.ALGORITHM
        headers[OSS_CLIENT_SIDE_ENCRYPTION_WRAP_ALG] = 'custom'

        # multipart file build header
        if multipart_context:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_DATA_SIZE] = str(multipart_context.data_size)
            headers[OSS_CLIENT_SIDE_ENCRYPTION_PART_SIZE] = str(multipart_context.part_size)

        self.plain_key = None
        self.plain_iv = None

        return headers

    def build_header_for_upload_part(self, headers=None):
        if not isinstance(headers, CaseInsensitiveDict):
            headers = CaseInsensitiveDict(headers)

        if 'content-md5' in headers:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_UNENCRYPTED_CONTENT_MD5] = headers['content-md5']
            del headers['content-md5']

        if 'content-length' in headers:
            headers[OSS_CLIENT_SIDE_ENCRYPTION_UNENCRYPTED_CONTENT_LENGTH] = headers['content-length']
            del headers['content-length']

        self.plain_key = None
        self.plain_iv = None

        return headers

    def get_key(self):
        self.plain_key = self.cipher.get_key()
        return self.plain_key

    def get_iv(self):
        self.plain_iv = self.cipher.get_iv()
        return self.plain_iv

    def decrypt_oss_meta_data(self, headers, key, conv=lambda x:x):
        try:
            return conv(self.private_key.decrypt(b64decode_from_string(headers[key])))
        except:
            return None

    def decrypt_from_str(self, key, value, conv=lambda x:x):
        try:
            return conv(self.private_key.decrypt(b64decode_from_string(value)))
        except:
            return None



# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
#
# 以杭州区域为例，Endpoint可以是：
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com
# 分别以HTTP、HTTPS协议访问。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')

# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param

key = 'motto.txt'
content = b'a' * 1024 * 1024
filename = 'download.txt'


# 创建Bucket对象，可以进行客户端数据加密(用户端RSA)，此模式下只提供对象整体上传下载操作
bucket = oss2.CryptoBucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name, crypto_provider=CustomCryptoProvider())

key1 = 'motto-copy.txt'

# 上传文件
bucket.put_object(key, content, headers={'content-length': str(1024 * 1024)})

"""
文件下载
"""

# 下载文件
# 原文件
result = bucket.get_object(key)

# 验证一下
content_got = b''
for chunk in result:
    content_got += chunk
assert content_got == content

# 下载原文件到本地文件
result = bucket.get_object_to_file(key, filename)

# 验证一下
with open(filename, 'rb') as fileobj:
    assert fileobj.read() == content

os.remove(filename)

"""
分片上传
"""
# 初始化上传分片
part_a = b'a' * 1024 * 100
part_b = b'b' * 1024 * 100
part_c = b'c' * 1024 * 100
multi_content = [part_a, part_b, part_c]

parts = []
data_size = 100 * 1024 * 3
part_size = 100 * 1024
multi_key = "test_crypto_multipart"

res = bucket.init_multipart_upload(multi_key, data_size, part_size)
upload_id = res.upload_id
crypto_multipart_context = res.crypto_multipart_context

# 分片上传
for i in range(3):
    result = bucket.upload_part(multi_key, upload_id, i+1, multi_content[i], crypto_multipart_context)
    parts.append(oss2.models.PartInfo(i+1, result.etag, size = part_size, part_crc = result.crc))

## 分片上传时，若意外中断丢失crypto_multipart_context, 利用list_parts找回。
#for i in range(2):
#    result = bucket.upload_part(multi_key, upload_id, i+1, multi_content[i], crypto_multipart_context)
#    parts.append(oss2.models.PartInfo(i+1, result.etag, size = part_size, part_crc = result.crc))
#
#res = bucket.list_parts(multi_key, upload_id)
#crypto_multipart_context_new = res.crypto_multipart_context
#
#result = bucket.upload_part(multi_key, upload_id, 3, multi_content[2], crypto_multipart_context_new)
#parts.append(oss2.models.PartInfo(3, result.etag, size = part_size, part_crc = result.crc))

# 完成上传
result = bucket.complete_multipart_upload(multi_key, upload_id, parts)

# 下载全部文件
result =  bucket.get_object(multi_key)

# 验证一下
content_got = b''
for chunk in result:
    content_got += chunk
assert content_got[0:102400] == part_a
assert content_got[102400:204800] == part_b
assert content_got[204800:307200] == part_c
