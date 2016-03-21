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
import shutil
import random
import string


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


def resumable_download(bucket, key, filename,
                       multiget_threshold=None,
                       part_size=None,
                       progress_callback=None,
                       num_threads=None):
    multiget_threshold = defaults.get(multiget_threshold, defaults.multiget_threshold)

    result = bucket.head_object(key)
    if result.content_length >= multiget_threshold:
        downloader = _ResumableDownloader(bucket, key, filename, _ObjectInfo.make(result),
                                          part_size=part_size,
                                          progress_callback=progress_callback,
                                          num_threads=num_threads)
        downloader.download()
    else:
        bucket.get_object_to_file(key, filename,
                                  progress_callback=progress_callback)


_MAX_MULTIGET_PART_COUNT = 100


class _ResumableOperation(object):
    def __init__(self, bucket, key, filename, size, store,
                 progress_callback=None):
        self.bucket = bucket
        self.key = key
        self.filename = filename
        self.size = size

        self._abspath = os.path.abspath(filename)

        self.__store = store
        self.__record_key = self.__store.make_store_key(bucket.bucket_name, key, self._abspath)

        # protect self.__progress_callback
        self.__plock = threading.Lock()
        self.__progress_callback = progress_callback

    def _del_record(self):
        self.__store.delete(self.__record_key)

    def _put_record(self, record):
        self.__store.put(self.__record_key, record)

    def _get_record(self):
        return self.__store.get(self.__record_key)

    def _report_progress(self, consumed_size):
        if self.__progress_callback:
            with self.__plock:
                self.__progress_callback(consumed_size, self.size)


def _split_to_parts(total_size, part_size):
    parts = []
    num_parts = utils.how_many(total_size, part_size)

    for i in range(num_parts):
        if i == num_parts - 1:
            start = i * part_size
            end = total_size
        else:
            start = i * part_size
            end = part_size + start

        parts.append(_PartToProcess(i + 1, start, end))

    return parts


class _ResumableDownloader(_ResumableOperation):
    def __init__(self, bucket, key, filename, objectInfo,
                 part_size=None,
                 store=None,
                 progress_callback=None,
                 num_threads=None):
        super(_ResumableDownloader, self).__init__(bucket, key, filename, objectInfo.size,
                                                   store or ResumableDownloadStore(),
                                                   progress_callback=progress_callback)
        self.objectInfo = objectInfo

        self.__part_size = defaults.get(part_size, defaults.multiget_part_size)
        self.__part_size = _determine_part_size_internal(self.size, self.__part_size, _MAX_MULTIGET_PART_COUNT)

        self.__tmp_file = None
        self.__num_threads = defaults.get(num_threads, defaults.multiget_num_threads)
        self.__finished_parts = None
        self.__finished_size = None

        # protect record
        self.__lock = threading.Lock()
        self.__record = None

    def download(self):
        self.__load_record()

        parts_to_download = self.__get_parts_to_download()

        # create tmp file is not exists
        open(self.__tmp_file, 'a').close()

        q = TaskQueue(functools.partial(self.__producer, parts_to_download=parts_to_download),
                      [self.__consumer] * self.__num_threads)
        q.run()

        os.rename(self.__tmp_file, self.filename)

        self._report_progress(self.size)
        self._del_record()

    def __producer(self, q, parts_to_download=None):
        for part in parts_to_download:
            q.put(part)

    def __consumer(self, q):
        while q.ok():
            part = q.get()
            if part is None:
                break

            self.__download_part(part)

    def __download_part(self, part):
        with open(self.__tmp_file, 'rb+') as f:
            f.seek(part.start, os.SEEK_SET)

            headers = {'If-Match': self.objectInfo.etag,
                       'If-Unmodified-Since': utils.http_date(self.objectInfo.mtime)}
            result = self.bucket.get_object(self.key, byte_range=(part.start, part.end - 1), headers=headers)
            shutil.copyfileobj(result, f)

        self.__finish_part(part)

    def __load_record(self):
        record = self._get_record()

        if record and not self.is_record_sane(record):
            self._del_record()
            record = None

        # TODO: if all parts have been uploaded, return here.
        # TODO: what if md5 conflict

        if record and self.__is_remote_changed(record):
            utils.silently_remove(self.filename + record['tmp_suffix'])
            self._del_record()
            record = None

        if not record:
            record = {'mtime': self.objectInfo.mtime, 'etag': self.objectInfo.etag, 'size': self.objectInfo.size,
                      'bucket': self.bucket.bucket_name, 'key': self.key, 'part_size': self.__part_size,
                      'tmp_suffix': self.__gen_tmp_suffix(), 'abspath': self._abspath,
                      'parts': []}
            self._put_record(record)

        self.__tmp_file = self.filename + record['tmp_suffix']
        self.__part_size = record['part_size']
        self.__finished_parts = list(_PartToProcess(p['part_number'], p['start'], p['end']) for p in record['parts'])
        self.__finished_size = sum(p.size for p in self.__finished_parts)
        self.__record = record

    def __get_parts_to_download(self):
        assert self.__record

        all_set = set(_split_to_parts(self.size, self.__part_size))
        finished_set = set(self.__finished_parts)

        return sorted(list(all_set - finished_set), key=lambda p: p.part_number)

    @staticmethod
    def is_record_sane(record):
        try:
            for key in ('etag', 'tmp_suffix', 'abspath', 'bucket', 'key'):
                if not isinstance(record[key], str):
                    logging.info('{0} is not a string: {1}, but {2}'.format(key, record[key], record[key].__class__))
                    return False

            for key in ('part_size', 'size', 'mtime'):
                if not isinstance(record[key], int):
                    logging.info('{0} is not an integer: {1}, but {2}'.format(key, record[key], record[key].__class__))
                    return False

            for key in ('parts'):
                if not isinstance(record['parts'], list):
                    logging.info('{0} is not a list: {1}, but {2}'.format(key, record[key], record[key].__class__))
                    return False
        except KeyError as e:
            logging.info('Key not found: {0}'.format(e.args))
            return False

        return True

    def __is_remote_changed(self, record):
        return (record['mtime'] != self.objectInfo.mtime or
            record['size'] != self.objectInfo.size or
            record['etag'] != self.objectInfo.etag)

    def __finish_part(self, part):
        logging.debug('finishing part: part_number={0}, start={1}, end={2}'.format(part.part_number, part.start, part.end))

        with self.__lock:
            self.__finished_parts.append(part)
            self.__finished_size += part.size

            self.__record['parts'].append({'part_number': part.part_number,
                                           'start': part.start,
                                           'end': part.end})
            self._put_record(self.__record)

    def __gen_tmp_suffix(self):
        return '.tmp-' + ''.join(random.choice(string.ascii_lowercase) for i in range(12))


