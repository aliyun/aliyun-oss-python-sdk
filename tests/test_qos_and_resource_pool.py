from oss2.models import QoSConfiguration
from .common import *

class TestQosAndResourcePool(OssTestCase):
    def test_qos_and_resource_pool(self):
        uid = OSS_TEST_UID
        resource_pool_name = 'test'

        service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)

        # put bucket requester qos info
        qos_info = QoSConfiguration(
            total_upload_bw = 100,
            intranet_upload_bw = 6,
            extranet_upload_bw = 12,
            total_download_bw = 110,
            intranet_download_bw = 20,
            extranet_download_bw = 50,
            total_qps = 300,
            intranet_qps = 160,
            extranet_qps = 170)

        result = self.bucket.put_bucket_requester_qos_info(uid, qos_info)
        self.assertEqual(200, result.status)

        # get bucket requester qos info
        result = self.bucket.get_bucket_requester_qos_info(uid)
        self.assertEqual(uid, result.requester)
        self.assertEqual(100, result.qos_configuration.total_upload_bw)
        self.assertEqual(6, result.qos_configuration.intranet_upload_bw)
        self.assertEqual(12, result.qos_configuration.extranet_upload_bw)
        self.assertEqual(110, result.qos_configuration.total_download_bw)
        self.assertEqual(20, result.qos_configuration.intranet_download_bw)
        self.assertEqual(50, result.qos_configuration.extranet_download_bw)
        self.assertEqual(300, result.qos_configuration.total_qps)
        self.assertEqual(160, result.qos_configuration.intranet_qps)
        self.assertEqual(170, result.qos_configuration.extranet_qps)

        # list bucket requester qos infos
        result = self.bucket.list_bucket_requester_qos_infos()
        self.assertEqual(self.OSS_BUCKET, result.bucket)
        self.assertEqual('', result.continuation_token)
        self.assertEqual('', result.next_continuation_token)
        self.assertEqual(False, result.is_truncated)
        self.assertEqual(100, result.requester_qos_info[0].qos_configuration.total_upload_bw)
        self.assertEqual(6, result.requester_qos_info[0].qos_configuration.intranet_upload_bw)
        self.assertEqual(12, result.requester_qos_info[0].qos_configuration.extranet_upload_bw)
        self.assertEqual(110, result.requester_qos_info[0].qos_configuration.total_download_bw)
        self.assertEqual(20, result.requester_qos_info[0].qos_configuration.intranet_download_bw)
        self.assertEqual(50, result.requester_qos_info[0].qos_configuration.extranet_download_bw)
        self.assertEqual(300, result.requester_qos_info[0].qos_configuration.total_qps)
        self.assertEqual(160, result.requester_qos_info[0].qos_configuration.intranet_qps)
        self.assertEqual(170, result.requester_qos_info[0].qos_configuration.extranet_qps)

        # delete bucket requester qos info
        result = self.bucket.delete_bucket_requester_qos_info(uid)
        self.assertEqual(204, result.status)

        # list resource pools
        result = service.list_resource_pools()
        self.assertEqual(200, result.status)
        self.assertEqual(OSS_REGION, result.region)
        self.assertEqual(uid, result.owner)
        self.assertEqual('', result.continuation_token)
        self.assertEqual('', result.next_continuation_token)
        self.assertEqual(False, result.is_truncated)

        # get resource pool info
        try:
            service.get_resource_pool_info(resource_pool_name)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 404)
            self.assertEqual(e.message, 'The specified resource pool does not exist.')


        # list resource pool buckets
        try:
            service.list_resource_pool_buckets(resource_pool_name)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 404)
            self.assertEqual(e.message, 'The specified resource pool does not exist.')


        # put resource pool requester qos info
        qos_info = QoSConfiguration(
            total_upload_bw = 200,
            intranet_upload_bw = 16,
            extranet_upload_bw = 112,
            total_download_bw = 210,
            intranet_download_bw = 120,
            extranet_download_bw = 150,
            total_qps = 400,
            intranet_qps = 260,
            extranet_qps = 270)
        try:
            service.put_resource_pool_requester_qos_info(uid, resource_pool_name, qos_info)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 404)
            self.assertEqual(e.message, 'The specified resource pool does not exist.')


        # get resource pool requester qos info
        try:
            service.get_resource_pool_requester_qos_info(uid, resource_pool_name)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 404)
            self.assertEqual(e.message, 'The specified resource pool does not exist.')


        # list resource pool requester qos infos
        try:
            service.list_resource_pool_requester_qos_infos(resource_pool_name)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 404)
            self.assertEqual(e.message, 'The specified resource pool does not exist.')


        # delete resource pool requester qos infos
        try:
            service.delete_resource_pool_requester_qos_info(uid, resource_pool_name)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 404)
            self.assertEqual(e.message, 'The specified resource pool does not exist.')


    def test_qos_and_resource_pool_exception(self):
        uid = None
        resource_pool_name = ''

        service = oss2.Service(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT)

        # put bucket requester qos info
        qos_info = None

        try:
            self.bucket.put_bucket_requester_qos_info(uid, qos_info)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: uid should not be empty')


        # get bucket requester qos info
        try:
            self.bucket.get_bucket_requester_qos_info(uid)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: uid should not be empty')


        # delete bucket requester qos info
        try:
            result = self.bucket.delete_bucket_requester_qos_info(uid)
            self.assertEqual(204, result.status)

        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: uid should not be empty')


        # get resource pool info
        try:
            service.get_resource_pool_info(resource_pool_name)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: resource_pool_name should not be empty')

        # list resource pool buckets
        try:
            service.list_resource_pool_buckets(resource_pool_name)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: resource_pool_name should not be empty')

        # put resource pool requester qos info
        qos_info = QoSConfiguration(
            total_upload_bw = 200,
            intranet_upload_bw = 16,
            extranet_upload_bw = 112,
            total_download_bw = 210,
            intranet_download_bw = 120,
            extranet_download_bw = 150,
            total_qps = 400,
            intranet_qps = 260,
            extranet_qps = 270)
        try:
            service.put_resource_pool_requester_qos_info(uid, resource_pool_name, qos_info)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: uid should not be empty')

        qos_info = None
        try:
            service.put_resource_pool_requester_qos_info('uid-test', resource_pool_name, qos_info)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: resource_pool_name should not be empty')

        # get resource pool requester qos info
        try:
            service.get_resource_pool_requester_qos_info(uid, resource_pool_name)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: uid should not be empty')

        try:
            service.get_resource_pool_requester_qos_info('uid-test', resource_pool_name)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: resource_pool_name should not be empty')


        # list resource pool requester qos infos
        try:
            service.list_resource_pool_requester_qos_infos(resource_pool_name)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: resource_pool_name should not be empty')


        # delete resource pool requester qos infos
        try:
            service.delete_resource_pool_requester_qos_info(uid, resource_pool_name)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: uid should not be empty')

        try:
            service.delete_resource_pool_requester_qos_info('uid-test', resource_pool_name)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: resource_pool_name should not be empty')


if __name__ == '__main__':
    unittest.main()
