# -*- coding: utf-8 -*-

import unittest
import oss
import oss.easy
import os
import tempfile

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

        oss.easy.upload_file(pathname, self.bucket, object_name)

        result = self.bucket.get_object(object_name)
        self.assertEqual(content, result.read())
        self.assertEqual(result.headers['x-oss-object-type'], 'Normal')

    def test_upload_large(self):
        object_name = random_string(16)
        content = random_bytes(5 * 100 * 1024)

        pathname = self._prepare_temp_file(content)

        oss.easy.upload_file(pathname, self.bucket, object_name, part_size=100*1024, multipart_threshold=200*1024)

        result = self.bucket.get_object(object_name)
        self.assertEqual(content, result.read())
        self.assertEqual(result.headers['x-oss-object-type'], 'Multipart')

if __name__ == '__main__':
    unittest.main()
