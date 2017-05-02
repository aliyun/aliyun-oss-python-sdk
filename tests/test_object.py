# -*- coding: utf-8 -*-

import requests
import filecmp
import calendar

from oss2.exceptions import (ClientError, RequestError, NoSuchBucket,
                             NotFound, NoSuchKey, Conflict, PositionNotEqualToLength, ObjectNotAppendable)
from common import *


def now():
    return int(calendar.timegm(time.gmtime()))


class TestObject(OssTestCase):
    def test_object(self):
        key = self.random_key('.js')
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
        self.assertTrue(get_result.client_crc is not None)
        self.assertTrue(get_result.server_crc is not None)
        self.assertTrue(get_result.client_crc == get_result.server_crc)

        head_result = self.bucket.head_object(key)
        assert_result(head_result)

        self.assertEqual(get_result.last_modified, head_result.last_modified)
        self.assertEqual(get_result.etag, head_result.etag)

        self.bucket.delete_object(key)

        self.assertRaises(NoSuchKey, self.bucket.get_object, key)

    def test_file(self):
        filename = random_string(12) + '.js'
        filename2 = random_string(12)

        key = self.random_key('.txt')
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

        # 上传本地文件的一部分到OSS
        key_partial = self.random_key('-partial.txt')
        offset = 100
        with open(filename, 'rb') as f:
            f.seek(offset, os.SEEK_SET)
            self.bucket.put_object(key_partial, f)

        # 检查上传后的文件
        result = self.bucket.get_object(key_partial)
        self.assertEqual(result.content_length, len(content) - offset)
        self.assertEqual(result.read(), content[offset:])

        # 清理
        os.remove(filename)
        os.remove(filename2)

    def test_streaming(self):
        src_key = self.random_key('.src')
        dst_key = self.random_key('.dst')

        content = random_bytes(1024 * 1024)

        self.bucket.put_object(src_key, content)

        # 获取OSS上的文件，一边读取一边写入到另外一个OSS文件
        src = self.bucket.get_object(src_key)
        result = self.bucket.put_object(dst_key, src)

        # verify        
        self.assertTrue(src.client_crc is not None)
        self.assertTrue(src.server_crc is not None)  
        self.assertEqual(src.client_crc, src.server_crc)
        self.assertEqual(result.crc, src.server_crc)
        self.assertEqual(self.bucket.get_object(src_key).read(), self.bucket.get_object(dst_key).read())

    def make_generator(self, content, chunk_size):
        def generator():
            offset = 0
            while offset < len(content):
                n = min(chunk_size, len(content) - offset)
                yield content[offset:offset+n]

                offset += n

        return generator()

    def test_data_generator(self):
        key = self.random_key()
        key2 = self.random_key()
        content = random_bytes(1024 * 1024 + 1)

        self.bucket.put_object(key, self.make_generator(content, 8192))
        self.assertEqual(self.bucket.get_object(key).read(), content)

        # test progress
        stats = {'previous': -1}

        def progress_callback(bytes_consumed, total_bytes):
            self.assertTrue(total_bytes is None)
            self.assertTrue(bytes_consumed > stats['previous'])

            stats['previous'] = bytes_consumed

        self.bucket.put_object(key2, self.make_generator(content, 8192), progress_callback=progress_callback)
        self.assertEqual(self.bucket.get_object(key).read(), content)

    def test_request_error(self):
        bad_endpoint = random_string(8) + '.' + random_string(16) + '.com'
        bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), bad_endpoint, OSS_BUCKET)

        try:
            bucket.get_bucket_acl()
        except RequestError as e:
            self.assertEqual(e.status, oss2.exceptions.OSS_REQUEST_ERROR_STATUS)
            self.assertEqual(e.request_id, '')
            self.assertEqual(e.code, '')
            self.assertEqual(e.message, '')

            self.assertTrue(str(e))
            self.assertTrue(e.body)

    def test_timeout(self):
        bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET,
                             connect_timeout=0.001)
        self.assertRaises(RequestError, bucket.get_bucket_acl)

    def test_default_timeout(self):
        oss2.defaults.connect_timeout = 0.001
        bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)
        self.assertRaises(RequestError, bucket.get_bucket_acl)

    def test_get_object_iterator(self):
        key = self.random_key()
        content = random_bytes(1024 * 1024)

        self.bucket.put_object(key, content)
        result = self.bucket.get_object(key)
        content_got = b''

        for chunk in result:
            content_got += chunk

        self.assertEqual(len(content), len(content_got))
        self.assertEqual(content, content_got)

    def test_anonymous(self):
        key = self.random_key()
        content = random_bytes(512)

        # 设置bucket为public-read，并确认可以上传和下载
        self.bucket.put_bucket_acl('public-read-write')
        time.sleep(2)

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
        time.sleep(1)

        self.assertRaises(oss2.exceptions.AccessDenied, b.put_object, key, content)
        self.assertRaises(oss2.exceptions.AccessDenied, b.get_object, key)

    def test_range_get(self):
        key = self.random_key()
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
            key = self.random_key()
            object_list.append(key)

            self.bucket.put_object(key, random_string(64))

        result = self.bucket.batch_delete_objects(object_list)
        self.assertEqual(sorted(object_list), sorted(result.deleted_keys))

        for object in object_list:
            self.assertTrue(not self.bucket.object_exists(object))

    def test_batch_delete_objects_empty(self):
        try:
            self.bucket.batch_delete_objects([])
        except ClientError as e:
            self.assertEqual(e.status, oss2.exceptions.OSS_CLIENT_ERROR_STATUS)
            self.assertEqual(e.request_id, '')
            self.assertEqual(e.code, '')
            self.assertEqual(e.message, '')

            self.assertTrue(e.body)
            self.assertTrue(str(e))

    def test_append_object(self):
        key = self.random_key()
        content1 = random_bytes(512)
        content2 = random_bytes(128)

        result = self.bucket.append_object(key, 0, content1, init_crc=0)
        self.assertEqual(result.next_position, len(content1))
        self.assertTrue(result.crc is not None)

        try:
            self.bucket.append_object(key, 0, content2)
        except PositionNotEqualToLength as e:
            self.assertEqual(e.next_position, len(content1))
        else:
            self.assertTrue(False)
        
        result = self.bucket.append_object(key, len(content1), content2, init_crc=result.crc)
        self.assertEqual(result.next_position, len(content1) + len(content2))
        self.assertTrue(result.crc is not None)

        self.bucket.delete_object(key)

    def test_private_download_url(self):
        for key in [self.random_key(), self.random_key(u'中文文件名')]:
            content = random_bytes(42)

            self.bucket.put_object(key, content)
            url = self.bucket.sign_url('GET', key, 60)

            resp = requests.get(url)
            self.assertEqual(content, resp.content)

    def test_copy_object(self):
        source_key = self.random_key()
        target_key = self.random_key()
        content = random_bytes(36)

        self.bucket.put_object(source_key, content)
        self.bucket.copy_object(self.bucket.bucket_name, source_key, target_key)

        result = self.bucket.get_object(target_key)
        self.assertEqual(content, result.read())

    def test_copy_object_source_with_escape(self):
        source_key = '阿里云/加油/:?;@&=+$, /<>{}[]|/'
        target_key = self.random_key()
        content = random_bytes(36)

        self.bucket.put_object(source_key, content)
        self.bucket.copy_object(self.bucket.bucket_name, source_key, target_key)

        result = self.bucket.get_object(target_key)
        self.assertEqual(content, result.read())

    def test_update_object_meta(self):
        key = self.random_key('.txt')
        content = random_bytes(36)

        self.bucket.put_object(key, content)

        # 更改Content-Type，增加用户自定义元数据
        self.bucket.update_object_meta(key, {'Content-Type': 'whatever',
                                                     'x-oss-meta-category': 'novel'})

        result = self.bucket.head_object(key)
        self.assertEqual(result.headers['content-type'], 'whatever')
        self.assertEqual(result.headers['x-oss-meta-category'], 'novel')

    def test_object_acl(self):
        key = self.random_key()
        content = random_bytes(32)

        self.bucket.put_object(key, content)
        self.assertEqual(self.bucket.get_object_acl(key).acl, oss2.OBJECT_ACL_DEFAULT)

        for permission in (oss2.OBJECT_ACL_PRIVATE, oss2.OBJECT_ACL_PUBLIC_READ, oss2.OBJECT_ACL_PUBLIC_READ_WRITE,
                           oss2.OBJECT_ACL_DEFAULT):
            self.bucket.put_object_acl(key, permission)
            self.assertEqual(self.bucket.get_object_acl(key).acl, permission)

        self.bucket.delete_object(key)

    def test_object_exists(self):
        key = self.random_key()
        
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        self.assertRaises(NoSuchBucket, bucket.object_exists, key)

        self.assertTrue(not self.bucket.object_exists(key))

        self.bucket.put_object(key, "hello world")
        self.assertTrue(self.bucket.object_exists(key))

    def test_user_meta(self):
        key = self.random_key()

        self.bucket.put_object(key, 'hello', headers={'x-oss-meta-key1': 'value1',
                                                      'X-Oss-Meta-Key2': 'value2'})

        headers = self.bucket.get_object(key).headers
        self.assertEqual(headers['x-oss-meta-key1'], 'value1')
        self.assertEqual(headers['x-oss-meta-key2'], 'value2')
        
    def test_get_object_meta(self):
        key = self.random_key()
        content = 'hello'
        
        # bucket no exist
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        
        self.assertRaises(NoSuchBucket, bucket.get_object_meta, key)
        
        # object no exist
        self.assertRaises(NoSuchKey, self.bucket.get_object_meta, key)

        self.bucket.put_object(key, content)
        
        # get meta normal
        result = self.bucket.get_object_meta(key)

        self.assertTrue(result.last_modified > 1472128796)
        self.assertEqual(result.content_length, len(content))
        self.assertEqual(result.etag, '5D41402ABC4B2A76B9719D911017C592')

    def test_progress(self):
        stats = {'previous': -1}

        def progress_callback(bytes_consumed, total_bytes):
            self.assertTrue(bytes_consumed <= total_bytes)
            self.assertTrue(bytes_consumed > stats['previous'])

            stats['previous'] = bytes_consumed

        key = self.random_key()
        content = random_bytes(2 * 1024 * 1024)

        # 上传内存中的内容
        stats = {'previous': -1}
        self.bucket.put_object(key, content, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 追加内容
        stats = {'previous': -1}
        self.bucket.append_object(self.random_key(), 0, content, progress_callback=progress_callback)
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
        key = self.random_key()
        content = random_bytes(16)

        self.assertRaises(NotFound, self.bucket.get_object, key)
        self.assertRaises(NoSuchKey, self.bucket.get_object, key)

        self.bucket.put_object(key, content)

        self.assertRaises(Conflict, self.bucket.append_object, key, len(content), b'more content')
        self.assertRaises(ObjectNotAppendable, self.bucket.append_object, key, len(content), b'more content')

    def test_gzip_get(self):
        """OSS supports HTTP Compression, see https://en.wikipedia.org/wiki/HTTP_compression for details.
        """
        key = self.random_key('.txt')       # ensure our content-type is text/plain, which could be compressed
        content = random_bytes(1024 * 1024) # ensure our content-length is larger than 1024 to trigger compression

        self.bucket.put_object(key, content)

        result = self.bucket.get_object(key, headers={'Accept-Encoding': 'gzip'})
        self.assertEqual(result.read(), content)
        self.assertTrue(result.content_length is None)
        self.assertEqual(result.headers['Content-Encoding'], 'gzip')

        # test progress
        stats = {'previous': -1}

        def progress_callback(bytes_consumed, total_bytes):
            self.assertTrue(total_bytes is None)
            self.assertTrue(bytes_consumed > stats['previous'])
            stats['previous'] = bytes_consumed

        content_got = b''
        result = self.bucket.get_object(key, headers={'Accept-Encoding': 'gzip'}, progress_callback=progress_callback)
        content_got = result.read()

        self.assertEqual(len(content), len(content_got))
        self.assertEqual(content, content_got)

    def test_invalid_object_name(self):
        key = '/invalid-object-name'
        content = random_bytes(16)

        self.assertRaises(oss2.exceptions.InvalidObjectName, self.bucket.put_object, key, content)

    def test_disable_crc(self): 
        key = self.random_key('.txt')
        content = random_bytes(1024 * 100)
        
        bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET, enable_crc=False)
        
        # put
        put_result = bucket.put_object(key, content)
        self.assertFalse(hasattr(put_result, 'get_crc'))
        self.assertTrue(put_result.crc is not None)
        
        # get 
        get_result = bucket.get_object(key)
        self.assertEqual(get_result.read(), content)
        self.assertTrue(get_result.client_crc is None)
        self.assertTrue(get_result.server_crc)
        
        bucket.delete_object(key)
        
        # append
        append_result = bucket.append_object(key, 0, content)
        self.assertFalse(hasattr(append_result, 'get_crc'))
        self.assertTrue(append_result.crc is not None)
        
        append_result = bucket.append_object(key, len(content), content)
        self.assertFalse(hasattr(append_result, 'get_crc'))
        self.assertTrue(append_result.crc is not None)
        
        bucket.delete_object(key)
        
        # multipart
        upload_id = bucket.init_multipart_upload(key).upload_id

        parts = []
        result = bucket.upload_part(key, upload_id, 1, content)
        parts.append(oss2.models.PartInfo(1, result.etag))
        result = bucket.upload_part(key, upload_id, 2, content)
        parts.append(oss2.models.PartInfo(2, result.etag))

        bucket.complete_multipart_upload(key, upload_id, parts)

    def test_invalid_crc(self):
        key = self.random_key()
        content = random_bytes(512)

        try:
            self.bucket.append_object(key, 0, content, init_crc=1)
        except oss2.exceptions.InconsistentError as e:
            self.assertEqual(e.status, -3)
            self.assertTrue(e.body.startswith('InconsistentError: the crc of'))
        else:
            self.assertTrue(False)

    def test_put_symlink(self):
        key  = self.random_key()
        symlink = self.random_key()
        content = 'hello'
        
        self.bucket.put_object(key, content)
        
        # put symlink normal
        self.bucket.put_symlink(key, symlink)
        
        head_result = self.bucket.head_object(symlink)
        self.assertEqual(head_result.content_length, len(content))
        self.assertEqual(head_result.etag, '5D41402ABC4B2A76B9719D911017C592')

        self.bucket.put_object(key, content)
        
        # put symlink with meta
        self.bucket.put_symlink(key, symlink, headers={'x-oss-meta-key1': 'value1',
                                                              'X-Oss-Meta-Key2': 'value2'})
        head_result = self.bucket.head_object(symlink)
        self.assertEqual(head_result.content_length, len(content))
        self.assertEqual(head_result.etag, '5D41402ABC4B2A76B9719D911017C592')
        self.assertEqual(head_result.headers['x-oss-meta-key1'], 'value1')
        self.assertEqual(head_result.headers['x-oss-meta-key2'], 'value2')

    def test_get_symlink(self):
        key = self.random_key()
        symlink = self.random_key()
        content = 'hello'
        
        # bucket no exist
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        
        self.assertRaises(NoSuchBucket, bucket.get_symlink, symlink)
        
        # object no exist
        self.assertRaises(NoSuchKey, self.bucket.get_symlink, symlink)
        
        self.bucket.put_object(key, content)
        self.bucket.put_symlink(key, symlink)
        
        # get symlink normal
        result = self.bucket.get_symlink(symlink)
        self.assertEqual(result.target_key, key)


if __name__ == '__main__':
    unittest.main()
