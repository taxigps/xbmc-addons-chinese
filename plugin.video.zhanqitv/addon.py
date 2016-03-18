# -*- coding: utf-8 -*-
# Module: default
# Author: Albert
# Created on: 17.1.2016
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
# Largely following the example at 
# https://github.com/romanvm/plugin.video.example/blob/master/main.py
import xbmc,xbmcgui,urllib2,re,xbmcplugin,time
from urlparse import parse_qsl
import sys
import json


# Get the plugin url in plugin:// notation.
_url=sys.argv[0]
# Get the plugin handle as an integer number.
_handle=int(sys.argv[1])

def list_categories():

    f = urllib2.urlopen('http://www.zhanqi.tv/api/static/game.lists/100-1.json?rand={ts}'.format(ts=time.time()))

    obj = json.loads(f.read())

    listing=[]
    for game in obj['data']['games']:
        list_item = xbmcgui.ListItem(label=game['name'], thumbnailImage=game['bpic'])
        list_item.setProperty('fanart_image', game['bpic'])
        url='{0}?action=room_list&game_id={1}'.format(_url, game['id'])

        #xbmc.log(url, 1)

        is_folder=True
        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle,listing,len(listing))
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def room_list(game_id):

    f = urllib2.urlopen('http://www.zhanqi.tv/api/static/game.lives/{game_id}/100-1.json?rand={ts}'.format(game_id=game_id, ts=time.time()))

    obj = json.loads(f.read())

    listing=[]
    for room in obj['data']['rooms']:
        list_item = xbmcgui.ListItem(label=room['title'], thumbnailImage=room['bpic'])
        list_item.setProperty('fanart_image', room['bpic'])
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
    f = urllib2.urlopen('http://www.zhanqi.tv/api/static/live.roomid/{room_id}.json?sid='.format(room_id=room_id))
    obj = json.loads(f.read())
    #path = 'http://dlhls.cdn.zhanqi.tv/zqlive/{video}.m3u8'.format(video=obj['data']['videoIdKey']);
    #path = 'http://ebithdl.cdn.zhanqi.tv/zqlive/{video}.flv'.format(video=obj['data']['videoIdKey'])
    path = 'rtmp://wsrtmp.load.cdn.zhanqi.tv/zqlive/{video}'.format(video=obj['data']['videoIdKey'])
    play_item = xbmcgui.ListItem(path=path, thumbnailImage=obj['data']['bpic'])
    play_item.setInfo(type="Video", infoLabels={"Title":obj['data']['title']})
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
    # directly play the item.
    xbmc.Player().play(path, play_item)

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
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
