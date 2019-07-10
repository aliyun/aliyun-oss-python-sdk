# -*- coding: utf-8 -*-

import requests
import filecmp
import calendar
import json
import base64

from oss2.exceptions import (ClientError, RequestError, NoSuchBucket, OpenApiServerError,
        NotFound, NoSuchKey, Conflict, PositionNotEqualToLength, ObjectNotAppendable)

from oss2.compat import is_py2, is_py33
from oss2.models import Tagging, TaggingRule
from oss2.headers import OSS_OBJECT_TAGGING, OSS_OBJECT_TAGGING_COPY_DIRECTIVE
from oss2.compat import urlunquote, urlquote

from .common import *


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

    def test_rsa_crypto_object(self):
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

        self.rsa_crypto_bucket.put_object(key, content)

        get_result = self.rsa_crypto_bucket.get_object(key)
        self.assertEqual(get_result.read(), content)
        assert_result(get_result)
        self.assertTrue(get_result.client_crc is not None)
        self.assertTrue(get_result.server_crc is not None)
        self.assertTrue(get_result.client_crc == get_result.server_crc)

    def test_kms_crypto_object(self):
        if is_py33:
            return

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

        self.kms_crypto_bucket.put_object(key, content, headers={'content-md5': oss2.utils.md5_string(content),
                                                                        'content-length': str(len(content))})

        get_result = self.kms_crypto_bucket.get_object(key)
        self.assertEqual(get_result.read(), content)
        assert_result(get_result)
        self.assertTrue(get_result.client_crc is not None)
        self.assertTrue(get_result.server_crc is not None)
        self.assertTrue(get_result.client_crc == get_result.server_crc)

    def test_restore_object(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-restore-object"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)

        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE, oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_ARCHIVE))

        service = oss2.Service(auth, OSS_ENDPOINT)
        wait_meta_sync()
        self.retry_assert(lambda: bucket.bucket_name in (b.name for b in
                                                         service.list_buckets(prefix=bucket.bucket_name).buckets))

        key = 'a.txt'
        bucket.put_object(key, 'content')
        self.assertEqual(202, bucket.restore_object(key).status)
        bucket.delete_object(key)
        bucket.delete_bucket()

    def test_last_modified_time(self):
        key = self.random_key()
        content = random_bytes(10)

        self.bucket.put_object(key, content)

        res = self.bucket.get_object(key)
        res.read()

        time_string = res.headers['Last-Modified']
        self.assertEqual(oss2.utils.http_to_unixtime(time_string), res.last_modified)
        self.assertEqual(oss2.utils.to_unixtime(time_string, '%a, %d %b %Y %H:%M:%S GMT'), res.last_modified)

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
        get_result = self.bucket.get_object_to_file(key, filename2)

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

    def test_object_empty(self):
        key = self.random_key()
        content = b''

        self.bucket.put_object(key, content)
        res = self.bucket.get_object(key)

        self.assertEqual(res.read(), b'')

    def test_file_empty(self):
        input_filename = random_string(12)
        output_filename = random_string(12)

        key = self.random_key()
        content = b''

        with open(input_filename, 'wb') as f:
            f.write(content)

        self.bucket.put_object_from_file(key, input_filename)
        self.bucket.get_object_to_file(key, output_filename)

        self.assertTrue(filecmp.cmp(input_filename, output_filename))

        os.remove(input_filename)
        os.remove(output_filename)

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
        oss2.defaults.connect_timeout = 60

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

        result = self.bucket.get_object(key)
        content_got = b''

        for chunk in result:
            content_got += chunk

        self.assertEqual(len(content), len(content_got))
        self.assertEqual(content, content_got)

    def test_query_parameter(self):
        key = self.random_key()
        content = random_bytes(1024 * 1024)
        self.bucket.put_object(key, content, headers={'Content-Type': 'plain/text'})
        query_params = {'response-content-type': 'image/jpeg'}
        result = self.bucket.get_object(key, params=query_params)
        self.assertEqual(result.headers['content-type'], 'image/jpeg')

    def test_anonymous(self):
        key = self.random_key()
        content = random_bytes(512)

        # 设置bucket为public-read，并确认可以上传和下载
        self.bucket.put_bucket_acl('public-read-write')
        wait_meta_sync()

        b = oss2.Bucket(oss2.AnonymousAuth(), OSS_ENDPOINT, OSS_BUCKET)
        b.put_object(key, content)
        result = b.get_object(key)
        self.assertEqual(result.read(), content)

        # 测试sign_url
        url = b.sign_url('GET', key, 100, params={'para1':'test'})
        resp = requests.get(url)
        self.assertEqual(content, resp.content)

        # 设置bucket为private，并确认上传和下载都会失败
        self.bucket.put_bucket_acl('private')
        wait_meta_sync()

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
        keys = []
        for i in range(0, 5):
            keys.append(result.delete_versions[i].key)
        self.assertEqual(sorted(object_list), sorted(keys))
        self.assertEqual(5, len(result.deleted_keys))
        self.assertEqual(5, len(result.delete_versions))

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
            
    def test_sign_url_with_callback(self):
        key = self.random_key()
        
        def encode_callback(cb_dict):
            cb_str = json.dumps(callback_params).strip()
            return oss2.compat.to_string(base64.b64encode(oss2.compat.to_bytes(cb_str))) 
        
        # callback
        callback_params = {}
        callback_params['callbackUrl'] = 'http://cbsrv.oss.demo.com'
        callback_params['callbackBody'] = 'bucket=${bucket}&object=${object}' 
        encoded_callback = encode_callback(callback_params)
        
        # callback vars
        callback_var_params = {'x:my_var1': 'my_val1', 'x:my_var2': 'my_val2'}
        encoded_callback_var = encode_callback(callback_var_params)
        
        # put with callback
        params = {'callback': encoded_callback, 'callback-var': encoded_callback_var}
        url = self.bucket.sign_url('PUT', key, 60, params=params)
        resp = requests.put(url)
        self.assertEqual(resp.status_code, 203)

    def test_private_download_url_with_extra_query(self):
        if os.getenv('OSS_TEST_AUTH_VERSION') != oss2.AUTH_VERSION_2:
            return
        key = self.random_key()
        content = random_bytes(42)

        self.bucket.put_object(key, content)
        url = self.bucket.sign_url('GET', key, 60, params={'extra-query': '1'})

        resp = requests.get(url)
        self.assertEqual(content, resp.content)

        resp = requests.get(url + '&another-query=1')
        self.assertEqual(resp.status_code, 403)

        e = oss2.exceptions.make_exception(oss2.http.Response(resp))
        self.assertEqual(e.status, 403)
        self.assertEqual(e.code, 'SignatureDoesNotMatch')

    def test_put_object_with_sign_url(self):
        key = self.random_key(".jpg")
        with open("tests/example.jpg", 'rb') as fr:
            data = fr.read()

        url = self.bucket.sign_url('PUT', key, 3600)
        result = self.bucket.put_object_with_url(url, data)
        self.assertEqual(result.status, 200)
        result = self.bucket.head_object(key)
        self.assertEqual(result.content_type, "application/octet-stream")

        headers = {'Content-Type': "image/jpeg"}
        self.assertRaises(oss2.exceptions.SignatureDoesNotMatch, self.bucket.put_object_with_url, url, data, headers=headers)

        url = self.bucket.sign_url('PUT', key, 3600, headers=headers)
        self.assertRaises(oss2.exceptions.SignatureDoesNotMatch, self.bucket.put_object_with_url, url, data)
        result = self.bucket.put_object_with_url(url, data, headers)
        self.assertEqual(result.status, 200)
        result = self.bucket.head_object(key)
        self.assertEqual(result.content_type, "image/jpeg")

    def test_get_object_with_sign_url(self):
        key = self.random_key('.txt')
        content = random_bytes(100)

        result = self.bucket.put_object(key, content)
        self.assertEqual(result.status, 200)

        # normal get with signed url
        url = self.bucket.sign_url("GET", key, 3600)
        result = self.bucket.get_object_with_url(url)
        self.assertEqual(result.status, 200)

        # signed without range, and get with range
        result = self.bucket.get_object_with_url(url, byte_range=(50, 99))
        self.assertEqual(result.status, 206)
        range_content = result.read()
        self.assertEqual(content[50:], range_content)

        # signed with range, and get without range
        headers = {'Range': 'bytes=50-99'}
        url = self.bucket.sign_url("GET", key, 3600, headers=headers)
        result = self.bucket.get_object_with_url(url)
        self.assertEqual(result.status, 200)
        range_content = result.read()
        self.assertEqual(content, range_content)

    def test_put_object_from_file_with_sign_url(self):
        key = self.random_key()
        file_name = self.random_filename()
        content = random_bytes(100)

        with open(file_name, 'wb') as fw:
            fw.write(content)

        headers = {'Content-Type': "text/plain"}
        url = self.bucket.sign_url('PUT', key, 3600, headers)
        result = self.bucket.put_object_with_url_from_file(url, file_name, headers=headers)
        self.assertEqual(result.status, 200)
        result = self.bucket.head_object(key)
        self.assertEqual(result.content_type, "text/plain")

    def test_get_object_to_file_with_sign_url(self):
        key = self.random_key('txt')
        file_name = self.random_filename()
        content = random_bytes(100)

        result = self.bucket.put_object(key, content)
        self.assertEqual(result.status, 200)

        url = self.bucket.sign_url("GET", key, 3600)
        result = self.bucket.get_object_with_url_to_file(url, file_name)
        self.assertEqual(result.status, 200)

    def test_modified_since(self):
        key = self.random_key()
        content = random_bytes(16)

        self.bucket.put_object(key, content)
        self.assertRaises(oss2.exceptions.NotModified,
                          self.bucket.get_object,
                          key,
                          headers={
                              'if-modified-since': oss2.utils.http_date(int(time.time()) + 60),
                          },
                          byte_range=(0, 7))

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
        bucket_name = OSS_BUCKET + "-test-object_exists"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
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
        bucket_name = OSS_BUCKET + "-test-get-object-meta"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        
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

    def test_crypto_progress(self):
        stats = {'previous': -1}

        def progress_callback(bytes_consumed, total_bytes):
            self.assertTrue(bytes_consumed <= total_bytes)
            self.assertTrue(bytes_consumed > stats['previous'])

            stats['previous'] = bytes_consumed

        key = self.random_key()
        content = random_bytes(2 * 1024 * 1024)

        # 上传内存中的内容
        stats = {'previous': -1}
        self.rsa_crypto_bucket.put_object(key, content, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 下载到文件
        stats = {'previous': -1}
        filename = random_string(12) + '.txt'
        self.rsa_crypto_bucket.get_object_to_file(key, filename, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 上传本地文件
        stats = {'previous': -1}
        self.rsa_crypto_bucket.put_object_from_file(key, filename, progress_callback=progress_callback)
        self.assertEqual(stats['previous'], len(content))

        # 下载到本地，采用iterator语法
        stats = {'previous': -1}
        result = self.rsa_crypto_bucket.get_object(key, progress_callback=progress_callback)
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
        #"""OSS supports HTTP Compression, see https://en.wikipedia.org/wiki/HTTP_compression for details.
        #"""
        key = self.random_key('.txt')       # ensure our content-type is text/plain, which could be compressed
        content = random_bytes(1024 * 1024) # ensure our content-length is larger than 1024 to trigger compression

        self.bucket.put_object(key, content)

        result = self.bucket.get_object(key, headers={'Accept-Encoding': 'gzip'})
        content_read = result.read()
        self.assertEqual(len(content_read), len(content))
        self.assertEqual(content_read, content)
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
            self.assertTrue(e.body.startswith('InconsistentError'))
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
        bucket_name = OSS_BUCKET + "-test-get-symlink"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        
        self.assertRaises(NoSuchBucket, bucket.get_symlink, symlink)
        
        # object no exist
        self.assertRaises(NoSuchKey, self.bucket.get_symlink, symlink)
        
        self.bucket.put_object(key, content)
        self.bucket.put_symlink(key, symlink)
        
        # get symlink normal
        result = self.bucket.get_symlink(symlink)
        self.assertEqual(result.target_key, key)

    def test_process_object(self):
        key = self.random_key(".jpg")
        result = self.bucket.put_object_from_file(key, "tests/example.jpg")
        self.assertEqual(result.status, 200)

        dest_key = self.random_key(".jpg")
        process = "image/resize,w_100|sys/saveas,o_{0},b_{1}".format(
            oss2.compat.to_string(base64.urlsafe_b64encode(oss2.compat.to_bytes(dest_key))),
            oss2.compat.to_string(base64.urlsafe_b64encode(oss2.compat.to_bytes(self.bucket.bucket_name))))
        result = self.bucket.process_object(key, process)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.bucket, self.bucket.bucket_name)
        self.assertEqual(result.object, dest_key)
        result = self.bucket.object_exists(dest_key)
        self.assertEqual(result, True)


        # If bucket-name not specified, it is saved to the current bucket by default.
        dest_key = self.random_key(".jpg")
        process = "image/resize,w_100|sys/saveas,o_{0}".format(
            oss2.compat.to_string(base64.urlsafe_b64encode(oss2.compat.to_bytes(dest_key))))
        result = self.bucket.process_object(key, process)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.bucket, "")
        self.assertEqual(result.object, dest_key)
        result = self.bucket.object_exists(dest_key)
        self.assertEqual(result, True)
    
    def test_object_tagging_client_error(self):

        rule = TaggingRule()
        self.assertRaises(oss2.exceptions.ClientError, rule.add, 129*'a', 'test')
        self.assertRaises(oss2.exceptions.ClientError, rule.add, 'test', 257*'a')
        self.assertRaises(oss2.exceptions.ClientError, rule.add, None, 'test')
        self.assertRaises(oss2.exceptions.ClientError, rule.add, '', 'test')
        self.assertRaises(KeyError, rule.delete, 'not_exist')

    def test_object_tagging_wrong_key(self):
       
        tagging = Tagging()
        tagging.tag_set.tagging_rule[129*'a'] = 'test'
        
        key = self.random_key('.dat')
        result = self.bucket.put_object(key, "test")

        try:
            result = self.bucket.put_object_tagging(key, tagging)
            self.assertFalse(True, 'should get exception')
        except oss2.exceptions.OssError:
            pass

        tagging.tag_set.delete(129*'a')

        self.assertTrue( 129*'a' not in tagging.tag_set.tagging_rule )

        tagging.tag_set.tagging_rule['%@abc'] = 'abc'

        try:
            result = self.bucket.put_object_tagging(key, tagging)
            self.assertFalse(True, 'should get exception')
        except oss2.exceptions.OssError:
            pass

        tagging.tag_set.delete('%@abc')

        self.assertTrue( '%@abc' not in tagging.tag_set.tagging_rule )

        tagging.tag_set.tagging_rule[''] = 'abc'

        try:
            result = self.bucket.put_object_tagging(key, tagging)
            self.assertFalse(True, 'should get exception')
        except oss2.exceptions.OssError:
            pass


    def test_object_tagging_wrong_value(self):
       
        tagging = Tagging()

        tagging.tag_set.tagging_rule['test'] = 257*'a'

        key = self.random_key('.dat')

        result = self.bucket.put_object(key, "test")

        try:
            result = self.bucket.put_object_tagging(key, tagging)
            self.assertFalse(True, 'should get exception')
        except oss2.exceptions.OssError:
            pass

        tagging.tag_set.tagging_rule['test']= '%abc'

        try:
            result = self.bucket.put_object_tagging(key, tagging)
            self.assertFalse(True, 'should get exception')
        except oss2.exceptions.OssError:
            pass

        tagging.tag_set.tagging_rule['test']= ''

        try:
            result = self.bucket.put_object_tagging(key, tagging)
        except oss2.exceptions.OssError:
            self.assertFalse(True, 'should get exception')

    def test_object_tagging_wrong_rule_num(self):
        
        key = self.random_key('.dat')
        result = self.bucket.put_object(key, "test")

        tagging = Tagging(None)
        for i in range(0,12):
            key='test_'+str(i)
            value='test_'+str(i)
            tagging.tag_set.add(key, value)

        try:
            result = self.bucket.put_object_tagging(key, tagging)
            self.assertFalse(True, 'should get exception')
        except oss2.exceptions.OssError:
            pass

    def test_object_tagging(self):

        key = self.random_key('.dat')
        result = self.bucket.put_object(key, "test")

        try:
            result=self.bucket.get_object_tagging(key)
            self.assertEqual(0, result.tag_set.len())
        except oss2.exceptions.OssError:
            self.assertFalse(True, "should get exception")

        rule = TaggingRule()
        key1=128*'a'
        value1=256*'a'
        rule.add(key1, value1)

        key2='+-.:'
        value2='_/'
        rule.add(key2, value2)

        tagging = Tagging(rule) 
        result = self.bucket.put_object_tagging(key, tagging)
        self.assertTrue(200, result.status)

        result = self.bucket.get_object_tagging(key)

        self.assertEqual(2, result.tag_set.len())
        self.assertEqual(256*'a', result.tag_set.tagging_rule[128*'a'])
        self.assertEqual('_/', result.tag_set.tagging_rule['+-.:'])

    def test_put_object_with_tagging(self):
    
        key = self.random_key('.dat')
        headers = dict()
        headers[OSS_OBJECT_TAGGING] = "k1=v1&k2=v2&k3=v3"

        result = self.bucket.put_object(key, 'test', headers=headers)
        self.assertEqual(200, result.status)
        
        result = self.bucket.get_object_tagging(key)
        self.assertEqual(3, result.tag_set.len())
        self.assertEqual('v1', result.tag_set.tagging_rule['k1'])
        self.assertEqual('v2', result.tag_set.tagging_rule['k2'])
        self.assertEqual('v3', result.tag_set.tagging_rule['k3'])

        result = self.bucket.delete_object_tagging(key)

        self.assertEqual(204, result.status)

        result = self.bucket.get_object_tagging(key)
        self.assertEqual(0, result.tag_set.len())

    def test_copy_object_with_tagging(self):
    
        #key = self.random_key('.dat')
        key = 'aaaaaaaaaaaaaa' 
        headers = dict()
        headers[OSS_OBJECT_TAGGING] = "k1=v1&k2=v2&k3=v3"

        result = self.bucket.put_object(key, 'test', headers=headers)
        self.assertEqual(200, result.status)

        result = self.bucket.get_object_tagging(key)
        self.assertEqual(3, result.tag_set.len())
        self.assertEqual('v1', result.tag_set.tagging_rule['k1'])
        self.assertEqual('v2', result.tag_set.tagging_rule['k2'])
        self.assertEqual('v3', result.tag_set.tagging_rule['k3'])

        headers=dict()
        headers[OSS_OBJECT_TAGGING_COPY_DIRECTIVE] = 'COPY'
        result = self.bucket.copy_object(self.bucket.bucket_name, key, key+'_test', headers=headers)

        result = self.bucket.get_object_tagging(key+'_test')
        self.assertEqual(3, result.tag_set.len())
        self.assertEqual('v1', result.tag_set.tagging_rule['k1'])
        self.assertEqual('v2', result.tag_set.tagging_rule['k2'])
        self.assertEqual('v3', result.tag_set.tagging_rule['k3'])

        tag_key1 = u' +/ '
        tag_value1 = u'中文'
        tag_str = urlquote(tag_key1.encode('UTF-8')) + '=' + urlquote(tag_value1.encode('UTF-8'))

        tag_key2 = u'中文'
        tag_value2 = u'test++/'
        tag_str += '&' + urlquote(tag_key2.encode('UTF-8')) + '=' + urlquote(tag_value2.encode('UTF-8'))

        headers[OSS_OBJECT_TAGGING] = tag_str
        headers[OSS_OBJECT_TAGGING_COPY_DIRECTIVE] = 'REPLACE'
        result = self.bucket.copy_object(self.bucket.bucket_name, key, key+'_test', headers=headers)

        result = self.bucket.get_object_tagging(key+'_test')
        self.assertEqual(2, result.tag_set.len())
        self.assertEqual('中文', result.tag_set.tagging_rule[' +/ '])
        self.assertEqual('test++/', result.tag_set.tagging_rule['中文'])

    def test_append_object_with_tagging(self):
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

        rule = TaggingRule()
        self.assertEqual('', rule.to_query_string())

        rule.add('key1', 'value1')
        self.assertEqual(rule.to_query_string(), 'key1=value1')

        rule.add(128*'a', 256*'b')
        rule.add('+-/', ':+:')
        self.assertEqual('key1=value1' in rule.to_query_string(), True)
        self.assertEqual((128*'a' + '=' + 256*'b') in rule.to_query_string(), True)
        self.assertEqual('%2B-/=%3A%2B%3A' in rule.to_query_string(), True)

        headers = dict()
        headers[OSS_OBJECT_TAGGING] = rule.to_query_string()

        result = self.bucket.append_object(key, 0, content1, init_crc=0, headers=headers)
        self.assertEqual(result.next_position, len(content1))
        self.assertTrue(result.crc is not None)

        result = self.bucket.append_object(key, len(content1), content2, init_crc=result.crc)
        self.assertEqual(result.next_position, len(content1) + len(content2))
        self.assertTrue(result.crc is not None)

        result = self.bucket.get_object_tagging(key)
        self.assertEqual(3, result.tag_set.len())

        tagging_rule = result.tag_set.tagging_rule
        self.assertEqual('value1', tagging_rule['key1'])
        self.assertEqual(256*'b', tagging_rule[128*'a'])
        self.assertEqual(':+:', tagging_rule['+-/'])

    def test_append_object_with_tagging_wrong_num(self):
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
        
        # append object with wrong tagging kv num, but not in 
        # first call, it will be ignored
        rule = TaggingRule()
        self.assertEqual('', rule.to_query_string())

        for i in range(0, 15):
            tag_key = 'key' + str(i)
            tag_value = 'value' + str(i)
            rule.add(tag_key, tag_value)

        headers = dict()
        headers[OSS_OBJECT_TAGGING] = rule.to_query_string()


        result = self.bucket.append_object(key, 0, content1, init_crc=0)
        self.assertEqual(result.next_position, len(content1))
        self.assertTrue(result.crc is not None)

        result = self.bucket.append_object(key, len(content1), content2, init_crc=result.crc, headers=headers)

        result_tagging = self.bucket.get_object_tagging(key)
        self.assertEqual(0, result_tagging.tag_set.len())
        
        rule.delete('key1')
        rule.delete('key2')
        rule.delete('key3')
        rule.delete('key4')
        rule.delete('key5')
        rule.delete('key6')

        self.assertEqual(9, rule.len())

        headers[OSS_OBJECT_TAGGING] = rule.to_query_string()

        try:
            result = self.bucket.append_object(key, len(content1)+len(content2), 
                    content2, init_crc=result.crc, headers=headers)
        except oss2.exceptions.OssError:
            self.assertFalse(True, 'should not get exception')

        result = self.bucket.get_object_tagging(key)
        self.assertEqual(0, result.tag_set.len())

        self.bucket.delete_object(key)

        wait_meta_sync()

        # append object with wrong tagging kv num in first call,
        # it will be fail
        rule = TaggingRule()
        self.assertEqual('', rule.to_query_string())

        for i in range(0, 15):
            tag_key = 'key' + str(i)
            tag_value = 'value' + str(i)
            rule.add(tag_key, tag_value)

        headers = dict()
        headers[OSS_OBJECT_TAGGING] = rule.to_query_string()

        try:
            self.bucket.append_object(key, 0, content1, init_crc=0, headers=headers)
            self.assertFalse(True, 'should get exception')
        except oss2.exceptions.OssError:
            pass

    def test_put_symlink_with_tagging(self):
        key  = self.random_key()
        symlink = self.random_key()
        content = 'hello'
        
        self.bucket.put_object(key, content)
        
        rule = TaggingRule()
        self.assertEqual('', rule.to_query_string())

        rule.add('key1', 'value1')
        self.assertTrue(rule.to_query_string() != '')

        rule.add(128*'a', 256*'b')
        rule.add('+-/', ':+:')

        headers = dict()
        headers[OSS_OBJECT_TAGGING] = rule.to_query_string()

        # put symlink normal
        self.bucket.put_symlink(key, symlink, headers=headers)

        result = self.bucket.get_object_tagging(symlink)
        self.assertEqual(3, result.tag_set.len())

        tagging_rule = result.tag_set.tagging_rule
        self.assertEqual('value1', tagging_rule['key1'])
        self.assertEqual(256*'b', tagging_rule[128*'a'])
        self.assertEqual(':+:', tagging_rule['+-/'])

        result = self.bucket.delete_object(symlink)
        self.assertEqual(204, int(result.status))

    def test_put_symlink_with_tagging_with_wrong_num(self):
        key  = self.random_key()
        symlink = self.random_key()
        content = 'hello'
        self.bucket.put_object(key, content)
        
        rule = TaggingRule()
        self.assertEqual('', rule.to_query_string())

        for i in range(0, 15):
            tag_key = 'key' + str(i)
            tag_value = 'value' + str(i)
            rule.add(tag_key, tag_value)

        headers = dict()
        headers[OSS_OBJECT_TAGGING] = rule.to_query_string()
        
        try:
            self.bucket.put_symlink(key, symlink, headers=headers)
            self.assertFalse(True, 'should get exception')
        except:
            pass
       
        rule.delete('key1')
        rule.delete('key2')
        rule.delete('key3')
        rule.delete('key4')
        rule.delete('key5')
        rule.delete('key6')

        headers[OSS_OBJECT_TAGGING] = rule.to_query_string()

        try:
            result = self.bucket.put_symlink(key, symlink, headers=headers)
        except:
            self.assertFalse(True, 'should not get exception')

        head_result = self.bucket.head_object(symlink)
        self.assertEqual(head_result.content_length, len(content))
        self.assertEqual(head_result.etag, '5D41402ABC4B2A76B9719D911017C592')

        # put symlink with meta
        self.bucket.put_symlink(key, symlink, headers={'x-oss-meta-key1': 'value1',
                'x-oss-meta-KEY2': 'value2'})

        head_result = self.bucket.head_object(symlink)
        self.assertEqual(head_result.content_length, len(content))
        self.assertEqual(head_result.etag, '5D41402ABC4B2A76B9719D911017C592')
        self.assertEqual(head_result.headers['x-oss-meta-key1'], 'value1')
        self.assertEqual(head_result.headers['x-oss-meta-key2'], 'value2')

    
class TestSign(TestObject):
    """
        这个类主要是用来增加测试覆盖率，当环境变量为oss2.AUTH_VERSION_2，则重新设置为oss2.AUTH_VERSION_1再运行TestObject，反之亦然
    """
    def __init__(self, *args, **kwargs):
        super(TestSign, self).__init__(*args, **kwargs)

    def setUp(self):
        if os.getenv('OSS_TEST_AUTH_VERSION') == oss2.AUTH_VERSION_2:
            os.environ['OSS_TEST_AUTH_VERSION'] = oss2.AUTH_VERSION_1
        else:
            os.environ['OSS_TEST_AUTH_VERSION'] = oss2.AUTH_VERSION_2
        super(TestSign, self).setUp()

    def tearDown(self):
        if os.getenv('OSS_TEST_AUTH_VERSION') == oss2.AUTH_VERSION_2:
            os.environ['OSS_TEST_AUTH_VERSION'] = oss2.AUTH_VERSION_1
        else:
            os.environ['OSS_TEST_AUTH_VERSION'] = oss2.AUTH_VERSION_2
        super(TestSign, self).tearDown()


if __name__ == '__main__':
    unittest.main()
