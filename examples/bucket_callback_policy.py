import base64
import os
import oss2
from oss2.models import CallbackPolicyInfo

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

# Set callback policy
callback_content = "{\"callbackUrl\":\"www.abc.com/callback\",\"callbackBody\":\"${etag}\"}"
callback_content2 = "{\"callbackUrl\":\"http://www.bbc.com/test\",\"callbackHost\":\"www.bbc.com\",\"callbackBody\":\"{\\\"mimeType\\\":${mimeType},\\\"size\\\":${size}}\"}"
callback_var_content2 = "{\"x:var1\":\"value1\",\"x:var2\":\"value2\"}"
callback = base64.b64encode(callback_content.encode(encoding='utf-8'))
callback2 = base64.b64encode(callback_content2.encode(encoding='utf-8'))
callback_var2 = base64.b64encode(callback_var_content2.encode(encoding='utf-8'))

callback_policy_1 = CallbackPolicyInfo('test_1', callback)
callback_policy_2 = CallbackPolicyInfo('test_2', callback2, callback_var2)
put_result = bucket.put_bucket_callback_policy([callback_policy_1, callback_policy_2])
print("Return put status: ", put_result.status)

# Get callback policy
get_result = bucket.get_bucket_callback_policy()
print("Return get status: ", get_result.status)
print("policy name: ", get_result.callback_policies[0].policy_name)
print("callback: ", get_result.callback_policies[0].callback)
print("policy name: ", get_result.callback_policies[1].policy_name)
print("callback: ", get_result.callback_policies[1].callback)
print("callback var: ", get_result.callback_policies[1].callback_var)

# Upload File Trigger Callback
bucket.put_object("test-key.txt", "aaa", headers={'x-oss-callback': base64.b64encode("{\"callbackPolicy\":\"test_2\"}".encode(encoding='utf-8'))})

# Delete callback policy
del_result = bucket.delete_bucket_callback_policy()
print("Return delete status: ", del_result.status)