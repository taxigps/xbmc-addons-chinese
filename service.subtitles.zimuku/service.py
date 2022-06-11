# -*- coding: utf-8 -*-

import os
import sys
import time
import urllib
import urllib.parse
import requests
from bs4 import BeautifulSoup
from kodi_six import xbmc, xbmcgui, xbmcaddon, xbmcplugin, xbmcvfs


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

ZIMUKU_API = 'http://zmk.pw/search?q=%s&vertoken=%s'
ZIMUKU_BASE = 'http://zmk.pw'
ZIMUKU_RESOURCE_BASE = 'http://zmk.pw'
UserAgent  = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'

MIN_SIZE = 1024

session = requests.Session()
vertoken = ''

def log(module, msg, level=xbmc.LOGDEBUG):
    xbmc.log("{0}::{1} - {2}".format(__scriptname__,module,msg) ,level=level )

def get_vertoken():
    # get vertoken from home page and cache it for the session
    global vertoken
    if vertoken:
        return vertoken
    else:
        log( sys._getframe().f_code.co_name, "Fetching new vertoken form home page", level=xbmc.LOGDEBUG)
        try:
            headers, data = get_page(ZIMUKU_BASE+'/')
            hsoup = BeautifulSoup(data, 'html.parser')
            vt = hsoup.find('input', attrs={'name': 'vertoken'}).attrs.get('value', '')
            vertoken = vt
            return vt
        except Exception as e:
            log(sys._getframe().f_code.co_name, "ERROR GETTING vertoken, E=(%s: %s)" % (Exception, e), level=xbmc.LOGWARNING)
            return ''

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
    global session
    headers = None
    http_body = None
    try:
        request_headers = {'User-Agent': UserAgent}
        if kwargs:
            for key, value in kwargs.items():
                request_headers[key.replace('_', '-')] = value

        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount('http://', adapter)
        log( sys._getframe().f_code.co_name, 'Got url %s' % (url), level=xbmc.LOGDEBUG)

        url += '&' if '?' in url else '?'
        url += 'security_verify_data=313932302c31303830'
        url1 = url + '&security_verify_data=313932302c31303830'
        session.get(url, headers=request_headers)
        session.get(url1, headers=request_headers)
        http_response = session.get(url, headers=request_headers)
        if http_response.status_code != 200:
            session.get(url, headers=request_headers)
            http_response = session.get(url, headers=request_headers)
        headers = http_response.headers
        http_body = http_response.content

    except Exception as e:
        log(sys._getframe().f_code.co_name, "Error: %s.    Failed to access %s" % (e, url), level=xbmc.LOGWARNING)

    return headers, http_body

