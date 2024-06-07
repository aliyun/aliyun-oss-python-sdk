
import os
import oss2

# Specify access information, such as AccessKeyId, AccessKeySecret, and Endpoint.
# You can obtain access information from evironment variables or replace sample values in the code, such as <your AccessKeyId> with actual values.
#
# For example, if your bucket is located in the China (Hangzhou) region, you can set Endpoint to one of the following values:
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com

access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<yourAccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<yourAccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<yourBucketName>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<yourEndpoint>')


# Make sure that all parameters are correctly configured
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set parameters：' + param


# Create a bucket. You can use the bucket to call all object-related operations
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# put access point policy
accessPointName = 'example-ap'
user_id = '12836***64516515'
oss_region = "oss-cn-hangzhou"
policy="{\"Version\":\"1\",\"Statement\":[{\"Action\":[\"oss:PutObject\",\"oss:GetObject\"],\"Effect\":\"Deny\",\"Principal\":[\""+user_id+"\"],\"Resource\":[\"acs:oss:"+oss_region+":"+user_id+":accesspoint/"+accessPointName+"\",\"acs:oss:"+oss_region+":"+user_id+":accesspoint/"+accessPointName+"/object/*\"]}]}"
put_policy_result = bucket.put_access_point_policy(accessPointName, policy)
print("status: ", put_policy_result.status)

# get access point policy
get_policy_result = bucket.get_access_point_policy(accessPointName)
print("status: ", get_policy_result.status)
print("policy: ", get_policy_result.policy)

# delete access point policy
del_policy_result = bucket.delete_access_point_policy(accessPointName)
print("status: ", del_policy_result.status)

