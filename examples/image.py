# -*- coding: utf-8 -*-

import json
import os

from PIL import Image

import oss2


# 以下代码展示了图片服务的基本用法。更详细应用请参看官网文档 https://help.aliyun.com/document_detail/32206.html

# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
#
# 以杭州区域为例，Endpoint可以是：
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com
# 分别以HTTP、HTTPS协议访问。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param

def get_image_info(image_file):
    """获取本地图片信息
    :param str image_file: 本地图片
    :return tuple: a 3-tuple(height, width, format).
    """
    im = Image.open(image_file)
    return im.height, im.width, im.format

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

key = 'example.jpg'
new_pic = 'new-example.jpg'

# 上传示例图片
bucket.put_object_from_file(key, 'example.jpg')

# 获取图片信息
result = bucket.get_object(key, process='image/info')

json_content = result.read()
decoded_json = json.loads(oss2.to_unicode(json_content))
assert int(decoded_json['ImageHeight']['value']) == 267
assert int(decoded_json['ImageWidth']['value']) == 400
assert int(decoded_json['FileSize']['value']) == 21839
assert decoded_json['Format']['value'] == 'jpg'

# 图片缩放
process = "image/resize,m_fixed,w_100,h_100"
bucket.get_object_to_file(key, new_pic, process=process)
info = get_image_info(new_pic)
assert info[0] == 100
assert info[1] == 100
assert info[2] == 'JPEG'

# 图片裁剪
process = "image/crop,w_100,h_100,x_100,y_100,r_1"
bucket.get_object_to_file(key, new_pic, process=process)
info = get_image_info(new_pic)
assert info[0] == 100
assert info[1] == 100
assert info[2] == 'JPEG'

# 图片旋转
process = "image/rotate,90"
bucket.get_object_to_file(key, new_pic, process=process)
info = get_image_info(new_pic)
assert info[0] == 400
assert info[1] == 267
assert info[2] == 'JPEG'

# 图片锐化
process = "image/sharpen,100"
bucket.get_object_to_file(key, new_pic, process=process)
info = get_image_info(new_pic)
assert info[0] == 267
assert info[1] == 400
assert info[2] == 'JPEG'

# 图片加文字水印
process = "image/watermark,text_SGVsbG8g5Zu-54mH5pyN5YqhIQ"
bucket.get_object_to_file(key, new_pic, process=process)
info = get_image_info(new_pic)
assert info[0] == 267
assert info[1] == 400
assert info[2] == 'JPEG'

# 图片格式转换
process = "image/format,png"
bucket.get_object_to_file(key, new_pic, process=process)
info = get_image_info(new_pic)
assert info[0] == 267
assert info[1] == 400
assert info[2] == 'PNG'

# 删除示例图片
bucket.delete_object(key)
# 清除本地文件
os.remove(new_pic)
