# -*- coding: utf-8 -*-

"""
oss2.models
~~~~~~~~~~

该模块包含Python SDK API接口所需要的输入参数以及返回值类型。
"""

from .utils import http_to_unixtime, make_progress_adapter, http_date
from .exceptions import ClientError


class PartInfo(object):
    """表示分片信息的文件。

    该文件既用于 :func:`list_parts <oss2.Bucket.list_parts>` 的输出，也用于 :func:`complete_multipart_upload
    <oss2.Bucket.complete_multipart_upload>` 的输入。

    :param int part_number: 分片号
    :param str etag: 分片的ETag
    :param int size: 分片的大小。仅用在 `list_parts` 的结果里。
    :param int last_modified: 该分片最后修改的时间戳，类型为int。参考 :ref:`unix_time`
    """
    def __init__(self, part_number, etag, size=None, last_modified=None):
        self.part_number = part_number
        self.etag = etag
        self.size = size
        self.last_modified = last_modified


def _hget(headers, key, converter=lambda x: x):
    if key in headers:
        return converter(headers[key])
    else:
        return None


def _get_etag(headers):
    return _hget(headers, 'etag', lambda x: x.strip('"'))


class RequestResult(object):
    def __init__(self, resp):
        #: HTTP响应
        self.resp = resp

        #: HTTP状态码
        self.status = resp.status

        #: HTTP头
        self.headers = resp.headers

        #: 请求ID，用于跟踪一个OSS请求。提交工单时，最后能够提供请求ID
        self.request_id = resp.headers.get('x-oss-request-id', '')


class HeadObjectResult(RequestResult):
    def __init__(self, resp):
        super(HeadObjectResult, self).__init__(resp)

        #: 文件类型，可以是'Normal'、'Multipart'、'Appendable'等
        self.object_type = _hget(self.headers, 'x-oss-object-type')

        #: 文件最后修改时间，类型为int。参考 :ref:`unix_time` 。

        self.last_modified = _hget(self.headers, 'last-modified', http_to_unixtime)

        #: 文件的MIME类型
        self.content_type = _hget(self.headers, 'content-type')

        #: Content-Length，可能是None。
        self.content_length = _hget(self.headers, 'content-length', int)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)


class GetObjectResult(HeadObjectResult):
    def __init__(self, resp, progress_callback=None):
        super(GetObjectResult, self).__init__(resp)

        if progress_callback:
            self.stream = make_progress_adapter(self.resp, progress_callback, self.content_length)
        else:
            self.stream = self.resp

    def read(self, amt=None):
        return self.stream.read(amt)

    def __iter__(self):
        return iter(self.stream)


class PutObjectResult(RequestResult):
    def __init__(self, resp):
        super(PutObjectResult, self).__init__(resp)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)


class AppendObjectResult(RequestResult):
    def __init__(self, resp):
        super(AppendObjectResult, self).__init__(resp)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)

        #: 本次追加写完成后，OSS上文件的CRC64值
        self.crc = _hget(resp.headers, 'x-oss-hash-crc64ecma', int)

        #: 下次追加写的偏移
        self.next_position = _hget(resp.headers, 'x-oss-next-append-position', int)


class BatchDeleteObjectsResult(RequestResult):
    def __init__(self, resp):
        super(BatchDeleteObjectsResult, self).__init__(resp)

        #: 已经删除的文件名列表
        self.deleted_keys = []


class InitMultipartUploadResult(RequestResult):
    def __init__(self, resp):
        super(InitMultipartUploadResult, self).__init__(resp)

        #: 新生成的Upload ID
        self.upload_id = None


