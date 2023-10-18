# -*- coding: utf-8 -*-
import os
import oss2
import logging
import json

# Specify access information, such as AccessKeyId, AccessKeySecret, and Endpoint.
# You can obtain access information from evironment variables or replace sample values in the code, such as <your AccessKeyId> with actual values.
#
# For example, if your bucket is located in the China (Hangzhou) region, you can set Endpoint to one of the following values:
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com


# access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<yourAccessKeyId>')
# access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<yourAccessKeySecret>')
# bucket_name = os.getenv('OSS_TEST_BUCKET', '<yourBucketName>')
# endpoint = os.getenv('OSS_TEST_ENDPOINT', '<yourEndpoint>')

access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<yourAccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<yourAccessKeySecret>')
endpoint = ''

route = 'test-ap-zxl-process-name-43-1283******516515-opap.oss-cn-beijing-internal.oss-object-process.aliyuncs.com'
token = 'OSSV1#UMoA43+Bi9b6Q1Lu6UjhLXnmq4I/wIFac3uZfBkgJtg2xtHkZJ4bZglDWyOgWRlGTrA8y/i6D9eH8PmAiq2NL2R/MD/UX6zvRhT8WMHUewgc9QWPs9LPHiZytkUZnGa39mnv/73cyPWTuxgxyk4dNhlzEE6U7PdzmCCu8gIrjuYLPrA9psRn0ZC8J2/DCZGVx0BE7AmIJTcNtLKTSjxsJyTts/******'
fwd_status = '200'
content = 'a' * 1024

# Fc function entry
def handler(event, context):

    headers = dict()
    headers['x-oss-fwd-header-Content-Type'] = 'application/octet-stream'
    headers['x-oss-fwd-header-ETag'] = 'testetag'

    logger = logging.getLogger()
    logger.info(event)
    logger.info("enter request")
    evt = json.loads(event)
    event_ctx = evt["getObjectContext"]
    route = event_ctx["outputRoute"]
    token = event_ctx["outputToken"]
    print('outputRoute: '+route)
    print('outputToken: '+token)

    endpoint = route

    service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), endpoint)
    resp = service.write_get_object_response(route, token, fwd_status, content, headers)

    logger.info(resp)
    logger.info("end request")
    return 'success'





