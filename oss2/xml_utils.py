# -*- coding: utf-8 -*-

"""
oss2.xml_utils
~~~~~~~~~~~~~~

XML处理相关。

主要包括两类接口：
    - parse_开头的函数：用来解析服务器端返回的XML
    - to_开头的函数：用来生成发往服务器端的XML

"""
import logging
import xml.etree.ElementTree as ElementTree

from .models import (SimplifiedObjectInfo,
                     SimplifiedBucketInfo,
                     PartInfo,
                     MultipartUploadInfo,
                     LifecycleRule,
                     LifecycleExpiration,
                     CorsRule,
                     LiveChannelInfoTarget,
                     LiveChannelInfo,
                     LiveRecord,
                     LiveChannelVideoStat,
                     LiveChannelAudioStat,
                     Owner,
                     AccessControlList,
                     AbortMultipartUpload,
                     StorageTransition)

from .compat import urlunquote, to_unicode, to_string
from .utils import iso8601_to_unixtime, date_to_iso8601, iso8601_to_date
from . import utils
import base64

logger = logging.getLogger(__name__)

def _find_tag(parent, path):
    child = parent.find(path)
    if child is None:
        raise RuntimeError("parse xml: " + path + " could not be found under " + parent.tag)

    if child.text is None:
        return ''

    return to_string(child.text)


def _find_bool(parent, path):
    text = _find_tag(parent, path)
    if text == 'true':
        return True
    elif text == 'false':
        return False
    else:
        raise RuntimeError("parse xml: value of " + path + " is not a boolean under " + parent.tag)


def _find_int(parent, path):
    return int(_find_tag(parent, path))


def _find_object(parent, path, url_encoded):
    name = _find_tag(parent, path)
    if url_encoded:
        return urlunquote(name)
    else:
        return name


def _find_all_tags(parent, tag):
    return [to_string(node.text) or '' for node in parent.findall(tag)]


def _is_url_encoding(root):
    node = root.find('EncodingType')
    if node is not None and to_string(node.text) == 'url':
        return True
    else:
        return False


def _node_to_string(root):
    return ElementTree.tostring(root, encoding='utf-8')


def _add_node_list(parent, tag, entries):
    for e in entries:
        _add_text_child(parent, tag, e)


def _add_text_child(parent, tag, text):
    ElementTree.SubElement(parent, tag).text = to_unicode(text)

def _add_node_child(parent, tag):
    return ElementTree.SubElement(parent, tag)

def parse_list_objects(result, body):
    root = ElementTree.fromstring(body)
    url_encoded = _is_url_encoding(root)
    result.is_truncated = _find_bool(root, 'IsTruncated')
    if result.is_truncated:
        result.next_marker = _find_object(root, 'NextMarker', url_encoded)

    for contents_node in root.findall('Contents'):
        result.object_list.append(SimplifiedObjectInfo(
            _find_object(contents_node, 'Key', url_encoded),
            iso8601_to_unixtime(_find_tag(contents_node, 'LastModified')),
            _find_tag(contents_node, 'ETag').strip('"'),
            _find_tag(contents_node, 'Type'),
            int(_find_tag(contents_node, 'Size')),
            _find_tag(contents_node, 'StorageClass')
        ))

    for prefix_node in root.findall('CommonPrefixes'):
        result.prefix_list.append(_find_object(prefix_node, 'Prefix', url_encoded))

    return result


def parse_list_buckets(result, body):
    root = ElementTree.fromstring(body)

    if root.find('IsTruncated') is None:
        result.is_truncated = False
    else:
        result.is_truncated = _find_bool(root, 'IsTruncated')

    if result.is_truncated:
        result.next_marker = _find_tag(root, 'NextMarker')

    for bucket_node in root.findall('Buckets/Bucket'):
        result.buckets.append(SimplifiedBucketInfo(
            _find_tag(bucket_node, 'Name'),
            _find_tag(bucket_node, 'Location'),
            iso8601_to_unixtime(_find_tag(bucket_node, 'CreationDate')),
            _find_tag(bucket_node, 'ExtranetEndpoint'),
            _find_tag(bucket_node, 'IntranetEndpoint'),
            _find_tag(bucket_node, 'StorageClass')
        ))

    return result


