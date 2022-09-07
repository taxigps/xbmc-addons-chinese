
import os
from requests import Session

import xbmcaddon
import xbmcgui

__addon__ = xbmcaddon.Addon()
__language__ = __addon__.getLocalizedString

from resources.lib.utilities import log

API_URL = "https://api.assrt.net/"
API_SUBTITLES = "v1/sub/search"
API_DOWNLOAD = "v1/sub/detail"
DEFAULT_TOKEN = "vXMvTf8eu4pfmAVmllp8OY6aYqVbeB4F"

CONTENT_TYPE = "application/json"
REQUEST_TIMEOUT = 30

SUBTYPE_EXT = (".srt", ".smi", ".ssa", ".ass", ".sup")

def logging(msg):
    return log(__name__, msg)

def server_msg(errorID):
    dialog = xbmcgui.Dialog()
    if errorID == 30900 and self.api_key == DEFAULT_TOKEN:
        dialog.notification(__name__, __language__(32009),
                        xbmcgui.NOTIFICATION_INFO, 3000)
    else:
        dialog.notification(__name__, __language__(32010) + '(%d): %s' % (result['status'], result['errmsg']),
                        xbmcgui.NOTIFICATION_ERROR, 3000)

class AssrtProvider:

    def __init__(self, api_key):

        self.api_key = api_key or DEFAULT_TOKEN

        self.request_headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": CONTENT_TYPE, "Accept": CONTENT_TYPE}

        self.session = Session()
        self.session.headers = self.request_headers

    def search_subtitles(self, query):
        # build query request
        subtitles_url = API_URL + API_SUBTITLES
        params = {"q": query}
        r = self.session.get(subtitles_url, params=params, timeout=REQUEST_TIMEOUT)
        logging(r.url)
        logging(r.request.headers)

        result = r.json()
        if result["status"]: # server return errorID
            server_msg(result["status"])
            return None

        logging(f"Query returned {len(result['sub']['subs'])} subtitles")

        if len(result["sub"]["subs"]):
            return result["sub"]["subs"]

        return None

    def download_subtitle(self, id):
        logging(f"Downloading subtitle ID： {id}")

        # build download request
        download_url = API_URL + API_DOWNLOAD
        params = {"id": id}
        r = self.session.get(download_url, params=params, timeout=REQUEST_TIMEOUT)
        logging(r.url)
        logging(r.request.headers)

        result = r.json()
        if result["status"]: # server return errorID
            server_msg(result["status"])
            return None

        sub = result["sub"]["subs"][0]
        if "filelist" not in sub or len(sub["filelist"]) == 0:
            ext = os.path.splitext(sub["filename"])[1].lower()
            url = sub["url"]
        elif len(sub["filelist"]) == 1:
            url = sub["filelist"][0]["url"]
            ext = os.path.splitext(sub["filelist"][0]["f"])[1].lower()
        else:
            sublist = [x for x in sub["filelist"] if os.path.splitext(x["f"])[1] in SUBTYPE_EXT]
            slist = [x["f"] for x in sublist]
            sel = xbmcgui.Dialog().select(__language__(32006), slist)
            if sel == -1:
                return None
            url = sublist[sel]["url"]
            ext = os.path.splitext(sublist[sel]["f"])[1].lower()
        r = self.session.get(url)
        subtitle = {"ext": ext, "content": r.content}
        return subtitle
