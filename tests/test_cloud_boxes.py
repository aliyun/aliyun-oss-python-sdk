# -*- coding: utf-8 -*-

import os, sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

from .common import *


class TestLiveChannel(OssTestCase):

    def _assert_list_result(self,
                            result,
                            marker = '',
                            prefix = '',
                            next_marker = '',
                            max_keys = 0,
                            is_truncated = False):
        self.assertEqual(result.prefix, prefix)
        self.assertEqual(result.marker, marker)
        self.assertEqual(result.next_marker, next_marker)
        self.assertEqual(result.max_keys, max_keys)
        self.assertEqual(result.is_truncated, is_truncated)


    def test_list_cloud_boxes(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-list-cloud-boxes"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)


        list_result = bucket.list_cloud_boxes()
        self._assert_list_result(list_result,
                                 prefix = '',
                                 marker = '',
                                 next_marker = '',
                                 max_keys = 1,
                                 is_truncated = False)

        list_result2 = bucket.list_cloud_boxes(marker=list_result.next_marker)

        self._assert_list_result(list_result2,
                                 prefix = '',
                                 marker = list_result.next_marker,
                                 next_marker = '',
                                 max_keys = 10,
                                 is_truncated = True)

        bucket.delete_bucket()
        wait_meta_sync()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)



if __name__ == '__main__':
    unittest.main()
