# -*- coding: utf-8 -*-

import unittest
import datetime
import time
import os, sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import oss2

from common import *
from oss2.exceptions import *


class TestLiveChannel(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestLiveChannel, self).__init__(*args, **kwargs)
        self.bucket = None

    def setUp(self):
        self.bucket = oss2.Bucket(oss2.Auth(OSS_ID, OSS_SECRET), OSS_ENDPOINT, OSS_BUCKET)
        self.bucket.create_bucket()

    def _get_play_url(self, bucket_name, channel_id, playlist_name):
        return 'http://%s.%s/%s/%s' % (bucket_name, OSS_ENDPOINT, channel_id, playlist_name if playlist_name else 'playlist.m3u8')

    def _get_publish_url(self, bucket_name, channel_id):
        return 'rtmp://%s.%s/live/%s' % (bucket_name, OSS_ENDPOINT, channel_id)

    def _get_fixed_number(self, size, n):
        nstr = str(n)
        if size > len(nstr):
            nstr = (size - len(nstr)) * '0' + nstr
        return nstr

    def _assert_list_result(self,
                            result,
                            marker = '',
                            prefix = '',
                            next_marker = '',
                            max_keys = 0,
                            is_truncated = False,
                            return_count = 0):
        self.assertEqual(result.prefix, prefix)
        self.assertEqual(result.marker, marker)
        self.assertEqual(result.next_marker, next_marker)
        self.assertEqual(result.max_keys, max_keys)
        self.assertEqual(result.is_truncated, is_truncated)
        self.assertEqual(len(result.channels), return_count)

    def test_create_live_channel(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = random_string(63).lower()
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        channel_id = 'rtmp-channel'
        playlist_name = 'test.m3u8'
        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = playlist_name)
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        create_result = bucket.create_live_channel(channel_id, channel_info)

        self.assertEqual(create_result.play_url,
                         self._get_play_url(bucket_name, channel_id, playlist_name))
        self.assertEqual(create_result.publish_url,
                         self._get_publish_url(bucket_name, channel_id))

        delete_result = bucket.delete_live_channel(channel_id)
        bucket.delete_bucket()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_get_live_channel(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        channel_id = 'rtmp-channel'

        self.assertRaises(NoSuchLiveChannel, bucket.get_live_channel, channel_id)

        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = 'test.m3u8')
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        create_result = bucket.create_live_channel(channel_id, channel_info)

        get_result = bucket.get_live_channel(channel_id)
        self.assertEqual(get_result.description, channel_info.description)
        self.assertEqual(get_result.status, channel_info.status)
        self.assertEqual(get_result.target.type, channel_target.type)
        self.assertEqual(get_result.target.frag_duration, str(channel_target.frag_duration))
        self.assertEqual(get_result.target.frag_count, str(channel_target.frag_count))
        self.assertEqual(get_result.target.playlist_name, channel_target.playlist_name)

        bucket.delete_live_channel(channel_id)
        bucket.delete_bucket()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_list_live_channel(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        channel_id = 'rtmp-channel'
        self.assertRaises(NoSuchLiveChannel, bucket.get_live_channel, channel_id)

        list_result = bucket.list_live_channel()
        self._assert_list_result(list_result,
                prefix = '',
                marker = '',
                next_marker = '',
                max_keys = 100,
                is_truncated = False,
                return_count = 0)

        channel_id_list = []
        prefix1 = random_string(5)
        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = 'test.m3u8')
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        for index in xrange(0, 200):
            channel_id_list.append(prefix1 + self._get_fixed_number(10, index))
            bucket.create_live_channel(channel_id_list[index], channel_info)

        list_result = bucket.list_live_channel()
        next_marker = prefix1 + self._get_fixed_number(10, 99)
        self._assert_list_result(list_result,
                prefix = '',
                marker = '',
                next_marker = next_marker,
                max_keys = 100,
                is_truncated = True,
                return_count = 100)

        prefix2 = random_string(5)
        list_result = bucket.list_live_channel(prefix = prefix2)
        self._assert_list_result(list_result,
                prefix = prefix2,
                marker = '',
                next_marker = '',
                max_keys = 100,
                is_truncated = False,
                return_count = 0)

        marker = prefix1 + self._get_fixed_number(10, 100)
        list_result = bucket.list_live_channel(
                prefix = prefix1,
                marker = marker)
        self._assert_list_result(list_result,
                prefix = prefix1,
                marker = marker,
                next_marker = '',
                max_keys = 100,
                is_truncated = False,
                return_count = 99)

        max_keys = 1000
        list_result = bucket.list_live_channel(max_keys = max_keys)
        self._assert_list_result(list_result,
                prefix = '',
                marker = '',
                next_marker = '',
                max_keys = max_keys,
                is_truncated = False,
                return_count = 200)

        for channel_id in channel_id_list:
            bucket.delete_live_channel(channel_id)
        bucket.delete_bucket()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_get_live_channel_stat(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        channel_id = 'rtmp-channel'
        _playlist_name = 'test.m3u8'
        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = _playlist_name)
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        create_result = bucket.create_live_channel(channel_id, channel_info)

        get_stat_result = bucket.get_live_channel_stat(channel_id)
        self.assertEqual(get_stat_result.status, 'Idle')

        bucket.delete_live_channel(channel_id)
        bucket.delete_bucket()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_put_live_channel_status(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        channel_id = 'rtmp-channel'
        channel_target = oss2.models.LiveChannelInfoTarget()
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        create_result = bucket.create_live_channel(channel_id, channel_info)

        get_result = bucket.get_live_channel(channel_id)
        self.assertEqual(get_result.status, 'enabled')

        bucket.put_live_channel_status(channel_id, 'disabled')

        get_result = bucket.get_live_channel(channel_id)
        self.assertEqual(get_result.status, 'disabled')

        bucket.delete_live_channel(channel_id)
        bucket.delete_bucket()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_get_live_channel_history(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        channel_id = 'rtmp-channel'
        channel_target = oss2.models.LiveChannelInfoTarget()
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        create_result = bucket.create_live_channel(channel_id, channel_info)

        get_result = bucket.get_live_channel_history(channel_id)
        self.assertEqual(len(get_result.records), 0)

        bucket.delete_live_channel(channel_id)
        bucket.delete_bucket()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_post_vod_playlist(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, random_string(63).lower())
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        channel_id = 'rtmp-channel'
        channel_target = oss2.models.LiveChannelInfoTarget()
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        create_result = bucket.create_live_channel(channel_id, channel_info)

        # publish rtmp stream here, generate some ts file on oss.

        end_time = int(time.time()) - 60
        start_time = end_time - 3600
        playlist_name = 'vod_playlist.m3u8'

        # throw exception because no ts file been generated.
        self.assertRaises(oss2.exceptions.InvalidArgument,
                          bucket.post_vod_playlist,
                          channel_id,
                          playlist_name,
                          start_time = start_time,
                          end_time = end_time)

        bucket.delete_live_channel(channel_id)
        bucket.delete_bucket()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

if __name__ == '__main__':
    unittest.main()