def parse_init_multipart_upload(result, body):
    root = ElementTree.fromstring(body)
    result.upload_id = _find_tag(root, 'UploadId')

    return result


def parse_list_multipart_uploads(result, body):
    root = ElementTree.fromstring(body)

    url_encoded = _is_url_encoding(root)

    result.is_truncated = _find_bool(root, 'IsTruncated')
    result.next_key_marker = _find_object(root, 'NextKeyMarker', url_encoded)
    result.next_upload_id_marker = _find_tag(root, 'NextUploadIdMarker')

    for upload_node in root.findall('Upload'):
        result.upload_list.append(MultipartUploadInfo(
            _find_object(upload_node, 'Key', url_encoded),
            _find_tag(upload_node, 'UploadId'),
            iso8601_to_unixtime(_find_tag(upload_node, 'Initiated'))
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
            size=_find_int(part_node, 'Size'),
            last_modified=iso8601_to_unixtime(_find_tag(part_node, 'LastModified'))
        ))

    return result


def parse_batch_delete_objects(result, body):
    if not body:
        return result

    root = ElementTree.fromstring(body)
    url_encoded = _is_url_encoding(root)

    for deleted_node in root.findall('Deleted'):
        result.deleted_keys.append(_find_object(deleted_node, 'Key', url_encoded))

    return result


def parse_get_bucket_acl(result, body):
    root = ElementTree.fromstring(body)
    result.acl = _find_tag(root, 'AccessControlList/Grant')

    return result


def parse_get_object_acl(result, body):
    root = ElementTree.fromstring(body)
    result.acl = _find_tag(root, 'AccessControlList/Grant')

    return result


def parse_get_bucket_location(result, body):
    result.location = to_string(ElementTree.fromstring(body).text)
    return result


def parse_get_bucket_logging(result, body):
    root = ElementTree.fromstring(body)

    if root.find('LoggingEnabled/TargetBucket') is not None:
        result.target_bucket = _find_tag(root, 'LoggingEnabled/TargetBucket')

    if root.find('LoggingEnabled/TargetPrefix') is not None:
        result.target_prefix = _find_tag(root, 'LoggingEnabled/TargetPrefix')

    return result


def parse_get_bucket_stat(result, body):
    root = ElementTree.fromstring(body)

    result.storage_size_in_bytes = _find_int(root, 'Storage')
    result.object_count = _find_int(root, 'ObjectCount')
    result.multi_part_upload_count = _find_int(root, 'MultipartUploadCount')

    return result


def parse_get_bucket_info(result, body):
    root = ElementTree.fromstring(body)

    result.name = _find_tag(root, 'Bucket/Name')
    result.creation_date = _find_tag(root, 'Bucket/CreationDate')
    result.storage_class = _find_tag(root, 'Bucket/StorageClass')
    result.extranet_endpoint = _find_tag(root, 'Bucket/ExtranetEndpoint')
    result.intranet_endpoint = _find_tag(root, 'Bucket/IntranetEndpoint')
    result.location = _find_tag(root, 'Bucket/Location')
    result.owner = Owner(_find_tag(root, 'Bucket/Owner/DisplayName'), _find_tag(root, 'Bucket/Owner/ID'))
    result.acl = AccessControlList(_find_tag(root, 'Bucket/AccessControlList/Grant'))

    return result


def parse_get_bucket_referer(result, body):
    root = ElementTree.fromstring(body)

    result.allow_empty_referer = _find_bool(root, 'AllowEmptyReferer')
    result.referers = _find_all_tags(root, 'RefererList/Referer')

    return result


def parse_get_bucket_websiste(result, body):
    root = ElementTree.fromstring(body)

    result.index_file = _find_tag(root, 'IndexDocument/Suffix')
    result.error_file = _find_tag(root, 'ErrorDocument/Key')

    return result


def parse_create_live_channel(result, body):
    root = ElementTree.fromstring(body)

    result.play_url = _find_tag(root, 'PlayUrls/Url')
    result.publish_url = _find_tag(root, 'PublishUrls/Url')

    return result


