# -*- coding: utf-8 -*-

from .common import *
import oss2
from oss2.headers import OSS_REQUEST_PAYER
from oss2.models import (PAYER_REQUESTER, 
                         BucketVersioningConfig, 
                         BatchDeleteObjectVersion, 
                         BatchDeleteObjectVersionList)


class TestObjectRequestPaymentVersions(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)
        self.endpoint = "http://oss-ap-south-1.aliyuncs.com"
        bucket_name = OSS_BUCKET + "-test-request-payment-versionging"

        policy_text = ''
        policy_text += '{'
        policy_text += '"Version":"1",'
        policy_text += '"Statement":[{'
        policy_text += '"Action":["oss:*"],'
        policy_text += '"Effect":"Allow",'
        policy_text += '"Principal":["{0}"],'.format(OSS_PAYER_UID)
        policy_text += '"Resource": ["acs:oss:*:*:{0}","acs:oss:*:*:{0}/*"]'.format(bucket_name)
        policy_text += '}]}'

        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        self.owner_bucket = oss2.Bucket(auth, self.endpoint, bucket_name)
        self.owner_bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        self.owner_bucket.put_bucket_policy(policy_text)

        # Enable bucket request payment
        result = self.owner_bucket.put_bucket_request_payment(PAYER_REQUESTER)
        self.assertEqual(result.status, 200)

        self.payer_bucket = oss2.Bucket(oss2.Auth(OSS_PAYER_ID, OSS_PAYER_SECRET), self.endpoint, bucket_name)

        # Enable bucket versioning
        config = BucketVersioningConfig()
        config.status = oss2.BUCKET_VERSIONING_ENABLE
        self.owner_bucket.put_bucket_versioning(config)
        self.assertEqual(result.status, 200)

    def test_delete_object_versions(self):
        key = 'requestpayment-test-delete-object-versions'
        content1 = 'test-content-1'
        content2 = 'test-content-2'

        result = self.owner_bucket.put_object(key, content1)
        versionid1 = result.versionid

        result = self.owner_bucket.put_object(key, content2)
        versionid2 = result.versionid

        version_list = BatchDeleteObjectVersionList()
        version_list.append(BatchDeleteObjectVersion(key=key, versionid=versionid1))
        version_list.append(BatchDeleteObjectVersion(key=key, versionid=versionid2))

        # Delete object verions without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.delete_object_versions, version_list)

        # Delete object verions with payer setting, should be failed.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        self.payer_bucket.delete_object_versions(version_list, headers=headers)

    def test_list_object_versions(self):
        # List object versions without payer setting, should be failed.
        self.assertRaises(oss2.exceptions.AccessDenied, self.payer_bucket.list_object_versions)

        # List object versions with payer setting, should be successful.
        headers = dict()
        headers[OSS_REQUEST_PAYER] = "requester"
        result = self.payer_bucket.list_object_versions(headers=headers)
        self.assertEqual(result.status, 200)


if __name__ == '__main__':
    unittest.main()