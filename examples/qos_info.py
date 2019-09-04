# -*- coding: utf-8 -*-

import os
import oss2
from oss2.models import BucketQosInfo

# 以下代码展示User以及Bucket的QoSInfo的操作示例

# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你要请求的Bucket名称>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')

# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param

# 以下代码展示user qos info的get操作示例
# 获取user qos info
service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), endpoint)
user_qos_info = service.get_user_qos_info()
print('===Get user qos info===')
print('region:', user_qos_info.region)
print('total_upload_bw:', user_qos_info.total_upload_bw)
print('intranet_upload_bw:', user_qos_info.intranet_upload_bw)
print('extranet_upload_bw:', user_qos_info.extranet_upload_bw)
print('total_download_bw:', user_qos_info.total_download_bw)
print('intranet_download_bw:', user_qos_info.intranet_download_bw)
print('extranet_download_bw:', user_qos_info.extranet_download_bw)
print('total_qps:', user_qos_info.total_qps)
print('intranet_qps:', user_qos_info.intranet_qps)
print('extranet_qps:', user_qos_info.extranet_qps)

# 以下代码展示bucket qos info的put get delete操作示例
# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# 创建BucketQosInfo对象, -1表示不做单独限制, 带宽单位为Gbps，具体设置规则请参考官网文档
bucket_qos_info = BucketQosInfo(
                    total_upload_bw = -1,
                    intranet_upload_bw = 2,
                    extranet_upload_bw = 2,
                    total_download_bw = -1,
                    intranet_download_bw = -1,
                    extranet_download_bw = -1,
                    total_qps = -1,
                    intranet_qps = -1,
                    extranet_qps = -1)

# 设置bucket qos info
result = bucket.put_bucket_qos_info(bucket_qos_info)
print('http response status:', result.status)

# 获取bucket qos info
bucket_qos_info = bucket.get_bucket_qos_info()
print('===Get bucket qos info===')
print('total_upload_bw:', bucket_qos_info.total_upload_bw)
print('intranet_upload_bw:', bucket_qos_info.intranet_upload_bw)
print('extranet_upload_bw:', bucket_qos_info.extranet_upload_bw)
print('total_download_bw:', bucket_qos_info.total_download_bw)
print('intranet_download_bw:', bucket_qos_info.intranet_download_bw)
print('extranet_download_bw:', bucket_qos_info.extranet_download_bw)
print('total_qps:', bucket_qos_info.total_qps)
print('intranet_qps:', bucket_qos_info.intranet_qps)
print('extranet_qps:', bucket_qos_info.extranet_qps)

# 删除bucket qos info配置
result = bucket.delete_bucket_qos_info()
print('http response status:', result.status)