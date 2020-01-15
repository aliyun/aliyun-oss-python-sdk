# -*- coding: utf-8 -*-

import oss2
import os
from oss2.models import (InventoryConfiguration,
                        InventoryFilter, 
                        InventorySchedule, 
                        InventoryDestination, 
                        InventoryBucketDestination, 
                        InventoryServerSideEncryptionKMS,
                        InventoryServerSideEncryptionOSS,
                        INVENTORY_INCLUDED_OBJECT_VERSIONS_CURRENT,
                        INVENTORY_INCLUDED_OBJECT_VERSIONS_ALL,
                        INVENTORY_FREQUENCY_DAILY,
                        INVENTORY_FREQUENCY_WEEKLY,
                        INVENTORY_FORMAT_CSV,
                        FIELD_SIZE,
                        FIELD_LAST_MODIFIED_DATE,
                        FIELD_STORAG_CLASS,
                        FIELD_ETAG,
                        FIELD_IS_MULTIPART_UPLOADED,
                        FIELD_ENCRYPTION_STATUS)

# 以下代码展示了bucket_inventory相关API的用法，

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

account_id = '<yourtBucketDestinationAccountId>'
role_arn = '<yourBucketDestinationRoleArn>'
dest_bucket_name = '<yourBucketDestinationName>'

# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint, account_id, role_arn, dest_bucket_name):
    assert '<' not in param, '请设置参数：' + param

# 打印清单配置
def print_inventory_configuration(configuration):
    print('======inventory configuration======')
    print('inventory_id', configuration.inventory_id)
    print('is_enabled', configuration.is_enabled)
    print('frequency', configuration.inventory_schedule.frequency)
    print('included_object_versions', configuration.included_object_versions)
    print('inventory_filter prefix', configuration.inventory_filter.prefix)
    print('fields', configuration.optional_fields)
    bucket_destin = configuration.inventory_destination.bucket_destination
    print('===bucket destination===')
    print('account_id', bucket_destin.account_id)
    print('role_arn', bucket_destin.role_arn)
    print('bucket', bucket_destin.bucket)
    print('format', bucket_destin.inventory_format)
    print('destination prefix', bucket_destin.prefix)
    if bucket_destin.sse_kms_encryption is not None:
        print('server side encryption by kms, key id:', bucket_destin.sse_kms_encryption.key_id)
    elif bucket_destin.sse_oss_encryption is not None:
        print('server side encryption by oss.')

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# 创建清单配置
inventory_id = "test-config-id"
optional_fields = [FIELD_SIZE, FIELD_LAST_MODIFIED_DATE, FIELD_STORAG_CLASS,
        FIELD_ETAG, FIELD_IS_MULTIPART_UPLOADED, FIELD_ENCRYPTION_STATUS]

# 设置清单bucket目的地信息。
bucket_destination = InventoryBucketDestination(
        # 目的地bucket的用户account_id。
        account_id=account_id, 
        # 目的地bucket的role_arn。
        role_arn=role_arn,
        # 目的地bucket的名称。
        bucket=dest_bucket_name,
        # 清单格式。
        inventory_format=INVENTORY_FORMAT_CSV,
        # 清单结果的存储路径前缀
        prefix='store-prefix',
        # 如果需要使用kms加密清单可以参考以下代码
        # sse_kms_encryption=InventoryServerSideEncryptionKMS("test-kms-id")
        # 如果需要使用OSS服务端加密清单可以参考以下代码
        # sse_oss_encryption=InventoryServerSideEncryptionOSS()
        )

# 创建清单配置。
inventory_configuration = InventoryConfiguration(
        # 清单的配置id。
        inventory_id=inventory_id,
        # 是否生效。
        is_enabled=True, 
        # 生成清单的计划。
        inventory_schedule=InventorySchedule(frequency=INVENTORY_FREQUENCY_DAILY),
        # 设置清单中包含的object的版本为当前版本。如果设置为INVENTORY_INCLUDED_OBJECT_VERSIONS_ALL则为所有版本，多版本环境生效。
        included_object_versions=INVENTORY_INCLUDED_OBJECT_VERSIONS_CURRENT,
        # 设置清单清筛选object的前缀。
        inventory_filter=InventoryFilter(prefix="obj-prefix"),
        # 设置清单中包含的object属性。
        optional_fields=optional_fields,
        # 设置清单的接收目的地配置。
        inventory_destination=InventoryDestination(bucket_destination=bucket_destination))

# 设置清单配置
bucket.put_bucket_inventory_configuration(inventory_configuration)

# 获取清单配置
result = bucket.get_bucket_inventory_configuration(inventory_id = inventory_id);
print_inventory_configuration(result)

# 罗列清单配置
# 如果存在超过100条配置，罗列结果将会分页，分页信息保存在 
# class:`ListInventoryConfigurationResult <oss2.models.ListInventoryConfigurationResult>`中。
result = bucket.list_bucket_inventory_configurations()
print('========list result=======')
print('is truncated', result.is_truncated)
print('continuaiton_token', result.continuaiton_token)
print('next_continuation_token', result.next_continuation_token)
for inventory_config in result.inventory_configurations:
    print_inventory_configuration(inventory_config)
    bucket.delete_bucket_inventory_configuration(inventory_config.id)

# 删除清单配置
bucket.delete_bucket_inventory_configuration(inventory_id)