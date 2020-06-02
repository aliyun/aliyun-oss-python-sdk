# -*- coding: utf-8 -*-

import os
import oss2
from oss2.models import ServerSideEncryptionRule
from oss2 import (SERVER_SIDE_ENCRYPTION_KMS, SERVER_SIDE_ENCRYPTION_AES256,
                  SERVER_SIDE_ENCRYPTION_SM4, KMS_DATA_ENCRYPTION_SM4)
from oss2.headers import (OSS_SERVER_SIDE_ENCRYPTION, OSS_SERVER_SIDE_ENCRYPTION_KEY_ID,
                          OSS_SERVER_SIDE_DATA_ENCRYPTION)
from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import PartInfo

# 以下代码展示了服务端加密设置的示例。

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

# ##########以下是设置bucket服务端加密的示例##############
# 以设置AES256加密为例。
rule = ServerSideEncryptionRule()
rule.sse_algorithm = SERVER_SIDE_ENCRYPTION_AES256
bucket.put_bucket_encryption(rule)

# 获取服务端加密配置。
result = bucket.get_bucket_encryption()
print('sse_algorithm:', result.sse_algorithm)
print('kms_key_id:', result.kms_master_keyid)
print('data_algorithm:', result.kms_data_encryption)

# ##########以下是使用put_object接口上传文件时单独指定文件的服务端加密方式的示例############
key = 'test_put_object'

# 在headers中指定加密方式。
headers = dict()
# 使用KMS加密
headers[OSS_SERVER_SIDE_ENCRYPTION] = SERVER_SIDE_ENCRYPTION_KMS
# 数据使用SM4算法
headers[OSS_SERVER_SIDE_DATA_ENCRYPTION] = KMS_DATA_ENCRYPTION_SM4

# 使用put_object接口上传文件时指定新的加密方式。
result = bucket.put_object(key, b'123', headers=headers)
sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
print('sse_algorithm:', sse_algo)
print('data_algorithm:', data_algo)
print('kms_key_id:', kms_key_id)

# 读取上传内容
object_stream = bucket.get_object(key)
print(object_stream.read())

# ##########以下是使用分片上传接口上传文件时单独指定文件的服务端加密方式的示例############
key = 'test-upload_file'
filename = '<yourLocalFile>'

total_size = os.path.getsize(filename)
# determine_part_size方法用来确定分片大小。
part_size = determine_part_size(total_size, preferred_size=100 * 1024)

# 在headers中指定加密方式
headers = dict()
# 使用OSS server端SM4加密算法
headers[OSS_SERVER_SIDE_ENCRYPTION] = SERVER_SIDE_ENCRYPTION_SM4

# 初始化分片时指定文件在服务端端加密类型
result = bucket.init_multipart_upload(key, headers=headers)
sse_algo = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION)
data_algo = result.headers.get(OSS_SERVER_SIDE_DATA_ENCRYPTION)
kms_key_id = result.headers.get(OSS_SERVER_SIDE_ENCRYPTION_KEY_ID)
print('sse_algorithm:', sse_algo)
print('data_algorithm:', data_algo)
print('kms_key_id:', kms_key_id)

upload_id = result.upload_id
parts = []

# 逐个上传分片。
with open(filename, 'rb') as fileobj:
    part_number = 1
    offset = 0
    while offset < total_size:
        num_to_upload = min(part_size, total_size - offset)
        # SizedFileAdapter(fileobj, size)方法会生成一个新的文件对象，重新计算起始追加位置。
        result = bucket.upload_part(key, upload_id, part_number,
                                    SizedFileAdapter(fileobj, num_to_upload))
        parts.append(PartInfo(part_number, result.etag))

        offset += num_to_upload
        part_number += 1

# 完成分片上传。
bucket.complete_multipart_upload(key, upload_id, parts)

# 验证分片上传。
with open(filename, 'rb') as fileobj:
    assert bucket.get_object(key).read() == fileobj.read()