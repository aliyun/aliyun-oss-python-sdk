# -*- coding: utf-8 -*-

"""
The data parameters in file upload methods
------------------------
For example, func:`put_object <Bucket.put_object>` has the 'data' parameter. It could be any one of the following types:
    - unicode type (for Python3 it's str): Internally it's converted to UTF-8 bytes.
    - bytes types：No convertion
    - file-like object：For seek()-able and tell()-able file object, it will read from the current position to the end. Otherwise, make sure the current position is the file start position.
    - Iterator types：The data must be iterator type if its length is not predictable. Internally it's using `Chunk encoding` for transfer.

The input parmater in bucket config update
-----------------------------
For example :func:`put_bucket_cors <Bucket.put_bucket_cors>` has `input` parameter. It could be any one of the following types:
  - Bucket config related class such as `BucketCors`
  - unicode type（For Python3, it's str）
  - UTF-8 encoded bytes
  - file-like object
  - Iterator types，uses `Chunked Encoding` for transfer
In other words, except supporting `Bucket config related class`, `input` has same types of `data` parameter.

Return value 
------
Most get methods in :class:`Service` and :class:`Bucket` return :class:`RequestResult <oss2.models.RequestResult>` or its subclasses.
`RequestResult` class defines the HTTP status code、response headers and OSS Request ID. And its subclasses define the scenario specific data that are interesting to uses.
For example,
`ListBucketsResult.buckets` returns the Bucket instance list; and `GetObjectResult` returns a file-like object which could call `read()` to get the response body.

Exceptions
----
Generally speaking Python SDK could throw 3 Exception types, which all inhert from :class:`OssError <oss2.exceptions.OssError>` ：
    - :class:`ClientError <oss2.exceptions.ClientError>`：It's the client side exception that is likely due to user's incorrect parameters of usage；
    - :class:`ServerError <oss2.exceptions.ServerError>` and its subclasses.Server side exceptions which contain error code such as 4xx or 5xx.
    - :class:`RequestError <oss2.exceptions.RequestError>` ：The underlying requests lib's exceptions, such as DNS error or timeout；
Besides, `Bucket.put_object_from_file` and `Bucket.get_object_to_file` may throw file related exceptions.


.. _byte_range:

Download range
------------
For example, :func:`get_object <Bucket.get_object>` and :func:`upload_part_copy <Bucket.upload_part_copy>` accept 'byte_range' parameters, which specifies the read range.
It's a 2-tuple: (start,last). These methods interanlly would translate the tuple into the value of Http header Range, such as:
    - For (0, 99), the translated Range header is 'bytes=0-99'，which means reading the first 100 bytes.
    - For (None, 99), the translated Range header is 'bytes=-99'，which means reading the last 99 bytes
    - For (100, None), the translated Range header is 'bytes=100-', which means reading the whole data starting from the 101th character (The index is 100 and index starts with 0).


Paging
-------
Listing APIs such as :func:`list_buckets <Service.list_buckets>` and :func:`list_objects <Bucket.list_objects>` support paging.
Specify the paging markers (e.g. marker, key_marker) to query a specific page after that marker. 
For the first page, the marker is empty, which is the by default value.
For next pages, use the next_marker or next_key_marker value as the marker value. Check the is_truncated value after each call to determine if it's the last page--false means it's the last page.

.. _progress_callback:

Upload or Download Progress
-----------
Upload or Download APIs such as `get_object`, `put_object`, `resumable_upload` support progress callback method. User can use it to implement progress bar or other functions that needs the progress data.

`progress_callback` definition ::

    def progress_callback(bytes_consumed, total_bytes):
        '''progress callback

        :param int bytes_consumed: Consumed bytes. For upload it's uploaded bytes; for download it's download bytes.
        :param int total_bytes: Total bytes.
        '''

Note that `total_bytes` has different meanings for download and upload.
    - For upload, if the input is bytes or file object supports seek/tell, it's the total size. Otherwise it's none.
    - Download: When http headers returned has content-length header, then it's the value of content-length. Otherwise it's none.


.. _unix_time:

Unix Time
---------
OSS Python SDK will automatically convert the server time to Unix time (or epoch time, `<https://en.wikipedia.org/wiki/Unix_time>`)

The common time format in OSS is:
    - HTTP Date format，like `Sat, 05 Dec 2015 11:04:39 GMT`. It's used in http headers such as If-Modified-Since or Last-Modified.
    - ISO8601 format，for example `2015-12-05T00:00:00.000Z`.
      It's used in lifecycle management configuration, create/last modified time in result of bucket list or file list.

`http_date` converts the Unix Time to HTTP Date；`http_to_unixtime` does the opposite. For example ::

    >>> import oss2, time
    >>> unix_time = int(time.time())             # Current time in UNIX Time，Value is 1449313829
    >>> date_str = oss2.http_date(unix_time)     # date_str will be 'Sat, 05 Dec 2015 11:10:29 GMT'
    >>> oss2.http_to_unixtime(date_str)          # the result is 1449313829

.. note::

    Please use `http_date` instead of 'strftime' to generate date in http protocol.Because the latter depends on the locale.
    For example, `strftime`result could contain Chinese which could not be parsed by OSS server.

`iso8601_to_unixtime` converts date in ISO8601 format to Unix Time；`date_to_iso8601` and `iso8601_to_date` does the translation between ISO8601 and datetime.date.
For example ::

    >>> import oss2
    >>> d = oss2.iso8601_to_date('2015-12-05T00:00:00.000Z')  # Gets datetime.date(2015, 12, 5)
    >>> date_str = oss2.date_to_iso8601(d)                    # Gets '2015-12-05T00:00:00.000Z'
    >>> oss2.iso8601_to_unixtime(date_str)                    # Gets 1449273600
"""

