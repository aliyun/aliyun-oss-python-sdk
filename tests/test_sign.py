
from .common import *


class TestSign(OssTestCase):
    def test_sign_v1_x_oss_date(self):
        headers = dict()
        content = 'test example'
        put_result = self.bucket.put_object('testexampleobject.txt', content, headers=headers)
        self.assertEqual(200, put_result.status)

        headers['x-oss-date'] = oss2.utils.http_date(int(time.time()) + 24 * 60 * 60)
        try:
            self.bucket.list_objects('oss', '/', '', 10, headers=headers)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 403)
            self.assertEqual(e.message, 'The difference between the request time and the current time is too large.')

        headers['x-oss-date'] = oss2.utils.http_date(int(time.time()) + 60)
        get_result = self.bucket.get_object('testexampleobject.txt', headers=headers)
        self.assertEqual(200, get_result.status)

    def test_sign_v1_x_oss_date_url(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-sign-v1-url"
        dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name)
        dest_bucket.create_bucket()
        key = 'testexampleobject.txt'
        headers = dict()
        content = 'test example'
        url = dest_bucket.sign_url('PUT', key, 1650801600, headers=headers)
        print(url)

        put_result = dest_bucket.put_object_with_url(url, content)
        self.assertEqual(200, put_result.status)

        headers['x-oss-date'] = oss2.utils.http_date(int(time.time()) + 24 * 60 * 60)
        try:
            dest_bucket.get_object(key, headers=headers)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 403)
            self.assertEqual(e.message, 'The difference between the request time and the current time is too large.')

        dest_bucket.delete_object(key)
        dest_bucket.delete_bucket()

    def test_sign_v2_x_oss_date(self):
        auth = oss2.AuthV2(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-sign-v2"
        dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name)
        dest_bucket.create_bucket()
        key = 'testexampleobject.txt'

        headers = dict()
        content = 'test example'
        put_result = dest_bucket.put_object(key, content, headers=headers)
        self.assertEqual(200, put_result.status)

        headers['x-oss-date'] = oss2.utils.http_date(int(time.time()) - 24 * 60 * 60)
        try:
            dest_bucket.list_objects('oss', '/', '', 10, headers=headers)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 403)
            self.assertEqual(e.message, 'The difference between the request time and the current time is too large.')

        dest_bucket.delete_object(key)
        dest_bucket.delete_bucket()

    def test_sign_v2_x_oss_date_url(self):
        auth = oss2.AuthV2(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-sign-v2-url"
        dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name)
        dest_bucket.create_bucket()
        key = 'testexampleobject.txt'
        headers = dict()
        content = 'test example'
        url = dest_bucket.sign_url('PUT', key, 1650801600, headers=headers)
        print(url)

        put_result = dest_bucket.put_object_with_url(url, content)
        self.assertEqual(200, put_result.status)

        headers['x-oss-date'] = oss2.utils.http_date(int(time.time()) + 24 * 60 * 60)
        try:
            dest_bucket.get_object(key, headers=headers)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.status, 403)
            self.assertEqual(e.message, 'The difference between the request time and the current time is too large.')

        dest_bucket.delete_object(key)
        dest_bucket.delete_bucket()

if __name__ == '__main__':
    unittest.main()
