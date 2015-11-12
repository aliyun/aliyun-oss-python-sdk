# -*- coding: utf-8 -*-

"""
兼容Python版本
"""

import sys

is_py2 = (sys.version_info[0] == 2)
is_py3 = (sys.version_info[0] == 3)

if is_py2:
    from urllib import quote as urlquote, unquote as urlunquote
    from urlparse import urlparse


    def to_bytes(data):
        """若输入为unicode， 则转为utf-8编码的bytes；其他则原样返回。"""
        if isinstance(data, unicode):
            return data.encode(encoding='utf-8')
        else:
            return data

    def to_string(data):
        """把输入转换为str对象"""
        return to_bytes(data)

    builtin_str = str
    bytes = str
    str = unicode


elif is_py3:
    from urllib.parse import quote as urlquote, unquote as urlunquote
    from urllib.parse import urlparse

    def to_bytes(data):
        """若输入为str（即unicode），则转为utf-8编码的bytes；其他则原样返回"""
        if isinstance(data, str):
            return data.encode(encoding='utf-8')
        else:
            return data

    def to_string(data):
        """若输入为bytes，则认为是utf-8编码，并返回str"""
        if isinstance(data, str):
            return data
        else:
            return data.decode('utf-8')

    builtin_str = str
    bytes = bytes
    str = str