class ListObjectsResult(RequestResult):
    def __init__(self, resp):
        super(ListObjectsResult, self).__init__(resp)

        #: True表示还有更多的文件可以罗列；False表示已经列举完毕。
        self.is_truncated = False

        #: 下一次罗列的分页标记符，即，可以作为 :func:`list_objects <oss2.Bucket.list_objects>` 的 `marker` 参数。
        self.next_marker = ''

        #: 本次罗列得到的文件列表。其中元素的类型为 :class:`SimplifiedObjectInfo` 。
        self.object_list = []

        #: 本次罗列得到的公共前缀列表，类型为str列表。
        self.prefix_list = []


class SimplifiedObjectInfo(object):
    def __init__(self, key, last_modified, etag, type, size, storage_class):
        #: 文件名，或公共前缀名。
        self.key = key

        #: 文件的最后修改时间
        self.last_modified = last_modified

        #: HTTP ETag
        self.etag = etag

        #: 文件类型
        self.type = type

        #: 文件大小
        self.size = size

        #: 文件的存储类别，是一个字符串。
        self.storage_class = storage_class

    def is_prefix(self):
        """如果是公共前缀，返回True；是文件，则返回False"""
        return self.last_modified is None


OBJECT_ACL_DEFAULT = 'default'
OBJECT_ACL_PRIVATE = 'private'
OBJECT_ACL_PUBLIC_READ = 'public-read'
OBJECT_ACL_PUBLIC_READ_WRITE = 'public-read-write'


class GetObjectAclResult(RequestResult):
    def __init__(self, resp):
        super(GetObjectAclResult, self).__init__(resp)

        #: 文件的ACL，其值可以是 `OBJECT_ACL_DEFAULT`、`OBJECT_ACL_PRIVATE`、`OBJECT_ACL_PUBLIC_READ`或
        #: `OBJECT_ACL_PUBLIC_READ_WRITE`
        self.acl = ''


class SimplifiedBucketInfo(object):
    """:func:`list_buckets <oss2.Service.list_objects>` 结果中的单个元素类型。"""
    def __init__(self, name, location, creation_date):
        #: Bucket名
        self.name = name

        #: Bucket的区域
        self.location = location

        #: Bucket的创建时间，类型为int。参考 :ref:`unix_time`。
        self.creation_date = creation_date


class ListBucketsResult(RequestResult):
    def __init__(self, resp):
        super(ListBucketsResult, self).__init__(resp)

        #: True表示还有更多的Bucket可以罗列；False表示已经列举完毕。
        self.is_truncated = False

        #: 下一次罗列的分页标记符，即，可以作为 :func:`list_buckets <oss2.Service.list_buckets>` 的 `marker` 参数。
        self.next_marker = ''

        #: 得到的Bucket列表，类型为 :class:`SimplifiedBucketInfo` 。
        self.buckets = []


class MultipartUploadInfo(object):
    def __init__(self, key, upload_id, initiation_date):
        #: 文件名
        self.key = key

        #: 分片上传ID
        self.upload_id = upload_id

        #: 分片上传初始化的时间，类型为int。参考 :ref:`unix_time`
        self.initiation_date = initiation_date

    def is_prefix(self):
        """如果是公共前缀则返回True"""
        return self.upload_id is None


class ListMultipartUploadsResult(RequestResult):
    def __init__(self, resp):
        super(ListMultipartUploadsResult, self).__init__(resp)

        #: True表示还有更多的为完成分片上传可以罗列；False表示已经列举完毕。
        self.is_truncated = False

        #: 文件名分页符
        self.next_key_marker = ''

        #: 分片上传ID分页符
        self.next_upload_id_marker = ''

        #: 分片上传列表。类型为`MultipartUploadInfo`列表。
        self.upload_list = []

        #: 公共前缀列表。类型为str列表。
        self.prefix_list = []


class ListPartsResult(RequestResult):
    def __init__(self, resp):
        super(ListPartsResult, self).__init__(resp)

        # True表示还有更多的Part可以罗列；False表示已经列举完毕。
        self.is_truncated = False

        # 下一个分页符
        self.next_marker = ''

        # 罗列出的Part信息，类型为 `PartInfo` 列表。
        self.parts = []


