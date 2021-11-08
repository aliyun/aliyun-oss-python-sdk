
import os
import oss2
import datetime
from oss2.headers import OSS_OBJECT_TAGGING, OSS_OBJECT_TAGGING_COPY_DIRECTIVE
from oss2 import SizedFileAdapter, determine_part_size
from oss2.headers import OSS_OBJECT_TAGGING
from oss2.models import (LifecycleExpiration, LifecycleRule,
                         BucketLifecycle, AbortMultipartUpload,
                         TaggingRule, Tagging, StorageTransition, PartInfo)

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

# The following code provides an example on how to add tags to an object when you upload the object by using simple upload:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'

# Configure the tagging string.
tagging = "k1=v1&k2=v2&k3=v3"

# If tags contain characters, you must encode the keys and values of the tags by using URL encoding.
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# Configure the tags in the HTTP headers.
headers = dict()
headers[OSS_OBJECT_TAGGING] = tagging

# Specify the headers when you call the put_object operation so that the tags are added to the object when it is uploaded.
result = bucket.put_object(object_name, 'content', headers=headers)
print('http response status: ', result.status)

# Query the tags added to the object.
result = bucket.get_object_tagging(object_name)
for key in result.tag_set.tagging_rule:
    print('tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))


# The following code provides an example on how to add tags to an object when you upload the object by using multipart upload:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'
# Specify the full path of the local file that you want to upload. Example: D:\\localpath\\examplefile.txt.
# By default, if you specify only the name of the local file such as examplefile.txt without specifying the local path, the local file is uploaded from the path of the project to which the sample program belongs.
filename = 'D:\\localpath\\examplefile.txt'

total_size = os.path.getsize(filename)
# Use the determine_part_size method to determine the size of each part.
part_size = determine_part_size(total_size, preferred_size=100 * 1024)

# Configure the tagging string.
tagging = "k1=v1&k2=v2&k3=v3"

# If tags contain characters, you must encode the keys and values of the tags by using URL encoding.
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# Configure the tags in the HTTP headers.
headers = dict()
headers[OSS_OBJECT_TAGGING] = tagging

# Initiate a multipart upload task.
# Specify the headers when you call the init_multipart_upload operation so that the tags are added to the object to upload.
upload_id = bucket.init_multipart_upload(object_name, headers=headers).upload_id
parts = []

# Upload the parts one by one.
with open(filename, 'rb') as fileobj:
    part_number = 1
    offset = 0
    while offset < total_size:
        num_to_upload = min(part_size, total_size - offset)
        # The SizedFileAdapter(fileobj, size) method generates a new object and recalculates the position from which the append operation starts.
        result = bucket.upload_part(object_name, upload_id, part_number,
                                    SizedFileAdapter(fileobj, num_to_upload))
        parts.append(PartInfo(part_number, result.etag))

        offset += num_to_upload
        part_number += 1

# Complete the multipart upload task.
result = bucket.complete_multipart_upload(object_name, upload_id, parts)
print('http response status: ', result.status)

# Query the tags added to the object.
result = bucket.get_object_tagging(object_name)
for key in result.tag_set.tagging_rule:
    print('tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))

# Verify the result of the multipart upload task.
with open(filename, 'rb') as fileobj:
    assert bucket.get_object(object_name).read() == fileobj.read()


# The following code provides an example on how to add tags to an object when you upload the object by using append upload:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'

# Configure the tagging string.
tagging = "k1=v1&k2=v2&k3=v3"

# If tags contain characters, you must encode the keys and values of the tags by using URL encoding.
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# Configure the tags in the HTTP headers.
headers = dict()
headers[OSS_OBJECT_TAGGING] = tagging

# Append the object. Specify the headers when you call the append_object operation so that the tags are added to the object.
# Only the tags configured the first time the object is appended are added to the object.
result = bucket.append_object(object_name, 0, '<yourContent>', headers=headers)

# Query the tags added to the object.
result = bucket.get_object_tagging(object_name)
for key in result.tag_set.tagging_rule:
    print('tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))


# The following code provides an example on how to add tags to an object when you upload the object by using resumable upload:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'
# Specify the full path of the local file. By default, if you do not specify the path of the local file, the local file is uploaded from the path of the project to which the sample program belongs.
local_file = 'D:\\localpath\\examplefile.txt'

# Configure the tagging string.
tagging = "k1=v1&k2=v2&k3=v3"

# If tags contain characters, you must encode the keys and values of the tags by using URL encoding.
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# Configure the tags in the HTTP headers.
headers = dict()
headers[OSS_OBJECT_TAGGING] = tagging

# When the object length is greater than or equal to the value of the multipart_threshold parameter, multipart upload is used. The multipart_threshold parameter is optional. The default value of multipart_threshold is 10 MB. If you do not specify a directory by using the store parameter, the .py-oss-upload directory is created in the HOME directory to store the checkpoint information.
# Specify the headers when you call the resumable_upload operation so that the tags are added to the object to be uploaded.
oss2.resumable_upload(bucket, object_name, local_file, headers=headers)

result = bucket.get_object_tagging(object_name)
for key in result.tag_set.tagging_rule:
    print('object tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))


# The following code provides an example on how to add tags to or modify the tags of an existing object:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'

# Create a tagging rule.
rule = TaggingRule()
rule.add('key1', 'value1')
rule.add('key2', 'value2')

# Create a tag.
tagging = Tagging(rule)

# Add the tag to the object.
result = bucket.put_object_tagging(object_name, tagging)
# Query the HTTP status code.
print('http response status:', result.status)


# The following code provides an example on how to add tags to a specified version of an object or modify the tags of the object:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'
# Specify the version ID of the object. Example: CAEQMxiBgICAof2D0BYiIDJhMGE3N2M1YTI1NDQzOGY5NTkyNTI3MGYyMzJm****.
version_id = 'CAEQMxiBgICAof2D0BYiIDJhMGE3N2M1YTI1NDQzOGY5NTkyNTI3MGYyMzJm****'

tagging = Tagging()
# Specify the key and value of the object tag. Example: the key is owner, and the value is John.
tagging.tag_set.add('owner', 'John')
tagging.tag_set.add('type', 'document')

params = dict()
params['versionId'] = version_id

bucket.put_object_tagging(object_name, tagging, params=params)


# The following code provides an example on how to add tags to an object smaller than 1 GB when you copy it by calling CopyObject:
# Specify the full path of the source object. Example: srcexampledir/exampleobject.txt.
src_object_name = 'srcexampledir/exampleobject.txt'
# Specify the full path of the destination object. Example: destexampledir1/exampleobject.txt.
dest_object_name1 = 'destexampledir1/exampleobject.txt'
# Specify the full path of the destination object. Example: destexampledir2/exampleobject.txt.
dest_object_name2 = 'destexampledir2/exampleobject.txt'

# Configure the tagging string.
tagging = "k1=v1&k2=v2&k3=v3"

# If tags contain characters, you must encode the keys and values of the tags by using URL encoding.
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# Set OSS_OBJECT_TAGGING_COPY_DIRECTIVE to COPY or keep the default value in the HTTP headers, so that the tags of the source object are added to the dest_object_name1 object.
headers=dict()
headers[OSS_OBJECT_TAGGING_COPY_DIRECTIVE] = 'COPY'
bucket.copy_object(bucket.bucket_name, src_object_name, dest_object_name1, headers=headers)

# Set OSS_OBJECT_TAGGING_COPY_DIRECTIVE to REPLACE in the HTTP headers, so that the tags specified in OSS_OBJECT_TAGGING are added to the dest_object_name2 object.
headers[OSS_OBJECT_TAGGING_COPY_DIRECTIVE] = 'REPLACE'
headers[OSS_OBJECT_TAGGING] = tagging
bucket.copy_object(bucket.bucket_name, src_object_name, dest_object_name2, headers=headers)

# Query the tags added to the src_object_name object.
result = bucket.get_object_tagging(src_object_name)
for key in result.tag_set.tagging_rule:
    print('src tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))

# Query the tags added to the dest_object_name1 object. The tags added to the dest_object_name1 object are the same as those of the src_object_name object.
result = bucket.get_object_tagging(dest_object_name1)
for key in result.tag_set.tagging_rule:
    print('dest1 object tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))

# Query the tags added to the dest_object_name2 object. The tags added to the dest_object_name2 object are those specified in headers[OSS_OBJECT_TAGGING].
result = bucket.get_object_tagging(dest_object_name2)
for key in result.tag_set.tagging_rule:
    print('dest2 object tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))


# The following code provides an example on how to add tags to an object larger than 1 GB when you copy it by calling MultipartUpload:
# Specify the full path of the source object. Example: srcexampledir/exampleobject.txt.
src_object_name = 'srcexampledir/exampleobject.txt'
# Specify the full path of the destination object. Example: destexampledir/exampleobject.txt.
dest_object_name = 'destexampledir/exampleobject.txt'

# Obtain the size of the source object.
head_info = bucket.head_object(src_object_name)
total_size = head_info.content_length
print('src object size:', total_size)

# Use the determine_part_size method to determine the size of each part.
part_size = determine_part_size(total_size, preferred_size=100 * 1024)
print('part_size:', part_size)

# Configure the tagging string.
tagging = "k1=v1&k2=v2&k3=v3"

# If tags contain characters, you must encode the keys and values of the tags by using URL encoding.
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# Configure the tags in the HTTP headers.
headers = dict()
headers[OSS_OBJECT_TAGGING] = tagging

# Initiate a multipart copy task.
# Specify the headers when you call the init_multipart_upload operation so that the tags are added to the destination object.
upload_id = bucket.init_multipart_upload(dest_object_name, headers=headers).upload_id
parts = []

# Upload the parts one by one.
part_number = 1
offset = 0
while offset < total_size:
    num_to_upload = min(part_size, total_size - offset)
    end = offset + num_to_upload - 1;
    result = bucket.upload_part_copy(bucket.bucket_name, src_object_name, (offset, end), dest_object_name, upload_id, part_number)
    # Save the part information.
    parts.append(PartInfo(part_number, result.etag))

    offset += num_to_upload
    part_number += 1

# Complete the multipart upload task.
result = bucket.complete_multipart_upload(dest_object_name, upload_id, parts)

# Obtain the metadata of the destination object.
head_info = bucket.head_object(dest_object_name)

# Query the size of the destination object.
dest_object_size = head_info.content_length
print('dest object size:', dest_object_size)

# Compare the size of the destination object with that of the source object.
assert dest_object_size == total_size

# Query the tags of the source object.
result = bucket.get_object_tagging(src_object_name)
for key in result.tag_set.tagging_rule:
    print('src tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))

# Query the tags added to the destination object.
result = bucket.get_object_tagging(dest_object_name)
for key in result.tag_set.tagging_rule:
    print('dest tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))


# The following code provides an example on how to add tags to a symbolic link:
# Specify the full path of the destination object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'
# Specify the full path of the symbolic link object. Example: shortcut/myobject.txt.
symlink_name = 'shortcut/myobject.txt'

# Configure the tagging string.
tagging = "k1=v1&k2=v2&k3=v3"

# If tags contain characters, you must encode the keys and values of the tags by using URL encoding.
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# Configure the tags in the HTTP headers.
headers = dict()
headers[OSS_OBJECT_TAGGING] = tagging

# Add a symbolic link to the object.
# Specify the headers when you call the put_symlink operation so that the tags are added to the symbolic link.
result = bucket.put_symlink(object_name, symlink_name, headers=headers)
print('http response status: ', result.status)

# Query the tags added to the symbolic link.
result = bucket.get_object_tagging(symlink_name)
for key in result.tag_set.tagging_rule:
    print('tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))



# The following code provides an example on how to query the tags of the exampleobject.txt object in the exampledir directory of the examplebucket bucket:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'

# Query the tags of the object.
result = bucket.get_object_tagging(object_name)

# View the tags of the object.
for key in result.tag_set.tagging_rule:
    print('tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))


# The following code provides an example on how to query the tags of a specified version of the exampleobject.txt object in the exampledir directory of the examplebucket bucket:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'
# Specify the version ID of the object. Example: CAEQMxiBgICAof2D0BYiIDJhMGE3N2M1YTI1NDQzOGY5NTkyNTI3MGYyMzJm****.
version_id = 'CAEQMxiBgICAof2D0BYiIDJhMGE3N2M1YTI1NDQzOGY5NTkyNTI3MGYyMzJm****'

params = dict()
params['versionId'] = version_id

result = bucket.get_object_tagging(object_name, params=params)
print(result)



# The following code provides an example on how to delete the tags of the exampleobject.txt object in the exampledir directory of the examplebucket bucket:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'

# Remove the tags of the object.
result = bucket.delete_object_tagging(object_name)
print('http response status: ', result.status)


# The following code provides an example on how to delete the tags of a specified version of the exampleobject.txt object in the exampledir directory of the examplebucket bucket:
# Specify the full path of the object. Example: exampledir/exampleobject.txt. The full path of the object cannot contain the bucket name.
object_name = 'exampledir/exampleobject.txt'
# Specify the version ID of the object.
version_id = 'CAEQMxiBgICAof2D0BYiIDJhMGE3N2M1YTI1NDQzOGY5NTkyNTI3MGYyMzJm****'

params = dict()
params['versionId'] = version_id
bucket.delete_object_tagging(object_name, params=params)



# The following code provides an example on how to add tagging configurations to a lifecycle rule:
# Specify that objects expire three days after they are last modified.
# Set the name of the expiration rule and the prefix to match the objects.
rule1 = LifecycleRule('rule1', 'tests/',
                      # Enable the expiration rule.
                      status=LifecycleRule.ENABLED,
                      # Set the validity period to three days after the last modified date.
                      expiration=LifecycleExpiration(days=3))

# Specify that the objects last modified before the specified date expire.
# Set the name of the expiration rule and the prefix to match the objects.
rule2 = LifecycleRule('rule2', 'logging-',
                      # Disable the expiration rule.
                      status=LifecycleRule.DISABLED,
                      # Specify that the objects last modified before the specified date expire.
                      expiration=LifecycleExpiration(created_before_date=datetime.date(2018, 12, 12)))

# Specify that parts expire three days after they are last modified.
rule3 = LifecycleRule('rule3', 'tests1/',
                      status=LifecycleRule.ENABLED,
                      abort_multipart_upload=AbortMultipartUpload(days=3))

# Specify that the parts last modified before the specified date expire.
rule4 = LifecycleRule('rule4', 'logging1-',
                      status=LifecycleRule.DISABLED,
                      abort_multipart_upload = AbortMultipartUpload(created_before_date=datetime.date(2018, 12, 12)))

# Configure tags to match objects.
tagging_rule = TaggingRule()
tagging_rule.add('key1', 'value1')
tagging_rule.add('key2', 'value2')
tagging = Tagging(tagging_rule)

# Configure the rule to convert the storage class of objects. Specify that the storage class of objects is converted to Archive 365 days after the objects are last modified.
# Tags to match objects are specified in rule5. The rule applies only to objects that match tag conditions of key1=value1 and key2=value2.
rule5 = LifecycleRule('rule5', 'logging2-',
                      status=LifecycleRule.ENABLED,
                      storage_transitions=[StorageTransition(days=365, storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE)],
                      tagging = tagging)

lifecycle = BucketLifecycle([rule1, rule2, rule3, rule4, rule5])

bucket.put_bucket_lifecycle(lifecycle)


# The following code provides an example on how to view the tagging configurations of a lifecycle rule:
# View the lifecycle rules.
lifecycle = bucket.get_bucket_lifecycle()

for rule in lifecycle.rules:
    # View the part expiration rules.
    if rule.abort_multipart_upload is not None:
        print('id={0}, prefix={1}, tagging={2}, status={3}, days={4}, created_before_date={5}'
              .format(rule.id, rule.prefix, rule.tagging, rule.status,
                      rule.abort_multipart_upload.days,
                      rule.abort_multipart_upload.created_before_date))

    # View the object expiration rules.
    if rule.expiration is not None:
        print('id={0}, prefix={1}, tagging={2}, status={3}, days={4}, created_before_date={5}'
              .format(rule.id, rule.prefix, rule.tagging, rule.status,
                      rule.expiration.days,
                      rule.expiration.created_before_date))
    # View the rules to convert the storage class.
    if len(rule.storage_transitions) > 0:
        storage_trans_info = ''
        for storage_rule in rule.storage_transitions:
            storage_trans_info += 'days={0}, created_before_date={1}, storage_class={2} **** '.format(
                storage_rule.days, storage_rule.created_before_date, storage_rule.storage_class)

        print('id={0}, prefix={1}, tagging={2}, status={3},, StorageTransition={4}'
              .format(rule.id, rule.prefix, rule.tagging, rule.status, storage_trans_info))