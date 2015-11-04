from . models import PartInfo
from .exceptions import NoSuchUpload


class PartsIterator(object):
    def __init__(self, bucket, object_name, upload_id):
        self.bucket = bucket
        self.object_name = object_name
        self.upload_id = upload_id
        self.parts = []

        self.next_marker = ''
        self.is_truncated = True

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self.parts:
                return self.parts.pop(0)

            if not self.is_truncated:
                raise StopIteration

            result = self.bucket.list_parts(self.object_name, self.upload_id, next_marker=self.next_marker)
            self.parts = result.parts
            self.next_marker = result.next_marker
            self.is_truncated = result.is_truncated

    def next(self):
        return self.__next__()


class _SizedStreamReader(object):
    def __init__(self, file_object, size):
        self.file_object = file_object
        self.size = size
        self.offset = 0

    def read(self, amt=None):
        if self.offset >= self.size:
            return ''

        if (amt is None or amt < 0) or (amt + self.offset >= self.size):
            data = self.file_object.read(self.size - self.offset)
            self.offset = self.size
            return data

        self.offset += amt
        return self.file_object.read(amt)

    def __len__(self):
        return self.size


_MAX_PART_COUNT = 10000
_MIN_PART_SIZE = 100 * 1024


def how_many(m, n):
    return (m + n - 1)/n


class ResumableUploader(object):
    def __init__(self, stream, size, part_size, bucket, object_name, upload_id):
        self.stream = stream
        self.size = size
        self.part_size = part_size
        self.bucket = bucket
        self.object_name = object_name
        self.upload_id = upload_id

    def upload(self):
        if self.upload_id:
            self.__resume_upload()
        else:
            self.__new_upload()

    def __upload_and_complete(self, uploaded_parts):
        if uploaded_parts:
            self.part_size = uploaded_parts[0].size

            uploaded_size = sum(p.size for p in uploaded_parts)
            remaining = self.size - uploaded_size
            num_parts = len(uploaded_parts) + how_many(self.size - uploaded_size, self.part_size)
        else:
            remaining = self.size
            num_parts = (self.size + self.part_size - 1)/self.part_size

        for i in xrange(uploaded_parts[-1].part_number+1, num_parts+1):
            if i == num_parts:
                bytes_to_upload = remaining % self.part_size
            else:
                bytes_to_upload = self.part_size

            result = self.bucket.upload_part(self.object_name, self.upload_id, i,
                                             _SizedStreamReader(self.stream, bytes_to_upload))
            uploaded_parts.append(PartInfo(i, result.etag))

        self.bucket.complete_multipart_upload(self.object_name, self.upload_id, uploaded_parts)

    def __new_upload(self):
        self.upload_id = self.bucket.init_multipart_upload(self.object_name).upload_id
        self.__upload_and_complete([])

    def __resume_upload(self):
        assert self.upload_id

        try:
            uploaded_parts = list(PartsIterator(self.bucket, self.object_name, self.upload_id))
        except NoSuchUpload:
            self.upload_id = ''
            self.__new_upload()
            return

        #TODO: mingzai.ym verify uploaded_parts is expected
        self.__upload_and_complete(uploaded_parts)