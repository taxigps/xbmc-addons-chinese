# -*- coding: utf-8 -*-
# Module: default
# Author: Yangqian
# Created on: 26.12.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
# Largely following the example at 
# https://github.com/romanvm/plugin.video.example/blob/master/main.py
#get from https://github.com/chrippa/livestreamer/blob/develop/src/livestreamer/plugins/douyutv.py
#further from https://github.com/soimort/you-get/issues/580
#and from https://github.com/yan12125/douyu-hack


from contextlib import contextmanager, closing, nested
import requests
import xbmc,xbmcgui,urllib2,re,xbmcplugin
from bs4 import BeautifulSoup
from urlparse import parse_qsl
import sys
import json,urllib
import hashlib,time,uuid
import xbmcaddon
import HTMLParser
import logging
from BulletScreen import BulletScreen
from douyudanmu import douyudanmu
from Douyu import Douyu_HTTP_Server
pars=HTMLParser.HTMLParser()
__addon__ = xbmcaddon.Addon()
__language__=__addon__.getLocalizedString
API_URL = "http://www.douyutv.com/swf_api/room/{0}?cdn={1}&nofan=yes&_t={2}&sign={3}"
API_SECRET = u'bLFlashflowlad92'
PAGE_LIMIT=10
NEXT_PAGE=__language__(32001)
headers={'Accept':
     'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Encoding': 'gzip, deflate','User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:16.0) Gecko/20100101 Firefox/16.0'}

APPKEY = 'Y237pxTx2In5ayGz' #from android-hd client (https://gist.github.com/ERioK/d73f76dbb0334618ff905f1bf3363401)

#Initialize logging
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(module)s][%(funcName)s] %(message)s')


TORRENT2HTTP_POLL = 1000
XBFONT_LEFT = 0x00000000
XBFONT_RIGHT = 0x00000001
XBFONT_CENTER_X = 0x00000002
XBFONT_CENTER_Y = 0x00000004
XBFONT_TRUNCATED = 0x00000008
XBFONT_JUSTIFY = 0x00000010

VIEWPORT_WIDTH = 1920.0
VIEWPORT_HEIGHT = 1088.0
OVERLAY_WIDTH = int(VIEWPORT_WIDTH * 0.4) # 70% size
OVERLAY_HEIGHT = 150


# Get the plugin url in plugin:// notation.
_url=sys.argv[0]
# Get the plugin handle as an integer number.
_handle=int(sys.argv[1])

def list_categories(offset):
    #f=urllib2.urlopen('http://www.douyutv.com/directory')
    #rr=BeautifulSoup(f.read())
    rr=BeautifulSoup(requests.get('http://www.douyutv.com/directory',headers=headers).text)
    catel=rr.findAll('a',{'class':'thumb'},limit=offset+PAGE_LIMIT+1)
    rrr=[(x['href'], x.p.text,x.img['data-original']) for x in catel]
    offset=int(offset)
    if offset+PAGE_LIMIT<len(rrr):
      rrr=rrr[offset:offset+PAGE_LIMIT]
      nextpageflag=True
    else:
      rrr=rrr[offset:]
      nextpageflag=False
    listing=[]
    for classname,textinfo,img in rrr:
        list_item=xbmcgui.ListItem(label=textinfo,thumbnailImage=img)
        #list_item.setProperty('fanart_image',img)
        url=u'{0}?action=listing&category={1}&offset=0'.format(_url,classname)
        is_folder=True
        listing.append((url,list_item,is_folder))
    if nextpageflag==True:
        list_item=xbmcgui.ListItem(label=NEXT_PAGE)
        url=u'{0}?offset={1}'.format(_url,str(offset+PAGE_LIMIT))
        is_folder=True
        listing.append((url,list_item,is_folder))
    xbmcplugin.addDirectoryItems(_handle,listing,len(listing))
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle) 

