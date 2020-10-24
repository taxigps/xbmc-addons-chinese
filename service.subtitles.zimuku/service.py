# -*- coding: UTF-8 -*-

import os
import sys
import json
import time
import urllib
import urlparse
import shutil
import requests
from bs4 import BeautifulSoup
from kodi_six import xbmc, xbmcgui, xbmcaddon, xbmcplugin, xbmcvfs

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

#sys = reload(sys)
#sys.setdefaultencoding('UTF-8')

ZIMUKU_API = 'http://www.zimuku.la/search?q=%s'
ZIMUKU_BASE = 'http://www.zimuku.la'
ZIMUKU_RESOURCE_BASE = 'http://zmk.pw'
# IE UA
UserAgent  = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
# Chrome UA
UserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'

session = requests.Session()

MIN_SIZE = 1024

def get_KodiVersion():
    json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')
    if sys.version_info[0] >= 3:
        json_query = str(json_query)
    else:
        json_query = json_query.encode('utf-8')
    json_query = json.loads(json_query)
    version_installed = []
    if 'result' in json_query and 'version' in json_query['result']:
        version_installed  = json_query['result']['version']
    return version_installed

__kodi__ = get_KodiVersion()

def log(module, msg, level=xbmc.LOGDEBUG):
    if isinstance(msg, unicode): msg = msg.encode("utf-8")
    xbmc.log("{0}::{1} - {2}".format(__scriptname__,module,msg) ,level=level )

def Search( item ):
    subtitles_list = []

    if item['mansearch']:
        search_str = item['mansearchstr']
    elif len(item['tvshow']) > 0:
        search_str = item['tvshow']
    else:
        search_str = item['title']
    log( sys._getframe().f_code.co_name ,"Search for [%s] by str %s" % (os.path.basename(item['file_original_path']), search_str))
    url = ZIMUKU_API % (urllib.quote(str(search_str)))
    log( sys._getframe().f_code.co_name ,"Search API url: %s" % (url))
    try:
        # Search page.
        _headers, data = get_page(url)
        soup = BeautifulSoup(data, 'html.parser')
    except Exception, e:
        log( sys._getframe().f_code.co_name ,'%s: %s    Error searching.' % (Exception, e), level=xbmc.LOGERROR)
        return
    results = soup.find_all("div", class_="item prel clearfix")
    for it in results:
        #moviename = it.find("div", class_="title").a.text.encode('utf-8')
        movieurl = urlparse.urljoin(ZIMUKU_BASE, it.find("div", class_="title").a.get('href').encode('utf-8'))
        try:
            # Movie page.
            _headers, data = get_page(movieurl)
            soup = BeautifulSoup(data, 'html.parser').find("div", class_="subs box clearfix")
        except:
            log( sys._getframe().f_code.co_name ,'Error searching.', level=xbmc.LOGERROR)
            return
        subs = soup.tbody.find_all("tr")
        for sub in subs:
            link = urlparse.urljoin(ZIMUKU_BASE, sub.a.get('href').encode('utf-8'))
            version = sub.a.text.encode('utf-8')
            try:
                td = sub.find("td", class_="tac lang")
                r2 = td.find_all("img")
                langs = [x.get('title').encode('utf-8') for x in r2]
            except:
                langs = '未知'
            name = '%s (%s)' % (version, ",".join(langs))
            #name = version

            # Get rating. rating from str(int [0 , 5]).
            try:
                rating_div = sub.find("td", class_="tac hidden-xs")
                rating_div_str = str(rating_div)
                rating_star_str = "allstar"
                rating = rating_div_str[rating_div_str.find(rating_star_str) + len(rating_star_str)]
                if rating not in ["0", "1", "2", "3", "4", "5"]:
                    log( sys._getframe().f_code.co_name ,"Failed to locate rating in %s from %s" % (rating_div_str, link), level=xbmc.LOGWARNING)
                    rating = "0"
            except:
                rating = "0"

            if '简体中文' in langs or '繁體中文' in langs or '简体中文字幕' in langs or '繁體中文字幕' in langs:
                # In GUI, only "lang", "filename" and "rating" displays to users, .
                subtitles_list.append({"language_name":"Chinese", "filename":name, "link":link, "language_flag":'zh', "rating":str(rating), "lang":langs})
            elif '双语' in langs or '双语字幕' in langs:
                subtitles_list.append({"language_name":"Chinese", "filename":name, "link":link, "language_flag":'zh', "rating":str(rating), "lang":langs})
            elif 'English' in langs:
                subtitles_list.append({"language_name":"English", "filename":name, "link":link, "language_flag":'en', "rating":str(rating), "lang":langs})
            else:
                log( sys._getframe().f_code.co_name ,"Unrecognized lang: %s" % (langs), level=xbmc.LOGDEBUG)
                subtitles_list.append({"language_name":"Unknown", "filename":name, "link":link, "language_flag":'en', "rating":str(rating), "lang":langs})

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

