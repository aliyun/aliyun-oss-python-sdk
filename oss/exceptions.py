from .result import ErrorResult

_OSS_ERROR_TO_EXCEPTION = {} # populated at end of module


class OssError(Exception):
    def __init__(self, result):
        super(OssError, self).__init__()
        self.result = result

    def __str__(self):
        return repr(self.result)


class NoSuchBucket(OssError):
    status = 404
    code = 'NoSuchBucket'


class NoSuchKey(OssError):
    status = 404
    code = 'NoSuchKey'


def make_exception(resp):
    assert resp.status / 100 != 2

    result = ErrorResult(resp)

    try:
        klass = _OSS_ERROR_TO_EXCEPTION[(result.status, result.code)]
        return klass(result)
    except KeyError:
        return OssError(result)


def _walk_subclasses(klass):
    for sub in klass.__subclasses__():
        yield sub
        for subsub in _walk_subclasses(sub):
            yield subsub


for klass in _walk_subclasses(OssError):
    status = getattr(klass, 'status', None)
    code = getattr(klass, 'code', None)

    if status is not None and code is not None:
        _OSS_ERROR_TO_EXCEPTION[(status, code)] = klass
