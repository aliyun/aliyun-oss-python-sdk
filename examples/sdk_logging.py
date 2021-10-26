
import os
import oss2
import logging
from itertools import islice

# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
#
# 以杭州区域为例，Endpoint可以是：
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com


access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param


# 为方便追查问题，Python SDK提供了日志记录功能，该功能默认处于关闭状态。
# Python SDK日志记录功能可以收集定位各类OSS操作的日志信息，并以日志文件的形式存储在本地。
# 日志级别：CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
# 下载日志信息到本地日志文件，并保存到指定的本地路径中。
# 如果未指定本地路径只填写了本地日志文件名称（例如examplelogfile.log），则下载后的文件默认保存到示例程序所属项目对应本地路径中。
log_file_path = "D:\\localpath\\examplelogfile.log"

# 开启日志。
oss2.set_file_logger(log_file_path, 'oss2', logging.INFO)
# 阿里云账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM用户进行API访问或日常运维，请登录RAM控制台创建RAM用户。
auth = oss2.Auth('yourAccessKeyId', 'yourAccessKeySecret')
# yourEndpoint填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
# 填写Bucket名称，例如examplebucket。
bucket = oss2.Bucket(auth, 'yourEndpoint', 'examplebucket')

# 遍历文件目录。
for b in islice(oss2.ObjectIterator(bucket), 10):
    print(b.key)
# 获取文件元信息。
# 填写Object完整路径，例如exampledir/exampleobject.txt。Object完整路径中不能包含Bucket名称。
object_meta = bucket.get_object_meta('exampledir/exampleobject.txt')