BUCKET_ACL_PRIVATE = 'private'
BUCKET_ACL_PUBLIC_READ = 'public-read'
BUCKET_ACL_PUBLIC_READ_WRITE = 'public-read-write'


class GetBucketAclResult(RequestResult):
    def __init__(self, resp):
        super(GetBucketAclResult, self).__init__(resp)

        #: Bucket的ACL，其值可以是 `BUCKET_ACL_PRIVATE`、`BUCKET_ACL_PUBLIC_READ`或`BUCKET_ACL_PUBLIC_READ_WRITE`。
        self.acl = ''


class GetBucketLocationResult(RequestResult):
    def __init__(self, resp):
        super(GetBucketLocationResult, self).__init__(resp)

        #: Bucket所在的数据中心
        self.location = ''


class BucketLogging(object):
    """Bucket日志配置信息。

    :param str target_bucket: 存储日志到这个Bucket。
    :param str target_prefix: 生成的日志文件名加上该前缀。
    """
    def __init__(self, target_bucket, target_prefix):
        self.target_bucket = target_bucket
        self.target_prefix = target_prefix


class GetBucketLoggingResult(RequestResult, BucketLogging):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketLogging.__init__(self, '', '')


class BucketReferer(object):
    """Bucket防盗链设置。

    :param bool allow_empty_referer: 是否允许空的Referer。
    :param referers: Referer列表，每个元素是一个str。
    """
    def __init__(self, allow_empty_referer, referers):
        self.allow_empty_referer = allow_empty_referer
        self.referers = referers


class GetBucketRefererResult(RequestResult, BucketReferer):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketReferer.__init__(self, False, [])


class BucketWebsite(object):
    """静态网站托管配置。

    :param str index_file: 索引页面文件
    :param str error_file: 404页面文件
    """
    def __init__(self, index_file, error_file):
        self.index_file = index_file
        self.error_file = error_file


class GetBucketWebsiteResult(RequestResult, BucketWebsite):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketWebsite.__init__(self, '', '')


class LifecycleExpiration(object):
    """过期删除操作。

    :param days: 表示在文件修改后过了这么多天，就会匹配规则，从而被删除
    :param date: 表示在该日期之后，规则就一直生效。即每天都会对符合前缀的文件执行删除操作（如，删除），而不管文件是什么时候生成的。
        *不建议使用*
    :type date: `datetime.date`
    """
    def __init__(self, days=None, date=None):
        if days is not None and date is not None:
            raise ClientError('days and date should not be both specified')

        self.days = days
        self.date = date


class LifecycleRule(object):
    """生命周期规则。

    :param id: 规则名
    :param prefix: 只有文件名匹配该前缀的文件才适用本规则
    :param expiration: 过期删除操作。
    :type expiration: :class:`LifecycleExpiration`
    :param status: 启用还是禁止该规则。可选值为 `LifecycleRule.ENABLED` 或 `LifecycleRule.DISABLED`
    """

    ENABLED = 'Enabled'
    DISABLED = 'Disabled'

    def __init__(self, id, prefix,
                 status=ENABLED, expiration=None):
        self.id = id
        self.prefix = prefix
        self.status = status
        self.expiration = expiration


class BucketLifecycle(object):
    """Bucket的生命周期配置。

    :param rules: 规则列表，
    :type rules: list of :class:`LifecycleRule`
    """
    def __init__(self, rules=None):
        self.rules = rules or []


class GetBucketLifecycleResult(RequestResult, BucketLifecycle):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketLifecycle.__init__(self)


class CorsRule(object):
    """CORS（跨域资源共享）规则。

    :param allowed_origins: 允许跨域访问的域。
    :type allowed_origins: list of str

    :param allowed_methods: 允许跨域访问的HTTP方法，如'GET'等。
    :type allowed_methods: list of str

    :param allowed_headers: 允许跨域访问的HTTP头部。
    :type allowed_headers: list of str


    """
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
