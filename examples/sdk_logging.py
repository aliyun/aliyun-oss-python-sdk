
import os
import oss2
import logging
from itertools import islice

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


# Download log information to a local log file, and store the log file in the specified local path.
# By default, if you specify the name of a local file such as examplelogfile.log without specifying the local path, the local file is saved to the local path of the project to which the sample program belongs.
log_file_path = "D:\\localpath\\examplelogfile.log"

# Enable log recording.
oss2.set_file_logger(log_file_path, 'oss2', logging.INFO)
# Security risks may arise if you use the AccessKey pair of an Alibaba Cloud account to access OSS because the account has permissions on all API operations. We recommend that you use a RAM user to call API operations or perform routine O&M. To create a RAM user, log on to the RAM console.
auth = oss2.Auth('yourAccessKeyId', 'yourAccessKeySecret')
# Set yourEndpoint to the endpoint of the region in which the bucket is located. For example, if your bucket is located in the China (Hangzhou) region, set yourEndpoint to https://oss-cn-hangzhou.aliyuncs.com.
# Specify the name of the bucket. Example: examplebucket.
bucket = oss2.Bucket(auth, 'yourEndpoint', 'examplebucket')

# Traverse objects and directories.
for b in islice(oss2.ObjectIterator(bucket), 10):
    print(b.key)
# Obtain the metadata of the object.
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain bucket names.
object_meta = bucket.get_object_meta('exampledir/exampleobject.txt')