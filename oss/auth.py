import hmac
import hashlib
import base64
import time
import logging


class Auth(object):
    subresource_key_set = frozenset(
        ['response-content-type', 'response-content-language',
         'response-cache-control', 'logging', 'response-content-encoding',
         'acl', 'uploadId', 'uploads', 'partNumber', 'group', 'link',
         'delete', 'website', 'location', 'objectInfo',
         'response-expires', 'response-content-disposition', 'cors', 'lifecycle',
          'restore', 'qos', 'referer', 'append', 'position']
    )

    def __init__(self, access_key_id, access_key_secret):
        self.id = access_key_id
        self.secret = access_key_secret

    def sign_request(self, req, bucket_name, object_name):
        req.headers['date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        string_to_sign = self.get_string_to_sign(req, bucket_name, object_name)
        h = hmac.new(self.secret, string_to_sign, hashlib.sha1)
        signature = base64.b64encode(h.digest())
        req.headers['authorization'] = "OSS {}:{}".format(self.id, signature)

        logging.debug("string_to_sign={}".format(repr(string_to_sign)))

    def get_string_to_sign(self, req, bucket_name, object_name):
        resource_string = self.get_resource_string(req, bucket_name, object_name)
        headers_string = self.get_headers_string(req)

        content_md5 = req.headers.get('content-md5', '')
        content_type = req.headers.get('content-type', '')
        date = req.headers.get('date', '')
        return '\n'.join([req.method,
                          content_md5,
                          content_type,
                          date,
                          headers_string + resource_string])

    def get_headers_string(self, req):
        headers = req.headers
        canon_headers = []
        for k, v in headers.items():
            lower_key = k.lower()
            if lower_key.startswith('x-oss-'):
                canon_headers.append((lower_key, v))

        canon_headers.sort(key=lambda x: x[0])

        if canon_headers:
            return '\n'.join(k + ':' + v for k, v in canon_headers) + '\n'
        else:
            return ''

    def get_resource_string(self, req, bucket_name, object_name):
        if not bucket_name:
            return '/'
        else:
            return '/{}/{}{}'.format(bucket_name, object_name, self.get_subresource_string(req.params))

    def get_subresource_string(self, params):
        if not params:
            return ''

        subresource_params = []
        for key, value in params.items():
            if key in self.subresource_key_set:
                subresource_params.append((key, value))

        subresource_params.sort(key=lambda e: e[0])

        if subresource_params:
            return '?' + '&'.join(self.__param_to_query(k, v) for k, v in subresource_params)
        else:
            return ''

    def __param_to_query(self, k, v):
        if v:
            return k + '=' + v
        else:
            return k

