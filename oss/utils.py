import os.path
import mimetypes

_EXTRA_TYPES_MAP = {
    "js": "application/javascript",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xltx": "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
    "potx": "application/vnd.openxmlformats-officedocument.presentationml.template",
    "ppsx": "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "sldx": "application/vnd.openxmlformats-officedocument.presentationml.slide",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
    "xlam": "application/vnd.ms-excel.addin.macroEnabled.12",
    "xlsb": "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
    "apk": "application/vnd.android.package-archive"
}


def content_type_by_name(name):
    ext = os.path.splitext(name)[1].lower()
    if ext in _EXTRA_TYPES_MAP:
        return _EXTRA_TYPES_MAP[ext]

    return mimetypes.guess_type(name)[0]


def case_find(d, key):
    for k, v in d.items():
        if key.lower() == k.lower():
            return k

    return None


def set_content_type(headers, name):
    headers = headers or {}

    key = case_find(headers, 'content-type')
    if key:
        return headers

    content_type = content_type_by_name(name)
    if content_type:
        headers['content-type'] = content_type

    return headers
