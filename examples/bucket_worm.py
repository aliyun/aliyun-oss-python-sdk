
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

# 新建合规保留策略，并指定Object保护天数为1天。
result = bucket.init_bucket_worm(1)
# 查看合规保留策略ID。
print(result.worm_id)

# 锁定合规保留策略。
bucket.complete_bucket_worm('<yourWromId>')

# 获取合规保留策略。
result = bucket.get_bucket_worm()

# 查看合规保留策略ID。
print(result.worm_id)
# 查看合规保留策略状态。未锁定状态下为"InProgress"，锁定状态下为"Locked"。
print(result.state)
# 查看Object的保护时间。
print(result.retention_period_days)
# 查看合规保留策略创建时间。
print(result.creation_date)

# 取消未锁定的合规保留策略。
bucket.abort_bucket_worm()

# 延长已锁定的合规保留策略中Object的保留天数。
bucket.extend_bucket_worm('<yourWormId>', 2)