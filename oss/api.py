# -*- coding: utf-8 -*-

"""
oss.api
~~~~~~~

这个模块包含了用于访问OSS的底层接口。

对象上传方法中的data参数
----------------------
诸如 :func:`put_object <Bucket.put_object>` 这样的上传接口都会有 `data` 参数用于接收用户数据。`data` 可以是下述类型
    - unicode类型（对于Python3则是str类型）
    - 经过utf-8编码的bytes类型
    - file-like object
    - 可迭代类型，会通过chunked编码传输


Bucket配置修改方法中的input参数
-----------------------------
诸如 :func:`put_bucket_cors <Bucket.put_bucket_cors>` 这样的Bucket配置修改接口都会有 `input` 参数接收用户提供的配置数据。
`input` 可以是下述类型
  - Bucket配置信息相关的类，如 `BucketCors`
  - unicode类型（对于Python3则是str类型）
  - 经过utf-8编码的bytes类型
  - file-like object
  - 可迭代类型，会通过chunked编码传输


返回值
------
:class:`Service` 和 :class:`Bucket` 类的大多数方法都是返回 :class:`RequestResult <oss.models.RequestResult>`
及其子类。`RequestResult` 包含了HTTP响应的状态码、头部以及OSS Request ID，而它的子类则包含用户真正想要的结果。例如，
`ListBucketsResult.buckets` 就是返回的Bucket信息列表；`GetObjectResult` 则是一个file-like object，可以调用`read()`来获取响应的
HTTP包体。


异常
----
当HTTP请求失败时，即响应状态码不是2XX时，如无特殊说明都会抛出 :class:`OssError <oss.exceptions.OssError>` 异常或是其子类。


.. _range:

对象下载方法中的range参数
-----------------------
诸如 :func:`get_object <Bucket.get_object>` 以及 :func:`upload_part_copy <Bucket.upload_part_copy>` 这样的函数，可以接受
range参数，表明读取数据的范围。Range是一个二元tuple：(start, last)。这些接口会把它转换为Range头部的值，如：
    - range 为 (0, 99) 转换为 'bytes=0-99'，表示读取前100个字节
    - range 为 (None, 99) 转换为 'bytes=-99'
    - range 为 (100, None) 转换为 'bytes=100-'，表示读取第101个字节到对象结尾的部分


分页罗列
-------
罗列各种资源的接口，如 :func:`list_buckets <Service.list_buckets>` 、 :func:`list_objects <Bucket.list_objects>` 都支持
分页查询。通过设定分页标记（如：`marker` 、 `key_marker` ）的方式可以指定查询某一页。首次调用将分页标记设为空（缺省值，可以不设），
后续的调用使用返回值中的 `next_marker` 、 `next_key_marker` 等。每次调用后检查返回值中的 `is_truncated` ，其值为 `False` 说明
已经到了最后一页。
"""

from . import xml_utils
from . import http
from . import utils
from . import exceptions

from .models import *
from .compat import urlquote, urlparse

import time

class _Base(object):
    def __init__(self, auth, endpoint, is_cname, session):
        self.auth = auth
        self.endpoint = _normalize_endpoint(endpoint)
        self.session = session or http.Session()

        self._make_url = _UrlMaker(self.endpoint, is_cname)

    def _do(self, method, bucket_name, object_name, **kwargs):
        req = http.Request(method, self._make_url(bucket_name, object_name), **kwargs)
        self.auth._sign_request(req, bucket_name, object_name)

        resp = self.session.do_request(req)
        if resp.status // 100 != 2:
            raise exceptions.make_exception(resp)

        return resp

    def _parse_result(self, resp, parse_func, klass):
        result = klass(resp)
        parse_func(result, resp.read())
        return result


