#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import json
import time
from common import *
import xbmcvfs
import xbmcgui
import xbmcaddon
SERVER = "http://api.rrmj.tv"
__ADDON__ = xbmcaddon.Addon()


FAKE_HEADERS = {
    "a": "cf2ecd4d-dea3-40ca-814f-3f0462623b1c",
    "b": "",
    "clientType": "android_%E5%B0%8F%E7%B1%B3",
    "clientVersion": "2.0.7.3",
    "c": "5a1fb134-9384-4fc8-a5ae-6e711e24afc1",
    "d": "",
    "e": "d4dd075d894dd2b8c81f96062dbe7dcbf7d467fd"
}


def getGUID():
    if xbmcvfs.exists("special://temp/rrmj.key"):
        f = xbmcvfs.File("special://temp/rrmj.key")
        result = f.read()
        f.close()
        if result != "":
            return result
    import uuid
    key = str(uuid.uuid1())
    f = xbmcvfs.File("special://temp/rrmj.key", 'w')
    result = f.write(key)
    f.close()
    return key


def createKey():
    constantStr = "yyets"
    c = str(int(time.time()))+"416"
    return caesarEncryption(constantStr + c, 3)


def caesarEncryption(source, offset):
    dic = "abcdefghijklmnopqrstuvwxyz0123456789"
    length = len(dic)
    result = ""
    for ch in source:
        i = dic.find(ch)
        if i+offset >= length:
            result += dic[(i+offset) % length]
        else:
            result += dic[i+offset]
    return result


class RenRenMeiJu(object):
    """docstring for RenRenMeiJu"""
    def __init__(self):
        self._header = FAKE_HEADERS
        key_id = getGUID()
        self._header.update(a=key_id)
        self.get_ticket()

    def get_json(self, url, data=None, pretty=False):
        headers = self.header
        headers.update(b=url)
        s = json.loads(GetHttpData(url, data=data, headers=headers))
        if pretty:
            print headers
            print json.dumps(s, sort_keys=True,
                             indent=4, separators=(',', ': '))
        return s

    def get_ticket(self):
        expired_time = __ADDON__.getSetting("expired_time")
        if expired_time != "":
            now = int(time.time())*1000
            if now < int(expired_time):
                return
        API = '/auth/ticket'
        auth_data = {"a": FAKE_HEADERS["a"],
                     "b": createKey()}
        data = self.get_json(SERVER + API, data=urllib.urlencode(auth_data))
        if data["data"]["ticket"] != "":
            __ADDON__.setSetting("expired_time", str(data["data"]["expiredTime"]))

    @property
    def header(self):
        self._header.update(d=str(int(time.time()))+"416")
        return self._header

    def search(self, page=1, rows=12, **kwargs):
        API = '/v2/video/search'
        kwargs["page"] = page
        kwargs["rows"] = rows
        return self.get_json(SERVER + API, data=urllib.urlencode(kwargs))

    def get_album(self, albumId=2):
        API = '/v2/video/album'
        return self.get_json(SERVER + API, data=urllib.urlencode(dict(albumId=albumId)))

    def index_info(self):
        API = '/v2/video/indexInfo'
        return self.get_json(SERVER + API)

    def video_detail(self, seasonId, userId=0, **kwargs):
        API = '/v2/video/detail'
        kwargs["seasonId"] = seasonId
        kwargs["userId"] = userId
        return self.get_json(SERVER + API, data=urllib.urlencode(kwargs))

    def hot_word(self):
        API = '/v2/video/hotWord'
        return self.get_json(SERVER + API)


class RRMJResolver(RenRenMeiJu):

    def get_by_sid(self, **kwargs):
        API = "/v2/video/findM3u8ByEpisodeSid"
        data = self.get_json(SERVER + API, data=urllib.urlencode(kwargs), pretty=False)
        if data["code"] != "0000":
            return None, None
        else:
            m3u8 = data["data"]["m3u8"]
            current_quality = m3u8["currentQuality"]
            quality_array = m3u8["qualityArr"]
            if current_quality == "QQ":
                decoded_url = m3u8["url"].decode("base64")
                real_url = json.loads(decoded_url)
                print real_url
                return real_url["V"][0]["U"], current_quality
            else:
                return m3u8["url"], current_quality


    def get_play(self, seasonId, episodeSid, quality=""):
        return self.get_by_sid(seasonId=seasonId, episodeSid=episodeSid, quality=quality)
