# -*- coding: utf-8 -*-

import os

import oss


# 该文件展示了一些和文件相关的高级用法，如设置用户自定义元数据、拷贝文件、追加上传等。


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


# 上传时携带自定义元数据
# 自定义元数据通过以x-oss-meta-开头的HTTP Header来设置
bucket.put_object('quote.txt', "Anything you're good at contributes to happiness.",
                  headers={'x-oss-meta-author': 'Bertrand Russell'})

# 查看自定义元数据
result = bucket.head_object('quote.txt')
assert result.headers['x-oss-meta-author'] == 'Bertrand Russell'


# 有些文件可以进行追加写，比如日志文件
# 先删除可能存在的文件，即使不存在，也不会报错
bucket.delete_object('logging.txt')

# 创建可追加文件，首次偏移（position）设为0
result = bucket.append_object('logging.txt', 0, 'Hello OSS!\n')

# 追加一行数据，偏移可以从上次响应中获得。
# 当然，也可以通过head_object()获得当前长度，作为偏移，只是比较低效。
bucket.append_object('logging.txt', result.next_position, 'Hello Guys!\n')

