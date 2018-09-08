# -*- coding: utf-8 -*-

import os
import random
import string
import oss2


# 以下代码展示了文件上传的高级用法，如断点续传、分片上传等。
# 基本的文件上传如上传普通文件、追加文件，请参见object_basic.py


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


def random_string(n):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(n))

# 生成一个本地文件用于测试。文件内容是bytes类型。
filename = random_string(32) + '.txt'
content = oss2.to_bytes(random_string(1024 * 1024))

with open(filename, 'wb') as fileobj:
    fileobj.write(content)


"""
断点续传上传
"""

# 断点续传一：因为文件比较小（小于oss2.defaults.multipart_threshold），
# 所以实际上用的是oss2.Bucket.put_object
oss2.resumable_upload(bucket, 'remote-normal.txt', filename)

# 断点续传二：为了展示的需要，我们指定multipart_threshold可选参数，确保使用分片上传
oss2.resumable_upload(bucket, 'remote-multipart.txt', filename, multipart_threshold=100 * 1024)


"""
分片上传
"""

# 也可以直接调用分片上传接口。
# 首先可以用帮助函数设定分片大小，设我们期望的分片大小为128KB
total_size = os.path.getsize(filename)
part_size = oss2.determine_part_size(total_size, preferred_size=128 * 1024)

# 初始化分片上传，得到Upload ID。接下来的接口都要用到这个Upload ID。
key = 'remote-multipart2.txt'
upload_id = bucket.init_multipart_upload(key).upload_id

# 逐个上传分片
# 其中oss2.SizedFileAdapter()把fileobj转换为一个新的文件对象，新的文件对象可读的长度等于size_to_upload
with open(filename, 'rb') as fileobj:
    parts = []
    part_number = 1
    offset = 0
    while offset < total_size:
        size_to_upload = min(part_size, total_size - offset)
        result = bucket.upload_part(key, upload_id, part_number,
                                    oss2.SizedFileAdapter(fileobj, size_to_upload))
        parts.append(oss2.models.PartInfo(part_number, result.etag, size = size_to_upload, part_crc = result.crc))

        offset += size_to_upload
        part_number += 1

    # 完成分片上传
    bucket.complete_multipart_upload(key, upload_id, parts)

# 验证一下
with open(filename, 'rb') as fileobj:
    assert bucket.get_object(key).read() == fileobj.read()


os.remove(filename)
