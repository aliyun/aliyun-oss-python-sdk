# -*- coding: utf-8 -*-

"""
oss2.models
~~~~~~~~~~

The module contains all classes' definition for parameters and return values in the Python SDK API.
"""

from .utils import http_to_unixtime, make_progress_adapter, make_crc_adapter
from .exceptions import ClientError
from .compat import urlunquote

class PartInfo(object):
    """Part information.

    This class is the output object of :func:`list_parts <oss2.Bucket.list_parts>`， and the input parameters for :func:`complete_multipart_upload
    <oss2.Bucket.complete_multipart_upload>`.

    :param int part_number: part number (starting from 1)
    :param str etag: ETag
    :param int size: Part size in bytes.It's only used in  `list_parts` result.
    :param int last_modified: The last modified of that part in unix time, type is int. Check out :ref:`unix_time` for more information.
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
        #: HTTP response
        self.resp = resp

        #: HTTP status code (such as 200,404, etc)
        self.status = resp.status

        #: HTTP headers
        self.headers = resp.headers

        #: Request ID which is used for tracking OSS request.It's very useful when submitting a customer ticket.
        self.request_id = resp.headers.get('x-oss-request-id', '')


class HeadObjectResult(RequestResult):
    def __init__(self, resp):
        super(HeadObjectResult, self).__init__(resp)

        #: File type, three types are supported: 'Normal'、'Multipart'、'Appendable'.
        self.object_type = _hget(self.headers, 'x-oss-object-type')

        #: File's last modified time in unix time, type is int.

        self.last_modified = _hget(self.headers, 'last-modified', http_to_unixtime)

        #: File's MIME type.
        self.content_type = _hget(self.headers, 'content-type')

        #: Content-Length，it could be None。
        self.content_length = _hget(self.headers, 'content-length', int)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)


class GetObjectMetaResult(RequestResult):
    def __init__(self, resp):
        super(GetObjectMetaResult, self).__init__(resp)

        #: Last modified time of a file, in unix time. Check out :ref:`unix_time` for more information.
        self.last_modified = _hget(self.headers, 'last-modified', http_to_unixtime)

        #: Content-Length，file size in bytes. Type is int.
        self.content_length = _hget(self.headers, 'content-length', int)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)


class GetSymlinkResult(RequestResult):
    def __init__(self, resp):
        super(GetSymlinkResult, self).__init__(resp)

        #: The target file of the symlink file.
        self.target_key = urlunquote(_hget(self.headers, 'x-oss-symlink-target'))
        
        
class GetObjectResult(HeadObjectResult):
    def __init__(self, resp, progress_callback=None, crc_enabled=False):
        super(GetObjectResult, self).__init__(resp)
        self.__crc_enabled = crc_enabled
        
        if progress_callback:
            self.stream = make_progress_adapter(self.resp, progress_callback, self.content_length)
        else:
            self.stream = self.resp
        
        self.__crc = _hget(self.headers, 'x-oss-hash-crc64ecma', int)
        if self.__crc_enabled:
            self.stream = make_crc_adapter(self.stream)
            
    def read(self, amt=None):
        return self.stream.read(amt)

    def __iter__(self):
        return iter(self.stream)
    
    @property
    def client_crc(self):
        if self.__crc_enabled:
            return self.stream.crc
        else:
            return None
    
    @property
    def server_crc(self):
        return self.__crc


class PutObjectResult(RequestResult):
    def __init__(self, resp):
        super(PutObjectResult, self).__init__(resp)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)
        
        #: CRC value of the file uploaded.
        self.crc = _hget(resp.headers, 'x-oss-hash-crc64ecma', int)


class AppendObjectResult(RequestResult):
    def __init__(self, resp):
        super(AppendObjectResult, self).__init__(resp)

        #: HTTP ETag
        self.etag = _get_etag(self.headers)

        #: The updated CRC64 value after the append operation.
        self.crc = _hget(resp.headers, 'x-oss-hash-crc64ecma', int)

        #: The next position for append operation.
        self.next_position = _hget(resp.headers, 'x-oss-next-append-position', int)


class BatchDeleteObjectsResult(RequestResult):
    def __init__(self, resp):
        super(BatchDeleteObjectsResult, self).__init__(resp)

        #: The deleted file name list
        self.deleted_keys = []


class InitMultipartUploadResult(RequestResult):
    def __init__(self, resp):
        super(InitMultipartUploadResult, self).__init__(resp)

        #: initial Upload ID
        self.upload_id = None


class ListObjectsResult(RequestResult):
    def __init__(self, resp):
        super(ListObjectsResult, self).__init__(resp)

        #: True means there's more files to list; False means all files are listed.
        self.is_truncated = False

        #: Paging marker for next call. It should be the value of parameter marker in next :func:`list_objects <oss2.Bucket.list_objects>` call.
        self.next_marker = ''

        #: The object list. The object type is :class:`SimplifiedObjectInfo`.
        self.object_list = []

        #: The prefix list
        self.prefix_list = []


class SimplifiedObjectInfo(object):
    def __init__(self, key, last_modified, etag, type, size, storage_class):
        #: The file name or common prefix name (folder name).
        self.key = key

        #: Last modified time.
        self.last_modified = last_modified

        #: HTTP ETag
        self.etag = etag

        #: File type
        self.type = type

        #: File size
        self.size = size

        #: Storage class (Standard, IA and Archive)
        self.storage_class = storage_class

    def is_prefix(self):
        """If it's common prefix (folder), returns true; Otherwise returns False."""
        return self.last_modified is None


