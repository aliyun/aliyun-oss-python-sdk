# -*- coding: utf-8 -*-

import unittest
import oss
import logging

from common import *


class TestMultipart(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestMultipart, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    def test_multipart(self):
        object_name = random_string(64)
        content = random_bytes(128 * 1024)

        parts = []
        upload_id = self.bucket.init_multipart_upload(object_name).upload_id

        result = self.bucket.upload_part(object_name, upload_id, 1, content)
        parts.append(oss.models.PartInfo(1, result.etag))

        self.bucket.complete_multipart_upload(object_name, upload_id, parts)

        result = self.bucket.get_object(object_name)
        self.assertEqual(content, result.read())

    def test_upload_part_copy(self):
        src_object = random_string(64)
        dst_object = random_string(32)

        content = random_bytes(200 * 1024)

        # 上传源文件
        self.bucket.put_object(src_object, content)

        # part copy到目标文件
        parts = []
        upload_id = self.bucket.init_multipart_upload(dst_object).upload_id

        result = self.bucket.upload_part_copy(self.bucket.bucket_name, src_object,
                                              (0, 100 * 1024 - 1), dst_object, upload_id, 1)
        parts.append(oss.models.PartInfo(1, result.etag))

        result = self.bucket.upload_part_copy(self.bucket.bucket_name, src_object,
                                              (100*1024, None), dst_object, upload_id, 2)
        parts.append(oss.models.PartInfo(2, result.etag))

        self.bucket.complete_multipart_upload(dst_object, upload_id, parts)

        # 验证
        content_got = self.bucket.get_object(dst_object).read()
        self.assertEqual(len(content_got), len(content))
        self.assertEqual(content_got, content)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()