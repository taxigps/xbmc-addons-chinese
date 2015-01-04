#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys,urllib2,urllib,re,json,time
from pprint import pprint
userAgent = 'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10'
homepage = 'http://m.kugou.com'
headers = {'User-Agent': userAgent, 'Referer': homepage}

def getHttpData(u, query):
    url = '%s/app/i/%s?%s' % (homepage, u, urllib.urlencode(query))
    req = urllib2.Request(url, headers = headers)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    return httpdata

def getSingerPic(title, size = 200):
    #根据歌手获得相应的信息
    singerList = re.findall('(【.*?】)?(.*?)-', title)
    if singerList:
        query = {'singerName': singerList[0][1],
                 'size': size,
                 'd': time.time()*1000}
        singerUrl = 'getSingerHead_new.php'
        singerInfo = getHttpData(singerUrl, query)
        return json.loads(singerInfo).get('url', '')
    return ''

def getSongInfo(hashId):
    #根据hash 获得mp3的相应信息
    query = {'hash': hashId, 'cmd': 'playInfo'}
    songUrl = 'getSongInfo.php'
    songStr =  getHttpData(songUrl, query)
    songJson = json.loads(songStr)
    return songJson['url']

def getSongs(fmid, t = None, size = 30):
    #只选取前80首歌(可以查询的歌曲相当的多！！！)  返回的是相应的json
    listUrl = 'fmSongs.php'
    offset = {"time":int(t if t else time.time())}
    query = {'fmid':str(fmid), 'offset':str(offset),'size':size}
    listStr = getHttpData(listUrl, query)
    listJson = json.loads(listStr)
    return listJson['data'][0]['songs']

def getFmList(page, pagesize = 30):
    #获得酷狗Fm列表 json
    query = {'pageindex': page, 'pagesize':pagesize}
    url = 'fmList.php'
    reqStr = getHttpData(url, query)
    reqJson = json.loads(reqStr)
    return reqJson

if __name__ == '__main__':
    pprint(getSingerPic("【上海话】顶楼的马戏团 - 上海童年"))
