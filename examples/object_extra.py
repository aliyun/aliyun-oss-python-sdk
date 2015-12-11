# -*- coding: utf-8 -*-

import os
from datetime import datetime

import oss2


# 以下代码展示了一些和文件相关的高级用法，如中文、设置用户自定义元数据、拷贝文件、追加上传等。


# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param


# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)


# Object名、前缀名等等参数可以直接用str类型（即Python2的bytes，Python3的unicode）
# 文件内容原则上只接受bytes类型。如果用户提供了unicode类型，则转换为UTF-8编码的bytes
bucket.put_object('中文文件名.txt', '中文内容')


# 上传时携带自定义元数据
# 自定义元数据通过以x-oss-meta-开头的HTTP Header来设置
result = bucket.put_object('quote.txt', "Anything you're good at contributes to happiness.",
                           headers={'x-oss-meta-author': 'Russell'})

# 几乎所有的result都是RequestResult的子类，携带了一些必要的信息，可以用来调试等；
# 向阿里云客服提交工单时，能够提供request id，可以极大的方便问题的排查。
print('http-status={0} request-id={1}'.format(result.status, result.request_id))


# 修改自定义元数据
bucket.update_object_meta('quote.txt', {'x-oss-meta-author': 'Bertrand Russell'})

# 查看自定义元数据
result = bucket.head_object('quote.txt')
assert result.headers['x-oss-meta-author'] == 'Bertrand Russell'

# 也可以查看长度，最后修改时间等
print(result.content_length)
print(datetime.fromtimestamp(result.last_modified))


# 拷贝Object（适用于小文件）。这里是把quote.txt拷贝成quote-backup.txt
bucket.copy_object(bucket.bucket_name, 'quote.txt', 'quote-backup.txt')


# 有些文件可以进行追加写，比如日志文件
# 先删除可能存在的文件，即使不存在，也不会报错
bucket.delete_object('logging.txt')

# 创建可追加文件，首次偏移（position）设为0
result = bucket.append_object('logging.txt', 0, 'Hello OSS!\n')

# 追加一行数据，偏移可以从上次响应中获得。
# 当然，也可以通过head_object()获得当前长度作为偏移，只是比较低效。
bucket.append_object('logging.txt', result.next_position, 'Hello Guys!\n')

