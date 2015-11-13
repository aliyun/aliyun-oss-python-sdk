# -*- coding: utf-8 -*-

import unittest
import logging
import hashlib

import oss
from common import *


class TestIterator(unittest.TestCase):
    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    def test_bucket_iterator(self):
        service = oss.Service(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)
        self.assertTrue(OSS_BUCKET in (b.name for b in oss.BucketIterator(service)))

    def test_object_iterator(self):
        prefix = random_string(12) + '/'
        object_list = []
        dir_list = []

        # 准备文件
        for i in range(20):
            object_list.append(prefix + random_string(16))
            self.bucket.put_object(object_list[-1], random_bytes(10))

        # 准备目录
        for i in range(5):
            dir_list.append(prefix + random_string(5) + '/')
            self.bucket.put_object(dir_list[-1] + random_string(5), random_bytes(3))

        # 验证
        objects_got = []
        dirs_got = []
        for info in oss.easy.ObjectIterator(self.bucket, prefix, delimiter='/', max_keys=4):
            if info.is_prefix():
                dirs_got.append(info.name)
            else:
                objects_got.append(info.name)

        self.assertEqual(sorted(object_list), objects_got)
        self.assertEqual(sorted(dir_list), dirs_got)

    def test_upload_iterator(self):
        prefix = random_string(10) + '/'
        object_name = prefix + random_string(16)

        upload_list = []
        dir_list = []

        # 准备分片上传
        for i in range(10):
            upload_list.append(self.bucket.init_multipart_upload(object_name).upload_id)

        # 准备碎片目录
        for i in range(4):
            dir_list.append(prefix + random_string(5) + '/')
            self.bucket.init_multipart_upload(dir_list[-1] + random_string(5))

        # 验证
        uploads_got = []
        dirs_got = []
        for u in oss.easy.MultipartUploadIterator(self.bucket, prefix=prefix, delimiter='/', max_uploads=2):
            if u.is_prefix():
                dirs_got.append(u.object_name)
            else:
                uploads_got.append(u.upload_id)

        self.assertEqual(sorted(upload_list), uploads_got)
        self.assertEqual(sorted(dir_list), dirs_got)

    def test_part_iterator(self):
        object_name = random_string(16)

        upload_id = self.bucket.init_multipart_upload(object_name).upload_id

        # 准备分片
        part_list = []
        for part_number in [1, 3, 6, 7, 9, 10]:
            content = random_string(128 * 1024)
            etag = hashlib.md5(oss.compat.to_bytes(content)).hexdigest().upper()
            part_list.append(oss.models.PartInfo(part_number, etag, len(content)))

            self.bucket.upload_part(object_name, upload_id, part_number, content)

        # 验证
        parts_got = []
        for part_info in oss.easy.PartIterator(self.bucket, object_name, upload_id):
            parts_got.append(part_info)

        self.assertEqual(len(part_list), len(parts_got))

        for i in range(len(part_list)):
            self.assertEqual(part_list[i].part_number, parts_got[i].part_number)
            self.assertEqual(part_list[i].etag, parts_got[i].etag)
            self.assertEqual(part_list[i].size, parts_got[i].size)



