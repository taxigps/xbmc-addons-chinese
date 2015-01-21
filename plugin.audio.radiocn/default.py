# -*- coding: utf-8 -*-

from music import *
import xbmc, xbmcgui, xbmcplugin
import urllib, urllib2, sys

def addList(lists):
    #name, mode, icon[, area, type, channelId]
    n = len(lists)
    plugin = sys.argv[0]
    handle = int(sys.argv[1])
    for item in lists:
        name = item.pop('name')
        mode = item.get('mode', MODE_NONE)
        icon = item.get('icon', '')
        li = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
        u = '%s?%s' % (plugin, urllib.urlencode(item))
        xbmcplugin.addDirectoryItem(handle, u, li, isFolder(mode), n)
    xbmcplugin.endOfDirectory(handle)

def play(item):
    channelId = item.get('channelId', '')
    if channelId:
        icon = item.get('icon', '')
        name, url = getPlayinfo(channelId)
        li = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
        li.setInfo(type='Video', infoLabels = {'Title': name})
        print('play', url)
        xbmc.Player().play(url, li)

def get_params():
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
mode = params.get('mode', MODE_MENU)

l = []
if mode == MODE_MENU:
    l = getMenu()
elif mode == MODE_CHANNELS:
    area = params.get('area', '0')
    type = params.get('type', '0')
    l = getChannels(area, type)
elif mode == MODE_PLAY:
    play(params)
if l:
    addList(l)
