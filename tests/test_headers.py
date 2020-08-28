# -*- coding: utf-8 -*-

from .common import *
from oss2.headers import *


class TestHeaders(OssTestCase):
    def test_check_requestHeader(self):
        myHeader = RequestHeader()
        
        myHeader.set_server_side_encryption(algorithm="AES256")
        self.assertEqual(myHeader["x-oss-server-side-encryption"], "AES256")

        myHeader.set_server_side_encryption(algorithm='KMS')
        self.assertEqual(myHeader["x-oss-server-side-encryption"], "KMS")
        self.assertTrue("x-oss-server-side-encryption-key-id" not in myHeader)

        myHeader.set_server_side_encryption(algorithm="KMS", cmk_id="1111")
        self.assertEqual(myHeader["x-oss-server-side-encryption"], "KMS")
        self.assertEqual(myHeader["x-oss-server-side-encryption-key-id"], "1111")

        myHeader.set_server_side_encryption(algorithm="aaa")
        self.assertTrue("x-oss-server-side-encryption" not in myHeader)
        self.assertTrue("x-oss-server-side-encryption-key-id" not in myHeader)


if __name__ == '__main__':
    unittest.main()