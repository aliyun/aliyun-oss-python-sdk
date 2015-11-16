# -*- coding: utf-8 -*-

"""
oss.resumable
~~~~~~~~~~~~~

该模块包含了断点续传相关的函数和类。
"""

import os

from . import utils
from . import iterators
from . import exceptions

from .models import PartInfo
from .compat import json

import logging

_STORE_VERSION = '1'

_MULTIPART_THRESHOLD = 500 * 1024 * 1024
_PREFERRED_PART_SIZE = 100 * 1024 * 1024

_MAX_PART_COUNT = 10000
_MIN_PART_SIZE = 100 * 1024


def upload_file(filename, bucket, object_name,
                store=None,
                multipart_threshold=_MULTIPART_THRESHOLD,
                part_size=_PREFERRED_PART_SIZE):
    size = os.path.getsize(filename)

    if size >= multipart_threshold:
        uploader = ResumableUploader(filename, size, bucket, object_name, store, part_size=part_size)
        uploader.upload()
    else:
        with open(filename, 'rb') as f:
            bucket.put_object(object_name, f)


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

    :param bucket: :class:`Bucket <oss.api.Bucket>` 对象
    :param object_name: 对象名
    :param filename: 待上传的文件名
    :param size: 文件总长度
    :param store: 用来保存进度的持久化存储
    :param part_size: 分片大小。优先使用用户提供的值。如果用户没有指定，那么对于新上传，计算出一个合理值；对于老的上传，采用第一个
        分片的大小。
    """
    def __init__(self, filename, size, bucket, object_name,
                 store=None, part_size=_PREFERRED_PART_SIZE):
        self.bucket = bucket
        self.object_name = object_name
        self.filename = filename
        self.size = size

        self.store = store or FileStore()
        self.part_size = part_size

        self.abspath = os.path.abspath(filename)
        self.mtime = os.path.getmtime(filename)

        self.key = self.store.make_key(bucket.bucket_name, object_name, self.abspath)

    def upload(self):
        record = self.__load_record()

        parts_uploaded = [PartInfo(int(p['part_number']), p['etag']) for p in record['parts']]
        verify_parts = self.__file_changed(record)
        upload_id = record['upload_id']

        with open(self.filename, 'rb') as f:
            parts_to_upload, kept_parts = self.__get_parts_to_upload(f, parts_uploaded, verify_parts)
            parts_to_upload = sorted(parts_to_upload, key=lambda p: p.part_number)

            for part in parts_to_upload:
                f.seek(part.start, os.SEEK_SET)
                result = self.bucket.upload_part(self.object_name, upload_id, part.part_number,
                                                 _SizedStreamReader(f, part.size))
                kept_parts.append(PartInfo(part.part_number, result.etag))

                record['parts'].append({'part_number': part.part_number, 'etag': result.etag})
                self.store.put(self.key, record)

            self.bucket.complete_multipart_upload(self.object_name, upload_id, kept_parts)
            self.store.delete(self.key)

    def __load_record(self):
        record = self.store.get(self.key)

        if record and not is_record_sane(record):
            self.store.delete(self.key)
            record = None

        if record:
            if not self.__upload_exists(record['upload_id']):
                self.store.delete(self.key)
                record = None

        if record:
            self.part_size = record['part_size']
        else:
            self.part_size = self.part_size or determine_part_size(self.size)
            upload_id = self.bucket.init_multipart_upload(self.object_name).upload_id
            record = {'upload_id': upload_id, 'mtime': self.mtime, 'size': self.size, 'parts': [],
                      'abspath': self.abspath, 'object_name': self.object_name,
                      'part_size': self.part_size}

            self.store.put(self.key, record)

        return record

    def __list_parts(self, upload_id, part_marker):
        try:
            return list(iterators.PartIterator(self.bucket, self.object_name, upload_id, str(part_marker)))
        except exceptions.NoSuchUpload:
            return None

    def __upload_exists(self, upload_id):
        try:
            list(iterators.PartIterator(self.bucket, self.object_name, upload_id, '0', max_parts=1))
        except exceptions.NoSuchUpload:
            return False
        else:
            return True

    def __file_changed(self, record):
        return record['mtime'] != self.mtime or record['size'] != self.size

    def __get_parts_to_upload(self, f, parts_uploaded, verify_parts):
        num_parts = utils.how_many(self.size, self.part_size)
        uploaded_map = {}
        to_upload_map = {}

        for uploaded in parts_uploaded:
            uploaded_map[uploaded.part_number] = uploaded

        for i in range(num_parts):
            if i == num_parts - 1:
                start = i * self.part_size
                end = self.size
            else:
                start = i * self.part_size
                end = self.part_size + start

            to_upload_map[i + 1] = _PartToUpload(i + 1, start, end)

        if not parts_uploaded:
            return to_upload_map.values(), []

        kept_parts = []
        if verify_parts:
            for uploaded in parts_uploaded:
                if uploaded.part_number in to_upload_map:
                    if uploaded.etag == self.__compute_etag(f, to_upload_map[uploaded.part_number]):
                        del to_upload_map[uploaded.part_number]
                        kept_parts.append(uploaded)

        return to_upload_map.values(), kept_parts

    def __compute_etag(self, f, part_to_upload):
        f.seek(part_to_upload.start, os.SEEK_SET)
        return utils.etag(_SizedStreamReader(f, part_to_upload.size))


class FileStore(object):
    def __init__(self, dir=None):
        self.dir = dir or os.path.expanduser('~')

    @staticmethod
    def make_key(bucket_name, object_name, filename):
        oss_pathname = 'oss://{0}/{1}'.format(bucket_name, object_name)
        return utils.md5_string(oss_pathname) + '-' + utils.md5_string(filename)

    def get(self, key):
        pathname = self.__path(key)

        logging.debug('get key={0}, pathname={1}'.format(key, pathname))

        if not os.path.exists(pathname):
            return None

        with open(pathname, 'r') as f:
            return json.load(f)

    def put(self, key, value):
        pathname = self.__path(key)

        with open(pathname, 'w') as f:
            json.dump(value, f)

        logging.debug('put key={0}, pathname={1}'.format(key, pathname))

    def delete(self, key):
        pathname = self.__path(key)
        os.remove(pathname)

        logging.debug('del key={0}, pathname={1}'.format(key, pathname))

    def __path(self, key):
        return os.path.join(self.dir, key)


def rebuild_record(store, bucket, object_name, filename, upload_id, part_size=None):
    abspath = os.path.abspath(filename)
    mtime = os.path.getmtime(filename)
    size = os.path.getsize(filename)

    key = store.make_key(bucket.bucket_name, object_name, abspath)
    record = {'upload_id': upload_id, 'mtime': mtime, 'size': size, 'parts': [],
              'abspath': abspath, 'object_name': object_name}

    for p in iterators.PartIterator(bucket, object_name, upload_id):
        record['parts'].append({'part_number': p.part_number,
                                'etag': p.etag})

        if not part_size:
            part_size = p.size

    record['part_size'] = part_size

    store.put(key, record)


def is_record_sane(record):
    try:
        for key in ('upload_id', 'abspath', 'object_name'):
            if not isinstance(record[key], str):
                logging.info('{0} is not a string: {1}'.format(key, record[key]))
                return False

        for key in ('size', 'part_size'):
            if not isinstance(record[key], int):
                logging.error('{0} is not an integer: {1}'.format(key, record[key]))
                return False

        if not isinstance(record['mtime'], int) and not isinstance(record['mtime'], float):
            logging.info('mtime is not a float or an integer: {0}'.format(record['mtime']))
            return False

        if not isinstance(record['parts'], list):
            logging.info('parts is not a list: {0}'.format(record['parts'].__class__.__name__))
            return False
    except KeyError as e:
        logging.error('Key not found: {0}'.format(e.args))
        return False

    return True


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


class _PartToUpload(object):
    def __init__(self, part_number, start, end):
        self.part_number = part_number
        self.start = start
        self.end = end

    @property
    def size(self):
        return self.end - self.start
