import base64
import os
import time
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

key = 'test-video.mp4'
dest_key = 'dest_test-video'
video_path = 'your mp4 video path'

# Make sure that all parameters are correctly configured
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set parameters：' + param


# Create a bucket. You can use the bucket to call all object-related operations
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# Upload local video files
put_result = bucket.put_object_from_file(key, video_path)
print("put object result status: %s" % put_result.status)

try:
    # Set process
    process = "video/convert,f_mp4,vcodec_h265,s_1920x1080,vb_2000000,fps_30,acodec_aac,ab_100000,sn_1|sys/saveas,o_{0},b_{1}".format(
        oss2.compat.to_string(base64.urlsafe_b64encode(oss2.compat.to_bytes(dest_key))).replace('=', ''),
        oss2.compat.to_string(base64.urlsafe_b64encode(oss2.compat.to_bytes(bucket.bucket_name))).replace('=', ''))

    # Call async_ process_ Object interface
    result = bucket.async_process_object(key, process)
    print("async process object result status: %s" % result.status)
    print(result.request_id)
    print("event_id: %s" % result.event_id)
    print("async_request_id: %s" % result.async_request_id)
    print("task_id: %s" % result.task_id)

    # Sleep for a period of time, waiting for asynchronous video processing to complete
    time.sleep(10)

    # Check if the processed video exists
    exists = bucket.object_exists(dest_key+".mp4")
    print("is exists: %s" % exists)
except oss2.exceptions.OssError as e:
    pass
finally:
    # Delete video files and processed files
    del_key = bucket.delete_object(key)
    print("delete key result: %s" % del_key.status)
    del_dest_key = bucket.delete_object(dest_key+".mp4")
    print("delete dest key result: %s" % del_dest_key.status)