def parse_get_live_channel(result, body):
    root = ElementTree.fromstring(body)

    result.status = _find_tag(root, 'Status')
    result.description = _find_tag(root, 'Description')

    target = LiveChannelInfoTarget()
    target.type = _find_tag(root, 'Target/Type')
    target.frag_duration = _find_tag(root, 'Target/FragDuration')
    target.frag_count = _find_tag(root, 'Target/FragCount')
    target.playlist_name = _find_tag(root, 'Target/PlaylistName')

    result.target = target

    return result


def parse_list_live_channel(result, body):
    root = ElementTree.fromstring(body)

    result.prefix = _find_tag(root, 'Prefix')
    result.marker = _find_tag(root, 'Marker')
    result.max_keys = _find_int(root, 'MaxKeys')
    result.is_truncated = _find_bool(root, 'IsTruncated')
    
    if result.is_truncated:
        result.next_marker = _find_tag(root, 'NextMarker')

    channels = root.findall('LiveChannel')
    for channel in channels:
        tmp = LiveChannelInfo()
        tmp.name = _find_tag(channel, 'Name')
        tmp.description = _find_tag(channel, 'Description')
        tmp.status = _find_tag(channel, 'Status')
        tmp.last_modified = iso8601_to_unixtime(_find_tag(channel, 'LastModified'))
        tmp.play_url = _find_tag(channel, 'PlayUrls/Url')
        tmp.publish_url = _find_tag(channel, 'PublishUrls/Url')

        result.channels.append(tmp)

    return result


def parse_stat_video(video_node, video):
    video.width = _find_int(video_node, 'Width')
    video.height = _find_int(video_node, 'Height')
    video.frame_rate = _find_int(video_node, 'FrameRate')
    video.bandwidth = _find_int(video_node, 'Bandwidth')
    video.codec = _find_tag(video_node, 'Codec')


def parse_stat_audio(audio_node, audio):
    audio.bandwidth = _find_int(audio_node, 'Bandwidth')
    audio.sample_rate = _find_int(audio_node, 'SampleRate')
    audio.codec = _find_tag(audio_node, 'Codec')


def parse_live_channel_stat(result, body):
    root = ElementTree.fromstring(body)

    result.status = _find_tag(root, 'Status')
    if root.find('RemoteAddr') is not None:
        result.remote_addr = _find_tag(root, 'RemoteAddr')
    if root.find('ConnectedTime') is not None:
        result.connected_time = iso8601_to_unixtime(_find_tag(root, 'ConnectedTime'))

    video_node = root.find('Video')
    audio_node = root.find('Audio')

    if video_node is not None:
        result.video = LiveChannelVideoStat()
        parse_stat_video(video_node, result.video)
    if audio_node is not None:
        result.audio = LiveChannelAudioStat()
        parse_stat_audio(audio_node, result.audio)

    return result


def parse_live_channel_history(result, body):
    root = ElementTree.fromstring(body)

    records = root.findall('LiveRecord')
    for record in records:
        tmp = LiveRecord()
        tmp.start_time = iso8601_to_unixtime(_find_tag(record, 'StartTime'))
        tmp.end_time = iso8601_to_unixtime(_find_tag(record, 'EndTime'))
        tmp.remote_addr = _find_tag(record, 'RemoteAddr')
        result.records.append(tmp)

    return result


def parse_lifecycle_expiration(expiration_node):
    if expiration_node is None:
        return None

    expiration = LifecycleExpiration()

    if expiration_node.find('Days') is not None:
        expiration.days = _find_int(expiration_node, 'Days')
    elif expiration_node.find('Date') is not None:
        expiration.date = iso8601_to_date(_find_tag(expiration_node, 'Date'))

    return expiration


def parse_lifecycle_abort_multipart_upload(abort_multipart_upload_node):
    if abort_multipart_upload_node is None:
        return None
    abort_multipart_upload = AbortMultipartUpload()

    if abort_multipart_upload_node.find('Days') is not None:
        abort_multipart_upload.days = _find_int(abort_multipart_upload_node, 'Days')
    elif abort_multipart_upload_node.find('CreatedBeforeDate') is not None:
        abort_multipart_upload.created_before_date = iso8601_to_date(_find_tag(abort_multipart_upload_node,
                                                                               'CreatedBeforeDate'))
    return abort_multipart_upload


