# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import urllib.parse
import urllib.request
import json
import xbmcvfs
import requests
import xbmcaddon
import xbmcgui,xbmcplugin
from bs4 import BeautifulSoup
import time

__addon__      = xbmcaddon.Addon()
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') )
__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
__temp__       = xbmc.translatePath( os.path.join( __profile__, 'temp') )

sys.path.append (__resource__)

try:
    loc = [i for i in requests.get('http://www.rrys.tv', allow_redirects=False).text.split() if 'location.href' in i ][0]
    loc = loc.split('=')[1].strip('"').strip("'")
    # http://www.zmz2019.com/rrys/index.html to http://www.zmz2019.com
    ZIMUZU_BASE = "/".join(loc.split('/')[:3])
except:
    ZIMUZU_BASE = 'http://www.zimuzu.tv'

ZIMUZU_API = ZIMUZU_BASE + '/search?keyword=%s&type=subtitle'
UserAgent  = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'

def log(module, msg):
    xbmc.log("{0}::{1} - {2}".format(__scriptname__,module,msg) ,level=xbmc.LOGDEBUG )

def GetHttpData(url, data=''):
    log(sys._getframe().f_code.co_name, "url [%s]" % (url))
    if data:
        req = urllib.request.Request(url, data)
    else:
        req = urllib.request.Request(url)
    req.add_header('User-Agent', UserAgent)
    try:
        response = urllib.request.urlopen(req)
        httpdata = response.read()
        response.close()
    except:
        log(sys._getframe().f_code.co_name, "Error (%d) [%s]" % (
               sys.exc_info()[2].tb_lineno,
               sys.exc_info()[1]
               ))
        return ''
    return httpdata

def Search( item ):
    subtitles_list = []

    log(sys._getframe().f_code.co_name, "Search for [%s] by name" % (os.path.basename( item['file_original_path'] )))
    if item['mansearch']:
        search_string = item['mansearchstr']
    elif len(item['tvshow']) > 0:
        search_string = "%s S%.2dE%.2d" % (item['tvshow'],
                                           int(item['season']),
                                           int(item['episode']),)
    else:
        search_string = item['title']
    url = ZIMUZU_API % (urllib.parse.quote(search_string))
    data = GetHttpData(url)
    try:
        soup = BeautifulSoup(data, 'html.parser')
    except:
        return
    results = soup.find_all("div", class_="search-item")
    for it in results:
        link = ZIMUZU_BASE + it.find("div", class_="fl-info").a.get('href')
        title = it.find("strong", class_="list_title").text
        subtitles_list.append({"language_name":"Chinese", "filename":title, "link":link, "language_flag":'zh', "rating":"0"})

    if subtitles_list:
        for it in subtitles_list:
            listitem = xbmcgui.ListItem(label=it["language_name"],
                                        label2=it["filename"])
            listitem.setArt({'icon': it["rating"], 'thumb': it["language_flag"]})
            listitem.setProperty( "sync", "false" )
            listitem.setProperty( "hearing_imp", "false" )

            url = "plugin://%s/?action=download&link=%s" % (__scriptid__,
                                                            it["link"]
                                                            )
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

def Download(url):
    if not xbmcvfs.exists(__temp__.replace('\\','/')):
        xbmcvfs.mkdirs(__temp__)
    dirs, files = xbmcvfs.listdir(__temp__)
    for file in files:
        xbmcvfs.delete(os.path.join(__temp__, file))

    subtitle_list = []
    exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
    try:
        data = GetHttpData(url)
        soup = BeautifulSoup(data, 'html.parser')
        url = soup.find("div", class_="subtitle-links").a.get('href')
        url = url.replace('subtitle.html', 'api/v1/static/subtitle/detail')
        data = json.loads(GetHttpData(url))
        if data['info'] != 'OK':
            return []
        url = data['data']['info']['file']
        data = GetHttpData(url)
    except:
        return []
    if len(data) < 1024:
        return []
    t = time.time()
    ts = time.strftime("%Y%m%d%H%M%S",time.localtime(t)) + str(int((t - int(t)) * 1000))
    tmpfile = os.path.join(__temp__, "subtitles%s%s" % (ts, os.path.splitext(url)[1])).replace('\\','/')
    with open(tmpfile, "wb") as subFile:
        subFile.write(data)

    xbmc.sleep(500)
    header = data[:4].decode('ISO-8859-1')
    archive = urllib.parse.quote_plus(tmpfile)
    if header == 'Rar!':
        path = 'rar://%s' % (archive)
    else:
        path = 'zip://%s' % (archive)
    dirs, files = xbmcvfs.listdir(path)
    if ('__MACOSX') in dirs:
        dirs.remove('__MACOSX')
    if len(dirs) > 0:
        path = path + '/' + dirs[0]
        dirs, files = xbmcvfs.listdir(path)
    list = []
    for subfile in files:
        if (os.path.splitext( subfile )[1] in exts):
            list.append(subfile)
    if len(list) == 1:
        subtitle_list.append(path + '/' + list[0])
    elif len(list) > 1:
        sel = xbmcgui.Dialog().select('请选择压缩包中的字幕', list)
        if sel == -1:
            sel = 0
        subtitle_list.append(path + '/' + list[sel])

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
    item['year']               = xbmc.getInfoLabel("VideoPlayer.Year")                 # Year
    item['season']             = str(xbmc.getInfoLabel("VideoPlayer.Season"))          # Season
    item['episode']            = str(xbmc.getInfoLabel("VideoPlayer.Episode"))         # Episode
    item['tvshow']             = xbmc.getInfoLabel("VideoPlayer.TVshowtitle")          # Show
    item['title']              = xbmc.getInfoLabel("VideoPlayer.OriginalTitle")        # try to get original title
    item['file_original_path'] = urllib.parse.unquote(xbmc.Player().getPlayingFile())  # Full path of a playing file
    item['3let_language']      = []

    if 'searchstring' in params:
        item['mansearch'] = True
        item['mansearchstr'] = params['searchstring']

    for lang in urllib.parse.unquote(params['languages']).split(","):
        item['3let_language'].append(xbmc.convertLanguage(lang,xbmc.ISO_639_2))

    if item['title'] == "":
        item['title']  = xbmc.getInfoLabel("VideoPlayer.Title")                       # no original title, get just Title
        if item['title'] == os.path.basename(xbmc.Player().getPlayingFile()):         # get movie title and year if is filename
            title, year = xbmc.getCleanMovieTitle(item['title'])
            item['title'] = title.replace('[','').replace(']','')
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
    subs = Download(params["link"])
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
