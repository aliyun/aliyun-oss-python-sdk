# -*- coding: utf-8 -*-

import os
import oss2
from .common import *
from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import OSS_TRAFFIC_LIMIT, PartInfo

OBJECT_SIZE_1MB = (1 * 1024 * 1024)
LIMIT_100KB = (100 * 1024 * 8)

class TestTrafficLimit(OssTestCase):
    def test_put_object(self):
        key = 'traffic-limit-test-put-object'
        content = b'a' * OBJECT_SIZE_1MB

        # Put object with payer setting, should be successful.
        headers = dict()
        headers[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);

        start_time_sec = int(time.time())
        result = self.bucket.put_object(key, content, headers=headers)
        self.assertEqual(result.status, 200)
        end_time_sec = int(time.time())

        # Calculate expensed time
        expense_time_sec = end_time_sec - start_time_sec

        # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
        theoretical_exepnse_min = 10 * 0.7

        # Compare to minimum theoretical time
        self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)
        self.bucket.delete_object(key)

    def test_get_object(self):
        key = 'traffic-limit-test-get-object'
        content = b'a' * OBJECT_SIZE_1MB
        file_name = key + '.txt'

        result = self.bucket.put_object(key, content)

        headers = dict()
        headers[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);

        # Get object with traffic limit
        start_time_sec = int(time.time())
        result = self.bucket.get_object_to_file(key, file_name, headers=headers)
        self.assertEqual(result.status, 200)
        end_time_sec = int(time.time())

        os.remove(file_name)
        self.bucket.delete_object(key)

        # Calculate expensed time
        expense_time_sec = end_time_sec - start_time_sec

        # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
        theoretical_exepnse_min = 10 * 0.7

        # Compare to minimum theoretical time
        self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)

    def test_append_object(self):
        key = 'traffic-limit-test-apend-object'
        content = b'a' * OBJECT_SIZE_1MB

        headers = dict()
        headers[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);

        # Append object with traffic limit
        start_time_sec = int(time.time())
        result = self.bucket.append_object(key, 0, content, headers=headers)
        self.assertEqual(result.status, 200)
        end_time_sec = int(time.time())

        self.bucket.delete_object(key)

        # Calculate expensed time
        expense_time_sec = end_time_sec - start_time_sec

        # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
        theoretical_exepnse_min = 10 * 0.7

        # Compare to minimum theoretical time
        self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)

    def test_resumable_upload(self):
        key = 'traffic-limit-test-resumble-upload-object'
        pathname = self._prepare_temp_file_with_size(OBJECT_SIZE_1MB)

        headers = dict()
        headers[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);

        # Resumable upload object smaller than multipart_threshold with traffic limit
        start_time_sec = int(time.time())
        result = oss2.resumable_upload(self.bucket, key, pathname, multipart_threshold=(OBJECT_SIZE_1MB*2), headers=headers, num_threads=1)
        self.assertEqual(result.status, 200)
        end_time_sec = int(time.time())

        self.bucket.delete_object(key)

        # Calculate expensed time
        expense_time_sec = end_time_sec - start_time_sec
        # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
        theoretical_exepnse_min = 10 * 0.7
        # Compare to minimum theoretical time
        self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)

        # Resumable upload object bigger than multipart_threshold with traffic limit
        start_time_sec = int(time.time())
        result = oss2.resumable_upload(self.bucket, key, pathname, multipart_threshold=(OBJECT_SIZE_1MB-1024), headers=headers, num_threads=1)
        self.assertEqual(result.status, 200)
        end_time_sec = int(time.time())

        self.bucket.delete_object(key)

        # Calculate expensed time
        expense_time_sec = end_time_sec - start_time_sec
        # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
        theoretical_exepnse_min = 10 * 0.7
        # Compare to minimum theoretical time
        self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)

    def test_upload_part(self):
        key = 'traffic-limit-test-resumble-upload-object'
        # Create tmp file 2MB
        file_name = self._prepare_temp_file_with_size(OBJECT_SIZE_1MB * 2)

        total_size = os.path.getsize(file_name)
        # Determine part size is 1MB
        part_size = determine_part_size(total_size, preferred_size=(1024*1024))     

        # Init part
        upload_id = self.bucket.init_multipart_upload(key).upload_id
        parts = []  

        headers = dict()
        headers[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);    

        #  Upload part
        with open(file_name, 'rb') as fileobj:
            part_number = 1
            offset = 0
            while offset < total_size:
                num_to_upload = min(part_size, total_size - offset)

                # Upload part with traffic limit setting
                start_time_sec = int(time.time())
                result = self.bucket.upload_part(key, upload_id, part_number,
                                            SizedFileAdapter(fileobj, num_to_upload),
                                            headers=headers)
                end_time_sec = int(time.time())

                # Calculate expensed time
                expense_time_sec = end_time_sec - start_time_sec
                # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
                theoretical_exepnse_min = 10 * 0.7
                # Compare to minimum theoretical time
                self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)
                self.assertEqual((expense_time_sec > theoretical_exepnse_min), True)

                parts.append(PartInfo(part_number, result.etag))
                offset += num_to_upload
                part_number += 1        

        result = self.bucket.complete_multipart_upload(key, upload_id, parts)
        self.assertEqual(result.status, 200)

    def test_resumable_download(self):
        key = 'traffic-limit-test-resumble-download-object'
        content = b'a' * OBJECT_SIZE_1MB
        file_name = key + '.txt'

        # Put object
        self.bucket.put_object(key, content)

        headers = dict()
        headers[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);  

        # Resumable download object smaller than multiget_threshold with traffic limit setting.
        start_time_sec = int(time.time())
        oss2.resumable_download(self.bucket, key, file_name, multiget_threshold=(OBJECT_SIZE_1MB*2), num_threads=1, headers=headers)
        self.assertFileContent(file_name, content)
        end_time_sec = int(time.time())

        os.remove(file_name)

        # Calculate expensed time
        expense_time_sec = end_time_sec - start_time_sec
        # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
        theoretical_exepnse_min = 10 * 0.7
        # Compare to minimum theoretical time
        self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)

        # Resumable download object bigger than multiget_threshold with traffic limit setting.
        start_time_sec = int(time.time())
        oss2.resumable_download(self.bucket, key, file_name, multiget_threshold=(OBJECT_SIZE_1MB-1024), num_threads=1, headers=headers)
        self.assertFileContent(file_name, content)
        end_time_sec = int(time.time())

        os.remove(file_name)
        self.bucket.delete_object(key)

        # Calculate expensed time
        expense_time_sec = end_time_sec - start_time_sec
        # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
        theoretical_exepnse_min = 10 * 0.7
        # Compare to minimum theoretical time
        self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)

    def test_put_object_with_signed_url(self):
        key = 'traffic-limit-test-put-object-signed-url'
        file_name = self._prepare_temp_file_with_size(OBJECT_SIZE_1MB)

        # Create url with taffic limit setting.
        params = dict()
        params[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);  
        url = self.bucket.sign_url('PUT', key, 60, params=params)

        # Put object with url form file
        start_time_sec = int(time.time())
        result = self.bucket.put_object_with_url_from_file(url, file_name)
        self.assertEqual(result.status, 200)
        end_time_sec = int(time.time())

        # Check file size
        result = self.bucket.head_object(key)
        self.assertEqual(result.content_length, OBJECT_SIZE_1MB)

        self.bucket.delete_object(key)

        # Calculate expensed time
        expense_time_sec = end_time_sec - start_time_sec

        # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
        theoretical_exepnse_min = 10 * 0.7

        # Compare to minimum theoretical time
        self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)

    def test_get_object_with_signed_url(self):
        key = 'traffic-limit-test-get-object-signed-url'
        content = b'a' * OBJECT_SIZE_1MB
        file_name = key + '.txt'

        # Put file 
        result = self.bucket.put_object(key, content);
        self.assertEqual(result.status, 200)

        # Create url with taffic limit setting.
        params = dict()
        params[OSS_TRAFFIC_LIMIT] = str(LIMIT_100KB);  
        url = self.bucket.sign_url('GET', key, 60, params=params)

        # Get object to file with url 
        start_time_sec = int(time.time())
        result = self.bucket.get_object_with_url_to_file(url, file_name)
        self.assertEqual(result.status, 200)
        end_time_sec = int(time.time())

        # Check file size
        file_size = os.stat(file_name).st_size
        self.assertEqual(file_size, OBJECT_SIZE_1MB)

        os.remove(file_name)
        self.bucket.delete_object(key)

        # Calculate expensed time
        expense_time_sec = end_time_sec - start_time_sec

        # Theoretical time is 1MB/100KB = 10s, set the minimum theoretical time to 10*0.7s
        theoretical_exepnse_min = 10 * 0.7

        # Compare to minimum theoretical time
        self.assertEqual((expense_time_sec>theoretical_exepnse_min), True)


if __name__ == '__main__':
    unittest.main()