
import os
import oss2
from oss2.models import (RestoreJobParameters,
                         RestoreConfiguration,
                         RESTORE_TIER_EXPEDITED,
                         RESTORE_TIER_STANDARD,
                         RESTORE_TIER_BULK)

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


# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

object_name = "<yourObjectName>"
# 解冻归档文件
bucket.restore_object(object_name)

# 解冻冷归档文件
# 如需上传文件的同时指定文件的存储类型为冷归档类型，请参考以下代码。
# bucket.put_object(object_name, '<yourContent>', headers={"x-oss-storage-class": oss2.BUCKET_STORAGE_CLASS_COLD_ARCHIVE})

# 指定解冻ColdArchive（冷归档）类型文件的优先级。
# RESTORE_TIER_EXPEDITED: 1个小时之内解冻完成。
# RESTORE_TIER_STANDARD: 2~5小时之内解冻完成。
# RESTORE_TIER_BULK: 5~12小时之内解冻完成。
job_parameters = RestoreJobParameters(RESTORE_TIER_STANDARD)

# 配置解冻参数，以设置5小时内解冻完成，解冻状态保持2天为例。
# days表示解冻之后保持解冻状态的天数，默认为1天，此参数适用于解冻Archive与ColdArchive类型文件。
# job_parameters表示解冻优先级配置，此参数只适用于解冻ColdArchive类型的文件。
restore_config= RestoreConfiguration(days=2, job_parameters=job_parameters)

# 发起解冻请求。
bucket.restore_object(object_name, input=restore_config)