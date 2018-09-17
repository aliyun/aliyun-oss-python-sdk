# -*- coding: utf-8 -*-

import json
import base64
import os

import oss2


# 以下代码展示了上传回调的用法。

# put_object/complete_multipart_upload支持上传回调，resumable_upload不支持。
# 回调服务器(callbacke server)的示例代码请参考 http://shinenuaa.oss-cn-hangzhou.aliyuncs.com/images/callback_app_server.py.zip
# 您也可以使用OSS提供的回调服务器 http://oss-demo.aliyuncs.com:23450，调试您的程序。调试完成后换成您的回调服务器。

# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param

key = 'quote.txt'
content = "Anything you're good at contributes to happiness."

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

"""
put_object上传回调
"""

# 准备回调参数，更详细的信息请参考 https://help.aliyun.com/document_detail/31989.html
callback_dict = {}
callback_dict['callbackUrl'] = 'http://oss-demo.aliyuncs.com:23450'
callback_dict['callbackHost'] = 'oss-cn-hangzhou.aliyuncs.com'
callback_dict['callbackBody'] = 'filename=${object}&size=${size}&mimeType=${mimeType}'
callback_dict['callbackBodyType'] = 'application/x-www-form-urlencoded'
# 回调参数是json格式，并且base64编码
callback_param = json.dumps(callback_dict).strip()
base64_callback_body = oss2.utils.b64encode_as_string(callback_param)
# 回调参数编码后放在header中传给oss
headers = {'x-oss-callback': base64_callback_body}

# 上传并回调
result = bucket.put_object(key, content, headers)

# 上传并回调成功status为200，上传成功回调失败status为203
assert result.status == 200
# result.resp的内容为回调服务器返回的内容
assert result.resp.read() == b'{"Status":"OK"}'

# 确认文件上传成功
result = bucket.head_object(key)
assert result.headers['x-oss-hash-crc64ecma'] == '108247482078852440'

# 删除上传的文件
bucket.delete_object(key)

"""
分片上传回调
"""

# 分片上传回调
# 初始化上传任务
parts = []
upload_id = bucket.init_multipart_upload(key).upload_id
# 上传分片
result = bucket.upload_part(key, upload_id, 1, content)
parts.append(oss2.models.PartInfo(1, result.etag, size = len(content), part_crc = result.crc))
# 完成上传并回调
result = bucket.complete_multipart_upload(key, upload_id, parts, headers)

# 上传并回调成功status为200，上传成功回调失败status为203
assert result.status == 200
# result.resp的内容为回调服务器返回的内容
assert result.resp.read() == b'{"Status":"OK"}'

# 确认文件上传成功
result = bucket.head_object(key)
assert result.headers['x-oss-hash-crc64ecma'] == '108247482078852440'

# 删除上传的文件
bucket.delete_object(key)
