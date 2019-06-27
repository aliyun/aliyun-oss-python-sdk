# -*- coding: utf-8 -*-

import os
import oss2
from oss2.models import (ConditionInlcudeHeader, 
                        Condition, 
                        Redirect, 
                        RedirectMirrorHeaders,
                        MirrorHeadersSet, 
                        RoutingRule, 
                        BucketWebsite,
                        REDIRECT_TYPE_MIRROR,
                        REDIRECT_TYPE_EXTERNAL,
                        REDIRECT_TYPE_ALICDN,
                        REDIRECT_TYPE_INTERNAL)

# 以下代码展示了设置静态网站托管的相关操作


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

index_file = 'index.html'
error_file = 'error.html'
# 以下代码展示只设置主页与404页面的静态网站托管
bucket.put_bucket_website(BucketWebsite(index_file, error_file))

# 获取website配置
result = bucket.get_bucket_website()
print('get_bucket_website without redirect:')
print('result index_file:', result.index_file)
print('result error_file:', result.error_file)

bucket.delete_bucket_website()

# 以下代码展示镜像回源的网站托管配置，采用主备模式或者多站点模式
# 设置匹配规则
include_header1= ConditionInlcudeHeader('host', 'test.oss-cn-beijing-internal.aliyuncs.com')
include_header2 = ConditionInlcudeHeader('host', 'test.oss-cn-shenzhen-internal.aliyuncs.com')
condition1 = Condition(key_prefix_equals='key1', 
                    http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])
condition2 = Condition(key_prefix_equals='key2', 
                    http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])

# 设置跳转规则，
mirror_headers_set_1 = MirrorHeadersSet("myheader-key5","myheader-value5")
mirror_headers_set_2 = MirrorHeadersSet("myheader-key6","myheader-value6")
set_list = [mirror_headers_set_1, mirror_headers_set_2]
pass_list = ['myheader-key1', 'myheader-key2']
remove_list = ['myheader-key3', 'myheader-key4']
mirror_header = RedirectMirrorHeaders(pass_all=True, pass_list=pass_list, remove_list=remove_list, set_list=set_list)

# 使用主备源站模式, 使用mirror_url_slave，mirror_url_probe参数
redirect1 = Redirect(redirect_type=REDIRECT_TYPE_MIRROR, pass_query_string=False, mirror_url='http://www.test.com/', 
                mirror_url_slave='http://www.slave.com/', mirror_url_probe='http://www.test.com/index.html', mirror_pass_query_string=False, 
                mirror_follow_redirect=True, mirror_check_md5=True, mirror_headers=mirror_header)

# 不指定备站
redirect2 = Redirect(redirect_type=REDIRECT_TYPE_MIRROR, mirror_url='http://www.test.com/',
                mirror_pass_query_string=True, mirror_follow_redirect=True, mirror_check_md5=False)

# 可以设置一条或多条，本示例展示设置多条
rule1 = RoutingRule(rule_num=1, condition=condition1, redirect=redirect1)
rule2 = RoutingRule(rule_num=2, condition=condition2, redirect=redirect2)
website_set = BucketWebsite(index_file, error_file, [rule1, rule2])
bucket.put_bucket_website(website_set)

# 获取website配置
website_get = bucket.get_bucket_website()
print('get_bucket_website mirror type:')
print('indext_file:', website_get.index_file)
print('error_file:', website_get.error_file)
print('rule sum:', len(website_get.rules))

bucket.delete_bucket_website()  

# 以下代码展示阿里云CDN跳转以及外部跳转或者内部跳转的设置
include_header1= ConditionInlcudeHeader('host', 'test.oss-cn-beijing-internal.aliyuncs.com')
include_header2 = ConditionInlcudeHeader('host', 'test.oss-cn-shenzhen-internal.aliyuncs.com')
condition1 = Condition(key_prefix_equals='key3', 
                    http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])
condition2 = Condition(key_prefix_equals='key4', 
                    http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])
condition3 = Condition(key_prefix_equals='key5',
                    http_err_code_return_equals=404, include_header_list=[include_header1, include_header2])

# AliCDN 
redirect1 = Redirect(redirect_type=REDIRECT_TYPE_ALICDN, pass_query_string=True,  
                replace_key_with='${key}.suffix', proto='http', http_redirect_code=302)

# External
redirect2 = Redirect(redirect_type=REDIRECT_TYPE_EXTERNAL, pass_query_string=False, replace_key_prefix_with='abc', 
                proto='https', host_name='oss.aliyuncs.com', http_redirect_code=302)

# Internal
redirect3 = Redirect(redirect_type=REDIRECT_TYPE_INTERNAL, pass_query_string=False, replace_key_with='${key}.suffix')

# 可以设置一条或多条规则，本示例展示设置多条
rule1 = RoutingRule(rule_num=1, condition=condition1, redirect=redirect1)
rule2 = RoutingRule(rule_num=2, condition=condition2, redirect=redirect2)
rule3 = RoutingRule(rule_num=3, condition=condition3, redirect=redirect3)
website_set = BucketWebsite(index_file, error_file, [rule1, rule2, rule3])
bucket.put_bucket_website(website_set)

# 获取website配置
website_get = bucket.get_bucket_website()
print('get_bucket_website other type:')
print('indext_file:', website_get.index_file)
print('error_file:', website_get.error_file)
print('rule sum:', len(website_get.rules))
for rule in website_get.rules:
    print('rule_num:{}, redirect_type:{}'.format(rule.rule_num, rule.redirect.redirect_type))

bucket.delete_bucket_website()  