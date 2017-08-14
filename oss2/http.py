# -*- coding: utf-8 -*-

"""
oss2.http
~~~~~~~~
This is the HTTP Adapters for requests library. So that the dependency of request library is totally transparent to the SDK caller.
It has the wrapper class `Session` 、 `Request` 、`Response`  for its counterparts in the requests library.
"""

import platform

import requests
from requests.structures import CaseInsensitiveDict

from . import __version__, defaults
from .compat import to_bytes
from .exceptions import RequestError
from .utils import file_object_remaining_bytes, SizedFileAdapter


_USER_AGENT = 'aliyun-sdk-python/{0}({1}/{2}/{3};{4})'.format(
    __version__, platform.system(), platform.release(), platform.machine(), platform.python_version())


class Session(object):
    """Requests of the same session share the same connection pool and possiblly same HTTP connectoin."""
    def __init__(self):
        self.session = requests.Session()

        psize = defaults.connection_pool_size
        self.session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=psize, pool_maxsize=psize))
        self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=psize, pool_maxsize=psize))

    def do_request(self, req, timeout):
        try:
            return Response(self.session.request(req.method, req.url,
                                                 data=req.data,
                                                 params=req.params,
                                                 headers=req.headers,
                                                 stream=True,
                                                 timeout=timeout))
        except requests.RequestException as e:
            raise RequestError(e)


class Request(object):
    def __init__(self, method, url,
                 data=None,
                 params=None,
                 headers=None,
                 app_name=''):
        self.method = method
        self.url = url
        self.data = _convert_request_body(data)
        self.params = params or {}

        if not isinstance(headers, CaseInsensitiveDict):
            self.headers = CaseInsensitiveDict(headers)
        else:
            self.headers = headers

        # tell requests not to add 'Accept-Encoding: gzip, deflate' by default
        if 'Accept-Encoding' not in self.headers:
            self.headers['Accept-Encoding'] = None

        if 'User-Agent' not in self.headers:
            if app_name:
                self.headers['User-Agent'] = _USER_AGENT + '/' + app_name
            else:
                self.headers['User-Agent'] = _USER_AGENT


_CHUNK_SIZE = 8 * 1024


class Response(object):
    def __init__(self, response):
        self.response = response
        self.status = response.status_code
        self.headers = response.headers

    def read(self, amt=None):
        if amt is None:
            content_list = []
            for chunk in self.response.iter_content(_CHUNK_SIZE):
                content_list.append(chunk)
            return b''.join(content_list)
        else:
            try:
                return next(self.response.iter_content(amt))
            except StopIteration:
                return b''

    def __iter__(self):
        return self.response.iter_content(_CHUNK_SIZE)


# TODOTODO
# requests对于具有fileno()方法的file object，会用fileno()的返回值作为Content-Length。
# 这对于已经读取了部分内容，或执行了seek()的file object是不正确的。
#
# _convert_request_body()对于支持seek()和tell() file object，确保是从
# 当前位置读取，且只读取当前位置到文件结束的内容。
def _convert_request_body(data):
    data = to_bytes(data)

    if hasattr(data, '__len__'):
        return data

    if hasattr(data, 'seek') and hasattr(data, 'tell'):
        return SizedFileAdapter(data, file_object_remaining_bytes(data))

    return data


