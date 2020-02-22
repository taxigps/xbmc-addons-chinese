# -*- coding: utf-8 -*-

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
import json
import time

__addon__      = xbmcaddon.Addon()
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

SUBHD_BASE = 'http://subhd.la'
SUBHD_API  = SUBHD_BASE + '/search/%s'
UserAgent  = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'

def get_KodiVersion():
    json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')
    if sys.version_info[0] >= 3:
        json_query = str(json_query)
    else:
        json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_query = json.loads(json_query)
    version_installed = []
    if 'result' in json_query and 'version' in json_query['result']:
        version_installed  = json_query['result']['version']
    return version_installed

__kodi__ = get_KodiVersion()

def log(module, msg):
    if isinstance(msg,str):
        msg = msg.decode('utf-8')
    xbmc.log((u"%s::%s - %s" % (__scriptname__,module,msg,)).encode('utf-8'),level=xbmc.LOGDEBUG )

def session_get(url, id='', referer='', dtoken=''):
    log(sys._getframe().f_code.co_name, "url=%s id=%s referer=%s dtoken=%s" % (url, id, referer, dtoken))
    if id:
        HEADERS={'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Origin': SUBHD_BASE,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0'}
        s = requests.Session()
        s.headers.update(HEADERS)
        r = s.get(referer)
        s.headers.update({'Referer': referer})
        r = s.post(url, data={'sub_id': id, 'dtoken': dtoken})
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
    div_class_of_item = 'float-left pt-3 pb-3 px-3'
    div_class_of_link = 'f12 pt-1'
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

    results = soup.find_all("div", class_="col-sm-10 p-3 position-relative")

    # if can't find subtitle for the specified episode, try the whole season instead
    if (len(results) == 0) and (len(item['tvshow']) > 0):
        search_string = "%s S%.2d" % (item['tvshow'], int(item['season']))
        url = SUBHD_API % (urllib.quote(search_string))
        data = session_get(url)
        try:
            soup = BeautifulSoup(data, "html.parser")
        except:
            return
        results = [x for x in soup.find_all("div", class_="col-sm-10 p-3 position-relative") if x.find('div', class_="f12 pt-1")]

    for it in results:
        a = it.find('div', class_="f12 pt-1").a
        link = SUBHD_BASE + a.get('href').encode('utf-8')
        title = a.get('title') if a.get('title') else a.text
        version = title.encode('utf-8')
        if version.find('本字幕按 ') == 0:
            version = version.split()[1]

        try:
            langs = it.find("div", class_="pt-1 text-secondary").text.split()
            langs = [x.encode('utf-8') for x in langs][:-1]
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

def Download(url,lang):
    if not xbmcvfs.exists(__temp__.replace('\\','/')):
        xbmcvfs.mkdirs(__temp__)
    dirs, files = xbmcvfs.listdir(__temp__)
    for file in files:
        xbmcvfs.delete(os.path.join(__temp__, file))

    referer = url
    subtitle_list = []
    exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
    try:
        data = session_get(url)
        soup = BeautifulSoup(data, "html.parser")
        id = soup.find("button", class_="btn btn-danger btn-sm").get("sid").encode('utf-8')
        dtoken = soup.find("button", class_="btn btn-danger btn-sm").get("dtoken").encode('utf-8')
        url = "%s/ajax/down_ajax" % SUBHD_BASE
        data = session_get(url, id=id, referer=referer, dtoken=dtoken)
        json_response = json.loads(data)
        if json_response['success']:
            url = json_response['url'].encode('utf-8')
            if url[:4] != 'http':
                url = '%s%s' % (SUBHD_BASE, url)
            data = session_get(url)
        else:
            msg = json_response['msg']
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
    t = time.time()
    ts = time.strftime("%Y%m%d%H%M%S",time.localtime(t)) + str(int((t - int(t)) * 1000))
    tempfile = os.path.join(__temp__, "subtitles%s%s" % (ts, os.path.splitext(url)[1])).replace('\\','/')
    with open(tempfile, "wb") as subFile:
        subFile.write(data)
    subFile.close()
    xbmc.sleep(500)
    if data[:4] == 'Rar!' or data[:2] == 'PK':
        archive = urllib.quote_plus(tempfile)
        if data[:4] == 'Rar!':
            path = 'rar://%s' % (archive)
        else:
            path = 'zip://%s' % (archive)
        dirs, files = xbmcvfs.listdir(path)
        if ('__MACOSX') in dirs:
            dirs.remove('__MACOSX')
        if len(dirs) > 0:
            path = path + '/' + dirs[0].decode('utf-8')
            dirs, files = xbmcvfs.listdir(path)
        list = []
        for subfile in files:
            if (os.path.splitext( subfile )[1] in exts):
                list.append(subfile.decode('utf-8'))
        if list:
            if len(list) == 1:
                subtitle_list.append(path + '/' + list[0])
            else:
                # hack to fix encoding problem of zip file in Kodi 18
                if __kodi__['major'] >= 18 and data[:2] == 'PK':
                    try:
                        dlist = [x.encode('CP437').decode('gbk') for x in list]
                    except:
                        dlist = list
                else:
                    dlist = list

                sel = xbmcgui.Dialog().select('请选择压缩包中的字幕', dlist)
                if sel == -1:
                    sel = 0
                subtitle_list.append(path + '/' + list[sel])
    else:
        subtitle_list.append(tempfile)
    if len(subtitle_list) > 0:
        log(sys._getframe().f_code.co_name, "Get subtitle file: %s" % (subtitle_list[0]))
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
    item['tvshow']             = xbmc.getInfoLabel("VideoPlayer.TVshowtitle")                    # Show
    item['title']              = xbmc.getInfoLabel("VideoPlayer.OriginalTitle")                  # try to get original title
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
    subs = Download(params["link"], params["lang"])
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