def store_file(filename, data):
    """
    Store file function. Store bin(data) into os.path.join(__temp__, "subtitles<time>.<ext>")

    This may store subtitle files or compressed archive. So write in binary mode.

    Params:
        filename    The name of the file. May include non-unicode chars, so may cause problems if used as filename to store directly.
        data        The data of the file. May be compressed.

    Return:
        The absolute path to the file.
    """
     # Store file in an ascii name since some chars may cause some problems.
    t = time.time()
    ts = time.strftime("%Y%m%d%H%M%S",time.localtime(t)) + str(int((t - int(t)) * 1000))
    tempfile = os.path.join(__temp__, "subtitles%s%s" % (ts, os.path.splitext(filename)[1])).replace('\\','/')
    with open(tempfile, "wb") as subFile:
        subFile.write(data)
    # May require close file explicitly to ensure the file.
    subFile.close()
    return tempfile.replace('\\','/')

def DownloadLinks(links, referer):
    """
    Download subtitles one by one until success.
    
    Parameters:
        links   The list of subtitle download links.
        referer The url of dld list page, used as referer.

    Return:
        '', []          If nothing to return.
        filename, data  If success.
    """
    filename = None
    data = None
    small_size_confirmed = False
    data_size = -1
    link_string = ''

    for link in links:
        url = link.get('href').encode('utf-8')
        if not url.startswith('http://'):
            url = urlparse.urljoin(ZIMUKU_RESOURCE_BASE, url)
        link_string += url + ' '

        try:
            log( sys._getframe().f_code.co_name ,"Download subtitle url: %s" % (url))
            # Download subtitle one by one until success.
            headers, data = get_page(url, Referer=referer)

            filename = headers['Content-Disposition'].split('filename=')[1].strip('"').strip("'")
            small_size_confirmed = data_size == len(data)
            if len(data) > MIN_SIZE or small_size_confirmed:
                break
            else:
                data_size = len(data)

        except Exception:
            if filename is not None:
                log( sys._getframe().f_code.co_name ,"Failed to download subtitle data of %s." % (filename))
                filename = None
            else:
                log( sys._getframe().f_code.co_name ,"Failed to download subtitle from %s" % (url))

    if filename is not None:
        if data is not None and (len(data) > MIN_SIZE or small_size_confirmed):
            return filename, data
        else:
            log( sys._getframe().f_code.co_name ,'File received but too small: %s %d bytes' % (filename, len(data)), level=xbmc.LOGWARNING)
            return '', ''
    else:
        log( sys._getframe().f_code.co_name ,'Failed to download subtitle from all links: %s' % (referer), level=xbmc.LOGWARNING)
        return '', ''

