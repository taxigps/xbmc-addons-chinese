import os
import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()
pwd_path=addon.getAddonInfo('path')

xbmcplugin.setContent(addon_handle, 'movies')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

mode = args.get('mode', None)

if mode is None:
    f = open(os.path.join(pwd_path,'cat_list.txt'),'r')
    for i in f:
        if i.startswith('Y'): 
            Y,cat,sym =i.split()
            url = build_url({'mode': 'folder', 'foldername': cat, 'symbol': sym })
            li = xbmcgui.ListItem(cat, iconImage=pwd_path+'/'+'icon.png')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)
    f.close()
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder':
    foldername = args['foldername'][0]
    symbol=args['symbol'][0]
    print 'cat='+foldername+' symbol='+symbol
    f = open(os.path.join(pwd_path,'tv_list.txt'),'r')
    tv_listing = []                                          
    for i in f:
        if i and i[0].isalpha(): 
            id,label,url =i.split()
            if symbol in id and 'N'not in id:
                tv_listing.append([label,url])
    f.close()
    tv_listing.sort()
    for i in tv_listing:
        li = xbmcgui.ListItem(i[0], iconImage='icon.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=i[1], listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)
