# -*- coding: utf-8 -*-

import unittest
import requests
import filecmp
import os
import calendar
import time

import oss2

from oss2.exceptions import NotFound, NoSuchKey, Conflict, PositionNotEqualToLength, ObjectNotAppendable
from oss2 import to_string

from common import *


def now():
    return int(calendar.timegm(time.gmtime()))


class TestObject(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestObject, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    def test_object(self):
        key = random_string(12) + '.js'
        content = random_bytes(1024)

        self.assertRaises(NotFound, self.bucket.head_object, key)

        lower_bound = now() - 60 * 16
        upper_bound = now() + 60 * 16

        def assert_result(result):
            self.assertEqual(result.content_length, len(content))
            self.assertEqual(result.content_type, 'application/javascript')
            self.assertEqual(result.object_type, 'Normal')

            self.assertTrue(result.last_modified > lower_bound)
            self.assertTrue(result.last_modified < upper_bound)

            self.assertTrue(result.etag)

        self.bucket.put_object(key, content)

        get_result = self.bucket.get_object(key)
        self.assertEqual(get_result.read(), content)
        assert_result(get_result)

        head_result = self.bucket.head_object(key)
        assert_result(head_result)

        self.assertEqual(get_result.last_modified, head_result.last_modified)
        self.assertEqual(get_result.etag, head_result.etag)

        self.bucket.delete_object(key)

        self.assertRaises(NoSuchKey, self.bucket.get_object, key)

    def test_file(self):
        filename = random_string(12) + '.js'
        filename2 = random_string(12)

        key = random_string(12) + '.txt'
        content = random_bytes(1024 * 1024)

        with open(filename, 'wb') as f:
            f.write(content)

        # 上传本地文件到OSS
        self.bucket.put_object_from_file(key, filename)

        # 检查Content-Type应该是javascript
        result = self.bucket.head_object(key)
        self.assertEqual(result.headers['content-type'], 'application/javascript')

        # 下载到本地文件
        self.bucket.get_object_to_file(key, filename2)

        self.assertTrue(filecmp.cmp(filename, filename2))

        # 清理
        os.remove(filename)
        os.remove(filename2)

    def test_streaming(self):
        src_key = random_string(12) + '.src'
        dst_key = random_string(12) + '.dst'

        content = random_bytes(1024 * 1024)

        self.bucket.put_object(src_key, content)

        # 获取OSS上的文件，一边读取一边写入到另外一个OSS文件
        src = self.bucket.get_object(src_key)
        self.bucket.put_object(dst_key, src)

        # verify
        self.assertEqual(self.bucket.get_object(src_key).read(), self.bucket.get_object(dst_key).read())

    def test_get_object_iterator(self):
        key = random_string(12)
        content = random_bytes(1024 * 1024)

        self.bucket.put_object(key, content)
        result = self.bucket.get_object(key)
        content_got = b''

        for chunk in result:
            content_got += chunk

        self.assertEqual(len(content), len(content_got))
        self.assertEqual(content, content_got)

    def test_anonymous(self):
        key = random_string(12)
        content = random_bytes(512)

        # 设置bucket为public-read，并确认可以上传和下载
        self.bucket.put_bucket_acl('public-read-write')

        b = oss2.Bucket(oss2.AnonymousAuth(), OSS_ENDPOINT, OSS_BUCKET)
        b.put_object(key, content)
        result = b.get_object(key)
        self.assertEqual(result.read(), content)

        # 测试sign_url
        url = b.sign_url('GET', key, 100)
        resp = requests.get(url)
        self.assertEqual(content, resp.content)

        # 设置bucket为private，并确认上传和下载都会失败
        self.bucket.put_bucket_acl('private')

        self.assertRaises(oss2.exceptions.AccessDenied, b.put_object, key, content)
        self.assertRaises(oss2.exceptions.AccessDenied, b.get_object, key)

    def test_range_get(self):
        key = random_string(12)
        content = random_bytes(1024)

        self.bucket.put_object(key, content)

        result = self.bucket.get_object(key, byte_range=(500, None))
        self.assertEqual(result.read(), content[500:])

        result = self.bucket.get_object(key, byte_range=(None, 199))
        self.assertEqual(result.read(), content[-199:])

        result = self.bucket.get_object(key, byte_range=(3, 3))
        self.assertEqual(result.read(), content[3:4])

    def test_list_objects(self):
        result = self.bucket.list_objects()
        self.assertEqual(result.status, 200)

    def test_batch_delete_objects(self):
        object_list = []
        for i in range(0, 5):
            key = random_string(12)
            object_list.append(key)

            self.bucket.put_object(key, random_string(64))

        result = self.bucket.batch_delete_objects(object_list)
        self.assertEqual(sorted(object_list), sorted(result.deleted_keys))

        for object in object_list:
            self.assertTrue(not self.bucket.object_exists(object))

    def test_append_object(self):
        key = random_string(12)
        content1 = random_bytes(512)
        content2 = random_bytes(128)

        result = self.bucket.append_object(key, 0, content1)
        self.assertEqual(result.next_position, len(content1))

        try:
            self.bucket.append_object(key, 0, content2)
        except PositionNotEqualToLength as e:
            self.assertEqual(e.next_position, len(content1))
        else:
            self.assertTrue(False)

        result = self.bucket.append_object(key, len(content1), content2)
        self.assertEqual(result.next_position, len(content1) + len(content2))

        self.bucket.delete_object(key)

    def test_private_download_url(self):
        for key in [random_string(12), u'中文文件名']:
            content = random_bytes(42)

            str_name = to_string(key)
            self.bucket.put_object(str_name, content)
            url = self.bucket.sign_url('GET', str_name, 60)

            resp = requests.get(url)
            self.assertEqual(content, resp.content)

    def test_copy_object(self):
        source_key = random_string(12)
        target_key = random_string(13)
        content = random_bytes(36)

        self.bucket.put_object(source_key, content)
        self.bucket.copy_object(self.bucket.bucket_name, source_key, target_key)

        result = self.bucket.get_object(target_key)
        self.assertEqual(content, result.read())

    def test_update_object_meta(self):
        key = random_string(12) + '.txt'
        content = random_bytes(36)

        self.bucket.put_object(key, content)

        # 更改Content-Type，增加用户自定义元数据
        self.bucket.update_object_meta(key, {'Content-Type': 'whatever',
                                                     'x-oss-meta-category': 'novel'})

        result = self.bucket.head_object(key)
        self.assertEqual(result.headers['content-type'], 'whatever')
        self.assertEqual(result.headers['x-oss-meta-category'], 'novel')

    def test_object_acl(self):
        key = random_string(12)
        content = random_bytes(32)

        self.bucket.put_object(key, content)
        self.assertEqual(self.bucket.get_object_acl(key).acl, 'default')

        self.bucket.put_object_acl(key, 'private')
        self.assertEqual(self.bucket.get_object_acl(key).acl, 'private')

        self.bucket.delete_object(key)

    def test_object_exists(self):
        key = random_string(12)

        self.assertTrue(not self.bucket.object_exists(key))

        self.bucket.put_object(key, "hello world")
        self.assertTrue(self.bucket.object_exists(key))

    def test_user_meta(self):
        key = random_string(12)

        self.bucket.put_object(key, 'hello', headers={'x-oss-meta-key1': 'value1',
                                                      'X-Oss-Meta-Key2': 'value2'})

        headers = self.bucket.get_object(key).headers
        self.assertEqual(headers['x-oss-meta-key1'], 'value1')
        self.assertEqual(headers['x-oss-meta-key2'], 'value2')

    def test_progress(self):
        stats = {'previous': -1}

        def progress_callback(bytes_consumed, total_bytes, bytes_to_consume):
            self.assertTrue(bytes_consumed + bytes_to_consume <= total_bytes)
            self.assertTrue(bytes_consumed > stats['previous'])

            stats['previous'] = bytes_consumed

        key = random_string(12)
        content = random_bytes(2 * 1024 * 1024)

        # 上传内存中的内容
        stats = {'previous': -1}
        self.bucket.put_object(key, content, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 下载到文件
        stats = {'previous': -1}
        filename = random_string(12) + '.txt'
        self.bucket.get_object_to_file(key, filename, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 上传本地文件
        stats = {'previous': -1}
        self.bucket.put_object_from_file(key, filename, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 下载到本地，采用iterator语法
        stats = {'previous': -1}
        result = self.bucket.get_object(key, progress_callback=progress_callback)
        content_got = b''
        for chunk in result:
            content_got += chunk
        self.assertEqual(stats['previous'], len(content))
        self.assertEqual(content, content_got)

        os.remove(filename)

    def test_exceptions(self):
        key = random_string(12)
        content = random_bytes(16)

        self.assertRaises(NotFound, self.bucket.get_object, key)
        self.assertRaises(NoSuchKey, self.bucket.get_object, key)

        self.bucket.put_object(key, content)

        self.assertRaises(Conflict, self.bucket.append_object, key, len(content), b'more content')
        self.assertRaises(ObjectNotAppendable, self.bucket.append_object, key, len(content), b'more content')


if __name__ == '__main__':
    unittest.main()