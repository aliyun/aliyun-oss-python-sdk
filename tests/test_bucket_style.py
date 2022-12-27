from .common import *

class TestBucketStyle(OssTestCase):
    def test_bucket_style_normal(self):
        result = self.bucket.put_bucket_style('imagestyle','image/resize,w_200')
        self.assertEqual(200, result.status)

        get_result = self.bucket.get_bucket_style('imagestyle')
        self.assertEqual('imagestyle', get_result.name)
        self.assertEqual('image/resize,w_200', get_result.content)

        result = self.bucket.put_bucket_style('imagestyle1','image/resize,w_300')
        self.assertEqual(200, result.status)

        list_result = self.bucket.list_bucket_style()
        self.assertEqual('imagestyle', list_result.styles[0].name)
        self.assertEqual('image/resize,w_200', list_result.styles[0].content)
        self.assertEqual('imagestyle1', list_result.styles[1].name)
        self.assertEqual('image/resize,w_300', list_result.styles[1].content)

        del_result = self.bucket.delete_bucket_style('imagestyle')
        self.assertEqual(204, del_result.status)

        del2_result = self.bucket.delete_bucket_style('imagestyle1')
        self.assertEqual(204, del2_result.status)

    def test_bucket_style_exception(self):
        try:
            self.bucket.put_bucket_style('imagestyle','')
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.details['Message'], 'Style content is invalid.')

    def test_bucket_style_exception_style_name(self):
        try:
            self.bucket.put_bucket_style('@%$^&%(&(*(*','image/resize,w_200')
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.details['Code'], 'InvalidArgument')

    def test_bucket_style_content(self):
        self.bucket.put_bucket_style('aaa','csdar5324')
        get_result = self.bucket.get_bucket_style('aaa')
        self.assertEqual('aaa', get_result.name)
        self.assertEqual('csdar5324', get_result.content)

if __name__ == '__main__':
    unittest.main()
