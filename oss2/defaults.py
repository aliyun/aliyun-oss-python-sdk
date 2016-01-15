# -*- coding: utf-8 -*-

"""
oss2.defaults
~~~~~~~~~~~~~

全局缺省变量。

"""


def get(value, default_value):
    if value is None:
        return default_value
    else:
        return value


#: 连接超时时间
connect_timeout = 60

#: 缺省重试次数
request_retries = 3

#: 对于某些接口，上传数据长度大于或等于该值时，就采用分片上传。
multipart_threshold = 10 * 1024 * 1024

#: 缺省分片大小
part_size = 10 * 1024 * 1024