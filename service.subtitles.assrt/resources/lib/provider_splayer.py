import hashlib
import os
import random
import struct
import sys
import zlib
from http.client import HTTPConnection, OK
from io import BytesIO
from urllib.parse import urlparse

import xbmcaddon
import xbmcvfs

from resources.lib.utilities import log

__addon__ = xbmcaddon.Addon()
__profile__ = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
__temp__ = xbmcvfs.translatePath(os.path.join(__profile__, "temp", ""))

SVP_REV_NUMBER = 1543
CLIENTKEY = "SP,aerSP,aer %d &e(\xd7\x02 %s %s"
RETRY = 3

def logging(msg):
    return log(__name__, msg)

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

class Package(object):
    def __init__(self, s):
        self.parse(s)
    def parse(self, s):
        c = s.read(1)
        self.SubPackageCount = struct.unpack("!B", c)[0]
        logging("SubPackageCount: %d" % (self.SubPackageCount))
        self.SubPackages = []
        for i in range(self.SubPackageCount):
            try:
                sub = SubPackage(s)
            except:
                logging("Error (%d) [%s]" % (
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

class SplayerProvider:

    def __init__(self):
        self.subtitles = []

    def search_subtitles(self, filepath, langs):
        self.subtitles = []
        if "zh" in langs:
            self.getSubByHash(filepath, "chn", "zh", "Chinese")
        if "en" in langs:
            self.getSubByHash(filepath, "eng", "en", "English")

        logging(f"Query returned {len(self.subtitles)} subtitles")

        if len(self.subtitles):
            return self.subtitles

        return None


    def getSubByHash(self, filepath, languagesearch, languageshort, languagelong):
        subdata = self.downloadSubs(filepath, languagesearch)
        if (subdata):
            package = Package(BytesIO(subdata))
            basename = os.path.basename(filepath)
            barename = basename.rsplit(".", 1)[0]
            id = 0
            for sub in package.SubPackages:
                id += 1
                for file in sub.Files:
                    local_tmp_file = os.path.join(__temp__, ".".join(
                        [barename, languageshort, str(id), file.ExtName]))
                    try:
                        local_file_handle = open(local_tmp_file, "wb")
                        local_file_handle.write(file.FileData)
                        local_file_handle.close()
                    except:
                        logging(f"Failed to save subtitles to '{local_tmp_file}'")
                    self.subtitles.append({"filepath": local_tmp_file, 
                                           "filename": ".".join([barename, file.ExtName]),
                                           "ext": file.ExtName,
                                           "language_flag": languageshort,
                                           "language_name": languagelong})

    def downloadSubs(self, fpath, lang):
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
                        logging("Trying %s (retry %d)" % (theurl, i))
                        handle = self.urlopen(theurl, SVP_REV_NUMBER, formdata)
                        resp = handle.read()
                        if len(resp) > 1024:
                            return resp
                        else:
                            return ''
                    except Exception as e:
                        logging("Failed to access %s" % (theurl))
        return ''

    def urlopen(self, url, svprev, formdata):
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
