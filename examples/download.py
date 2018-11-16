# -*- coding: utf-8 -*-

import os

import oss2


# 以下代码展示了文件下载的用法，如下载文件、范围下载、断点续传下载等。


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
content = oss2.to_bytes('a' * 1024 * 1024)
filename = 'download.txt'

# 上传文件
bucket.put_object(key, content, headers={'content-length': str(1024 * 1024)})

"""
文件下载
"""

# 下载文件
result = bucket.get_object(key)

# 验证一下
content_got = b''
for chunk in result:
    content_got += chunk
assert content_got == content

# 下载到本地文件
result = bucket.get_object_to_file(key, filename)

# 验证一下
with open(filename, 'rb') as fileobj:
    assert fileobj.read() == content

"""
范围下载
"""

# 范围下载，如果指定的范围无效，则下载整个文件
result = bucket.get_object(key, byte_range=(0, 1023))

# 验证一下
content_got = b''
for chunk in result:
    content_got += chunk
assert content_got == oss2.to_bytes('a'*1024)


# 范围下载到本地文件
result = bucket.get_object_to_file(key, filename, byte_range=(1024, 2047))

# 验证一下
with open(filename, 'rb') as fileobj:
    assert fileobj.read() == oss2.to_bytes('a'*1024)


"""
断点续传下载
"""

# 断点续传下载
oss2.resumable_download(bucket, key, filename,
                        multiget_threshold=200*1024,
                        part_size=100*1024,
                        num_threads=3)

# 验证一下
with open(filename, 'rb') as fileobj:
    assert fileobj.read() == content

# 清理文件
os.remove(filename)
