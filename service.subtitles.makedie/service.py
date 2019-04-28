# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import urllib
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin
import unicodedata
import chardet
from cStringIO import StringIO
import random
from urlparse import urlparse
import re
import json
import itertools
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
from langconv import *


def get_KodiVersion():
    json_query = xbmc.executeJSONRPC(
        '{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')
    if sys.version_info[0] >= 3:
        json_query = str(json_query)
    else:
        json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_query = json.loads(json_query)
    version_installed = []
    if 'result' in json_query and 'version' in json_query['result']:
        version_installed = json_query['result']['version']
    return version_installed


__kodi__ = get_KodiVersion()

if __kodi__['major'] >= '18':
    API_BASE = "https://api.assrt.net"
else:
    API_BASE = "http://api.assrt.net"

DEFAULT_TOKEN = "vXMvTf8eu4pfmAVmllp8OY6aYqVbeB4F"

SUBTYPE_EXT = (".srt", ".ssa", ".ass", ".smi")

SVP_REV_NUMBER = 1543
CLIENTKEY = "SP,aerSP,aer %d &e(\xd7\x02 %s %s"
RETRY = 3

class AppURLopener(urllib.FancyURLopener):
    version = "XBMC(Kodi)-subtitle/%s" % __version__ #cf block default ua
urllib._urlopener = AppURLopener()

sess = requests.Session()
sess.headers.update({"User-Agent": "XBMC(Kodi)-subtitle/%s" % __version__})

def log(module, msg):
    xbmc.log((u"%s::%s - %s" % (__scriptname__,module,msg,)).encode('utf-8'),level=xbmc.LOGDEBUG )

def grapBlock(f, offset, size):
    f.seek(offset, 0)
    return f.read(size)

def getBlockHash(f, offset):
    return hashlib.md5(grapBlock(f, offset, 4096)).hexdigest()

def genFileHash(fpath):
    f = xbmcvfs.File(fpath)
    ftotallen = f.size()
    if ftotallen < 8192:
        f.close()
        return ""
    offset = [4096, ftotallen/3*2, ftotallen/3, ftotallen - 8192]
    hash = ";".join(getBlockHash(f, i) for i in offset)
    f.close()
    return hash

def getShortNameByFileName(fpath):
    fpath = os.path.basename(fpath).rsplit(".",1)[0]
    fpath = fpath.lower()

    for stop in ["blueray","bluray","dvdrip","xvid","cd1","cd2","cd3","cd4","cd5","cd6","vc1","vc-1","hdtv","1080p","720p","1080i","x264","stv","limited","ac3","xxx","hddvd"]:
        i = fpath.find(stop)
        if i >= 0:
            fpath = fpath[:i]

    for c in "[].-#_=+<>,":
        fpath = fpath.replace(c, " ")

    return fpath.strip()

def getShortName(fpath):
    for i in range(3):
        shortname = getShortNameByFileName(os.path.basename(fpath))
        if not shortname:
            fpath = os.path.dirname(fpath)
        else:
            return shortname

def genVHash(svprev, fpath, fhash):
    """
    the clientkey is not avaliable now, but we can get it by reverse engineering splayer.exe
    to get the clientkey from splayer.exe:
    f = open("splayer","rb").read()
    i = f.find(" %s %s%s")"""
    global CLIENTKEY
    if CLIENTKEY:
        #sprintf_s( buffx, 4096, CLIENTKEY , SVP_REV_NUMBER, szTerm2, szTerm3, uniqueIDHash);
        vhash = hashlib.md5(CLIENTKEY%(svprev, fpath, fhash)).hexdigest()
    else:
        #sprintf_s( buffx, 4096, "un authiority client %d %s %s %s", SVP_REV_NUMBER, fpath.encode("utf8"), fhash.encode("utf8"), uniqueIDHash);
        vhash = hashlib.md5("un authiority client %d %s %s "%(svprev, fpath, fhash)).hexdigest()
    return vhash

def urlopen(url, svprev, formdata):
    ua = "SPlayer Build %d" % svprev
    #prepare data
    #generate a random boundary
    boundary = "----------------------------" + "%x"%random.getrandbits(48)
    data = []
    for item in formdata:
        data.append("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + item[0] + "\"\r\n\r\n" + item[1] + "\r\n")
    data.append("--" + boundary + "--\r\n")
    data = "".join(data)
    cl = str(len(data))

    r = urlparse(url)
    h = HTTPConnection(r.hostname)
    h.connect()
    h.putrequest("POST", r.path, skip_host=True, skip_accept_encoding=True)
    h.putheader("User-Agent", ua)
    h.putheader("Host", r.hostname)
    h.putheader("Accept", "*/*")
    h.putheader("Content-Length", cl)
    h.putheader("Expect", "100-continue")
    h.putheader("Content-Type", "multipart/form-data; boundary=" + boundary)
    h.endheaders()

    h.send(data)

    resp = h.getresponse()
    if resp.status != OK:
        raise Exception("HTTP response " + str(resp.status) + ": " + resp.reason)
    return resp

