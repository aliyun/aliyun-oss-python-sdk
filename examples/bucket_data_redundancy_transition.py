
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
service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), endpoint)

# Create a storage redundancy conversion task for the bucket.
targetType = "ZRS"
create_result = bucket.create_bucket_data_redundancy_transition(targetType)

# Obtain storage redundancy conversion tasks.
get_result = bucket.get_bucket_data_redundancy_transition(create_result.task_id)
print("Return status: ", get_result.status)
print("Return task id: ", get_result.task_id)
print("Return transition status: ", get_result.transition_status)
print("Return create time: ", get_result.create_time)
print("Return start time: ", get_result.start_time)
print("Return end time: ", get_result.end_time)
print("Return process percentage: ", get_result.process_percentage)
print("Return estimated remaining time: ", get_result.estimated_remaining_time)

# List all storage redundancy conversion tasks of the requester.
list_user_result = service.list_user_data_redundancy_transition(continuation_token='', max_keys=10)
print("Return status: ", list_user_result.status)
print("Return task id: ", list_user_result.data_redundancy_transitions[0].task_id)
print("Return transition status: ", list_user_result.data_redundancy_transitions[0].transition_status)
print("Return create time: ", list_user_result.data_redundancy_transitions[0].create_time)
print("Return start time: ", list_user_result.data_redundancy_transitions[0].start_time)
print("Return end time: ", list_user_result.data_redundancy_transitions[0].end_time)
print("Return process percentage: ", list_user_result.data_redundancy_transitions[0].process_percentage)
print("Return estimated remaining time: ", list_user_result.data_redundancy_transitions[0].estimated_remaining_time)

# List all storage redundancy conversion tasks under a certain bucket.
list_bucket_result = bucket.list_bucket_data_redundancy_transition()
print("Return status: ", list_bucket_result.status)
print("Return task id: ", list_bucket_result.data_redundancy_transitions[0].task_id)
print("Return transition status: ", list_bucket_result.data_redundancy_transitions[0].transition_status)
print("Return create time: ", list_bucket_result.data_redundancy_transitions[0].create_time)
print("Return start time: ", list_bucket_result.data_redundancy_transitions[0].start_time)
print("Return end time: ", list_bucket_result.data_redundancy_transitions[0].end_time)
print("Return process percentage: ", list_bucket_result.data_redundancy_transitions[0].process_percentage)
print("Return estimated remaining time: ", list_bucket_result.data_redundancy_transitions[0].estimated_remaining_time)

# Delete storage redundancy conversion task.
del_result = bucket.delete_bucket_data_redundancy_transition(create_result.task_id)
print("Return status: ", del_result.status)
