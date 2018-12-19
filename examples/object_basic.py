# -*- coding: utf-8 -*-

import os
import shutil

import oss2


# 以下代码展示了基本的文件上传、下载、罗列、删除用法。


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


# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)


# 上传一段字符串。Object名是motto.txt，内容是一段名言。
bucket.put_object('motto.txt', 'Never give up. - Jack Ma')

# 获取Object的metadata
object_meta = bucket.get_object_meta('你的对象名')
print('last modified: ' + object_meta.last_modified)
print('etag: ' + object_meta.etag)
print('size: ' + object_meta.content_length)

# 下载到本地文件
bucket.get_object_to_file('motto.txt', '本地文件名.txt')


# 把刚刚上传的Object下载到本地文件 “座右铭.txt” 中
# 因为get_object()方法返回的是一个file-like object，所以我们可以直接用shutil.copyfileobj()做拷贝
with open(oss2.to_unicode('本地座右铭.txt'), 'wb') as f:
    shutil.copyfileobj(bucket.get_object('motto.txt'), f)


# 把本地文件 “座右铭.txt” 上传到OSS，新的Object叫做 “我的座右铭.txt”
# 注意到，这次put_object()的第二个参数是file object；而上次上传是一个字符串。
# put_object()能够识别不同的参数类型
with open(oss2.to_unicode('本地座右铭.txt'), 'rb') as f:
    bucket.put_object('云上座右铭.txt', f)


# 上面两行代码，也可以用下面的一行代码来实现
bucket.put_object_from_file('云上座右铭.txt', '本地座右铭.txt')


# 列举Bucket下10个Object，并打印它们的最后修改时间、文件名
for i, object_info in enumerate(oss2.ObjectIterator(bucket)):
    print("{0} {1}".format(object_info.last_modified, object_info.key))

    if i >= 9:
        break


# 删除名为motto.txt的Object
bucket.delete_object('motto.txt')

# 也可以批量删除
# 注意：重复删除motto.txt，并不会报错
bucket.batch_delete_objects(['motto.txt', '云上座右铭.txt'])


# 确认Object已经被删除了
assert not bucket.object_exists('motto.txt')


# 获取不存在的文件会抛出oss2.exceptions.NoSuchKey异常
try:
    bucket.get_object('云上座右铭.txt')
except oss2.exceptions.NoSuchKey as e:
    print(u'已经被删除了：request_id={0}'.format(e.request_id))
else:
    assert False

# 清除本地文件
os.remove(u'本地文件名.txt')
os.remove(u'本地座右铭.txt')
