
import os
import oss2
import time

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

object_name = '<yourObjectName>'

# The following code provides an example of how to convert the storage class of an object from Standard or IA to Archive:
# Add a header that specifies the storage class. Set the storage class to Archive.
headers = {'x-oss-storage-class': oss2.BUCKET_STORAGE_CLASS_ARCHIVE}

# Modify the storage class of the object.
bucket.copy_object(bucket.bucket_name, object_name, object_name, headers)

# The following code provides an example of how to convert the storage class of an object from Archive to IA:
# Obtain the object metadata.
meta = bucket.head_object(object_name)

# Check whether the storage class of the object is Archive. If the storage class of the source object is Archive, you must restore the object before you can modify the storage class. Wait for about one minute until the object is restored.
if meta.resp.headers['x-oss-storage-class'] == oss2.BUCKET_STORAGE_CLASS_ARCHIVE:
    bucket.restore_object(object_name)
    while True:
        meta = bucket.head_object(object_name)
        if meta.resp.headers['x-oss-restore'] == 'ongoing-request="true"':
            time.sleep(5)
        else:
            break

# Add a header that specifies the storage class. Set the storage class to IA.
headers = {'x-oss-storage-class': oss2.BUCKET_STORAGE_CLASS_IA}

# Modify the storage class of the object.
bucket.copy_object(bucket.bucket_name, object_name, object_name, headers)