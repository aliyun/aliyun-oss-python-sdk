# -*- coding: utf-8 -*-

"""
oss.easy
~~~~~~~~

该模块包含了一些易用性接口。一般用户应优先使用这些接口。
"""

from . models import PartInfo, MultipartUploadInfo, SimplifiedObjectInfo
from .exceptions import NoSuchUpload


class _BaseIterator(object):
    def __init__(self, marker):
        self.is_truncated = True
        self.next_marker = marker

        self.entries = []

    def _fetch(self):
        raise NotImplemented

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self.entries:
                return self.entries.pop(0)

            if not self.is_truncated:
                raise StopIteration

            self.is_truncated, self.next_marker = self._fetch()

    def next(self):
        return self.__next__()


class BucketIterator(_BaseIterator):
    """遍历用户Bucket的迭代器。每次迭代返回的是 :class:`SimplifiedBucketInfo <oss.models.SimplifiedBucketInfo>` 对象。

    :param service: :class:`Service <oss.api.Service>` 对象
    :param prefix: 只列举匹配该前缀的Bucket
    :param marker: 分页符。只列举Bucket名字典序在此之后的Bucket
    :param max_keys: 每次调用 `list_buckets` 时的max_keys参数。注意迭代器返回的数目可能会大于该值。
    """
    def __init__(self, service, prefix='', marker='', max_keys=100):
        super(BucketIterator, self).__init__(marker)
        self.service = service
        self.prefix = prefix
        self.max_keys = max_keys

    def _fetch(self):
        result = self.service.list_buckets(prefix=self.prefix,
                                           marker=self.next_marker,
                                           max_keys=self.max_keys)
        self.entries = result.buckets

        return result.is_truncated, result.next_marker


class ObjectIterator(_BaseIterator):
    """遍历Bucket里对象的迭代器。每次迭代返回的是 :class:`SimplifiedObjectInfo <oss.models.SimplifiedObjectInfo>` 对象。

    :param bucket: :class:`Bucket <oss.api.Bucket>` 对象
    :param prefix: 只列举匹配该前缀的对象
    :param delimiter: 目录分隔符
    :param marker: 分页符
    :param max_keys: 每次调用 `list_objects` 时的max_keys参数。注意迭代器返回的数目可能会大于该值。
    """
    def __init__(self, bucket, prefix='', delimiter='', marker='', max_keys=100):
        super(ObjectIterator, self).__init__(marker)

        self.bucket = bucket
        self.prefix = prefix
        self.delimiter = delimiter
        self.max_keys = max_keys

    def _fetch(self):
        result = self.bucket.list_objects(prefix=self.prefix,
                                          delimiter=self.delimiter,
                                          marker=self.next_marker,
                                          max_keys=self.max_keys)
        self.entries = result.object_list + [SimplifiedObjectInfo(prefix, None, None, None, None)
                                             for prefix in result.prefix_list]
        self.entries.sort(key=lambda obj: obj.name)

        return result.is_truncated, result.next_marker


class MultipartUploadIterator(_BaseIterator):
    """遍历Bucket里未完成的分片上传。

    :param bucket: :class:`Bucket <oss.api.Bucket>` 对象
    :param prefix: 仅列举匹配该前缀的对象的分片上传
    :param delimiter: 目录分隔符
    :param key_marker: 对象名分页符
    :param upload_id_marker: 分片上传ID分页符
    :param max_uploads: 每次调用 `list_multipart_uploads` 时的max_uploads参数。注意迭代器返回的数目可能会大于该值。
    """
    def __init__(self, bucket, prefix='', delimiter='', key_marker='', upload_id_marker='', max_uploads=1000):
        super(MultipartUploadIterator,self).__init__(key_marker)

        self.bucket = bucket
        self.prefix = prefix
        self.delimiter = delimiter
        self.next_upload_id_marker = upload_id_marker
        self.max_uploads = max_uploads

    def _fetch(self):
        result = self.bucket.list_multipart_uploads(prefix=self.prefix,
                                                    delimiter=self.delimiter,
                                                    key_marker=self.next_marker,
                                                    upload_id_marker=self.next_upload_id_marker,
                                                    max_uploads=self.max_uploads)
        self.entries = result.upload_list + [MultipartUploadInfo(prefix, None, None) for prefix in result.prefix_list]
        self.entries.sort(key=lambda u: u.object_name)

        self.next_upload_id_marker = result.next_upload_id_marker
        return result.is_truncated, result.next_key_marker


