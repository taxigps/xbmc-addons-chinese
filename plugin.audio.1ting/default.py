# -*- coding: utf-8 -*-

import music
import xbmc, xbmcgui, xbmcplugin
import urllib, urllib2, sys

menus = [(1, '歌手'), (11,'随便一听')]

def banner(s):
    return '[COLOR FFDEB887]【%s】[/COLOR]' % s

def addMenu():        #add top directory
    lists = menus
    n = len(lists)
    query = {}
    for mode, name in lists:
        li = xbmcgui.ListItem(name)
        query["mode"] = mode
        u = "%s?%s" % (sys.argv[0], urllib.urlencode(query))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,n)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def addSinger1():
    lists = music.getSingerGroup()
    n = len(lists)
    for url, name in lists:
        if url:
            query = {"mode": 2, "url": url}
        else:
            query = {"mode": -1}
            name = banner(name)
        u = "%s?%s" % (sys.argv[0], urllib.urlencode(query))
        li = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,n)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def addSinger2(url):
    lists = music.getSingerList(url)
    n = len(lists)
    for url, name in lists:
        if url:
            query = {"mode": 3, "url": url}
            icon = music.getSingerIcon(url)
        else:
            query = {"mode": -1}
            name = banner(name)
            icon = ''
        u = "%s?%s" % (sys.argv[0], urllib.urlencode(query))
        li = xbmcgui.ListItem(name)
        li.setIconImage(icon)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,n)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def addSinger3(pUrl, page):           #add the third direcdory, get the directory name from the web page
    lists = music.getSongList(pUrl, page)
    n = len(lists)
    query = {}
    for url, name in lists:
        query["mode"] = 3
        query["url"] = pUrl
        isFolder = True
        if name == '上一页':     # if it's the prior page, deal with the prior page directory, if user click the prior page
            query["page"] = page -1
            name = banner(name)
        elif name == '下一页':     # if it's the next page, deal with the next page directory, if user click the next page
            query["page"] = page +1
            name = banner(name)
        else:
            query["mode"] = 4
            query["url"] = url
            query["name"] = name
            isFolder = False
        u = "%s?%s" % (sys.argv[0], urllib.urlencode(query))
        li = xbmcgui.ListItem(name)     # get the song name, or just the prior or next page
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,isFolder,n)
    xbmcplugin.endOfDirectory(int(sys.argv[1])) 

def addRand():
    lists = music.getRandList()
    n = len(lists)
    query = {"mode": 12}
    for songInfo in lists:
        query.update(songInfo)
        songInfo.pop("song_filepath")
        icon = songInfo.pop("icon")
        name = songInfo["title"]
        li = xbmcgui.ListItem(name)
        li.setInfo(type="Music",infoLabels=songInfo)
        li.setThumbnailImage(icon)
        u = "%s?%s" % (sys.argv[0], urllib.urlencode(query))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,False,n)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def playItem(params):
    songAddress = music.getSongUrl(params['song_filepath'])
    icon = params['icon']
    name = params['title']
    songInfo = {'title': name, 'artist': params['artist'], 'album': params['album']}
    li = xbmcgui.ListItem(name)
    li.setInfo(type='Music',infoLabels=songInfo)
    li.setThumbnailImage(icon)
    xbmc.Player().play(songAddress, li)

def playAudio(url, name):           # play the song according the part url information
    songInfo = music.getSongAddr(url)
    if songInfo and songInfo['url']:
        songAddress = songInfo.pop('url')
        icon = songInfo.pop('icon')
        name = songInfo['title']
        li = xbmcgui.ListItem(name)
        li.setInfo(type="Music",infoLabels=songInfo)
        li.setThumbnailImage(icon)
        xbmc.Player().play(songAddress, li)
    else:
        xbmcgui.Dialog().notification(name, '该歌曲不存在或者由于版权到期而下线!', xbmcgui.NOTIFICATION_ERROR)

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

pMode = int(paramlist.get("mode", 0))
url = paramlist.get("url", "")

if pMode == 0:
    addMenu()
#歌手
elif pMode == 1:
    addSinger1()
elif pMode == 2:
    addSinger2(url)
elif pMode == 3:
    pPage = int(paramlist.get("page", 1))
    addSinger3(url, pPage)
elif pMode == 4:
    name = paramlist.get("name", "")
    playAudio(url, name)
#随便一听
elif pMode == 11:
    addRand()
elif pMode == 12:
    playItem(paramlist)
