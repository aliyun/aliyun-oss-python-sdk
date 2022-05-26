
import os
import oss2
from oss2.models import MetaQuery, AggregationsRequest

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

# open meta query
bucket.open_bucket_meta_query()

# Gets the meta query information of the specified storage space (bucket)
result = bucket.get_bucket_meta_query_status()
print("Print the status of the meta query: ", result.state)

# Query the files (objects) that meet the specified conditions, and list the file information according to the specified fields and sorting method.
aggregations1 = AggregationsRequest(field='Size', operation='sum')
aggregations2 = AggregationsRequest(field='Size', operation='max')
do_meta_query_request = MetaQuery(max_results=2, query='{"Field": "Size","Value": "1048576","Operation": "lt"}', sort='Size', order='asc', aggregations=[aggregations1, aggregations2])
result = bucket.do_bucket_meta_query(do_meta_query_request)

# Turn off the meta query of the storage space (bucket).
result = bucket.close_bucket_meta_query()