# -*- coding: utf-8 -*-

import sys

is_py2 = (sys.version_info[0] == 2)
is_py3 = (sys.version_info[0] == 3)

if is_py2:
    from urllib import quote as urlquote, unquote as urlunquote
    from urlparse import urlparse


    def to_bytes(data):
        if isinstance(data, unicode):
            return data.encode(encoding='utf-8')
        else:
            return data

    def to_string(data):
        if isinstance(data, str):
            return data
        else:
            return data.encode('utf-8')

    builtin_str = str
    bytes = str
    str = unicode


elif is_py3:
    from urllib.parse import quote as urlquote, unquote as urlunquote
    from urllib.parse import urlparse

    def to_bytes(data):
        if isinstance(data, str):
            return data.encode(encoding='utf-8')
        else:
            return data

    def to_string(data):
        if isinstance(data, str):
            return data
        else:
            return data.decode('utf-8')

    builtin_str = str
    bytes = bytes
    str = str