# -*- coding: utf-8 -*-

import unittest
import oss
import oss.iterators
import os
import tempfile
import logging
import sys

from common import *

logging.basicConfig(level=logging.DEBUG)


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

        oss.resumable.upload_file(pathname, self.bucket, object_name, part_size=100*1024, multipart_threshold=200*1024)

        result = self.bucket.get_object(object_name)
        self.assertEqual(content, result.read())
        self.assertEqual(result.headers['x-oss-object-type'], 'Multipart')

    def __test_resume(self, content_size, uploaded_parts, upload_part_func=None, expected_unfinished=0):
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

            if upload_part_func:
                upload_part_func(object_name, upload_id, part_number, content[start:end])
            else:
                self.bucket.upload_part(object_name, upload_id, part_number, content[start:end])

        oss.resumable.rebuild_record(pathname, oss.resumable.FileStore(), self.bucket, object_name, upload_id, part_size)

        oss.resumable.upload_file(self.bucket, object_name, pathname, part_size=100*1024, multipart_threshold=0)

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

    def __test_interrupt(self, content_size, failed_part_number):
        orig_upload_part = oss.Bucket.upload_part

        def upload_part(self, object_name, upload_id, part_number, data):
            if part_number == failed_part_number:
                raise RuntimeError
            else:
                return orig_upload_part(self, object_name, upload_id, part_number, data)

        from unittest.mock import patch

        object_name = 'resume-' + random_string(32)
        content = random_bytes(content_size)

        pathname = self._prepare_temp_file(content)

        with patch.object(oss.Bucket, 'upload_part', side_effect=upload_part, autospec=True) as mock_upload_part:
            try:
                oss.resumable.upload_file(pathname, self.bucket, object_name, part_size=100*1024, multipart_threshold=0)
            except RuntimeError:
                pass

        oss.resumable.upload_file(pathname, self.bucket, object_name, part_size=100*1024, multipart_threshold=0)

        self.assertTrue(not list(oss.iterators.ObjectUploadIterator(self.bucket, object_name)))

    @unittest.skipIf(sys.version_info < (3, 3), 'Py33 is required')
    def test_interrupt_empty(self):
        self.__test_interrupt(310 * 1024, 1)

    @unittest.skipIf(sys.version_info < (3, 3), 'Py33 is required')
    def test_interrupt_mid(self):
        self.__test_interrupt(510 * 1024, 3)

    @unittest.skipIf(sys.version_info < (3, 3), 'Py33 is required')
    def test_interrupt_last(self):
        self.__test_interrupt(500 * 1024 - 1, 5)

if __name__ == '__main__':
    unittest.main()
