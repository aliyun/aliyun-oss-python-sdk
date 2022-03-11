
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

# Create the retention policy and set the retention period to 1 days.
result = bucket.init_bucket_worm(1)
# Query the ID of the retention policy.
print(result.worm_id)

# Lock the retention policy.
bucket.complete_bucket_worm('<yourWormId>')

# Query the retention policy.
result = bucket.get_bucket_worm()

# Query the ID of the retention policy.
print(result.worm_id)
# Query the status of the retention policy. InProgress indicates that the retention policy is not locked. Locked indicates that the retention policy is locked.
print(result.state)
# Query the retention period of the retention policy.
print(result.retention_period_days)
# Query the created time of the retention policy.
print(result.creation_date)

# Cancel the unlocked retention policy.
bucket.abort_bucket_worm()

# Extend the retention period of the locked retention policy.
bucket.extend_bucket_worm('<yourWormId>', 2)