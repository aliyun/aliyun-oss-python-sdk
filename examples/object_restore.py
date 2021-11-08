
import os
import oss2
from oss2.models import (RestoreJobParameters,
                         RestoreConfiguration,
                         RESTORE_TIER_EXPEDITED,
                         RESTORE_TIER_STANDARD,
                         RESTORE_TIER_BULK)

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

object_name = "<yourObjectName>"
# Restore archived objects
bucket.restore_object(object_name)

# Restore cold archived objects
# Refer to the following code if you set the storage class of the object to upload to Cold Archive.
# bucket.put_object(object_name, '<yourContent>', headers={"x-oss-storage-class": oss2.BUCKET_STORAGE_CLASS_COLD_ARCHIVE})

# Configure the restore mode of the cold archived object. # RESTORE_TIER_EXPEDITED: The object is restored within one hour.
# RESTORE_TIER_STANDARD: The object is restored within two to five hours.
# RESTORE_TIER_BULK: The object is restored within five to twelve hours.
job_parameters = RestoreJobParameters(RESTORE_TIER_STANDARD)

# Configure parameters. For example, set the restore mode of the object to Standard and set the duration for which the object can remain in the restored state to two days.
# The days parameter indicates the duration for which the object can remain in the restored state. The default value is one day. This parameter applies to archived objects and cold archived objects.
# The job_parameters parameter indicates the restore mode of the object. This parameter applies only to cold archived objects.
restore_config= RestoreConfiguration(days=2, job_parameters=job_parameters)

# Initiate a restore request.
bucket.restore_object(object_name, input=restore_config)