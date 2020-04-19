# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import urllib
import urllib.parse
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin
import chardet

import hashlib
from http.client import HTTPConnection, OK
import struct
from io import BytesIO
import zlib
import random
from bs4 import BeautifulSoup

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
from langconv import *

SVP_REV_NUMBER = 1543
CLIENTKEY = "SP,aerSP,aer %d &e(\xd7\x02 %s %s"
RETRY = 3

def log(module, msg):
    xbmc.log("{0}::{1} - {2}".format(__scriptname__,module,msg) ,level=xbmc.LOGDEBUG )

def grapBlock(f, offset, size):
    f.seek(offset, 0)
    return f.readBytes(size)

def getBlockHash(f, offset):
    return hashlib.md5(grapBlock(f, offset, 4096)).hexdigest()

def genFileHash(fpath):
    f = xbmcvfs.File(fpath)
    ftotallen = f.size()
    if ftotallen < 8192:
        f.close()
        return ""
    offset = [4096, int(ftotallen/3*2), int(ftotallen/3), ftotallen - 8192]
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
        vhash = hashlib.md5((CLIENTKEY%(svprev, fpath, fhash)).encode("utf-8")).hexdigest()
    else:
        #sprintf_s( buffx, 4096, "un authiority client %d %s %s %s", SVP_REV_NUMBER, fpath, fhash, uniqueIDHash);
        vhash = hashlib.md5(("un authiority client %d %s %s "%(svprev, fpath, fhash)).encode("utf-8")).hexdigest()
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
    data = ("".join(data)).encode('utf-8')
    cl = str(len(data))

    r = urllib.parse.urlparse(url)
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
    vhash = genVHash(SVP_REV_NUMBER, fpath, filehash)
    formdata = []
    formdata.append(("pathinfo", pathinfo))
    formdata.append(("filehash", filehash))
    if vhash:
        formdata.append(("vhash", vhash))
    formdata.append(("shortname", shortname))
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
                except Exception as e:
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
                log(sys._getframe().f_code.co_name, "Error (%d) [%s]" % (
                    sys.exc_info()[2].tb_lineno,
                    sys.exc_info()[1]
                    ))
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
        self.ExtName = s.read(self.ExtNameLength).decode("utf-8")
        c = s.read(4)
        self.FileDataLength = struct.unpack("!I", c)[0]
        self.FileData = s.read(self.FileDataLength)
        if self.FileData.startswith(b"\x1f\x8b"):
            d = zlib.decompressobj(16+zlib.MAX_WBITS)
            self.FileData = d.decompress(self.FileData)

def getSubByHash(fpath, languagesearch, languageshort, languagelong):
    subdata = downloadSubs(fpath, languagesearch)
    if (subdata):
        package = Package(BytesIO(subdata))
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
                                                label2=showname)
                    listitem.setArt({'icon': "0", 'thumb': languageshort})
                    listitem.setProperty( "sync", "true" )
                    listitem.setProperty( "hearing_imp", "false" )
                    url = "plugin://%s/?action=download&filename=%s" % (__scriptid__, local_tmp_file)
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

def Search(item):
    if not xbmcvfs.exists(__temp__.replace('\\','/')):
        xbmcvfs.mkdirs(__temp__)
    dirs, files = xbmcvfs.listdir(__temp__)
    for file in files:
        xbmcvfs.delete(os.path.join(__temp__, file))

    if 'chi' in item['3let_language']:
        getSubByHash(item['file_original_path'], "chn", "zh", "Chinese")
    if 'eng' in item['3let_language']:
        getSubByHash(item['file_original_path'], "eng", "en", "English")

def ChangeFileEndcoding(filepath):
    if __addon__.getSetting("transUTF8") == "true" and os.path.splitext(filepath)[1] in [".srt", ".ssa", ".ass", ".smi"]:
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
                log(sys._getframe().f_code.co_name, "Failed to save subtitles to '%s'" % (filename))

def Download(filename):
    subtitle_list = []
    ChangeFileEndcoding(filename)
    subtitle_list.append(filename)
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
        item['title'] = xbmc.getInfoLabel("VideoPlayer.Title")                         # no original title, get just Title
        if item['title'] == os.path.basename(xbmc.Player().getPlayingFile()):          # get movie title and year if is filename
            title, year = xbmc.getCleanMovieTitle(item['title'])
            item['title'] = title.replace('[','').replace(']','')
            item['year'] = year

    if item['episode'].lower().find("s") > -1:                                         # Check if season is "Special"
        item['season'] = "0"                                                           #
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
    subs = Download(params["filename"])
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
