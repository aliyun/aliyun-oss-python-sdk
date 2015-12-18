# -*- coding: utf-8 -*-

"""
oss2.exceptions
~~~~~~~~~~~~~~

异常类。
"""

import re

import xml.etree.ElementTree as ElementTree
from xml.parsers import expat


from .compat import to_string


_OSS_ERROR_TO_EXCEPTION = {} # populated at end of module


OSS_CLIENT_ERROR_STATUS = -1
OSS_REQUEST_ERROR_STATUS = -2


class OssError(Exception):
    def __init__(self, status, headers, body, details):
        #: HTTP 状态码
        self.status = status

        #: 请求ID，用于跟踪一个OSS请求。提交工单时，最好能够提供请求ID
        self.request_id = headers.get('x-oss-request-id', '')

        #: HTTP响应体（部分）
        self.body = body

        #: 详细错误信息，是一个string到string的dict
        self.details = details

        #: OSS错误码
        self.code = self.details.get('Code', '')

        #: OSS错误信息
        self.message = self.details.get('Message', '')

    def __str__(self):
        return str(self.details)


class ClientError(OssError):
    def __init__(self, message):
        OssError.__init__(self, OSS_CLIENT_ERROR_STATUS, {}, 'ClientError: ' + message, {})

    def __str__(self):
        return self.body


class RequestError(OssError):
    def __init__(self, e):
        OssError.__init__(self, OSS_REQUEST_ERROR_STATUS, {}, 'RequestError: ' + str(e), {})
        self.exception = e

    def __str__(self):
        return self.body


class ServerError(OssError):
    pass


class NotFound(ServerError):
    status = 404
    code = ''


class MalformedXml(ServerError):
    status = 400
    code = 'MalformedXML'


class InvalidArgument(ServerError):
    status = 400
    code = 'InvalidArgument'

    def __init__(self, status, headers, body, details):
        super(InvalidArgument, self).__init__(status, headers, body, details)
        self.name = details.get('ArgumentName')
        self.value = details.get('ArgumentValue')


class InvalidObjectName(ServerError):
    status = 400
    code = 'InvalidObjectName'


class NoSuchBucket(NotFound):
    status = 404
    code = 'NoSuchBucket'


class NoSuchKey(NotFound):
    status = 404
    code = 'NoSuchKey'


class NoSuchUpload(NotFound):
    status = 404
    code = 'NoSuchUpload'


class NoSuchWebsite(NotFound):
    status = 404
    code = 'NoSuchWebsiteConfiguration'


class NoSuchLifecycle(NotFound):
    status = 404
    code = 'NoSuchLifecycle'


class NoSuchCors(NotFound):
    status = 404
    code = 'NoSuchCORSConfiguration'


class Conflict(ServerError):
    status = 409
    code = ''


class BucketNotEmpty(Conflict):
    status = 409
    code = 'BucketNotEmpty'


class PositionNotEqualToLength(Conflict):
    status = 409
    code = 'PositionNotEqualToLength'

    def __init__(self, status, headers, body, details):
        super(PositionNotEqualToLength, self).__init__(status, headers, body, details)
        self.next_position = int(headers['x-oss-next-append-position'])


class ObjectNotAppendable(Conflict):
    status = 409
    code = 'ObjectNotAppendable'


class NotModified(ServerError):
    status = 304
    code = ''


class AccessDenied(ServerError):
    status = 403
    code = 'AccessDenied'


def make_exception(resp):
    status = resp.status
    headers = resp.headers
    body = resp.read(4096)
    details = _parse_error_body(body)
    code = details.get('Code', '')

    try:
        klass = _OSS_ERROR_TO_EXCEPTION[(status, code)]
        return klass(status, headers, body, details)
    except KeyError:
        return ServerError(status, headers, body, details)


def _walk_subclasses(klass):
    for sub in klass.__subclasses__():
        yield sub
        for subsub in _walk_subclasses(sub):
            yield subsub


for klass in _walk_subclasses(ServerError):
    status = getattr(klass, 'status', None)
    code = getattr(klass, 'code', None)

    if status is not None and code is not None:
        _OSS_ERROR_TO_EXCEPTION[(status, code)] = klass


# XML parsing exceptions have changed in Python2.7 and ElementTree 1.3
if hasattr(ElementTree, 'ParseError'):
    ElementTreeParseError = (ElementTree.ParseError, expat.ExpatError)
else:
    ElementTreeParseError = (expat.ExpatError)


def _parse_error_body(body):
    try:
        root = ElementTree.fromstring(body)
        if root.tag != 'Error':
            return {}

        details = {}
        for child in root:
            details[child.tag] = child.text
        return details
    except ElementTreeParseError:
        return _guess_error_details(body)


def _guess_error_details(body):
    details = {}
    body = to_string(body)

    if '<Error>' not in body or '</Error>' not in body:
        return details

    m = re.search('<Code>(.*)</Code>', body)
    if m:
        details['Code'] = m.group(1)

    m = re.search('<Message>(.*)</Message>', body)
    if m:
        details['Message'] = m.group(1)

    return details
