# -*- coding: utf-8 -*-

"""
oss2.resumable
~~~~~~~~~~~~~~

该模块包含了断点续传相关的函数和类。
"""

import os

from . import utils
from . import iterators
from . import exceptions
from . import defaults

from .models import PartInfo
from .compat import json, stringify, to_unicode
from .task_queue import TaskQueue


import logging
import functools
import threading


_MAX_PART_COUNT = 10000
_MIN_PART_SIZE = 100 * 1024


def resumable_upload(bucket, key, filename,
                     store=None,
                     headers=None,
                     multipart_threshold=None,
                     part_size=None,
                     progress_callback=None,
                     num_threads=None):
    """断点上传本地文件。

    缺省条件下，该函数会在用户HOME目录下保存断点续传的信息。当待上传的本地文件没有发生变化，
    且目标文件名没有变化时，会根据本地保存的信息，从断点开始上传。

    :param bucket: :class:`Bucket <oss2.Bucket>` 对象
    :param key: 上传到用户空间的文件名
    :param filename: 待上传本地文件名
    :param store: 用来保存断点信息的持久存储，参见 :class:`ResumableStore` 的接口。如不指定，则使用 `ResumableStore` 。
    :param headers: 传给 `put_object` 或 `init_multipart_upload` 的HTTP头部
    :param multipart_threshold: 文件长度大于该值时，则用分片上传。
    :param part_size: 指定分片上传的每个分片的大小。如不指定，则自动计算。
    :param progress_callback: 上传进度回调函数。参见 :ref:`progress_callback` 。
    :param num_threads: 并发上传的线程数，如不指定则使用 `oss2.defaults.multipart_threshold` 。
    """
    size = os.path.getsize(filename)
    multipart_threshold = defaults.get(multipart_threshold, defaults.multipart_threshold)

    if size >= multipart_threshold:
        uploader = _ResumableUploader(bucket, key, filename, size, store,
                                      part_size=part_size,
                                      headers=headers,
                                      progress_callback=progress_callback,
                                      num_threads=num_threads)
        uploader.upload()
    else:
        with open(to_unicode(filename), 'rb') as f:
            bucket.put_object(key, f,
                              headers=headers,
                              progress_callback=progress_callback)


def determine_part_size(total_size,
                        preferred_size=None):
    """确定分片大小。

    :param int total_size: 总共需要上传的长度
    :param int preferred_size: 用户期望的分片大小。如果不指定则采用defaults.part_size

    :return: 分片大小
    """
    if not preferred_size:
        preferred_size = defaults.part_size

    if total_size < preferred_size:
        return total_size

    if preferred_size * _MAX_PART_COUNT < total_size:
        if total_size % _MAX_PART_COUNT:
            return total_size // _MAX_PART_COUNT + 1
        else:
            return total_size // _MAX_PART_COUNT
    else:
        return preferred_size


