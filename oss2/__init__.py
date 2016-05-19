__version__ = '2.1.1'

from . import models, exceptions

from .api import Service, Bucket
from .auth import Auth, AnonymousAuth, StsAuth
from .http import Session, CaseInsensitiveDict


from .iterators import (BucketIterator, ObjectIterator,
                        MultipartUploadIterator, ObjectUploadIterator,
                        PartIterator, LiveChannelIterator)


from .resumable import resumable_upload, resumable_download, ResumableStore, ResumableDownloadStore, determine_part_size
from .resumable import make_upload_store, make_download_store


from .compat import to_bytes, to_string, to_unicode, urlparse, urlquote, urlunquote

from .utils import SizedFileAdapter, make_progress_adapter
from .utils import content_type_by_name, is_valid_bucket_name
from .utils import http_date, http_to_unixtime, iso8601_to_unixtime, date_to_iso8601, iso8601_to_date


from .models import BUCKET_ACL_PRIVATE, BUCKET_ACL_PUBLIC_READ, BUCKET_ACL_PUBLIC_READ_WRITE
from .models import OBJECT_ACL_DEFAULT, OBJECT_ACL_PRIVATE, OBJECT_ACL_PUBLIC_READ, OBJECT_ACL_PUBLIC_READ_WRITE
