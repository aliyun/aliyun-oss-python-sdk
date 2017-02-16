# -*- coding: utf-8 -*-

import os
import oss2


# Below code demonstrates sign requests with OSS V2 signature algorithm


# First initialize AccessKeyId、AccessKeySecret、Endpoint.
# You may set environment variables to set access_key_id etc., or you may directly replace '<Your AccessKeyId>' with
# real AccessKeyId.
#
# Take Hangzhou (East China 1) region as example, endpoint should be
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com
# for HTTP and HTTPS requests respectively.
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<Your AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<Your AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<Your Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<Your Endpoint>')


# Verify access_key_id and others are properly initialized
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set variable: ' + param


# Create an AuthV2 instance so that we sign our requests by V2 algorithm:
auth = oss2.AuthV2(access_key_id, access_key_secret)

# Create a Bucket instance, all bucket and object operations are taken on it
bucket = oss2.Bucket(auth, endpoint, bucket_name)

content = 'Never give up. - Jack Ma'

# Upload an object from memory
bucket.put_object('motto.txt', content)

# download the object to memory
result = bucket.get_object('motto.txt')

assert result.read() == content

# generate a signed URL, which will be exipred after 60 seconds
url = bucket.sign_url('GET', 'motto.txt', 60)

print(url)
