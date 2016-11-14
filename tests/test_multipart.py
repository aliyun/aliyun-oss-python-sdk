# -*- coding: utf-8 -*-

import unittest
import oss2

from common import *


class TestMultipart(OssTestCase):
    def do_multipart_internal(self, do_md5):
        key = self.random_key()
        content = random_bytes(128 * 1024)

        parts = []
        upload_id = self.bucket.init_multipart_upload(key).upload_id

        if do_md5:
            headers = {'Content-Md5': oss2.utils.content_md5(content)}
        else:
            headers = None

        result = self.bucket.upload_part(key, upload_id, 1, content, headers=headers)
        parts.append(oss2.models.PartInfo(1, result.etag))
        self.assertTrue(result.crc is not None)

        self.bucket.complete_multipart_upload(key, upload_id, parts)

        result = self.bucket.get_object(key)
        self.assertEqual(content, result.read())

    def test_multipart(self):
        self.do_multipart_internal(False)

    def test_upload_part_content_md5_good(self):
        self.do_multipart_internal(True)

    def test_upload_part_content_md5_bad(self):
        key = self.random_key()
        content = random_bytes(128 * 1024)

        parts = []
        upload_id = self.bucket.init_multipart_upload(key).upload_id

        # construct a bad Content-Md5 by using 'content + content's Content-Md5
        headers = {'Content-Md5': oss2.utils.content_md5(content + content)}

        self.assertRaises(oss2.exceptions.InvalidDigest, self.bucket.upload_part, key, upload_id, 1, content, headers=headers)

    def test_progress(self):
        stats = {'previous': -1}

        def progress_callback(bytes_consumed, total_bytes):
            self.assertTrue(bytes_consumed <= total_bytes)
            self.assertTrue(bytes_consumed > stats['previous'])

            stats['previous'] = bytes_consumed

        key = self.random_key()
        content = random_bytes(128 * 1024)

        upload_id = self.bucket.init_multipart_upload(key).upload_id
        self.bucket.upload_part(key, upload_id, 1, content, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        self.bucket.abort_multipart_upload(key, upload_id)

    def test_upload_part_copy(self):
        src_object = self.random_key()
        dst_object = self.random_key()

        content = random_bytes(200 * 1024)

        # 上传源文件
        self.bucket.put_object(src_object, content)

        # part copy到目标文件
        parts = []
        upload_id = self.bucket.init_multipart_upload(dst_object).upload_id

        result = self.bucket.upload_part_copy(self.bucket.bucket_name, src_object,
                                              (0, 100 * 1024 - 1), dst_object, upload_id, 1)
        parts.append(oss2.models.PartInfo(1, result.etag))

        result = self.bucket.upload_part_copy(self.bucket.bucket_name, src_object,
                                              (100*1024, None), dst_object, upload_id, 2)
        parts.append(oss2.models.PartInfo(2, result.etag))

        self.bucket.complete_multipart_upload(dst_object, upload_id, parts)

        # 验证
        content_got = self.bucket.get_object(dst_object).read()
        self.assertEqual(len(content_got), len(content))
        self.assertEqual(content_got, content)


if __name__ == '__main__':
    unittest.main()