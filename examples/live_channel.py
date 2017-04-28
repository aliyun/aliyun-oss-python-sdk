# -*- coding: utf-8 -*-

import os
import time

import oss2


# 以下代码展示了视频直播相关接口的用法。


# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<您的AccessKeyId>”替换成真实的AccessKeyId等。
#
# 以杭州区域为例，Endpoint是：
#   http://oss-cn-shenzhen.aliyuncs.com 或
#   https://oss-cn-shenzhen.aliyuncs.com
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<您的AccessKeyId>')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<您的AccessKeySecret>')
bucket_name = os.getenv('OSS_TEST_BUCKET', '<您的Bucket>')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '<您的访问域名>')


# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint):
    assert '<' not in param, '请设置参数：' + param


# 创建Bucket对象，所有直播相关的接口都可以通过Bucket对象来进行
bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)


# 创建一个直播频道。
# 频道的名称是test_rtmp_live。直播生成的m3u8文件叫做test.m3u8，该索引文件包含3片ts文件，每片ts文件的时长为5秒（这只是一个建议值，具体的时长取决于关键帧）。
channel_name = 'test_rtmp_live'
playlist_name = 'test.m3u8'
create_result = bucket.create_live_channel(
        channel_name,
        oss2.models.LiveChannelInfo(
            status = 'enabled',
            description = '测试使用的直播频道',
            target = oss2.models.LiveChannelInfoTarget(
                playlist_name = playlist_name,
                frag_count = 3,
                frag_duration = 5)))

# 创建直播频道之后拿到推流用的play_url（rtmp推流的url，如果Bucket不是公共读写权限那么还需要带上签名，见下文示例）和观流用的publish_url（推流产生的m3u8文件的url）。
publish_url = create_result.publish_url
play_url = create_result.play_url

# 创建好直播频道之后调用get_live_channel可以得到频道相关的信息。
get_result = bucket.get_live_channel(channel_name)
print(get_result.description)
print(get_result.status)
print(get_result.target.type)
print(get_result.target.frag_count)
print(get_result.target.frag_duration)
print(get_result.target.playlist_name)

# 拿到推流地址和观流地址之后就可以向OSS推流和观流。如果Bucket的权限不是公共读写，那么还需要对推流做签名，如果Bucket是公共读写的，那么可以直接用publish_url推流。
# 这里的expires是一个相对时间，指的是从现在开始这次推流过期的秒数。
# params是一个dict类型的参数，表示用户自定义的参数。所有的参数都会参与签名。
# 拿到这个签过名的signed_url就可以使用推流工具直接进行推流，一旦连接上OSS之后超过上面的expires流也不会断掉，OSS仅在每次推流连接的时候检查expires是否合法。
expires = 3600
signed_url = bucket.sign_rtmp_url(channel_name, playlist_name, expires)

# 创建好直播频道，如果想把这个频道禁用掉（断掉正在推的流或者不再允许向一个地址推流），应该使用put_live_channel_status接口，将频道的status改成“disabled”，如果要将一个禁用状态的频道启用，那么也是调用这个接口，将status改成“enabled”。
bucket.put_live_channel_status(channel_name, 'enabled')
bucket.put_live_channel_status(channel_name, 'disabled')

# 对创建好的频道，可以使用LiveChannelIterator来进行列举已达到管理的目的。
# prefix可以按照前缀过滤list出来的频道。
# max_keys表示迭代器内部一次list出来的频道的最大数量，这个值最大不能超过1000，不填写的话默认为100。

prefix = ''
max_keys = 1000

for info in oss2.LiveChannelIterator(bucket, prefix, max_keys=max_keys):
    print(info.name)

# 对于正在推流的频道调用get_live_channel_stat可以获得流的状态信息。
# 如果频道正在推流，那么stat_result中的所有字段都有意义。
# 如果频道闲置或者处于“disabled”状态，那么status为“Idle”或“Disabled”，其他字段无意义。
stat_result = bucket.get_live_channel_stat(channel_name)
print(stat_result.status)
print(stat_result.remote_addr)
print(stat_result.connected_time)
print(stat_result.video)
print(stat_result.audio)

# 如果想查看一个频道历史推流记录，可以调用get_live_channel_history。目前最多可以看到10次推流的记录
history_result = bucket.get_live_channel_history(channel_name)
print(len(history_result.records))

# 如果希望利用直播推流产生的ts文件生成一个点播列表，可以使用post_vod_playlist方法。
# 指定起始时间为当前时间减去60秒，结束时间为当前时间，这意味着将生成一个长度为60秒的点播视频。
# 播放列表指定为“vod_playlist.m3u8”，也就是说这个接口调用成功之后会在OSS上生成一个名叫“vod_playlist.m3u8”的播放列表文件。

end_time = int(time.time()) - 60
start_time = end_time - 3600
bucket.post_vod_playlist(channel_name,
                         playlist_name,
                         start_time = start_time,
                         end_time = end_time)

# 如果一个直播频道已经不打算再使用了，那么可以调用delete_live_channel来删除频道。
bucket.delete_live_channel(channel_name)
