# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import urllib
import urllib2
import xbmcvfs
import xbmcaddon
import xbmcgui,xbmcplugin
from bs4 import BeautifulSoup
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

ZIMUKU_API = 'http://www.zimuku.la/search?q=%s'
ZIMUKU_BASE = 'http://www.zimuku.la'
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
    if isinstance(msg, unicode): msg = msg.encode("utf-8")
    xbmc.log("{0}::{1} - {2}".format(__scriptname__,module,msg) ,level=xbmc.LOGDEBUG )

def Search( item ):
    subtitles_list = []

    log( sys._getframe().f_code.co_name ,"Search for [%s] by name" % (os.path.basename(item['file_original_path'])))
    if item['mansearch']:
        search_str = item['mansearchstr']
    elif len(item['tvshow']) > 0:
        search_str = item['tvshow']
    else:
        search_str = item['title']
    url = ZIMUKU_API % (urllib.quote(search_str))
    log( sys._getframe().f_code.co_name ,"Search API url: %s" % (url))
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', UserAgent)
        socket = urllib2.urlopen(req)
        data = socket.read()
        socket.close()
        soup = BeautifulSoup(data, 'html.parser')
    except:
        return
    results = soup.find_all("div", class_="item prel clearfix")
    for it in results:
        moviename = it.find("div", class_="title").a.text.encode('utf-8')
        movieurl = '%s%s' % (ZIMUKU_BASE, it.find("div", class_="title").a.get('href').encode('utf-8'))
        try:
            req = urllib2.Request(movieurl)
            req.add_header('User-Agent', UserAgent)
            socket = urllib2.urlopen(req)
            data = socket.read()
            socket.close()
            soup = BeautifulSoup(data, 'html.parser').find("div", class_="subs box clearfix")
        except:
            return
        subs = soup.tbody.find_all("tr")
        for sub in subs:
            link = '%s%s' % (ZIMUKU_BASE, sub.a.get('href').encode('utf-8'))
            version = sub.a.text.encode('utf-8')
            try:
                td = sub.find("td", class_="tac lang")
                r2 = td.find_all("img")
                langs = [x.get('title').encode('utf-8') for x in r2]
            except:
                langs = '未知'
            name = '%s (%s)' % (version, ",".join(langs))
            if ('English' in langs) and not(('简体中文' in langs) or ('繁體中文' in langs)):
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

def DownloadLinks(links, referer):
    for link in links:
        url = link.get('href').encode('utf-8')
        if url[:4] != 'http':
            url = ZIMUKU_BASE + url
        try:
            log( sys._getframe().f_code.co_name ,"Download url: %s" % (url))
            req = urllib2.Request(url)
            req.add_header('User-Agent', UserAgent)
            req.add_header('Referer', referer)
            socket = urllib2.urlopen(req)
            filename = socket.headers['Content-Disposition'].split('filename=')[1]
            if filename[0] == '"' or filename[0] == "'":
                filename = filename[1:-1]
            data = socket.read()
            socket.close()
            if len(data) > 1024:
                return filename, data
            else:
                return '', ''
        except Exception, e:
            log(sys._getframe().f_code.co_name, "Failed to access %s" % (url))
    return '', ''

def Download(url,lang):
    if not xbmcvfs.exists(__temp__.replace('\\','/')):
        xbmcvfs.mkdirs(__temp__)
    dirs, files = xbmcvfs.listdir(__temp__)
    for file in files:
        xbmcvfs.delete(os.path.join(__temp__, file.decode('utf-8')))

    subtitle_list = []
    exts = [".srt", ".sub", ".smi", ".ssa", ".ass" ]
    log( sys._getframe().f_code.co_name ,"Download page: %s" % (url))
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', UserAgent)
        socket = urllib2.urlopen(req)
        data = socket.read()
        soup = BeautifulSoup(data, 'html.parser')
        url = soup.find("li", class_="dlsub").a.get('href').encode('utf-8')
        if url[:4] != 'http':
            url = ZIMUKU_BASE + url
        log( sys._getframe().f_code.co_name ,"Download links: %s" % (url))
        req = urllib2.Request(url)
        req.add_header('User-Agent', UserAgent)
        socket = urllib2.urlopen(req)
        data = socket.read()
        socket.close()
        soup = BeautifulSoup(data, 'html.parser')
        links = soup.find("div", {"class":"clearfix"}).find_all('a')
    except:
        log( sys.exc_info()[2].tb_frame.f_code.co_name, "Error (%d) [%s]" % (
            sys.exc_info()[2].tb_lineno,
            sys.exc_info()[1]
            ))
        return []
    filename, data = DownloadLinks(links, url)
    if len(data) < 1024:
        return []
    t = time.time()
    ts = time.strftime("%Y%m%d%H%M%S",time.localtime(t)) + str(int((t - int(t)) * 1000))
    tempfile = os.path.join(__temp__, "subtitles%s%s" % (ts, os.path.splitext(filename)[1])).replace('\\','/')
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
    item['tvshow']             = xbmc.getInfoLabel("VideoPlayer.TVshowtitle")   # Show
    item['title']              = xbmc.getInfoLabel("VideoPlayer.OriginalTitle") # try to get original title
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
