# -*- coding: utf-8 -*-

"""
oss2.utils
----------

Utils module
"""

from email.utils import formatdate

import os.path
import mimetypes
import socket
import hashlib
import base64
import threading
import calendar
import datetime
import time
import errno
import crcmod

from .compat import to_string, to_bytes
from .exceptions import ClientError, InconsistentError, RequestError


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
    """Calculate the MD5 of the data. The return value is base64 encoded str.

    The return value could be value of of HTTP Content-MD5 header.
    """
    m = hashlib.md5(to_bytes(data))
    return b64encode_as_string(m.digest())


def md5_string(data):
    """Returns MD5 value of `data` in hex string (hexdigest())"""
    return hashlib.md5(to_bytes(data)).hexdigest()


def content_type_by_name(name):
    """Return the Content-Type by file name."""
    ext = os.path.splitext(name)[1].lower()
    if ext in _EXTRA_TYPES_MAP:
        return _EXTRA_TYPES_MAP[ext]

    return mimetypes.guess_type(name)[0]


def set_content_type(headers, name):
    """Sets the content type by the name. If the content-type has been set, no-op and return."""
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


_ALPHA_NUM = 'abcdefghijklmnopqrstuvwxyz0123456789'
_HYPHEN = '-'
_BUCKET_NAME_CHARS = set(_ALPHA_NUM + _HYPHEN)


def is_valid_bucket_name(name):
    """Checks if the bucket name is valid."""
    if len(name) < 3 or len(name) > 63:
        return False

    if name[-1] == _HYPHEN:
        return False

    if name[0] not in _ALPHA_NUM:
        return False

    return set(name) <= _BUCKET_NAME_CHARS


class SizedFileAdapter(object):
    """It guarantees only read up to the specified 'size' data, even if the original 'file_object' size （Adapter）is bigger."""
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

    @property
    def len(self):
        return self.size


def how_many(m, n):
    return (m + n - 1) // n


def file_object_remaining_bytes(fileobj):
    current = fileobj.tell()

    fileobj.seek(0, os.SEEK_END)
    end = fileobj.tell()
    fileobj.seek(current, os.SEEK_SET)

    return end - current


def _has_data_size_attr(data):
    return hasattr(data, '__len__') or hasattr(data, 'len') or (hasattr(data, 'seek') and hasattr(data, 'tell'))


def _get_data_size(data):
    if hasattr(data, '__len__'):
        return len(data)

    if hasattr(data, 'len'):
        return data.len

    if hasattr(data, 'seek') and hasattr(data, 'tell'):
        return file_object_remaining_bytes(data)

    return None


_CHUNK_SIZE = 8 * 1024


def make_progress_adapter(data, progress_callback, size=None):
    """Returns an adapter instance so that the progress callback is called when reading the data.
     When parameter `size` is not specified and cannot be dertermined, the total size in the callback is None.

    :param data: It could be bytes、file object or iterable
    :param progress_callback: Progress callback. Check out :ref:`progress_callback`
    :param size: Specify the `data` size, optional.

    :return: The adapters that could call the progress callback.
    """
    data = to_bytes(data)

    if size is None:
        size = _get_data_size(data)

    if size is None:
        if hasattr(data, 'read'):
            return _FileLikeAdapter(data, progress_callback)
        elif hasattr(data, '__iter__'):
            return _IterableAdapter(data, progress_callback)
        else:
            raise ClientError('{0} is not a file object, nor an iterator'.format(data.__class__.__name__))
    else:
        return _BytesAndFileAdapter(data, progress_callback, size)


def make_crc_adapter(data, init_crc=0):
    """Returns an adapter instance so that the CRC could be calculated during read.

    :param data: It could be bytes、file object or iterable
    :param init_crc: Init CRC value, optional.

    :return: A adapter that could calls CRC caluclating function.
    """
    data = to_bytes(data)

    # bytes or file object
    if _has_data_size_attr(data):
        return _BytesAndFileAdapter(data, 
                                    size=_get_data_size(data), 
                                    crc_callback=Crc64(init_crc))
    # file-like object
    elif hasattr(data, 'read'): 
        return _FileLikeAdapter(data, crc_callback=Crc64(init_crc))
    # iterator
    elif hasattr(data, '__iter__'):
        return _IterableAdapter(data, crc_callback=Crc64(init_crc))
    else:
        raise ClientError('{0} is not a file object, nor an iterator'.format(data.__class__.__name__))

    
def check_crc(operation, client_crc, oss_crc):
    if client_crc != oss_crc:
        raise InconsistentError('the crc of {0} between client and oss is not inconsistent'.format(operation))


def _invoke_crc_callback(crc_callback, content):
    if crc_callback:
        crc_callback(content)


def _invoke_progress_callback(progress_callback, consumed_bytes, total_bytes):
    if progress_callback:
        progress_callback(consumed_bytes, total_bytes)


class _IterableAdapter(object):
    def __init__(self, data, progress_callback=None, crc_callback=None):
        self.iter = iter(data)
        self.progress_callback = progress_callback
        self.offset = 0
        
        self.crc_callback = crc_callback

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):            
        _invoke_progress_callback(self.progress_callback, self.offset, None)

        content = next(self.iter)
        self.offset += len(content)
                
        _invoke_crc_callback(self.crc_callback, content)

        return content
    
    @property
    def crc(self):
        return self.crc_callback.crc


