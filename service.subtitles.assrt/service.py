
import sys
import xbmcplugin

from resources.lib.subtitle_downloader import SubtitleDownloader


SubtitleDownloader().handle_action()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