OBJECT_ACL_DEFAULT = 'default'
OBJECT_ACL_PRIVATE = 'private'
OBJECT_ACL_PUBLIC_READ = 'public-read'
OBJECT_ACL_PUBLIC_READ_WRITE = 'public-read-write'


class GetObjectAclResult(RequestResult):
    def __init__(self, resp):
        super(GetObjectAclResult, self).__init__(resp)

        #: File ACL, The value could be `OBJECT_ACL_DEFAULT`、`OBJECT_ACL_PRIVATE`、`OBJECT_ACL_PUBLIC_READ` or 
        #: `OBJECT_ACL_PUBLIC_READ_WRITE`
        self.acl = ''


class SimplifiedBucketInfo(object):
    """:func:`list_buckets <oss2.Service.list_objects>` 结果中的单个元素类型。"""
    def __init__(self, name, location, creation_date):
        #: Bucket name
        self.name = name

        #: Bucket location
        self.location = location

        #: Bucket created time in unix time. Check out :ref:`unix_time` for more information.
        self.creation_date = creation_date


class ListBucketsResult(RequestResult):
    def __init__(self, resp):
        super(ListBucketsResult, self).__init__(resp)

        #: True means more buckets to list; False means all buckets have been listed.
        self.is_truncated = False

        #: The next paging marker--that is it could be the value of parameter `marker` in :func:`list_buckets <oss2.Service.list_buckets>`.
        self.next_marker = ''

        #: Gets the bucket list. The type is :class:`SimplifiedBucketInfo`.
        self.buckets = []


class MultipartUploadInfo(object):
    def __init__(self, key, upload_id, initiation_date):
        #: File name
        self.key = key

        #: upload Id
        self.upload_id = upload_id

        #: The initialization time of a multipart upload in unix time. Please check out :ref:`unix_time`.
        self.initiation_date = initiation_date

    def is_prefix(self):
        """If it's common prefix then return true;Otherwise return false"""
        return self.upload_id is None


class ListMultipartUploadsResult(RequestResult):
    def __init__(self, resp):
        super(ListMultipartUploadsResult, self).__init__(resp)

        #: True means more unfinished multiparts uploads to list;False means no more multiparts uploads.
        self.is_truncated = False

        #: The paging key marker.
        self.next_key_marker = ''

        #: The paging upload Id marker
        self.next_upload_id_marker = ''

        #: list of the multiparts upload. The type is `MultipartUploadInfo`.
        self.upload_list = []

        #: The common prefix. The type is str.
        self.prefix_list = []


class ListPartsResult(RequestResult):
    def __init__(self, resp):
        super(ListPartsResult, self).__init__(resp)

        # True means more parts to list. False means no more parts to list.
        self.is_truncated = False

        # Next paging marker
        self.next_marker = ''

        # parts list. The type is `PartInfo`.
        self.parts = []


BUCKET_ACL_PRIVATE = 'private'
BUCKET_ACL_PUBLIC_READ = 'public-read'
BUCKET_ACL_PUBLIC_READ_WRITE = 'public-read-write'


