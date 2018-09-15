# -*- coding: utf-8 -*-

import os
import shutil

import oss2
from oss2.headers import RequestHeader


# 以下代码展示了其用服务端加密功能的各项操作


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


key = 'server-crypto.txt'
content = b'a' * 1024 * 1024

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)


# 上传文件使用服务端AES256进行加密
myHeader = RequestHeader()
myHeader.set_server_side_encryption("AES256")
bucket.put_object(key, content, headers = myHeader)

# 下载文件验证一下
result = bucket.get_object(key)
content_got = b''
for chunk in result:
    content_got += chunk
assert content_got == content

# 上传文件使用服务端KMS进行加密
myHeader = RequestHeader()
myHeader.set_server_side_encryption("KMS", cmk_id = "11111")
bucket.put_object(key, content, headers = myHeader)

# 下载文件验证一下
result = bucket.get_object(key)
content_got = b''
for chunk in result:
    content_got += chunk
assert content_got == content
