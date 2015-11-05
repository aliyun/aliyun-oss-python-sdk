from . import xml_utils
from . import http
from . import utils

from .exceptions import make_exception

from .models import (RequestResult,
                     ListObjectsResult,
                     GetObjectResult,
                     PutObjectResult,
                     BucketResult,
                     ListBucketsResult,
                     InitMultipartUploadResult,
                     ListPartsResult,
                     ListMultipartUploadsResult)

import urlparse


class _Base(object):
    def __init__(self, auth, endpoint, is_cname, session):
        self.auth = auth
        self.endpoint = _normalize_endpoint(endpoint)
        self.session = session or http.Session()

        self._make_url = _UrlMaker(self.endpoint, is_cname)

    def _do(self, method, bucket_name, object_name, **kwargs):
        req = http.Request(method, self._make_url(bucket_name, object_name), **kwargs)
        self.auth.sign_request(req, bucket_name, object_name)

        resp = self.session.do_request(req)
        if resp.status / 100 != 2:
            raise make_exception(resp)

        return resp


class Service(_Base):
    def __init__(self, auth, endpoint,
                 session=None):
        super(Service, self).__init__(auth, endpoint, False, session)

    def list_buckets(self, prefix='', marker='', max_keys=100):
        resp = self._do('GET', '', '',
                        params={'prefix': prefix,
                                'marker': marker,
                                'max-keys': max_keys})
        result = ListBucketsResult(resp)
        xml_utils.parse_list_buckets(result, resp.read())
        return result


class Bucket(_Base):
    def __init__(self, auth, endpoint, bucket_name,
                 is_cname=False,
                 session=None):
        super(Bucket, self).__init__(auth, endpoint, is_cname, session)
        self.bucket_name = bucket_name

    def list_objects(self, prefix='', delimiter='', marker='', max_keys=100):
        resp = self.__do_object('GET', '',
                                params={'prefix': prefix,
                                        'delimiter': delimiter,
                                        'marker': marker,
                                        'max-keys': max_keys,
                                        'encoding-type': 'url'})
        result = ListObjectsResult(resp)
        return xml_utils.parse_list_objects(result, resp.read())

    def put_object(self, object_name, data, headers=None):
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), object_name)

        resp = self.__do_object('PUT', object_name, data=data, headers=headers)
        return PutObjectResult(resp)

    def get_object(self, object_name, headers=None):
        resp = self.__do_object('GET', object_name, headers=headers)
        return GetObjectResult(resp)

    def delete_object(self, object_name, headers=None):
        resp = self.__do_object('DELETE', object_name, headers=headers)
        return RequestResult(resp)

    def init_multipart_upload(self, object_name, headers=None):
        headers = utils.set_content_type(http.CaseInsensitiveDict(headers), object_name)

        resp = self.__do_object('POST', object_name, params={'uploads': ''}, headers=headers)
        result = InitMultipartUploadResult(resp)
        return xml_utils.parse_init_multipart_upload(result, resp.read())

    def upload_part(self, object_name, upload_id, part_number, data, headers=None):
        resp = self.__do_object('PUT', object_name,
                                params={'uploadId': upload_id, 'partNumber': str(part_number)},
                                data=data,
                                headers=headers)
        return PutObjectResult(resp)

    def complete_multipart_upload(self, object_name, upload_id, parts, headers=None):
        data = xml_utils.to_complete_upload_request(parts)
        resp = self.__do_object('POST', object_name,
                                params={'uploadId': upload_id},
                                data=data,
                                headers=headers)
        return PutObjectResult(resp)

    def abort_multipart_upload(self, object_name, upload_id, headers=None):
        resp = self.__do_object('DELETE', object_name,
                                params={'uploadId': upload_id},
                                headers=headers)
        return RequestResult(resp)

    def list_multipart_uploads(self,
                               prefix='',
                               delimiter='',
                               key_marker='',
                               upload_id_marker='',
                               max_uploads=1000):
        resp = self.__do_object('GET',
                                params={'uploads': '',
                                        'prefix': prefix,
                                        'delimiter': delimiter,
                                        'key-marker': key_marker,
                                        'upload-id-marker': upload_id_marker,
                                        'max-uploads': max_uploads,
                                        'encoding-type': 'url'})
        result = ListMultipartUploadsResult(resp)
        return xml_utils.parse_list_multipart_uploads(result, resp.read())

    def list_parts(self, object_name, upload_id,
                   marker=''):
        resp = self.__do_object('GET', object_name,
                                params={'uploadId': upload_id, 'part-number-marker': marker})
        result = ListPartsResult(resp)
        return xml_utils.parse_list_parts(result, resp.read())

    def create_bucket(self, permission):
        resp = self.__do_bucket('PUT', headers={'x-oss-acl': permission})
        return RequestResult(resp)

    def delete_bucket(self):
        resp = self.__do_bucket('DELETE')
        return RequestResult(resp)

    def put_lifecycle(self, data):
        resp = self.__do_bucket('PUT', params={'lifecycle': ''}, data=data)
        return RequestResult(resp)

    def get_lifecycle(self):
        resp = self.__do_bucket('GET', params={'lifecycle': ''})
        return BucketResult(resp)

    def delete_lifecycle(self):
        resp = self.__do_bucket('DELETE', params={'lifecycle': ''})
        return RequestResult(resp)

    def __do_object(self, method, object_name, **kwargs):
        return self._do(method, self.bucket_name, object_name, **kwargs)

    def __do_bucket(self, method, **kwargs):
        return self._do(method, self.bucket_name, '', **kwargs)


def _normalize_endpoint(endpoint):
    if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
        return 'http://' + endpoint
    else:
        return endpoint


#TODO: mingzai.ym make it better?
def _is_ip(s):
    tmp_list = s.split(':')
    s = tmp_list[0]
    if s == 'localhost':
        return True
    tmp_list = s.split('.')
    if len(tmp_list) != 4:
        return False
    else:
        for i in tmp_list:
            if int(i) < 0 or int(i) > 255:
                return False
    return True

_ENDPOINT_TYPE_ALIYUN = 0
_ENDPOINT_TYPE_CNAME = 1
_ENDPOINT_TYPE_IP = 2


def _determine_endpoint_type(netloc, is_cname):
    if _is_ip(netloc):
        return _ENDPOINT_TYPE_IP

    if is_cname:
        return _ENDPOINT_TYPE_CNAME
    else:
        return _ENDPOINT_TYPE_ALIYUN


class _UrlMaker(object):
    def __init__(self, endpoint, is_cname):
        p = urlparse.urlparse(endpoint)

        self.scheme = p.scheme
        self.netloc = p.netloc
        self.type = _determine_endpoint_type(p.netloc, is_cname)

    def __call__(self, bucket_name, object_name):
        if self.type == _ENDPOINT_TYPE_CNAME:
            return '{}://{}/{}'.format(self.scheme, self.netloc, object_name)

        if self.type == _ENDPOINT_TYPE_IP:
            assert bucket_name
            return '{}://{}/{}/{}'.format(self.scheme, self.netloc, bucket_name, object_name)

        if not bucket_name:
            assert not object_name
            return '{}://{}'.format(self.scheme, self.netloc)

        return '{}://{}.{}/{}'.format(self.scheme, bucket_name, self.netloc, object_name)
