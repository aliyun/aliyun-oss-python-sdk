# -*- coding: utf-8 -*-

import unittest
import oss2
from oss2.utils import calc_obj_crc_from_parts

from .common import *
from oss2.headers import OSS_OBJECT_TAGGING, OSS_OBJECT_TAGGING_COPY_DIRECTIVE
from oss2.compat import urlunquote, urlquote


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
        parts.append(oss2.models.PartInfo(1, result.etag, size=len(content), part_crc=result.crc))
        self.assertTrue(result.crc is not None)

        complete_result = self.bucket.complete_multipart_upload(key, upload_id, parts)

        object_crc = calc_obj_crc_from_parts(parts)
        self.assertTrue(complete_result.crc is not None)
        self.assertEqual(object_crc, result.crc)

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

    def test_init_multipart_with_object_tagging_exceptions(self):

        key = self.random_key()

        headers=dict()
        # wrong key
        tag_str='=a&b=a'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass

        # wrong key
        long_str=129*'a'
        tag_str=long_str+'=b&b=a'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass


        # wrong value
        tag_str='a=&b=c'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
        except oss2.exceptions.OssError:
            self.assertFalse(True, 'should get a exception')


        # wrong value
        long_str=257*'a'
        tag_str = 'a='+long_str+'&b=a'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass


        # dup kv
        tag_str='a=b&a=b&a=b'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass


        # max+1 kv pairs
        tag_str='a1=b1&a2=b2&a3=b4&a4=b4&a5=b5&a6=b6&a7=b7&a8=b8&a9=b9&a10=b10&a11=b11&a12=b12'
        headers[OSS_OBJECT_TAGGING] = tag_str
        try:
            resp = self.bucket.init_multipart_upload(key, headers=headers)
            self.assertFalse(True, 'should get a exception')
        except oss2.exceptions.OssError:
            pass

    def test_multipart_with_object_tagging(self):

        key = self.random_key()
        content = random_bytes(128 * 1024)

        tag_str=''

        tag_key1=urlquote('+:/')
        tag_value1=urlquote('.-')
        tag_str = tag_key1+'='+tag_value1

        tag_ke2=urlquote(' + ')
        tag_value2=urlquote(u'中文'.encode('UTF-8'))
        tag_str += '&'+tag_ke2+'='+tag_value2

        headers=dict()
        headers[OSS_OBJECT_TAGGING] = tag_str

        parts = []
        upload_id = self.bucket.init_multipart_upload(key, headers=headers).upload_id

        headers = {'Content-Md5': oss2.utils.content_md5(content)}

        result = self.bucket.upload_part(key, upload_id, 1, content, headers=headers)
        parts.append(oss2.models.PartInfo(1, result.etag, size=len(content), part_crc=result.crc))
        self.assertTrue(result.crc is not None)

        complete_result = self.bucket.complete_multipart_upload(key, upload_id, parts)

        object_crc = calc_obj_crc_from_parts(parts)
        self.assertTrue(complete_result.crc is not None)
        self.assertEqual(object_crc, result.crc)

        result = self.bucket.get_object(key)
        self.assertEqual(content, result.read())

        result = self.bucket.get_object_tagging(key)

        self.assertEqual(2, result.tag_set.len())
        self.assertEqual('.-', result.tag_set.tagging_rule['+:/'])
        self.assertEqual('中文', result.tag_set.tagging_rule[' + '])

        result = self.bucket.delete_object_tagging(key)
   
if __name__ == '__main__':
    unittest.main()
