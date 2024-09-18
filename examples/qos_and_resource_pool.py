import os
from oss2.models import QoSConfiguration
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
uid = 'yourAccountID'
resource_pool_name = 'yourResourcePoolName'


# Make sure that all parameters are correctly configured
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set parameters：' + param


# Create a bucket. You can use the bucket to call all object-related operations
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# Create a service.
service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), endpoint)


# put bucket requester qos info
qos_info = QoSConfiguration(
    total_upload_bw = 100,
    intranet_upload_bw = 6,
    extranet_upload_bw = 12,
    total_download_bw = 110,
    intranet_download_bw = 20,
    extranet_download_bw = 50,
    total_qps = 300,
    intranet_qps = 160,
    extranet_qps = 170)

result = bucket.put_bucket_requester_qos_info(uid, qos_info)
print(result.status)

# get bucket requester qos info
result = bucket.get_bucket_requester_qos_info(uid)
print(result.requester)
print(result.qos_configuration.total_upload_bw)
print(result.qos_configuration.intranet_upload_bw)
print(result.qos_configuration.extranet_upload_bw)
print(result.qos_configuration.total_download_bw)
print(result.qos_configuration.intranet_download_bw)
print(result.qos_configuration.extranet_download_bw)
print(result.qos_configuration.total_qps)
print(result.qos_configuration.intranet_qps)
print(result.qos_configuration.extranet_qps)


# list bucket requester qos infos
result = bucket.list_bucket_requester_qos_infos()
print(result.bucket)
print(result.continuation_token)
print(result.next_continuation_token)
print(result.is_truncated)

for i, element in enumerate(result.requester_qos_info):
    print(element.qos_configuration.total_upload_bw)
    print(element.qos_configuration.intranet_upload_bw)
    print(element.qos_configuration.extranet_upload_bw)
    print(element.qos_configuration.total_download_bw)
    print(element.qos_configuration.intranet_download_bw)
    print(element.qos_configuration.extranet_download_bw)
    print(element.qos_configuration.total_qps)
    print(element.qos_configuration.intranet_qps)
    print(element.qos_configuration.extranet_qps)

# delete bucket requester qos info
result = bucket.delete_bucket_requester_qos_info(uid)
print(result.status)


# list resource pools
result = service.list_resource_pools()
print(result.status)
print(result.region)
print(result.owner)
print(result.continuation_token)
print(result.next_continuation_token)
print(result.is_truncated)

for i, element in enumerate(result.resource_pool):
    print(element.name)
    print(element.create_time)


# get resource pool info
result = service.get_resource_pool_info(resource_pool_name)
print(result.status)
print(result.region)
print(result.owner)
print(result.create_time)
print(result.qos_configuration.total_upload_bw)
print(result.qos_configuration.intranet_upload_bw)
print(result.qos_configuration.extranet_upload_bw)
print(result.qos_configuration.total_download_bw)
print(result.qos_configuration.intranet_download_bw)
print(result.qos_configuration.extranet_download_bw)
print(result.qos_configuration.total_qps)
print(result.qos_configuration.intranet_qps)
print(result.qos_configuration.extranet_qps)


# list resource pool buckets
result = service.list_resource_pool_buckets(resource_pool_name)
print(result.status)
print(result.resource_pool)
print(result.continuation_token)
print(result.next_continuation_token)
print(result.is_truncated)

for i, element in enumerate(result.resource_pool_buckets):
    print(element.name)
    print(element.join_time)

# put resource pool requester qos info
qos_info = QoSConfiguration(
    total_upload_bw = 200,
    intranet_upload_bw = 16,
    extranet_upload_bw = 112,
    total_download_bw = 210,
    intranet_download_bw = 120,
    extranet_download_bw = 150,
    total_qps = 400,
    intranet_qps = 260,
    extranet_qps = 270)
result = service.put_resource_pool_requester_qos_info(uid, resource_pool_name, qos_info)
print(result.status)


# get resource pool requester qos info
result = service.get_resource_pool_requester_qos_info(uid, resource_pool_name)
print(result.status)
print(result.requester)
print(result.qos_configuration.total_upload_bw)
print(result.qos_configuration.intranet_upload_bw)
print(result.qos_configuration.extranet_upload_bw)
print(result.qos_configuration.total_download_bw)
print(result.qos_configuration.intranet_download_bw)
print(result.qos_configuration.extranet_download_bw)
print(result.qos_configuration.total_qps)
print(result.qos_configuration.intranet_qps)
print(result.qos_configuration.extranet_qps)


# list resource pool requester qos infos
result = service.list_resource_pool_requester_qos_infos(resource_pool_name)
print(result.status)
print(result.resource_pool)
print(result.continuation_token)
print(result.next_continuation_token)
print(result.is_truncated)

for i, element in enumerate(result.requester_qos_info):
    print(element.qos_configuration.total_upload_bw)
    print(element.qos_configuration.intranet_upload_bw)
    print(element.qos_configuration.extranet_upload_bw)
    print(element.qos_configuration.total_download_bw)
    print(element.qos_configuration.intranet_download_bw)
    print(element.qos_configuration.extranet_download_bw)
    print(element.qos_configuration.total_qps)
    print(element.qos_configuration.intranet_qps)
    print(element.qos_configuration.extranet_qps)


# delete resource pool requester qos infos
result = service.delete_resource_pool_requester_qos_info(uid, resource_pool_name)
print(result.status)