def list_videos(category,offset=0):
    #request=urllib2.Request('http://www.douyu.com'+category,headers=headers)
    #f=urllib2.urlopen(request)
    #f=urllib2.urlopen('http://www.douyu.com'+category)
    #r=f.read()
    #rr=BeautifulSoup(r)
    rr=BeautifulSoup(requests.get('http://www.douyu.com'+category,headers=headers).text)
    videol=rr.findAll('a',{'class':'play-list-link'},limit=offset+PAGE_LIMIT+1)
    listing=[]
    #with open('rooml.dat','w') as f:
    #  f.writelines([str(x) for x in videol])
    if offset+PAGE_LIMIT<len(videol):
      videol=videol[offset:offset+PAGE_LIMIT]
      nextpageflag=True
    else:
      videol=videol[offset:]
      nextpageflag=False
    for x in videol:
        roomid=x['href'][1:]
        img=x.img['data-original']
        title=x['title']
        nickname=x.find('span',{'class':'dy-name ellipsis fl'}).text
        view=x.find('span',{'class':'dy-num fr'}).text
        liveinfo=u'{0}:{1}:{2}'.format(nickname,title,view)
        list_item=xbmcgui.ListItem(label=liveinfo,thumbnailImage=img)
        #list_item.setProperty('fanart_image',img)
        url='{0}?action=play&video={1}'.format(_url,roomid)
        is_folder=False
        listing.append((url,list_item,is_folder))
    if nextpageflag==True:
        list_item=xbmcgui.ListItem(label=NEXT_PAGE)
        url='{0}?action=listing&category={1}&offset={2}'.format(_url,category,offset+PAGE_LIMIT)
        is_folder=True
        listing.append((url,list_item,is_folder))
    xbmcplugin.addDirectoryItems(_handle,listing,len(listing))
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle) 

def get_room(roomid,cdn):
      ts = int(time.time()/60)
      sign = hashlib.md5(("{0}{1}{2}".format(roomid, API_SECRET, ts)).encode("utf-8")).hexdigest()
      url=API_URL.format(roomid, cdn, ts, sign)
      res = urllib2.urlopen(url).read()
      room=json.loads(res)
      #with open('room.dat','w') as f:
      #  f.writelines([str(cdn),str(ts),str(sign),url,str(room)])
      return room


# def get_play_item_old(room):
#       img=room['data']['owner_avatar']
#       nickname=room['data']['nickname']
#       roomname=room['data']['room_name']
#       roomid=room['data']['room_id']
#       cdn=room['data']['rtmp_cdn']
#       combinedname=pars.unescape(u'{0}:{1}:{3}?cdn={2}'.format(nickname,roomname,cdn,roomid))
#       baseurl=room['data']['rtmp_url']
#       vbest=room['data']['rtmp_live']
#       multi_bitrate=room['data']['rtmp_multi_bitrate']
#       if len(multi_bitrate)!=0:
#         v900=room['data']['rtmp_multi_bitrate']['middle2']
#         v500=room['data']['rtmp_multi_bitrate']['middle']
#       else:
#         v900=vbest
#         v500=vbest
#       if __addon__.getSetting("videoQuality") == "0":
#           vquality=vbest
#       elif __addon__.getSetting("videoQuality") == "1":
#           vquality=v900
#       else:
#           vquality=v500
#       path='{0}/{1}'.format(baseurl,vquality)
#       play_item = xbmcgui.ListItem(combinedname,path=path,thumbnailImage=img)
#       play_item.setInfo(type="Video",infoLabels={"Title":combinedname})
#       return (path,play_item)


# def get_play_item(roomid, cdn):
#     html = urllib2.urlopen("http://www.douyu.com/%s" % (roomid)).read().decode('utf-8')
#     match = re.search(r'"room_id"\s*:\s*(\d+),', html)
#     if match:
#         if match.group(0) != u'0':
#             roomid = match.group(1)
# 
#     json_request_url = "http://m.douyu.com/html5/live?roomId=%s" % roomid
#     res = json.loads(urllib2.urlopen(json_request_url).read().decode('utf-8'))
#     status = res.get('error', 0)
#     if status is not 0:
#         logging.error('Unable to get information for roomid: %s' % (roomid))
#         return '', None #Error
#     data = res['data']
#     if data['show_status'] != u'1':
#         logging.error('The live stream is not online.')
#         return '', None #The live stream is not online
#     img=data['avatar']
#     nickname=data['nickname']
#     roomname=data['room_name']
#     combinedname=pars.unescape(u'{0}:{1}:{3}?cdn={2}'.format(nickname,roomname,cdn,roomid))
# 
# 
#     tt = int(time.time()) 
#     did = uuid.uuid4().hex.upper()
#     sign_content = 'lapi/live/thirdPart/getPlay/{0}?aid=pcclient&cdn={1}&rate={2}&time={3}9TUk5fjjUjg9qIMH3sdnh'.format(roomid,
#             cdn, '0', tt).encode("ascii")
#     sign = hashlib.md5(sign_content.encode('utf-8')).hexdigest()
#     headers = {"auth": sign, "time": str(tt), "aid": "pcclient"}
# 
#     json_request_url = "https://coapi.douyucdn.cn/lapi/live/thirdPart/getPlay/{0}?cdn={1}&rate={2}".format(roomid,
#             cdn, '0')
#     content = urllib2.urlopen(urllib2.Request(json_request_url,
#         headers=headers)).read()
# 
#     res = json.loads(content.decode('utf-8'))
#     status = res.get('error', 0)
#     if status is not 0:
#         logging.error('Unable to get URL for roomid: %s' % (roomid))
#         return '', None #Error
#     data = res['data']
#     path = data.get('live_url')
#     play_item = xbmcgui.ListItem(combinedname,path=path,thumbnailImage=img)
#     play_item.setInfo(type="Video",infoLabels={"Title":combinedname})
#     return (roomid,path,play_item)


