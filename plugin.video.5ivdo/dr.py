# -*- coding: utf-8 -*-


import  urllib2, urllib, re, string, sys, os, gzip, StringIO, urlparse
from random import random
import base64, time
try:
    import simplejson
except ImportError:
    import json as simplejson

    
UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'


def GetHttpData(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    if response.headers.get('content-encoding', None) == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    response.close()
    match = re.compile('<meta http-equiv="[Cc]ontent-[Tt]ype" content="text/html; charset=(.+?)"').findall(httpdata)
    if len(match)<=0:
        match = re.compile('meta charset="(.+?)"').findall(httpdata)
    if len(match)>0:
        charset = match[0].lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = unicode(httpdata, charset).encode('utf8')
    return httpdata


class YOUKU_DR:
    f_code_1 = 'becaf9be'
    f_code_2 = 'bf7e5f01'
    def __init__( self ):
        return
    def trans_e(self, a, c):
        b = range(256)
        f = 0
        result = ''
        h = 0
        while h < 256:
            f = (f + b[h] + ord(a[h % len(a)])) % 256
            b[h], b[f] = b[f], b[h]
            h += 1
        q = f = h = 0
        while q < len(c):
            h = (h + 1) % 256
            f = (f + b[h]) % 256
            b[h], b[f] = b[f], b[h]
            result += chr(ord(c[q]) ^ b[(b[h] + b[f]) % 256])
            q += 1
        return result
    def _calc_ep2(self, vid, ep):
        e_code = self.trans_e(self.f_code_1, base64.b64decode(ep))
        sid, token = e_code.split('_')
        new_ep = self.trans_e(self.f_code_2, '%s_%s_%s' % (sid, vid, token))
        return base64.b64encode(new_ep), token, sid
    def selResolution(self,streamtypes):
        for i in range(0,len(streamtypes)):
            if streamtypes[i] == 'mp4':  return streamtypes[i]
        return streamtypes[0]
    def GetPlayList(self,vid):
        url = 'http://v.youku.com/player/getPlayList/VideoIDS/%s/ctype/12/ev/1' % (vid)
        link = GetHttpData(url)
        json_response = simplejson.loads(link)
        typeid = self.selResolution(json_response['data'][0]['streamtypes'])
        video_id = json_response['data'][0]['videoid']
        oip = json_response['data'][0]['ip']
        ep = json_response['data'][0]['ep']
        ep, token, sid = self._calc_ep2(video_id, ep)
        query = urllib.urlencode(dict(
            vid=video_id, ts=int(time.time()), keyframe=1, type=typeid,
            ep=ep, oip=oip, ctype=12, ev=1, token=token, sid=sid,
        ))
        movurl = 'http://pl.youku.com/playlist/m3u8?%s' % (query)
        return 'M3U8', movurl


# http://hot.vrs.sohu.com/vrs_flash.action?vid=2339874
class SOHU_DR:
    def __init__( self ):
        return
    def real_url(self,host,vid,tvid,new,clipURL,ck):
        url = 'http://'+host+'/?prot=9&prod=flash&pt=1&file='+clipURL+'&new='+new +'&key='+ ck+'&vid='+str(vid)+'&uid='+str(int(time.time()*1000))+'&t='+str(random())
        return simplejson.loads(GetHttpData(url))['url'].encode('utf-8')
    def get_hqvid(self,ppage):
        match = re.compile('"norVid":(.+?),"highVid":(.+?),"superVid":(.+?),"oriVid":(.+?),').search(ppage)
        if match:
            if match.group(4) !='0' : 
                return match.group(4)
            if match.group(3) !='0' : 
                return match.group(3)
            if match.group(2) !='0' : 
                return match.group(2)
            if match.group(1) !='0' : 
                return match.group(1)
        else:
            return 'ERROR'
    def GetPlayList(self,pvid):
        link = GetHttpData('http://hot.vrs.sohu.com/vrs_flash.action?vid='+pvid)
        hqvid = self.get_hqvid(link)
        if hqvid == 'ERROR':
            return 'ERROR',''
        info = simplejson.loads(link)
        host = info['allot']
        tvid = info['tvid']
        urls = []
        data = info['data']
#        assert len(data['clipsURL']) == len(data['clipsBytes']) == len(data['su'])
        for new,clip,ck, in zip(data['su'], data['clipsURL'], data['ck']):
            clipURL = urlparse.urlparse(clip).path
            urls.append(self.real_url(host,hqvid,tvid,new,clipURL,ck))
        return 'MULTI',urls


# itype,iurl=SOHU_DR().GetPlayList('2339874')
# 


def work(purl):
    ips = purl.split(',')
    if ips[0] == 'DR_YOUKU':
        itype,iurl=YOUKU_DR().GetPlayList(ips[1])
    if ips[0] == 'DR_SOHU':
        itype,iurl=SOHU_DR().GetPlayList(ips[1])
    else:
        itype ='ERROR'
        iurl=''
    return itype,iurl

def version():
    return '20150805c'

