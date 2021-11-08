
import os
import oss2
from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import PartInfo

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

# The following code provides an example on how to disable overwrite for an object with the same name when you use simple upload:
# Upload the object.
# Specify whether the PutObject operation overwrites the object with the same name.
# By default, if x-oss-forbid-overwrite is not specified, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to false, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to true, the object with the same name is not overwritten. If the object with the same name already exists, an error is returned.
headers = dict()
headers["x-oss-forbid-overwrite"] = "true"
result = bucket.put_object('<yourObjectName>', 'content of object', headers=headers)

# Obtain the HTTP status code.
print('http status: {0}'.format(result.status))
# Obtain the unique request ID. We recommend that you add this parameter in the program logs.
print('request_id: {0}'.format(result.request_id))
# Obtain the ETag value returned by the put_object method.
print('ETag: {0}'.format(result.etag))
# Obtain the HTTP response headers.
print('date: {0}'.format(result.headers['date']))


# The following code provides an example on how to copy a small object without overwriting the object with the same object name:
# Specify whether the copy_object operation overwrites the object with the same object name.
# By default, if x-oss-forbid-overwrite is not specified, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to false, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to true, the object with the same name is not overwritten. If the object with the same name already exists, an error is returned.
headers = dict()
headers["x-oss-forbid-overwrite"] = "true"
bucket.copy_object('<yourSourceBucketName>', '<yourSourceObjectName>', '<yourDestinationObjectName>', headers=headers)


# The following code provides an example on how to disable overwrite for the object with the same name when you copy a large object by using multipart copy:
src_object = '<yourSourceObjectName>'
dst_object = '<yourDestinationObjectName>'

total_size = bucket.head_object(src_object).content_length
part_size = determine_part_size(total_size, preferred_size=100 * 1024)

# Initiate a multipart copy task.
# Specify whether to overwrite an object with the same name when copying an object.
# By default, if x-oss-forbid-overwrite is not specified, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to false, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to true, the object with the same name is not overwritten. If the object with the same name already exists, an error is returned.
headers = dict()
headers["x-oss-forbid-overwrite"] = "true"
upload_id = bucket.init_multipart_upload(dst_object, headers=headers).upload_id
parts = []

# Copy each part sequentially.
part_number = 1
offset = 0
while offset < total_size:
    num_to_upload = min(part_size, total_size - offset)
    byte_range = (offset, offset + num_to_upload - 1)

    result = bucket.upload_part_copy(bucket.bucket_name, src_object, byte_range,dst_object, upload_id, part_number)
    parts.append(PartInfo(part_number, result.etag))

    offset += num_to_upload
    part_number += 1

# Complete multipart copy.
# Specify whether to overwrite an object with the same name when copying an object.
# By default, if x-oss-forbid-overwrite is not specified, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to false, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to true, the object with the same name is not overwritten. If the object with the same name already exists, an error is returned.
headers = dict()
headers["x-oss-forbid-overwrite"] = "true"
bucket.complete_multipart_upload(dst_object, upload_id, parts, headers=headers)


# The following code provides an example on how to disable overwrite for the object with the same name when you use multipart upload:
key = '<yourObjectName>'
filename = '<yourLocalFile>'

total_size = os.path.getsize(filename)
# Use the determine_part_size method to determine the size of each part.
part_size = determine_part_size(total_size, preferred_size=100 * 1024)

# Initiate a multipart upload task.
# Specify whether to overwrite the object with the same name when performing multipart upload.
# By default, if x-oss-forbid-overwrite is not specified, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to false, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to true, the object with the same name is not overwritten. If the object with the same name already exists, an error is returned.
headers["x-oss-forbid-overwrite"] = "true"
upload_id = bucket.init_multipart_upload(key, headers=headers).upload_id
parts = []

# Upload each part sequentially.
with open(filename, 'rb') as fileobj:
    part_number = 1
    offset = 0
    while offset < total_size:
        num_to_upload = min(part_size, total_size - offset)
        # The SizedFileAdapter(fileobj, size) method generates a new object and recalculates the length of the append object.
        result = bucket.upload_part(key, upload_id, part_number,
                                    SizedFileAdapter(fileobj, num_to_upload))
        parts.append(PartInfo(part_number, result.etag))

        offset += num_to_upload
        part_number += 1

# Complete multipart upload.
# Specify whether to overwrite the object with the same name when performing multipart upload.
# By default, if x-oss-forbid-overwrite is not specified, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to false, the object with the same name is overwritten.
# If x-oss-forbid-overwrite is set to true, the object with the same name is not overwritten. If the object with the same name already exists, an error is returned.
headers["x-oss-forbid-overwrite"] = "true"
bucket.complete_multipart_upload(key, upload_id, parts, headers=headers)

# Verify multipart upload.
with open(filename, 'rb') as fileobj:
    assert bucket.get_object(key).read() == fileobj.read()