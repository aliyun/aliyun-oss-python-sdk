# -*- coding: utf-8 -*-

import oss2
from .common import *
from oss2.models import (InventoryConfiguration,
                        InventoryFilter, 
                        InventorySchedule, 
                        InventoryDestination, 
                        InventoryBucketDestination, 
                        InventoryServerSideEncryptionKMS,
                        InventoryServerSideEncryptionOSS,
                        INVENTORY_INCLUDED_OBJECT_VERSIONS_CURRENT,
                        INVENTORY_INCLUDED_OBJECT_VERSIONS_ALL,
                        INVENTORY_FREQUENCY_DAILY,
                        INVENTORY_FREQUENCY_WEEKLY,
                        INVENTORY_FORMAT_CSV,
                        FIELD_SIZE,
                        FIELD_LAST_MODIFIED_DATE,
                        FIELD_STORAG_CLASS,
                        FIELD_ETAG,
                        FIELD_IS_MULTIPART_UPLOADED,
                        FIELD_ENCRYPTION_STATUS)

class TestBucketInventory(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)
        self.endpoint = OSS_ENDPOINT
        bucket_name = self.OSS_BUCKET + "-test-inventory"
        self.bucket1 = oss2.Bucket(oss2.make_auth(OSS_ID, OSS_SECRET, OSS_AUTH_VERSION), self.endpoint, bucket_name)
        self.bucket1.create_bucket()


    def test_bucket_inventory(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-test-inventory-dest"
        dest_bucket = oss2.Bucket(auth, self.endpoint, dest_bucket_name)
        dest_bucket.create_bucket()

        inventory_id = "test-id-3"
        optional_fields = [FIELD_SIZE, FIELD_LAST_MODIFIED_DATE, FIELD_STORAG_CLASS,
                FIELD_ETAG, FIELD_IS_MULTIPART_UPLOADED, FIELD_ENCRYPTION_STATUS]

        bucket_destination = InventoryBucketDestination(
                account_id=OSS_INVENTORY_BUCKET_DESTINATION_ACCOUNT, 
                role_arn=OSS_INVENTORY_BUCKET_DESTINATION_ARN,
                bucket=dest_bucket_name,
                inventory_format=INVENTORY_FORMAT_CSV,
                prefix="destination-prefix",
                sse_oss_encryption=InventoryServerSideEncryptionOSS())

        inventory_configuration = InventoryConfiguration(
                inventory_id=inventory_id,
                is_enabled=True, 
                inventory_schedule=InventorySchedule(frequency=INVENTORY_FREQUENCY_WEEKLY),
                included_object_versions=INVENTORY_INCLUDED_OBJECT_VERSIONS_ALL,
                inventory_filter=InventoryFilter(prefix="obj-prefix"),
                optional_fields=optional_fields,
                inventory_destination=InventoryDestination(bucket_destination=bucket_destination))

        self.bucket1.put_bucket_inventory_configuration(inventory_configuration);

        result = self.bucket1.get_bucket_inventory_configuration(inventory_id = inventory_id);
        self.assertEquals(inventory_id, result.inventory_id)
        self.assertEquals(True, result.is_enabled)
        self.assertEquals(INVENTORY_FREQUENCY_WEEKLY, result.inventory_schedule.frequency)
        self.assertEquals(INVENTORY_INCLUDED_OBJECT_VERSIONS_ALL, result.included_object_versions)
        self.assertEquals("obj-prefix", result.inventory_filter.prefix)
        self.assertEquals(len(optional_fields), len(result.optional_fields))
        ret_bucket_destin = result.inventory_destination.bucket_destination
        self.assertEquals(OSS_INVENTORY_BUCKET_DESTINATION_ACCOUNT, ret_bucket_destin.account_id)
        self.assertEquals(OSS_INVENTORY_BUCKET_DESTINATION_ARN, ret_bucket_destin.role_arn)
        self.assertEquals(dest_bucket_name, ret_bucket_destin.bucket)
        self.assertEquals(INVENTORY_FORMAT_CSV, ret_bucket_destin.inventory_format)
        self.assertEquals("destination-prefix", ret_bucket_destin.prefix)
        self.assertIsNone(ret_bucket_destin.sse_kms_encryption)
        self.assertIsNotNone(ret_bucket_destin.sse_oss_encryption)

        self.bucket1.delete_bucket_inventory_configuration(inventory_id)
        dest_bucket.delete_bucket()

    def test_error_bucket_encryption(self):
        # both encryption set.
        self.assertRaises(oss2.exceptions.ClientError, InventoryBucketDestination,
                account_id=OSS_INVENTORY_BUCKET_DESTINATION_ACCOUNT, 
                role_arn=OSS_INVENTORY_BUCKET_DESTINATION_ARN,
                bucket="test-bucket-name",
                inventory_format=INVENTORY_FORMAT_CSV,
                prefix="test-",
                sse_kms_encryption = InventoryServerSideEncryptionKMS("test-kms-id"),
                sse_oss_encryption=InventoryServerSideEncryptionOSS())           

    def test_list_few_bucket_inventory(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-test-inventory-dest"
        dest_bucket = oss2.Bucket(auth, self.endpoint, dest_bucket_name)
        dest_bucket.create_bucket()
        time.sleep(5)

        inventory_id_prefix = "test-id-"
        for index in range(0, 3):
            inventory_id = inventory_id_prefix + str(index)
            optional_fields = [FIELD_SIZE, FIELD_LAST_MODIFIED_DATE, FIELD_STORAG_CLASS,
                    FIELD_ETAG, FIELD_IS_MULTIPART_UPLOADED, FIELD_ENCRYPTION_STATUS]

            bucket_destination = InventoryBucketDestination(
                    account_id=OSS_INVENTORY_BUCKET_DESTINATION_ACCOUNT, 
                    role_arn=OSS_INVENTORY_BUCKET_DESTINATION_ARN,
                    bucket=self.OSS_BUCKET,
                    inventory_format=INVENTORY_FORMAT_CSV,
                    prefix="destination-prefix",
                    sse_kms_encryption=InventoryServerSideEncryptionKMS(OSS_CMK))

            inventory_configuration = InventoryConfiguration(
                    inventory_id=inventory_id,
                    is_enabled=True, 
                    inventory_schedule=InventorySchedule(frequency=INVENTORY_FREQUENCY_DAILY),
                    included_object_versions=INVENTORY_INCLUDED_OBJECT_VERSIONS_CURRENT,
                    inventory_filter=InventoryFilter(prefix="obj-prefix"),
                    optional_fields=optional_fields,
                    inventory_destination=InventoryDestination(bucket_destination=bucket_destination))

            self.bucket1.put_bucket_inventory_configuration(inventory_configuration);
        
        # test with param empty
        result = self.bucket1.list_bucket_inventory_configurations('')
        self.assertEquals(3, len(result.inventory_configurations))
        self.assertEquals(False, result.is_truncated)
        self.assertEquals(None, result.continuaiton_token)
        self.assertEquals(None, result.next_continuation_token)

        # test with param None
        result = self.bucket1.list_bucket_inventory_configurations()
        self.assertEquals(3, len(result.inventory_configurations))
        self.assertEquals(False, result.is_truncated)
        self.assertEquals(None, result.continuaiton_token)
        self.assertEquals(None, result.next_continuation_token)

        dest_bucket.delete_bucket()

    def test_list_lot_bucket_inventory(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-test-inventory-dest"
        dest_bucket = oss2.Bucket(auth, self.endpoint, dest_bucket_name)
        dest_bucket.create_bucket()

        inventory_id_prefix = "test-lot-id-"
        for index in range(0, 120):
            inventory_id = inventory_id_prefix + str(index)
            optional_fields = [FIELD_SIZE, FIELD_LAST_MODIFIED_DATE, FIELD_STORAG_CLASS,
                    FIELD_ETAG, FIELD_IS_MULTIPART_UPLOADED, FIELD_ENCRYPTION_STATUS]

            bucket_destination = InventoryBucketDestination(
                    account_id=OSS_INVENTORY_BUCKET_DESTINATION_ACCOUNT, 
                    role_arn=OSS_INVENTORY_BUCKET_DESTINATION_ARN,
                    bucket=self.OSS_BUCKET,
                    inventory_format=INVENTORY_FORMAT_CSV,
                    prefix="destination-prefix")

            inventory_configuration = InventoryConfiguration(
                    inventory_id=inventory_id,
                    is_enabled=True, 
                    inventory_schedule=InventorySchedule(frequency=INVENTORY_FREQUENCY_DAILY),
                    included_object_versions=INVENTORY_INCLUDED_OBJECT_VERSIONS_CURRENT,
                    inventory_filter=InventoryFilter(prefix="obj-prefix"),
                    optional_fields=optional_fields,
                    inventory_destination=InventoryDestination(bucket_destination=bucket_destination))

            self.bucket1.put_bucket_inventory_configuration(inventory_configuration);

        result = self.bucket1.list_bucket_inventory_configurations()
        self.assertEquals(100, len(result.inventory_configurations))
        self.assertEquals(True, result.is_truncated)
        self.assertEquals(None, result.continuaiton_token)
        self.assertIsNotNone(result.next_continuation_token)

        next_continuation_token = result.next_continuation_token
        result = self.bucket1.list_bucket_inventory_configurations(next_continuation_token)
        self.assertEquals(20, len(result.inventory_configurations))
        self.assertEquals(False, result.is_truncated)
        self.assertEquals(next_continuation_token, result.continuaiton_token)
        self.assertEquals(None, result.next_continuation_token)

        dest_bucket.delete_bucket()

    def test_list_none_inventory(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-test-none-inventory"
        dest_bucket = oss2.Bucket(auth, self.endpoint, dest_bucket_name)
        dest_bucket.create_bucket()
        self.assertRaises(oss2.exceptions.NoSuchInventory, dest_bucket.list_bucket_inventory_configurations)

        dest_bucket.delete_bucket()


if __name__ == '__main__':
    unittest.main()
