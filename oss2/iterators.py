# -*- coding: utf-8 -*-

"""
oss2.iterators
~~~~~~~~~~~~~~

This module contains some easy to use iterators for enumerating bucket, file, parts, etc.
"""

from .models import MultipartUploadInfo, SimplifiedObjectInfo
from .exceptions import ServerError

from . import defaults


class _BaseIterator(object):
    def __init__(self, marker, max_retries):
        self.is_truncated = True
        self.next_marker = marker

        max_retries = defaults.get(max_retries, defaults.request_retries)
        self.max_retries = max_retries if max_retries > 0 else 1

        self.entries = []

    def _fetch(self):
        raise NotImplemented    # pragma: no cover

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self.entries:
                return self.entries.pop(0)

            if not self.is_truncated:
                raise StopIteration

            self.fetch_with_retry()

    def next(self):
        return self.__next__()

    def fetch_with_retry(self):
        for i in range(self.max_retries):
            try:
                self.is_truncated, self.next_marker = self._fetch()
            except ServerError as e:
                if e.status // 100 != 5:
                    raise

                if i == self.max_retries - 1:
                    raise
            else:
                return


class BucketIterator(_BaseIterator):
    """Iterator for bucket

    It returns a :class:`SimplifiedBucketInfo <oss2.models.SimplifiedBucketInfo>` instance in each iteration (via next()).

    :param service: :class:`Service <oss2.Service>` instance
    :param prefix: Bucket name prefix---only buckets with the prefix are listed.
    :param marker: Paging marker. Only lists bucket whose name is after the marker in the lexicographic order.
    :param max_keys: The max keys to return for list_buckets. Note that it does **not** mean the max keys for the iterator to return is no more than it. The iterator could return more items than max_keys.
    """
    def __init__(self, service, prefix='', marker='', max_keys=100, max_retries=None):
        super(BucketIterator, self).__init__(marker, max_retries)
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
    """Iterator for files in bucket.

    It returns a :class:`SimplifiedObjectInfo <oss2.models.SimplifiedObjectInfo>` instance for each iteration (via next()).
    When `SimplifiedObjectInfo.is_prefix()` is True, it means the objet is common prefix (directory, not a file); Otherwise it's a file.

    :param bucket: :class:`Bucket <oss2.Bucket>` instance
    :param prefix: The file name prefix
    :param delimiter: delimiter for the directory
    :param marker: Paging marker
    :param max_keys: The max keys to return for each `list_objects` call. However the total entries iterator returns could be more than that.
    """
    def __init__(self, bucket, prefix='', delimiter='', marker='', max_keys=100, max_retries=None):
        super(ObjectIterator, self).__init__(marker, max_retries)

        self.bucket = bucket
        self.prefix = prefix
        self.delimiter = delimiter
        self.max_keys = max_keys

    def _fetch(self):
        result = self.bucket.list_objects(prefix=self.prefix,
                                          delimiter=self.delimiter,
                                          marker=self.next_marker,
                                          max_keys=self.max_keys)
        self.entries = result.object_list + [SimplifiedObjectInfo(prefix, None, None, None, None, None)
                                             for prefix in result.prefix_list]
        self.entries.sort(key=lambda obj: obj.key)

        return result.is_truncated, result.next_marker


class MultipartUploadIterator(_BaseIterator):
    """Iterator of ongoing parts in multiparts upload.

    It returns a :class:`MultipartUploadInfo <oss2.models.MultipartUploadInfo>` instance for each iteration.
    When `MultipartUploadInfo.is_prefix()` returns true, it means it's a folder. Otherwise it's a file.

    :param bucket: :class:`Bucket <oss2.Bucket>` instance
    :param prefix: file key prefix---only parts of those files will be listed.
    :param delimiter: directory delimeter.
    :param key_marker: Paging marker.
    :param upload_id_marker: Paging upload Id marker.
    :param max_uploads: Max entries for each  `list_multipart_uploads` call. Note that the total count the iterator returns could be more than that.
    """
    def __init__(self, bucket,
                 prefix='', delimiter='', key_marker='', upload_id_marker='',
                 max_uploads=1000, max_retries=None):
        super(MultipartUploadIterator, self).__init__(key_marker, max_retries)

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
        self.entries.sort(key=lambda u: u.key)

        self.next_upload_id_marker = result.next_upload_id_marker
        return result.is_truncated, result.next_key_marker


class ObjectUploadIterator(_BaseIterator):
    """Iterator of ongoing multiparts upload.

    It returns a :class:`MultipartUploadInfo <oss2.models.MultipartUploadInfo>` instance for each iteration.
    When `MultipartUploadInfo.is_prefix()` is true, it means the common prefix (folder).

    :param bucket: :class:`Bucket <oss2.Bucket>` instance
    :param key: object key.
    :param max_uploads: Max entries for each `list_multipart_uploads` call. Note the total count the iterator returns could be more than that.
    """
    def __init__(self, bucket, key, max_uploads=1000, max_retries=None):
        super(ObjectUploadIterator, self).__init__('', max_retries)
        self.bucket = bucket
        self.key = key
        self.next_upload_id_marker = ''
        self.max_uploads = max_uploads

    def _fetch(self):
        result = self.bucket.list_multipart_uploads(prefix=self.key,
                                                    key_marker=self.next_marker,
                                                    upload_id_marker=self.next_upload_id_marker,
                                                    max_uploads=self.max_uploads)

        self.entries = [u for u in result.upload_list if u.key == self.key]
        self.next_upload_id_marker = result.next_upload_id_marker

        if not result.is_truncated or not self.entries:
            return False, result.next_key_marker

        if result.next_key_marker > self.key:
            return False, result.next_key_marker

        return result.is_truncated, result.next_key_marker


class PartIterator(_BaseIterator):
    """Iterator of uploaded parts of a specific multipart upload.

    It returns a :class:`PartInfo <oss2.models.PartInfo>` instance for each iteration.

    :param bucket: :class:`Bucket <oss2.Bucket>` instance.
    :param key: object key.
    :param upload_id: Upload Id.
    :param marker: Paging marker
    :param max_parts: The max parts for each `list_parts` call. Note that the total count the iterator returns could be more than that.
    """
    def __init__(self, bucket, key, upload_id,
                 marker='0', max_parts=1000, max_retries=None):
        super(PartIterator, self).__init__(marker, max_retries)

        self.bucket = bucket
        self.key = key
        self.upload_id = upload_id
        self.max_parts = max_parts

    def _fetch(self):
        result = self.bucket.list_parts(self.key, self.upload_id,
                                        marker=self.next_marker,
                                        max_parts=self.max_parts)
        self.entries = result.parts

        return result.is_truncated, result.next_marker


class LiveChannelIterator(_BaseIterator):
    """Iterator of Live Channel in a bucket.

    It returns a :class:`LiveChannelInfo <oss2.models.LiveChannelInfo>` instance for each iteration.

    :param bucket: :class:`Bucket <oss2.Bucket>` instance.
    :param prefix: Live Channel prefix
    :param marker: Paging marker.
    :param max_keys: Max entries for each `list_live_channel` call. Note that the total count the iterator returns could be more than that.
    """
    def __init__(self, bucket, prefix='', marker='', max_keys=100, max_retries=None):
        super(LiveChannelIterator, self).__init__(marker, max_retries)

        self.bucket = bucket
        self.prefix = prefix
        self.max_keys = max_keys

    def _fetch(self):
        result = self.bucket.list_live_channel(prefix=self.prefix,
                                               marker=self.next_marker,
                                               max_keys=self.max_keys)
        self.entries = result.channels

        return result.is_truncated, result.next_marker

