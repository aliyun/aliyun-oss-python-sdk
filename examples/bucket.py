# -*- coding: utf-8 -*-

import time
import os

import oss2


# 以下代码展示了Bucket相关操作，诸如创建、删除、列举Bucket等。


# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param


# 列举所有的Bucket
#   1. 先创建一个Service对象
#   2. 用oss2.BucketIterator遍历
service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), endpoint)
print('\n'.join(info.name for info in oss2.BucketIterator(service)))


# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)


# 下面只展示如何配置静态网站托管。其他的Bucket操作方式类似，可以参考tests/test_bucket.py里的内容

# 方法一：可以生成一个BucketWebsite对象来设置
bucket.put_bucket_website(oss2.models.BucketWebsite('index.html', 'error.html'))

# 方法二：可以直接设置XML
xml = '''
<WebsiteConfiguration>
    <IndexDocument>
        <Suffix>index2.html</Suffix>
    </IndexDocument>

    <ErrorDocument>
        <Key>error2.html</Key>
    </ErrorDocument>
</WebsiteConfiguration>
'''
bucket.put_bucket_website(xml)

# 方法三：可以从本地文件读取XML配置
# oss2.to_bytes()可以把unicode转换为bytes
with open('website_config.xml', 'wb') as f:
    f.write(oss2.to_bytes(xml))

with open('website_config.xml', 'rb') as f:
    bucket.put_bucket_website(f)

os.remove('website_config.xml')


# 获取配置
# 因为是分布式系统，所以配置刚刚设置好，可能还不能立即获取到，先等几秒钟
time.sleep(5)

result = bucket.get_bucket_website()
assert result.index_file == 'index2.html'
assert result.error_file == 'error2.html'


# 取消静态网站托管模式
bucket.delete_bucket_website()