def parse_lifecycle_storage_transitions(storage_transition_nodes):
    storage_transitions = []
    for storage_transition_node in storage_transition_nodes:
        storage_class = _find_tag(storage_transition_node, 'StorageClass')
        storage_transition = StorageTransition(storage_class=storage_class)
        if storage_transition_node.find('Days') is not None:
            storage_transition.days = _find_int(storage_transition_node, 'Days')
        elif storage_transition_node.find('CreatedBeforeDate') is not None:
            storage_transition.created_before_date = iso8601_to_date(_find_tag(storage_transition_node,
                                                                               'CreatedBeforeDate'))

        storage_transitions.append(storage_transition)

    return storage_transitions


def parse_get_bucket_lifecycle(result, body):
    root = ElementTree.fromstring(body)

    for rule_node in root.findall('Rule'):
        expiration = parse_lifecycle_expiration(rule_node.find('Expiration'))
        abort_multipart_upload = parse_lifecycle_abort_multipart_upload(rule_node.find('AbortMultipartUpload'))
        storage_transitions = parse_lifecycle_storage_transitions(rule_node.findall('Transition'))
        rule = LifecycleRule(
            _find_tag(rule_node, 'ID'),
            _find_tag(rule_node, 'Prefix'),
            status=_find_tag(rule_node, 'Status'),
            expiration=expiration,
            abort_multipart_upload=abort_multipart_upload,
            storage_transitions=storage_transitions
            )
        result.rules.append(rule)

    return result


def parse_get_bucket_cors(result, body):
    root = ElementTree.fromstring(body)

    for rule_node in root.findall('CORSRule'):
        rule = CorsRule()
        rule.allowed_origins = _find_all_tags(rule_node, 'AllowedOrigin')
        rule.allowed_methods = _find_all_tags(rule_node, 'AllowedMethod')
        rule.allowed_headers = _find_all_tags(rule_node, 'AllowedHeader')
        rule.expose_headers = _find_all_tags(rule_node, 'ExposeHeader')

        max_age_node = rule_node.find('MaxAgeSeconds')
        if max_age_node is not None:
            rule.max_age_seconds = int(max_age_node.text)

        result.rules.append(rule)

    return result


def to_complete_upload_request(parts):
    root = ElementTree.Element('CompleteMultipartUpload')
    for p in parts:
        part_node = ElementTree.SubElement(root, "Part")
        _add_text_child(part_node, 'PartNumber', str(p.part_number))
        _add_text_child(part_node, 'ETag', '"{0}"'.format(p.etag))

    return _node_to_string(root)


def to_batch_delete_objects_request(keys, quiet):
    root_node = ElementTree.Element('Delete')

    _add_text_child(root_node, 'Quiet', str(quiet).lower())

    for key in keys:
        object_node = ElementTree.SubElement(root_node, 'Object')
        _add_text_child(object_node, 'Key', key)

    return _node_to_string(root_node)


def to_put_bucket_config(bucket_config):
    root = ElementTree.Element('CreateBucketConfiguration')

    _add_text_child(root, 'StorageClass', str(bucket_config.storage_class))

    return _node_to_string(root)


def to_put_bucket_logging(bucket_logging):
    root = ElementTree.Element('BucketLoggingStatus')

    if bucket_logging.target_bucket:
        logging_node = ElementTree.SubElement(root, 'LoggingEnabled')
        _add_text_child(logging_node, 'TargetBucket', bucket_logging.target_bucket)
        _add_text_child(logging_node, 'TargetPrefix', bucket_logging.target_prefix)

    return _node_to_string(root)


def to_put_bucket_referer(bucket_referer):
    root = ElementTree.Element('RefererConfiguration')

    _add_text_child(root, 'AllowEmptyReferer', str(bucket_referer.allow_empty_referer).lower())
    list_node = ElementTree.SubElement(root, 'RefererList')

    for r in bucket_referer.referers:
        _add_text_child(list_node, 'Referer', r)

    return _node_to_string(root)


