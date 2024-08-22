import os
import time
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
access_point_name = os.getenv('OSS_TEST_ACCESS_POINT_NAME', '<yourAccessPointName>')


# Make sure that all parameters are correctly configured
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set parameters：' + param


# Create a bucket. You can use the bucket to call all object-related operations
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# Create a service. You can use the service to call all object-related operations
service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# Enables Block Public Access for Object Storage Service (OSS) resources.
result = service.put_public_access_block(True)
print(result.status)

# Sleep for a period of time and wait for status updates
time.sleep(3)

# Queries the Block Public Access configurations of Object Storage Service (OSS) resources.
result = service.get_public_access_block()
print(result.status)
print(result.block_public_access)

# Deletes the Block Public Access configurations of Object Storage Service (OSS) resources.
result = service.delete_public_access_block()
print(result.status)



# Enables Block Public Access for a bucket.
result = bucket.put_bucket_public_access_block(True)
print(result.status)

# Sleep for a period of time and wait for status updates
time.sleep(3)

# Queries the Block Public Access configurations of a bucket.
result = bucket.get_bucket_public_access_block()
print(result.status)
print(result.block_public_access)

# Deletes the Block Public Access configurations of a bucket.
result = bucket.delete_bucket_public_access_block()
print(result.status)



# Enables Block Public Access for an access point.
result = bucket.put_access_point_public_access_block(access_point_name, True)
print(result.status)

# Sleep for a period of time and wait for status updates
time.sleep(3)

# Queries the Block Public Access configurations of an access point.
result = bucket.get_access_point_public_access_block(access_point_name)
print(result.status)
print(result.block_public_access)

# Deletes the Block Public Access configurations of an access point.
result = bucket.delete_access_point_public_access_block(access_point_name)
print(result.status)

