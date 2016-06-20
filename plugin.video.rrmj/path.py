# -*- coding: utf8 -*-

from xbmcswift2 import Plugin, CLI_MODE, xbmcaddon, ListItem, xbmc, xbmcgui, xbmcplugin
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
SEASON_CACHE = plugin.get_storage('season')
HISTORY = plugin.get_storage('history')


def parse_qs(qs):
    "Query String to Dictionary"
    return dict([s1.split('=') for s1 in urllib.unquote(qs).split('&')])


def remap_url(req_url):
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


def set_auto_play():
    auto_play_setting = plugin.get_setting("auto_next")
    print setSettingByRPC("videoplayer.autoplaynextitem", auto_play_setting)


# main entrance
@plugin.route('/')
def index():
    set_auto_play()
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
    yield {
        'label': "历史",
        'path': plugin.url_for("list_history"),
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


# list catagories
@plugin.route('/cat/')
def category():
    for ca in CATE:
        item = {
            'label': ca,
            'path': plugin.url_for("cat_list", cat=ca),
            'is_playable': False
        }
        yield item


# search entrance
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


# get search result by input keyword
@plugin.route("/input/")
def input_keyword():
    keyboard = Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        url = plugin.url_for("search_title", title=keyword)
        plugin.redirect(url)


@plugin.route('/search/cat_<cat>/page_<page>', name="cat_list", options={"page": "1"})  # get search result by catagory
@plugin.route('/search/title_<title>/page_<page>', name="search_title", options={"page": "1"})  # get search result by search title
@plugin.route('/search/s_<sort>/o_<order>/m_<mark>/page_<page>', name="mark_list", options={"page": "1"})  # get search result by catagory and page
@plugin.route('/search/page_<page>', options={"page": "1"})  # get search result by nothing??
def search(page, **kwargs):
    c_list = Meiju.search(page, PAGE_ROWS, **kwargs)
    for one in c_list["data"]["results"]:
        item = ListItem(**{
            'label': one.get("title"),
            'path': plugin.url_for("detail", seasonId=one.get("id")),
            'icon': one["cover"],
            'thumbnail': one["cover"],
        })
        item.set_info("video", {"plot": one.get("brief", ""),
                                "rating ": float(one["score"]),
                                "genre": one["cat"],
                                "season": one["seasonNo"]})
        item.set_is_playable(False)
        yield item
    plugin.set_content('TVShows')


@plugin.route('/album/<albumId>/', name="album")
def get_album(albumId):
    c_list = Meiju.get_album(albumId)
    for one in c_list["data"]["results"]:
        item = ListItem(**{
            'label': one.get("title"),
            'path': plugin.url_for("detail", seasonId=one.get("id")),
            'icon': one["cover"],
            'thumbnail': one["cover"],
        })
        item.set_info("video", {"plot": one.get("brief", ""),
                                "rating ": float(one["score"]),
                                "genre": one["cat"],
                                "season": one["seasonNo"]})
        item.set_is_playable(False)
        yield item
    plugin.set_content('TVShows')


# get season episodes by season id
@plugin.route('/detail/<seasonId>', name="detail")
def video_detail(seasonId):
    detail = Meiju.video_detail(seasonId)
    title = detail["data"]["seasonDetail"]["title"]
    SEASON_CACHE[seasonId] = detail["data"]  # store season detail
    history = HISTORY.get("list", None)
    playing_episode = "0"
    if history is not None:
        for l in history:
            if l["seasonId"] == seasonId:
                playing_episode = l["index"]
    for episode in detail["data"]["seasonDetail"]["episode_brief"]:
        label = title + episode["episode"]
        if episode["episode"] == playing_episode:
            label = "[B]" + colorize(label, "green") + "[/B]"
        item = ListItem(**{
            'label': label,
            'path': plugin.url_for("play_season", seasonId=seasonId, index=episode["episode"], Esid=episode["sid"]),
        })
        item.set_info("video", {"plot": episode["text"],
                                "TVShowTitle": episode["text"],
                                "episode": int(episode["episode"]),
                                "season": 0})
        item.set_is_playable(True)
        yield item
    plugin.set_content('episodes')


@plugin.route('/play/<seasonId>/<index>/<Esid>', name="play_season")
def play(seasonId="", index="", Esid=""):
    season_data = SEASON_CACHE.get(seasonId)
    title = season_data["seasonDetail"]["title"]
    episode_sid = Esid
    rs = RRMJResolver()
    play_url, _ = rs.get_play(seasonId, episode_sid, plugin.get_setting("quality"))
    if play_url is not None:
        add_history(seasonId, index, Esid, title)
        li = ListItem(title, path=play_url)
        plugin.set_resolved_url(li)


def add_history(seasonId, index, Esid, title):
    if "list" not in HISTORY:
        HISTORY["list"] = []
    for l in HISTORY["list"]:
        if l["seasonId"] == seasonId:
            HISTORY["list"].remove(l)
    item = {"seasonId": seasonId,
            "index": index,
            "sid": Esid,
            "season_name": title}
    HISTORY["list"].insert(0, item)


@plugin.route('/history/list')
def list_history():
    if "list" in HISTORY:
        for l in HISTORY["list"]:
            seasonId = l["seasonId"]
            index = l["index"]
            sid = l["sid"]
            yield {
                'label': u"[COLOR green]{title}[/COLOR]  观看到第[COLOR yellow]{index}[/COLOR]集".format(title=l["season_name"], index=l["index"]),
                'path': plugin.url_for("detail", seasonId=seasonId),
                'is_playable': False
            }
