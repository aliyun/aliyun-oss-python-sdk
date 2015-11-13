# -*- coding: utf-8 -*-

"""
oss.easy
~~~~~~~~

该模块包含了一些易用性接口。一般用户应优先使用这些接口。
"""

from .models import PartInfo
from .exceptions import NoSuchUpload
from .iterators import PartIterator, ObjectUploadIterator

from . import utils
import os

_MULTIPART_THRESHOLD = 500 * 1024 * 1024

_MAX_PART_COUNT = 10000
_MIN_PART_SIZE = 100 * 1024

_PREFERRED_PART_SIZE = 100 * 1024 * 1024
_PREFERRED_PART_COUNT = 100


def upload_file(filename, bucket, object_name,
                upload_id='',
                part_size=_PREFERRED_PART_SIZE,
                multipart_threshold=_MULTIPART_THRESHOLD):
    size = os.path.getsize(filename)

    with open(filename, 'rb') as f:
        if upload_id:
            uploader = ResumableUploader(f, size, bucket, object_name, upload_id, part_size=part_size)
            uploader.upload()
        elif size >= multipart_threshold:
            upload_id = _get_latest_upload_id(bucket, object_name)
            uploader = ResumableUploader(f, size, bucket, object_name, upload_id, part_size=part_size)
            uploader.upload()
        else:
            bucket.put_object(object_name, f)


def _get_latest_upload_id(bucket, object_name):
    latest = None

    for u in ObjectUploadIterator(bucket, object_name):
        if latest is None or u.creation_time > latest.creation_time:
            latest = u

    if latest:
        return latest.upload_id
    else:
        return ''


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


def determine_part_size(total_size,
                        preferred_size=_PREFERRED_PART_SIZE):
    if total_size < preferred_size:
        return total_size

    if preferred_size * _MAX_PART_COUNT < total_size:
        return total_size // _MAX_PART_COUNT + 1
    else:
        return preferred_size


class _PartToUpload(object):
    def __init__(self, part_number, start, end):
        self.part_number = part_number
        self.start = start
        self.end = end
        self.etag = ''

    def size(self):
        return self.end - self.start


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

    def __get_parts_to_upload(self, uploaded_parts):
        num_parts = how_many(self.size, self.part_size)
        uploaded_map = {}
        to_upload_map = {}

        for uploaded in uploaded_parts:
            uploaded_map[uploaded.part_number] = uploaded

        for i in range(num_parts):
            if i == num_parts - 1:
                start = i * self.part_size
                end = self.size
            else:
                start = i * self.part_size
                end = self.part_size + start

            to_upload_map[i + 1] = _PartToUpload(i + 1, start, end)

        if not uploaded_parts:
            return True, to_upload_map.values()

        for uploaded in uploaded_parts:
            part_number = uploaded.part_number
            if part_number in to_upload_map:
                if uploaded.size != to_upload_map[part_number].size:
                    return False, to_upload_map.values()

        for uploaded in uploaded_parts:
            if uploaded.part_number in to_upload_map:
                if uploaded.etag == self.__compute_etag(to_upload_map[uploaded.part_number]):
                    del to_upload_map[uploaded.part_number]

        return True, to_upload_map.values()

    def __compute_etag(self, part_to_upload):
        self.stream.seek(part_to_upload.start, os.SEEK_SET)
        return utils.etag(_SizedStreamReader(self.stream, part_to_upload.size()))

    def __upload_and_complete(self, uploaded_parts):
        assert self.part_size
        assert self.upload_id

        safe, parts_to_upload = self.__get_parts_to_upload(uploaded_parts)

        if not safe:
            self.upload_id = self.bucket.init_multipart_upload(self.object_name).upload_id
            uploaded_parts = []

        parts_to_upload = sorted(parts_to_upload, key=lambda p: p.part_number)

        for part in parts_to_upload:
            self.stream.seek(part.start, os.SEEK_SET)
            result = self.bucket.upload_part(self.object_name, self.upload_id, part.part_number,
                                             _SizedStreamReader(self.stream, part.size()))
            uploaded_parts.append(PartInfo(part.part_number, result.etag))

        self.bucket.complete_multipart_upload(self.object_name, self.upload_id, uploaded_parts)
