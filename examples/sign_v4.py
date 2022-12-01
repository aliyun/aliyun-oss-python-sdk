# -*- coding: utf-8 -*-

import os
import oss2


# 下面的代码展示了使用OSS V4签名算法来对请求进行签名


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
region = os.getenv('OSS_TEST_REGION', '<Your Region>')


if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
    endpoint = 'http://' + endpoint


# 验证access_key_id和其他参数都被合理地初始化
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, 'Please set variable: ' + param


# 创建一个AuthV4对象，这样我们就可以用V4算法来签名请求。也可以使用oss2.make_auth函数，默认采用V1算法
auth = oss2.AuthV4(access_key_id, access_key_secret)
# auth = oss2.make_auth(access_key_id, access_key_secret, oss2.AUTH_VERSION_4)

# 创建一个Bucket，利用它进行所有bucket与object相关操作
bucket = oss2.Bucket(auth, endpoint, bucket_name, region=region)

service = oss2.Service(auth, endpoint, region=region)

content = b'Never give up. - Jack Ma'

# 上传一个Object
bucket.put_object('motto.txt', content)

# 下载一个object
result = bucket.get_object('motto.txt')

assert result.read() == content

# 生成一个签名的URL，将在60秒后过期
url = bucket.sign_url('GET', 'motto.txt', 60)

print(url)