def determine_part_size(total_size,
                        preferred_size=None):
    """确定分片大小。

    :param int total_size: 总共需要上传的长度
    :param int preferred_size: 用户期望的分片大小。如果不指定则采用defaults.part_size

    :return: 分片大小
    """
    if not preferred_size:
        preferred_size = defaults.part_size

    return _determine_part_size_internal(total_size, preferred_size, _MAX_PART_COUNT)


def _determine_part_size_internal(total_size, preferred_size, max_count):
    if total_size < preferred_size:
        return total_size

    if preferred_size * max_count < total_size:
        if total_size % max_count:
            return total_size // max_count + 1
        else:
            return total_size // max_count
    else:
        return preferred_size


class _ObjectInfo(object):
    def __init__(self):
        self.size = None
        self.etag = None
        self.mtime = None

    @staticmethod
    def make(head_object_result):
        objectInfo = _ObjectInfo()
        objectInfo.size = head_object_result.content_length
        objectInfo.etag = head_object_result.etag
        objectInfo.mtime = head_object_result.last_modified

        return objectInfo


class _ResumableUploader(_ResumableOperation):
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
        super(_ResumableUploader, self).__init__(bucket, key, filename, size,
                                                 store or ResumableStore(),
                                                 progress_callback=progress_callback)

        self.__headers = headers
        self.__part_size = defaults.get(part_size, defaults.part_size)

        self.__mtime = os.path.getmtime(filename)

        self.__num_threads = defaults.get(num_threads, defaults.multipart_num_threads)

        self.__upload_id = None

        # protect below fields
        self.__lock = threading.Lock()
        self.__record = None
        self.__finished_size = 0
        self.__finished_parts = None

    def upload(self):
        self.__load_record()

        parts_to_upload = self.__get_parts_to_upload(self.__finished_parts)
        parts_to_upload = sorted(parts_to_upload, key=lambda p: p.part_number)

        q = TaskQueue(functools.partial(self.__producer, parts_to_upload=parts_to_upload),
                      [self.__consumer] * self.__num_threads)
        q.run()

        self._report_progress(self.size)

        self.bucket.complete_multipart_upload(self.key, self.__upload_id, self.__finished_parts)
        self._del_record()

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
            self._report_progress(self.__finished_size)

            f.seek(part.start, os.SEEK_SET)
            result = self.bucket.upload_part(self.key, self.__upload_id, part.part_number,
                                             utils.SizedFileAdapter(f, part.size))

            self.__finish_part(PartInfo(part.part_number, result.etag, size=part.size))

    def __finish_part(self, part_info):
        with self.__lock:
            self.__finished_parts.append(part_info)
            self.__finished_size += part_info.size

            self.__record['parts'].append({'part_number': part_info.part_number, 'etag': part_info.etag})
            self._put_record(self.__record)

    def __load_record(self):
        record = self._get_record()

        if record and not _is_record_sane(record):
            self._del_record()
            record = None

        if record and self.__file_changed(record):
            logging.debug('{0} was changed, clear the record.'.format(self.filename))
            self._del_record()
            record = None

        if record and not self.__upload_exists(record['upload_id']):
            logging.debug('{0} upload not exist, clear the record.'.format(record['upload_id']))
            self._del_record()
            record = None

        if not record:
            part_size = determine_part_size(self.size, self.__part_size)
            upload_id = self.bucket.init_multipart_upload(self.key, headers=self.__headers).upload_id
            record = {'upload_id': upload_id, 'mtime': self.__mtime, 'size': self.size, 'parts': [],
                      'abspath': self._abspath, 'key': self.key,
                      'part_size': part_size}

            logging.debug('put new record upload_id={0} part_size={1}'.format(upload_id, part_size))
            self._put_record(record)

        self.__record = record
        self.__part_size = self.__record['part_size']
        self.__upload_id = self.__record['upload_id']
        self.__finished_parts = self.__get_finished_parts()
        self.__finished_size = sum(p.size for p in self.__finished_parts)

    def __get_finished_parts(self):
        last_part_number = utils.how_many(self.size, self.__part_size)

        parts = []

        for p in self.__record['parts']:
            part_info = PartInfo(int(p['part_number']), p['etag'])
            if part_info.part_number == last_part_number:
                part_info.size = self.size % self.__part_size
            else:
                part_info.size = self.__part_size

            parts.append(part_info)

        return parts

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
        all_parts = _split_to_parts(self.size, self.__part_size)
        if not parts_uploaded:
            return all_parts

        all_parts_map = dict((p.part_number, p) for p in all_parts)

        for uploaded in parts_uploaded:
            if uploaded.part_number in all_parts_map:
                del all_parts_map[uploaded.part_number]

        return all_parts_map.values()


