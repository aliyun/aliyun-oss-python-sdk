# -*- coding: utf-8 -*-

import hmac
import hashlib
import time

from . import utils
from .compat import urlquote, to_bytes

from .defaults import get_logger


class Auth(object):
    """Store user's AccessKeyId、AccessKeySecret information and calcualte the signature"""

    _subresource_key_set = frozenset(
        ['response-content-type', 'response-content-language',
         'response-cache-control', 'logging', 'response-content-encoding',
         'acl', 'uploadId', 'uploads', 'partNumber', 'group', 'link',
         'delete', 'website', 'location', 'objectInfo', 'objectMeta',
         'response-expires', 'response-content-disposition', 'cors', 'lifecycle',
         'restore', 'qos', 'referer', 'append', 'position', 'security-token',
         'live', 'comp', 'status', 'vod', 'startTime', 'endTime', 'x-oss-process',
         'symlink']
    )

    def __init__(self, access_key_id, access_key_secret):
        self.id = access_key_id.strip()
        self.secret = access_key_secret.strip()

    def _sign_request(self, req, bucket_name, key):
        req.headers['date'] = utils.http_date()

        signature = self.__make_signature(req, bucket_name, key)
        req.headers['authorization'] = "OSS {0}:{1}".format(self.id, signature)

    def _sign_url(self, req, bucket_name, key, expires):
        expiration_time = int(time.time()) + expires

        req.headers['date'] = str(expiration_time)
        signature = self.__make_signature(req, bucket_name, key)

        req.params['OSSAccessKeyId'] = self.id
        req.params['Expires'] = str(expiration_time)
        req.params['Signature'] = signature

        return req.url + '?' + '&'.join(_param_to_quoted_query(k, v) for k, v in req.params.items())

    def __make_signature(self, req, bucket_name, key):
        string_to_sign = self.__get_string_to_sign(req, bucket_name, key)

        get_logger().debug('string_to_sign={0}'.format(string_to_sign))

        h = hmac.new(to_bytes(self.secret), to_bytes(string_to_sign), hashlib.sha1)
        return utils.b64encode_as_string(h.digest())

    def __get_string_to_sign(self, req, bucket_name, key):
        resource_string = self.__get_resource_string(req, bucket_name, key)
        headers_string = self.__get_headers_string(req)

        content_md5 = req.headers.get('content-md5', '')
        content_type = req.headers.get('content-type', '')
        date = req.headers.get('date', '')
        return '\n'.join([req.method,
                          content_md5,
                          content_type,
                          date,
                          headers_string + resource_string])

    def __get_headers_string(self, req):
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

    def __get_resource_string(self, req, bucket_name, key):
        if not bucket_name:
            return '/'
        else:
            return '/{0}/{1}{2}'.format(bucket_name, key, self.__get_subresource_string(req.params))

    def __get_subresource_string(self, params):
        if not params:
            return ''

        subresource_params = []
        for key, value in params.items():
            if key in self._subresource_key_set:
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

    def _sign_rtmp_url(self, url, bucket_name, channel_name, playlist_name, expires, params):
        expiration_time = int(time.time()) + expires

        canonicalized_resource = "/%s/%s" % (bucket_name, channel_name)
        canonicalized_params = []
        
        if params:
            items = params.items()
            for k,v in items:
                if k != "OSSAccessKeyId" and k != "Signature" and k!= "Expires" and k!= "SecurityToken":
                    canonicalized_params.append((k, v))
                    
        canonicalized_params.sort(key=lambda e: e[0]) 
        canon_params_str = ''
        for k, v in canonicalized_params:
            canon_params_str += '%s:%s\n' % (k, v)
        
        p = params if params else {}
        string_to_sign = str(expiration_time) + "\n" + canon_params_str + canonicalized_resource
        get_logger().debug('string_to_sign={0}'.format(string_to_sign))
        
        h = hmac.new(to_bytes(self.secret), to_bytes(string_to_sign), hashlib.sha1)
        signature = utils.b64encode_as_string(h.digest())

        p['OSSAccessKeyId'] = self.id
        p['Expires'] = str(expiration_time)
        p['Signature'] = signature

        return url + '?' + '&'.join(_param_to_quoted_query(k, v) for k, v in p.items())
    

class AnonymousAuth(object):
    """Anonymous Auth

    .. note::
        Anonymous auth can only read bucket with public-read permission, or read/write bucket with public-read-write permissions.
        It cannot execute service or bucket related operations(e.g. add a new bucket or list files under a bucket).
    """
    def _sign_request(self, req, bucket_name, key):
        pass

    def _sign_url(self, req, bucket_name, key, expires):
        return req.url + '?' + '&'.join(_param_to_quoted_query(k, v) for k, v in req.params.items())
    
    def _sign_rtmp_url(self, url, bucket_name, channel_name, playlist_name, expires, params):
        return url + '?' + '&'.join(_param_to_quoted_query(k, v) for k, v in params.items())
        

class StsAuth(object):
    """For STS Auth. User could get the AccessKeyId, AccessKeySecret and SecurityToken from the AliCloud's STS service (https://sts.aliyuncs.com)

    Note that the AccessKeyId/Secret and SecurtyToken has the expiration time. Once they're renewed, the STSAuth property in class Bucket instance needs 
    to be updated with the new credentials.

    :param str access_key_id: 临时AccessKeyId
    :param str access_key_secret: 临时AccessKeySecret
    :param str security_token: 临时安全令牌(SecurityToken)
    """
    def __init__(self, access_key_id, access_key_secret, security_token):
        self.__auth = Auth(access_key_id, access_key_secret)
        self.__security_token = security_token

    def _sign_request(self, req, bucket_name, key):
        req.headers['x-oss-security-token'] = self.__security_token
        self.__auth._sign_request(req, bucket_name, key)

    def _sign_url(self, req, bucket_name, key, expires):
        req.params['security-token'] = self.__security_token
        return self.__auth._sign_url(req, bucket_name, key, expires)
    
    def _sign_rtmp_url(self, url, bucket_name, channel_name, playlist_name, expires, params):
        params['security-token'] = self.__security_token
        return self.__auth._sign_rtmp_url(url, bucket_name, channel_name, playlist_name, expires, params)


def _param_to_quoted_query(k, v):
    if v:
        return urlquote(k, '') + '=' + urlquote(v, '')
    else:
        return urlquote(k, '')
