from .common import *

class TestExceptionEC(OssTestCase):
    def setUp(self):
        OssTestCase.setUp(self)

    def tearDown(self):
        try:
            OssTestCase.tearDown(self)
        except:
            pass
    def test_1_exception_normal(self):
        key = 'a.txt'
        try:
            self.bucket.get_object(key)
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.headers.get('x-oss-ec'), '0026-00000001')
            self.assertEqual(e.ec, '0026-00000001')

    def test_2_exception_head(self):
        key = 'a.txt'
        try:
            self.bucket.get_object_meta(key)
        except oss2.exceptions.OssError as e:
            self.assertEqual(e.ec, '0026-00000001')
            self.assertEqual(e.headers.get('x-oss-ec'), '0026-00000001')

if __name__ == '__main__':
    unittest.main()
