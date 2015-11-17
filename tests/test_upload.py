# -*- coding: utf-8 -*-

import unittest
import oss
import os
import tempfile
import sys
import time

from common import *


class TestUpload(unittest.TestCase):
    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)
        self.temp_files = []

    def tearDown(self):
        for temp_file in self.temp_files:
            os.remove(temp_file)

    def _prepare_temp_file(self, content):
        fd, pathname = tempfile.mkstemp(suffix='test-upload')

        os.write(fd, content)
        os.close(fd)

        self.temp_files.append(pathname)
        return pathname

    def test_upload_small(self):
        object_name = random_string(16)
        content = random_bytes(100)

        pathname = self._prepare_temp_file(content)

        oss.resumable.upload_file(pathname, self.bucket, object_name)

        result = self.bucket.get_object(object_name)
        self.assertEqual(content, result.read())
        self.assertEqual(result.headers['x-oss-object-type'], 'Normal')

    def test_upload_large(self):
        object_name = random_string(16)
        content = random_bytes(5 * 100 * 1024)

        pathname = self._prepare_temp_file(content)

        oss.resumable.upload_file(pathname, self.bucket, object_name, multipart_threshold=200*1024, part_size=None)

        result = self.bucket.get_object(object_name)
        self.assertEqual(content, result.read())
        self.assertEqual(result.headers['x-oss-object-type'], 'Multipart')

    def __test_resume(self, content_size, uploaded_parts, expected_unfinished=0):
        part_size = 100 * 1024
        num_parts = (content_size + part_size - 1) // part_size

        object_name = 'resume-' + random_string(32)
        content = random_bytes(content_size)

        pathname = self._prepare_temp_file(content)

        upload_id = self.bucket.init_multipart_upload(object_name).upload_id

        for part_number in uploaded_parts:
            start = (part_number -1) * part_size
            if part_number == num_parts:
                end = content_size
            else:
                end = start + part_size

            self.bucket.upload_part(object_name, upload_id, part_number, content[start:end])

        oss.resumable.rebuild_record(pathname, oss.resumable.FileStore(), self.bucket, object_name, upload_id, part_size)
        oss.resumable.upload_file(pathname, self.bucket, object_name, part_size=100*1024, multipart_threshold=0)

        result = self.bucket.get_object(object_name)
        self.assertEqual(content, result.read())

        self.assertEqual(len(list(oss.iterators.ObjectUploadIterator(self.bucket, object_name))), expected_unfinished)

    def test_resume_empty(self):
        self.__test_resume(250 * 1024, [])

    def test_resume_continuous(self):
        self.__test_resume(500 * 1024, [1, 2])

    def test_resume_hole_mid(self):
        self.__test_resume(510 * 1024, [1, 4])

    def test_resume_hole_end(self):
        self.__test_resume(300 * 1024 + 1, [4])

    def __test_interrupt(self, content_size, failed_part_number,
                         expected_unfinished=0,
                         modify_record_func=None):
        orig_upload_part = oss.Bucket.upload_part

        def upload_part(self, object_name, upload_id, part_number, data):
            if part_number == failed_part_number:
                raise RuntimeError
            else:
                return orig_upload_part(self, object_name, upload_id, part_number, data)

        object_name = 'resume-' + random_string(32)
        content = random_bytes(content_size)

        pathname = self._prepare_temp_file(content)

        from unittest.mock import patch
        with patch.object(oss.Bucket, 'upload_part', side_effect=upload_part, autospec=True) as mock_upload_part:
            try:
                oss.resumable.upload_file(pathname, self.bucket, object_name, part_size=100*1024, multipart_threshold=0)
            except RuntimeError:
                pass

        if modify_record_func:
            modify_record_func(oss.resumable.FileStore(), self.bucket.bucket_name, object_name, pathname)

        oss.resumable.upload_file(pathname, self.bucket, object_name, part_size=100*1024, multipart_threshold=0)

        self.assertEqual(len(list(oss.iterators.ObjectUploadIterator(self.bucket, object_name))), expected_unfinished)

    if sys.version_info >= (3, 3):
        def test_interrupt_empty(self):
            self.__test_interrupt(310 * 1024, 1)

        def test_interrupt_mid(self):
            self.__test_interrupt(510 * 1024, 3)

        def test_interrupt_last(self):
            self.__test_interrupt(500 * 1024 - 1, 5)

        def test_record_bad_size(self):
            self.__test_interrupt(500 * 1024, 3,
                                  modify_record_func=self.__make_corrupt_record('size', 'hello'),
                                  expected_unfinished=1)

        def test_record_no_such_upload_id(self):
            self.__test_interrupt(500 * 1024, 3,
                                  modify_record_func=self.__make_corrupt_record('upload_id', 'ABCD1234'),
                                  expected_unfinished=1)

        def test_file_changed_mtime(self):
            def change_mtime(store, bucket_name, object_name, pathname):
                time.sleep(2)
                os.utime(pathname, (time.time(), time.time()))

            self.__test_interrupt(500 * 1024, 3,
                                  modify_record_func=change_mtime,
                                  expected_unfinished=1)

        def test_file_changed_size(self):
            def change_size(store, bucket_name, object_name, pathname):
                mtime = os.path.getmtime(pathname)

                with open(pathname, 'w') as f:
                    f.write('hello world')

                os.utime(pathname, (mtime, mtime))
            self.__test_interrupt(500 * 1024, 3,
                                  modify_record_func=change_size,
                                  expected_unfinished=1)
    else:
        print('skip error injection cases for Python version < 3.3')

    def __make_corrupt_record(self, name, value):
        def corrupt_record(store, bucket_name, object_name, pathname):
            key = store.make_key(bucket_name, object_name, pathname)

            record = store.get(key)
            record[name] = value
            store.put(key, record)
        return corrupt_record

    def test_is_record_sane(self):
        record = {
            'upload_id': 'ABCD',
            'size': 123,
            'part_size': 123,
            'mtime': 12345,
            'abspath': '/hello',
            'object_name': 'hello.txt',
            'parts': []
        }

        def check_not_sane(key, value):
            old = record[key]
            record[key] = value

            self.assertTrue(not oss.resumable.is_record_sane(record))

            record[key] = old

        self.assertTrue(oss.resumable.is_record_sane(record))
        self.assertTrue(not oss.resumable.is_record_sane({}))

        check_not_sane('upload_id', 1)
        check_not_sane('size', '123')
        check_not_sane('part_size', 'hello')
        check_not_sane('mtime', 'hello')
        check_not_sane('abspath', 1)
        check_not_sane('object_name', None)
        check_not_sane('parts', None)


if __name__ == '__main__':
    unittest.main()
