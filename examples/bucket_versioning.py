
import os
import oss2
from oss2.models import BucketVersioningConfig

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

# Initialize the versioning configurations for the bucket.
config = BucketVersioningConfig()
# Set the versioning state to Enabled or Suspended.
config.status = oss2.BUCKET_VERSIONING_ENABLE

# Configure versioning for the bucket.
result = bucket.put_bucket_versioning(config)
# View the HTTP status code.
print('http response code:', result.status)


# Obtain the versioning state of the bucket.
versioning_info = bucket.get_bucket_versioning()
# View the versioning state of the bucket. If versioning has been enabled, Enabled or Suspended is returned. If versioning has not been enabled, None is returned.
print('bucket versioning status:', versioning_info.status)