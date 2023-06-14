
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
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<yourEndpoint>')


# Make sure that all parameters are correctly configured
for param in (access_key_id, access_key_secret, endpoint):
    assert '<' not in param, 'Please set parameters：' + param

service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), endpoint)

# Query Endpoint information corresponding to all supported regions
result = service.describe_regions()

for r in result.regions:
    print('region: {0}'.format(r.region))
    print('internet_endpoint: {0}'.format(r.internet_endpoint))
    print('internal_endpoint: {0}'.format(r.internal_endpoint))
    print('accelerate_endpoint: {0}'.format(r.accelerate_endpoint))


# Querying Endpoint Information Corresponding to a Specific Region
result = service.describe_regions('oss-cn-hangzhou')

for r in result.regions:
    print('Specific region: {0}'.format(r.region))
    print('Specific internet_endpoint: {0}'.format(r.internet_endpoint))
    print('Specific internal_endpoint: {0}'.format(r.internal_endpoint))
    print('Specific accelerate_endpoint: {0}'.format(r.accelerate_endpoint))