class _FileLikeAdapter(object):
    """The adapter to monior the progress for `fileobj` that the content length could not be termined.

    :param fileobj: file-like object，as long as read() is supported.
    :param progress_callback: Progress callback.
    """
    def __init__(self, fileobj, progress_callback=None, crc_callback=None):
        self.fileobj = fileobj
        self.progress_callback = progress_callback
        self.offset = 0
        
        self.crc_callback = crc_callback

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        content = self.read(_CHUNK_SIZE)

        if content:
            return content
        else:
            raise StopIteration

    def read(self, amt=None):
        content = self.fileobj.read(amt)
        if not content:
            _invoke_progress_callback(self.progress_callback, self.offset, None) 
        else:
            _invoke_progress_callback(self.progress_callback, self.offset, None)
                
            self.offset += len(content)
                                   
            _invoke_crc_callback(self.crc_callback, content)

        return content
    
    @property
    def crc(self):
        return self.crc_callback.crc


class _BytesAndFileAdapter(object):
    """The adapter to monitor data's progress.

    :param data: It could be unicode（internally it's convereted to UTF-8 bytes）、bytes or file object
    :param progress_callback: Progress callback，The signature is callback(bytes_read, total_bytes).
        `bytes_read` is the bytes read and `total_bytes` is the total bytes.
    :param int size: The size of the `data`.
    """
    def __init__(self, data, progress_callback=None, size=None, crc_callback=None):
        self.data = to_bytes(data)
        self.progress_callback = progress_callback
        self.size = size
        self.offset = 0
        
        self.crc_callback = crc_callback

    @property
    def len(self):
        return self.size

    # for python 2.x
    def __bool__(self):
        return True
    # for python 3.x
    __nonzero__=__bool__

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        content = self.read(_CHUNK_SIZE)

        if content:
            return content
        else:
            raise StopIteration

    def read(self, amt=None):
        if self.offset >= self.size:
            return ''

        if amt is None or amt < 0:
            bytes_to_read = self.size - self.offset
        else:
            bytes_to_read = min(amt, self.size - self.offset)

        if isinstance(self.data, bytes):
            content = self.data[self.offset:self.offset+bytes_to_read]
        else:
            content = self.data.read(bytes_to_read)

        self.offset += bytes_to_read
            
        _invoke_progress_callback(self.progress_callback, min(self.offset, self.size), self.size)

        _invoke_crc_callback(self.crc_callback, content)

        return content
    
    @property
    def crc(self):
        return self.crc_callback.crc


class Crc64(object):

    _POLY = 0x142F0E1EBA9EA3693
    _XOROUT = 0XFFFFFFFFFFFFFFFF
    
    def __init__(self, init_crc=0):
        self.crc64 = crcmod.Crc(self._POLY, initCrc=init_crc, rev=True, xorOut=self._XOROUT)

    def __call__(self, data):
        self.update(data)
    
    def update(self, data):
        self.crc64.update(data)
    
    @property
    def crc(self):
        return self.crc64.crcValue


_STRPTIME_LOCK = threading.Lock()

_GMT_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"
_ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"


def to_unixtime(time_string, format_string):
    with _STRPTIME_LOCK:
        return int(calendar.timegm(time.strptime(time_string, format_string)))


def http_date(timeval=None):
    """Returns the HTTP standard GMT time string. If using strftime format, it would be "%a, %d %b %Y %H:%M:%S GMT".
    But strftime() cannot be used as it's locale dependent.
    """
    return formatdate(timeval, usegmt=True)


def http_to_unixtime(time_string):
    """Converts the Http date to unix time（total seconds since 1970 Jan First, 00:00).

    HTTP Date such as `Sat, 05 Dec 2015 11:10:29 GMT` 。
    """
    return to_unixtime(time_string, _GMT_FORMAT)


def iso8601_to_unixtime(time_string):
    """Coverts the ISO8601 time string (e.g. 2012-02-24T06:07:48.000Z）to unix time in seconds"""
    return to_unixtime(time_string, _ISO8601_FORMAT)


def date_to_iso8601(d):
    return d.strftime(_ISO8601_FORMAT)  # It's OK to use strftime, since _ISO8601_FORMAT is not locale dependent


def iso8601_to_date(time_string):
    timestamp = iso8601_to_unixtime(time_string)
    return datetime.date.fromtimestamp(timestamp)


def makedir_p(dirpath):
    try:
        os.makedirs(dirpath)
    except os.error as e:
        if e.errno != errno.EEXIST:
            raise


def silently_remove(filename):
    """Silently remove the file. If the file does not exist, no op and return without error."""
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def force_rename(src, dst):
    try:
        os.rename(src, dst)
    except OSError as e:
        if e.errno == errno.EEXIST:
            silently_remove(dst)
            os.rename(src, dst)
        else:
            raise


def copyfileobj_and_verify(fsrc, fdst, expected_len,
                           chunk_size=16*1024,
                           request_id=''):
    """copy data from file-like object fsrc to file-like object fdst, and verify length"""

    num_read = 0

    while 1:
        buf = fsrc.read(chunk_size)
        if not buf:
            break

        num_read += len(buf)
        fdst.write(buf)

    if num_read != expected_len:
        raise InconsistentError("IncompleteRead from source", request_id)
