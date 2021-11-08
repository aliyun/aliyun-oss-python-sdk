
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

# Determine whether an object exists
# Specify the full path of the object. The full path of the object cannot contain bucket names.
exist = bucket.object_exists('exampleobject.txt')
# If the returned value is true, the specified object exists. If the returned value is false, the specified object does not exist.
if exist:
    print('object exist')
else:
    print('object not exist')


# Configure the ACL for the object.
bucket.put_object_acl('<yourObjectName>', oss2. OBJECT_ACL_PUBLIC_READ)

# Obtain the ACL for an object.
print(bucket.get_object_acl('<yourObjectName>').acl)
