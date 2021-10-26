
import os
import oss2
from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import PartInfo

# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
#
# 以杭州区域为例，Endpoint可以是：
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com


access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param


# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# 简单上传时禁止覆盖同名文件
# 上传文件。
# 指定PutObject操作时是否覆盖同名Object。
# 不指定x-oss-forbid-overwrite时，默认覆盖同名Object。
# 指定x-oss-forbid-overwrite为false时，表示允许覆盖同名Object。
# 指定x-oss-forbid-overwrite为true时，表示禁止覆盖同名Object，如果同名Object已存在，程序将报错。
headers = dict()
headers["x-oss-forbid-overwrite"] = "true"
result = bucket.put_object('<yourObjectName>', 'content of object', headers=headers)

# HTTP返回码。
print('http status: {0}'.format(result.status))
# 请求ID。请求ID是请求的唯一标识，强烈建议在程序日志中添加此参数。
print('request_id: {0}'.format(result.request_id))
# ETag是put_object方法返回值特有的属性。
print('ETag: {0}'.format(result.etag))
# HTTP响应头部。
print('date: {0}'.format(result.headers['date']))

# 拷贝小文件时禁止覆盖同名文件
# 指定copy_object操作时是否覆盖同名Object。
# 不指定x-oss-forbid-overwrite时，默认覆盖同名Object。
# 指定x-oss-forbid-overwrite为false时，表示允许覆盖同名Object。
# 指定x-oss-forbid-overwrite为true时，表示禁止覆盖同名Object，如果同名Object已存在，程序将报错。
headers = dict()
headers["x-oss-forbid-overwrite"] = "true"
bucket.copy_object('<yourSourceBucketName>', '<yourSourceObjectName>', '<yourDestinationObjectName>', headers=headers)

# 分片上传时禁止覆盖同名文件
key = '<yourObjectName>'
filename = '<yourLocalFile>'

total_size = os.path.getsize(filename)
# determine_part_size方法用来确定分片大小。
part_size = determine_part_size(total_size, preferred_size=100 * 1024)

# 初始化分片。
# 指定分片上传操作时是否覆盖同名Object。
# 不指定x-oss-forbid-overwrite时，默认覆盖同名Object。
# 指定x-oss-forbid-overwrite为false时，表示允许覆盖同名Object。
# 指定x-oss-forbid-overwrite为true时，表示禁止覆盖同名Object，如果同名Object已存在，程序将报错。
headers["x-oss-forbid-overwrite"] = "true"
upload_id = bucket.init_multipart_upload(key, headers=headers).upload_id
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
# 指定分片上传操作时是否覆盖同名Object。
# 不指定x-oss-forbid-overwrite时，默认覆盖同名Object。
# 指定x-oss-forbid-overwrite为false时，表示允许覆盖同名Object。
# 指定x-oss-forbid-overwrite为true时，表示禁止覆盖同名Object，如果同名Object已存在，程序将报错。
headers["x-oss-forbid-overwrite"] = "true"
bucket.complete_multipart_upload(key, upload_id, parts, headers=headers)

# 验证分片上传。
with open(filename, 'rb') as fileobj:
    assert bucket.get_object(key).read() == fileobj.read()