class Service(_Base):
    """用于Service操作的类，如罗列用户所有的Bucket。

    用法::

        >>> import oss
        >>> auth = oss.Auth('your-access-key-id', 'your-access-key-secret')
        >>> service = oss.Service(auth, 'oss-cn-hangzhou.aliyuncs.com')
        >>> service.list_buckets()
        <oss.models.ListBucketsResult object at 0x0299FAB0>

    :param auth: 包含了用户认证信息的Auth对象
    :param endpoint: 访问域名，如杭州区域的域名为oss-cn-hangzhou.aliyuncs.com
    :param session: 会话。如果是None表示新开会话，非None则复用传入的会话
    :type session: Session或None
    """
    def __init__(self, auth, endpoint,
                 session=None):
        super(Service, self).__init__(auth, endpoint, False, session)

    def list_buckets(self, prefix='', marker='', max_keys=100):
        """根据前缀罗列用户的Bucket。

        :param prefix: 只罗列Bucket名为该前缀的Bucket，空串表示罗列所有的Bucket
        :param marker: 分页标志。首次调用传空串，后续使用返回值的next_marker
        :param max_keys: 每次调用最多返回的Bucket数目

        :return: 罗列的结果
        :rtype: :class:`ListBucketsResult <oss.models.ListBucketsResult>`
        """
        resp = self._do('GET', '', '',
                        params={'prefix': prefix,
                                'marker': marker,
                                'max-keys': max_keys})
        return self._parse_result(resp, xml_utils.parse_list_buckets, ListBucketsResult)


