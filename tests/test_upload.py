# -*- coding: utf-8 -*-

import unittest
import oss2
import os
import sys
import time

from .common import *

from mock import patch


class TestUpload(OssTestCase):
    def test_upload_small(self):
        for bucket in [self.bucket, self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = random_string(16)
            content = random_bytes(100)

            pathname = self._prepare_temp_file(content)

            result = oss2.resumable_upload(bucket, key, pathname)
            self.assertTrue(result is not None)
            self.assertTrue(result.etag is not None)
            self.assertTrue(result.request_id is not None)

            result = bucket.get_object(key)
            self.assertEqual(content, result.read())
            self.assertEqual(result.headers['x-oss-object-type'], 'Normal')

            bucket.delete_object(key)

    def test_upload_large(self):
        for bucket in [self.bucket, self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = random_string(16)
            content = random_bytes(5 * 100 * 1024)

            pathname = self._prepare_temp_file(content)

            result = oss2.resumable_upload(bucket, key, pathname, multipart_threshold=200 * 1024, part_size=None)
            self.assertTrue(result is not None)
            self.assertTrue(result.etag is not None)
            self.assertTrue(result.request_id is not None)

            result = bucket.get_object(key)
            self.assertEqual(content, result.read())
            self.assertEqual(result.headers['x-oss-object-type'], 'Multipart')

            bucket.delete_object(key)

    def test_concurrency(self):
        for bucket in [self.bucket, self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            key = random_string(16)
            content = random_bytes(64 * 100 * 1024)

            pathname = self._prepare_temp_file(content)

            oss2.resumable_upload(bucket, key, pathname,
                                  multipart_threshold=200 * 1024,
                                  part_size=100 * 1024,
                                  num_threads=8)
            result = bucket.get_object(key)
            self.assertEqual(content, result.read())
            self.assertEqual(result.headers['x-oss-object-type'], 'Multipart')

    def test_progress(self):
        for bucket in [self.bucket, self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            stats = {'previous': -1, 'ncalled': 0}

            def progress_callback(bytes_consumed, total_bytes):
                self.assertTrue(bytes_consumed <= total_bytes)
                self.assertTrue(bytes_consumed > stats['previous'])

                stats['previous'] = bytes_consumed
                stats['ncalled'] += 1

            key = random_string(16)
            content = random_bytes(5 * 100 * 1024 + 100)

            pathname = self._prepare_temp_file(content)

            part_size = 100 * 1024
            oss2.resumable_upload(bucket, key, pathname,
                                  multipart_threshold=200 * 1024,
                                  part_size=part_size,
                                  progress_callback=progress_callback,
                                  num_threads=1)
            self.assertEqual(stats['previous'], len(content))
            self.assertEqual(stats['ncalled'], oss2.utils.how_many(len(content), part_size) + 1)

            stats = {'previous': -1, 'ncalled': 0}
            oss2.resumable_upload(bucket, key, pathname,
                                  multipart_threshold=len(content) + 100,
                                  progress_callback=progress_callback)
            self.assertEqual(stats['previous'], len(content))

            bucket.delete_object(key)

    def _rebuild_record(self, filename, store, bucket, key, upload_id, part_size=None):
        abspath = os.path.abspath(filename)
        mtime = os.path.getmtime(filename)
        size = os.path.getsize(filename)

        record = {'op_type': 'ResumableUpload', 'upload_id': upload_id, 'file_path': abspath, 'size': size,
                  'mtime': mtime, 'bucket': bucket.bucket_name, 'key': key, 'part_size': part_size}

        store_key = store.make_store_key(bucket.bucket_name, key, abspath)
        store.put(store_key, record)

    def __test_resume(self, content_size, uploaded_parts, expected_unfinished=0):
        for bucket in [self.bucket, self.rsa_crypto_bucket, self.kms_crypto_bucket]:
            part_size = 100 * 1024
            num_parts = (content_size + part_size - 1) // part_size

            key = 'resume-' + random_string(32)
            content = random_bytes(content_size)

            pathname = self._prepare_temp_file(content)
            if isinstance(bucket, oss2.CryptoBucket):
                upload_id = bucket.init_multipart_upload(key, content_size, part_size).upload_id
            else:
                upload_id = bucket.init_multipart_upload(key).upload_id

            for part_number in uploaded_parts:
                start = (part_number - 1) * part_size
                if part_number == num_parts:
                    end = content_size
                else:
                    end = start + part_size

                bucket.upload_part(key, upload_id, part_number, content[start:end])

            self._rebuild_record(pathname, oss2.resumable.make_upload_store(), bucket, key, upload_id, part_size)
            oss2.resumable_upload(bucket, key, pathname, multipart_threshold=0, part_size=100 * 1024)

            result = bucket.get_object(key)
            self.assertEqual(content, result.read())

            self.assertEqual(len(list(oss2.ObjectUploadIterator(self.bucket, key))), expected_unfinished)

            bucket.delete_object(key)

    def test_resume_empty(self):
        self.__test_resume(250 * 1024, [])

    def test_resume_continuous(self):
        self.__test_resume(500 * 1024, [1, 2])

    def test_resume_hole_mid(self):
        self.__test_resume(510 * 1024, [1, 4])

    def test_resume_hole_end(self):
        self.__test_resume(300 * 1024 + 1, [4])

    def __test_interrupt(self, content_size, failed_part_number,
                         expected_unfinished=0,
                         modify_record_func=None, all_buckets=True):
        buckets = [self.bucket]
        if all_buckets:
            buckets = [self.bucket, self.rsa_crypto_bucket, self.kms_crypto_bucket]
        for bucket in buckets:
            orig_upload_part = bucket.upload_part

            def upload_part(self, key, upload_id, part_number, data, progress_callback=None, headers=None):
                if part_number == failed_part_number:
                    raise RuntimeError
                else:
                    return orig_upload_part(key, upload_id, part_number, data, progress_callback, headers)

            key = 'ResumableUpload-' + random_string(32)
            content = random_bytes(content_size)

            pathname = self._prepare_temp_file(content)

            with patch.object(oss2.Bucket, 'upload_part', side_effect=upload_part, autospec=True) as mock_upload_part:
                self.assertRaises(RuntimeError, oss2.resumable_upload, bucket, key, pathname, multipart_threshold=0,
                                  part_size=100 * 1024)

            if modify_record_func:
                modify_record_func(oss2.resumable.make_upload_store(), bucket.bucket_name, key, pathname)

            oss2.resumable_upload(bucket, key, pathname, multipart_threshold=0, part_size=100 * 1024)

            self.assertEqual(len(list(oss2.ObjectUploadIterator(self.bucket, key))), expected_unfinished)

    def test_interrupt_at_start(self):
        self.__test_interrupt(310 * 1024, 1)

    def test_interrupt_at_mid(self):
        self.__test_interrupt(510 * 1024, 3)

    def test_interrupt_at_end(self):
        self.__test_interrupt(500 * 1024 - 1, 5)

    def test_record_invalid_op(self):
        self.__test_interrupt(500 * 1024, 1,
                              modify_record_func=self.__make_corrupt_record('op_type', 'ResumableDownload'),
                              expected_unfinished=1, all_buckets=False)

    def test_record_invalid_upload_id(self):
        self.__test_interrupt(500 * 1024, 1,
                              modify_record_func=self.__make_corrupt_record('upload_id', random.randint(1, 100)),
                              expected_unfinished=1, all_buckets=False)

    def test_record_invalid_file_path(self):
        self.__test_interrupt(500 * 1024, 1,
                              modify_record_func=self.__make_corrupt_record('file_path', random.randint(1, 100)),
                              expected_unfinished=1, all_buckets=False)

    def test_record_invalid_size(self):
        self.__test_interrupt(500 * 1024, 1,
                              modify_record_func=self.__make_corrupt_record('size', 'invalid_size_type'),
                              expected_unfinished=1, all_buckets=False)

    def test_record_invalid_mtime(self):
        self.__test_interrupt(500 * 1024, 1,
                              modify_record_func=self.__make_corrupt_record('mtime', 'invalid_mtime'),
                              expected_unfinished=1, all_buckets=False)

    def test_record_invalid_bucket(self):
        self.__test_interrupt(500 * 1024, 1,
                              modify_record_func=self.__make_corrupt_record('bucket', random.randint(1, 100)),
                              expected_unfinished=1, all_buckets=False)

    def test_record_invalid_key(self):
        self.__test_interrupt(500 * 1024, 1,
                              modify_record_func=self.__make_corrupt_record('key', random.randint(1, 100)),
                              expected_unfinished=1, all_buckets=False)

    def test_record_invalid_part_size(self):
        self.__test_interrupt(500 * 1024, 1,
                              modify_record_func=self.__make_corrupt_record('part_size', 'invalid_part_size'),
                              expected_unfinished=1, all_buckets=False)

    def test_file_changed_mtime(self):
        def change_mtime(store, bucket_name, key, pathname):
            time.sleep(2)
            os.utime(pathname, (time.time(), time.time()))

        self.__test_interrupt(500 * 1024, 3,
                              modify_record_func=change_mtime,
                              expected_unfinished=1)

    def test_file_changed_size(self):
        def change_size(store, bucket_name, key, pathname):
            mtime = os.path.getmtime(pathname)

            with open(pathname, 'w') as f:
                f.write(random_bytes(500 * 1024 - 1))

            os.utime(pathname, (mtime, mtime))

        self.__test_interrupt(500 * 1024, 3,
                              modify_record_func=change_size,
                              expected_unfinished=1)

    def __make_corrupt_record(self, name, value):
        def corrupt_record(store, bucket_name, key, pathname):
            store_key = store.make_store_key(bucket_name, key, pathname)

            record = store.get(store_key)
            record[name] = value
            store.put(store_key, record)

        return corrupt_record

    def test_upload_large_with_tagging(self):

        from oss2.compat import urlquote

        key = random_string(16)
        content = random_bytes(5 * 100 * 1024)

        pathname = self._prepare_temp_file(content)

        headers = dict()
        tagging_header = oss2.headers.OSS_OBJECT_TAGGING

        key1 = 128 * 'a'
        value1 = 256 * 'b'

        key2 = '+-:/'
        value2 = ':+:'

        key3 = '中文'
        value3 = '++中文++'

        tag_str = key1 + '=' + value1
        tag_str += '&' + urlquote(key2) + '=' + urlquote(value2)
        tag_str += '&' + urlquote(key3) + '=' + urlquote(value3)

        headers[tagging_header] = tag_str

        result = oss2.resumable_upload(self.bucket, key, pathname, multipart_threshold=200 * 1024, num_threads=3,
                                       headers=headers)

        self.assertTrue(result is not None)
        self.assertTrue(result.etag is not None)
        self.assertTrue(result.request_id is not None)

        result = self.bucket.get_object(key)
        self.assertEqual(content, result.read())
        self.assertEqual(result.headers['x-oss-object-type'], 'Multipart')

        result = self.bucket.get_object_tagging(key)

        self.assertEqual(3, result.tag_set.len())
        tagging_rule = result.tag_set.tagging_rule
        self.assertEqual(256 * 'b', tagging_rule[128 * 'a'])
        self.assertEqual(':+:', tagging_rule['+-:/'])
        self.assertEqual('++中文++', tagging_rule['中文'])

        self.bucket.delete_object_tagging(key)

        result = self.bucket.get_object_tagging(key)

        self.assertEqual(0, result.tag_set.len())
        self.bucket.delete_object(key)


if __name__ == '__main__':
    unittest.main()