def to_put_bucket_website(bucket_websiste):
    root = ElementTree.Element('WebsiteConfiguration')

    index_node = ElementTree.SubElement(root, 'IndexDocument')
    _add_text_child(index_node, 'Suffix', bucket_websiste.index_file)

    error_node = ElementTree.SubElement(root, 'ErrorDocument')
    _add_text_child(error_node, 'Key', bucket_websiste.error_file)

    return _node_to_string(root)


def to_put_bucket_lifecycle(bucket_lifecycle):
    root = ElementTree.Element('LifecycleConfiguration')

    for rule in bucket_lifecycle.rules:
        rule_node = ElementTree.SubElement(root, 'Rule')
        _add_text_child(rule_node, 'ID', rule.id)
        _add_text_child(rule_node, 'Prefix', rule.prefix)
        _add_text_child(rule_node, 'Status', rule.status)

        expiration = rule.expiration
        if expiration:
            expiration_node = ElementTree.SubElement(rule_node, 'Expiration')

            if expiration.days is not None:
                _add_text_child(expiration_node, 'Days', str(expiration.days))
            elif expiration.date is not None:
                _add_text_child(expiration_node, 'Date', date_to_iso8601(expiration.date))
            elif expiration.created_before_date is not None:
                _add_text_child(expiration_node, 'CreatedBeforeDate', date_to_iso8601(expiration.created_before_date))

        abort_multipart_upload = rule.abort_multipart_upload
        if abort_multipart_upload:
            abort_multipart_upload_node = ElementTree.SubElement(rule_node, 'AbortMultipartUpload')
            if abort_multipart_upload.days is not None:
                _add_text_child(abort_multipart_upload_node, 'Days', str(abort_multipart_upload.days))
            elif abort_multipart_upload.created_before_date is not None:
                _add_text_child(abort_multipart_upload_node, 'CreatedBeforeDate',
                                date_to_iso8601(abort_multipart_upload.created_before_date))

        storage_transitions = rule.storage_transitions
        if storage_transitions:
            for storage_transition in storage_transitions:
                storage_transition_node = ElementTree.SubElement(rule_node, 'Transition')
                _add_text_child(storage_transition_node, 'StorageClass', str(storage_transition.storage_class))
                if storage_transition.days is not None:
                    _add_text_child(storage_transition_node, 'Days', str(storage_transition.days))
                elif storage_transition.created_before_date is not None:
                    _add_text_child(storage_transition_node, 'CreatedBeforeDate',
                                    date_to_iso8601(storage_transition.created_before_date))

    return _node_to_string(root)


def to_put_bucket_cors(bucket_cors):
    root = ElementTree.Element('CORSConfiguration')

    for rule in bucket_cors.rules:
        rule_node = ElementTree.SubElement(root, 'CORSRule')
        _add_node_list(rule_node, 'AllowedOrigin', rule.allowed_origins)
        _add_node_list(rule_node, 'AllowedMethod', rule.allowed_methods)
        _add_node_list(rule_node, 'AllowedHeader', rule.allowed_headers)
        _add_node_list(rule_node, 'ExposeHeader', rule.expose_headers)

        if rule.max_age_seconds is not None:
            _add_text_child(rule_node, 'MaxAgeSeconds', str(rule.max_age_seconds))

    return _node_to_string(root)

def to_create_live_channel(live_channel):
    root = ElementTree.Element('LiveChannelConfiguration')

    _add_text_child(root, 'Description', live_channel.description)
    _add_text_child(root, 'Status', live_channel.status)
    target_node = _add_node_child(root, 'Target')

    _add_text_child(target_node, 'Type', live_channel.target.type)
    _add_text_child(target_node, 'FragDuration', str(live_channel.target.frag_duration))
    _add_text_child(target_node, 'FragCount', str(live_channel.target.frag_count))
    _add_text_child(target_node, 'PlaylistName', str(live_channel.target.playlist_name))

    return _node_to_string(root)

