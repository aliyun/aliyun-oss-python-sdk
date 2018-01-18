# -*- coding: utf-8 -*-

import os

import oss2
from oss2.crypto import LocalRsaProvider

# 以下代码展示了客户端文件加密上传下载的用法，如下载文件、上传文件等，注意在客户端加密的条件下，oss暂不支持文件分片上传下载操作。


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

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

key = 'motto.txt'
content = b'a' * 1024 * 1024
filename = 'download.txt'


# 创建Bucket对象，可以进行客户端数据加密，此模式下只提供对象整体上传下载操作
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name, crypto_provider=LocalRsaProvider())

key1 = 'motto-copy.txt'

# 上传文件
bucket.put_object(key, content, headers={'content-length': str(1024 * 1024)})

# 复制文件
bucket.copy_object(bucket_name, key, key1)

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

# 复制文件
result = bucket.get_object(key1)

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

# 下载复制文件到本地文件
result = bucket.get_object_to_file(key1, filename)

# 验证一下
with open(filename, 'rb') as fileobj:
    assert fileobj.read() == content

os.remove(filename)