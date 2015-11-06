import xml.etree.ElementTree as ElementTree
import urllib
import io

from .models import (SimplifiedObjectInfo,
                     SimplifiedBucketInfo,
                     PartInfo,
                     MultipartUploadInfo)


def _find_tag(parent, path):
    child = parent.find(path)
    if child is None:
        raise KeyError("parse xml: " + path + " could not be found under " + parent.tag)
    return child.text


def _find_bool(parent, path):
    text = _find_tag(parent, path)
    if text == 'true':
        return True
    elif text == 'false':
        return False
    else:
        raise ValueError("parse xml: value of " + path + " is not a boolean under " + parent.tag)


def _find_int(parent, path):
    return int(_find_tag(parent, path))


def _find_object(parent, path, url_encoded):
    name = _find_tag(parent, path)
    if url_encoded:
        return urllib.unquote(name)
    else:
        return name


def _is_url_encoding(root):
    node = root.find('EncodingType')
    if node is not None and node.text == 'url':
        return True
    else:
        return False

#TODO: generalize xml to list k-v interfaces
def parse_error_body(body):
    try:
        root = ElementTree.fromstring(body)
        if root.tag != 'Error':
            return {}

        details = {}
        for child in root:
            details[child.tag] = child.text
        return details
    except ElementTree.ParseError:
        return {}


def parse_list_objects(result, body):
    root = ElementTree.fromstring(body)
    url_encoded = _is_url_encoding(root)

    result.is_truncated = _find_bool(root, 'IsTruncated')
    if result.is_truncated:
        result.next_marker = _find_object(root, 'NextMarker', url_encoded)

    for contents_node in root.findall('Contents'):
        result.object_list.append(SimplifiedObjectInfo(
            _find_object(contents_node, 'Key', url_encoded),
            _find_tag(contents_node, 'LastModified'),
            _find_tag(contents_node, 'ETag').strip('"'),
            _find_tag(contents_node, 'Type'),
            int(_find_tag(contents_node, 'Size'))
        ))

    for prefix_node in root.findall('CommonPrefixes'):
        result.prefix_list.append(_find_object(prefix_node, 'Prefix', url_encoded))

    return result


def parse_list_buckets(result, body):
    root = ElementTree.fromstring(body)

    if not root.find('IsTruncated'):
        result.is_truncated = False
    else:
        result.is_truncated = _find_bool(root, 'IsTruncated')

    if result.is_truncated:
        result.next_marker = _find_tag(root, 'NextMarker')

    for bucket_node in root.findall('Buckets/Bucket'):
        result.buckets.append(SimplifiedBucketInfo(
            _find_tag(bucket_node, 'Name'),
            _find_tag(bucket_node, 'Location'),
            _find_tag(bucket_node, 'CreationDate')
        ))


def parse_init_multipart_upload(result, body):
    root = ElementTree.fromstring(body)
    result.upload_id = _find_tag(root, 'UploadId')

    return result


def parse_list_multipart_uploads(result, body):
    root = ElementTree.fromstring(body)

    url_encoded = _is_url_encoding(root)

    result.is_truncated = _find_bool(root, 'IsTruncated')
    result.next_key_marker = _find_tag(root, 'NextKeyMarker')
    result.next_upload_id_marker = _find_tag('NextUploadIdMarker')

    for upload_node in root.findall('Upload'):
        result.upload_list.append(MultipartUploadInfo(
            _find_object(upload_node, 'Key', url_encoded),
            _find_tag(upload_node, 'UploadId'),
            _find_tag(upload_node, 'Initiated')
        ))

    for prefix_node in root.findall('CommonPrefixes'):
        result.prefix_list.append(_find_object(prefix_node, 'Prefix', url_encoded))

    return result


def parse_list_parts(result, body):
    root = ElementTree.fromstring(body)

    result.is_truncated = _find_bool(root, 'IsTruncated')
    result.next_marker = _find_tag(root, 'NextPartNumberMarker')
    for part_node in root.findall('Part'):
        result.parts.append(PartInfo(
            _find_int(part_node, 'PartNumber'),
            _find_tag(part_node, 'ETag').strip('"'),
            _find_int(part_node, 'Size')
        ))

    return result


def parse_batch_delete_objects(result, body):
    if not body:
        return result

    root = ElementTree.fromstring(body)
    url_encoded = _is_url_encoding(root)

    for deleted_node in root.findall('Deleted'):
        result.object_list.append(_find_object(deleted_node, 'Key', url_encoded))

    return result


def parse_get_bucket_acl(result, body):
    root = ElementTree.fromstring(body)
    result.acl = root.find('AccessControlList/Grant').text.strip()

    return result


def parse_get_bucket_logging(result, body):
    root = ElementTree.fromstring(body)
    result.target_bucket = root.find('LoggingEnabled/TargetBucket').text.strip()
    result.target_prefix = root.find('LoggingEnabled/TargetPrefix').text.strip()

    return result


def _tree_to_string(tree):
    xml = None
    with io.BytesIO(xml) as f:
        tree.write(f, xml_declaration=True)
        xml = f.getvalue()

    return xml


def _make_encoder(encoding_type):
    if encoding_type == 'url':
        return urllib.quote
    else:
        return lambda x: x


def to_complete_upload_request(parts):
    root = ElementTree.Element('CompleteMultipartUpload')
    for p in parts:
        part_node = ElementTree.SubElement(root, "Part")
        ElementTree.SubElement(part_node, 'PartNumber').text = str(p.part_number)
        ElementTree.SubElement(part_node, 'ETag').text = '"{}"'.format(p.etag)

    tree = ElementTree.ElementTree(root)
    return _tree_to_string(tree)


def to_batch_delete_objects_request(objects, quiet, encoding_type):
    encoder = _make_encoder(encoding_type)

    root_node = ElementTree.Element('Delete')

    quiet_node = ElementTree.SubElement(root_node, 'Quiet')
    quiet_node.text = str(quiet).lower()

    for object_name in objects:
        object_node = ElementTree.SubElement(root_node, 'Object')
        ElementTree.SubElement(object_node, 'Key').text = encoder(object_name)

    tree = ElementTree.ElementTree(root_node)
    return _tree_to_string(tree)


def to_put_bucket_logging(target_bucket, target_prefix):
    root = ElementTree.Element('BucketLoggingStatus')

    if target_bucket:
        logging_node = ElementTree.SubElement(root, 'LoggingEnabled')
        ElementTree.SubElement(logging_node, 'TargetBucket').text = target_bucket
        ElementTree.SubElement(logging_node, 'TargetPrefix').text = target_prefix

    tree = ElementTree.ElementTree(root)
    return _tree_to_string(tree)
