# -*- coding: utf-8 -*-

import unittest
import hashlib

import oss2

from .common import *
from oss2 import to_string


class TestIterator(OssTestCase):
    def test_bucket_iterator(self):
        service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)
        self.assertTrue(OSS_BUCKET in (b.name for b in oss2.BucketIterator(service, max_keys=2)))

    def test_object_iterator(self):
        prefix = self.random_key('/')
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
        for info in oss2.ObjectIterator(self.bucket, prefix, delimiter='/', max_keys=4):
            if info.is_prefix():
                dirs_got.append(info.key)
            else:
                objects_got.append(info.key)

                result = self.bucket.head_object(info.key)
                self.assertEqual(result.last_modified, info.last_modified)

        self.assertEqual(sorted(object_list), objects_got)
        self.assertEqual(sorted(dir_list), dirs_got)

        delete_keys(self.bucket, object_list)

    def test_object_iterator_chinese(self):
        for prefix in [self.random_key('中+文'), self.random_key(u'中+文')]:
            self.bucket.put_object(prefix, b'content of object')
            object_got = list(oss2.ObjectIterator(self.bucket, prefix=prefix, max_keys=1))[0].key
            self.assertEqual(to_string(prefix), object_got)

    def test_upload_iterator(self):
        prefix = self.random_key('/')
        key = prefix + random_string(16)

        upload_list = []
        dir_list = []

        # 准备分片上传
        for i in range(10):
            upload_list.append(self.bucket.init_multipart_upload(key).upload_id)

        # 准备碎片目录
        for i in range(4):
            dir_list.append(prefix + random_string(5) + '/')
            self.bucket.init_multipart_upload(dir_list[-1] + random_string(5))

        # 验证
        uploads_got = []
        dirs_got = []
        for u in oss2.MultipartUploadIterator(self.bucket, prefix=prefix, delimiter='/', max_uploads=2):
            if u.is_prefix():
                dirs_got.append(u.key)
            else:
                uploads_got.append(u.upload_id)

        self.assertEqual(sorted(upload_list), uploads_got)
        self.assertEqual(sorted(dir_list), dirs_got)

    def test_upload_iterator_chinese(self):
        upload_list = []

        p = self.random_key()
        prefix_list = [p + '中文-阿+里-巴*巴', p + u'中文-四/十*大%盗']
        for prefix in prefix_list:
            upload_list.append(self.bucket.init_multipart_upload(prefix).upload_id)

        uploads_got = []
        for prefix in prefix_list:
            listed = list(oss2.MultipartUploadIterator(self.bucket, prefix=prefix, max_uploads=1))
            uploads_got.append(listed[0].upload_id)

        self.assertEqual(sorted(upload_list), sorted(uploads_got))

    def test_object_upload_iterator(self):
        # target_object是想要列举的文件，而intact_object则不是。
        # 这里intact_object故意以target_object为前缀
        target_object = self.random_key()
        intact_object = self.random_key()

        target_list = []
        intact_list = []

        # 准备分片
        for i in range(10):
            target_list.append(self.bucket.init_multipart_upload(target_object).upload_id)
            intact_list.append(self.bucket.init_multipart_upload(intact_object).upload_id)

        # 验证：max_uploads能被分片数整除
        uploads_got = []
        for u in oss2.ObjectUploadIterator(self.bucket, target_object, max_uploads=5):
            uploads_got.append(u.upload_id)

        self.assertEqual(sorted(target_list), uploads_got)

        # 验证：max_uploads不能被分片数整除
        uploads_got = []
        for u in oss2.ObjectUploadIterator(self.bucket, target_object, max_uploads=3):
            uploads_got.append(u.upload_id)

        self.assertEqual(sorted(target_list), uploads_got)


        # 清理
        for upload_id in target_list:
            self.bucket.abort_multipart_upload(target_object, upload_id)

        for upload_id in intact_list:
            self.bucket.abort_multipart_upload(intact_object, upload_id)

    def test_part_iterator(self):
        for key in [random_string(16), '中文+_)(*&^%$#@!前缀', u'中文+_)(*&^%$#@!前缀']:
            upload_id = self.bucket.init_multipart_upload(key).upload_id

            # 准备分片
            part_list = []
            for part_number in [1, 3, 6, 7, 9, 10]:
                content = random_string(128 * 1024)
                etag = hashlib.md5(oss2.to_bytes(content)).hexdigest().upper()
                part_list.append(oss2.models.PartInfo(part_number, etag, len(content)))

                self.bucket.upload_part(key, upload_id, part_number, content)

            # 验证
            parts_got = []
            for part_info in oss2.PartIterator(self.bucket, key, upload_id):
                parts_got.append(part_info)

            self.assertEqual(len(part_list), len(parts_got))

            for i in range(len(part_list)):
                self.assertEqual(part_list[i].part_number, parts_got[i].part_number)
                self.assertEqual(part_list[i].etag, parts_got[i].etag)
                self.assertEqual(part_list[i].size, parts_got[i].size)

            self.bucket.abort_multipart_upload(key, upload_id)

    def test_live_channel_iterator(self):
        prefix = self.random_key()
        channel_name_list = []

        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = 'test.m3u8')
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        # 准备频道
        for i in range(20):
            channel_name_list.append(prefix + random_string(16))
            self.bucket.create_live_channel(channel_name_list[-1], channel_info)

        # 验证
        live_channel_got = []
        for info in oss2.LiveChannelIterator(self.bucket, prefix, max_keys=4):
            live_channel_got.append(info.name)

            result = self.bucket.get_live_channel(info.name)
            self.assertEqual(result.description, info.description)

        self.assertEqual(sorted(channel_name_list), live_channel_got)

        for live_channel in channel_name_list:
            self.bucket.delete_live_channel(live_channel)


if __name__ == '__main__':
    unittest.main()