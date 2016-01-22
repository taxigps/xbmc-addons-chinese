# -*- coding: utf8 -*-

from xbmcswift2 import Plugin, CLI_MODE, xbmcaddon, ListItem, xbmc, xbmcgui
import os
import sys

try:
    from ChineseKeyboard import Keyboard
except Exception, e:
    print e
    from xbmc import Keyboard

CATE = ["喜剧", "科幻", "恐怖", "剧情", "魔幻", "罪案", "冒险", "动作", "悬疑"]

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_PATH = ADDON.getAddonInfo('path').decode("utf-8")
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_DATA_PATH = xbmc.translatePath("special://profile/addon_data/%s" % ADDON_ID).decode("utf-8")
sys.path.append(os.path.join(ADDON_PATH, 'resources', 'lib'))
from rrmj import *
from common import *

plugin = Plugin()
Meiju = RenRenMeiJu()
PAGE_ROWS = plugin.get_setting("page_rows")


def parse_qs(qs):
    return dict([s1.split('=') for s1 in urllib.unquote(qs).split('&')])


def remap_url(req_url, page=1):
    array = req_url.split("?")
    params = parse_qs(array[1])
    if array[0] == "/video/search":
        endpoint = "search"
        if "cat" in params:
            endpoint = "cat_list"
        elif "mark" in params:
            endpoint = "mark_list"
    elif array[0] == "/video/album":
        endpoint = "album"
    return plugin.url_for(endpoint, **params)


@plugin.route('/')
def index():
    yield {
        'label': "分类",
        'path': plugin.url_for("category"),
        'is_playable': False
    }
    yield {
        'label': "搜索",
        'path': plugin.url_for("hotword"),
        'is_playable': False
    }
    data = Meiju.index_info()
    if data["code"] != "0000":
        return
    for serial in data["data"]["index"]:
        url = remap_url(str(serial.get("requestUrl")))
        season_list = serial.get("seasonList")
        list_string = " ".join(season["title"] for season in season_list)
        item = {
            'label': "^^^".join([serial.get("title"), list_string]),
            'path': url,
            'is_playable': False
        }
        yield item
    for album in data["data"]["album"]:
        url = remap_url(str(album.get("requestUrl")))
        item = {
            'label': album["name"],
            'path': url,
            'icon': album["coverUrl"],
            'thumbnail': album["coverUrl"],
            'is_playable': False
        }
        yield item


@plugin.route('/cat/')
def category():
    for ca in CATE:
        item = {
            'label': ca,
            'path': plugin.url_for("cat_list", cat=ca),
            'is_playable': False
        }
        yield item


@plugin.route('/hotword/')
def hotword():
    yield {
            'label': colorize("输入关键字搜索", "yellow"),
            'path': plugin.url_for("input_keyword"),
            'is_playable': False
        }
    hotwords = Meiju.hot_word()
    for word in hotwords["data"]["wordList"]:
        word = word.encode("utf8")
        item = {
            'label': colorize(word, "green"),
            'path': plugin.url_for("search_title", title=word),
            'is_playable': False
        }
        yield item


@plugin.route("/input/")
def input_keyword():
    keyboard = Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        url = plugin.url_for("search_title", title=keyword)
        plugin.redirect(url)


@plugin.route('/search/cat_<cat>/page_<page>', name="cat_list", options={"page": "1"})
@plugin.route('/search/title_<title>/page_<page>', name="search_title", options={"page": "1"})
@plugin.route('/search/s_<sort>/o_<order>/m_<mark>/page_<page>', name="mark_list", options={"page": "1"})
@plugin.route('/search/page_<page>', options={"page": "1"})
def search(page, **kwargs):
    c_list = Meiju.search(page, PAGE_ROWS, **kwargs)
    for one in c_list["data"]["results"]:
        item = {
            'label': one.get("title"),
            'path': plugin.url_for("detail", seasonId=one.get("id")),
            'icon': one["cover"],
            'thumbnail': one["cover"],
            'is_playable': False
        }
        yield item


@plugin.route('/album/<albumId>', name="album")
def get_album(albumId):
    c_list = Meiju.get_album(albumId)
    for one in c_list["data"]["results"]:
        item = {
            'label': one.get("title"),
            'path': plugin.url_for("detail", seasonId=one.get("id")),
            'is_playable': False
        }
        yield item


@plugin.route('/detail/<seasonId>', name="detail")
def video_detail(seasonId):
    detail = Meiju.video_detail(seasonId)
    title = detail["data"]["seasonDetail"]["title"]
    for index, episode in enumerate(sorted(detail["data"]["seasonDetail"]["playUrlList"], key=lambda episode: episode['id'])):
        item = {
            'label': title + str(index+1),
            'path': plugin.url_for("play", url=episode["playLink"]),
            'is_playable': True
        }
        yield item


@plugin.route('/play/<url>')
def play(url):

    rs = RRMJResolver()
    m3u8 = rs.get_m3u8(url)
    print m3u8
    plugin.set_resolved_url(m3u8["url"])
    # else:
    #     plugin.set_resolved_url("stack://" + " , ".join(urls))