class GetBucketAclResult(RequestResult):
    def __init__(self, resp):
        super(GetBucketAclResult, self).__init__(resp)

        #: Bucket ACL, the value could be `BUCKET_ACL_PRIVATE`、`BUCKET_ACL_PUBLIC_READ`或`BUCKET_ACL_PUBLIC_READ_WRITE`。
        self.acl = ''


class GetBucketLocationResult(RequestResult):
    def __init__(self, resp):
        super(GetBucketLocationResult, self).__init__(resp)

        #: Bucket's datacenter location
        self.location = ''


class BucketLogging(object):
    """Bucket logging configuration.

    :param str target_bucket: logging files' bucket。
    :param str target_prefix: The prefix of the logging files.
    """
    def __init__(self, target_bucket, target_prefix):
        self.target_bucket = target_bucket
        self.target_prefix = target_prefix


class GetBucketLoggingResult(RequestResult, BucketLogging):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketLogging.__init__(self, '', '')


class BucketReferer(object):
    """Bucket referer settings

    :param bool allow_empty_referer: Flag of allowing empty Referer。
    :param referers: Referer list. The type of element is str.
    """
    def __init__(self, allow_empty_referer, referers):
        self.allow_empty_referer = allow_empty_referer
        self.referers = referers


class GetBucketRefererResult(RequestResult, BucketReferer):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketReferer.__init__(self, False, [])


class BucketWebsite(object):
    """Static website configuraiton.

    :param str index_file: The home page file.
    :param str error_file: 404 not found file.
    """
    def __init__(self, index_file, error_file):
        self.index_file = index_file
        self.error_file = error_file


class GetBucketWebsiteResult(RequestResult, BucketWebsite):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketWebsite.__init__(self, '', '')


class LifecycleExpiration(object):
    """Life cycle expiration。

    :param days: The days after last modified to trigger the expiration rule (such as delete files).
    :param date: The date threshold to trigger the expiration rule---after this date the expiration rule will be always valid (not recommended).
        
    :type date: `datetime.date`
    """
    def __init__(self, days=None, date=None):
        if days is not None and date is not None:
            raise ClientError('days and date should not be both specified')

        self.days = days
        self.date = date


class LifecycleRule(object):
    """Life cycle rule

    :param id: Rule name
    :param prefix: File prefix to match the rule
    :param expiration: Expiration time
    :type expiration: :class:`LifecycleExpiration`
    :param status: Enable or disable the rule. The value is either `LifecycleRule.ENABLED` or `LifecycleRule.DISABLED`
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
    """Bucket's life cycle configuration。

    :param rules: Life cycle rule list，
    :type rules: list of :class:`LifecycleRule`
    """
    def __init__(self, rules=None):
        self.rules = rules or []


class GetBucketLifecycleResult(RequestResult, BucketLifecycle):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        BucketLifecycle.__init__(self)


class CorsRule(object):
    """CORS (cross origin resource sharing) rules

    :param allowed_origins: Allow origins to access the bucket
    :type allowed_origins: list of str

    :param allowed_methods: Allowed HTTP methods for CORS.
    :type allowed_methods: list of str

    :param allowed_headers: Allowed HTTP headers for CORS.
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


class LiveChannelInfoTarget(object):
    """Target information in the Live channel，which includes the parameters of the target protocol.

    :param type: prtocol, only HLS is supported for now.
    :type type: str

    :param frag_duration: The expected time length in seconds of HLS protocol's TS files.
    :type frag_duration: int

    :param frag_count: TS file count in the m3u8 file of HLS protocol.
    :type frag_count: int"""

    def __init__(self,
            type = 'HLS',
            frag_duration = 5,
            frag_count = 3,
            playlist_name = ''):
        self.type = type
        self.frag_duration = frag_duration
        self.frag_count = frag_count
        self.playlist_name = playlist_name


class LiveChannelInfo(object):
    """Live channel configuration

    :param status: status: the value is either "enabled" or "disabled".
    :type status: str

    :param description: The live channel's description, the max length is 128 bytes.
    :type description: str

    :param target: The target informtion of a pushing streaming, including the parameters about the target protocol.
    :type class:`LiveChannelInfoTarget <oss2.models.LiveChannelInfoTarget>`

    :param last_modified: The last modified time of the live channel. It's only used in `ListLiveChannel`.
    :type last_modified: Last modified time in unix time (int type), Check out :ref:`unix_time`.
    
    :param name: The live channel name.
    :type name: str
        
    :param play_url: play url.
    :type play_url: str
        
    :param publish_url: publish url
    :type publish_url: str"""
    
    def __init__(self,
            status = 'enabled',
            description = '',
            target = None,
            last_modified = None,
            name = None,
            play_url = None,
            publish_url = None):
        self.status = status
        self.description = description
        self.target = target
        self.last_modified = last_modified
        self.name = name
        self.play_url = play_url
        self.publish_url = publish_url


