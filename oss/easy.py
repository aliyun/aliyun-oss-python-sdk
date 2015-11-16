# -*- coding: utf-8 -*-

"""
oss.easy
~~~~~~~~

该模块包含了一些易用性接口。一般用户应优先使用这些接口。
"""

import os
import logging

from .models import PartInfo
from .exceptions import NoSuchUpload
from .iterators import PartIterator, ObjectUploadIterator
from . import utils
from oss.utils import _SizedStreamReader, how_many

_MULTIPART_THRESHOLD = 500 * 1024 * 1024

_MAX_PART_COUNT = 10000
_MIN_PART_SIZE = 100 * 1024

_PREFERRED_PART_SIZE = 100 * 1024 * 1024
_PREFERRED_PART_COUNT = 100

