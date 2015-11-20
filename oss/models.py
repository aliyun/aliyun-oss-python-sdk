# -*- coding: utf-8 -*-

"""
oss.models
~~~~~~~~~~

该模块包含Python SDK API接口所需要的输入参数以及返回值类型。
"""

import re

import xml.etree.ElementTree as ElementTree

from .compat import to_string


class PartInfo(object):
    def __init__(self, part_number, etag, size=None):
        self.part_number = part_number
        self.etag = etag
        self.size = size


class RequestResult(object):
    def __init__(self, resp):
        self.resp = resp
        self.status = resp.status
        self.headers = resp.headers
        self.request_id = resp.headers['x-oss-request-id']


class ErrorResult(RequestResult):
    def __init__(self, resp):
        super(ErrorResult, self).__init__(resp)
        self.error_body = resp.read(4096)
        self.details = _parse_error_body(self.error_body)
        self.code = self.details.get('Code', '')
        self.message = self.details.get('Message', '')

    def __repr__(self):
        return repr(self.details)


class GetObjectResult(RequestResult):
    def __init__(self, resp):
        super(GetObjectResult, self).__init__(resp)

    def read(self, amt=None):
        return self.resp.read(amt)


class PutObjectResult(RequestResult):
    def __init__(self, resp):
        super(PutObjectResult, self).__init__(resp)
        self.etag = resp.headers['etag'].strip('"')


class AppendObjectResult(RequestResult):
    def __init__(self, resp):
        super(AppendObjectResult, self).__init__(resp)
        self.etag = resp.headers['etag'].strip('"')
        self.crc = int(resp.headers['x-oss-hash-crc64ecma'])
        self.next_position = int(resp.headers['x-oss-next-append-position'])


class BatchDeleteObjectsResult(RequestResult):
    def __init__(self, resp):
        super(BatchDeleteObjectsResult, self).__init__(resp)
        self.object_list = []


class InitMultipartUploadResult(RequestResult):
    def __init__(self, resp):
        super(InitMultipartUploadResult, self).__init__(resp)
        self.upload_id = None


class ListObjectsResult(RequestResult):
    def __init__(self, resp):
        super(ListObjectsResult, self).__init__(resp)
        self.is_truncated = False
        self.next_marker = ''
        self.object_list = []
        self.prefix_list = []


class SimplifiedObjectInfo(object):
    def __init__(self, name, last_modified, etag, type, size):
        self.name = name
        self.last_modified = last_modified
        self.etag = etag
        self.type = type
        self.size = size

    def is_prefix(self):
        return self.last_modified is None


class GetObjectAclResult(RequestResult):
    def __init__(self, resp):
        super(GetObjectAclResult, self).__init__(resp)
        self.acl = ''


class SimplifiedBucketInfo(object):
    def __init__(self, name, location, creation_date):
        self.name = name
        self.location = location
        self.creation_date = creation_date


class ListBucketsResult(RequestResult):
    def __init__(self, resp):
        super(ListBucketsResult, self).__init__(resp)
        self.is_truncated = False
        self.next_marker = ''
        self.buckets = []


class MultipartUploadInfo(object):
    def __init__(self, object_name, upload_id, creation_time):
        self.object_name = object_name
        self.upload_id = upload_id
        self.creation_time = creation_time

    def is_prefix(self):
        return self.upload_id is None


class ListMultipartUploadsResult(RequestResult):
    def __init__(self, resp):
        super(ListMultipartUploadsResult, self).__init__(resp)
        self.is_truncated = False
        self.next_key_marker = ''
        self.next_upload_id_marker = ''
        self.upload_list = []
        self.prefix_list = []


class ListPartsResult(RequestResult):
    def __init__(self, resp):
        super(ListPartsResult, self).__init__(resp)
        self.is_truncated = False
        self.next_marker = ''
        self.parts = []


class GetBucketAclResult(RequestResult):
    def __init__(self, resp):
        super(GetBucketAclResult, self).__init__(resp)
        self.acl = ''


class GetBucketLocationResult(RequestResult):
    def __init__(self, resp):
        super(GetBucketLocationResult, self).__init__(resp)
        self.location = ''


class BucketLogging(object):
    def __init__(self, target_bucket, target_prefix):
        self.target_bucket = target_bucket
        self.target_prefix = target_prefix


class GetBucketLoggingResult(RequestResult, BucketLogging):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketLogging.__init__(self, '', '')


class BucketReferer(object):
    def __init__(self, allow_empty_referer, referers):
        self.allow_empty_referer = allow_empty_referer
        self.referers = referers


class GetBucketRefererResult(RequestResult, BucketReferer):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketReferer.__init__(self, False, [])


class BucketWebsite(object):
    def __init__(self, index_file, error_file):
        self.index_file = index_file
        self.error_file = error_file


class GetBucketWebsiteResult(RequestResult, BucketWebsite):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketWebsite.__init__(self, '', '')


class LifecycleAction(object):
    def __init__(self, action, time_spec, time_value):
        self.action = action
        self.time_spec = time_spec
        self.time_value = str(time_value)


class LifecycleRule(object):
    def __init__(self, id, prefix, status, actions):
        self.id = id
        self.prefix = prefix
        self.status = status
        self.actions = actions


class BucketLifecycle(object):
    def __init__(self, rules=None):
        self.rules = rules or []


class GetBucketLifecycleResult(RequestResult, BucketLifecycle):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketLifecycle.__init__(self)


class CorsRule(object):
    def __init__(self,
                 allowed_origins=None,
                 allowed_methods=None,
                 allowed_headers=None,
                 expose_headers=None,
                 max_age_seconds=None):
        self.allowed_origins = allowed_origins or []
        self.allowed_methods = allowed_methods or []
        self.allowed_headers = allowed_headers or []
        self.expose_headers = expose_headers or []
        self.max_age_seconds = max_age_seconds


class BucketCors(object):
    def __init__(self, rules=None):
        self.rules = rules or []


class GetBucketCorsResult(RequestResult, BucketCors):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketCors.__init__(self)


def _parse_error_body(body):
    try:
        root = ElementTree.fromstring(body)
        if root.tag != 'Error':
            return {}

        details = {}
        for child in root:
            details[child.tag] = child.text
        return details
    except ElementTree.ParseError:
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
