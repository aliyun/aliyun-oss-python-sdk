# -*- coding: utf-8 -*-

import oss2
import os
from oss2.models import (InventoryConfiguration,
                        InventoryFilter, 
                        InventorySchedule, 
                        InventoryDestination, 
                        InventoryBucketDestination, 
                        InventoryServerSideEncryptionKMS,
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
    print('prefix', bucket_destin.prefix)
    if bucket_destin.sse_kms_encryption is not None:
        print('kms key id', bucket_destin.sse_kms_encryption.key_id)

# 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

# 创建清单配置
inventory_id = "test-config-id"
optional_fields = [FIELD_SIZE, FIELD_LAST_MODIFIED_DATE, FIELD_STORAG_CLASS,
        FIELD_ETAG, FIELD_IS_MULTIPART_UPLOADED, FIELD_ENCRYPTION_STATUS]

bucket_destination = InventoryBucketDestination(
        account_id=account_id, 
        role_arn=role_arn,
        bucket=dest_bucket_name,
        inventory_format=INVENTORY_FORMAT_CSV,
        prefix="test-",
        sse_kms_encryption=InventoryServerSideEncryptionKMS("test-kms-id"))

inventory_configuration = InventoryConfiguration(
        inventory_id=inventory_id,
        is_enabled=True, 
        inventory_schedule=InventorySchedule(frequency=INVENTORY_FREQUENCY_DAILY),
        included_object_versions=INVENTORY_INCLUDED_OBJECT_VERSIONS_CURRENT,
        inventory_filter=InventoryFilter(prefix="inv-prefix"),
        optional_fields=optional_fields,
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