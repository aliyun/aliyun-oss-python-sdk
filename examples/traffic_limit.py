# -*- coding: utf-8 -*-

import os
import oss2
from oss2.models import OSS_TRAFFIC_LIMIT

# 以下代码展示了限速上传下载文件的设置方法

# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你要请求的Bucket名称>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')

# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

OBJECT_SIZE_1MB = (1 * 1024 * 1024)
LIMIT_100KB = (100 * 1024 * 8)

headers = dict()
headers[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);

key = 'traffic-limit-test-put-object'
content = b'a' * OBJECT_SIZE_1MB

# 限速上传文件
result = bucket.put_object(key, content, headers=headers)
print('http response status:', result.status)

# 限速下载文件到本地
file_name = key + '.txt'
result = bucket.get_object_to_file(key, file_name, headers=headers)
print('http response status:', result.status)

os.remove(file_name)
bucket.delete_object(key)

# 使用签名url方式限速上传文件
params = dict()
params[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);
local_file_name = "example.jpg"

# 创建限速上传文件的签名url, 有效期60s
url = bucket.sign_url('PUT', key, 60, params=params)
# 限速上传
result = bucket.put_object_with_url_from_file(url, local_file_name)
print('http response status:', result.status)

# 创建限速下载文件的签名url, 有效期60s
down_file_name = key + '.tmp'
url = bucket.sign_url('GET', key, 60, params=params)
# 限速下载
result = bucket.get_object_with_url_to_file(url, down_file_name)
print('http response status:', result.status)

os.remove(down_file_name)
bucket.delete_object(key)