class _ResumableUploader(object):
    """以断点续传方式上传文件。

    :param bucket: :class:`Bucket <oss2.Bucket>` 对象
    :param key: 文件名
    :param filename: 待上传的文件名
    :param size: 文件总长度
    :param store: 用来保存进度的持久化存储
    :param headers: 传给 `init_multipart_upload` 的HTTP头部
    :param part_size: 分片大小。优先使用用户提供的值。如果用户没有指定，那么对于新上传，计算出一个合理值；对于老的上传，采用第一个
        分片的大小。
    :param progress_callback: 上传进度回调函数。参见 :ref:`progress_callback` 。
    """
    def __init__(self, bucket, key, filename, size,
                 store=None,
                 headers=None,
                 part_size=None,
                 progress_callback=None,
                 num_threads=None):
        self.bucket = bucket
        self.key = key
        self.filename = filename
        self.size = size

        self.__store = store or ResumableStore()
        self.__headers = headers
        self.__part_size = defaults.get(part_size, defaults.part_size)

        self.__abspath = os.path.abspath(filename)
        self.__mtime = os.path.getmtime(filename)

        # protect self.__progress_callback
        self.__plock = threading.Lock()
        self.__progress_callback = progress_callback

        self.__num_threads = defaults.get(num_threads, defaults.multipart_num_threads)
        self.__store_key = self.__store.make_store_key(bucket.bucket_name, key, self.__abspath)

        self.__upload_id = None

        # protect below fields
        self.__lock = threading.Lock()
        self.__record = None
        self.__size_uploaded = 0
        self.__parts = None

    def upload(self):
        self.__load_record()
        parts_uploaded = self.__recorded_parts()

        parts_to_upload, self.__parts = self.__get_parts_to_upload(parts_uploaded)
        parts_to_upload = sorted(parts_to_upload, key=lambda p: p.part_number)

        self.__size_uploaded = sum(p.size for p in self.__parts)

        q = TaskQueue(functools.partial(self.__producer, parts_to_upload=parts_to_upload),
                      [self.__consumer] * self.__num_threads)
        q.run()

        self.__report_progress(self.size)

        self.bucket.complete_multipart_upload(self.key, self.__upload_id, self.__parts)
        self.__store_delete()

    def __producer(self, q, parts_to_upload=None):
        for part in parts_to_upload:
            q.put(part)

    def __consumer(self, q):
        while True:
            part = q.get()
            if part is None:
                break

            self.__upload_part(part)

    def __upload_part(self, part):
        with open(to_unicode(self.filename), 'rb') as f:
            self.__report_progress(self.__size_uploaded)

            f.seek(part.start, os.SEEK_SET)
            result = self.bucket.upload_part(self.key, self.__upload_id, part.part_number,
                                             utils.SizedFileAdapter(f, part.size))

            self.__finish_part(PartInfo(part.part_number, result.etag, size=part.size))

    def __finish_part(self, part_info):
        with self.__lock:
            self.__parts.append(part_info)
            self.__size_uploaded += part_info.size

            self.__record['parts'].append({'part_number': part_info.part_number, 'etag': part_info.etag})
            self.__store_put(self.__record)

    def __report_progress(self, uploaded_size):
        if self.__progress_callback:
            with self.__plock:
                self.__progress_callback(uploaded_size, self.size)

    def __store_get(self):
        return self.__store.get(self.__store_key)

    def __store_put(self, record):
        return self.__store.put(self.__store_key, record)

    def __store_delete(self):
        return self.__store.delete(self.__store_key)

    def __load_record(self):
        record = self.__store_get()

        if record and not _is_record_sane(record):
            self.__store_delete()
            record = None

        if record and self.__file_changed(record):
            logging.debug('{0} was changed, clear the record.'.format(self.filename))
            self.__store_delete()
            record = None

        if record and not self.__upload_exists(record['upload_id']):
            self.__store_delete()
            record = None

        if record:
            self.__record = record
        else:
            part_size = determine_part_size(self.size, self.__part_size)
            upload_id = self.bucket.init_multipart_upload(self.key, headers=self.__headers).upload_id
            record = {'upload_id': upload_id, 'mtime': self.__mtime, 'size': self.size, 'parts': [],
                      'abspath': self.__abspath, 'key': self.key,
                      'part_size': part_size}

            self.__store_put(record)

        self.__part_size = record['part_size']
        self.__upload_id = record['upload_id']
        self.__record = record

    def __recorded_parts(self):
        last_part_number = utils.how_many(self.size, self.__part_size)

        parts_uploaded = []

        for p in self.__record['parts']:
            part_info = PartInfo(int(p['part_number']), p['etag'])
            if part_info.part_number == last_part_number:
                part_info.size = self.size % self.__part_size
            else:
                part_info.size = self.__part_size

            parts_uploaded.append(part_info)

        return parts_uploaded

    def __upload_exists(self, upload_id):
        try:
            list(iterators.PartIterator(self.bucket, self.key, upload_id, '0', max_parts=1))
        except exceptions.NoSuchUpload:
            return False
        else:
            return True

    def __file_changed(self, record):
        return record['mtime'] != self.__mtime or record['size'] != self.size

    def __get_parts_to_upload(self, parts_uploaded):
        num_parts = utils.how_many(self.size, self.__part_size)
        uploaded_map = {}
        to_upload_map = {}

        for uploaded in parts_uploaded:
            uploaded_map[uploaded.part_number] = uploaded

        for i in range(num_parts):
            if i == num_parts - 1:
                start = i * self.__part_size
                end = self.size
            else:
                start = i * self.__part_size
                end = self.__part_size + start

            to_upload_map[i + 1] = _PartToUpload(i + 1, start, end)

        if not parts_uploaded:
            return to_upload_map.values(), []

        kept_parts = []

        for uploaded in parts_uploaded:
            if uploaded.part_number in to_upload_map:
                del to_upload_map[uploaded.part_number]
                kept_parts.append(uploaded)

        return to_upload_map.values(), kept_parts


