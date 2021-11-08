
import os
import oss2
from oss2.models import Tagging, TaggingRule

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

# Add a tag to a bucket
# Creates a tagging rule.
rule = TaggingRule()
rule.add('key1', 'value1')
rule.add('key2', 'value2')

# Creates a tag.
tagging = Tagging(rule)
# Adds the tag to the bucket.
result = bucket.put_bucket_tagging(tagging)
# Checks the returned HTTP status code.
print('http status:', result.status)


# Obtain the tags added to a bucket
result = bucket.get_bucket_tagging()
# Views the obtained tagging rule.
tag_rule = result.tag_set.tagging_rule
print('tag rule:', tag_rule)

# Deletes the tags added to the bucket.
result = bucket.delete_bucket_tagging()
# Checks the returned HTTP status code.
print('http status:', result.status)