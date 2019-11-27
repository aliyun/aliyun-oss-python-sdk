import os
import oss2
import base64
import time
from oss2.compat import to_bytes
from oss2.models import AsyncFetchTaskConfiguration

# 以下代码展示了创建异步获取文件到bucket任务到API的用法

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

object_name = "test-async-object"
url = "<yourSrcObjectUrl>"
callback = '{"callbackUrl":"www.abc.com/callback","callbackBody":"${etag}"}'
base64_callback = oss2.utils.b64encode_as_string(to_bytes(callback))

# 可以选填host, callback, content_md5, ignore_same_key等参数
task_config = AsyncFetchTaskConfiguration(url, object_name, callback=base64_callback, ignore_same_key=False)

# 创建异步获取文件到bucket的任务
result = bucket.put_async_fetch_task(task_config)
task_id = result.task_id
print('task_id:', result.task_id)

time.sleep(5)

# 获取指定的异步任务信息
result = bucket.get_async_fetch_task(task_id)

# 打印获取到的异步任务信息
print('=====get result======')
print('task_id:', result.task_id)
print('state:', result.task_state)
print('error_msg:', result.error_msg)
task_config = result.task_config
print('task info:')
print('url:', task_config.url)
print('object_name:', task_config.object_name)
print('host:', task_config.host)
print('content_md5:', task_config.content_md5)
print('callback:', task_config.callback)
print('ignoreSameKey:', task_config.ignore_same_key)