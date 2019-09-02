# -*- coding: utf-8 -*-

import os, sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

from .common import *
from oss2.exceptions import *


class TestLiveChannel(OssTestCase):
    def tearDown(self):
        self._delete_channels()
        OssTestCase.tearDown(self)
            
    def _get_play_url(self, bucket_name, channel_name, playlist_name):
        return 'http://%s.%s/%s/%s' % (bucket_name, 
                                       OSS_ENDPOINT.replace('http://', '').replace('https://', ''), 
                                       channel_name, 
                                       playlist_name if playlist_name else 'playlist.m3u8')

    def _get_publish_url(self, bucket_name, channel_name):
        return 'rtmp://%s.%s/live/%s' % (bucket_name, 
                                         OSS_ENDPOINT.replace('http://', '').replace('https://', ''),
                                         channel_name)

    def _get_fixed_number(self, size, n):
        nstr = str(n)
        if size > len(nstr):
            nstr = (size - len(nstr)) * '0' + nstr
        return nstr
    
    def _delete_channels(self):
        prefix = ''
        max_keys = 1000
        for info in oss2.LiveChannelIterator(self.bucket, prefix, max_keys=max_keys):
            self.bucket.delete_live_channel(info.name)

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
        channel_name = 'test-create-channel'
        playlist_name = 'test.m3u8'
        
        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = playlist_name)
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        create_result = self.bucket.create_live_channel(channel_name, channel_info)

        self.assertEqual(create_result.play_url,
                         self._get_play_url(self.bucket.bucket_name, channel_name, playlist_name))
        self.assertEqual(create_result.publish_url,
                         self._get_publish_url(self.bucket.bucket_name, channel_name))

        self.bucket.delete_live_channel(channel_name)

    def test_get_live_channel(self):
        channel_name = 'test-get-channel'

        self.assertRaises(NoSuchLiveChannel, self.bucket.get_live_channel, channel_name)

        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = 'test.m3u8')
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        self.bucket.create_live_channel(channel_name, channel_info)

        get_result = self.bucket.get_live_channel(channel_name)
        self.assertEqual(get_result.description, channel_info.description)
        self.assertEqual(get_result.status, channel_info.status)
        self.assertEqual(get_result.target.type, channel_target.type)
        self.assertEqual(get_result.target.frag_duration, str(channel_target.frag_duration))
        self.assertEqual(get_result.target.frag_count, str(channel_target.frag_count))
        self.assertEqual(get_result.target.playlist_name, channel_target.playlist_name)

        self.bucket.delete_live_channel(channel_name)

    def test_list_live_channel(self):
        auth = oss2.Auth(OSS_ID, OSS_SECRET)
        bucket_name = OSS_BUCKET + "-test-list-live-channel"
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, bucket_name)
        bucket.create_bucket(oss2.BUCKET_ACL_PRIVATE)

        channel_name = 'test-list-channel'
        self.assertRaises(NoSuchLiveChannel, bucket.get_live_channel, channel_name)

        list_result = bucket.list_live_channel()
        self._assert_list_result(list_result,
                prefix = '',
                marker = '',
                next_marker = '',
                max_keys = 100,
                is_truncated = False,
                return_count = 0)

        channel_name_list = []
        prefix1 = random_string(5)
        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = 'test.m3u8')
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        for index in range(200):
            channel_name_list.append(prefix1 + self._get_fixed_number(10, index))
            bucket.create_live_channel(channel_name_list[index], channel_info)

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

        for channel_name in channel_name_list:
            bucket.delete_live_channel(channel_name)
        bucket.delete_bucket()
        wait_meta_sync()
        self.assertRaises(oss2.exceptions.NoSuchBucket, bucket.delete_bucket)

    def test_get_live_channel_stat(self):
        channel_name = 'test-get-channel-stat'
        playlist_name = 'test.m3u8'
        
        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = playlist_name)
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        self.bucket.create_live_channel(channel_name, channel_info)

        get_stat_result = self.bucket.get_live_channel_stat(channel_name)
        self.assertEqual(get_stat_result.status, 'Idle')

        self.bucket.delete_live_channel(channel_name)

    def test_put_live_channel_status(self):
        channel_name = 'test-put-channel-status'
        
        channel_target = oss2.models.LiveChannelInfoTarget()
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        self.bucket.create_live_channel(channel_name, channel_info)

        get_result = self.bucket.get_live_channel(channel_name)
        self.assertEqual(get_result.status, 'enabled')

        self.bucket.put_live_channel_status(channel_name, 'disabled')

        get_result = self.bucket.get_live_channel(channel_name)
        self.assertEqual(get_result.status, 'disabled')
        
        self.bucket.put_live_channel_status(channel_name, 'enabled')
        
        get_result = self.bucket.get_live_channel(channel_name)
        self.assertEqual(get_result.status, 'enabled')

        self.bucket.delete_live_channel(channel_name)

    def test_get_live_channel_history(self):
        channel_name = 'test-get-channel-history'
        
        channel_target = oss2.models.LiveChannelInfoTarget()
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        self.bucket.create_live_channel(channel_name, channel_info)

        get_result = self.bucket.get_live_channel_history(channel_name)
        self.assertEqual(len(get_result.records), 0)

        self.bucket.delete_live_channel(channel_name)

    def test_post_vod_playlist(self):
        channel_name = 'test-post-vod-playlist'
        
        channel_target = oss2.models.LiveChannelInfoTarget()
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        self.bucket.create_live_channel(channel_name, channel_info)

        # push rtmp stream here, then generate some ts files on oss.

        end_time = int(time.time()) - 60
        start_time = end_time - 3600
        playlist_name = 'vod_playlist.m3u8'

        # throw exception because no ts file been generated.
        self.assertRaises(oss2.exceptions.InvalidArgument,
                          self.bucket.post_vod_playlist,
                          channel_name,
                          playlist_name,
                          start_time = start_time,
                          end_time = end_time)

        self.bucket.delete_live_channel(channel_name)
        
    def test_sign_rtmp_url(self):
        channel_name = 'test-sign-rtmp-url'
        playlist_name = 'test.m3u8'
        
        channel_target = oss2.models.LiveChannelInfoTarget(playlist_name = playlist_name)
        channel_info = oss2.models.LiveChannelInfo(target = channel_target)
        self.bucket.create_live_channel(channel_name, channel_info)
        
        expires = 3600
        signed_url = self.bucket.sign_rtmp_url(channel_name, playlist_name, expires)
        self.assertTrue(signed_url.startswith(self._get_publish_url(self.bucket.bucket_name, channel_name)))

        # empty playlist name
        signed_url = self.bucket.sign_rtmp_url(channel_name, '', expires)
        self.assertTrue(signed_url.startswith(self._get_publish_url(self.bucket.bucket_name, channel_name)))
         
        self.bucket.delete_live_channel(channel_name)
        
    def test_anonymous_auth(self):
        channel_name = 'test-chan-anonymous-auth'
        playlist_name = 'test.m3u8'
        
        bucket = oss2.Bucket(oss2.AnonymousAuth(), OSS_ENDPOINT, self.bucket.bucket_name)
        signed_url = bucket.sign_rtmp_url(channel_name, playlist_name, 0)
        self.assertEqual(signed_url, self._get_publish_url(self.bucket.bucket_name, channel_name) 
                         + "?playlistName=" + playlist_name)
        
        self.assertRaises(oss2.exceptions.AccessDenied, bucket.delete_live_channel, 'test-live-chan')
    

if __name__ == '__main__':
    unittest.main()
