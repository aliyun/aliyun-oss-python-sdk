from oss2.models import AccessPointVpcConfiguration, CreateAccessPointRequest
from .common import *

class TestBucketAccessMonitor(OssTestCase):

    def test_access_point(self):
        accessPointName = 'test-ap-py-5'
        vpc_id = 'example-vpc-1'
        vpc = AccessPointVpcConfiguration(vpc_id)
        service = oss2.Service(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), OSS_ENDPOINT)
        try:
            access_point = CreateAccessPointRequest(accessPointName, 'internet')
            # access_point = CreateAccessPointRequest(accessPointName, 'vpc', vpc)
            result = self.bucket.create_access_point(access_point)
            self.assertEqual(result.status, 200)
            print("create_access_point")

            get_result = self.bucket.get_access_point(accessPointName)
            self.assertEqual(get_result.status, 200)
            self.assertEqual(get_result.access_point_name, accessPointName)
            self.assertEqual(get_result.bucket, self.bucket.bucket_name)
            self.assertIsNotNone(get_result.account_id)
            self.assertEqual(get_result.network_origin, "internet")
            self.assertEqual(get_result.access_point_arn, result.access_point_arn)
            self.assertIsNotNone(get_result.creation_date)
            self.assertEqual(get_result.alias, result.alias)
            self.assertIsNotNone(get_result.access_point_status)
            self.assertIsNotNone(get_result.endpoints.public_endpoint)
            self.assertIsNotNone(get_result.endpoints.internal_endpoint)
            print("get_access_point")

            list_result = self.bucket.list_bucket_access_points(max_keys=10, continuation_token='')
            self.assertEqual(10, list_result.max_keys)
            self.assertIsNotNone(True, list_result.is_truncated)
            self.assertEqual(accessPointName, list_result.access_points[0].access_point_name)
            self.assertEqual(self.bucket.bucket_name, list_result.access_points[0].bucket)
            self.assertIsNotNone(list_result.access_points[0].network_origin)
            self.assertEqual(result.alias, list_result.access_points[0].alias)
            self.assertIsNotNone(list_result.access_points[0].status)
            print("list_bucket_access_points")

            list_result2 = service.list_access_points(max_keys=10, continuation_token='')
            self.assertEqual(10, list_result2.max_keys)
            self.assertIsNotNone(True, list_result2.is_truncated)
            self.assertEqual(accessPointName, list_result2.access_points[0].access_point_name)
            self.assertEqual(self.bucket.bucket_name, list_result2.access_points[0].bucket)
            self.assertIsNotNone(list_result2.access_points[0].network_origin)
            self.assertEqual(result.alias, list_result2.access_points[0].alias)
            self.assertIsNotNone(list_result2.access_points[0].status)
            print("list_access_points")

            num = 1
            while True:
                count = 0
                get_result = self.bucket.get_access_point(accessPointName)

                if num > 180:
                    break

                if get_result.access_point_status == 'enable':
                    count += 1
                    print("get_result status: "+get_result.access_point_status)
                    policy="{\"Version\":\"1\",\"Statement\":[{\"Action\":[\"oss:PutObject\",\"oss:GetObject\"],\"Effect\":\"Deny\",\"Principal\":[\""+OSS_TEST_UID+"\"],\"Resource\":[\"acs:oss:"+OSS_REGION+":"+OSS_TEST_UID+":accesspoint/"+accessPointName+"\",\"acs:oss:"+OSS_REGION+":"+OSS_TEST_UID+":accesspoint/"+accessPointName+"/object/*\"]}]}"

                    put_policy_result = self.bucket.put_access_point_policy(accessPointName, policy)
                    self.assertEqual(put_policy_result.status, 200)
                    print("put_access_point_policy")

                    get_policy_result = self.bucket.get_access_point_policy(accessPointName)
                    self.assertEqual(get_policy_result.status, 200)
                    self.assertEqual(get_policy_result.policy, policy)
                    print("get_access_point_policy")

                    del_policy_result = self.bucket.delete_access_point_policy(accessPointName)
                    self.assertEqual(del_policy_result.status, 204)
                    print("delete_access_point_policy")

                num += 1
                if count == 1:
                    break
                time.sleep(5)
        except Exception as e:
            print("Exception: {0}".format(e))
        finally:
            num = 1
            while True:
                count = 0
                list_result = service.list_access_points(max_keys=100)

                if num > 180:
                    break

                for ap in list_result.access_points:
                    if ap.access_point_name.startswith('test-ap-py-'):
                        count += 1
                        if ap.status == 'enable':
                            print("status: "+ap.status)
                            del_result = self.bucket.delete_access_point(ap.access_point_name)
                            self.assertEqual(del_result.status, 204)
                            print("delete_access_point")

                num += 1
                if count == 0:
                    break
                time.sleep(10)

if __name__ == '__main__':
    unittest.main()
