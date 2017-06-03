﻿# -*- coding: utf-8 -*-

import re
import os
import sys
import xbmc
import urllib
import xbmcvfs
import xbmcaddon
import xbmcgui,xbmcplugin
import simplejson
from bs4 import BeautifulSoup

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

SEARCH_API   = 'http://www.163sub.com/search.ashx?q=%s&lastid=%s'
DOWNLOAD_API = 'http://www.163sub.com/download/%s'

def log(module, msg):
    xbmc.log((u"%s::%s - %s" % (__scriptname__,module,msg,)).encode('utf-8'),level=xbmc.LOGDEBUG )

def normalizeString(str):
    return str

def Search( item ):
    subtitles_list = []

    if item['mansearch']:
        search_str = item['mansearchstr']
    elif len(item['tvshow']) > 0:
        search_str = "%s S%.2dE%.2d" % (item['tvshow'],
                                        int(item['season']),
                                        int(item['episode']),)
    else:
        search_str = item['title']
    log( __name__ ,"Search for [%s] with [%s]" % (os.path.basename( item['file_original_path'] ),search_str.decode('utf-8')))
    search_str = urllib.quote(search_str)
    lastid = ''
    results = []
    try:
        while True:
            url = SEARCH_API % (search_str, lastid)
            socket = urllib.urlopen(url)
            data = socket.read()
            json_response = simplejson.loads(data)
            lastid = json_response['Data'][-1]['linkID']
            results.extend(json_response['Data'])
            if __addon__.getSetting("resultsNumber") == "0" or len(json_response['Data']) < 10:
                break
        socket.close()
    except:
        return
    for sub in results:
        version = sub['mkvName'].encode('utf-8')
        if version[-4:] in ('.rar', '.zip'):
            version = version[:-4]
        title = sub['enName'].encode('utf-8')
        if (len(re.findall(r"[\w']+", version)) < 5):
            if (title.find(version) == -1):
                version = title + ' ' + version
            else:
                version = title
        info = sub['otherName2'].encode('utf-8')
        langs = []
        lang_list = ['双语', '简体', '繁体', '英文']
        for x in lang_list:
            if (info.find(x) != -1):
                langs.append(x)
        if (len(langs) == 0):
            langs.append('未知语言')
            lang_name = 'Chinese'
            lang_flag = 'zh'
        elif (len(langs) == 1) and (langs[0] == '英文'):
            lang_name = 'English'
            lang_flag = 'en'
        else:
            lang_name = 'Chinese'
            lang_flag = 'zh'
        id = sub['ID'].encode('utf-8')
        group = sub['subFrom'].encode('utf-8')
        if (group != '转载/未知/其他') and (group != '见字幕文件') and (version.find(group) == -1):
            version += ' ' + group
        name = '%s (%s)' % (version, ",".join(langs))
        subtitles_list.append({"language_name":lang_name, "filename":name, "link":id, "language_flag":lang_flag, "rating":"0", "lang":langs})

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

def Download(id,lang):
    try: rmtree(__temp__)
    except: pass
    try: os.makedirs(__temp__)
    except: pass

    subtitle_list = []
    exts = [".srt", ".sub", ".smi", ".ssa", ".ass" ]
    url = DOWNLOAD_API % (id)
    try:
        socket = urllib.urlopen( url )
        data = socket.read()
        socket.close()
        soup = BeautifulSoup(data)
        url = soup.find("a", class_="down_ink download_link").get('href').encode('utf-8')
        socket = urllib.urlopen( url )
        #filename = socket.headers['Content-Disposition'].split('filename=')[1]
        #if filename[0] == '"' or filename[0] == "'":
        #    filename = filename[1:-1]
        filename = os.path.basename(url)
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
        if len(list):
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
