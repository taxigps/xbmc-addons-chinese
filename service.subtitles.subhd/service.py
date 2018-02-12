# -*- coding: utf-8 -*-

import re
import os
import sys
import xbmc
import urllib
import urllib2
import xbmcvfs
import xbmcaddon
import xbmcgui,xbmcplugin
from bs4 import BeautifulSoup
import requests

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


HEADERS={'Cache-Control': 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'User-Agent': 'Mozilla/6.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.5) Gecko/2008092417 Firefox/3.0.3'}

def session_get(url, id='', referer=''):
    if id:
        HEADERS={'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Host': 'subhd.com',
            'Origin': 'http://subhd.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}

        s = requests.Session()
        s.headers.update(HEADERS)
        r = s.get(referer)
        s.headers.update({'Referer': referer})
        r = s.post(url, data={'sub_id': id})
        return r.content
    else:
        s = requests.Session()
        r = s.get(url)
        return r.text

def Search( item ):
    subtitles_list = []

    log( __name__ ,"Search for [%s] by name" % (os.path.basename( item['file_original_path'] ),))
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

def Download(url, lang):
    referer = url
    try: rmtree(__temp__)
    except: pass
    try: os.makedirs(__temp__)
    except: pass

    subtitle_list = []
    exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
    try:
        log(__name__, url)
        data = session_get(url)
        soup = BeautifulSoup(data, "html.parser")
        # log(__name__, str(soup))
        id = soup.find("button", class_="btn btn-danger btn-sm").get("sid")
        url = "http://subhd.com/ajax/down_ajax"
        data = session_get(url, id=id, referer=referer)

        match = re.compile('"url":"([^"]+)"').search(data)
        url = match.group(1).replace(r'\/','/').decode("unicode-escape").encode('utf-8')
    except:
        return []

    if url:
        import zipfile
        zipfile_path = os.path.join(__temp__, "subtitles.zip")
        r = requests.get(url)
        with open(zipfile_path, 'wb') as f:
            f.write(r.content)
        xbmc.sleep(500)
        dirs, files = xbmcvfs.listdir(__temp__)

        zip_ref = zipfile.ZipFile(os.path.join(__temp__, 'subtitles.zip'), 'r')
        zip_ref.extractall(__temp__)
        zip_ref.close()

        dirs, files = xbmcvfs.listdir(__temp__)
        sub_path = dirs[0]
        dirs, files = xbmcvfs.listdir(os.path.join(__temp__, sub_path))

        list = []
        for subfile in files:
            list.append(subfile.decode('utf-8'))
        if len(list) == 1:
            subtitle_list.append(os.path.join(__temp__, sub_path, list[0]))
        elif len(list) > 1:
            sel = xbmcgui.Dialog().select('请选择压缩包中的字幕', list)
            if sel == -1:
                sel = 0
            subtitle_list.append(os.path.join(__temp__, sub_path, list[sel]))

        return subtitle_list
    else:
        return None

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
