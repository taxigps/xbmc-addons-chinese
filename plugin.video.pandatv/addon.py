# -*- coding: utf-8 -*-
# Module: default
# Author: Yangqian;tclh123
# Created on: 25.12.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
# Largely following the example at
# https://github.com/romanvm/plugin.video.example/blob/master/main.py

import re
import sys
import json
import time
import logging
from urlparse import parse_qsl

import xbmc,xbmcgui,urllib2,re,xbmcplugin

TITLE_PATTERN = '{author}:{topic}:{view_count}'
RE_ROOM_INFOS = re.compile(r"""<span class="video-title" title=".*?">(.*?)</span>\s*<span class="video-nickname">\s*<i class="icon-host-level.*"></i>\s*(.*?)\s*</span>\s*<span class="video-number">(.*?)</span>""")
RE_ROOM_IMG = re.compile(r'<img class="video-img.*" data-original="(.*?)" alt=".*?">')


def post(url, data):
    req = urllib2.Request(url)
    #enable cookie
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data)
    return response.read()

# Get the plugin url in plugin:// notation.
_url=sys.argv[0]
# Get the plugin handle as an integer number.
_handle=int(sys.argv[1])

def list_categories():

    f = urllib2.urlopen('http://api.m.panda.tv/ajax_get_all_subcate?__version=1.0.5.1098&__plat=iOS')

    obj = json.loads(f.read())

    listing=[]

    list_item = xbmcgui.ListItem(label='全部直播')
    # list_item.setProperty('fanart_image', game['img'])
    url='{0}?action=all'.format(_url)
    listing.append((url, list_item, True))

    for game in obj['data']:
        list_item = xbmcgui.ListItem(label=game['cname'], thumbnailImage=game['img'])
        list_item.setProperty('fanart_image', game['img'])
        url='{0}?action=room_list&game_id={1}'.format(_url, game['ename'])

        is_folder=True
        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle,listing,len(listing))
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


# def all_list():
#     html = urllib2.urlopen('https://www.panda.tv/all').read()
# 
#     room_ids = re.findall(r'<a href="/\d+" class="video-list-item-wrap" data-id="(\d+)">', html)
#     room_infos = RE_ROOM_INFOS.findall(html, re.MULTILINE)
#     room_imgs = RE_ROOM_IMG.findall(html)
# 
#     listing=[]
#     for i, room_id in enumerate(room_ids):
#         room_name, author, view_count = room_infos[i]
#         img = room_imgs[i]
#         title = TITLE_PATTERN.format(topic=room_name, author=author, view_count=view_count)
#         list_item = xbmcgui.ListItem(label=title, thumbnailImage=img)
#         list_item.setProperty('fanart_image', img)
#         url='{0}?action=play&room_id={1}'.format(_url, room_id)
#         is_folder=False
#         listing.append((url, list_item, is_folder))
#     xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
#     xbmcplugin.endOfDirectory(_handle)


def room_list(game_id):
    if game_id == 'ALL':
        apiurl = 'http://api.m.panda.tv/ajax_live_lists'
        params = 'pageno=1&pagenum=100&status=2&order=person_num&sproom=1&__version=2.0.1.1481&__plat=android&banner=1'
    else:
        apiurl = "http://api.m.panda.tv/ajax_get_live_list_by_cate"
        params = "__plat=iOS&__version=1.0.5.1098&cate={ename}&order=person_num&pageno=1&pagenum=100&status=2".format(ename=game_id)

    returndata = post(apiurl, params);

    obj = json.loads(returndata)

    listing=[]
    for room in obj['data']['items']:
        title = TITLE_PATTERN.format(topic=room['name'].encode('utf-8'), author=room['userinfo']['nickName'].encode('utf-8'), view_count=room['person_num'].encode('utf-8'))
        list_item = xbmcgui.ListItem(label=title, thumbnailImage=room['pictures']['img'])
        list_item.setProperty('fanart_image', room['pictures']['img'])
        url='{0}?action=play&room_id={1}'.format(_url, room['id'])
        is_folder=False
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(room_id):
    """
    Play a video by the provided path.
    :param path: str
    :return: None
    """
    r = get_panda_url(room_id)
    if r:
        path, play_item = r
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
        # directly play the item.
        xbmc.Player().play(path, play_item)


def get_panda_url(roomid):
    json_request_url ="http://www.panda.tv/api_room_v2?roomid={}&__plat=pc_web&_={}".format(roomid, int(time.time()))
    f = urllib2.urlopen(json_request_url)
    content = f.read()
    api_json = json.loads(content)

    errno = api_json["errno"]
    errmsg = api_json["errmsg"]
    if errno:
        msg = "Errno : {}, Errmsg : {}".format(errno, errmsg)
        xbmcgui.Dialog().ok('提示框', msg)
        logging.error(msg)
        return

    data = api_json["data"]
    topic = data["roominfo"]["name"]
    author = data['hostinfo']['name']
    view_count = data['roominfo']['person_num']
    title = TITLE_PATTERN.format(topic=topic.encode('utf-8'), author=author.encode('utf-8'), view_count=view_count.encode('utf-8'))
    room_key = data["videoinfo"]["room_key"]
    plflag = data["videoinfo"]["plflag"].split("_")
    status = data["videoinfo"]["status"]
    if status != "2":
        msg = "The live stream is not online! (status:%s)" % status
        xbmcgui.Dialog().ok('提示框', msg)
        logging.error(msg)
        return

    data2 = json.loads(data["videoinfo"]["plflag_list"])
    rid = data2["auth"]["rid"]
    sign = data2["auth"]["sign"]
    ts = data2["auth"]["time"]
    real_url = "http://pl{}.live.panda.tv/live_panda/{}.flv?sign={}&ts={}&rid={}".format(plflag[1], room_key, sign, ts, rid)

    play_item = xbmcgui.ListItem(path=real_url, thumbnailImage=data['hostinfo']['avatar'])
    play_item.setInfo(type="Video", infoLabels={"Title": title})

    return real_url, play_item


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring:
    :return:
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'room_list':
            # Display the list of videos in a provided category.
            room_list(params['game_id'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['room_id'])
        elif params['action'] == 'all':
            # all_list()
            room_list('ALL')
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