def get_play_item(roomid, cdn):
    html = urllib2.urlopen("http://www.douyu.com/%s" % (roomid)).read().decode('utf-8')
    match = re.search(r'"room_id"\s*:\s*(\d+),', html)
    if match:
        if match.group(0) != u'0':
            roomid = match.group(1)

    authstr = 'room/{0}?aid=androidhd1&cdn={1}&client_sys=android&time={2}'.format(roomid, cdn, int(time.time()))
    authmd5 = hashlib.md5((authstr + APPKEY).encode()).hexdigest()
    url = 'https://capi.douyucdn.cn/api/v1/{0}&auth={1}'.format(authstr,authmd5)
    res = requests.get(url).json()

    status = res.get('error', 0)
    if status is not 0:
        logging.error('Unable to get information for roomid: %s' % (roomid))
        return '', None #Error
    data = res['data']
    if data['show_status'] != u'1':
        logging.error('The live stream is not online.')
        return '', None #The live stream is not online
    img=data['owner_avatar']
    nickname=data['nickname']
    roomname=data['room_name']
    combinedname=pars.unescape(u'{0}:{1}:{3}?cdn={2}'.format(nickname,roomname,cdn,roomid))

    realurl = data.get('rtmp_url')+'/'+ data.get('rtmp_live')
    # hls = data.get('hls_url')

    path = realurl
    play_item = xbmcgui.ListItem(combinedname,path=path,thumbnailImage=img)
    play_item.setInfo(type="Video",infoLabels={"Title":combinedname})
    return (roomid,path,play_item)


def play_video(roomid):
    """
    Play a video by the provided path.
    :param path: str
    :return: None
    """
    cdnindex=__addon__.getSetting("cdn")
    player=xbmc.Player()
    cdndict={"0":"","1":"ws","2":"ws2","3":"lx","4":"dl","5":"tct"}
    cdn=cdndict[cdnindex]
    # directly play the item.
    roomid,path,play_item=get_play_item(roomid, cdn)
    logging.debug(path)
    if path == '':
        return
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
    douyu=Douyu_HTTP_Server()
    path=douyu.proxy(path)
    player.play(path, play_item)
    if __addon__.getSetting("danmu") == "true":
        colordict={"0":"FF0000", "1":"00FF00", "2":"0000FF", "3":"FFFFFF", "4":"000000"}
        fontdict={"0":"normal","1":"large"}
        speeddict={"0":20000,"1":10000}
        positiondict={"0":"up","1":"down"}
        textColor="{:X}".format(int(__addon__.getSetting("textAlpha"))) + colordict[__addon__.getSetting("textColor")]
        fontSize=fontdict[__addon__.getSetting("fontSize")]
        position=positiondict[__addon__.getSetting("position")]
        speed=speeddict[__addon__.getSetting("speed")]
        bs = BulletScreen(textColor=textColor, position=position, fontSize=fontSize, speed=speed)
        while not player.isPlaying():
          xbmc.sleep(100)
        danmu=douyudanmu(roomid)
        while not xbmc.abortRequested and player.isPlaying():
          s=danmu.get_danmu()
          if len(s)!=0:
              bs.addText(s)
        bs.exit()
        danmu.exit()
        douyu.exit()
    else:
        douyu.wait_for_idle(1)


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
    if 'action' in params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params['category'],int(params['offset']))
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        if 'offset' in params:
          list_categories(int(params['offset']))
        else:
          list_categories(0)


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
