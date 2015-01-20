# -*- coding: utf-8 -*-

import music
import xbmc, xbmcgui, xbmcplugin
import urllib, urllib2, sys

def addList(lists):
    #name, mode, icon, area, type, channelId
    n = len(lists)
    plugin = sys.argv[0]
    handle = int(sys.argv[1])
    for item in lists:
        name = item['name']
        mode = item['mode']
        isFolder = music.isFolder(mode)
        li = xbmcgui.ListItem(name)
        icon = item.get('icon', '')
        if icon:
            li.setIconImage(icon)
        u = "%s?%s" % (plugin, urllib.urlencode(item))
        xbmcplugin.addDirectoryItem(handle, u, li, isFolder, n)
    xbmcplugin.endOfDirectory(handle)

def play(params):
    name = params.get("name", "")
    icon = params.get("icon", "")
    channelId = params.get("channelId", "")
    if channelId:
        li = xbmcgui.ListItem(name)
        info = {'title': name}
        li.setInfo(type='Video', infoLabels = info)
        if icon:
            li.setThumbnailImage(icon)
        url = music.getStreamUrl(channelId)
        xbmc.Player().play(url, li)

def get_params():         # get part of the url, help to judge the param of the url, direcdory
    param = {}
    params = sys.argv[2]
    if len(params) >= 2:
        cleanedparams = params.rsplit('?',1)
        if len(cleanedparams) == 2:
            cleanedparams = cleanedparams[1]
        else:
            cleanedparams = params.replace('?','')
        param = dict(urllib2.urlparse.parse_qsl(cleanedparams))
    print(param)
    return param

params = get_params()
mode = params.get("mode", music.MODE_MENU)

l = []
if mode == music.MODE_MENU:
    l = music.getMenu()
elif mode == music.MODE_CHANNELS:
    area = params.get("area", "0")
    type = params.get("type", "0")
    l = music.getChannels(area, type)
elif mode == music.MODE_PLAY:
    play(params)
if l:
    addList(l)