def to_select_object(sql, select_params):
    root = ElementTree.Element('SelectRequest')
    _add_text_child(root, 'Expression', base64.b64encode(str.encode(sql)))
    input_ser = ElementTree.SubElement(root, 'InputSerialization')
    output_ser = ElementTree.SubElement(root, 'OutputSerialization')
    csv = ElementTree.SubElement(input_ser, 'CSV')
    out_csv = ElementTree.SubElement(output_ser, 'CSV')
    options = ElementTree.SubElement(root, 'Options')
    if (select_params is not None):
        if 'CsvHeaderInfo' in select_params:
            _add_text_child(csv, 'FileHeaderInfo', select_params['CsvHeaderInfo'])
        if 'CommentCharacter' in select_params:
            _add_text_child(csv, 'CommentCharacter', base64.b64encode(str.encode(select_params['CommentCharacter'])))
        if 'RecordDelimiter' in select_params:
            _add_text_child(csv, 'RecordDelimiter', base64.b64encode(str.encode(select_params['RecordDelimiter'])))
        if 'OutputRecordDelimiter' in select_params:
            _add_text_child(out_csv, 'RecordDelimiter', base64.b64encode(str.encode(select_params['OutputRecordDelimiter'])))
        if 'FieldDelimiter' in select_params:
            _add_text_child(csv, 'FieldDelimiter', base64.b64encode(str.encode(select_params['FieldDelimiter'])))
        if 'OutputFieldDelimiter' in select_params:
            _add_text_child(out_csv, 'FieldDelimiter', base64.b64encode(str.encode(select_params['OutputFieldDelimiter'])))
        if 'QuoteCharacter' in select_params:
            _add_text_child(csv, 'QuoteCharacter', base64.b64encode(str.encode(select_params['QuoteCharacter'])))
        if 'SplitRange' in select_params:
            _add_text_child(csv, 'Range', utils._make_split_range_string(select_params['SplitRange']))
        elif 'LineRange' in select_params:
            _add_text_child(csv, 'Range', utils._make_line_range_string(select_params['LineRange']))
        if 'CompressionType' in select_params:
            _add_text_child(input_ser, 'CompressionType', select_params['CompressionType'])
        if 'KeepAllColumns' in select_params:
            _add_text_child(output_ser, 'KeepAllColumns', str(select_params['KeepAllColumns']))
        if 'OutputRawData' in select_params:
            _add_text_child(output_ser, 'OutputRawData', str(select_params['OutputRawData']))
        if 'EnablePayloadCrc' in select_params:
            _add_text_child(output_ser, 'EnablePayloadCrc', str(select_params['EnablePayloadCrc']))
        if 'OutputHeader' in select_params:
            _add_text_child(output_ser, 'OutputHeader', str(select_params['OutputHeader']))
        if 'SkipPartialDataRecord' in select_params:
            _add_text_child(options, 'SkipPartialDataRecord', str(select_params['SkipPartialDataRecord']))

    return _node_to_string(root)

def to_get_select_object_meta(csv_meta_param):
    root = ElementTree.Element('CsvMetaRequest')
    input_ser = ElementTree.SubElement(root, 'InputSerialization')
    csv = ElementTree.SubElement(input_ser, 'CSV')
    if (csv_meta_param is not None):
        if 'RecordDelimiter' in csv_meta_param:
            _add_text_child(csv, 'RecordDelimiter', base64.b64encode(str.encode(csv_meta_param['RecordDelimiter'])))
        if 'FieldDelimiter' in csv_meta_param:
            _add_text_child(csv, 'FieldDelimiter', base64.b64encode(str.encode(csv_meta_param['FieldDelimiter'])))
        if 'QuoteCharacter' in csv_meta_param:
            _add_text_child(csv, 'QuoteCharacter', base64.b64encode(str.encode(csv_meta_param['QuoteCharacter'])))
        if 'CompressionType' in csv_meta_param:
            _add_text_child(input_ser, 'CompressionType', base64.b64encode(str.encode(csv_meta_param['CompressionType'])))
        if 'OverwriteIfExists' in csv_meta_param:
            _add_text_child(root, 'OverwriteIfExists', str(csv_meta_param['OverwriteIfExists']))
    return _node_to_string(root)
