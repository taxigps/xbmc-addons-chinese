#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, urllib, re, json

baseHtml = "http://bk2.radio.cn/mms4/videoPlay/"
typeHtml = "getAreaAndType.jspa"
channelHtml = "pcGetChannels.jspa"
playinfoHtml = "getChannelPlayInfoJson.jspa"

headers = { "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:35.0) Gecko/20100101 Firefox/35.0",
            "Host": "bk2.radio.cn",
            "Referer": "http://www.radio.cn/index.php?option=default,radio"}

MODE_NONE = "none"
MODE_MENU = "menu"
MODE_CHANNELS = "channels"
MODE_PLAY = "play"

def request(url):
    if not url.startswith('http'):
        url = baseHtml + url
    print('request', url)
    req = urllib2.Request(url, headers = headers)
    response = urllib2.urlopen(req)
    cont = response.read()
    response.close()
    return json.loads(cont.strip("()"))

def isFolder(mode):
    return mode in (MODE_MENU, MODE_CHANNELS)

def getMenu():
    #name, mode, icon, area, type
    c = request(typeHtml)
    d = {'area': '地区', 'type': '类型'}
    l = []
    for i in d.keys():
        h = '[COLOR FFDEB887]【%s】[/COLOR]' % (d[i])
        item = {'name': h, 'mode': MODE_NONE}
        l.append(item)
        for j in c[i]:
            item = {'name': j['value'],
                    'mode': MODE_CHANNELS,
                    'icon': j['url']}
            item[i] = j['key']
            l.append(item)
    return l

def getChannels(area = 0, type =  0):
    query = {'area': area,
             'type': type,
             'callback': ''}
    url = '%s?%s' % (channelHtml, urllib.urlencode(query))
    c = request(url)
    # name, mode, icon, channelId
    return [ {'name':j['channelName'],
              'mode': MODE_PLAY,
              'icon': j['icon'],
              'channelId': j['channelId']} for j in c ]

def getPlayinfo(channelId):
    # name, url
    url = playinfoHtml
    query = {'channelId': channelId,
             'location': 'http://www.radio.cn/',
             'terminalType': 'PC',
             'callback': ''}
    url = '%s?%s' % (url, urllib.urlencode(query))
    c = request(url)
    print(c)
    return c['channelName'], c['streams'][0]['url']

if __name__ == '__main__':
    print(getStreamUrl(183))
