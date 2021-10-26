
import os
import oss2
import time

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

object_name = '<yourObjectName>'

# 以下代码用于将Object的存储类型从标准或低频访问转换为归档类型
# 添加存储类型header，此处以更改文件存储类型为归档类型为例。
headers = {'x-oss-storage-class': oss2.BUCKET_STORAGE_CLASS_ARCHIVE}

# 更改文件存储类型。
bucket.copy_object(bucket.bucket_name, object_name, object_name, headers)

# 以下代码用于将Object的存储类型从归档转换为低频访问类型
# 获取文件元信息。
meta = bucket.head_object(object_name)

# 查看文件存储类型是否为归档类型。如果是，则需要先解冻才能修改文件存储类型。解冻时间预计1分钟。
if meta.resp.headers['x-oss-storage-class'] == oss2.BUCKET_STORAGE_CLASS_ARCHIVE:
    bucket.restore_object(object_name)
    while True:
        meta = bucket.head_object(object_name)
        if meta.resp.headers['x-oss-restore'] == 'ongoing-request="true"':
            time.sleep(5)
        else:
            break

# 添加存储类型header，此处以更改文件存储类型为低频访问类型为例。
headers = {'x-oss-storage-class': oss2.BUCKET_STORAGE_CLASS_IA}

# 更改文件存储类型。
bucket.copy_object(bucket.bucket_name, object_name, object_name, headers)