def Search( item ):
    subtitles_list = []
    get_vertoken()

    if item['mansearch']:
        search_str = item['mansearchstr']
    elif len(item['tvshow']) > 0:
        search_str = item['tvshow']
    else:
        search_str = item['title']
    log( sys._getframe().f_code.co_name ,"Search for [%s] by str %s" % (os.path.basename(item['file_original_path']), search_str))
    url = ZIMUKU_API % (urllib.parse.quote(search_str), vertoken)
    log( sys._getframe().f_code.co_name ,"Search API url: %s" % (url))
    try:
        # Search page.
        _headers, data = get_page(url)
        soup = BeautifulSoup(data, 'html.parser')
    except Exception as e:
        log( sys._getframe().f_code.co_name ,'%s: %s    Error searching.' % (Exception, e), level=xbmc.LOGERROR)
        return
    results = soup.find_all("div", class_="item prel clearfix")
    for it in results:
        #moviename = it.find("div", class_="title").a.text
        movieurl = urllib.parse.urljoin(ZIMUKU_BASE, it.find("div", class_="title").a.get('href'))
        try:
            # Movie page.
            _headers, data = get_page(movieurl)
            soup = BeautifulSoup(data, 'html.parser').find("div", class_="subs box clearfix")
        except:
            log( sys._getframe().f_code.co_name ,'Error get movie page.', level=xbmc.LOGERROR)
            return
        subs = soup.tbody.find_all("tr")
        for sub in subs:
            link = urllib.parse.urljoin(ZIMUKU_BASE, sub.a.get('href'))
            version = sub.a.text
            try:
                td = sub.find("td", class_="tac lang")
                r2 = td.find_all("img")
                langs = [x.get('title').rstrip('字幕') for x in r2]
            except:
                langs = '未知'
            name = '%s (%s)' % (version, ",".join(langs))

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

            if '简体中文' in langs or '繁體中文' in langs or '双语' in langs:
                # In GUI, only "lang", "filename" and "rating" displays to users, .
                subtitles_list.append({"language_name":"Chinese", "filename":name, "link":link, "language_flag":'zh', "rating":str(rating), "lang":langs})
            elif 'English' in langs:
                subtitles_list.append({"language_name":"English", "filename":name, "link":link, "language_flag":'en', "rating":str(rating), "lang":langs})
            else:
                log( sys._getframe().f_code.co_name ,"Unrecognized lang: %s" % (langs), level=xbmc.LOGDEBUG)
                subtitles_list.append({"language_name":"Unknown", "filename":name, "link":link, "language_flag":'en', "rating":str(rating), "lang":langs})

    if subtitles_list:
        for it in subtitles_list:
            listitem = xbmcgui.ListItem(label=it["language_name"],
                                        label2=it["filename"])
            listitem.setArt({'icon': it["rating"], 'thumb': it["language_flag"]})
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
        url = link.get('href')
        if not url.startswith('http://'):
            url = urllib.parse.urljoin(ZIMUKU_RESOURCE_BASE, url)
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

def Download(url,lang):
    if not xbmcvfs.exists(__temp__.replace('\\','/')):
        xbmcvfs.mkdirs(__temp__)
    dirs, files = xbmcvfs.listdir(__temp__)
    for file in files:
        xbmcvfs.delete(os.path.join(__temp__, file))

    subtitle_list = []
    exts = (".srt", ".sub", ".smi", ".ssa", ".ass", ".sup" )
    supported_archive_exts = ( ".zip", ".7z", ".tar", ".bz2", ".rar", ".gz", ".xz", ".iso", ".tgz", ".tbz2", ".cbr" )

    log( sys._getframe().f_code.co_name ,"Download page: %s" % (url))
    try:
        # Subtitle detail page.
        _headers, data = get_page(url)
        soup = BeautifulSoup(data, 'html.parser')
        url = soup.find("li", class_="dlsub").a.get('href')

        if not ( url.startswith('http://') or url.startswith('https://')):
            url = urllib.parse.urljoin(ZIMUKU_RESOURCE_BASE, url)
        log( sys._getframe().f_code.co_name ,"Download links: %s" % (url))

        # Subtitle download-list page.
        _headers, data = get_page(url)
        soup = BeautifulSoup(data, 'html.parser')
        links = soup.find("div", {"class":"clearfix"}).find_all('a')
    except:
        log(sys._getframe().f_code.co_name, "Error (%d) [%s]" % (
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
            # hack to fix encoding problem of zip file after Kodi 18
            if data[:2] == 'PK':
                try:
                    dlist = [x.encode('CP437').decode('gbk') for x in list]
                except:
                    dlist = list
            else:
                dlist = list

            sel = xbmcgui.Dialog().select('请选择压缩包中的字幕', dlist)
            if sel == -1:
                sel = 0
            subtitle_list.append( os.path.join( archive_path, list[sel] ).replace('\\','/'))

    else:
        log(sys._getframe().f_code.co_name, "Unsupported file: %s" % (filename), level=xbmc.LOGWARNING)
        xbmc.executebuiltin(('XBMC.Notification("zimuku","不支持的压缩格式，请选择其他字幕文件。")'), True)

    if len(subtitle_list) > 0:
        log(sys._getframe().f_code.co_name, "Get subtitle file: %s" % (subtitle_list[0]), level=xbmc.LOGINFO)
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
    subs = Download(params["link"], params["lang"])
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
