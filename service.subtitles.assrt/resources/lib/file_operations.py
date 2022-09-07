
import chardet
import os

import xbmcaddon

from resources.lib.langconv import Converter
from resources.lib.utilities import log

__addon__ = xbmcaddon.Addon()

TEXTSUB_EXT = (".srt", ".smi", ".ssa", ".ass")

def get_file_data(file_original_path):
    item = {"temp": False, "rar": False, "file_original_path": file_original_path}


    if file_original_path.find("http") > -1:
        item["temp"] = True

    elif file_original_path.find("rar://") > -1:
        item["rar"] = True
        item["file_original_path"] = os.path.dirname(file_original_path[6:])

    elif file_original_path.find("stack://") > -1:
        stack_path = file_original_path.split(" , ")
        item["file_original_path"] = stack_path[0][8:]

    return item

def change_file_encoding(filepath):
    if __addon__.getSetting("transUTF8") == "true" and os.path.splitext(filepath)[1] in TEXTSUB_EXT:
        data = open(filepath, 'rb').read()
        enc = chardet.detect(data)['encoding']
        if enc:
            data = data.decode(enc, 'ignore')
            # translate to Simplified
            if __addon__.getSetting("transJianFan") == "1":
                data = Converter('zh-hans').convert(data)
            # translate to Traditional
            elif __addon__.getSetting("transJianFan") == "2":
                data = Converter('zh-hant').convert(data)
            data = data.encode('utf-8', 'ignore')
        try:
            local_file_handle = open(filepath, "wb")
            local_file_handle.write(data)
            local_file_handle.close()
        except:
            log(__name__, "Failed to save subtitles to '%s'" % (filepath))
