import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc
import sys
import dircache
import fnmatch
import operator
import os

addon = xbmcaddon.Addon()
thisPlugin = int(sys.argv[1])
pwd_path=addon.getAddonInfo('path')
f = open(os.path.join(pwd_path,'channel_list.txt'),'r')
tv_dict= {}
for line in f:
    if line.startswith('channel'): 
        key, value =line.split()
        tv_dict[key] = value
        xbmc.log(  key + ' =' + tv_dict[key])
f.close
xbmc.log('#=#=#=# fufill the dictionary #=#=#`=#')

def createListing():
    dirContent = dircache.listdir(pwd_path)
    #parse contents for all .flv files
    dirContent = fnmatch.filter(dirContent, '*.flv')
    #create listing
    listing = []
    for file in dirContent:
        uri = 'http://fms.cntv.lxdns.com/live/flv/' + file
        label = file.replace('.flv','')
        label = label.replace('channel','')
        
        # 
        if file in tv_dict: 
            xbmc.log( '#=#=#=# ' +  file + '=' + tv_dict[file] + ' #=#=#=#')
            label = tv_dict[file] + ' ' + label.zfill(3)
        else:
            label = label.zfill(3)
        listing.append([label,uri])
    listing=sorted(listing, key=operator.itemgetter(0))
    return listing

def sendToXbmc(listing):
    global thisPlugin
    for item in listing:
    	listItem = xbmcgui.ListItem(item[0])
    	xbmcplugin.addDirectoryItem(thisPlugin,item[1],listItem)

    xbmcplugin.endOfDirectory(thisPlugin)

sendToXbmc(createListing())
