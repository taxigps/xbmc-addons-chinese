#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import json
from common import *
SERVER = "http://api2.rrmj.tv"

FAKE_HEADERS = {
    "a": "cf2ecd4d-dea3-40ca-814f-3f0462623b1c",
    "b": "http://api.rrmj.tv/v2/video/indexInfo",
    "c": "5a1fb134-9384-4fc8-a5ae-6e711e24afc1",
    "d": "1454936672005",
    "e": "d4dd075d894dd2b8c81f96062dbe7dcbf7d467fd"
}


class RenRenMeiJu(object):
    """docstring for RenRenMeiJu"""
    def __init__(self):
        super(RenRenMeiJu, self).__init__()

    def search(self, page=1, rows=12, **kwargs):
        API = '/v2/video/search'
        kwargs["page"] = page
        kwargs["rows"] = rows
        data = GetHttpData(SERVER + API, data=urllib.urlencode(kwargs), headers=FAKE_HEADERS)
        return json.loads(data)

    def get_album(self, albumId=2):
        API = '/v2/video/album'
        data = GetHttpData(SERVER + API, data=urllib.urlencode(dict(albumId=albumId)), headers=FAKE_HEADERS)
        return json.loads(data)

    def index_info(self):
        API = '/v2/video/indexInfo'
        data = GetHttpData(SERVER + API, headers=FAKE_HEADERS)
        return json.loads(data)

    def video_detail(self, seasonId, userId=0, **kwargs):
        API = '/v2/video/detail'
        kwargs["seasonId"] = seasonId
        kwargs["userId"] = userId
        data = GetHttpData(SERVER + API, data=urllib.urlencode(kwargs), headers=FAKE_HEADERS)
        return json.loads(data)

    def hot_word(self):
        API = '/v2/video/hotWord'
        data = GetHttpData(SERVER + API, headers=FAKE_HEADERS)
        return json.loads(data)


class RRMJResolver(object):

    def get_m3u8(self, url, quality=""):
        print quality
        API = '/v2/video/findM3u8'
        params = dict({"htmlUrl": url,
                       "quality": quality
                       })
        data = json.loads(GetHttpData(SERVER + API, data=urllib.urlencode(params), headers=FAKE_HEADERS))
        print data
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

    def get_play(self, url, quality=""):
        return self.get_m3u8(url, quality)

if __name__ == "__main__":
    rrmj = RenRenMeiJu()
    # print rrmj.get_album()
    # print rrmj.search("喜剧")
    print rrmj.index_info()
    # print rrmj.video_detail("933")
