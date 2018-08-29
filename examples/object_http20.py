# -*- coding: utf-8 -*-

import os
import shutil

import oss2


# 以下代码展示了如何启用Http2.0来发送请求。


# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
#
# 以杭州区域为例，Endpoint可以是：
#   https://oss-cn-hangzhou.aliyuncs.com
# 目前Http2.0只支持HTTPS协议访问。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name, enable_http20=True)

# 上传一段字符串。Object名是motto.txt，内容是一段名言。
bucket.put_object('motto.txt', 'Never give up. - Jack Ma')

# 下载到本地文件
bucket.get_object_to_file('motto.txt', '本地文件名.txt')

# 清除本地文件
os.remove(u'本地文件名.txt')
