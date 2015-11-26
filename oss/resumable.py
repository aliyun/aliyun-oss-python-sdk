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
from . import defaults

from .models import PartInfo
from .compat import json, stringify

import logging


_MAX_PART_COUNT = 10000
_MIN_PART_SIZE = 100 * 1024


def upload_file(bucket, object_name, filename,
                store=None,
                headers=None,
                multipart_threshold=defaults.multipart_threshold,
                part_size=defaults.part_size):
    """断点上传本地文件。

    缺省条件下，该函数会在用户HOME目录下保存断点续传的信息。当待上传的本地文件没有发生变化，
    且目标对象名没有变化时，会根据本地保存的信息，从断点开始上传。

    :param filename: 待上传本地文件名
    :param bucket: :class:`Bucket <oss.api.Bucket>` 对象
    :param object_name: 上传到用户空间的对象名
    :param store: 用来保存断点信息的持久存储，参见 :class:`FileStore` 的接口。如不指定，则使用 `FileStore` 。
    :param headers: 传给 `put_object` 或 `init_multipart_upload` 的HTTP头部
    :param multipart_threshold: 文件长度大于该值时，则用分片上传。
    :param part_size: 指定分片上传的每个分片的大小。如不指定，则自动计算。
    """
    size = os.path.getsize(filename)

    if size >= multipart_threshold:
        uploader = ResumableUploader(bucket, object_name, filename, size, store,
                                     part_size=part_size,
                                     headers=headers)
        uploader.upload()
    else:
        with open(filename, 'rb') as f:
            bucket.put_object(object_name, f, headers=headers)


def determine_part_size(total_size,
                        preferred_size=defaults.part_size):
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
    :param headers: 传给 `init_multipart_upload` 的HTTP头部
    :param part_size: 分片大小。优先使用用户提供的值。如果用户没有指定，那么对于新上传，计算出一个合理值；对于老的上传，采用第一个
        分片的大小。
    """
    def __init__(self, bucket, object_name, filename, size,
                 store=None,
                 headers=None,
                 part_size=defaults.part_size):
        self.bucket = bucket
        self.object_name = object_name
        self.filename = filename
        self.size = size

        self.store = store or FileStore()
        self.headers = headers
        self.part_size = part_size

        self.abspath = os.path.abspath(filename)
        self.mtime = os.path.getmtime(filename)

        self.key = self.store.make_key(bucket.bucket_name, object_name, self.abspath)

    def upload(self):
        record = self.__load_record()

        parts_uploaded = [PartInfo(int(p['part_number']), p['etag']) for p in record['parts']]
        upload_id = record['upload_id']

        with open(self.filename, 'rb') as f:
            parts_to_upload, kept_parts = self.__get_parts_to_upload(f, parts_uploaded)
            parts_to_upload = sorted(parts_to_upload, key=lambda p: p.part_number)

            for part in parts_to_upload:
                f.seek(part.start, os.SEEK_SET)
                result = self.bucket.upload_part(self.object_name, upload_id, part.part_number,
                                                 utils.SizedStreamReader(f, part.size))
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

        if record and self.__file_changed(record):
            logging.debug('{0} was changed, clear the record.'.format(self.filename))
            self.store.delete(self.key)
            record = None

        if record and not self.__upload_exists(record['upload_id']):
            self.store.delete(self.key)
            record = None

        if record:
            self.part_size = record['part_size']
        else:
            self.part_size = self.part_size or determine_part_size(self.size)
            upload_id = self.bucket.init_multipart_upload(self.object_name, headers=self.headers).upload_id
            record = {'upload_id': upload_id, 'mtime': self.mtime, 'size': self.size, 'parts': [],
                      'abspath': self.abspath, 'object_name': self.object_name,
                      'part_size': self.part_size}

            self.store.put(self.key, record)

        return record

    def __upload_exists(self, upload_id):
        try:
            list(iterators.PartIterator(self.bucket, self.object_name, upload_id, '0', max_parts=1))
        except exceptions.NoSuchUpload:
            return False
        else:
            return True

    def __file_changed(self, record):
        return record['mtime'] != self.mtime or record['size'] != self.size

    def __get_parts_to_upload(self, f, parts_uploaded):
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

        for uploaded in parts_uploaded:
            if uploaded.part_number in to_upload_map:
                del to_upload_map[uploaded.part_number]
                kept_parts.append(uploaded)

        return to_upload_map.values(), kept_parts


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

        # json.load()返回的总是unicode，对于Python2，我们将其转换
        # 为str。
        with open(pathname, 'r') as f:
            return stringify(json.load(f))

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


def rebuild_record(filename, store, bucket, object_name, upload_id, part_size=None):
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
                logging.error('{0} is not a string: {1}, but {2}'.format(key, record[key], record[key].__class__))
                return False

        for key in ('size', 'part_size'):
            if not isinstance(record[key], int):
                logging.error('{0} is not an integer: {1}'.format(key, record[key]))
                return False

        if not isinstance(record['mtime'], int) and not isinstance(record['mtime'], float):
            logging.error('mtime is not a float or an integer: {0}'.format(record['mtime']))
            return False

        if not isinstance(record['parts'], list):
            logging.error('parts is not a list: {0}'.format(record['parts'].__class__.__name__))
            return False
    except KeyError as e:
        logging.error('Key not found: {0}'.format(e.args))
        return False

    return True


class _PartToUpload(object):
    def __init__(self, part_number, start, end):
        self.part_number = part_number
        self.start = start
        self.end = end

    @property
    def size(self):
        return self.end - self.start