_UPLOAD_TEMP_DIR = '.py-oss-upload'


class ResumableStore(object):
    """操作续传信息的类。

    每次上传的信息会保存在root/dir/下面的某个文件里。

    :param str root: 父目录，缺省为HOME
    :param str dir: 自目录，缺省为_UPLOAD_TEMP_DIR
    """
    def __init__(self, root=None, dir=None):
        root = root or os.path.expanduser('~')
        dir = dir or _UPLOAD_TEMP_DIR

        self.dir = os.path.join(root, dir)

        if os.path.isdir(self.dir):
            return

        utils.makedir_p(self.dir)

    @staticmethod
    def make_store_key(bucket_name, key, filename):
        oss_pathname = 'oss://{0}/{1}'.format(bucket_name, key)
        return utils.md5_string(oss_pathname) + '-' + utils.md5_string(filename)

    def get(self, key):
        pathname = self.__path(key)

        logging.debug('get key={0}, pathname={1}'.format(key, pathname))

        if not os.path.exists(pathname):
            return None

        # json.load()返回的总是unicode，对于Python2，我们将其转换
        # 为str。
        with open(to_unicode(pathname), 'r') as f:
            return stringify(json.load(f))

    def put(self, key, value):
        pathname = self.__path(key)

        with open(to_unicode(pathname), 'w') as f:
            json.dump(value, f)

        logging.debug('put key={0}, pathname={1}'.format(key, pathname))

    def delete(self, key):
        pathname = self.__path(key)
        os.remove(pathname)

        logging.debug('del key={0}, pathname={1}'.format(key, pathname))

    def __path(self, key):
        return os.path.join(self.dir, key)


def make_upload_store():
    return ResumableStore(dir=_UPLOAD_TEMP_DIR)


def _rebuild_record(filename, store, bucket, key, upload_id, part_size=None):
    abspath = os.path.abspath(filename)
    mtime = os.path.getmtime(filename)
    size = os.path.getsize(filename)

    store_key = store.make_store_key(bucket.bucket_name, key, abspath)
    record = {'upload_id': upload_id, 'mtime': mtime, 'size': size, 'parts': [],
              'abspath': abspath, 'key': key}

    for p in iterators.PartIterator(bucket, key, upload_id):
        record['parts'].append({'part_number': p.part_number,
                                'etag': p.etag})

        if not part_size:
            part_size = p.size

    record['part_size'] = part_size

    store.put(store_key, record)


def _is_record_sane(record):
    try:
        for key in ('upload_id', 'abspath', 'key'):
            if not isinstance(record[key], str):
                logging.info('{0} is not a string: {1}, but {2}'.format(key, record[key], record[key].__class__))
                return False

        for key in ('size', 'part_size'):
            if not isinstance(record[key], int):
                logging.info('{0} is not an integer: {1}'.format(key, record[key]))
                return False

        if not isinstance(record['mtime'], int) and not isinstance(record['mtime'], float):
            logging.info('mtime is not a float or an integer: {0}'.format(record['mtime']))
            return False

        if not isinstance(record['parts'], list):
            logging.info('parts is not a list: {0}'.format(record['parts'].__class__.__name__))
            return False
    except KeyError as e:
        logging.info('Key not found: {0}'.format(e.args))
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
