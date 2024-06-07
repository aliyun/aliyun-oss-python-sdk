
import os
import oss2

# Specify access information, such as AccessKeyId, AccessKeySecret, and Endpoint.
# You can obtain access information from evironment variables or replace sample values in the code, such as <your AccessKeyId> with actual values.
#
# For example, if your bucket is located in the China (Hangzhou) region, you can set Endpoint to one of the following values:
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com
from oss2.models import CreateAccessPointRequest, AccessPointVpcConfiguration

access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<yourAccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<yourAccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<yourBucketName>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<yourEndpoint>')


# Make sure that all parameters are correctly configured
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set parameters：' + param


# Create a bucket. You can use the bucket to call all object-related operations
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# create access point
accessPointName = 'example-ap'
vpc_id = 'your-vpc-id'
vpc = AccessPointVpcConfiguration(vpc_id)
access_point = CreateAccessPointRequest(accessPointName, 'internet')
# access_point = CreateAccessPointRequest(accessPointName, 'vpc', vpc)
result = bucket.create_access_point(access_point)
print("status: ", result.status)

# get access point
get_result = bucket.get_access_point(accessPointName)
print("status: ", get_result.status)
print("access point name: ", get_result.access_point_name)
print("bucket: ", get_result.bucket)
print("account id: ", get_result.account_id)
print("network origin: ", get_result.network_origin)
print("access point arn: ", get_result.access_point_arn)
print("creation date: ", get_result.creation_date)
print("alias: ", get_result.alias)
print("access point status: ", get_result.access_point_status)
print("public endpoint: ", get_result.endpoints.public_endpoint)
print("internal endpoint: ", get_result.endpoints.internal_endpoint)

# Bucket three-level domain name query access point
list_result = bucket.list_bucket_access_points(accessPointName)
print("is truncated: ", list_result.is_truncated)
print("access point name: ", list_result.access_points[0].access_point_name)
print("bucket: ", list_result.access_points[0].bucket)
print("network origin: ", list_result.access_points[0].network_origin)
print("alias: ", list_result.access_points[0].alias)
print("status: ", list_result.access_points[0].status)

# Secondary domain name query access point
service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)
list_result2 = service.list_access_points(accessPointName)
print("is truncated: ", list_result2.is_truncated)
print("access point name: ", list_result2.access_points[0].access_point_name)
print("bucket: ", list_result2.access_points[0].bucket)
print("network origin: ", list_result2.access_points[0].network_origin)
print("alias: ", list_result2.access_points[0].alias)
print("status: ", list_result2.access_points[0].status)

# delete access point
del_result = service.delete_access_point(accessPointName)
print("status: ", del_result.status)



