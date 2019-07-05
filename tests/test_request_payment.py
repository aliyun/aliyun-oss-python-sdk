# -*- coding: utf-8 -*-

from .common import *
from oss2.models import PAYER_BUCKETOWNER, PAYER_REQUESTER

class TestRequestPayment(OssTestCase):

    def test_request_payment(self):
        payer = PAYER_REQUESTER

        # test default payer
        result = self.bucket.get_bucket_request_payment()
        self.assertEqual(result.payer, PAYER_BUCKETOWNER)

        # test set request payer
        result = self.bucket.put_bucket_request_payment(payer)
        self.assertEqual(result.status, 200)

        # test get request payer
        result = self.bucket.get_bucket_request_payment()
        self.assertEqual(result.payer, payer)


if __name__ == '__main__':
    unittest.main()