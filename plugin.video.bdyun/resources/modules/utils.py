"""
This file contains additional utility functions
"""
import xbmc, xbmcgui, xbmcvfs, xbmcaddon
import os
import sys

__addon_id__= u'plugin.video.bdyun'
__Addon = xbmcaddon.Addon(__addon_id__)


def data_dir():
    """"get user data directory of this addon. 
    according to http://wiki.xbmc.org/index.php?title=Add-on_Rules#Requirements_for_scripts_and_plugins
    """
    __datapath__ = xbmc.translatePath( __Addon.getAddonInfo('profile') ).decode('utf-8')
    if not xbmcvfs.exists(__datapath__):
        xbmcvfs.mkdir(__datapath__)
    return __datapath__

def addon_dir():
    """"get source directory of this addon.
    according to http://wiki.xbmc.org/index.php?title=Add-on_Rules#Requirements_for_scripts_and_plugins
    """
    return __Addon.getAddonInfo('path').decode('utf-8')

def encode(string):
    return string.encode('UTF-8','replace')

def decode(string):
    return string.decode('UTF-8') 

def log(message,loglevel=xbmc.LOGNOTICE):
    """"save message to kodi.log.
    
    Args:
        message: has to be unicode, http://wiki.xbmc.org/index.php?title=Add-on_unicode_paths#Logging
        loglevel: xbmc.LOGDEBUG, xbmc.LOGINFO, xbmc.LOGNOTICE, xbmc.LOGWARNING, xbmc.LOGERROR, xbmc.LOGFATAL
    """
    xbmc.log(encode(__addon_id__ + u": " + message), level=loglevel)
    

def showNotification(title,message, time=4000):
    """Show Notification

    Args: 
        title: has to be unicode
        message: has to be unicode
        time: Time that the message is beeing displayed
    """
    __addoniconpath__ = os.path.join(addon_dir(),"icon.png")
    log(u'Notification. %s: %s' % (title, message) )
    xbmc.executebuiltin(encode('Notification("' + title + '","' + message + '",'+(str(time)).decode('utf-8')+',"' + __addoniconpath__ + '")'))

def getString(string_id):
    # return a localized string from resources/language/*.po
    # The returned string is unicode
    return __Addon.getLocalizedString(string_id)
