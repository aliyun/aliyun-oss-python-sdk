
import os
import oss2
import json

# 以下代码展示了bucket_policy相关API的用法，
# 具体policy书写规则参考官网文档说明

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

# 创建policy_text
policy=dict()
policy["Version"] = "1"
policy["Statement"] = []
statement = dict()
statement["Action"] = ["oss:PutObject"]
statement["Effect"] = "Allow"
statement["Resource"] = ["acs:oss:*:*:*/*"]
policy["Statement"].append(statement)
policy_text = json.dumps(policy)

# Put bolicy_text
print("Put policy text : ", policy_text)
bucket.put_bucket_policy(policy_text)

# Get bucket Policy
result = bucket.get_bucket_policy()
policy_json = json.loads(result.policy) 
print("Get policy text: ", policy_json)

# 校验返回的policy
assert len(policy["Statement"]) == len(policy_json["Statement"])
assert policy["Version"] == policy_json["Version"]
policy_resource = policy["Statement"][0]["Resource"][0]
policy_json_resource = policy_json["Statement"][0]["Resource"][0]
assert policy_resource == policy_json_resource

# 删除policy
result = bucket.delete_bucket_policy()
assert int(result.status)//100 == 2