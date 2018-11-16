# -*- coding: utf-8 -*-

import base64
import hashlib
import os
import tempfile

import oss2

# 以下代码展示了上传/下载时数据校验的用法。

# OSS支持MD5、CRC64两种数据校验。MD5校验，需要用户计算出上传内容的MD5值，并放到header的`Content-MD5`中。
# CRC64校验，上传时自动完成校验，下载时需要用户校验。OSS Python SDK默认代开CRC64校验。

# 注意：断点续传上传不支持MD5，断点续传下载不支持CRC64，其它上传/下载都支持MD5和CRC64校验。

# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param


def calculate_file_md5(file_name, block_size=64 * 1024):
    """计算文件的MD5
    :param file_name: 文件名
    :param block_size: 计算MD5的数据块大小，默认64KB
    :return 文件内容的MD5值
    """
    with open(file_name, 'rb') as f:
        md5 = hashlib.md5()
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
            
    return base64.b64encode(md5.digest())

def calculate_data_md5(data):
    """计算数据的MD5
    :param data: 数据
    :return MD5值
    """
    md5 = hashlib.md5()
    md5.update(data)
    return base64.b64encode(md5.digest())


def calculate_file_crc64(file_name, block_size=64 * 1024, init_crc=0):
    """计算文件的MD5
    :param file_name: 文件名
    :param block_size: 计算MD5的数据块大小，默认64KB
    :return 文件内容的MD5值
    """
    with open(file_name, 'rb') as f:
        crc64 = oss2.utils.Crc64(init_crc)
        while True:
            data = f.read(block_size)
            if not data:
                break
            crc64.update(data)
            
    return crc64.crc

def _prepare_temp_file(content):
    """创建临时文件
    :param content: 文件内容
    :return 文件名
    """
    fd, pathname = tempfile.mkstemp(suffix='exam-progress-')
    os.write(fd, content)
    os.close(fd)
    return pathname

key = 'story.txt'
content = 'a' * 1024 * 1024

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

"""
MD5校验
"""

# 上传数据
encode_md5 = calculate_data_md5(content)
bucket.put_object(key, content, headers={'Content-MD5': encode_md5})


# 上传文件
file_name = _prepare_temp_file(content)
encode_md5 = calculate_file_md5(file_name)
bucket.put_object_from_file(key, file_name, headers={'Content-MD5': encode_md5})

# 删除上传的文件
bucket.delete_object(key)


# 追加上传
# 第一次上传位置为0
encode_md5 = calculate_data_md5(content)
result = bucket.append_object(key, 0, content, headers={'Content-MD5': encode_md5})
# 第二次上传位置从result获取
bucket.append_object(key, result.next_position, content, headers={'Content-MD5': encode_md5})

# 删除上传的文件
bucket.delete_object(key)


# 分片上传
parts = []
upload_id = bucket.init_multipart_upload(key).upload_id
 
# 上传分片，每个分片单独MD5校验
encode_md5 = calculate_data_md5(content)
for i in range(3):
    result = bucket.upload_part(key, upload_id, i+1, content, headers={'Content-MD5': encode_md5})
    parts.append(oss2.models.PartInfo(i+1, result.etag, size = len(content), part_crc = result.crc))

# 完成上传并回调
result = bucket.complete_multipart_upload(key, upload_id, parts)


"""
CRC64校验
"""
# CRC校验默认打开。关闭CRC校验方法如下，oss2.Bucket(auth, endpoint, bucket_name, enable_crc=False)

# 上传数据，默认自动开启CRC校验
bucket.put_object(key, content)

# 删除上传的文件
bucket.delete_object(key)


# 追加上传，必须指定init_crc才会开启CRC校验
result = bucket.append_object(key, 0, content, init_crc=0)
# 第二次上传位置及init_crc从result获取
bucket.append_object(key, result.next_position, content, init_crc=result.crc)

# 删除上传的文件
bucket.delete_object(key)


# 分片上传，默认自动开启CRC校验
parts = []
upload_id = bucket.init_multipart_upload(key).upload_id
 
# 上传分片，每个分片单独CRC校验
for i in range(3):
    result = bucket.upload_part(key, upload_id, i+1, content)
    parts.append(oss2.models.PartInfo(i+1, result.etag, size = len(content), part_crc = result.crc))

# 完成上传并回调
result = bucket.complete_multipart_upload(key, upload_id, parts)


# 断点续传上传，默认自动开启CRC校验
pathname = _prepare_temp_file(content)
oss2.resumable_upload(bucket, key, pathname, 
                      multipart_threshold=200*1024,
                      part_size=100*1024,
                      num_threads=3)


# 下载文件
result = bucket.get_object(key)
content_got = b''
for chunk in result:
    content_got += chunk
assert result.client_crc == result.server_crc


# 下载文件到本地,默认开启CRC校验
local_file = 'download.txt'
result = bucket.get_object_to_file(key, local_file)
os.remove(local_file)
assert result.client_crc == result.server_crc


# 断点续传下载, 自动开启CRC校验，也可以用如下方法校验
oss2.resumable_download(bucket, key, local_file,
                        multiget_threshold=200*1024,
                        part_size=100*1024,
                        num_threads=3)

crc64 = calculate_file_crc64(local_file)
os.remove(local_file)

result = bucket.head_object(key)

assert str(crc64) == result.headers['x-oss-hash-crc64ecma']
