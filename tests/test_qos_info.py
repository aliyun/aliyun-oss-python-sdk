# -*- coding: utf-8 -*-

from .common import *
from oss2.models import UserQosInfo, BucketQosInfo

class TestQosInfo(OssTestCase):
    def test_get_user_qos_info(self):
        service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)

        result = service.get_user_qos_info()
        self.assertEqual(result.status, 200)
        self.assertTrue(result.region is not None)
        self.assertTrue(result.total_upload_bw is not None)
        self.assertTrue(result.intranet_upload_bw is not None)
        self.assertTrue(result.extranet_upload_bw is not None)
        self.assertTrue(result.total_download_bw is not None)
        self.assertTrue(result.intranet_download_bw is not None)
        self.assertTrue(result.extranet_download_bw is not None)
        self.assertTrue(result.total_qps is not None)
        self.assertTrue(result.intranet_qps is not None)
        self.assertTrue(result.extranet_qps is not None)

    def test_put_bucket_qos_info_with_all_args(self):
        bucket_qos_info = BucketQosInfo(
                    total_upload_bw = -1,
                    intranet_upload_bw = 2,
                    extranet_upload_bw = 2,
                    total_download_bw = -1,
                    intranet_download_bw = -1,
                    extranet_download_bw = -1,
                    total_qps = -1,
                    intranet_qps = -1,
                    extranet_qps = -1)

        result = self.bucket.put_bucket_qos_info(bucket_qos_info)
        self.assertEqual(result.status, 200)

        result = self.bucket.get_bucket_qos_info()
        self.assertEqual(result.status, 200)
        self.assertEqual(result.total_upload_bw, bucket_qos_info.total_upload_bw)
        self.assertEqual(result.intranet_upload_bw, bucket_qos_info.intranet_upload_bw)
        self.assertEqual(result.extranet_upload_bw, bucket_qos_info.extranet_upload_bw)
        self.assertEqual(result.total_download_bw, bucket_qos_info.total_download_bw)
        self.assertEqual(result.intranet_download_bw, bucket_qos_info.intranet_download_bw)
        self.assertEqual(result.extranet_download_bw, bucket_qos_info.extranet_download_bw)
        self.assertEqual(result.total_qps, bucket_qos_info.total_qps)
        self.assertEqual(result.intranet_qps, bucket_qos_info.intranet_qps)
        self.assertEqual(result.extranet_qps, bucket_qos_info.extranet_qps)

        result = self.bucket.delete_bucket_qos_info()
        self.assertEqual(result.status, 204)

    def test_put_bucket_qos_info_with_none_args(self):
        bucket_qos_info = BucketQosInfo()

        # put bucket qos info without args setting, the default value of -1 will be returned.
        result = self.bucket.put_bucket_qos_info(bucket_qos_info)
        self.assertEqual(result.status, 200)

        result = self.bucket.get_bucket_qos_info()
        self.assertEqual(result.total_upload_bw, -1)
        self.assertEqual(result.intranet_upload_bw, -1)
        self.assertEqual(result.extranet_upload_bw, -1)
        self.assertEqual(result.total_download_bw, -1)
        self.assertEqual(result.intranet_download_bw, -1)
        self.assertEqual(result.extranet_download_bw, -1)
        self.assertEqual(result.total_qps, -1)
        self.assertEqual(result.intranet_qps, -1)
        self.assertEqual(result.extranet_qps, -1)

        result = self.bucket.delete_bucket_qos_info()
        self.assertEqual(result.status, 204)

    def test_put_bucket_qos_info_illegal_args(self):
        service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)
        user_qos_info = service.get_user_qos_info()
        self.assertTrue(user_qos_info.total_upload_bw > 0, 'user_qos_info.total_upload_bw should be > 0')
        self.assertTrue(user_qos_info.total_download_bw > 0, 'user_qos_info.total_download_bw should be > 0')

        # total_upload_bw > user_qos_info.total_upload_bw, should be failed.
        total_upload_bw = user_qos_info.total_upload_bw + 1
        bucket_qos_info = BucketQosInfo(total_upload_bw=total_upload_bw)
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_qos_info, bucket_qos_info)

        # intranet_upload_bw > total_upload_bw, should be failed.
        total_upload_bw = user_qos_info.total_upload_bw
        intranet_upload_bw = total_upload_bw + 1
        bucket_qos_info = BucketQosInfo(total_upload_bw=total_upload_bw, intranet_upload_bw=intranet_upload_bw)
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_qos_info, bucket_qos_info)

        # extranet_upload_bw > total_upload_bw, should be failed.
        total_upload_bw = user_qos_info.total_upload_bw
        extranet_upload_bw = total_upload_bw + 1
        bucket_qos_info = BucketQosInfo(total_upload_bw, extranet_upload_bw=extranet_upload_bw)
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_qos_info, bucket_qos_info)

        # total_download_bw > user_qos_info.total_upload_bw, should be failed.
        total_download_bw = user_qos_info.total_download_bw + 1
        bucket_qos_info = BucketQosInfo(total_download_bw=total_download_bw)
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_qos_info, bucket_qos_info)

        # intranet_download_bw > total_download_bw, should be failed.
        total_download_bw = user_qos_info.total_download_bw
        intranet_download_bw = total_download_bw + 1
        bucket_qos_info = BucketQosInfo(total_download_bw=total_download_bw, intranet_download_bw=intranet_download_bw)
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_qos_info, bucket_qos_info)

        # extranet_download_bw > total_download_bw, should be failed.
        total_download_bw = user_qos_info.total_download_bw
        extranet_download_bw = total_download_bw + 1
        bucket_qos_info = BucketQosInfo(total_download_bw=total_download_bw, extranet_download_bw=extranet_download_bw)
        self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_qos_info, bucket_qos_info)

        #self.assertTrue(user_qos_info.total_qps > 0, 'user_qos_info.total_qps should be > 0')
        if user_qos_info.total_qps > 0 :
            # total_qps > user_qos_info.total_qps, should be failed.
            total_qps = user_qos_info.total_qps + 1
            bucket_qos_info = BucketQosInfo(total_qps=total_qps)
            self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_qos_info, bucket_qos_info)

            # intranet_qps > total_qps, should be failed.
            total_qps = total_qps
            intranet_qps = total_qps + 1
            bucket_qos_info = BucketQosInfo(total_qps=total_qps, intranet_qps=intranet_qps)
            self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_qos_info, bucket_qos_info)

            # extranet_qps > total_qps, should be failed.
            total_qps = total_qps
            extranet_qps = total_qps + 1
            bucket_qos_info = BucketQosInfo(extranet_qps=extranet_qps)
            self.assertRaises(oss2.exceptions.InvalidArgument, self.bucket.put_bucket_qos_info, bucket_qos_info)
        else:
            self.assertTrue(user_qos_info.total_qps == -1, 'default user_qos_info.total_qps is -1')

if __name__ == '__main__':
    unittest.main()