class PartIterator(_BaseIterator):
    """遍历一个分片上传会话中已经上传的分片。

    :param bucket: :class:`Bucket <oss.api.Bucket>` 对象
    :param object_name: 对象名
    :param upload_id: 分片上传ID
    :param marker: 分页符
    :param max_parts: 每次调用 `list_parts` 时的max_parts参数。注意迭代器返回的数目可能会大于该值。
    """
    def __init__(self, bucket, object_name, upload_id, marker='0', max_parts=1000):
        super(PartIterator, self).__init__(marker)

        self.bucket = bucket
        self.object_name = object_name
        self.upload_id = upload_id
        self.max_parts = max_parts

    def _fetch(self):
        result = self.bucket.list_parts(self.object_name, self.upload_id,
                                        marker=self.next_marker,
                                        max_parts=self.max_parts)
        self.entries = result.parts

        return result.is_truncated, result.next_marker


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


_MAX_PART_COUNT = 10000
_MIN_PART_SIZE = 100 * 1024

_PREFERRED_PART_SIZE = 100 * 1024 * 1024
_PREFERRED_PART_COUNT = 100


def how_many(m, n):
    return (m + n - 1) // n


def determine_part_size(total_size,
                        preferred_size=_PREFERRED_PART_SIZE):
    if total_size < preferred_size:
        return total_size

    if preferred_size * _MAX_PART_COUNT < total_size:
        return total_size // _MAX_PART_COUNT + 1
    else:
        return preferred_size


class ResumableUploader(object):
    """以断点续传方式上传文件。

    :param stream: file-like object
    :param size: 文件总长度
    :param bucket: :class:`Bucket <oss.api.Bucket>` 对象
    :param object_name: 对象名
    :param upload_id: 分片上传ID
    :param part_size: 分片大小。优先使用用户提供的值。如果用户没有指定，那么对于新上传，计算出一个合理值；对于老的上传，采用第一个
        分片的大小。
    """
    def __init__(self, stream, size, bucket, object_name, upload_id,
                 part_size=None):
        self.stream = stream
        self.size = size
        self.bucket = bucket
        self.object_name = object_name
        self.upload_id = upload_id

        self.part_size = part_size

    def upload(self):
        uploaded_parts = []

        if self.upload_id:
            try:
                uploaded_parts = list(PartIterator(self.bucket, self.object_name, self.upload_id))
            except NoSuchUpload:
                self.upload_id = ''

        if not self.part_size:
            if uploaded_parts:
                self.part_size = max(p.size for p in uploaded_parts)
            else:
                self.part_size = determine_part_size(self.size)

        if self.upload_id:
            self.__resume_upload(uploaded_parts)
        else:
            self.__new_upload()

    def __new_upload(self):
        assert not self.upload_id

        self.upload_id = self.bucket.init_multipart_upload(self.object_name).upload_id
        self.__upload_and_complete([])

    def __resume_upload(self, uploaded_parts):
        self.__upload_and_complete(uploaded_parts)

    def __upload_and_complete(self, uploaded_parts):
        assert self.part_size
        assert self.upload_id

        if uploaded_parts:
            uploaded_size = sum(p.size for p in uploaded_parts)
            remaining = self.size - uploaded_size

            start_part = uploaded_parts[-1].part_number+1
            num_parts = len(uploaded_parts) + how_many(self.size - uploaded_size, self.part_size)

            self.stream.seek(uploaded_size)
        else:
            remaining = self.size
            num_parts = how_many(self.size, self.part_size)
            start_part = 1

        for i in range(start_part, num_parts+1):
            if i == num_parts:
                bytes_to_upload = remaining % self.part_size
            else:
                bytes_to_upload = self.part_size

            result = self.bucket.upload_part(self.object_name, self.upload_id, i,
                                             _SizedStreamReader(self.stream, bytes_to_upload))
            uploaded_parts.append(PartInfo(i, result.etag))

        self.bucket.complete_multipart_upload(self.object_name, self.upload_id, uploaded_parts)