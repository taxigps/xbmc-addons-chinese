# -*- coding: utf-8 -*-

import DoubanFM
import xbmcplugin,xbmcgui,xbmc
import urllib,urllib2,re,os

def CATEGORIES():
    channels = DoubanFM.GetChannels()
    n = len(channels)
    for name, url in channels:
        addLink(name.encode('utf-8'), str(url), 1, n)

def PlayList(url):
    playlist=xbmc.PlayList(0) 
    playlist.clear()  

    #add song to playlist
    songs = DoubanFM.GetSongs(url)
    for song in songs:
        pic = song.pop('pic')
        url = song.pop('url')
        listitem=xbmcgui.ListItem(song['title'])
        listitem.setInfo('Music', song)
        listitem.setThumbnailImage(pic)
        playlist.add(url, listitem)

    print 'Added '+str(playlist.size()) + ' songs'
    xbmc.Player().play(playlist)

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]
                            
    return param

def addLink(name,url,mode,totalItems):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    liz=xbmcgui.ListItem(name)
    liz.setInfo( type="Music", infoLabels={ "Title": name } )
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,liz, False, totalItems)

params=get_params()
url=None
name=None
mode=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

print "Current select: "+"Mode: "+str(mode) + "  URL: "+str(url) + "  Name: "+str(name)
if mode==None:
    print "CATEGORIES()"
    CATEGORIES()
elif mode==1:
    print "PlayList()"
    PlayList(url) 

xbmcplugin.endOfDirectory(int(sys.argv[1]))
