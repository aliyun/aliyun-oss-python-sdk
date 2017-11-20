# -*- coding: utf-8 -*-

import os
import oss2
import requests
import datetime
import time
import hashlib
import hmac


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


if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
    endpoint = 'http://' + endpoint


# Verify access_key_id and others are properly initialized
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set variable: ' + param


# Create an Auth instance with sign_version=oss2.SIGN_VERSION_2 so that we sign our requests by V2 algorithm:
auth = oss2.Auth(access_key_id, access_key_secret, sign_version=oss2.SIGN_VERSION_2)

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


# manually construct a PostObject request and use V2 signature
key = 'object-from-post.txt'

boundary = 'arbitraryboundaryvalue'
headers = {'Content-Type': 'multipart/form-data; boundary=' + boundary}
encoded_policy = oss2.utils.b64encode_as_string('{ "expiration": "%s","conditions": [["starts-with", "$key", ""]]}'
         % oss2.date_to_iso8601(datetime.datetime.utcfromtimestamp(int(time.time()) + 60)))

digest = hmac.new(oss2.to_bytes(access_key_secret), oss2.to_bytes(encoded_policy), hashlib.sha256).digest()
signature = oss2.utils.b64encode_as_string(digest)

form_fields = {
    'x-oss-signature-version': 'OSS2',
    'x-oss-signature': signature,
    'x-oss-access-key-id': access_key_id,
    'policy': encoded_policy,
    'key': key,
}

# the content of the object
content = 'file content for post object request'

body = ''

for k, v in form_fields.items():
    body += '--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (boundary, k, v)

body += '--%s\r\nContent-Disposition: form-data; name="file"; filename="%s"\r\n\r\n%s\r\n' % (boundary, key, content)
body += '--%s\r\nContent-Disposition: form-data; name="submit"\r\n\r\nUpload to OSS\r\n--%s--\r\n' % (boundary, boundary)

p = oss2.urlparse(endpoint)
requests.post('%s://%s.%s' % (p.scheme, bucket_name, p.netloc), data=body, headers=headers)
