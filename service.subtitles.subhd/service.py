﻿# -*- coding: utf-8 -*-

import re
import os
import sys
import xbmc
import urllib
import xbmcvfs
import xbmcaddon
import xbmcgui,xbmcplugin
from bs4 import BeautifulSoup
import requests
import simplejson

__addon__ = xbmcaddon.Addon()
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")
__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode("utf-8")
__temp__       = xbmc.translatePath( os.path.join( __profile__, 'temp') ).decode("utf-8")

sys.path.append (__resource__)

SUBHD_API  = 'http://subhd.com/search/%s'
SUBHD_BASE = 'http://subhd.com'
UserAgent  = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'

def log(module, msg):
    xbmc.log((u"%s::%s - %s" % (__scriptname__,module,msg,)).encode('utf-8'),level=xbmc.LOGDEBUG )

def normalizeString(str):
    return str

def session_get(url, id='', referer='', token=''):
    if id:
        HEADERS={'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Host': 'subhd.com',
            'Origin': 'http://subhd.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0'}
        s = requests.Session()
        s.headers.update(HEADERS)
        r = s.get(referer)
        s.headers.update({'Referer': referer})
        r = s.post(url, data={'sub_id': id, 'd_token': token})
        return r.content
    else:
        HEADERS={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0'}
        s = requests.Session()
        s.headers.update(HEADERS)
        r = s.get(url)
        return r.content

def Search( item ):
    subtitles_list = []

    log(sys._getframe().f_code.co_name, "Search for [%s] by name" % (os.path.basename( item['file_original_path'] ),))
    if item['mansearch']:
        search_string = item['mansearchstr']
    elif len(item['tvshow']) > 0:
        search_string = "%s S%.2dE%.2d" % (item['tvshow'],
                                           int(item['season']),
                                           int(item['episode']))
    else:
        search_string = item['title']
    url = SUBHD_API % (urllib.quote(search_string))
    data = session_get(url)
    try:
        soup = BeautifulSoup(data, "html.parser")
    except:
        return

    results = soup.find_all("div", class_="box")

    # if can't find subtitle for the specified episode, try the whole season instead
    if (len(results) == 0) and (len(item['tvshow']) > 0):
        search_string = "%s S%.2d" % (item['tvshow'], int(item['season']))
        url = SUBHD_API % (urllib.quote(search_string))
        data = session_get(url)
        try:
            soup = BeautifulSoup(data, "html.parser")
        except:
            return
        results = [x for x in soup.find_all("div", class_="box") if x.find('div', class_='tvlist')]

    for it in results:
        link = SUBHD_BASE + it.find("div", class_="d_title").a.get('href').encode('utf-8')
        version = it.find("div", class_="d_title").a.get('title').encode('utf-8')
        if version.find('本字幕按 ') == 0:
            version = version.split()[1]
        try:
            group = it.find("div", class_="d_zu").text.encode('utf-8')
            if group.isspace():
                group = ''
        except:
            group = ''
        if group and (version.find(group) == -1):
            version += ' ' + group
        try:
            r2 = it.find_all("span", class_="label")
            langs = [x.text.encode('utf-8') for x in r2][:-1]
        except:
            langs = '未知'
        name = '%s (%s)' % (version, ",".join(langs))
        if ('英文' in langs) and not(('简体' in langs) or ('繁体' in langs)):
            subtitles_list.append({"language_name":"English", "filename":name, "link":link, "language_flag":'en', "rating":"0", "lang":langs})
        else:
            subtitles_list.append({"language_name":"Chinese", "filename":name, "link":link, "language_flag":'zh', "rating":"0", "lang":langs})

    if subtitles_list:
        for it in subtitles_list:
            listitem = xbmcgui.ListItem(label=it["language_name"],
                                        label2=it["filename"],
                                        iconImage=it["rating"],
                                        thumbnailImage=it["language_flag"]
                                       )

            listitem.setProperty( "sync", "false" )
            listitem.setProperty( "hearing_imp", "false" )

            url = "plugin://%s/?action=download&link=%s&lang=%s" % (__scriptid__,
                                                                    it["link"],
                                                                    it["lang"]
                                                                    )
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

def rmtree(path):
    if isinstance(path, unicode):
        path = path.encode('utf-8')
    dirs, files = xbmcvfs.listdir(path)
    for dir in dirs:
        rmtree(os.path.join(path, dir))
    for file in files:
        xbmcvfs.delete(os.path.join(path, file))
    xbmcvfs.rmdir(path)

def Download(url,lang):
    try: rmtree(__temp__)
    except: pass
    try: os.makedirs(__temp__)
    except: pass

    referer = url
    subtitle_list = []
    exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
    try:
        data = session_get(url)
        soup = BeautifulSoup(data, "html.parser")
        id = soup.find("button", class_="btn btn-danger btn-sm").get("sid").encode('utf-8')
        token = soup.select_one("#down").attrs['dtoken']
        url = "http://subhd.com/ajax/down_ajax"
        data = session_get(url, id=id, referer=referer, token=token)
        json_response = simplejson.loads(data)
        if json_response['success']:
            url = json_response['url'].replace(r'\/','/').decode("unicode-escape").encode('utf-8')
            if url[:4] <> 'http':
                url = 'http://subhd.com%s' % (url)
            log(sys._getframe().f_code.co_name, "Downloading %s" % (url.decode('utf-8')))
            data = session_get(url)
        else:
            msg = json_response['msg'].decode("unicode-escape")
            xbmc.executebuiltin((u'XBMC.Notification("subhd","%s")' % (msg)).encode('utf-8'), True)
            data = ''
    except:
        log(sys._getframe().f_code.co_name, "%s (%d) [%s]" % (
               sys.exc_info()[2].tb_frame.f_code.co_name,
               sys.exc_info()[2].tb_lineno,
               sys.exc_info()[1]
               ))
        return []
    if len(data) < 1024:
        return []
    zip = os.path.join(__temp__, "subtitles%s" % os.path.splitext(url)[1])
    with open(zip, "wb") as subFile:
        subFile.write(data)
    subFile.close()
    xbmc.sleep(500)
    if data[:4] == 'Rar!' or data[:2] == 'PK':
        xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (zip,__temp__,)).encode('utf-8'), True)
    path = __temp__
    dirs, files = xbmcvfs.listdir(path)
    if ('__MACOSX') in dirs:
        dirs.remove('__MACOSX')
    if len(dirs) > 0:
        path = os.path.join(__temp__, dirs[0].decode('utf-8'))
        dirs, files = xbmcvfs.listdir(path)
    list = []
    for subfile in files:
        if (os.path.splitext( subfile )[1] in exts):
            list.append(subfile.decode('utf-8'))
    if len(list) == 1:
        subtitle_list.append(os.path.join(path, list[0]))
    elif len(list) > 1:
        sel = xbmcgui.Dialog().select('请选择压缩包中的字幕', list)
        if sel == -1:
            sel = 0
        subtitle_list.append(os.path.join(path, list[sel]))

    return subtitle_list

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=paramstring
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