def downloadSubs(fpath, lang):
    global SVP_REV_NUMBER
    global RETRY
    pathinfo = fpath
    if os.path.sep != "\\":
        #*nix
        pathinfo = "E:\\" + pathinfo.replace(os.path.sep, "\\")
    filehash = genFileHash(fpath)
    shortname = getShortName(fpath)
    vhash = genVHash(SVP_REV_NUMBER, fpath.encode("utf-8"), filehash)
    formdata = []
    formdata.append(("pathinfo", pathinfo.encode("utf-8")))
    formdata.append(("filehash", filehash))
    if vhash:
        formdata.append(("vhash", vhash))
    formdata.append(("shortname", shortname.encode("utf-8")))
    if lang != "chn":
        formdata.append(("lang", lang))

    for server in ["www", "svplayer", "splayer1", "splayer2", "splayer3", "splayer4", "splayer5", "splayer6", "splayer7", "splayer8", "splayer9"]:
        for schema in ["http", "https"]:
            theurl = schema + "://" + server + ".shooter.cn/api/subapi.php"
            for i in range(1, RETRY+1):
                try:
                    log(sys._getframe().f_code.co_name, "Trying %s (retry %d)" % (theurl, i))
                    handle = urlopen(theurl, SVP_REV_NUMBER, formdata)
                    resp = handle.read()
                    if len(resp) > 1024:
                        return resp
                    else:
                        return ''
                except Exception, e:
                    log(sys._getframe().f_code.co_name, "Failed to access %s" % (theurl))
    return ''

class Package(object):
    def __init__(self, s):
        self.parse(s)
    def parse(self, s):
        c = s.read(1)
        self.SubPackageCount = struct.unpack("!B", c)[0]
        log(sys._getframe().f_code.co_name, "SubPackageCount: %d" % (self.SubPackageCount))
        self.SubPackages = []
        for i in range(self.SubPackageCount):
            try:
                sub = SubPackage(s)
            except:
                break
            self.SubPackages.append(sub)

class SubPackage(object):
    def __init__(self, s):
        self.parse(s)
    def parse(self, s):
        c = s.read(8)
        self.PackageLength, self.DescLength = struct.unpack("!II", c)
        self.DescData = s.read(self.DescLength)
        c = s.read(5)
        self.FileDataLength, self.FileCount = struct.unpack("!IB", c)
        self.Files = []
        for i in range(self.FileCount):
            file = SubFile(s)
            self.Files.append(file)

class SubFile(object):
    def __init__(self, s):
        self.parse(s)
    def parse(self, s):
        c = s.read(8)
        self.FilePackLength, self.ExtNameLength = struct.unpack("!II", c)
        self.ExtName = s.read(self.ExtNameLength)
        c = s.read(4)
        self.FileDataLength = struct.unpack("!I", c)[0]
        self.FileData = s.read(self.FileDataLength)
        if self.FileData.startswith("\x1f\x8b"):
            d = zlib.decompressobj(16+zlib.MAX_WBITS)
            self.FileData = d.decompress(self.FileData)

def getSubByHash(fpath, languagesearch, languageshort, languagelong):
    subdata = downloadSubs(fpath, languagesearch)
    if (subdata):
        package = Package(StringIO(subdata))
        basename = os.path.basename(fpath)
        barename = basename.rsplit(".",1)[0]
        id = 0
        for sub in package.SubPackages:
            id += 1
            for file in sub.Files:
                local_tmp_file = os.path.join(__temp__, ".".join([barename, languageshort, str(id), file.ExtName]))
                try:
                    local_file_handle = open(local_tmp_file, "wb")
                    local_file_handle.write(file.FileData)
                    local_file_handle.close()
                except:
                    log(sys._getframe().f_code.co_name, "Failed to save subtitles to '%s'" % (local_tmp_file))
                if (file.ExtName in ["srt", "ssa", "ass", "smi", "sub"]):
                    showname = ".".join([barename, file.ExtName])
                    listitem = xbmcgui.ListItem(label=languagelong,
                                                label2=showname,
                                                iconImage="0",
                                                thumbnailImage=languageshort
                                                )
                    listitem.setProperty( "sync", "true" )
                    listitem.setProperty( "hearing_imp", "false" )
                    url = "plugin://%s/?action=download&filename=%s" % (__scriptid__, local_tmp_file)
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

