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
        li = xbmcgui.ListItem(name)
        isFolder = music.isFolder(mode)
        query = {"mode": mode}
        if len(i) > 2: query["url"] = i[2]
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

def playSong(params):
    name = params['title']
    mode = params['mode']
    url = params['url']
    icon = params['icon']
    info = {'title': name, 'artist': params['artist'], 'album': params['album']}
    play(name, mode, url, icon, info)

def playList(url):
    song = music.getPlayList(url)[0]
    if len(song) == 5:
        play(*song)
    else:
        xbmcgui.Dialog().notification(url, song[0], xbmcgui.NOTIFICATION_ERROR)

def get_keyword():
    try:
        import ChineseKeyboard as m
    except:
        m = xbmc
    keyboard = m.Keyboard('','请输入歌名,专辑或歌手进行搜索,支持简拼.')
    #xbmc.sleep(1500)
    keyboard.doModal()
    if keyboard.isConfirmed():
        keyword = keyboard.getText()
        return keyword

def search():
    q = get_keyword()
    if q:
        url = music.getSearchUrl(q)
        return music.getSearchList(url)
    else:
        return []

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

paramlist = get_params()
mode = paramlist.get("mode", music.MODE_MENU)
url = paramlist.get("url", "")

l = []

if mode == music.MODE_SONG:
    playSong(paramlist)
elif mode == music.MODE_PLAYLIST:
    playList(url)
elif mode == music.MODE_SEARCH:
    l = search()
else:
    l = music.getList(mode, url)
if l:
    addList(l)
