
import os
import oss2

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

# 设置Bucket的传输加速状态。
# 当设置enabled为true时，表示开启传输加速；当设置enabled为false时，表示关闭传输加速。
enabled = 'true'
bucket.put_bucket_transfer_acceleration(enabled)

# 查询Bucket的传输加速状态。
# 如果返回值为true，则Bucket已开启传输加速功能；如果返回值为false，则Bucket的传输加速功能为关闭状态。
result = bucket.get_bucket_transfer_acceleration()
enabled_text = result.enabled
print("Returns whether to enable transfer acceleration: ", enabled_text)