def CalcFileHash(a):
    def b(j):
        g = ""
        for i in range(len(j)):
            h=ord(j[i])
            if (h+47>=126):
                g += chr(ord(" ") + (h+47) % 126)
            else:
                g += chr(h+47)
        return g
    def d(g):
        h=""
        for i in range(len(g)):
            h+=g[len(g)-i-1]
        return h
    def c(j,h,g,f):
        p = len(j)
        return j[p-f+g-h:p-f+g] +j[p-f:p-f+g-h]+j[p-f+g:p]+j[0:p-f]
    if len(a) >32:
        charString =a[1:len(a)]
        result = {
            'o': lambda : b(c(charString, 8, 17, 27)),
            'n': lambda : b(d(c(charString, 6, 15, 17))),
            'm': lambda : d(c(charString, 6, 11, 17)),
            'l': lambda : d(b(c(charString, 6, 12, 17))),
            'k': lambda : c(charString, 14, 17, 24),
            'j': lambda : c(b(d(charString)), 11, 17, 27),
            'i': lambda : c(d(b(charString)), 5, 7, 24),
            'h': lambda : c(b(charString), 12, 22, 30),
            'g': lambda : c(d(charString), 11, 15, 21),
            'f': lambda : c(charString, 14, 17, 24),
            'e': lambda : c(charString, 4, 7, 22),
            'd': lambda : d(b(charString)),
            'c': lambda : b(d(charString)),
            'b': lambda : d(charString),
            'a': lambda : b(charString)
        }[a[0]]()
        return result
    return a


def getSubByTitle(title, langs):
    subtitles_list = []
    token = __addon__.getSetting("customToken") or DEFAULT_TOKEN
    extra_arg = ""
    if title == os.path.basename(xbmc.Player().getPlayingFile()):
        extra_arg = "&no_muxer=1"
    url = '%s/v1/sub/search?&q=%s&xbmc=1%s' % (
        API_BASE, title, extra_arg)
    r = sess.post(url, headers={'Authorization': 'Bearer %s' % token})
    result = r.json()
    if result['status']:
        dialog = xbmcgui.Dialog()
        if result['status'] == 30900 and token == DEFAULT_TOKEN:
            dialog.notification(__language__(32009), '', xbmcgui.NOTIFICATION_INFO, 3000)
        else:
            dialog.notification(__language__(32010) + '(%d): %s' % (result['status'], result['errmsg']),
               '', xbmcgui.NOTIFICATION_ERROR, 3000)
        return
    for sub in result['sub']['subs']:
        titles = [sub['native_name']]
        if not getCommon([sub['native_name'], sub['videoname']]):
            titles.append(sub['videoname'])
        release = ''
        if 'release_site' in sub and sub['release_site'] != u"个人":
            release = sub['release_site']
        it = {"id": sub['id'],
              "filename": "/".join(titles),
              "rating": str(int(sub['vote_score']) / 20),
              "language_name": "",
              "language_flag": "",
              "release": release,
              "vote_machine_translate": 'vote_machine_translate' in sub,
              "revision": 'revision' in sub and sub['revision'],
              }
        if 'lang' in sub:
            ll = sub['lang']['langlist']
            if 'langchs' in ll or 'langcht' in ll or 'langdou' in ll:
                it.update({"language_name":"Chinese", "language_flag":'zh'})
            elif 'langeng' in ll:
                it.update({"language_name":"English", "language_flag":'en'})
            elif 'langjap' in ll:
                it.update({"language_name":"Japanese", "language_flag":'jp'})
            elif 'langkor' in ll:
                it.update({"language_name":"Korea", "language_flag":'kr'})
            elif 'langesp' in ll:
                it.update({"language_name":"Spanish", "language_flag":'es'})
            elif 'langfra' in ll:
                it.update({"language_name":"France", "language_flag":'fr'})
        subtitles_list.append(it)

    if subtitles_list:
        for it in subtitles_list:
            fname = it["filename"]
            if it["release"]:
                fname = "[B]%s[/B] %s" % (it["release"], fname)
            if it["vote_machine_translate"] or it["revision"]:
                fname = "[COLOR FF999999]%s[/COLOR]" % fname
            listitem = xbmcgui.ListItem(label=it["language_name"],
                                        label2=fname,
                                        iconImage=it["rating"],
                                        thumbnailImage=it["language_flag"]
                                        )
            sync = "false"
            try:
                # remove resolution
                pattern = re.sub("\d{3,4}[Pp]", ".+", os.path.splitext(title)[0])
                if re.findall(pattern, it['filename'], re.I):
                    sync = 'true'
            except:
                pass
            listitem.setProperty("sync", sync)
            listitem.setProperty("hearing_imp", "false")
            url = "plugin://%s/?action=download&fid=%s" % (
                __scriptid__, it["id"])
            xbmcplugin.addDirectoryItem(handle=int(
                sys.argv[1]), url=url, listitem=listitem, isFolder=False)


