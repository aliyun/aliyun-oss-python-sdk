# -*- coding: utf-8 -*-

from .common import *


class TestInit(OssTestCase):

    def test_set_logger(self):
        oss2.set_stream_logger('oss2', logging.DEBUG)
        self.assertTrue(oss2.logger.name, 'oss2')
        self.assertTrue(oss2.logger.level, logging.DEBUG)

        log_file_path = self.random_filename()
        oss2.set_file_logger(log_file_path, 'oss2', logging.INFO)
        self.assertTrue(oss2.logger.name, 'oss2')
        self.assertTrue(oss2.logger.level, logging.INFO)
        oss2.logger.info("hello, oss2")

        with open(log_file_path,'rb') as f:
            self.assertTrue("hello, oss2" in oss2.to_string(f.read()))

        oss2.set_stream_logger('oss2', logging.CRITICAL)
        oss2.set_file_logger(log_file_path, 'oss2', logging.CRITICAL)


if __name__ == '__main__':
    unittest.main()