params = get_params()
if params['action'] == 'search' or params['action'] == 'manualsearch':
    item = {}
    item['temp']               = False
    item['rar']                = False
    item['mansearch']          = False
    item['year']               = xbmc.getInfoLabel("VideoPlayer.Year")                           # Year
    item['season']             = str(xbmc.getInfoLabel("VideoPlayer.Season"))                    # Season
    item['episode']            = str(xbmc.getInfoLabel("VideoPlayer.Episode"))                   # Episode
    item['tvshow']             = normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))   # Show
    item['title']              = normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle")) # try to get original title
    item['file_original_path'] = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))  # Full path of a playing file
    item['3let_language']      = []

    if 'searchstring' in params:
        item['mansearch'] = True
        item['mansearchstr'] = params['searchstring']

    for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
        item['3let_language'].append(xbmc.convertLanguage(lang,xbmc.ISO_639_2))

    if item['title'] == "":
        item['title']  = xbmc.getInfoLabel("VideoPlayer.Title")                       # no original title, get just Title
        if item['title'] == os.path.basename(xbmc.Player().getPlayingFile()):         # get movie title and year if is filename
            title, year = xbmc.getCleanMovieTitle(item['title'])
            item['title'] = normalizeString(title.replace('[','').replace(']',''))
            item['year'] = year

    if item['episode'].lower().find("s") > -1:                                        # Check if season is "Special"
        item['season'] = "0"                                                          #
        item['episode'] = item['episode'][-1:]

    if ( item['file_original_path'].find("http") > -1 ):
        item['temp'] = True

    elif ( item['file_original_path'].find("rar://") > -1 ):
        item['rar']  = True
        item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

    elif ( item['file_original_path'].find("stack://") > -1 ):
        stackPath = item['file_original_path'].split(" , ")
        item['file_original_path'] = stackPath[0][8:]

    Search(item)

elif params['action'] == 'download':
    subs = Download(params["link"], params["lang"])
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