class Bucket(_Base):
    """用于Bucket和Object操作的类，诸如创建、删除Bucket，上传、下载对象等。

    用法::
        >>> import oss
        >>> auth = oss.Auth('your-access-key-id', 'your-access-key-secret')
        >>> bucket = oss.Bucket(auth, 'oss-cn-beijing.aliyuncs.com', 'your-bucket')
        >>> bucket.put_object('readme.txt', 'content of the object')
        <oss.models.PutObjectResult object at 0x029B9930>

    :param auth: 包含了用户认证信息的Auth对象
    :param endpoint: 访问域名或者CNAME
    :param bucket_name: Bucket名
    :param is_cname: 如果`endpoint`是CNAME则设为True;如果是诸如oss-cn-hangzhou.aliyuncs.com的域名则为False
    :param session: 会话。如果是None表示新开会话，非None则复用传入的会话
    :type session: Session或None
    """
    def __init__(self, auth, endpoint, bucket_name,
                 is_cname=False,
                 session=None):
        super(Bucket, self).__init__(auth, endpoint, is_cname, session)
        self.bucket_name = bucket_name

    def sign_url(self, method, object_name, expires, headers=None, params=None):
        """生成签名URL。

        常见的用法是生成加签的URL以供授信用户下载，如为log.jpg生成一个5分钟后过期的下载链接::

            >>> bucket._sign_url('GET', 'log.jpg', 5 * 60)
            'http://your-bucket.oss-cn-hangzhou.aliyuncs.com/logo.jpg?OSSAccessKeyId=YourAccessKeyId\&Expires=1447178011&Signature=UJfeJgvcypWq6Q%2Bm3IJcSHbvSak%3D'

        :param method: HTTP方法，如'GET'、'PUT'、'DELETE'等
        :type method: str
        :param object_name: 对象名
        :param expires: 过期时间（单位：秒），链接在当前时间再过expires秒后过期
        :param headers: 需要签名的HTTP头部，如名称以x-oss-开头的头部、Content-Type头部等。对于下载，不需要填。
        :param params: 需要签名的HTTP查询参数

        :return: 签名URL。
        """
        req = http.Request(method, self._make_url(self.bucket_name, object_name),
                           headers=headers,
                           params=params)
        return self.auth._sign_url(req, self.bucket_name, object_name, expires)

    def list_objects(self, prefix='', delimiter='', marker='', max_keys=100):
        """根据前缀罗列Bucket里的对象。

        :param prefix: 只罗列以文件名为该前缀的对象
        :param delimiter: 分隔符，可以用来模拟目录
        :param marker: 分页标志。首次调用传空串，后续使用返回值的next_marker
        :param max_keys: 最多返回对象的个数，对象和目录的和不能超过该值

        :return: :class:`ListObjectsResult <oss.models.ListObjectsResult>`
        """
        resp = self.__do_object('GET', '',
                                params={'prefix': prefix,
                                        'delimiter': delimiter,
                                        'marker': marker,
                                        'max-keys': max_keys,
                                        'encoding-type': 'url'})
        return self._parse_result(resp, xml_utils.parse_list_objects, ListObjectsResult)

    def put_object(self, object_name, data, headers=None):
        """上传一个普通对象。

        :param object_name: 上传到OSS的对象名
        :param data: 待上传的内容。
        :type data: bytes，str或file-like object
        :param headers: 用户指定的HTTP头部。可以指定Content-Type、Content-MD5、x-oss-开头的头部等

        :return: :class:`PutObjectResult <oss.models.PutObjectResult>`

        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), object_name)

        resp = self.__do_object('PUT', object_name, data=data, headers=headers)
        return PutObjectResult(resp)

    def append_object(self, object_name, position, data, headers=None):
        """追加上传一个对象。

        :param object_name: 新的对象名，或已经存在的可追加对象名
        :param position: 追加上传一个新的对象， `position` 设为0；追加一个已经存在的可追加对象， `position` 设为对象的当前长度。
            position可以从上次追加的结果 `AppendObjectResult.next_position` 中获得。
        :param data: 用户数据
        :type data: str、bytes、file-like object或可迭代对象
        :param headers: 用户指定的HTTP头部。可以指定Content-Type、Content-MD5、x-oss-开头的头部等

        :return: :class:`AppendObjectResult <oss.models.AppendObjectResult>`

        :raises: 如果 `position` 和对象当前文件长度不一致，抛出 :class:`PositionNotEqualToLength <oss.exceptions.PositionNotEqualToLength>` ；
                 如果当前对象不是可追加类型，抛出 :class:`ObjectNotAppendable <oss.exceptions.ObjectNotAppendable>` ；
                 还会抛出其他一些异常
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), object_name)

        resp = self.__do_object('POST', object_name,
                                data=data,
                                headers=headers,
                                params={'append': '', 'position': str(position)})
        return AppendObjectResult(resp)

    def get_object(self, object_name, range=None, headers=None):
        """下载一个对象。

        用法::

            >>> result = bucket.get_object('readme.txt')
            >>> print(result.read())
            'hello world'

        :param object_name: 对象名
        :param range: 指定下载范围。参见 :ref:`range`
        :param headers: HTTP头部

        :return: file-like object

        :raises: 如果对象不存在，则抛出 :class:`NoSuchKey <oss.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        headers = http.CaseInsensitiveDict(headers)

        range_string = _make_range_string(range)
        if range_string:
            headers['range'] = range_string

        resp = self.__do_object('GET', object_name, headers=headers)
        return GetObjectResult(resp)

    def head_object(self, object_name, headers=None):
        """获取对象元信息。

        HTTP响应的头部包含了对象元信息，可以通过 `RequestResult` 的 `headers` 成员获得。

        :param object_name: 对象名
        :param headers: HTTP头部

        :return: :class:`RequestResult <oss.models.RequestResults>`

        :raises: 如果对象不存在，则抛出 :class:`NoSuchKey <oss.exceptions.NoSuchKey>` ；还可能抛出其他异常
        """
        resp = self.__do_object('HEAD', object_name, headers=headers)
        return RequestResult(resp)

    def object_exists(self, object_name):
        """如果对象存在就返回True，否则返回False。如果Bucket不存在，或是发生其他错误，则抛出异常。"""

        # 如果我们用head_object来实现的话，由于HTTP HEAD请求没有响应体，只有响应头部，这样当发生404时，
        # 我们无法区分是NoSuchBucket还是NoSuchKey错误。
        #
        # 下面的实现是通过if-modified-since头部，把date设为当前时间1小时后，这样如果对象存在，则会返回
        # 304 (NotModified)；不存在，则会返回NoSuchKey
        date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time() + 60 * 60))

        try:
            self.get_object(object_name, headers={'if-modified-since': date})
        except exceptions.NotModified:
            return True
        except exceptions.NoSuchKey:
            return False
        else:
            raise RuntimeError('This is impossible')

    def copy_object(self, source_bucket_name, source_object_name, target_object_name, headers=None):
        """拷贝一个对象到当前Bucket。

        :param source_bucket_name: 源Bucket名
        :param source_object_name: 源对象名
        :param target_object_name: 目标对象名
        :param headers: HTTP头部

        :return: :class:`PutObjectResult <oss.models.PutObjectResult>`
        """
        headers = http.CaseInsensitiveDict(headers)
        headers['x-oss-copy-source'] = '/' + source_bucket_name + '/' + source_object_name

        resp = self.__do_object('PUT', target_object_name, headers=headers)
        return PutObjectResult(resp)

    def delete_object(self, object_name):
        """删除一个对象。

        :param object_name: 对象名

        :return: :class:`RequestResult <oss.models.RequestResult>`
        """
        resp = self.__do_object('DELETE', object_name)
        return RequestResult(resp)

    def put_object_acl(self, object_name, permission):
        """设置对象的ACL。

        :param object_name: 对象名
        :param permission: 可以是'private'、'public-read'或'public-read-write'

        :return: :class:`RequestResult <oss.models.RequestResult>`
        """
        resp = self.__do_object('PUT', object_name, params={'acl': ''}, headers={'x-oss-object-acl': permission})
        return RequestResult(resp)

    def get_object_acl(self, object_name):
        """获取对象的ACL。

        :return: :class:`GetObjectAclResult <oss.models.GetObjectAclResult>`
        """
        resp = self.__do_object('GET', object_name, params={'acl': ''})
        return self._parse_result(resp, xml_utils.parse_get_object_acl, GetObjectAclResult)

    def batch_delete_objects(self, objects):
        """批量删除对象。

        :param objects: 对象名列表

        :return: :class:`BatchDeleteObjectsResult <oss.models.BatchDeleteObjectsResult>`
        """
        data = xml_utils.to_batch_delete_objects_request(objects, False, 'url')
        resp = self.__do_object('POST', '',
                                data=data,
                                params={'delete': ''},
                                headers={'Content-MD5': utils.content_md5(data)})
        return self._parse_result(resp, xml_utils.parse_batch_delete_objects, BatchDeleteObjectsResult)

    def init_multipart_upload(self, object_name, headers=None):
        """初始化分片上传。

        返回值中的 `upload_id` 以及bucket名和object_name三元组唯一对应了此次分片上传的会话。

        :param object_name: 待上传的对象名
        :param headers: HTTP头部

        :return: :class:`InitMultipartUploadResult <oss.models.InitMultipartUploadResult>`
        """
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), object_name)

        resp = self.__do_object('POST', object_name, params={'uploads': ''}, headers=headers)
        return self._parse_result(resp, xml_utils.parse_init_multipart_upload, InitMultipartUploadResult)

    def upload_part(self, object_name, upload_id, part_number, data):
        """上传一个分片。

        :param object_name: 待上传对象名，这个对象名要和 :func:`init_multipart_upload` 的对象名一致。
        :param upload_id: 分片上传ID
        :param part_number: 分片号，最小值是1.
        :param data: 待上传数据

        :return: :class:`PutObjectResult <oss.models.PutObjectResult>`
        """
        resp = self.__do_object('PUT', object_name,
                                params={'uploadId': upload_id, 'partNumber': str(part_number)},
                                data=data)
        return PutObjectResult(resp)

    def complete_multipart_upload(self, object_name, upload_id, parts, headers=None):
        """完成分片上传，创建对象。

        :param object_name: 待上传的对象名，这个对象名要和 :func:`init_multipart_upload` 的对象名一致。
        :param upload_id: 分片上传ID
        :param parts: `PartInfo` 列表，按照分片号升序的方式排列。 `PartInfo` 中的 `etag` 可以从 `upload_part` 的返回值中得到。
        :param headers: HTTP头部

        :return: :class:`PutObjectResult <oss.models.PutObjectResult>`
        """
        data = xml_utils.to_complete_upload_request(parts)
        resp = self.__do_object('POST', object_name,
                                params={'uploadId': upload_id},
                                data=data,
                                headers=headers)
        return PutObjectResult(resp)

    def abort_multipart_upload(self, object_name, upload_id):
        """取消分片上传。

        :param object_name: 待上传的对象名，这个对象名要和 :func:`init_multipart_upload` 的对象名一致。
        :param upload_id: 分片上传ID

        :return: :class:`RequestResult <oss.models.RequestResult>`
        """
        resp = self.__do_object('DELETE', object_name,
                                params={'uploadId': upload_id})
        return RequestResult(resp)

    def list_multipart_uploads(self,
                               prefix='',
                               delimiter='',
                               key_marker='',
                               upload_id_marker='',
                               max_uploads=1000):
        """罗列正在进行中的分片上传。支持分页。

        :param prefix: 只罗列对象名为该前缀的对象的分片上传
        :param delimiter: 目录分割符
        :param key_marker: 对象名分页符。第一次调用可以不传，后续设为返回值中的 `next_key_marker`
        :param upload_id_marker: 分片ID分页符。第一次调用可以不传，后续设为返回值中的 `next_upload_id_marker`
        :param max_uploads: 一次罗列最多能够返回的条目数

        :return: :class:`ListMultipartUploadsResult <oss.models.ListMultipartUploadsResult>`
        """
        resp = self.__do_object('GET', '',
                                params={'uploads': '',
                                        'prefix': prefix,
                                        'delimiter': delimiter,
                                        'key-marker': key_marker,
                                        'upload-id-marker': upload_id_marker,
                                        'max-uploads': max_uploads,
                                        'encoding-type': 'url'})
        return self._parse_result(resp, xml_utils.parse_list_multipart_uploads, ListMultipartUploadsResult)

    def upload_part_copy(self, source_bucket_name, source_object_name, source_range,
                         target_object_name, target_upload_id, target_part_number,
                         headers=None):
        """分片拷贝。把一个已有对象的一部分或整体拷贝成目标对象的一个分片。

        :param source_range: 指定待拷贝的范围。参见 :ref:`range`

        :return: :class:`PutObjectResult <oss.models.PutObjectResult>`
        """
        headers = http.CaseInsensitiveDict(headers)
        headers['x-oss-copy-source'] = '/' + source_bucket_name + '/' + source_object_name

        range_string = _make_range_string(source_range)
        if range_string:
            headers['x-oss-copy-source-range'] = 'bytes=' + range_string

        resp = self.__do_object('PUT', target_object_name,
                                params={'uploadId': target_upload_id,
                                        'partNumber': str(target_part_number)})
        return PutObjectResult(resp)

    def list_parts(self, object_name, upload_id,
                   marker='', max_parts=1000):
        """列举分片上传会话中已经上传的分片。支持分页。

        :return: :class:`ListPartsResult <oss.models.ListPartsResult>`
        """
        resp = self.__do_object('GET', object_name,
                                params={'uploadId': upload_id,
                                        'part-number-marker': marker,
                                        'max-parts': str(max_parts)})
        return self._parse_result(resp, xml_utils.parse_list_parts, ListPartsResult)

    def create_bucket(self, permission):
        """创建新的Bucket。

        :param permission: 指定Bucket的ACL，可以是'private'（推荐）、'public-read'或是'public-read-write'
        """
        resp = self.__do_bucket('PUT', headers={'x-oss-acl': permission})
        return RequestResult(resp)

    def delete_bucket(self):
        """删除一个Bucket。只有没有任何对象，也没有任何未完成的分片上传的Bucket才能被删除。

        :return: :class:`RequestResult <oss.models.RequestResult>`

        ":raises: 如果试图删除一个非空Bucket，则抛出 :class:`BucketNotEmpty <oss.exceptions.BucketNotEmpty>`
        """
        resp = self.__do_bucket('DELETE')
        return RequestResult(resp)

    def bucket_exists(self):
        """如果Bucket存在则返回True，反之返回False。
        """
        try:
            self.get_bucket_acl()
        except exceptions.NoSuchBucket:
            return False
        else:
            return True

    def put_bucket_acl(self, permission):
        """设置Bucket的ACL。

        :param permission: 新的ACL，可以是'private'、'public-read'或`public-read-write`
        """
        resp = self.__do_bucket('PUT', headers={'x-oss-acl': permission}, params={'acl': ''})
        return RequestResult(resp)

    def get_bucket_acl(self):
        """获取Bucket的ACL。

        :return: :class:`GetBucketAclResult <oss.models.GetBucketAclResult>`
        """
        resp = self.__do_bucket('GET', params={'acl': ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_acl, GetBucketAclResult)

    def put_bucket_cors(self, input):
        """设置Bucket的CORS。

        :param input: :class:`BucketCors <oss.models.BucketCors>` 对象或其他
        """
        data = self.__convert_data(BucketCors, xml_utils.to_put_bucket_cors, input)
        resp = self.__do_bucket('PUT', data=data, params={'cors': ''})
        return RequestResult(resp)

    def get_bucket_cors(self):
        """获取Bucket的CORS配置。

        :return: :class:`GetBucketCorsResult <oss.models.GetBucketCorsResult>`
        """
        resp = self.__do_bucket('GET', params={'cors': ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_cors, GetBucketCorsResult)

    def delete_bucket_cors(self):
        """删除Bucket的CORS配置。"""
        resp = self.__do_bucket('DELETE', params={'cors': ''})
        return RequestResult(resp)

    def put_bucket_lifecycle(self, input):
        """设置对象生命周期管理的配置。

        :param input: :class:`BucketLifecycle <oss.models.BucketLifecycle>` 对象或其他
        """
        data = self.__convert_data(BucketLifecycle, xml_utils.to_put_bucket_lifecycle, input)
        resp = self.__do_bucket('PUT', data=data, params={'lifecycle': ''})
        return RequestResult(resp)

    def get_bucket_lifecycle(self):
        """获取对象生命周期管理配置。

        :return: :class:`GetBucketLifecycleResult <oss.models.GetBucketLifecycleResult>`
        """
        resp = self.__do_bucket('GET', params={'lifecycle': ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_lifecycle, GetBucketLifecycleResult)

    def delete_bucket_lifecycle(self):
        """删除对象生命周期管理配置"""
        resp = self.__do_bucket('DELETE', params={'lifecycle': ''})
        return RequestResult(resp)

    def get_bucket_location(self):
        """获取Bucket的数据中心。

        :return: :class:`GetBucketLocationResult <oss.models.GetBucketLocationResult>`
        """
        resp = self.__do_bucket('GET', params={'location': ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_location, GetBucketLocationResult)

    def put_bucket_logging(self, input):
        """设置Bucket的日志收集功能。

        :param input: :class:`BucketLogging <oss.models.BucketLogging>` 对象或其他
        """
        data = self.__convert_data(BucketLogging, xml_utils.to_put_bucket_logging, input)
        resp = self.__do_bucket('PUT', data=data, params={'logging': ''})
        return RequestResult(resp)

    def get_bucket_logging(self):
        """获取Bucket的日志功能配置。

        :return: :class:`GetBucketLoggingResult <oss.models.GetBucketLoggingResult>`
        """
        resp = self.__do_bucket('GET', params={'logging': ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_logging, GetBucketLoggingResult)

    def delete_bucket_logging(self):
        """关闭Bucket的日志功能。"""
        resp = self.__do_bucket('DELETE', params={'logging': ''})
        return RequestResult(resp)

    def put_bucket_referer(self, input):
        """为Bucket设置防盗链。

        :param input: :class:`BucketReferer <oss.models.BucketReferer>` 对象或其他
        """
        data = self.__convert_data(BucketReferer, xml_utils.to_put_bucket_referer, input)
        resp = self.__do_bucket('PUT', data=data, params={'referer': ''})
        return RequestResult(resp)

    def get_bucket_referer(self):
        """获取Bucket的防盗链配置。

        :return: :class:`GetBucketRefererResult <oss.models.GetBucketRefererResult>`
        """
        resp = self.__do_bucket('GET', params={'referer': ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_referer, GetBucketRefererResult)

    def put_bucket_website(self, input):
        """为Bucket配置静态网站托管功能。

        :param input: :class:`BucketWebsite <oss.models.BucketWebsite>`
        """
        data = self.__convert_data(BucketWebsite, xml_utils.to_put_bucket_website, input)
        resp = self.__do_bucket('PUT', data=data, params={'website': ''})
        return RequestResult(resp)

    def get_bucket_website(self):
        """获取Bucket的静态网站托管配置。

        :return: :class:`GetBucketWebsiteResult <oss.models.GetBucketWebsiteResult>`
        """
        resp = self.__do_bucket('GET', params={'website': ''})
        return self._parse_result(resp, xml_utils.parse_get_bucket_websiste, GetBucketWebsiteResult)

    def delete_bucket_website(self):
        """关闭Bucket的静态网站托管功能。"""
        resp = self.__do_bucket('DELETE', params={'website': ''})
        return RequestResult(resp)

    def __do_object(self, method, object_name, **kwargs):
        return self._do(method, self.bucket_name, object_name, **kwargs)

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


def _determine_endpoint_type(netloc, is_cname):
    if utils.is_ip_or_localhost(netloc):
        return _ENDPOINT_TYPE_IP

    if is_cname:
        return _ENDPOINT_TYPE_CNAME
    else:
        return _ENDPOINT_TYPE_ALIYUN


class _UrlMaker(object):
    def __init__(self, endpoint, is_cname):
        p = urlparse(endpoint)

        self.scheme = p.scheme
        self.netloc = p.netloc
        self.type = _determine_endpoint_type(p.netloc, is_cname)

    def __call__(self, bucket_name, object_name):
        object_name = urlquote(object_name)

        if self.type == _ENDPOINT_TYPE_CNAME:
            return '{0}://{1}/{2}'.format(self.scheme, self.netloc, object_name)

        if self.type == _ENDPOINT_TYPE_IP:
            if bucket_name:
                return '{0}://{1}/{2}/{3}'.format(self.scheme, self.netloc, bucket_name, object_name)
            else:
                return '{0}://{1}/{2}'.format(self.scheme, self.netloc, object_name)

        if not bucket_name:
            assert not object_name
            return '{0}://{1}'.format(self.scheme, self.netloc)

        return '{0}://{1}.{2}/{3}'.format(self.scheme, bucket_name, self.netloc, object_name)
