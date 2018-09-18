# -*- coding: utf-8 -*-

import os
import sys
import tempfile

import oss2

# 以下代码展示了进度条功能的用法，包括上传进度条和下载进度条。


# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param

def percentage(consumed_bytes, total_bytes):
    """进度条回调函数，计算当前完成的百分比
    
    :param consumed_bytes: 已经上传/下载的数据量
    :param total_bytes: 总数据量
    """
    if total_bytes:
        rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
        print('\r{0}% '.format(rate))
        sys.stdout.flush()

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
流式上传
"""
# 带有进度条的覆盖上传
bucket.put_object(key, content, progress_callback=percentage)

# 删除上传的文件
bucket.delete_object(key)

"""
追加上传
"""
# 带有进度条的追加上传，每一次追加一个进度条
# 创建可追加文件，首次偏移（position）设为0
result = bucket.append_object(key, 0, content, progress_callback=percentage)
# 追加一行数据，偏移可以从上次响应中获得
# 当然，也可以通过head_object()获得当前长度作为偏移，只是比较低效
bucket.append_object(key, result.next_position, content, progress_callback=percentage)

# 删除上传的文件
bucket.delete_object(key)

"""
分片上传
"""
# 带有进度条的分片上传，每个分片上传一个进度条
parts = []
upload_id = bucket.init_multipart_upload(key).upload_id

# 上传分片
for i in range(3):
    result = bucket.upload_part(key, upload_id, i+1, content, progress_callback=percentage)
    parts.append(oss2.models.PartInfo(i+1, result.etag, size = len(content), part_crc = result.crc))

# 完成上传并回调
result = bucket.complete_multipart_upload(key, upload_id, parts)

"""
断点续传上传
"""
# 带进度条的断点续传
pathname = _prepare_temp_file(content)
oss2.resumable_upload(bucket, key, pathname, 
                      multipart_threshold=200*1024,
                      part_size=100*1024,
                      num_threads=3,
                      progress_callback=percentage)

"""
文件下载
"""
# 带进度条的下载
result = bucket.get_object(key, progress_callback=percentage)
content_got = b''
for chunk in result:
    content_got += chunk
assert content == content_got

"""
范围下载
"""
# 带进度条的范围下载
result = bucket.get_object(key, byte_range=(1024, 2047), progress_callback=percentage)
content_got = b''
for chunk in result:
    content_got += chunk
assert 'a'*1024 == content_got

"""
断点续传下载 
"""
# 带进度条的断点续传下载 
filename = 'download.txt'
oss2.resumable_download(bucket, key, filename,
                        multiget_threshold=200*1024,
                        part_size=100*1024,
                        num_threads=3,
                        progress_callback=percentage) 
os.remove(filename)

# 删除上传的文件
bucket.delete_object(key)
