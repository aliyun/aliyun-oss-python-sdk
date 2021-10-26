
import os
import oss2
import datetime
from oss2.headers import OSS_OBJECT_TAGGING
from oss2.models import (LifecycleExpiration, LifecycleRule,
                         BucketLifecycle,AbortMultipartUpload,
                         TaggingRule, Tagging, StorageTransition)

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

# 简单上传时添加对象标签
# 填写Object完整路径，例如exampledir/exampleobject.txt。Object完整路径中不能包含Bucket名称。
object_name = 'exampledir/exampleobject.txt'

# 设置tagging字符串。
tagging = "k1=v1&k2=v2&k3=v3"

# 如果标签中包含了任意字符，则需要对标签的Key和Value做URL编码。
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# 在HTTP header中设置标签信息。
headers = dict()
headers[OSS_OBJECT_TAGGING] = tagging

# 调用put_object接口时指定headers，将会为上传的文件添加标签。
result = bucket.put_object(object_name, 'content', headers=headers)
print('http response status: ', result.status)

# 查看Object的标签信息。
result = bucket.get_object_tagging(object_name)
for key in result.tag_set.tagging_rule:
    print('tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))


# 追加上传时添加对象标签
# 设置tagging字符串。
tagging = "k1=v1&k2=v2&k3=v3"

# 如果标签中包含了任意字符，则需要对标签的Key和Value做URL编码。
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# 在HTTP header中设置标签信息。
headers = dict()
headers[OSS_OBJECT_TAGGING] = tagging

# 追加上传文件。调用append_object接口时指定headers，将会给文件设置标签。
# 只有第一次调用append_object设置的标签才会生效，后续使用此种方式添加的标签不生效。
result = bucket.append_object(object_name, 0, '<yourContent>', headers=headers)

# 查看Object的标签信息。
result = bucket.get_object_tagging(object_name)
for key in result.tag_set.tagging_rule:
    print('tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))


# 为已上传Object添加或更改对象标签
# 创建标签规则。
rule = TaggingRule()
rule.add('key1', 'value1')
rule.add('key2', 'value2')

# 创建标签。
tagging = Tagging(rule)

# 设置标签。
result = bucket.put_object_tagging(object_name, tagging)
# 查看HTTP返回码。
print('http response status:', result.status)


# 为Object指定版本添加或更改对象标签
# 填写Object的版本ID，例如CAEQMxiBgICAof2D0BYiIDJhMGE3N2M1YTI1NDQzOGY5NTkyNTI3MGYyMzJm****。
version_id = 'CAEQMxiBgICAof2D0BYiIDJhMGE3N2M1YTI1NDQzOGY5NTkyNTI3MGYyMzJm****'

tagging = Tagging()
# 依次填写对象标签的键（例如owner）和值（例如John）。
tagging.tag_set.add('owner', 'John')
tagging.tag_set.add('type', 'document')

params = dict()
params['versionId'] = version_id

bucket.put_object_tagging(object_name, tagging, params=params)


# 为软链接文件设置标签
# 填写软链接完整路径，例如shortcut/myobject.txt。
symlink_name = 'shortcut/myobject.txt'

# 设置tagging字符串。
tagging = "k1=v1&k2=v2&k3=v3"

# 如果标签中包含了任意字符，则需要对标签的Key和Value做URL编码。
k4 = "k4+-="
v4 = "+-=._:/"
tagging += "&" + oss2.urlquote(k4) + "=" + oss2.urlquote(v4)

# 在HTTP header中设置标签信息。
headers = dict()
headers[OSS_OBJECT_TAGGING] = tagging

# 添加软链接。
# 调用put_symlink接口时指定headers，将会给软链接文件添加标签。
result = bucket.put_symlink(object_name, symlink_name, headers=headers)
print('http response status: ', result.status)

# 查看软链接文件的标签信息。
result = bucket.get_object_tagging(symlink_name)
for key in result.tag_set.tagging_rule:
    print('tagging key: {}, value: {}'.format(key, result.tag_set.tagging_rule[key]))


# 生命周期规则中添加标签匹配规则
# 设置Object过期规则，距最后修改时间3天后过期。
# 设置过期规则名称和Object的匹配前缀。
rule1 = LifecycleRule('rule1', 'tests/',
                      # 启用过期规则。
                      status=LifecycleRule.ENABLED,
                      # 设置过期规则为距最后修改时间3天后过期。
                      expiration=LifecycleExpiration(days=3))

# 设置Object过期规则，指定日期之前创建的文件过期。
# 设置过期规则名称和Object的匹配前缀。
rule2 = LifecycleRule('rule2', 'logging-',
                      # 不启用过期规则。
                      status=LifecycleRule.DISABLED,
                      # 设置过期规则为指定日期之前创建的文件过期。
                      expiration=LifecycleExpiration(created_before_date=datetime.date(2018, 12, 12)))

# 设置分片过期规则，分片3天后过期。
rule3 = LifecycleRule('rule3', 'tests1/',
                      status=LifecycleRule.ENABLED,
                      abort_multipart_upload=AbortMultipartUpload(days=3))

# 设置分片过期规则，指定日期之前的分片过期。
rule4 = LifecycleRule('rule4', 'logging1-',
                      status=LifecycleRule.DISABLED,
                      abort_multipart_upload = AbortMultipartUpload(created_before_date=datetime.date(2018, 12, 12)))

# 设置Object的匹配标签。
tagging_rule = TaggingRule()
tagging_rule.add('key1', 'value1')
tagging_rule.add('key2', 'value2')
tagging = Tagging(tagging_rule)

# 设置转储规则，最后修改时间超过365天后转为归档存储（ARCHIVE）。
# rule5中指定了Object的匹配标签，只有同时拥有key1=value1和key2=value2两个标签的Object才会匹配此规则。
rule5 = LifecycleRule('rule5', 'logging2-',
                      status=LifecycleRule.ENABLED,
                      storage_transitions=[StorageTransition(days=365, storage_class=oss2.BUCKET_STORAGE_CLASS_ARCHIVE)],
                      tagging = tagging)

lifecycle = BucketLifecycle([rule1, rule2, rule3, rule4, rule5])
bucket.put_bucket_lifecycle(lifecycle)


# 查看生命周期规则中匹配的标签信息
# 查看生命周期规则。
lifecycle = bucket.get_bucket_lifecycle()

for rule in lifecycle.rules:
    # 查看分片过期规则。
    if rule.abort_multipart_upload is not None:
        print('id={0}, prefix={1}, tagging={2}, status={3}, days={4}, created_before_date={5}'
              .format(rule.id, rule.prefix, rule.tagging, rule.status,
                      rule.abort_multipart_upload.days,
                      rule.abort_multipart_upload.created_before_date))

    # 查看Object过期规则。
    if rule.expiration is not None:
        print('id={0}, prefix={1}, tagging={2}, status={3}, days={4}, created_before_date={5}'
              .format(rule.id, rule.prefix, rule.tagging, rule.status,
                      rule.expiration.days,
                      rule.expiration.created_before_date))
    # 查看转储规则。
    if len(rule.storage_transitions) > 0:
        storage_trans_info = ''
        for storage_rule in rule.storage_transitions:
            storage_trans_info += 'days={0}, created_before_date={1}, storage_class={2} **** '.format(
                storage_rule.days, storage_rule.created_before_date, storage_rule.storage_class)

        print('id={0}, prefix={1}, tagging={2}, status={3},, StorageTransition={4}'
              .format(rule.id, rule.prefix, rule.tagging, rule.status, storage_trans_info))