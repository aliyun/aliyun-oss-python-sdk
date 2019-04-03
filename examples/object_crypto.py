# -*- coding: utf-8 -*-

import os

import oss2
from oss2.crypto import LocalRsaProvider, AliKMSProvider

# 以下代码展示了客户端文件加密上传下载的用法，如下载文件、上传文件等。


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
cmk = os.getenv('OSS_TEST_CMK', '<你的CMK>')
region = os.getenv('OSS_TEST_REGION', '<你的区域>')

# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint, cmk, region):
    assert '<' not in param, '请设置参数：' + param

key = 'motto.txt'
content = b'a' * 1024 * 1024
filename = 'download.txt'

# 创建Bucket对象，可以进行客户端数据加密(用户端RSA)
bucket = oss2.CryptoBucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name, crypto_provider=LocalRsaProvider())


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

# 下载部分文件
result = bucket.get_object(key, byte_range=(32,1024))

#验证一下
content_got = b''
for chunk in result:
    content_got +=chunk
assert content_got == content[32:1025]


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
crypto_multipart_context = res.crypto_multipart_context;

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

# 创建Bucket对象，可以进行客户端数据加密(使用阿里云KMS)
bucket = oss2.CryptoBucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name,
                           crypto_provider=AliKMSProvider(access_key_id, access_key_secret, region, cmk))

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

# 下载部分文件
result = bucket.get_object(key, byte_range=(32,1024))

#验证一下
content_got = b''
for chunk in result:
    content_got +=chunk
assert content_got == content[32:1025]

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
crypto_multipart_context = res.crypto_multipart_context;

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