from . import xml_utils
from . import http
from . import utils
from . import exceptions
from . import defaults

from .models import *
from .compat import urlquote, urlparse, to_unicode, to_string

import time
import shutil
import oss2.utils

class _Base(object):
    def __init__(self, auth, endpoint, is_cname, session, connect_timeout,
                 app_name='', enable_crc=True):
        self.auth = auth
        self.endpoint = _normalize_endpoint(endpoint.strip())
        self.session = session or http.Session()
        self.timeout = defaults.get(connect_timeout, defaults.connect_timeout)
        self.app_name = app_name
        self.enable_crc = enable_crc

        self._make_url = _UrlMaker(self.endpoint, is_cname)

    def _do(self, method, bucket_name, key, **kwargs):
        key = to_string(key)
        req = http.Request(method, self._make_url(bucket_name, key),
                           app_name=self.app_name,
                           **kwargs)
        self.auth._sign_request(req, bucket_name, key)

        resp = self.session.do_request(req, timeout=self.timeout)
        if resp.status // 100 != 2:
            raise exceptions.make_exception(resp)
        
        # Note that connections are only released back to the pool for reuse once all body data has been read; 
        # be sure to either set stream to False or read the content property of the Response object.
        # For more details, please refer to http://docs.python-requests.org/en/master/user/advanced/#keep-alive.
        content_length = oss2.models._hget(resp.headers, 'content-length', int)
        if content_length is not None and content_length == 0:
            resp.read()

        return resp

    def _parse_result(self, resp, parse_func, klass):
        result = klass(resp)
        parse_func(result, resp.read())
        return result


class Service(_Base):
    """The class for interacting with Service. For example list all buckets.

    For example ::

        >>> import oss2
        >>> auth = oss2.Auth('your-access-key-id', 'your-access-key-secret')
        >>> service = oss2.Service(auth, 'oss-cn-hangzhou.aliyuncs.com')
        >>> service.list_buckets()
        <oss2.models.ListBucketsResult object at 0x0299FAB0>

    :param auth: the auth instance that contains access-key-id and access-key-secret.
    :type auth: oss2.Auth

    :param str endpoint: the domain of endpoint, such as 'oss-cn-hangzhou.aliyuncs.com'

    :param session: session instance. If it's None, then it will use a new session.
    :type session: oss2.Session

    :param float connect_timeout: connection timeout in seconds.
    :param str app_name: App name. If it's not null, it will be appended in User Agent header.
        Note that this value will be part of the Http header value and thus must follow the http protocol.
    """
    def __init__(self, auth, endpoint,
                 session=None,
                 connect_timeout=None,
                 app_name=''):
        super(Service, self).__init__(auth, endpoint, False, session, connect_timeout,
                                      app_name=app_name)

    def list_buckets(self, prefix='', marker='', max_keys=100):
        """List buckets by prefix

        :param str prefix: The prefix of buckets tolist. List all buckets if it's empty.
        :param str marker: The paging maker. It's empty for first page and then use next_marker in the response of the previous page.
        :param int max_keys: Max bucket count to return.

        :return: The bucket lists
        :rtype: oss2.models.ListBucketsResult
        """
        resp = self._do('GET', '', '',
                        params={'prefix': prefix,
                                'marker': marker,
                                'max-keys': str(max_keys)})
        return self._parse_result(resp, xml_utils.parse_list_buckets, ListBucketsResult)


