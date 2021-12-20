
import os
import oss2
from oss2.models import ReplicationRule

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

# Specify the replication rule ID, the name of the destination bucket, the region in which the destination bucket is located, and whether to synchronize historical data.
# If you do not set the rule_id parameter or you leave the rule_id parameter empty, OSS generates a unique value for this replication rule.
# If the destination bucket is located in the China (Beijing) region, set target_bucket_location to oss-cn-beijing.
# By default, OSS synchronizes historical data. If you set is_enable_historical_object_replication to false, historical data is not synchronized.
replica_config = ReplicationRule(rule_id='test_replication_1',
                                 target_bucket_name='dstexamplebucket',
                                 target_bucket_location='oss-cn-beijing',
                                 is_enable_historical_object_replication=False
                                 )
# Enable CRR for the source bucket.
bucket.put_bucket_replication(replica_config)

# Query the CRR configurations of a bucket
result = bucket.get_bucket_replication()
# Display the returned information.
for rule in result.rule_list:
    print(rule.rule_id)
    print(rule.target_bucket_name)
    print(rule.target_bucket_location)

# Query the progress of the CRR task that is performed on the bucket.
# Specify the replication rule ID. Example: test_replication_1.
result = bucket.get_bucket_replication_progress('test_replication_1')
print(result.progress.rule_id)
# Check whether CRR is enabled for historical data in the bucket.
print(result.progress.is_enable_historical_object_replication)
# Display the progress of historical data synchronization.
print(result.progress.historical_object_progress)
# Display the progress of real-time data synchronization.
print(result.progress.new_object_progress)

# Query the regions to which data in the source bucket can be synchronized.
result = bucket.get_bucket_replication_location()
for location in result.location_list:
    print(location)

# Disable CRR for this bucket.
# Specify the replication rule ID. Example: test_replication_1.
result = bucket.delete_bucket_replication('test_replication_1')