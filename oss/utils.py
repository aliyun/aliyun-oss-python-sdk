# -*- coding: utf-8 -*-

"""
oss.utils
---------

工具函数模块。
"""

import os.path
import mimetypes
import socket
import hashlib
import base64

from .compat import to_string, to_bytes

_EXTRA_TYPES_MAP = {
    ".js": "application/javascript",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xltx": "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
    ".potx": "application/vnd.openxmlformats-officedocument.presentationml.template",
    ".ppsx": "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".sldx": "application/vnd.openxmlformats-officedocument.presentationml.slide",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
    ".xlam": "application/vnd.ms-excel.addin.macroEnabled.12",
    ".xlsb": "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
    ".apk": "application/vnd.android.package-archive"
}


def b64encode_as_string(data):
    return to_string(base64.b64encode(data))


def content_md5(data):
    """计算data的MD5值，经过Base64编码并返回str类型。

    返回值可以直接作为HTTP Content-Type头部的值
    """
    m = hashlib.md5(to_bytes(data))
    return b64encode_as_string(m.digest())


def md5_string(data):
    """返回 `data` 的MD5值，以十六进制可读字符串（32个小写字符）的方式。"""
    return hashlib.md5(to_bytes(data)).hexdigest()


def content_type_by_name(name):
    """根据文件名，返回Content-Type。"""
    ext = os.path.splitext(name)[1].lower()
    if ext in _EXTRA_TYPES_MAP:
        return _EXTRA_TYPES_MAP[ext]

    return mimetypes.guess_type(name)[0]


def set_content_type(headers, name):
    """根据文件名在headers里设置Content-Type。如果headers中已经存在Content-Type，则直接返回。"""
    headers = headers or {}

    if 'Content-Type' in headers:
        return headers

    content_type = content_type_by_name(name)
    if content_type:
        headers['Content-Type'] = content_type

    return headers


def is_ip_or_localhost(netloc):
    """判断网络地址是否为IP或localhost。"""
    loc = netloc.split(':')[0]
    if loc == 'localhost':
        return True

    try:
        socket.inet_aton(loc)
    except socket.error:
        return False

    return True


class _SizedStreamReader(object):
    def __init__(self, file_object, size):
        self.file_object = file_object
        self.size = size
        self.offset = 0

    def read(self, amt=None):
        if self.offset >= self.size:
            return ''

        if (amt is None or amt < 0) or (amt + self.offset >= self.size):
            data = self.file_object.read(self.size - self.offset)
            self.offset = self.size
            return data

        self.offset += amt
        return self.file_object.read(amt)

    def __len__(self):
        return self.size


def how_many(m, n):
    return (m + n - 1) // n


def _get_data_size(data):
    if hasattr(data, '__len__'):
        return len(data)

    if hasattr(data, 'seek') and hasattr(data, 'tell'):
        current = data.tell()

        data.seek(0, os.SEEK_END)
        end = data.tell()
        data.seek(current, os.SEEK_SET)

        return end - current

    raise RuntimeError('Cannot determine the size of data of type: {0}'.format(data.__class__.__name__))


class MonitoredStreamReader(object):
    def __init__(self, data, callback, size=None):
        self.data = to_bytes(data)
        self.callback = callback

        if size is None:
            self.size = _get_data_size(data)
        else:
            self.size = size

        self.offset = 0

    def __len__(self):
        return self.size

    def read(self, amt=None):
        if self.offset >= self.size:
            self.callback(self.size, self.size, 0)
            return ''

        if amt is None or amt < 0:
            bytes_to_read = self.size - self.offset
        else:
            bytes_to_read = min(amt, self.size - self.offset)

        self.callback(self.offset, self.size, bytes_to_read)

        if isinstance(self.data, bytes):
            content = self.__read_bytes(bytes_to_read)
        else:
            content = self.__read_file(bytes_to_read)

        return content

    def __read_bytes(self, bytes_to_read):
        assert bytes_to_read is not None and bytes_to_read >= 0

        content = self.data[self.offset:self.offset+bytes_to_read]
        self.offset += bytes_to_read

        return content

    def __read_file(self, bytes_to_read):
        assert bytes_to_read is not None and bytes_to_read >= 0

        self.offset += bytes_to_read

        return self.data.read(bytes_to_read)