def get_page(url, **kwargs):
    """
    Get page with requests.

    Parameters:
        url     Target URL.
        kwargs  Attached headers. HTTP_HEADER_KEY = HTTP_HEADER_VALUE. Use '_' instead of '-' in HTTP_HEADER_KEY since '-' is illegal in python variable name.

    Return:
        headers     The http response headers.
        http_body   The http response body.
    """
    headers = None
    http_body = None
    try:
        request_headers = {'User-Agent': UserAgent}
        if kwargs:
            for key, value in kwargs.items():
                request_headers[key.replace('_', '-')] = value

        http_response = session.get(url, headers=request_headers)
        log( sys._getframe().f_code.co_name ,'Got url %s' % (url), level=xbmc.LOGDEBUG)
        headers = http_response.headers
        http_body = http_response.content

    except Exception, e:
        log(sys._getframe().f_code.co_name, "Error: %s.    Failed to access %s" % (e, url), level=xbmc.LOGWARNING)

    return headers, http_body   

def Download(url,lang):
    global ZIMUKU_RESOURCE_BASE
    if not xbmcvfs.exists(__temp__.replace('\\','/')):
        xbmcvfs.mkdirs(__temp__)
    _dirs, files = xbmcvfs.listdir(__temp__)
    for file in files:
        xbmcvfs.delete(os.path.join(__temp__, file.decode('utf-8')))

    subtitle_list = []
    exts = ( ".srt", ".sub", ".smi", ".ssa", ".ass" )
    # Some exts may cause fatal failure/ crash with some coding except from UTF-8.
    supported_archive_exts = ( ".zip", ".7z", ".tar", ".bz2", ".rar", ".gz", ".xz", ".iso", ".tgz", ".tbz2", ".cbr" )
    #self_archive_exts = ( ".zip", ".rar" )

    log( sys._getframe().f_code.co_name ,"Download page: %s" % (url))

    try:
        # Subtitle detail page.
        _headers, data = get_page(url)
        soup = BeautifulSoup(data, 'html.parser')
        url = soup.find("li", class_="dlsub").a.get('href').encode('utf-8')

        if not ( url.startswith('http://') or url.startswith('https://')):
            url = urlparse.urljoin(ZIMUKU_RESOURCE_BASE, url)
        else:
            ZIMUKU_RESOURCE_BASE = "{host_info.scheme}://{host_info.netloc}".format(host_info=urlparse.urlparse(url))
        log( sys._getframe().f_code.co_name ,"Download links: %s" % (url))

        # Subtitle download-list page.
        _headers, data = get_page(url)

        soup = BeautifulSoup(data, 'html.parser')
        links = soup.find("div", {"class":"clearfix"}).find_all('a')
    except:
        log( sys.exc_info()[2].tb_frame.f_code.co_name, "Error (%d) [%s]" % (
            sys.exc_info()[2].tb_lineno,
            sys.exc_info()[1]
            ),
            level=xbmc.LOGERROR
            )
        return []

    filename, data = DownloadLinks(links, url)
    if filename == '':
        # No file received.
        return []

    if filename.endswith(exts):
        tempfile = store_file(filename, data)
        subtitle_list.append(tempfile)

    elif filename.endswith(supported_archive_exts):
        tempfile = store_file(filename, data)
        # libarchive requires the access to the file, so sleep a while to ensure the file.
        xbmc.sleep(500)
        # Import here to avoid waste.
        import zimuku_archive
        archive_path, list = zimuku_archive.unpack(tempfile)

        if len(list) == 1:
            subtitle_list.append( os.path.join( archive_path, list[0] ).replace('\\','/'))
        elif len(list) > 1:
            sel = xbmcgui.Dialog().select('请选择压缩包中的字幕', list)
            if sel == -1:
                sel = 0
            subtitle_list.append( os.path.join( archive_path, list[sel] ).replace('\\','/'))

    else:
        log(sys._getframe().f_code.co_name, "Unsupported file: %s" % (filename), level=xbmc.LOGWARNING)
        raise TypeError, "Unsupported file compressed format! Please try another subtitle."

    if len(subtitle_list) > 0:
        log(sys._getframe().f_code.co_name, "Get subtitle file: %s" % (subtitle_list[0]), level=xbmc.LOGINFO)

    return subtitle_list

def get_params():
    """
    Decode params from sys.argv[2].
    """
    return dict(urlparse.parse_qsl(urlparse.urlparse(sys.argv[2]).query))

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
