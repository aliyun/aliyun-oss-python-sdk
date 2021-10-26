
import os
import oss2
from oss2.models import BucketVersioningConfig

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

# 创建bucket版本控制配置。
config = BucketVersioningConfig()
# 状态配置为Enabled或Suspended。
config.status = oss2.BUCKET_VERSIONING_ENABLE

# 设置bucket版本控制状态。
result = bucket.put_bucket_versioning(config)
# 查看http返回码。
print('http response code:', result.status)


# 获取bucket版本控制状态信息。
versioning_info = bucket.get_bucket_versioning()
# 查看bucket版本控制状态, 如果曾开启过版本控制则返回Enabled或Suspended, 如果从未开启过版本控制则返回None。
print('bucket versioning status:', versioning_info.status)