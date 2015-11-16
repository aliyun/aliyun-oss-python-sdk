import unittest
import oss
import logging
import io

from common import *


class TestMultipart(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestMultipart, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss.Bucket(oss.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)

    def test_multipart(self):
        object_name = random_string(64)
        content = random_bytes(128 * 1024)

        parts = []
        upload_id = self.bucket.init_multipart_upload(object_name).upload_id

        result = self.bucket.upload_part(object_name, upload_id, 1, content)
        parts.append(oss.models.PartInfo(1, result.etag))

        self.bucket.complete_multipart_upload(object_name, upload_id, parts)

        result = self.bucket.get_object(object_name)
        self.assertEqual(content, result.read())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()