def Search(item):
    try: rmtree(__temp__)
    except: pass
    try: os.makedirs(__temp__)
    except: pass

    if item['mansearch']:
        title = item['mansearchstr']
        getSubByTitle(title, item['3let_language'])
    else:
        title = '%s %s' % (item['title'], item['year'])
        # pass original filename, api.assrt.net will handle it more properly
        getSubByTitle(xbmc.getInfoLabel("VideoPlayer.Title"), item['3let_language']) # use assrt.net
        if __addon__.getSetting("subSourceAPI") == 'true': # use splayer api
            if 'chi' in item['3let_language']:
                getSubByHash(item['file_original_path'], "chn", "zh", "Chinese")
            if 'eng' in item['3let_language']:
                getSubByHash(item['file_original_path'], "eng", "en", "English")

def ChangeFileEndcoding(filepath):
    if __addon__.getSetting("transUTF8") == "true" and os.path.splitext(filepath)[1] in SUBTYPE_EXT:
        data = open(filepath, 'rb').read()
        enc = chardet.detect(data)['encoding']
        if enc:
            data = data.decode(enc, 'ignore')
            if __addon__.getSetting("transJianFan") == "1":   # translate to Simplified
                data = Converter('zh-hans').convert(data)
            elif __addon__.getSetting("transJianFan") == "2": # translate to Traditional
                data = Converter('zh-hant').convert(data)
            data = data.encode('utf-8', 'ignore')
        try:
            local_file_handle = open(filepath, "wb")
            local_file_handle.write(data)
            local_file_handle.close()
        except:
            log(sys._getframe().f_code.co_name, "Failed to save subtitles to '%s'" % (filepath))

def Download(filename):
    subtitle_list = []
    ChangeFileEndcoding(filename.decode('utf-8'))
    subtitle_list.append(filename)
    return subtitle_list

def CheckSubList(files):
    list = []
    for subfile in files:
        if os.path.splitext(subfile)[1] in SUBTYPE_EXT:
            list.append(subfile)
    return list

# https://yooooo.us/2014/a-string-pattern-finding-algorithm
def getCommon(ori_lst, splt='.-_ ]', with_no_digit=False):
    if not ori_lst:
        return ''
    lst = ['.'.join(x.split('.')[:-1]) for x in ori_lst]#strip ext name
    if len(lst) == 1:
        return lst[0]
    # judge which splitter gets most split
    m_splt = max(splt, key = lambda x:sum(map(lambda l:len(l.split(x)), lst)))
    def getEqual(l):
        cnt = len(l)
        equals = {}
        for i, j in itertools.combinations(l, 2):
            if not i or not j:
                continue
            if i == j:
                pass
            elif i.upper() == j.upper():
                i = i.upper()
            else:
                continue
            #else i == j
            if i not in equals:
                equals[i] = 1
            else:
                equals[i] += 1
        if not equals:
            #print 'end'
            return False, ''
        m = max(equals.iteritems(), key = lambda x:x[1])
        _comb = cnt * (cnt -1) /2
        if m[1] > 0.3 * _comb or m[1] == _comb:
            return True, m[0]
        else:
            return False, ''
    m_lst = map(lambda l:l.split(m_splt), lst)
    m_pattern = []
    for p in map(None, *m_lst):#add None to fillup short ones
        suc, new_pattern = getEqual(p)
        if suc:
            m_pattern.append(new_pattern)
        else:
            break
    ret = m_splt.join(m_pattern) + (']' if m_splt == ']' else '')
    if not ret and not with_no_digit:#let's try strings without digits to get rid of "season" and "episode" difference
        return getCommon(lst, with_no_digit=True)#we pass prepared lst instead of ori_lst
    else:
        return ret

