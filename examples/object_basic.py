# -*- coding: utf-8 -*-

import os
import shutil

import oss


# 该文件展示了基本的文件上传、下载、罗列、删除用法。


# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真是的AccessKeyId等。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param


# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss.Bucket(oss.Auth(access_key_id, access_key_secret), endpoint, bucket_name)


# 上传一段字符串。Object名是motto.txt，内容是一段名言。
bucket.put_object('motto.txt', 'Never give up. - Jack Ma')


# 把刚刚上传的Object下载到本地文件 “座右铭.txt” 中
# 因为get_object()方法返回的是一个file-like object，所以我们可以直接用shutil.copyfileobj()做拷贝
with open('座右铭.txt', 'wb') as f:
    shutil.copyfileobj(bucket.get_object('motto.txt'), f)


# 把本地文件 “座右铭.txt” 上传到OSS，新的Object叫做 “我的座右铭.txt”
# 注意到，这次put_object()的第二个参数是file object；而上次上传是一个字符串。
# put_object()能够识别不同的参数类型
with open('座右铭.txt', 'rb') as f:
    bucket.put_object('我的座右铭.txt', f)


# 列举Bucket下10个Object，并打印它们的最后修改时间、文件名
for i, object_info in enumerate(oss.iterators.ObjectIterator(bucket)):
    print("{0} {1}".format(object_info.last_modified, object_info.name))

    if i >= 9:
        break


# 删除名为motto.txt的Object
bucket.delete_object('motto.txt')

# 也可以批量删除
# 注意：重复删除motto.txt，并不会报错
bucket.batch_delete_objects(['motto.txt', '我的座右铭.txt'])


# 确认Object已经被删除了
assert not bucket.object_exists('motto.txt')


# 获取不存在的文件会抛出oss.exceptions.NoSuchKey异常
try:
    bucket.get_object('我的座右铭.txt')
except oss.exceptions.NoSuchKey:
    print('已经被删除了')
else:
    assert False