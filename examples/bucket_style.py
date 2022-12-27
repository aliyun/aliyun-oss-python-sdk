
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

# Call the PutStyle interface to add a new picture style.
result = bucket.put_bucket_style('imagestyle','image/resize,w_200')
print(result.status)

# Call the GetStyle interface to query the image style information specified in a bucket.
get_result = bucket.get_bucket_style('imagestyle')
print(get_result.name)
print(get_result.content)

# Call the ListStyle interface to query all the image styles created in a bucket.
list_result = bucket.list_bucket_style()
print(list_result.styles[0].name)
print(list_result.styles[0].content)


# Call DeleteStyle to delete the specified picture style in a bucket.
del_result = bucket.delete_bucket_style('imagestyle')
print(del_result.status)
