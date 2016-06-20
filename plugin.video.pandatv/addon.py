# -*- coding: utf-8 -*-
# Module: default
# Author: Yangqian
# Created on: 25.12.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
# Largely following the example at 
# https://github.com/romanvm/plugin.video.example/blob/master/main.py
import xbmc,xbmcgui,urllib2,re,xbmcplugin
from urlparse import parse_qsl
import sys
import json

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


def room_list(game_id):

    apiurl = "http://api.m.panda.tv/ajax_get_live_list_by_cate";
    params = "__plat=iOS&__version=1.0.5.1098&cate={ename}&order=person_num&pageno=1&pagenum=100&status=2".format(ename=game_id)

    returndata = post(apiurl, params);

    obj = json.loads(returndata)

    listing=[]
    for room in obj['data']['items']:
        list_item = xbmcgui.ListItem(label=room['name'], thumbnailImage=room['pictures']['img'])
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
    f = urllib2.urlopen('http://www.panda.tv/api_room?roomid={room_id}'.format(room_id=room_id))
    obj = json.loads(f.read())
    path = 'http://pl3.live.panda.tv/live_panda/{video}.flv'.format(video=obj['data']['videoinfo']['room_key'])
    play_item = xbmcgui.ListItem(path=path, thumbnailImage=obj['data']['hostinfo']['avatar'])
    play_item.setInfo(type="Video", infoLabels={"Title":obj['data']['roominfo']['name']})
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
