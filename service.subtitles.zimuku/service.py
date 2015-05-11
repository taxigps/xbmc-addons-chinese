# -*- coding: utf-8 -*-

import re
import os
import sys
import xbmc
import urllib
import shutil
import xbmcvfs
import xbmcaddon
import xbmcgui,xbmcplugin
from bs4 import BeautifulSoup

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

ZIMUKU_API = 'http://www.zimuku.net/search?q=%s'
ZIMUKU_BASE = 'http://www.zimuku.net'
FLAG_DICT = {'china':'简', 'hongkong':'繁', 'uk':'英', 'jollyroger':'双语'}

def log(module, msg):
    xbmc.log((u"%s::%s - %s" % (__scriptname__,module,msg,)).encode('utf-8'),level=xbmc.LOGDEBUG )

def normalizeString(str):
    return str

def Search( item ):
    subtitles_list = []

    log( __name__ ,"Search for [%s] by name" % (os.path.basename( item['file_original_path'] ),))
    if item['mansearch']:
        url = ZIMUKU_API % (item['mansearchstr'])
    else:
        url = ZIMUKU_API % (item['title'])
    try:
        socket = urllib.urlopen(url)
        data = socket.read()
        socket.close()
        soup = BeautifulSoup(data)
    except:
        return
    results = soup.find_all("div", class_="item clearfix")
    for it in results:
        moviename = it.find("div", class_="title").a.text.encode('utf-8')
        movieurl = '%s%s' % (ZIMUKU_BASE, it.find("div", class_="title").a.get('href').encode('utf-8'))
        try:
            socket = urllib.urlopen(movieurl)
            data = socket.read()
            socket.close()
            soup = BeautifulSoup(data).find("div", class_="sublist")
        except:
            return
        subs = soup.find_all("tr")
        for sub in subs:
            version = sub.a.text.encode('utf-8')
            flag = sub.img.get('src').split('/')[-1].split('.')[0].encode('utf-8')
            lang = FLAG_DICT[flag]
            link = '%s%s' % (ZIMUKU_BASE, sub.a.get('href').encode('utf-8'))
            name = '%s (%s)' % (version, lang)
            if lang == '英':
                subtitles_list.append({"language_name":"English", "filename":name, "link":link, "language_flag":'en', "rating":"0", "lang":lang})
            else:
                subtitles_list.append({"language_name":"Chinese", "filename":name, "link":link, "language_flag":'zh', "rating":"0", "lang":lang})

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
    try: shutil.rmtree(__temp__)
    except: pass
    try: os.makedirs(__temp__)
    except: pass

    subtitle_list = []
    exts = [".srt", ".sub", ".smi", ".ssa", ".ass" ]
    try:
        socket = urllib.urlopen( url )
        data = socket.read()
        soup = BeautifulSoup(data)
        url = '%s%s' % (ZIMUKU_BASE, soup.find("li", class_="dlsub").a.get('href').encode('utf-8'))
        socket = urllib.urlopen( url )
        filename = socket.headers['Content-Disposition'].split('filename=')[1]
        if filename[0] == '"' or filename[0] == "'":  
            filename = filename[1:-1]  
        data = socket.read()
        socket.close()
    except:
        return []
    if len(data) < 1024:
        return []
    tempfile = os.path.join(__temp__, "subtitles%s" % os.path.splitext(filename)[1])
    with open(tempfile, "wb") as subFile:
        subFile.write(data)
    subFile.close()
    xbmc.sleep(500)
    if data[:4] == 'Rar!' or data[:2] == 'PK':
        xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (tempfile,__temp__,)).encode('utf-8'), True)
    path = __temp__
    dirs, files = xbmcvfs.listdir(path)
    if len(dirs) > 0:
        path = os.path.join(__temp__, dirs[0].decode('utf-8'))
        dirs, files = xbmcvfs.listdir(path)
    list = []
    for subfile in files:
        if (os.path.splitext( subfile )[1] in exts):
            list.append(subfile.decode('utf-8'))
    if len(list) == 1:
        subtitle_list.append(os.path.join(path, list[0]))
    else:
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
