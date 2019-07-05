# -*- coding: utf-8 -*-

import os
import oss2
from oss2.headers import OSS_REQUEST_PAYER

# 以下代码展示了第三方付费请求object的示例
# 在此之前需要Bucket的拥有者给第三方请授权，并开启请求者付费模式。

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

object_name = 'test-request-object'

# header中指定请求者付费
headers = dict()
headers[OSS_REQUEST_PAYER] = "requester"

# 上传文件, 需要指定header
result = bucket.put_object(object_name, 'test-content', headers=headers)
print('http response status: ', result.status)

# 删除文件, 需要指定header.
result = bucket.delete_object(object_name, headers=headers);
print('http response status: ', result.status)