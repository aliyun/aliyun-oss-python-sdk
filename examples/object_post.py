# -*- coding: utf-8 -*-

import time
import datetime
import json
import base64
import hmac
import hashlib
import os
import crcmod
import requests


# 以下代码展示了PostObject的用法。PostObject不依赖于OSS Python SDK。

# POST表单域的详细说明请参RFC2388 https://tools.ietf.org/html/rfc2388
# PostObject的官网 https://help.aliyun.com/document_detail/31988.html
# PostObject错误及排查 https://yq.aliyun.com/articles/58524

# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的访问域名>')

# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param

def calculate_crc64(data):
    """计算文件的MD5
    :param data: 数据
    :return 数据的MD5值
    """
    _POLY = 0x142F0E1EBA9EA3693
    _XOROUT = 0XFFFFFFFFFFFFFFFF
    
    crc64 = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
    crc64.update(data)

    return crc64.crcValue

def build_gmt_expired_time(expire_time):
    """生成GMT格式的请求超时时间
    :param int expire_time: 超时时间，单位秒
    :return str GMT格式的超时时间
    """
    now = int(time.time())
    expire_syncpoint  = now + expire_time
    
    expire_gmt = datetime.datetime.fromtimestamp(expire_syncpoint).isoformat()
    expire_gmt += 'Z'
    
    return expire_gmt

def build_encode_policy(expired_time, condition_list):
    """生成policy
    :param int expired_time: 超时时间，单位秒
    :param list condition_list: 限制条件列表
    """ 
    policy_dict = {}
    policy_dict['expiration'] = build_gmt_expired_time(expired_time)
    policy_dict['conditions'] = condition_list
    
    policy = json.dumps(policy_dict).strip()
    policy_encode = base64.b64encode(policy)
    
    return policy_encode

def build_signature(access_key_secret, encode_policy):
    """生成签名
    :param str access_key_secret: access key secret
    :param str encode_policy: 编码后的Policy
    :return str 请求签名
    """
    h = hmac.new(access_key_secret, encode_policy, hashlib.sha1)
    signature = base64.encodestring(h.digest()).strip()
    return signature

def bulid_callback(cb_url, cb_body, cb_body_type=None, cb_host=None):
    """生成callback字符串
    :param str cb_url: 回调服务器地址，文件上传成功后OSS向此url发送回调请求
    :param str cb_body: 发起回调请求的Content-Type，默认application/x-www-form-urlencoded
    :param str cb_body_type: 发起回调时请求body
    :param str cb_host: 发起回调请求时Host头的值
    :return str 编码后的Callback
    """
    callback_dict = {}
    
    callback_dict['callbackUrl'] = cb_url
    
    callback_dict['callbackBody'] = cb_body
    if cb_body_type is None:
        callback_dict['callbackBodyType'] = 'application/x-www-form-urlencoded'
    else:
        callback_dict['callbackBodyType'] = cb_body_type
    
    if cb_host is not None:
        callback_dict['callbackHost'] = cb_host
        
    callback_param = json.dumps(callback_dict).strip()
    base64_callback = base64.b64encode(callback_param);
    
    return base64_callback

def build_post_url(endpoint, bucket_name):
    """生成POST请求URL
    :param str endpoint: endpoint
    :param str bucket_name: bucket name
    :return str POST请求URL
    """
    if endpoint.startswith('http://'):
        return endpoint.replace('http://', 'http://{0}.'.format(bucket_name))
    elif endpoint.startswith('https://'):
        return endpoint.replace('https://', 'https://{0}.'.format(bucket_name))
    else:
        return 'http://{0}.{1}'.format(bucket_name, endpoint)

def build_post_body(field_dict, boundary):
    """生成POST请求Body
    :param dict field_dict: POST请求表单域
    :param str boundary: 表单域的边界字符串
    :return str POST请求Body
    """
    post_body = b''

    # 编码表单域
    for k,v in field_dict.iteritems():
        if k != 'content' and k != 'content-type':
            post_body += '''--{0}\r\nContent-Disposition: form-data; name=\"{1}\"\r\n\r\n{2}\r\n'''.format(boundary, k, v)
    
    # 上传文件的内容，必须作为最后一个表单域
    post_body += '''--{0}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{1}\"\r\nContent-Type: {2}\r\n\r\n{3}'''.format(
    boundary, field_dict['key'], field_dict['content-type'], field_dict['content'])
    
    # 加上表单域结束符
    post_body += '\r\n--{0}--\r\n'.format(boundary)

    return post_body

def build_post_headers(body_len, boundary, headers=None):
    """生气POST请求Header
    :param str body_len: POST请求Body长度
    :param str boundary: 表单域的边界字符串
    :param dict 请求Header
    """
    headers = headers if headers else {}
    headers['Content-Length'] = str(body_len)
    headers['Content-Type'] = 'multipart/form-data; boundary={0}'.format(boundary)

    return headers


# POST请求表单域，注意大小写
field_dict = {}
# object名称
field_dict['key'] = 'post.txt'
# access key id
field_dict['OSSAccessKeyId'] = access_key_id
# Policy包括超时时间(单位秒)和限制条件condition
field_dict['policy'] = build_encode_policy(120, [['eq','$bucket', bucket_name],
                                                 ['content-length-range', 0, 104857600]])
# 请求签名
field_dict['Signature'] = build_signature(access_key_secret, field_dict['policy']) 
# 临时用户Token，当使用临时用户密钥时Token必填；非临时用户填空或不填
field_dict['x-oss-security-token'] = ''
# Content-Disposition
field_dict['Content-Disposition'] = 'attachment;filename=download.txt'
# 用户自定义meta
field_dict['x-oss-meta-uuid'] = 'uuid-xxx'
# callback，没有回调需求不填该域
field_dict['callback'] = bulid_callback('http://oss-demo.aliyuncs.com:23450',
                                        'filename=${object}&size=${size}&mimeType=${mimeType}',
                                        'application/x-www-form-urlencoded') 
# callback中的自定义变量，没有回调不填该域
field_dict['x:var1'] = 'callback-var1-val'
# 上传文件内容
field_dict['content'] = 'a'*64
# 上传文件类型
field_dict['content-type'] = 'text/plain'

# 表单域的边界字符串，一般为随机字符串
boundary = '9431149156168'

# 发送POST请求
body = build_post_body(field_dict, boundary)
headers = build_post_headers(len(body), boundary)

resp = requests.post(build_post_url(endpoint, bucket_name),
                     data=body,
                     headers=headers)

# 确认请求结果
assert resp.status_code == 200
assert resp.content == '{"Status":"OK"}'
assert resp.headers['x-oss-hash-crc64ecma'] == str(calculate_crc64(field_dict['content']))
