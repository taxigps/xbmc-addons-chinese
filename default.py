# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcaddon
import os

from resources.lib.utils import *

mode = xbmcgui.Dialog().select(getString(30030),[getString(30031),getString(30032)])

#check if program should be run
if(mode != -1):

    if(mode == 0):
        #open the settings dialog
        openSettings()

    elif(mode == 1):
        addonid = 'pvr.iptvsimple'
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", "params": { "addonid": "%s", "enabled": true }, "id": 1 }' %(addonid))
        iptvsimple = xbmcaddon.Addon(id=addonid)

        iptvsimple.setSetting("logoPathType", "0") #set to local path
        logoPath = os.path.join(addon_dir(), "resources", "media")
        iptvsimple.setSetting("logoPath", logoPath)

        iptvsimple.setSetting("m3uPathType", "0") #set to local path
        m3uPath = os.path.join(addon_dir(), "resources", "channel.m3u")
        iptvsimple.setSetting("m3uPath", m3uPath)

        if getSetting("epg") == "true":
            iptvsimple.setSetting("epgPathType", "0") #set to local path
            epgPath = os.path.join(data_dir(), "epg.xml")
            iptvsimple.setSetting("epgPath", epgPath)

        iptvsimple.openSettings()
