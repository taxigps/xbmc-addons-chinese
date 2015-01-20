#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, urllib, re, json

baseHtml = "http://bk2.radio.cn/mms4/videoPlay"
typeHtml = baseHtml + "/getAreaAndType.jspa"
channelHtml = baseHtml + "/pcGetChannels.jspa"
playinfoHtml = baseHtml + "/getChannelPlayInfoJson.jspa"

headers = { "Host": "bk2.radio.cn",
            "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:35.0) Gecko/20100101 Firefox/35.0", 
            "Referer": "http://www.radio.cn/index.php?option=default,radio"}

MODE_NONE = "none"
MODE_MENU = "menu"
MODE_CHANNELS = "channels"
MODE_PLAY = "play"

def request(url, js = True):
    print('request', url)
    req = urllib2.Request(url, headers = headers)
    response = urllib2.urlopen(req)
    cont = response.read()
    response.close()
    if js:
        cont = json.loads(cont.strip("()"))
    return cont

def isFolder(mode):
    return mode in (MODE_MENU, MODE_CHANNELS)

def getMenu():
    #name, mode, icon, area, type
    c = request(typeHtml)
    d = {"area": "地区", "type": "类型"}
    l = []
    for i in sorted(d.keys()):
        h = '[COLOR FFDEB887]【%s】[/COLOR]' % (d[i])
        item = {'name': h, 'mode': MODE_NONE}
        l.append(item)
        for j in c[i]:
            item = {'name': j['value'].encode('utf-8'), 
                    'mode': MODE_CHANNELS,
                    'icon': j['url'].encode('utf-8')}
            item[i] = j['key'].encode('utf-8')
            l.append(item)
    return l

def getChannels(area = 0, type =  0):
    url = channelHtml
    query = {"area": area, "type": type, "callback": ""}
    url = "%s?%s" % (url, urllib.urlencode(query))
    c = request(url)
    l = []
    # name, mode, icon, param
    for j in c:
        item = {'name':j['channelName'].encode('utf-8'),
                'mode': MODE_PLAY,
                'icon': j['icon'].encode('utf-8'),
                'channelId': j['channelId']}
        l.append(item)
    return l

def getStreamUrl(channelId):
    url = playinfoHtml
    query = {"channelId": channelId,
             "location": "http://www.radio.cn/index.php?option=default,radio",
             "terminalType": "PC", 
             "callback": ""}
    url = "%s?%s" % (url, urllib.urlencode(query))
    c = request(url)
    return c['streams'][0]['url']

if __name__ == '__main__':
    print(getStreamUrl(183))
