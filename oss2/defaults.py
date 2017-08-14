# -*- coding: utf-8 -*-

"""
oss2.defaults
~~~~~~~~~~~~~

Global Default variables.

"""

import logging


def get(value, default_value):
    if value is None:
        return default_value
    else:
        return value


#: connection timeout
connect_timeout = 60

#: retry count
request_retries = 3

#: The threshold of file size for using multipart upload in some APIs.
multipart_threshold = 10 * 1024 * 1024

#: Default thread count for multipart upload.
multipart_num_threads = 1

#: Default part size.
part_size = 10 * 1024 * 1024


#: Connection pool size for each session.
connection_pool_size = 10


#: The threshold of file size for using multipart download (multiget) in some APIs.
multiget_threshold = 100 * 1024 * 1024

#: Default thread count for multipart download (multiget)
multiget_num_threads = 4

#: Default part size in multipart download (multiget)
multiget_part_size = 10 * 1024 * 1024

#: Default Logger
logger = logging.getLogger()


def get_logger():
    return logger