class LiveChannelList(object):
    """The result of live channel list operation.

    :param prefix: The live channel to list
    :type prefix: str

    :param marker: The paging marker in the live channel list operation.
    :type marker: str

    :param max_keys: Max entries to return.
    :type max_keys: int

    :param is_truncated: Is there more live channels to list.
    :type is_truncated: bool

    :param next_marker: The next paging marker
    :type marker: str

    :param channels: the live channel list returned.
    :type channels: list，the type is :class:`LiveChannelInfo`"""

    def __init__(self,
            prefix = '',
            marker = '',
            max_keys = 100,
            is_truncated = False,
            next_marker = ''):
        self.prefix = prefix
        self.marker = marker
        self.max_keys = max_keys
        self.is_truncated = is_truncated
        self.next_marker = next_marker
        self.channels = []


class LiveChannelVideoStat(object):
    """The video node in LiveStat

    :param width: video width
    :type width: int

    :param height: video height
    :type height: int

    :param frame_rate: frame rate
    :type frame_rate: int

    :param codec: codec
    :type codec: str

    :param bandwidth: bandwith of the video
    :type bandwidth: int"""

    def __init__(self,
            width = 0,
            height = 0,
            frame_rate = 0,
            codec = '',
            bandwidth = 0):
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.codec = codec
        self.bandwidth = bandwidth


class LiveChannelAudioStat(object):
    """Audio node in LiveStat

    :param codec: Audio codec.
    :type codec: str

    :param sample_rate: Sample rate
    :type sample_rate: int

    :param bandwidth: bandwidth
    :type bandwidth: int"""

    def __init__(self,
            codec = '',
            sample_rate = 0,
            bandwidth = 0):
        self.codec = codec
        self.sample_rate = sample_rate
        self.bandwidth = bandwidth


class LiveChannelStat(object):
    """LiveStat result.

    :param status: live channel status
    :type codec: str

    :param remote_addr: remote address
    :type remote_addr: str

    :param connected_time: The connected time for the pusing streaming.
    :type connected_time: int, unix time

    :param video: Video description information
    :type video: class:`LiveChannelVideoStat <oss2.models.LiveChannelVideoStat>`

    :param audio: Audio description information
    :type audio: class:`LiveChannelAudioStat <oss2.models.LiveChannelAudioStat>`"""

    def __init__(self,
            status = '',
            remote_addr = '',
            connected_time = '',
            video = None,
            audio = None):
        self.status = status
        self.remote_addr = remote_addr
        self.connected_time = connected_time
        self.video = video
        self.audio = audio


class LiveRecord(object):
    """Pushing streaming record

    :param start_time: The start time of the push streaming.
    :type start_time: int, check out :ref:`unix_time`.

    :param end_time: The end time of the push streaming.
    :type end_time: int, check out :ref:`unix_time` for more information.

    :param remote_addr: The remote address of the pushing streaming.
    :type remote_addr: str"""

    def __init__(self,
            start_time = '',
            end_time = '',
            remote_addr = ''):
        self.start_time = start_time
        self.end_time = end_time
        self.remote_addr = remote_addr


class LiveChannelHistory(object):
    """Pushing streaming record of the live channel"""

    def __init__(self):
        self.records = []


class CreateLiveChannelResult(RequestResult, LiveChannelInfo):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        LiveChannelInfo.__init__(self)


class GetLiveChannelResult(RequestResult, LiveChannelInfo):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        LiveChannelInfo.__init__(self)


class ListLiveChannelResult(RequestResult, LiveChannelList):
    def __init__(self, resp):
       RequestResult.__init__(self, resp)
       LiveChannelList.__init__(self)


class GetLiveChannelStatResult(RequestResult, LiveChannelStat):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        LiveChannelStat.__init__(self)

class GetLiveChannelHistoryResult(RequestResult, LiveChannelHistory):
    def __init__(self, resp):
        RequestResult.__init__(self, resp)
        LiveChannelHistory.__init__(self)