def Detail(id):
    try:
        os.makedirs(__temp__)
    except:
        pass

    token = __addon__.getSetting("customToken") or DEFAULT_TOKEN
    url = '%s/v1/sub/detail?id=%s&xbmc=1' % (API_BASE, id)
    r = sess.post(url, headers={'Authorization': 'Bearer %s' % token})
    result = r.json()
    if result['status']:
        dialog = xbmcgui.Dialog()
        if result['status'] == 30900 and token == DEFAULT_TOKEN:
            dialog.notification(__language__(32009), '', xbmcgui.NOTIFICATION_INFO, 3000)
        else:
            dialog.notification(__language__(32010) + '(%d): %s' % (result['status'], result['errmsg']),
                '', xbmcgui.NOTIFICATION_ERROR, 3000)
        return []
    sub = result['sub']['subs'][0]
    if 'filelist' not in sub or len(sub['filelist']) == 0:
        ext = os.path.splitext(sub['filename'])[1].lower()
        if ext not in SUBTYPE_EXT:
            r = sess.get(sub['url'])
            data = r.content
            return extractArchive(data)
        # single file, not archive
        url = sub['url']
    elif len(sub['filelist']) == 1:
        url = sub['filelist'][0]['url']
        ext = os.path.splitext(sub['filelist'][0]['f'])[1].lower()
    else:
        allfiles = CheckSubList([f["f"] for f in sub['filelist']])
        common_prefix = getCommon(allfiles)
        sel = xbmcgui.Dialog().select(__language__(32006), [
            f[len(common_prefix):].lstrip('.') for f in allfiles])
        if sel == -1:
            return []
        url = sub['filelist'][sel]['url']
        ext = os.path.splitext(sub['filelist'][sel]['f'])[1].lower()
    r = sess.get(url)
    # XXX: use unicode path may not work on some android devices
    filename = os.path.join(__temp__, "%x.ass" % (random.getrandbits(48)))
    with open(filename, "wb") as f:
        f.write(r.content)
    ChangeFileEndcoding(filename)
    return [filename]


def rmtree(path):
    if isinstance(path, unicode):
        path = path.encode('utf-8')
    dirs, files = xbmcvfs.listdir(path)
    for dir in dirs:
        rmtree(os.path.join(path, dir))
    for file in files:
        xbmcvfs.delete(os.path.join(path, file))
    xbmcvfs.rmdir(path)

def DownloadID(id):
    try:
        rmtree(__temp__)
    except:
        pass
    try:
        os.makedirs(__temp__)
    except:
        pass

    url = 'http://shooter.cn/files/file3.php?hash=duei7chy7gj59fjew73hdwh213f&fileid=%s' % (
        id)
    data = sess.get(url).content
    url = 'http://file0.shooter.cn%s' % (splayer.CalcFileHash(data))
    #log(sys._getframe().f_code.co_name ,"url is %s" % (url))
    data = sess.get(url).content
    return extractArchive(data)


def extractArchive(data):
    subtitle_list = []
    header = data[:4]
    if header == 'Rar!':
        zipext = ".rar"
    else: # header == 'PK':
        zipext = ".zip"
    zipname = 'SUBPACK%s' % (zipext)
    zip = os.path.join( __temp__, zipname)
    with open(zip, "wb") as subFile:
        subFile.write(data)
    subFile.close()
    xbmc.sleep(500)
    dirs, files = xbmcvfs.listdir(__temp__) # refresh xbmc folder cache
    xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (zip,__temp__,)).encode('utf-8'), True)
    path = __temp__
    dirs, files = xbmcvfs.listdir(path)
    list = CheckSubList(files)
    if not list and len(dirs) > 0:
        path = os.path.join(__temp__, dirs[0].decode('utf-8'))
        dirs, files = xbmcvfs.listdir(path)
        list = CheckSubList(files)
    if list:
        filename = list[0].decode('utf-8')
    else:
        filename = ''
    if len(list) > 1:
        dialog = xbmcgui.Dialog()
        sel = dialog.select(__language__(32006), list)
        if sel != -1:
            filename = list[sel].decode('utf-8')
    if filename:
        filepath = os.path.join(path, filename)
        ChangeFileEndcoding(filepath)
        subtitle_list.append(filepath)

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
        item['title'] = xbmc.getInfoLabel("VideoPlayer.Title")                       # no original title, get just Title
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
    if 'fid' in params:
        subs = Detail(params["fid"])
    elif 'id' in params:
        subs = DownloadID(params["id"])
    else:
        subs = Download(params["filename"])
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