class Bucket(_Base):
    """The class for Bucket or Object related operations, such as create, delete bucket, upload or download object.

    Examples（Assuming Bucket is in Hangzhou datacenter） ::

        >>> import oss2
        >>> auth = oss2.Auth('your-access-key-id', 'your-access-key-secret')
        >>> bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', 'your-bucket')
        >>> bucket.put_object('readme.txt', 'content of the object')
        <oss2.models.PutObjectResult object at 0x029B9930>

    :param auth: Auth object that has the user's access key id and access key secret.
    :type auth: oss2.Auth

    :param str endpoint: Domain name of endpoint or the CName.
    :param str bucket_name: Bucket name
    :param bool is_cname: True if the endpoint is CNAME; Otherwise it's False.

    :param session: Session instance. None for creating a new session.
    :type session: oss2.Session

    :param float connect_timeout: connectio timeout in seconds.

    :param str app_name: App name. If it's not empty, it would be appended in User Agent.
        Note that this value needs to follow the http header value's requirement as it's part of the User Agent header.
    """

    ACL = 'acl'
    CORS = 'cors'
    LIFECYCLE = 'lifecycle'
    LOCATION = 'location'
    LOGGING = 'logging'
    REFERER = 'referer'
    WEBSITE = 'website'
    LIVE = 'live'
    COMP = 'comp'
    STATUS = 'status'
    VOD = 'vod'
    SYMLINK = 'symlink'

    def __init__(self, auth, endpoint, bucket_name,
                 is_cname=False,
                 session=None,
                 connect_timeout=None,
                 app_name='',
                 enable_crc=True):
        super(Bucket, self).__init__(auth, endpoint, is_cname, session, connect_timeout,
                                     app_name, enable_crc)
                
        self.bucket_name = bucket_name.strip()

    def sign_url(self, method, key, expires, headers=None, params=None):
        """generate the presigned url.

        The signed url could be used for accessing the object by any user who has the url. For example, in the code below, it generates the signed url with 5 minutes TTL for log.jpg file:

            >>> bucket.sign_url('GET', 'log.jpg', 5 * 60)
            'http://your-bucket.oss-cn-hangzhou.aliyuncs.com/logo.jpg?OSSAccessKeyId=YourAccessKeyId\&Expires=1447178011&Signature=UJfeJgvcypWq6Q%2Bm3IJcSHbvSak%3D'

        :param method: HTTP method such as 'GET', 'PUT', 'DELETE', etc
        :type method: str
        :param key: object key
        :param expires: Expiration time in seconds. The url is invalid after it's expired.

        :param headers: The http headers to sign. For example the headers startign with x-oss-meta- (user's custom metadata), Content-Type, etc.
            Not needed for download.
        :type headers: Could be dict, but recommendation is oss2.CaseInsensitiveDict

        :param params: http query parameters to sign

        :return: Signed url.
        """
        key = to_string(key)
        req = http.Request(method, self._make_url(self.bucket_name, key),
                           headers=headers,
                           params=params)
        return self.auth._sign_url(req, self.bucket_name, key, expires)

    def sign_rtmp_url(self, channel_name, playlist_name, expires):
        """Sign RTMP pushing streaming url.
        It's used to push the RTMP streaming to OSS for trusted user who has the url.

        :param channel_name: channel name
        :param expires: Expiration time in seconds.The url is invalid after it's expired.
        :param playlist_name: playlist name，it should be the one created in live channel creation time.
        :param params: Http query parameters to sign.

        :return: Signed url.
        """        
        url = self._make_url(self.bucket_name, 'live').replace('http://', 'rtmp://').replace('https://', 'rtmp://') + '/' + channel_name
        params = {}
        params['playlistName'] = playlist_name
        return self.auth._sign_rtmp_url(url, self.bucket_name, channel_name, playlist_name, expires, params)

    def list_objects(self, prefix='', delimiter='', marker='', max_keys=100):
        """List objects by the prefix under a bucket.

        :param str prefix: The prefix of the objects to list. 
        :param str delimiter: The folder separator
        :param str marker: Paging marker. It's empty for first page and then use next_marker in the response of the previous page.
        :param int max_keys: Max entries to return.

        :return: :class:`ListObjectsResult <oss2.models.ListObjectsResult>`
        """
        resp = self.__do_object('GET', '',
                                params={'prefix': prefix,
                                        'delimiter': delimiter,
                                        'marker': marker,
                                        'max-keys': str(max_keys),
                                        'encoding-type': 'url'})
        return self._parse_result(resp, xml_utils.parse_list_objects, ListObjectsResult)

    def put_object(self, key, data,
                   headers=None,
                   progress_callback=None):
        """Upload a normal file (not appendable).

        Example ::
            >>> bucket.put_object('readme.txt', 'content of readme.txt')
            >>> with open(u'local_file.txt', 'rb') as f:
            >>>     bucket.put_object('remote_file.txt', f)

                Upload a folder
            >>> bucket.enable_crc = False # this is needed as by default crc is enabled and it will not work when creating folder.
            >>> bucket.put_object('testfolder/', None)

        :param key: file name in OSS

        :param data: file content.
        :type data: bytes，str or file-like object

        :param headers: Http headers. It could be content-type, Content-MD5 or x-oss-meta- prefixed headers.
        :type headers: dict，but recommendation is oss2.CaseInsensitiveDict

        :param progress_callback: The user's callback. Typical usage is progress bar. Check out :ref:`progress_callback`.

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), key)

        if progress_callback:
            data = utils.make_progress_adapter(data, progress_callback)
        
        if self.enable_crc:
            data = utils.make_crc_adapter(data)

        resp = self.__do_object('PUT', key, data=data, headers=headers)
        result = PutObjectResult(resp)
        
        if self.enable_crc and result.crc is not None:
            utils.check_crc('put', data.crc, result.crc)
            
        return result

    def put_object_from_file(self, key, filename,
                             headers=None,
                             progress_callback=None):
        """Upload a normal file to OSS.

        :param str key: file name in oss.
        :param str filename: Local file path, called needs the read permission.

        :param headers: Http headers. It could be content-type, Content-MD5 or x-oss-meta- prefixed headers.
        :type headers: dict，but recommendation is oss2.CaseInsensitiveDict

        :param progress_callback: The user's callback. Typical usage is progress bar. Check out :ref:`progress_callback`.

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), filename)

        with open(to_unicode(filename), 'rb') as f:
            return self.put_object(key, f, headers=headers, progress_callback=progress_callback)

    def append_object(self, key, position, data,
                      headers=None,
                      progress_callback=None,
                      init_crc=None):
        """Append the data to an existing object or create a new appendable file if not existing.

        :param str key: existing file name or new file name.
        :param int position: 0 for creating a new appendable file or current length for appending an existing file.
            `position` value could be from `AppendObjectResult.next_position` of the previous append_object result's.

        :param data: User data
        :type data: str、bytes、file-like object or Iterator object

        :param headers: Http headers. It could be content-type, Content-MD5 or x-oss-meta- prefixed headers.
        :type headers: dict，but recommendation is oss2.CaseInsensitiveDict

        :param progress_callback: The user's callback. Typical usage is progress bar. Check out :ref:`progress_callback`.

        :return: :class:`AppendObjectResult <oss2.models.AppendObjectResult>`

        :raises: If the position is not same as the current file's length, :class:`PositionNotEqualToLength <oss2.exceptions.PositionNotEqualToLength>` will be thrown；
                 If the file is not appendable, :class:`ObjectNotAppendable <oss2.exceptions.ObjectNotAppendable>` is thrown ；
                 Other client side exceptions could be thrown as well
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), key)

        if progress_callback:
            data = utils.make_progress_adapter(data, progress_callback)
        
        if self.enable_crc and init_crc is not None:
            data = utils.make_crc_adapter(data, init_crc)

        resp = self.__do_object('POST', key,
                                data=data,
                                headers=headers,
                                params={'append': '', 'position': str(position)})
        result =  AppendObjectResult(resp)
    
        if self.enable_crc and result.crc is not None and init_crc is not None:
            utils.check_crc('append', data.crc, result.crc)
            
        return result

    def get_object(self, key,
                   byte_range=None,
                   headers=None,
                   progress_callback=None,
                   process=None):
        """Download a file.

        Example ::

            >>> result = bucket.get_object('readme.txt')
            >>> print(result.read())
            'hello world'

        :param key: object name in OSS
        :param byte_range: Download range. Check out :ref:`byte_range` for more information.

        :param headers: HTTP headers
        :type headers: dict or oss2.CaseInsensitiveDict (recommended)

        :param progress_callback: User callback. Please check out :ref:`progress_callback`

        :param process: oss file process，For example image processing. The returne object is applied with the process.
        
        :return: file-like object

        :raises: If the file does not exist, :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` is thrown ；Other exception could also happen though.
        """
        headers = http.CaseInsensitiveDict(headers)

        range_string = _make_range_string(byte_range)
        if range_string:
            headers['range'] = range_string
        
        params = None
        if process: 
            params={'x-oss-process': process}
        
        resp = self.__do_object('GET', key, headers=headers, params=params)
        return GetObjectResult(resp, progress_callback, self.enable_crc)

    def get_object_to_file(self, key, filename,
                           byte_range=None,
                           headers=None,
                           progress_callback=None,
                           process=None):
        """Download a file to the local file.

        :param key: object name in OSS
        :param filename: Local file name. The folder of the file must be available for write and pre-existing.
        :param byte_range: The download range. Check out :ref:`byte_range`.

        :param headers: HTTP headers
        :type headers: dict or oss2.CaseInsensitiveDict (recommended)

        :param progress_callback: user callback. Check out :ref:`progress_callback`
    
        :param process: oss file process，For example image processing. The returne object is applied with the process.

        :return: If the file does not exist, :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` is thrown ；Other exception could also happen though.
        """
        with open(to_unicode(filename), 'wb') as f:
            result = self.get_object(key, byte_range=byte_range, headers=headers, progress_callback=progress_callback,
                                     process=process)

            if result.content_length is None:
                shutil.copyfileobj(result, f)
            else:
                utils.copyfileobj_and_verify(result, f, result.content_length, request_id=result.request_id)

            return result

    def head_object(self, key, headers=None):
        """Gets object metadata

        The metadata is in HTTP response headers, which could be accessed by `RequestResult.headers`.
        Usage ::

            >>> result = bucket.head_object('readme.txt')
            >>> print(result.content_type)
            text/plain

        :param key: object name in OSS

        :param headers: HTTP headers.
        :type headers: dict or oss2.CaseInsensitiveDict (recommended)

        :return: :class:`HeadObjectResult <oss2.models.HeadObjectResult>`

        :raises: If the bucket or file does not exist, :class:`NotFound <oss2.exceptions.NotFound>` is thrown.
        """
        resp = self.__do_object('HEAD', key, headers=headers)
        return HeadObjectResult(resp)
    
    def get_object_meta(self, key):
        """Gets the object's basic metadata, which includes ETag, Size, LastModified.

        The metadata is in HTTP response headers, which could be accessed by `GetObjectMetaResult`'s 'last_modified`，`content_length`,`etag`

        :param key: object key in OSS.

        :return: :class:`GetObjectMetaResult <oss2.models.GetObjectMetaResult>`

        :raises: If file does not exist, :class:`NoSuchKey <oss2.exceptions.NoSuchKey>` is thrown；Other exception could also happen though.
        """
        resp = self.__do_object('GET', key, params={'objectMeta': ''})
        return GetObjectMetaResult(resp)

    def object_exists(self, key):
        """If the file exists, return true. Otherwise false. If the bucket does not exist or other errors happen, exceptions will be thrown."""

        # If head_object is used as the implementation, as it only has response header, when 404 is returned, no way to tell if it's a NoSuchBucket or NoSuchKey.
        #
        # Before version 2.2.0, it calls get_object with current + 24h as the if-modified-since parameter.
        # If file exists, it returns 304 (NotModified); If file does not exists, returns NoSuchkey. 
        # However get_object would retrieve object in other sites if "Retrieve from source" is set and object is not found in OSS.
        # That is the file could be from other sites and thus should have return 404 instead of the object in this case.
        # 
        # So the current solution is to call get_object_meta which is not impacted by "Retrieve from source" feature.
        # Meanwhile it could differentiate bucket not found or key not found.

        try:
            self.get_object_meta(key)
        except exceptions.NoSuchKey:
            return False
        except:
            raise
        
        return True

    def copy_object(self, source_bucket_name, source_key, target_key, headers=None):
        """Copy a file to current bucket.

        :param str source_bucket_name: Source bucket name
        :param str source_key: Source file name
        :param str target_key: Target file name

        :param headers: HTTP headers
        :type headers: dict or oss2.CaseInsensitiveDict (recommended)

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = http.CaseInsensitiveDict(headers)
        headers['x-oss-copy-source'] = '/' + source_bucket_name + '/' + urlquote(source_key, '')

        resp = self.__do_object('PUT', target_key, headers=headers)

        return PutObjectResult(resp)

    def update_object_meta(self, key, headers):
        """Update Object's metadata information, including HTTP standard headers such as Content-Type or x-oss-meta- prefixed custom metadata.
        If user specifies invalid headers (e.g. not standard headers or non x-oss-meta- headers), the call would still succeed but no operation is done in server side.

        User could call :func:`head_object` to get the updated information. Note that get_object_meta does return all metadata, but head_object does.

        :param str key: object key

        :param headers: HTTP headers, it could be a dict or oss2.CaseInsensitiveDict (recommended)

        :return: :class:`RequestResult <oss2.models.RequestResults>`
        """
        return self.copy_object(self.bucket_name, key, key, headers=headers)

    def delete_object(self, key):
        """Delete a file

        :param str key: object key

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        resp = self.__do_object('DELETE', key)
        return RequestResult(resp)

    def put_object_acl(self, key, permission):
        """Sets the object ACL

        :param str key: object name
        :param str permission: Valid values are oss2.OBJECT_ACL_DEFAULT、oss2.OBJECT_ACL_PRIVATE、oss2.OBJECT_ACL_PUBLIC_READ or
            oss2.OBJECT_ACL_PUBLIC_READ_WRITE.

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        resp = self.__do_object('PUT', key, params={'acl': ''}, headers={'x-oss-object-acl': permission})
        return RequestResult(resp)

    def get_object_acl(self, key):
        """Gets the object ACL

        :return: :class:`GetObjectAclResult <oss2.models.GetObjectAclResult>`
        """
        resp = self.__do_object('GET', key, params={'acl': ''})
        return self._parse_result(resp, xml_utils.parse_get_object_acl, GetObjectAclResult)

    def batch_delete_objects(self, key_list):
        """delete objects specified in key_list.

        :param key_list: object key list, non-empty.
        :type key_list: list of str

        :return: :class:`BatchDeleteObjectsResult <oss2.models.BatchDeleteObjectsResult>`
        """
        if not key_list:
            raise ClientError('key_list should not be empty')

        data = xml_utils.to_batch_delete_objects_request(key_list, False)
        resp = self.__do_object('POST', '',
                                data=data,
                                params={'delete': '', 'encoding-type': 'url'},
                                headers={'Content-MD5': utils.content_md5(data)})
        return self._parse_result(resp, xml_utils.parse_batch_delete_objects, BatchDeleteObjectsResult)

    def init_multipart_upload(self, key, headers=None):
        """initialize a multipart upload.

        `upload_id`, Bucket name and object key in the returned value forms a 3-tuple which is a unique id for the upload.

        :param str key: object key

        :param headers: HTTP headers
        :type headers: dict or oss2.CaseInsensitiveDict (recommended)

        :return: :class:`InitMultipartUploadResult <oss2.models.InitMultipartUploadResult>`
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), key)

        resp = self.__do_object('POST', key, params={'uploads': ''}, headers=headers)
        return self._parse_result(resp, xml_utils.parse_init_multipart_upload, InitMultipartUploadResult)

    def upload_part(self, key, upload_id, part_number, data, progress_callback=None, headers=None):
        """upload a part

        :param str key: object key, must be same as the on in :func:`init_multipart_upload`.
        :param str upload_id: upload Id
        :param int part_number: part number, starting with 1.
        :param data: data to upload
        :param progress_callback: user callback. Check out :ref:`progress_callback`.

        :param headers: http headers. such as Content-MD5
        :type headers: dict or oss2.CaseInsensitiveDict (recommended)

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        if progress_callback:
            data = utils.make_progress_adapter(data, progress_callback)
        
        if self.enable_crc:
            data = utils.make_crc_adapter(data)

        resp = self.__do_object('PUT', key,
                                params={'uploadId': upload_id, 'partNumber': str(part_number)},
                                headers=headers,
                                data=data)
        result = PutObjectResult(resp)
    
        if self.enable_crc and result.crc is not None:
            utils.check_crc('put', data.crc, result.crc)
        
        return result

    def complete_multipart_upload(self, key, upload_id, parts, headers=None):
        """Completes a multipart upload. A file would be created with all the parts' data and these parts will not be available to user.

        :param str key: The object key which should be same as the on in :func:`init_multipart_upload`.
        :param str upload_id: upload id.

        :param parts: PartInfo list. The part_number and Etag are required in PartInfo. The etag comes from the result of :func:`upload_part`.
        :type parts: list of `PartInfo <oss2.models.PartInfo>`

        :param headers: HTTP headers
        :type headers: dict or oss2.CaseInsensitiveDict (recommended)

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        data = xml_utils.to_complete_upload_request(sorted(parts, key=lambda p: p.part_number))
        resp = self.__do_object('POST', key,
                                params={'uploadId': upload_id},
                                data=data,
                                headers=headers)

        return PutObjectResult(resp)

    def abort_multipart_upload(self, key, upload_id):
        """abort a multipart upload.

        :param str key: The object key, must be same as the one in :func:`init_multipart_upload`.
        :param str upload_id: Upload Id.

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        resp = self.__do_object('DELETE', key,
                                params={'uploadId': upload_id})
        return RequestResult(resp)

    def list_multipart_uploads(self,
                               prefix='',
                               delimiter='',
                               key_marker='',
                               upload_id_marker='',
                               max_uploads=1000):
        """Lists all the ongoing uploads,and it supports paging.

        :param str prefix: Prefix filter
        :param str delimiter: delimiter of folder
        :param str key_marker: Key marker for paging. 
        :param str upload_id_marker: It's empty for first page and then use next_marker in the response of the previous page.
        :param int max_uploads: Max entries to return.

        :return: :class:`ListMultipartUploadsResult <oss2.models.ListMultipartUploadsResult>`
        """
        resp = self.__do_object('GET', '',
                                params={'uploads': '',
                                        'prefix': prefix,
                                        'delimiter': delimiter,
                                        'key-marker': key_marker,
                                        'upload-id-marker': upload_id_marker,
                                        'max-uploads': str(max_uploads),
                                        'encoding-type': 'url'})
        return self._parse_result(resp, xml_utils.parse_list_multipart_uploads, ListMultipartUploadsResult)

    def upload_part_copy(self, source_bucket_name, source_key, byte_range,
                         target_key, target_upload_id, target_part_number,
                         headers=None):
        """Uploads a part from another file.

        :param byte_range: The range to copy in the source file :ref:`byte_range`

        :param headers: HTTP headers
        :type headers: dict or oss2.CaseInsensitiveDict (recommended)

        :return: :class:`PutObjectResult <oss2.models.PutObjectResult>`
        """
        headers = http.CaseInsensitiveDict(headers)
        headers['x-oss-copy-source'] = '/' + source_bucket_name + '/' + source_key

        range_string = _make_range_string(byte_range)
        if range_string:
            headers['x-oss-copy-source-range'] = range_string

        resp = self.__do_object('PUT', target_key,
                                params={'uploadId': target_upload_id,
                                        'partNumber': str(target_part_number)},
                                headers=headers)

        return PutObjectResult(resp)

    def list_parts(self, key, upload_id,
                   marker='', max_parts=1000):
        """Lists uploaded parts and it supports paging. As comparison, list_multipart_uploads lists ongoing parts.

        :param str key: object key.
        :param str upload_id: upload Id.
        :param str marker: key marker for paging.
        :param int max_parts: Max entries to return.

        :return: :class:`ListPartsResult <oss2.models.ListPartsResult>`
        """
        resp = self.__do_object('GET', key,
                                params={'uploadId': upload_id,
                                        'part-number-marker': marker,
                                        'max-parts': str(max_parts)})
        return self._parse_result(resp, xml_utils.parse_list_parts, ListPartsResult)
    
    def put_symlink(self, target_key, symlink_key, headers=None):
        """Creates a symbolic file

        :param str target_key: Target file, which cannot be another symbolic file.
        :param str symlink_key: The symbolic file name.
        
        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        headers = headers or {}
        headers['x-oss-symlink-target'] = urlquote(target_key, '')
        resp = self.__do_object('PUT', symlink_key, headers=headers, params={Bucket.SYMLINK: ''})
        return RequestResult(resp)

    def get_symlink(self, symlink_key):
        """Gets the symbolic file's information.

        :param str symlink_key: The symbolic file key.

        :return: :class:`GetSymlinkResult <oss2.models.GetSymlinkResult>`

        :raises: If the symbolic file does not exist，:class:`NoSuchKey <oss2.exceptions.NoSuchKey>` is thrown ；
                 If the key is the symbolic file, then ServerError with error code NotSymlink is returned. Other exceptions are also possible though.
        """
        resp = self.__do_object('GET', symlink_key, params={Bucket.SYMLINK: ''})
        return GetSymlinkResult(resp)

    def create_bucket(self, permission=None):
        """Creates a new bucket。

        :param str permission: Bucket ACL. It could be oss2.BUCKET_ACL_PRIVATE（recommended,default value) or oss2.BUCKET_ACL_PUBLIC_READ or 
            oss2.BUCKET_ACL_PUBLIC_READ_WRITE.
        """
        if permission:
            headers = {'x-oss-acl': permission}
        else:
            headers = None
        resp = self.__do_bucket('PUT', headers=headers)
        return RequestResult(resp)

    def delete_bucket(self):
        """Deletes a bucket. A bucket could be deleted only when the bucket is empty.

        :return: :class:`RequestResult <oss2.models.RequestResult>`

        ":raises: If the bucket is not empty，:class:`BucketNotEmpty <oss2.exceptions.BucketNotEmpty>` is thrown
        """
        resp = self.__do_bucket('DELETE')
        return RequestResult(resp)

    def put_bucket_acl(self, permission):
        """Sets the bucket ACL.

        :param str permission: The value could be oss2.BUCKET_ACL_PRIVATE、oss2.BUCKET_ACL_PUBLIC_READ或
            oss2.BUCKET_ACL_PUBLIC_READ_WRITE
        """
        resp = self.__do_bucket('PUT', headers={'x-oss-acl': permission}, params={Bucket.ACL: ''})
        return RequestResult(resp)

    def get_bucket_acl(self):
        """Gets bucket ACL

        :return: :class:`GetBucketAclResult <oss2.models.GetBucketAclResult>`
        """
        resp = self.__do_bucket('GET', params={Bucket.ACL: ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_acl, GetBucketAclResult)

    def put_bucket_cors(self, input):
        """Sets the bucket CORS.

        :param input: :class:`BucketCors <oss2.models.BucketCors>` instance or data could be converted to BucketCor by xml_utils.to_put_bucket_cors.
        """
        data = self.__convert_data(BucketCors, xml_utils.to_put_bucket_cors, input)
        resp = self.__do_bucket('PUT', data=data, params={Bucket.CORS: ''})
        return RequestResult(resp)

    def get_bucket_cors(self):
        """Gets the bucket's CORS.

        :return: :class:`GetBucketCorsResult <oss2.models.GetBucketCorsResult>`
        """
        resp = self.__do_bucket('GET', params={Bucket.CORS: ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_cors, GetBucketCorsResult)

    def delete_bucket_cors(self):
        """Deletes the bucket's CORS"""
        resp = self.__do_bucket('DELETE', params={Bucket.CORS: ''})
        return RequestResult(resp)

    def put_bucket_lifecycle(self, input):
        """Sets the life cycle of the bucket.

        :param input: :class:`BucketLifecycle <oss2.models.BucketLifecycle>` instance or data could be convered to BucketLifecycle by xml_utils.to_put_bucket_lifecycle.
        """
        data = self.__convert_data(BucketLifecycle, xml_utils.to_put_bucket_lifecycle, input)
        resp = self.__do_bucket('PUT', data=data, params={Bucket.LIFECYCLE: ''})
        return RequestResult(resp)

    def get_bucket_lifecycle(self):
        """Gets the bucket lifecycle.

        :return: :class:`GetBucketLifecycleResult <oss2.models.GetBucketLifecycleResult>`

        :raises: If the life cycle is not set in the bucket, :class:`NoSuchLifecycle <oss2.exceptions.NoSuchLifecycle>` is thrown.
        """
        resp = self.__do_bucket('GET', params={Bucket.LIFECYCLE: ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_lifecycle, GetBucketLifecycleResult)

    def delete_bucket_lifecycle(self):
        """Deletes the life cycle of the bucket. It still return 200 OK if the life cycle does not exist."""
        resp = self.__do_bucket('DELETE', params={Bucket.LIFECYCLE: ''})
        return RequestResult(resp)

    def get_bucket_location(self):
        """Gets the bucket location.

        :return: :class:`GetBucketLocationResult <oss2.models.GetBucketLocationResult>`
        """
        resp = self.__do_bucket('GET', params={Bucket.LOCATION: ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_location, GetBucketLocationResult)

    def put_bucket_logging(self, input):
        """Sets the bucket's logging.

        :param input: :class:`BucketLogging <oss2.models.BucketLogging>` instance or other data that could be converted to BucketLogging by xml_utils.to_put_bucket_logging.
        """
        data = self.__convert_data(BucketLogging, xml_utils.to_put_bucket_logging, input)
        resp = self.__do_bucket('PUT', data=data, params={Bucket.LOGGING: ''})
        return RequestResult(resp)

    def get_bucket_logging(self):
        """Gets the bucket's logging.

        :return: :class:`GetBucketLoggingResult <oss2.models.GetBucketLoggingResult>`
        """
        resp = self.__do_bucket('GET', params={Bucket.LOGGING: ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_logging, GetBucketLoggingResult)

    def delete_bucket_logging(self):
        """Deletes the bucket's logging configuration---the existing logging files are not deleted."""
        resp = self.__do_bucket('DELETE', params={Bucket.LOGGING: ''})
        return RequestResult(resp)

    def put_bucket_referer(self, input):
        """Sets the bucket's allowed referer.

        :param input: :class:`BucketReferer <oss2.models.BucketReferer>` instance or other data that could be convered to BucketReferer by xml_utils.to_put_bucket_referer.
        """
        data = self.__convert_data(BucketReferer, xml_utils.to_put_bucket_referer, input)
        resp = self.__do_bucket('PUT', data=data, params={Bucket.REFERER: ''})
        return RequestResult(resp)

    def get_bucket_referer(self):
        """Gets the bucket's allowed referer.

        :return: :class:`GetBucketRefererResult <oss2.models.GetBucketRefererResult>`
        """
        resp = self.__do_bucket('GET', params={Bucket.REFERER: ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_referer, GetBucketRefererResult)

    def put_bucket_website(self, input):
        """Sets the static website config for the bucket.

        :param input: :class:`BucketWebsite <oss2.models.BucketWebsite>`
        """
        data = self.__convert_data(BucketWebsite, xml_utils.to_put_bucket_website, input)
        resp = self.__do_bucket('PUT', data=data, params={Bucket.WEBSITE: ''})
        return RequestResult(resp)

    def get_bucket_website(self):
        """Gets the static website config.

        :return: :class:`GetBucketWebsiteResult <oss2.models.GetBucketWebsiteResult>`

        :raises: If the static website config is not set, :class:`NoSuchWebsite <oss2.exceptions.NoSuchWebsite>` is thrown.
        """
        resp = self.__do_bucket('GET', params={Bucket.WEBSITE: ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_websiste, GetBucketWebsiteResult)

    def delete_bucket_website(self):
        """关闭Bucket的静态网站托管功能。"""
        resp = self.__do_bucket('DELETE', params={Bucket.WEBSITE: ''})
        return RequestResult(resp)

    def create_live_channel(self, channel_name, input):
        """Creates a live channel.

        :param str channel_name: The live channel name.
        :param input: LiveChannelInfo instance, which includes the live channel's description information.

        :return: :class:`CreateLiveChannelResult <oss2.models.CreateLiveChannelResult>`
        """
        data = self.__convert_data(LiveChannelInfo, xml_utils.to_create_live_channel, input)
        resp = self.__do_object('PUT', channel_name, data=data, params={Bucket.LIVE: ''})
        return self._parse_result(resp, xml_utils.parse_create_live_channel, CreateLiveChannelResult)

    def delete_live_channel(self, channel_name):
        """Deletes the live channel.

        :param str channel_name: The live channel name.
        """
        resp = self.__do_object('DELETE', channel_name, params={Bucket.LIVE: ''})
        return RequestResult(resp)

    def get_live_channel(self, channel_name):
        """Gets the live channel configuration.

        :param str channel_name: live channel name

        :return: :class:`GetLiveChannelResult <oss2.models.GetLiveChannelResult>`
        """
        resp = self.__do_object('GET', channel_name, params={Bucket.LIVE: ''})
        return self._parse_result(resp, xml_utils.parse_get_live_channel, GetLiveChannelResult)

    def list_live_channel(self, prefix='', marker='', max_keys=100):
        """Lists all live channels under the bucket according to the prefix and marker filters

        param: str prefix: The channel Id must start with this prefix.
        param: str marker: The channel Id marker for paging.
        param: int max_keys: The max channel  count to return.

        return: :class:`ListLiveChannelResult <oss2.models.ListLiveChannelResult>`
        """
        resp = self.__do_bucket('GET', params={Bucket.LIVE: '',
                                               'prefix': prefix,
                                               'marker': marker,
                                               'max-keys': str(max_keys)})
        return self._parse_result(resp, xml_utils.parse_list_live_channel, ListLiveChannelResult)

    def get_live_channel_stat(self, channel_name):
        """Gets the live channel's pushing streaming status.

        param str channel_name: The live channel name

        return: :class:`GetLiveChannelStatResult <oss2.models.GetLiveChannelStatResult>`
        """
        resp = self.__do_object('GET', channel_name, params={Bucket.LIVE: '', Bucket.COMP: 'stat'})
        return self._parse_result(resp, xml_utils.parse_live_channel_stat, GetLiveChannelStatResult)

    def put_live_channel_status(self, channel_name, status):
        """Update the live channel's status. Supported status is “enabled” or “disabled”.

        param str channel_name: live channel name,
        param str status: live channel's desired status
        """
        resp = self.__do_object('PUT', channel_name, params={Bucket.LIVE: '', Bucket.STATUS: status})
        return RequestResult(resp)

    def get_live_channel_history(self, channel_name):
        """Gets the up to 10's recent pushing streaming record of the live channel. Each record includes the 
        start/end time and the remote address (the source of the pushing streaming).

        param str channel_name: live channel name.

        return: :class:`GetLiveChannelHistoryResult <oss2.models.GetLiveChannelHistoryResult>`
        """
        resp = self.__do_object('GET', channel_name, params={Bucket.LIVE: '', Bucket.COMP: 'history'})
        return self._parse_result(resp, xml_utils.parse_live_channel_history, GetLiveChannelHistoryResult)

    def post_vod_playlist(self, channel_name, playlist_name, start_time = 0, end_time = 0):
        """Generates a VOD play list according to the play list name, start time and end time. 

        param str channel_name: Live channel name.
        param str playlist_name: The play list name (*.m3u8 file)
        param int start_time: Start time in Unix Time，which could be got from int(time.time())
        param int end_time: End time in Unix Time，which could be got from int(time.time())
        """
        key = channel_name + "/" + playlist_name
        resp = self.__do_object('POST', key, params={Bucket.VOD: '',
                                                            'startTime': str(start_time),
                                                            'endTime': str(end_time)})
        return RequestResult(resp)

    def _get_bucket_config(self, config):
        """Gets the bucket config.
        The raw xml string could be get by result.read() (not recommended though).

        :param str config: Supported values are `Bucket.ACL` 、 `Bucket.LOGGING`, etc (check out the beginning part of Bucket class for the complete list).

        :return: :class:`RequestResult <oss2.models.RequestResult>`
        """
        return self.__do_bucket('GET', params={config: ''})

    def __do_object(self, method, key, **kwargs):
        return self._do(method, self.bucket_name, key, **kwargs)

    def __do_bucket(self, method, **kwargs):
        return self._do(method, self.bucket_name, '', **kwargs)

    def __convert_data(self, klass, converter, data):
        if isinstance(data, klass):
            return converter(data)
        else:
            return data


def _normalize_endpoint(endpoint):
    if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
        return 'http://' + endpoint
    else:
        return endpoint


_ENDPOINT_TYPE_ALIYUN = 0
_ENDPOINT_TYPE_CNAME = 1
_ENDPOINT_TYPE_IP = 2


def _make_range_string(range):
    if range is None:
        return ''

    start = range[0]
    last = range[1]

    if start is None and last is None:
        return ''

    return 'bytes=' + _range(start, last)


def _range(start, last):
    def to_str(pos):
        if pos is None:
            return ''
        else:
            return str(pos)

    return to_str(start) + '-' + to_str(last)


def _determine_endpoint_type(netloc, is_cname, bucket_name):
    if utils.is_ip_or_localhost(netloc):
        return _ENDPOINT_TYPE_IP

    if is_cname:
        return _ENDPOINT_TYPE_CNAME

    if utils.is_valid_bucket_name(bucket_name):
        return _ENDPOINT_TYPE_ALIYUN
    else:
        return _ENDPOINT_TYPE_IP


class _UrlMaker(object):
    def __init__(self, endpoint, is_cname):
        p = urlparse(endpoint)

        self.scheme = p.scheme
        self.netloc = p.netloc
        self.is_cname = is_cname

    def __call__(self, bucket_name, key):
        self.type = _determine_endpoint_type(self.netloc, self.is_cname, bucket_name)

        key = urlquote(key, '')

        if self.type == _ENDPOINT_TYPE_CNAME:
            return '{0}://{1}/{2}'.format(self.scheme, self.netloc, key)

        if self.type == _ENDPOINT_TYPE_IP:
            if bucket_name:
                return '{0}://{1}/{2}/{3}'.format(self.scheme, self.netloc, bucket_name, key)
            else:
                return '{0}://{1}/{2}'.format(self.scheme, self.netloc, key)

        if not bucket_name:
            assert not key
            return '{0}://{1}'.format(self.scheme, self.netloc)

        return '{0}://{1}.{2}/{3}'.format(self.scheme, bucket_name, self.netloc, key)
