
import os
from urllib.parse import unquote
from difflib import SequenceMatcher

import xbmc

from resources.lib.utilities import log, normalize_string

def get_file_path():
    return xbmc.Player().getPlayingFile()


def get_media_data(params):
    item = {"year": xbmc.getInfoLabel("VideoPlayer.Year"),
            "season_number": str(xbmc.getInfoLabel("VideoPlayer.Season")),
            "episode_number": str(xbmc.getInfoLabel("VideoPlayer.Episode")),
            "tv_show_title": normalize_string(xbmc.getInfoLabel("VideoPlayer.TVshowtitle")),
            "original_title": normalize_string(xbmc.getInfoLabel("VideoPlayer.OriginalTitle")),
            "3let_language": []}

    for lang in unquote(params.get("languages")).split(","):
        item['3let_language'].append(xbmc.convertLanguage(lang, xbmc.ISO_639_1))

    if item["tv_show_title"]:
        item["title"] = item["tv_show_title"]
        item["year"] = None  # Kodi gives episode year, OS searches by series year. Without year safer.
    elif item["original_title"]:
        item["title"] = item["original_title"]
    else:
        # no original title, get just Title
        item['title'] = xbmc.getInfoLabel("VideoPlayer.Title")
        # get movie title and year if is filename
        if item['title'] == os.path.basename(xbmc.Player().getPlayingFile()):
            title, year = xbmc.getCleanMovieTitle(item['title'])
            item['title'] = title.replace('[', '').replace(']', '')
            item['year'] = year

    if item["episode_number"].lower().find("s") > -1:  # Check if season is "Special"
        item["season_number"] = "0"
        item["episode_number"] = item["episode_number"][-1:]

    return item

def clean_movie_name(native_name, videoname):
    if not native_name:
        if not videoname:
            raise ValueError("None of native_name, videoname contains a string")
        else:
            name = videoname
    else:
        name = native_name

    match_ratio = SequenceMatcher(None, name, videoname).ratio()
    log(__name__, f"name: {name}, videoname: {videoname}, match_ratio: {match_ratio}")
    if name in videoname:
        return videoname
    elif match_ratio > 0.3:
        return videoname
    else:
        return f"{name} {videoname}"

def convert_language(langlist):
    lang = ""
    if 'langchs' in langlist or 'langcht' in langlist or 'langdou' in langlist:
        lang = "zh"
    elif 'langeng' in langlist:
        lang = "en"
    elif 'langjap' in langlist:
        lang = "jp"
    elif 'langkor' in langlist:
        lang = "kr"
    elif 'langesp' in langlist:
        lang = "es"
    elif 'langfra' in langlist:
        lang = "fr"
    return lang