_UPLOAD_TEMP_DIR = '.py-oss-upload'
_DOWNLOAD_TEMP_DIR = '.py-oss-download'


class _ResumableStoreBase(object):
    def __init__(self, root, dir):
        self.dir = os.path.join(root, dir)

        if os.path.isdir(self.dir):
            return

        utils.makedir_p(self.dir)

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


class ResumableStore(_ResumableStoreBase):
    """操作断点上传信息的类。

    每次上传的信息会保存在root/dir/下面的某个文件里。

    :param str root: 父目录，缺省为HOME
    :param str dir: 自目录，缺省为_UPLOAD_TEMP_DIR
    """
    def __init__(self, root=None, dir=None):
        super(ResumableStore, self).__init__(root or os.path.expanduser('~'), dir or _UPLOAD_TEMP_DIR)

    @staticmethod
    def make_store_key(bucket_name, key, filename):
        oss_pathname = 'oss://{0}/{1}'.format(bucket_name, key)
        return utils.md5_string(oss_pathname) + '-' + utils.md5_string(filename)


class ResumableDownloadStore(_ResumableStoreBase):
    def __init__(self, root=None, dir=None):
        super(ResumableDownloadStore, self).__init__(root or os.path.expanduser('~'), dir or _DOWNLOAD_TEMP_DIR)

    @staticmethod
    def make_store_key(bucket_name, key, filename):
        oss_pathname = 'oss://{0}/{1}'.format(bucket_name, key)
        return utils.md5_string(oss_pathname) + '-' + utils.md5_string(filename) + '-download'


def make_upload_store():
    return ResumableStore()


def make_download_store():
    return ResumableDownloadStore()


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


class _PartToProcess(object):
    def __init__(self, part_number, start, end):
        self.part_number = part_number
        self.start = start
        self.end = end

    @property
    def size(self):
        return self.end - self.start

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return self.__key() == other.__key()

    def __key(self):
        return (self.part_number, self.start, self.end)