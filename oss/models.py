import xml_utils


class PartInfo(object):
    def __init__(self, part_number, etag, size=None):
        self.part_number = part_number
        self.etag = etag
        self.size = size


class RequestResult(object):
    def __init__(self, resp):
        self.resp = resp
        self.status = resp.status
        self.request_id = resp.headers['x-oss-request-id']


class ErrorResult(RequestResult):
    def __init__(self, resp):
        super(ErrorResult, self).__init__(resp)
        self.details = xml_utils.parse_error_body(resp.read(4096))
        self.code = self.details.get('Code', '')
        self.message = self.details.get('Message', '')

    def __repr__(self):
        return repr(self.details)


class GetObjectResult(RequestResult):
    def __init__(self, resp):
        super(GetObjectResult, self).__init__(resp)

    def read(self, amt=None):
        return self.resp.read(amt)


class PutObjectResult(RequestResult):
    def __init__(self, resp):
        super(PutObjectResult, self).__init__(resp)
        self.etag = resp.headers['etag'].strip('"')


class InitMultipartUploadResult(RequestResult):
    def __init__(self, resp):
        super(InitMultipartUploadResult, self).__init__(resp)
        self.upload_id = None


class ListObjectsResult(RequestResult):
    def __init__(self, resp):
        super(ListObjectsResult, self).__init__(resp)
        self.is_truncated = False
        self.next_marker = ''
        self.object_list = []
        self.prefix_list = []


class SimplifiedObjectInfo(object):
    def __init__(self, name, last_modified, etag, type, size):
        self.name = name
        self.last_modified = last_modified
        self.etag = etag
        self.type = type
        self.size = size


class BucketResult(RequestResult):
    def __init__(self, resp):
        super(BucketResult, self).__init__(resp)
        self.data = resp.read()


class SimplifiedBucketInfo(object):
    def __init__(self, name, location, creation_date):
        self.name = name
        self.location = location
        self.creation_date = creation_date


class ListBucketsResult(RequestResult):
    def __init__(self, resp):
        super(ListBucketsResult, self).__init__(resp)
        self.is_truncated = False
        self.next_marker = ''
        self.buckets = []


class ListPartsResult(RequestResult):
    def __init__(self, resp):
        super(ListPartsResult, self).__init__(resp)
        self.is_truncated = False
        self.next_marker = ''
        self.parts = []