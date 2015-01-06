# -*- coding: utf-8 -*-

import music
import xbmc, xbmcgui, xbmcplugin
import urllib, urllib2, sys

def addList(lists):
    #name, mode, url, icon, info
    n = len(lists)
    plugin = sys.argv[0]
    handle = int(sys.argv[1])
    for i in lists:
        name = i[0]
        mode = i[1] if len(i) > 1 else music.MODE_NONE
        isFolder = music.isFolder(mode)
        query = {"mode": mode}
        if len(i) > 2: query["url"] = i[2]
        li = xbmcgui.ListItem(name)
        if len(i) > 3:
            icon = i[3]
            query['icon'] = icon
            li.setIconImage(icon)
        if len(i) > 4:
            info = i[4]
            query.update(info)
            li.setInfo(type="Music",infoLabels=info)
            isFolder = False
        u = "%s?%s" % (plugin, urllib.urlencode(query))
        xbmcplugin.addDirectoryItem(handle, u, li, isFolder, n)
    xbmcplugin.endOfDirectory(handle)

def play(name, mode, url, icon, info):
    li = xbmcgui.ListItem(name)
    li.setInfo(type='Music', infoLabels=info)
    li.setThumbnailImage(icon)
    url = music.getSongUrl(url)
    xbmc.Player().play(url, li)

def playItem(params):
    name = params['title']
    icon = params['icon']
    mode = params['mode']
    url = params['url']
    info = {'title': name, 'artist': params['artist'], 'album': params['album']}
    play(name, mode, url, icon, info)

def playSong(url):
    song = music.getSongList(url)
    if song:
        name, mode, url, icon, info = song[0]
        play(name, mode, url, icon, info)
    else:
        xbmcgui.Dialog().notification(url, '该歌曲不存在或者由于版权到期而下线!', xbmcgui.NOTIFICATION_ERROR)

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

paramlist = get_params()

pMode = int(paramlist.get("mode", music.MODE_MENU))
url = paramlist.get("url", "")

l = music.getList(pMode, url)
if l:
    addList(l)
elif pMode == music.MODE_SONG:
    playSong(url)
elif pMode == music.MODE_SONG_ITEM:
    playItem(paramlist)
