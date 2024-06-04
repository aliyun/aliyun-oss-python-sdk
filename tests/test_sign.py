
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

    def test_sign_key_not_empty(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-sign-v1-url-key-not-empty"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        bucket.create_bucket()
        key = 'testexampleobject.txt'
        headers = dict()
        content = 'test example'
        url = bucket.sign_url('PUT', key, 1650801600, headers=headers)
        print(url)

        try:
            key = None
            bucket.sign_url('PUT', key, 1650801600, headers=headers)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: The key is invalid, please check it.')

        try:
            key = ''
            bucket.sign_url('PUT', key, 1650801600, headers=headers)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: The key is invalid, please check it.')

        bucket.delete_bucket()

    def test_sign_v4_x_oss_date(self):
        auth = oss2.AuthV4(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-sign-v4"
        dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name, region=OSS_REGION)

        try:
            dest_bucket.create_bucket()
            key = 'testexampleobject-v4.txt'

            headers = dict()
            content = 'test example-v4'
            put_result = dest_bucket.put_object(key, content, headers=headers)
            self.assertEqual(200, put_result.status)

            get_result = dest_bucket.get_object(key)
            self.assertEqual(200, get_result.status)

            dest_bucket.list_objects('oss', '/', '', 10, headers=headers)
        except oss2.exceptions.ServerError as e:
            print(e)
            self.assertEqual(e.message, 'Invalid credential in Authorization header.')
        finally:
            dest_bucket.delete_object(key)
            dest_bucket.delete_bucket()
            print("test_sign_v4_x_oss_date end")

    def test_sign_v4_x_oss_date_url(self):
        auth = oss2.AuthV4(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-sign-v4-url"
        dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name, region=OSS_REGION)

        key = 'testexample-v4.txt'
        headers = dict()
        content = 'test example v4'

        try:
            dest_bucket.create_bucket()

            url = dest_bucket.sign_url('PUT', key, 3600, headers=headers)
            print(url)

            put_result = dest_bucket.put_object_with_url(url, content)
            self.assertEqual(200, put_result.status)

            headers2 = dict()
            headers2['x-oss-user'] = 'user-001'
            url2 = dest_bucket.sign_url('PUT', key, 3600, headers=headers2)
            print(url2)

            put_result2 = dest_bucket.put_object_with_url(url2, content, headers=headers2)
            self.assertEqual(200, put_result2.status)

            headers3 = dict()
            get_url = dest_bucket.sign_url('GET', key, 60, headers=headers3)
            print(get_url)

            get_result = dest_bucket.get_object_with_url(get_url, headers=headers3)
            self.assertEqual(200, get_result.status)

            headers4 = dict()
            headers4['x-oss-user'] = 'user-004'
            get_url2 = dest_bucket.sign_url('GET', key, 60, headers=headers4)
            print(get_url2)

            get_result2 = dest_bucket.get_object_with_url(get_url2, headers=headers4)
            self.assertEqual(200, get_result2.status)

            dest_bucket.get_object(key, headers=headers)
        except oss2.exceptions.ServerError as e:
            print(e)
            self.assertEqual(e.message, 'Invalid credential in Authorization header.')
        finally:
            dest_bucket.delete_object(key)
            dest_bucket.delete_bucket()
            print("test_sign_v4_x_oss_date_url end")

    def test_sign_key_is_key_strictly(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = self.OSS_BUCKET + "-sign-v1-is-key-strictly-default"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        bucket.create_bucket()
        key = '123.txt'
        headers = dict()
        content = 'test example'
        url = bucket.sign_url('PUT', key, 1650801600, headers=headers)
        #print(url)

        put_result = bucket.put_object(key, content)
        self.assertEqual(200, put_result.status)

        get_result = bucket.get_object(key)
        self.assertEqual(200, get_result.status)

        del_result = bucket.delete_object(key)
        self.assertEqual(204, del_result.status)

        key = '?123.txt'
        try:
            bucket.sign_url('PUT', key, 1650801600, headers=headers)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: The key cannot start with `?`, please check it.')

        key = '?'
        try:
            bucket.sign_url('PUT', key, 1650801600, headers=headers)
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: The key cannot start with `?`, please check it.')

        bucket.delete_bucket()

        bucket_name = self.OSS_BUCKET + "-sign-v1-is-key-strictly"
        bucket2 = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name, is_verify_object_strict=False)
        bucket2.create_bucket()
        key = '?123.txt'
        url2 = bucket2.sign_url('PUT', key, 1650801600, headers=headers)
        #print(url2)

        put_result2 = bucket2.put_object(key, content)
        self.assertEqual(200, put_result2.status)

        get_result2 = bucket2.get_object(key)
        self.assertEqual(200, get_result2.status)

        del_result2 = bucket2.delete_object(key)
        self.assertEqual(204, del_result2.status)
        bucket2.delete_bucket()

    def test_sign_v2_additional_headers(self):
        auth = oss2.AuthV2(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-additional-header-sign-v2"
        dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name)
        key = 'v4_test.txt'
        additional_key = 'v4_additional_test.txt'

        try:
            dest_bucket.create_bucket()
            headers = dict()
            headers['Content-Length'] = '9'
            headers['custom-header'] = 'abc'
            additional_headers = set()
            additional_headers.add('Content-Length')
            additional_headers.add('custom-header')

            # no additional_headers
            url = dest_bucket.sign_url('PUT', key, 604800, slash_safe=True, headers=headers)
            print(url)
            dest_bucket.put_object_with_url(url, 'Hello OSS', headers=headers)
            get_url = dest_bucket.sign_url('GET', key, 604800, slash_safe=True, headers=headers)
            result = dest_bucket.get_object_with_url(get_url, byte_range=(1, 3), headers=headers)
            self.assertEqual(result.read().decode(), "ell")
            print(result.read().decode())

            # additional_headers
            url = dest_bucket.sign_url('PUT', additional_key, 604800, slash_safe=True, headers=headers, additional_headers=additional_headers)
            print(url)
            dest_bucket.put_object_with_url(url, 'Hello OSS', headers=headers)
            get_url = dest_bucket.sign_url('GET', additional_key, 604800, slash_safe=True, headers=headers, additional_headers=additional_headers)
            result = dest_bucket.get_object_with_url(get_url, byte_range=(2, 3), headers=headers)
            self.assertEqual(result.read().decode(), "ll")
            print(result.read().decode())
        except oss2.exceptions.ServerError as e:
            self.assertFalse(True, "should not get a exception")
        finally:
            dest_bucket.delete_object(key)
            dest_bucket.delete_object(additional_key)
            dest_bucket.delete_bucket()
            print("test_sign_v2_additional_headers end")

    def test_sign_v4_no_region(self):
        auth = oss2.AuthV4(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-region-sign-v4"
        dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name)
        region_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name, region=OSS_REGION)

        # no region
        try:
            dest_bucket.create_bucket()
        except oss2.exceptions.ClientError as e:
            self.assertEqual(e.body, 'ClientError: The region should not be None in signature version 4.')
        finally:
            print("test_sign_v4_no_region end")

        # sign url no region
        try:
            region_bucket.create_bucket()
            headers = dict()
            headers['Content-Length'] = '9'
            url = dest_bucket.sign_url('PUT', 'v4_test.txt', 604800, slash_safe=True, headers=headers)
            dest_bucket.put_object_with_url(url, 'Hello OSS', headers=headers)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.message, 'The signing region in credential is invalid.')
        finally:
            dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name, region=OSS_REGION)
            dest_bucket.delete_bucket()
            print("test_sign_v4_no_region_url end")

    def test_sign_v4_additional_headers(self):
        auth = oss2.AuthV4(OSS_ID, OSS_SECRET)
        dest_bucket_name = self.OSS_BUCKET + "-additional-header-sign-v4"
        dest_bucket = oss2.Bucket(auth, OSS_ENDPOINT, dest_bucket_name, region=OSS_REGION)
        key = 'v4_test.txt'
        additional_key = 'v4_additional_test.txt'

        try:
            dest_bucket.create_bucket()
            headers = dict()
            headers['Content-Length'] = '9'
            headers['custom-header'] = 'abc'
            headers['x-oss-forbid-overwrite'] = 'true'
            additional_headers = set()
            additional_headers.add('Content-Length')
            additional_headers.add('custom-header')
            additional_headers.add('noexist-header')
            additional_headers.add('x-oss-forbid-overwrite')

            # no additional_headers
            url = dest_bucket.sign_url('PUT', key, 604800, slash_safe=True, headers=headers)
            self.assertFalse(url.__contains__('x-oss-additional-headers'))
            dest_bucket.put_object_with_url(url, 'Hello OSS', headers=headers)
            get_url = dest_bucket.sign_url('GET', key, 604800, slash_safe=True, headers=headers)
            self.assertFalse(get_url.__contains__('x-oss-additional-headers'))
            result = dest_bucket.get_object_with_url(get_url, byte_range=(1, 4), headers=headers)
            self.assertEqual(result.read().decode(), "ello")
            print(result.read().decode())

            # additional_headers
            url = dest_bucket.sign_url('PUT', additional_key, 604800, slash_safe=True, headers=headers, additional_headers=additional_headers)
            self.assertTrue(url[url.index("="):].__contains__('x-oss-additional-headers=content-length%3Bcustom-header&'))
            dest_bucket.put_object_with_url(url, 'Hello OSS', headers=headers)
            get_url = dest_bucket.sign_url('GET', additional_key, 604800, slash_safe=True, headers=headers, additional_headers=additional_headers)
            self.assertTrue(get_url[get_url.index("="):].__contains__('x-oss-additional-headers=content-length%3Bcustom-header'))
            result = dest_bucket.get_object_with_url(get_url, byte_range=(2, 4), headers=headers)
            self.assertEqual(result.read().decode(), "llo")
            print(result.read().decode())
        except oss2.exceptions.ServerError as e:
            self.assertFalse(True, "should not get a exception")
        finally:
            dest_bucket.delete_object(key)
            dest_bucket.delete_object(additional_key)
            dest_bucket.delete_bucket()
            print("test_sign_v4_additional_headers end")

if __name__ == '__main__':
    unittest.main()
