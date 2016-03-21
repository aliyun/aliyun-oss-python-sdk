# -*- coding: utf-8 -*-

import unittest
import oss2
import os
import sys
import time
import copy

from mock import patch
from functools import partial

from common import *

import logging
logging.basicConfig(format="%(levelname)s %(funcName)s %(thread)d %(message)s", level=logging.INFO)


def modify_one(store, store_key, r, key=None, value=None):
    r[key] = value
    store.put(store_key, r)


class TestDownload(OssTestCase):
    def __prepare(self, file_size):
        content = random_bytes(file_size)
        key = self.random_key()
        filename = self.random_filename()

        self.bucket.put_object(key, content)

        return key, filename, content

    def __record(self, key, filename):
        store = oss2.resumable.make_download_store()
        store_key = store.make_store_key(self.bucket.bucket_name, key, os.path.abspath(filename))
        return store.get(store_key)

    def __test_normal(self, file_size):
        key, filename, content = self.__prepare(file_size)
        oss2.resumable_download(self.bucket, key, filename)

        self.assertFileContent(filename, content)

    def test_small(self):
        oss2.defaults.multiget_threshold = 1024 * 1024

        self.__test_normal(1023)

    def test_large_single_threaded(self):
        oss2.defaults.multiget_threshold = 1024 * 1024
        oss2.defaults.multiget_part_size = 100 * 1024 + 1
        oss2.defaults.multiget_num_threads = 1

        self.__test_normal(2 * 1024 * 1024 + 1)

    def test_large_multi_threaded(self):
        """多线程，线程数少于分片数"""

        oss2.defaults.multiget_threshold = 1024 * 1024
        oss2.defaults.multiget_part_size = 100 * 1024
        oss2.defaults.multiget_num_threads = 7

        self.__test_normal(2 * 1024 * 1024)

    def test_large_many_threads(self):
        """线程数多余分片数"""

        oss2.defaults.multiget_threshold = 1024 * 1024
        oss2.defaults.multiget_part_size = 100 * 1024
        oss2.defaults.multiget_num_threads = 10

        self.__test_normal(512 * 1024 - 1)

    def __test_resume(self, file_size, failed_parts, modify_func_record=None):
        orig_download_part = oss2.resumable._ResumableDownloader._ResumableDownloader__download_part

        def fail_download_part(self, part, failed_parts=None):
            if part.part_number in failed_parts:
                raise RuntimeError("Fail download_part for part: {0}".format(part.part_number))
            else:
                orig_download_part(self, part)

        key, filename, content = self.__prepare(file_size)

        with patch.object(oss2.resumable._ResumableDownloader, '_ResumableDownloader__download_part',
                          side_effect=partial(fail_download_part, failed_parts=failed_parts),
                          autospec=True):
            self.assertRaises(RuntimeError, oss2.resumable_download, self.bucket, key, filename)

        store = oss2.resumable.make_download_store()
        store_key = store.make_store_key(self.bucket.bucket_name, key, os.path.abspath(filename))
        record = store.get(store_key)

        tmp_file = filename + record['tmp_suffix']
        self.assertTrue(os.path.exists(tmp_file))
        self.assertTrue(not os.path.exists(filename))

        oss2.resumable_download(self.bucket, key, filename)

        self.assertTrue(not os.path.exists(tmp_file))
        self.assertFileContent(filename, content)

    def test_resume_hole_start(self):
        """最后一个part失败"""

        oss2.defaults.multiget_threshold = 1
        oss2.defaults.multiget_part_size = 500
        oss2.defaults.multiget_num_threads = 3

        self.__test_resume(500 * 10 + 16, [1])

    def test_resume_hole_end(self):
        """最后一个part失败"""

        oss2.defaults.multiget_threshold = 1
        oss2.defaults.multiget_part_size = 500
        oss2.defaults.multiget_num_threads = 2

        self.__test_resume(500 * 10 + 16, [11])

    def test_resume_hole_mid(self):
        """最后一个part失败"""

        oss2.defaults.multiget_threshold = 1
        oss2.defaults.multiget_part_size = 500
        oss2.defaults.multiget_num_threads = 3

        self.__test_resume(500 * 10 + 16, [3])

    def test_resume_rename_failed(self):
        size = 500 * 10
        part_size = 499

        oss2.defaults.multiget_threshold = 1
        oss2.defaults.multiget_part_size = part_size
        oss2.defaults.multiget_num_threads = 3

        key, filename, content = self.__prepare(size)

        with patch.object(os, 'rename', side_effect=RuntimeError(), autospec=True):
            self.assertRaises(RuntimeError, oss2.resumable_download, self.bucket, key, filename)

        r = self.__record(key, filename)

        # assert record fields are valid
        head_object_result = self.bucket.head_object(key)

        self.assertEqual(r['size'], size)
        self.assertEqual(r['mtime'], head_object_result.last_modified)
        self.assertEqual(r['etag'], head_object_result.etag)

        self.assertEqual(r['bucket'], self.bucket.bucket_name)
        self.assertEqual(r['key'], key)
        self.assertEqual(r['part_size'], part_size)

        self.assertTrue(os.path.exists(filename + r['tmp_suffix']))
        self.assertFileContent(filename + r['tmp_suffix'], content)

        self.assertTrue(not os.path.exists(filename))

        self.assertEqual(r['abspath'], os.path.abspath(filename))

        self.assertEqual(len(r['parts']), oss2.utils.how_many(size, part_size))

        parts = sorted(r['parts'], key=lambda p: p['part_number'])
        for i, p in enumerate(parts):
            self.assertEqual(p['part_number'], i+1)
            self.assertEqual(p['start'], part_size * i)
            self.assertEqual(p['end'], min(part_size*(i+1), size))

        with patch.object(oss2.resumable._ResumableDownloader, '_ResumableDownloader__download_part',
                          side_effect=RuntimeError(),
                          autospec=True):
            oss2.resumable_download(self.bucket, key, filename)

        self.assertTrue(not os.path.exists(filename + r['tmp_suffix']))
        self.assertFileContent(filename, content)
        self.assertEqual(self.__record(key, filename), None)

    def __test_insane_record(self, file_size, modify_record_func, old_tmp_exists=True):
        orig_rename = os.rename

        obj = NonlocalObject({})

        key, filename, content = self.__prepare(file_size)

        def mock_rename(src, dst):
            obj.var = self.__record(key, filename)
            orig_rename(src, dst)

        with patch.object(os, 'rename', side_effect=RuntimeError(), autospec=True):
            self.assertRaises(RuntimeError, oss2.resumable_download, self.bucket, key, filename)

        store = oss2.resumable.make_download_store()
        store_key = store.make_store_key(self.bucket.bucket_name, key, os.path.abspath(filename))
        r = store.get(store_key)

        modify_record_func(store, store_key, copy.deepcopy(r))

        with patch.object(os, 'rename', side_effect=mock_rename, autospec=True):
            oss2.resumable_download(self.bucket, key, filename)

        new_r = obj.var

        self.assertTrue(new_r['tmp_suffix'] != r['tmp_suffix'])

        self.assertEqual(new_r['size'], r['size'])
        self.assertEqual(new_r['mtime'], r['mtime'])
        self.assertEqual(new_r['etag'], r['etag'])
        self.assertEqual(new_r['part_size'], r['part_size'])

        self.assertEqual(os.path.exists(filename + r['tmp_suffix']), old_tmp_exists)
        self.assertTrue(not os.path.exists(filename + new_r['tmp_suffix']))

        oss2.utils.silently_remove(filename + r['tmp_suffix'])

    def test_insane_record_modify(self):
        oss2.defaults.multiget_threshold = 1
        oss2.defaults.multiget_part_size = 128
        oss2.defaults.multiget_num_threads = 3

        self.__test_insane_record(400, partial(modify_one, key='size', value='123'))
        self.__test_insane_record(400, partial(modify_one, key='mtime', value='123'))
        self.__test_insane_record(400, partial(modify_one, key='etag', value=123))

        self.__test_insane_record(400, partial(modify_one, key='part_size', value={}))
        self.__test_insane_record(400, partial(modify_one, key='tmp_suffix', value={1:2}))
        self.__test_insane_record(400, partial(modify_one, key='parts', value={1:2}))

        self.__test_insane_record(400, partial(modify_one, key='abspath', value=123))
        self.__test_insane_record(400, partial(modify_one, key='bucket', value=123))
        self.__test_insane_record(400, partial(modify_one, key='key', value=1.2))

    def test_insane_record_missing(self):
        oss2.defaults.multiget_threshold = 1
        oss2.defaults.multiget_part_size = 128
        oss2.defaults.multiget_num_threads = 3

        def missing_one(store, store_key, r, key=None):
            del r[key]
            store.put(store_key, r)

        self.__test_insane_record(400, partial(missing_one, key='key'))
        self.__test_insane_record(400, partial(missing_one, key='mtime'))
        self.__test_insane_record(400, partial(missing_one, key='parts'))

    def test_insane_record_deleted(self):
        oss2.defaults.multiget_threshold = 1
        oss2.defaults.multiget_part_size = 128
        oss2.defaults.multiget_num_threads = 3

        def delete_record(store, store_key, r):
            store.delete(store_key)

        self.__test_insane_record(400, delete_record)

    def test_remote_changed_before_start(self):
        """在开始下载之前，OSS上的文件就已经被修改了"""
        oss2.defaults.multiget_threshold = 1

        # reuse __test_insane_record to simulate
        self.__test_insane_record(400, partial(modify_one, key='etag', value='BABEF00D123456789'), old_tmp_exists=False)
        self.__test_insane_record(400, partial(modify_one, key='size', value=1024), old_tmp_exists=False)
        self.__test_insane_record(400, partial(modify_one, key='mtime', value=1024), old_tmp_exists=False)

    def test_remote_changed_during_upload(self):
        oss2.defaults.multiget_threshold = 1
        oss2.defaults.multiget_part_size = 100
        oss2.defaults.multiget_num_threads = 2

        orig_download_part = oss2.resumable._ResumableDownloader._ResumableDownloader__download_part
        orig_rename = os.rename

        file_size = 1000
        key, filename, content = self.__prepare(file_size)

        old_context = {}
        new_context = {}

        def mock_download_part(self, part, part_number=None):
            if part.part_number == part_number:
                r = self.__record(key, filename)

                old_context['tmp_suffix'] = r['tmp_suffix']
                old_context['etag'] = r['etag']
                old_context['content'] = random_bytes(file_size)

                self.bucket.put_object(key, context['content'])

                orig_download_part(self, part)

        def mock_rename(src, dst):
            r = self.__record(key, filename)

            new_context['tmp_suffix'] = r['tmp_suffix']
            new_context['etag'] = r['etag']

            orig_rename(src, dst)

        with patch.object(oss2.resumable._ResumableDownloader, '_ResumableDownloader__download_part',
                          side_effect=partial(mock_download_part, part_number=5),
                          autospec=True):
            self.assertRaises(RuntimeError, oss2.resumable_download, self.bucket, key, filename)

        with patch.object(os.rename, side_effect=mock_rename):
            oss2.resumable_download(self.bucket, key, filename)

        self.assertTrue(new_context['tmp_suffix'] != old_context['tmp_suffix'])
        self.assertTrue(new_context['etag'] != old_context['etag'])

