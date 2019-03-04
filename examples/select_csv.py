# -*- coding: utf-8 -*-

import os
import oss2


def select_call_back(consumed_bytes, total_bytes = None):
    print('Consumed Bytes:' + str(consumed_bytes) + '\n')
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
#objects = bucket.list_objects()
key = 'python_select.csv'
content = 'Tom Hanks,USA,45\r\n'*1024
filename = 'python_select.csv'

# 上传文件
bucket.put_object(key, content)

csv_meta_params = {'CsvHeaderInfo': 'None',
                'RecordDelimiter': '\r\n'}

select_csv_params = {'CsvHeaderInfo': 'None',
                'RecordDelimiter': '\r\n',
                'LineRange': (500, 1000)}

csv_header = bucket.create_select_object_meta(key, csv_meta_params)
print(csv_header.csv_rows)
print(csv_header.csv_splits)

result = bucket.select_object(key, "select * from ossobject where _3 > 44 limit 100000", select_call_back, select_csv_params)
content_got = b''
for chunk in result:
   content_got += chunk
print(content_got)
result = bucket.select_object_to_file(key, filename, 
        "select * from ossobject where _3 > 44 limit 100000", select_call_back, select_csv_params)

bucket.delete_object(key)