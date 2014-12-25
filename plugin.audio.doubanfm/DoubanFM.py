#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, json

__UserAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:6.0.2) Gecko/20100101 Firefox/6.0.2'
__ChannelUrl = 'http://www.douban.com/j/app/radio/channels'
PlayListUrlPre = 'http://douban.fm/j/mine/playlist?type=n&from=mainsite&channel='

def GetInfo(url, key):
    req = urllib2.Request(url)
    req.add_header('User-Agent', __UserAgent)
    response = urllib2.urlopen(req)
    info = json.load(response)
    return info[key]

def GetSongs(channel_id):
    url = "%s%s" % (PlayListUrlPre, channel_id)
    SongJson = GetInfo(url, 'song')
    ListSongInfo = []
    for song in SongJson:
        if 'rda' in song['url']:
            continue
        SongInfo = {'pic':song['picture'].replace('\\',''), 
                    'album':song['albumtitle'], 
                    'artist':song['artist'], 
                    'url':song['url'].replace('\\',''), 
                    'duration': song['length'], 
                    'rating': song['rating_avg'],
                    'title':song['title']}
        if song['public_time'].isdigit(): SongInfo['year'] = int(song['public_time'])
        ListSongInfo.append(SongInfo.copy())
    return ListSongInfo

def GetChannels():
    ChannelJson = GetInfo(__ChannelUrl, 'channels')
    ListChannelInfo = [(ch['name'], ch['channel_id']) for ch in ChannelJson]
    return ListChannelInfo

if __name__ == '__main__':
    for n, i in GetChannels():
        print n, i
    for d in GetSongs(0):
        print d['title'], d['url']
