from oss2.models import MetaQuery, AggregationsRequest
from .common import *

class TestBucketMetaQuery(OssTestCase):
    def test_1_bucket_meta_query(self):
        key = 'a.txt'
        self.bucket.put_object(key, 'content')
        # 开启元数据管理功能
        result = self.bucket.open_bucket_meta_query()
        self.assertEqual(200, result.status)
        key = 'b.txt'
        self.bucket.put_object(key, 'content bbbbbbb')

        while True:
            time.sleep(10)
            # 获取指定存储空间（Bucket）的元数据索引库信息
            get_result = self.bucket.get_bucket_meta_query()
            if get_result.state == 'Running':
                # 查询满足指定条件的文件（Object），并按照指定字段和排序方式列出文件信息。
                do_meta_query_request = MetaQuery('', 2, '{"Field": "Size","Value": "1048576","Operation": "lt"}', 'Size', 'asc')
                result = self.bucket.do_bucket_meta_query(do_meta_query_request)

                if result.files.__len__() <= 0:
                    continue
                self.assertEqual(200, result.status)
                self.assertEqual('a.txt', result.files[0].file_name)
                self.assertIsNotNone(result.files[0].etag)
                self.assertIsNotNone(result.files[0].oss_object_type)
                self.assertIsNotNone(result.files[0].oss_storage_class)
                self.assertIsNotNone(result.files[0].oss_crc64)
                self.assertIsNotNone(result.files[0].object_acl)
                self.assertEqual('b.txt', result.files[1].file_name)
                self.assertIsNotNone(result.files[1].etag)
                self.assertIsNotNone(result.files[1].oss_object_type)
                self.assertIsNotNone(result.files[1].oss_storage_class)
                self.assertIsNotNone(result.files[1].oss_crc64)
                self.assertIsNotNone(result.files[1].object_acl)
                break

        # 关闭存储空间（Bucket）的元数据管理功能。
        result = self.bucket.close_bucket_meta_query()
        self.assertEqual(200, result.status)

    def test_2_bucket_meta_query_aggregation(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        dest_bucket_name = OSS_BUCKET + "-test-meta-query"
        dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name)
        dest_bucket.create_bucket()

        key = 'c.txt'
        dest_bucket.put_object(key, 'content  ccccc')
        # 开启元数据管理功能
        result = dest_bucket.open_bucket_meta_query()
        self.assertEqual(200, result.status)
        key = 'd.txt'
        dest_bucket.put_object(key, 'content dddddd')
        while True:
            time.sleep(10)
            # 获取指定存储空间（Bucket）的元数据索引库信息
            get_result = dest_bucket.get_bucket_meta_query()
            if get_result.state == 'Running':
                # 查询满足指定条件的文件（Object），并按照指定字段和排序方式列出文件信息。
                aggregations1 = AggregationsRequest(field='Size', operation='sum')
                aggregations2 = AggregationsRequest(field='Size', operation='max')
                do_meta_query_request = MetaQuery(max_results=2, query='{"Field": "Size","Value": "1048576","Operation": "lt"}', sort='Size', order='asc', aggregations=[aggregations1, aggregations2])
                result = dest_bucket.do_bucket_meta_query(do_meta_query_request)

                if result.files.__len__() <= 0:
                    continue
                self.assertEqual(200, result.status)
                self.assertEqual('Size', result.aggregations[0].field)
                self.assertEqual('sum', result.aggregations[0].operation)
                self.assertEqual('Size', result.aggregations[1].field)
                self.assertEqual('max', result.aggregations[1].operation)
                break
        # 关闭存储空间（Bucket）的元数据管理功能。
        result = dest_bucket.close_bucket_meta_query()
        self.assertEqual(200, result.status)

        dest_bucket.delete_bucket()
        self.assertEqual(200, dest_bucket.status)

if __name__ == '__main__':
    unittest.main()
