# -*- coding: utf-8 -*-

"""
oss2.http
~~~~~~~~

这个模块包含了HTTP Adapters。尽管OSS Python SDK内部使用requests库进行HTTP通信，但是对使用者是透明的。
该模块中的 `Session` 、 `Request` 、`Response` 对requests的对应的类做了简单的封装。
"""

import requests
import platform

from . import __version__
from .compat import to_bytes

from requests.structures import CaseInsensitiveDict
from email.utils import formatdate


_USER_AGENT = 'aliyun-sdk-python/{0} ({1}/{2}/{3};{4})'.format(
    __version__, platform.system(), platform.release(), platform.machine(), platform.python_version())


class Session(object):
    """属于同一个Session的请求共享一组连接池，如有可能也会重用HTTP连接。"""
    def __init__(self):
        self.session = requests.Session()

    def do_request(self, req, timeout):
        return Response(self.session.request(req.method, req.url,
                                             data=req.data,
                                             params=req.params,
                                             headers=req.headers,
                                             stream=True,
                                             timeout=timeout))


class Request(object):
    def __init__(self, method, url,
                 data=None,
                 params=None,
                 headers=None):
        self.method = method
        self.url = url
        self.data = to_bytes(data)
        self.params = params or {}

        if not isinstance(headers, CaseInsensitiveDict):
            self.headers = CaseInsensitiveDict(headers)
        else:
            self.headers = headers

        # tell requests not to add 'Accept-Encoding: gzip, deflate' by default
        if 'Accept-Encoding' not in self.headers:
            self.headers['Accept-Encoding'] = None

        if 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = _USER_AGENT


_CHUNK_SIZE = 8 * 1024


class Response(object):
    def __init__(self, response):
        self.response = response
        self.status = response.status_code
        self.headers = response.headers

    def read(self, amt=None):
        if amt is None:
            content = b''
            for chunk in self.response.iter_content(_CHUNK_SIZE):
                content += chunk
            return content
        else:
            try:
                return next(self.response.iter_content(amt))
            except StopIteration:
                return b''

    def __iter__(self):
        return self.response.iter_content(_CHUNK_SIZE)


def http_date(timeval=None):
    """返回符合HTTP标准的GMT时间字符串，用strftime的格式表示就是"%a, %d %b %Y %H:%M:%S GMT"。
    但不能使用strftime，因为strftime的结果是和locale相关的。
    """
    return formatdate(timeval, usegmt=True)
