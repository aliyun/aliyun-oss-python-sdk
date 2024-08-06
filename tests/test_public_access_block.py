from .common import *

class TestPublicAccessBlock(OssTestCase):
    def test_public_access_block_normal(self):
        # case 1
        service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)
        result = service.put_public_access_block(True)
        self.assertEqual(200, result.status)

        # Sleep for a period of time and wait for status updates
        time.sleep(3)

        result = service.get_public_access_block()
        self.assertEqual(200, result.status)
        self.assertEqual(True, result.block_public_access)

        result = service.delete_public_access_block()
        self.assertEqual(204, result.status)

        # Sleep for a period of time and wait for status updates
        time.sleep(3)

        result = service.get_public_access_block()
        self.assertEqual(200, result.status)
        self.assertEqual(False, result.block_public_access)

        # case 2
        result = service.put_public_access_block()
        self.assertEqual(200, result.status)

        # Sleep for a period of time and wait for status updates
        time.sleep(3)

        result = service.get_public_access_block()
        self.assertEqual(200, result.status)
        self.assertEqual(False, result.block_public_access)

    def test_bucket_public_access_block_normal(self):
        # case 1
        result = self.bucket.put_bucket_public_access_block(True)
        self.assertEqual(200, result.status)

        # Sleep for a period of time and wait for status updates
        time.sleep(3)

        result = self.bucket.get_bucket_public_access_block()
        self.assertEqual(200, result.status)
        self.assertEqual(True, result.block_public_access)

        result = self.bucket.delete_bucket_public_access_block()
        self.assertEqual(204, result.status)

        # Sleep for a period of time and wait for status updates
        time.sleep(3)

        result = self.bucket.get_bucket_public_access_block()
        self.assertEqual(200, result.status)
        self.assertEqual(False, result.block_public_access)

        # case 2
        result = self.bucket.put_bucket_public_access_block()
        self.assertEqual(200, result.status)

        # Sleep for a period of time and wait for status updates
        time.sleep(3)

        result = self.bucket.get_bucket_public_access_block()
        self.assertEqual(200, result.status)
        self.assertEqual(False, result.block_public_access)


    def test_access_point_public_access_block_normal(self):

        # case 1
        result = self.bucket.put_access_point_public_access_block(OSS_ACCESS_POINT_NAME, True)
        self.assertEqual(200, result.status)

        # Sleep for a period of time and wait for status updates
        time.sleep(3)

        result = self.bucket.get_access_point_public_access_block(OSS_ACCESS_POINT_NAME)
        self.assertEqual(200, result.status)
        self.assertEqual(True, result.block_public_access)

        result = self.bucket.delete_access_point_public_access_block(OSS_ACCESS_POINT_NAME)
        self.assertEqual(204, result.status)

        # Sleep for a period of time and wait for status updates
        time.sleep(3)

        result = self.bucket.get_access_point_public_access_block(OSS_ACCESS_POINT_NAME)
        self.assertEqual(200, result.status)
        self.assertEqual(False, result.block_public_access)

        # case 2
        result = self.bucket.put_access_point_public_access_block(OSS_ACCESS_POINT_NAME)
        self.assertEqual(200, result.status)

        # Sleep for a period of time and wait for status updates
        time.sleep(3)

        result = self.bucket.get_access_point_public_access_block(OSS_ACCESS_POINT_NAME)
        self.assertEqual(200, result.status)
        self.assertEqual(False, result.block_public_access)


if __name__ == '__main__':
    unittest.main()
