
import os
import re
import shutil
import sys
import uuid
from urllib.parse import quote_plus

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.provider_assrt import AssrtProvider
from resources.lib.provider_splayer import SplayerProvider
from resources.lib.utilities import get_params, log
from resources.lib.file_operations import get_file_data, change_file_encoding
from resources.lib.data_collector import get_media_data, get_file_path, clean_movie_name, convert_language

__addon__ = xbmcaddon.Addon()
__scriptid__ = __addon__.getAddonInfo("id")

__profile__ = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
__temp__ = xbmcvfs.translatePath(os.path.join(__profile__, "temp", ""))

SUBTYPE_EXT = (".srt", ".smi", ".ssa", ".ass", ".sup")
SUPPORTED_ARCHIVE_EXT = (".zip", ".rar")

class SubtitleDownloader:

    def __init__(self):

        self.api_key = __addon__.getSetting("customToken")

        log(__name__, sys.argv)

        self.handle = int(sys.argv[1])
        self.params = get_params()
        self.query = ""
        self.subtitles = {}
        self.file = {}

        self.assrt_subtitles = AssrtProvider(self.api_key)
        self.splayer_subtitles = SplayerProvider()

    def handle_action(self):
        log(__name__, "action '%s' called" % self.params["action"])
        if self.params["action"] == "manualsearch":
            self.search(self.params['searchstring'])
        elif self.params["action"] == "search":
            self.search()
        elif self.params["action"] == "downloadID":
            self.downloadID(self.params["id"])
        elif self.params["action"] == "download":
            self.download(self.params["filepath"])

    def search(self, query=""):
        if xbmcvfs.exists(__temp__.replace('\\','/')):
            shutil.rmtree(__temp__)
        xbmcvfs.mkdirs(__temp__)

        file_data = get_file_data(get_file_path())
        media_data = get_media_data(self.params)

        log(__name__, "file_data '%s' " % file_data)
        log(__name__, "media_data '%s' " % media_data)

        if query:
            self.query = query
        else:
            self.query = '%s %s' % (media_data['title'], media_data['year'])

        self.subtitles = self.assrt_subtitles.search_subtitles(self.query)

        if self.subtitles and len(self.subtitles):
            log(__name__, f"{len(self.subtitles)} subtitle found from assrt.net")
            self.list_subtitles()
        else:
            log(__name__, "No subtitle found from assrt.net")

        if __addon__.getSetting("subSourceAPI") == 'true':  # use splayer api
            self.subtitles = self.splayer_subtitles.search_subtitles(
                            file_data["file_original_path"], media_data["3let_language"])
            if self.subtitles and len(self.subtitles):
                log(__name__, f"{len(self.subtitles)} subtitle found from splayer")
                self.list_subtitles2()
            else:
                log(__name__, "No subtitle found from splayer")

    def downloadID(self, id):
        self.file = self.assrt_subtitles.download_subtitle(id)

        if self.file:
            log(__name__, "download file type '%s' " % self.file["ext"])
            file_path = os.path.join(__temp__, f"{str(uuid.uuid4())}{self.file['ext']}")
            tmp_file = open(file_path, "w" + "b")
            tmp_file.write(self.file["content"])
            tmp_file.close()

            if self.file["ext"] in SUPPORTED_ARCHIVE_EXT:
                archive = quote_plus(file_path)
                if self.file["ext"] == '.rar':
                    path = 'rar://%s' % (archive)
                else:
                    path = 'zip://%s' % (archive)
                dirs, files = xbmcvfs.listdir(path)
                if ('__MACOSX') in dirs:
                    dirs.remove('__MACOSX')
                if len(dirs) > 0:
                    path = path + '/' + dirs[0]
                    dirs, files = xbmcvfs.listdir(path)
                slist = []
                for subfile in files:
                    if (os.path.splitext( subfile )[1] in SUBTYPE_EXT):
                        slist.append(subfile)
                if len(slist) == 1:
                    subtitle_path = path + '/' + slist[0]
                elif len(slist) > 1:
                    sel = xbmcgui.Dialog().select(__language__(32006), slist)
                    if sel == -1:
                        return
                    subtitle_path = path + '/' + list[sel]
                file_path2 = os.path.join(__temp__, f"{str(uuid.uuid4())}{os.path.splitext(subtitle_path)[1]}")
                if xbmcvfs.copy(subtitle_path, file_path2):
                    subtitle_path = file_path2
            elif self.file["ext"] in SUBTYPE_EXT:
                subtitle_path = file_path
            else:
                log(__name__, "Unsupported archive file: %s" % (self.file["ext"]))
                return

            change_file_encoding(subtitle_path)
            list_item = xbmcgui.ListItem(label=subtitle_path)
            xbmcplugin.addDirectoryItem(handle=self.handle, url=subtitle_path, listitem=list_item, isFolder=False)
        return

    def download(self, filepath):
        change_file_encoding(filepath)
        list_item = xbmcgui.ListItem(label=filepath)
        xbmcplugin.addDirectoryItem(handle=self.handle, url=filepath, listitem=list_item, isFolder=False)
        return

    def list_subtitles(self):
        for subtitle in self.subtitles:
            language_name = ""
            language_flag = ""
            if "lang" in subtitle:
                language_flag = convert_language(subtitle["lang"]["langlist"])
                language_name = xbmc.convertLanguage(language_flag, xbmc.ENGLISH_NAME)

            clean_name = clean_movie_name(subtitle["native_name"], subtitle["videoname"])
            fname = clean_name
            if "release_site" in subtitle and subtitle["release_site"] != u"个人":
                fname = "[B]%s[/B] %s" % (subtitle["release_site"], fname)
            if ("vote_machine_translate" in subtitle) or ("revision" in subtitle and subtitle["revision"]):
                fname = "[COLOR FF999999]%s[/COLOR]" % fname
            if "subtype" in subtitle:
                subtype = subtitle["subtype"]
            else:
                subtype = "未标"
            fname = "[%s]%s" % (subtype, fname)

            list_item = xbmcgui.ListItem(label=language_name,
                                         label2=fname)
            list_item.setArt({
                "icon": str(int(subtitle["vote_score"]) / 20),
                "thumb": language_flag})

            sync = "false"
            try:
                # remove resolution
                pattern = re.sub("\d{3,4}[Pp]", ".+", os.path.splitext(os.path.basename(get_file_path()))[0])
                if re.findall(pattern, clean_name, re.I):
                    sync = 'true'
            except:
                pass
            list_item.setProperty("sync", sync)
            list_item.setProperty("hearing_imp", "false")

            url = f"plugin://{__scriptid__}/?action=downloadID&id={subtitle['id']}"

            xbmcplugin.addDirectoryItem(handle=self.handle, url=url, listitem=list_item, isFolder=False)

    def list_subtitles2(self):
        for subtitle in self.subtitles:
            if (subtitle["ext"] in ["srt", "ssa", "ass", "smi", "sub"]):
                showname = f"[{subtitle['ext'].upper()}]{subtitle['filename']}"
                list_item = xbmcgui.ListItem(label=subtitle["language_name"],
                                            label2=showname)
                list_item.setArt({'icon': "0", 'thumb': subtitle["language_flag"]})
                list_item.setProperty("sync", "true")
                list_item.setProperty("hearing_imp", "false")
                url = f"plugin://{__scriptid__}/?action=download&filepath={subtitle['filepath']}"
                xbmcplugin.addDirectoryItem(handle=self.handle, url=url, listitem=list_item, isFolder=False)

