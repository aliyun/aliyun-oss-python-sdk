# -*- coding: utf-8 -*-

import os
import oss2
import requests
import datetime
import time
import hashlib
import hmac


# 下面的代码展示了使用OSS V2签名算法来对请求进行签名


# 首先，初始化AccessKeyId、AccessKeySecret和Endpoint.
# 你可以通过设置环境变量来设置access_key_id等, 或者直接使用真实access_key_id替换'<Your AccessKeyId>'等
#
# 以杭州(华东1)作为例子, endpoint应该是
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com
# 对HTTP和HTTPS请求，同样的处理
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<Your AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<Your AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<Your Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<Your Endpoint>')


if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
    endpoint = 'http://' + endpoint


# 验证access_key_id和其他参数都被合理地初始化
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set variable: ' + param


# 创建一个AuthV2对象，这样我们就可以用V2算法来签名请求。也可以使用oss2.make_auth函数，默认采用V1算法
auth = oss2.AuthV2(access_key_id, access_key_secret)
# auth = oss2.make_auth(access_key_id, access_key_secret, oss2.AUTH_VERSION_2)

# 创建一个Bucket，利用它进行所有bucket与object相关操作
bucket = oss2.Bucket(auth, endpoint, bucket_name)

content = b'Never give up. - Jack Ma'

# 上传一个Object
bucket.put_object('motto.txt', content)

# 下载一个object
result = bucket.get_object('motto.txt')

assert result.read() == content

# 生成一个签名的URL，将在60秒后过期
url = bucket.sign_url('GET', 'motto.txt', 60)

print(url)


# 人工构造一个使用V2签名的请求
key = 'object-from-post.txt'

boundary = 'arbitraryboundaryvalue'
headers = {'Content-Type': 'multipart/form-data; boundary=' + boundary}
encoded_policy = oss2.utils.b64encode_as_string(oss2.to_bytes('{ "expiration": "%s","conditions": [["starts-with", "$key", ""]]}'
         % oss2.date_to_iso8601(datetime.datetime.utcfromtimestamp(int(time.time()) + 60))))

digest = hmac.new(oss2.to_bytes(access_key_secret), oss2.to_bytes(encoded_policy), hashlib.sha256).digest()
signature = oss2.utils.b64encode_as_string(digest)

form_fields = {
    'x-oss-signature-version': 'OSS2',
    'x-oss-signature': signature,
    'x-oss-access-key-id': access_key_id,
    'policy': encoded_policy,
    'key': key,
}

# 对象的内容
content = 'file content for post object request'

body = ''

for k, v in form_fields.items():
    body += '--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (boundary, k, v)

body += '--%s\r\nContent-Disposition: form-data; name="file"; filename="%s"\r\n\r\n%s\r\n' % (boundary, key, content)
body += '--%s\r\nContent-Disposition: form-data; name="submit"\r\n\r\nUpload to OSS\r\n--%s--\r\n' % (boundary, boundary)

p = oss2.urlparse(endpoint)
requests.post('%s://%s.%s' % (p.scheme, bucket_name, p.netloc), data=body, headers=headers)
