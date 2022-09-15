# -*- coding: utf-8 -*-

from .common import *


class TestIteratorV2(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)
        self.endpoint = OSS_ENDPOINT

    def test_normal_list_objects(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-normal"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        # list empty bucket
        result = bucket.list_objects_v2()
        self.assertEqual(0, len(result.object_list))
        self.assertEqual(0, len(result.prefix_list))
        self.assertFalse(result.is_truncated)
        self.assertEqual('', result.next_continuation_token)

        # 9 files under sub-dir
        dir1 = 'test-dir/'
        sub_dir = 'sub-dir/'
        key_prefix = dir1 + sub_dir + 'test-file'
        for i in range(9):
            key = key_prefix + str(i) + '.txt'
            bucket.put_object(key, b'a')

        # 1 file under dir1
        bucket.put_object(dir1 + 'sub-file.txt', b'a')

        # 3 top dir files
        big_letter_prefix = 'z'
        bucket.put_object(big_letter_prefix + '1.txt', b'a')
        bucket.put_object(big_letter_prefix + '2.txt', b'a')
        bucket.put_object(big_letter_prefix + '3.txt', b'a')

        # list under bucket
        result = bucket.list_objects_v2(max_keys=10)
        self.assertEqual(10, len(result.object_list))
        self.assertEqual(0, len(result.prefix_list))
        self.assertTrue(result.is_truncated)
        self.assertTrue(len(result.next_continuation_token) > 0)

        # list with continuation_token
        continuation_token = result.next_continuation_token
        result = bucket.list_objects_v2(continuation_token=continuation_token)
        self.assertEqual(3, len(result.object_list))
        self.assertEqual(0, len(result.prefix_list))
        self.assertFalse(result.is_truncated)
        self.assertEqual('', result.next_continuation_token)

        # list with prefix
        result = bucket.list_objects_v2(prefix=big_letter_prefix)
        self.assertEqual(3, len(result.object_list))
        self.assertEqual(0, len(result.prefix_list))
        self.assertFalse(result.is_truncated)
        self.assertEqual('', result.next_continuation_token)

        # list with prefix and delimiter
        result = bucket.list_objects_v2(prefix=dir1, delimiter='/')
        self.assertEqual(1, len(result.object_list))
        self.assertEqual(1, len(result.prefix_list))
        self.assertFalse(result.is_truncated)
        self.assertEqual('', result.next_continuation_token)
        self.assertEqual(dir1 + 'sub-file.txt', result.object_list[0].key)
        self.assertIsNone(result.object_list[0].owner)
        self.assertEqual(dir1 + sub_dir, result.prefix_list[0])

        # list with start_after
        result = bucket.list_objects_v2(start_after=big_letter_prefix)
        self.assertEqual(3, len(result.object_list))
        self.assertEqual(0, len(result.prefix_list))
        self.assertFalse(result.is_truncated)
        self.assertEqual('', result.next_continuation_token)

    def test_list_with_encoding_type_None(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-list-with-encoding-type-none"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        object_name = "specified-char-" + "\001\007"
        bucket.put_object(object_name, b'a')

        # default is in url encoding type.
        result = bucket.list_objects_v2()
        self.assertEqual(object_name, result.object_list[0].key)

        # set encoding_type none
        try:
            bucket.list_objects_v2(encoding_type=None)
            self.assertFalse(True, "should be failed here.")
        except:
            pass

    def test_list_with_error_continuation_token(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-list-with-error-token"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        object_name = "test.txt"
        bucket.put_object(object_name, b'a')
        self.assertRaises(oss2.exceptions.InvalidArgument, bucket.list_objects_v2, continuation_token="err-token")


    def test_list_object_iterator_v2(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-test-list-iterator-v2"
        bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        bucket.create_bucket()

        prefix = 'test-dir/'
        object_list = []
        dir_list = []
        top_dir_object_list = []

        # 3 file with big letter prefix.
        big_letter_prefix = 'z'
        for i in range(3):
            top_dir_object_list.append(big_letter_prefix + random_string(16))
            bucket.put_object(top_dir_object_list[-1], random_bytes(10))

        # 10 file under dir.
        for i in range(10):
            object_list.append(prefix + random_string(16))
            bucket.put_object(object_list[-1], random_bytes(10))

        # 5 file under sub dir.
        for i in range(5):
            dir_list.append(prefix + random_string(5) + '/')
            bucket.put_object(dir_list[-1] + random_string(5), random_bytes(3))

        objects_got = []
        dirs_got = []
        for info in oss2.ObjectIteratorV2(bucket, prefix, delimiter='/', max_keys=4, fetch_owner=True):
            if info.is_prefix():
                dirs_got.append(info.key)
            else:
                objects_got.append(info.key)
                self.assertIsNotNone(info.owner)
                self.assertTrue(len(info.owner.display_name) > 0)
                self.assertTrue(len(info.owner.id) > 0)
                result = bucket.head_object(info.key)
                self.assertEqual(result.last_modified, info.last_modified)

        self.assertEqual(sorted(object_list), objects_got)
        self.assertEqual(sorted(dir_list), dirs_got)
        self.assertEqual(10, len(objects_got))
        self.assertEqual(5, len(dirs_got))

        # list with start after
        top_dir_object_got = []
        for info in oss2.ObjectIteratorV2(bucket, max_keys=2, start_after=big_letter_prefix):
            self.assertFalse(info.is_prefix())
            top_dir_object_got.append(info.key)
            self.assertIsNone(info.owner)

        self.assertEqual(3, len(top_dir_object_got))


if __name__ == '__main__':
    unittest.main()
