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
        oss_access_point_name = 'oss-access-point-name-test'

        try:
            self.bucket.put_access_point_public_access_block(oss_access_point_name, True)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(404, e.status)
            self.assertEqual('Accesspoint not found', e.message)

        try:
            self.bucket.get_access_point_public_access_block(oss_access_point_name)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(404, e.status)
            self.assertEqual('Accesspoint not found', e.message)

        try:
            self.bucket.delete_access_point_public_access_block(oss_access_point_name)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(404, e.status)
            self.assertEqual('Accesspoint not found', e.message)


if __name__ == '__main__':
    unittest.main()
