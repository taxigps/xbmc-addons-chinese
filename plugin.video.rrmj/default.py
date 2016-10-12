# -*- coding: utf8 -*-
import os
import sys
import xbmcaddon
ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo('path').decode("utf-8")
sys.path.append(os.path.join(ADDON_PATH, 'resources', 'lib'))

from path import plugin

if __name__ == '__main__':
    plugin.run()
