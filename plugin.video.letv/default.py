# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, string, sys, os, gzip, StringIO
import math, os.path, httplib, time, random
import cookielib
import base64
import simplejson
import threading

try:
    from ChineseKeyboard import Keyboard as Apps
except:
    from xbmc import Keyboard as Apps

########################################################################
# 乐视网(LeTv) by cmeng
########################################################################
# Version 1.5.2 2015-12-12 (cmeng)
# - Fixed logical errors

# See changelog.txt for previous history
########################################################################

# Plugin constants 
__addonname__ = "乐视网 (LeTV)"
__addonid__ = "plugin.video.letv"
__addon__ = xbmcaddon.Addon(id=__addonid__)
__addonicon__ = os.path.join(__addon__.getAddonInfo('path'), 'icon.png')
__settings__ = xbmcaddon.Addon(id=__addonid__)
__profile__ = xbmc.translatePath(__settings__.getAddonInfo('profile'))
cookieFile = __profile__ + 'cookies.letv'

# # UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
VIDEO_LIST = [['1', '电影', '&o=9'], ['2', '电视剧', '&o=51'], ['5', '动漫', '&o=9'], ['11', '综艺', '&o=9&s=3'], ['3', '明星', '&a=-1']]
UGC_LIST = [['4', '体育', '&o=1'], ['3', '娱乐', '&o=9'], ['9', '音乐', '&o=17'], ['20', '风尚', '&o=1'], ['16', '纪录片', '&o=1'], \
            ['22', '财经', '&o=1'], ['14', '汽车', '&o=1'], ['23', '旅游', '&o=1'], ['34', '亲子', '&o=9'], ['30', '热点', '&o=1']]

SERIES_LIST = ['电视剧', '动漫']
MOVIE_LIST = ['电影', '综艺']
VIDEO_RES = [["标清", 'sd'], ["高清", 'hd'], ["普通", ''], ["未注", "null"]]
COLOR_LIST = ['[COLOR FFFF0000]', '[COLOR FF00FF00]', '[COLOR FFFFFF00]', '[COLOR FF00FFFF]', '[COLOR FFFF00FF]']

FLVCD_PARSER_PHP = 'http://www.flvcd.com/parse.php'
FLVCD_DIY_URL = 'http://www.flvcd.com/diy/diy00'

CFRAGMAX = [10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]

##################################################################################
# LeTv player class
##################################################################################
class LetvPlayer(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self)

    def play(self, name, thumb, v_urls = None):
        self.is_active = True
        self.name = name
        self.thumb = thumb
        
        self.v_urls = v_urls
        if (v_urls):
            self.curpos = 0
        else:
            self.curpos = int(name.split('.')[0]) - 1
            
        self.videoplaycont = __addon__.getSetting('video_vplaycont')
        self.maxfp = CFRAGMAX[int(__addon__.getSetting('video_cfragmentmax'))]
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        self.psize = self.playlist.size()
        self.geturl()
        self.playrun()
    
    def geturl(self):
        ### Video  playback
        if (self.v_urls and (self.curpos <= len(self.v_urls))):
            x = (self.curpos / self.maxfp) % 2
            self.videourl = __profile__ + 'vfile-' + str(x) + '.ts'
            fs = open(self.videourl, 'wb')

            title = "%s - 第(%s~%s)/%s节" % (self.name, str(self.curpos+1), str(self.curpos+self.maxfp), str(len(self.v_urls)))
            self.listitem = xbmcgui.ListItem(title, thumbnailImage=self.thumb)
            self.listitem.setInfo(type="Video", infoLabels={"Title":title})

            endIndex = min((self.curpos + self.maxfp), len(self.v_urls))
            for i in range(self.curpos, endIndex):
                v_url = self.v_urls[i]
                bfile = getHttpData(v_url, True)
                fs.write(bfile)
                if (i == 3) and (not self.isPlayingVideo()):
                    xbmc.Player.play(self, self.videourl, self.listitem)
                elif (i > 4) and (i < (endIndex - 1)) and (not self.isPlayingVideo()):
                    break;
            fs.close()
            self.curpos += self.maxfp

        # ugc auto playback
        elif ((self.v_urls == None) and (self.curpos < self.psize)):
            x = self.curpos % 2
            self.videourl = __profile__ + 'vfile-' + str(x) + '.ts'
            fs = open(self.videourl, 'wb')

            p_item = self.playlist.__getitem__(self.curpos)
            p_url = p_item.getfilename(self.curpos)
            p_list = p_item.getdescription(self.curpos)
            self.listitem = p_item  # pass all li items including the embedded thumb image
            self.listitem.setInfo(type="Video", infoLabels={"Title":p_list})    

            v_urls = decrypt_url(p_url)
            for i, v_url in enumerate(v_urls):
                bfile = getHttpData(v_url, True)
                fs.write(bfile)
                if (i == 3) and (not self.isPlayingVideo()):
                    xbmc.Player.play(self, self.videourl, self.listitem)
                elif (i > 4) and (not self.isPlayingVideo()):
                    break;
            fs.close()
            self.curpos += 1
        else:
            self.videourl = None

    def playrun(self):
        if (not self.isPlayingVideo()):
            # print "### Player resumed !!!"
            xbmc.Player.play(self, self.videourl, self.listitem)
        if self.videoplaycont:
            self.geturl() 
        
    def onPlayBackStarted(self):
        xbmc.Player.onPlayBackStarted(self)

    def onPlayBackSeek(self, time, seekOffset):
        xbmc.Player.onPlayBackSeek(self, time, seekOffset)

    def onPlayBackSeekChapter(self, chapter):
        xbmc.Player.onPlayBackSeek(self, chapter)

    def onPlayBackEnded(self):
        if self.videourl:
            # print "### Player Ended-Continue !!!"
            self.playrun()
        else:
            # print "### Player Ended-Deleted !!!"
            self.is_active = False
            xbmc.Player.onPlayBackEnded(self)
            self.delTsFile()

    def onPlayBackStopped(self):
        # print "### Player Stopped -Deleted!!!"
        self.is_active = False
        self.delTsFile()
        
    def delTsFile(self):
        for k in range(10):
            tsfile = __profile__ + 'vfile-' + str(k) + '.ts'
            if os.path.isfile(tsfile):
                try:
                    os.remove(tsfile)
                except:
                    pass       

xplayer = LetvPlayer()
mplaylist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

##################################################################################
# Routine to fetech url site data using Mozilla browser
# - deletc '\r|\n|\t' for easy re.compile
# - do not delete ' ' i.e. <space> as some url include spaces
# - unicode with 'replace' option to avoid exception on some url
# - translate to utf8
##################################################################################
def getHttpData(url, binary=False):
    print "getHttpData: " + url
    # setup proxy support
    proxy = __addon__.getSetting('http_proxy')
    type = 'http'
    if proxy <> '':
        ptype = re.split(':', proxy)
        if len(ptype) < 3:
            # full path requires by Python 2.4
            proxy = type + '://' + proxy 
        else: type = ptype[0]
        httpProxy = {type: proxy}
    else:
        httpProxy = {}
    proxy_support = urllib2.ProxyHandler(httpProxy)

    # setup cookie support
    cj = cookielib.MozillaCookieJar(cookieFile)
    if os.path.isfile(cookieFile):
        cj.load(ignore_discard=True, ignore_expires=True)
    else:
        if not os.path.isdir(os.path.dirname(cookieFile)):
            os.makedirs(os.path.dirname(cookieFile))
    
    # create opener for both proxy and cookie
    opener = urllib2.build_opener(proxy_support, urllib2.HTTPCookieProcessor(cj))
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    # req.add_header('cookie', 'PHPSESSID=ruebtvftj69ervhpt24n1b86i3')
    
    for k in range(3):  # give 3 trails to fetch url data
        try:
            response = opener.open(req)
        except urllib2.HTTPError, e:
            httpdata = e.read()
        except urllib2.URLError, e:
            httpdata = "IO Timeout Error"
        else:
            httpdata = response.read()
            response.close()
            # Retry if exception: {"exception":{....
            if not "exception" in httpdata:
                cj.save(cookieFile, ignore_discard=True, ignore_expires=True)
                # for cookie in cj:
                #     print('%s --> %s'%(cookie.name,cookie.value))
                break

    if (not binary):
        httpdata = re.sub('\r|\n|\t', '', httpdata)
        match = re.compile('<meta.+?charset=["]*(.+?)"').findall(httpdata)
        if len(match):
            charset = match[0].lower()
            if (charset != 'utf-8') and (charset != 'utf8'):
                httpdata = unicode(httpdata, charset, 'replace').encode('utf-8')
                
    return httpdata

##################################################################################
# Routine to extract url ID from array based on given selected filter
# List = [['1','电影','&o=9'],['2','电视剧','&o=9'] ....
# .......
##################################################################################
def fetchID(dlist, idx):
    for i in range(0, len(dlist)):
        if dlist[i][1] == idx:
            return dlist[i][0]
    return ''

##################################################################################
# Routine to fetch and build video filter list
# Common routine for all categories
##################################################################################
def getListSEL(listpage):
    titlelist = []
    catlist = []
    itemList = []

    # extract categories selection
    match = re.compile('<li>(.+?)</li>').findall(listpage)
    for k, list in enumerate(match):
        title = re.compile('<h2.+?>(.+?)</h2>').findall(list)
        itemLists = re.compile('href="(.+?)"><b.+?>(.+?)</b>').findall(list)
        if (len(itemLists) > 1):
            itemList = [[x[0], x[1].strip()] for x in itemLists]
    
            item1 = itemList[0][0].split('_')
            item2 = itemList[1][0].split('_')
            ilist1 = len(item1)
            ilist2 = len(item2)
            
            # get the index of the current item variables 
            for j in range(ilist2):
                if not (item2[j] in item1):
                    break
            
            icnt = len(itemList)
                            # no filter for first item selection i.e. "全部"
            for i in range (icnt):
                if (i == 0) and (ilist1 < ilist2):
                    itemList[i][0] = ''
                else:
                    itemx = itemList[i][0].split('_')
                    itemList[i][0] = itemx[j]
        
            titlelist.append(title[0])
            catlist.append(itemList)

    # extract order selection if any
    title = re.compile('<span>(.+?)</span>').findall(listpage)
    if len(title):
        titlelist.append(title[0])
        match = re.compile('<lo>(.+?)</lo>').findall(listpage)
        itemLists = re.compile('data-order="(.+?)".+?>(.+?)</a>').findall(listpage)
        itemList = [[x[0], x[1].strip()] for x in itemLists]

    catlist.append(itemList)
    return titlelist, catlist   

##################################################################################
# Routine to update video list as per user selected filtrs
##################################################################################
def updateListSEL(name, url, cat, filtrs, page, listpage):
    dialog = xbmcgui.Dialog()
    titlelist, catlist = getListSEL(listpage)
    fltr = filtrs[1:].replace('=', '').split('&')

    cat = ''
    selection = ''
    for icat, title in enumerate(titlelist):
        fltrList = [x[0] for x in catlist[icat]]
        list = [x[1] for x in catlist[icat]]
        sel = -1
        if (page):  # 0: auto extract cat only
            sel = dialog.select(title, list)
        if sel == -1:
            # return last choice selected if ESC by user
            if len(fltr) == len(titlelist):
                sel = fltrList.index(fltr[icat])
            else:  # default for first time entry
                sel = 0
        selx = catlist[icat][sel][0]
        ctype = catlist[icat][sel][1]
        if (ctype == '全部'):
            ctype += title[1:]
        # filtrs.append([catlist[icat][sel][0], catlist[icat][sel][1]])
        cat += COLOR_LIST[icat % 5] + ctype + '[/COLOR]|'
        selcat = re.compile('([a-z]+)').findall(selx)[0]
        catlen = len(selcat)
        if (selx != ''):  # no need to add blank filter
            selection += '&' + selcat + '=' + selx[catlen:]
    filtrs = selection
    cat = cat[:-1]
    
    if (not page): return(cat)
    elif (name == '电影' or name == '电视剧' or name == '动漫' or name == '综艺'):
        progListMovie(name, url, cat, filtrs, page , listpage)
    elif (name == '明星'):
        progListStar(name, url, cat, filtrs, page , listpage)
    else:
        progListUgc(name, url, cat, filtrs, page , listpage)        

##################################################################################
# Routine to generate 'pages' list for selection
# Based on 30 items per page and total items count p_itemCount
# Pages exclude current selected page
##################################################################################
def getPages(p_itemCount, page):
    c_pageNum = int(page)
    p_pageSize = 30
    p_pageTotal = ((p_itemCount + p_pageSize - 1) / p_pageSize) + 1
    p_pageMid = int(p_pageTotal / 2)
    
    if (c_pageNum <= p_pageMid):
        p_pageEnd = min(8, p_pageTotal)
        pages = range(1, p_pageEnd)
        p_pageFromEnd = max((p_pageTotal - 2), (p_pageEnd + 1))
    else:
        pages = range(2)
        p_pageFromEnd = max((p_pageTotal - 8), 2)
        
    for x in range(p_pageFromEnd, p_pageTotal):
        pages.append(x)
        
    if c_pageNum in pages:
        pages.remove(c_pageNum)
    
    return pages 

##################################################################################
# Routine to fetch & build LeTV 网络电视 main menu
# - video list as per [VIDEO_LIST]
# - ugc list as per [UGC_LIST]
# - movie, series, star & ugc require different sub-menu access methods
##################################################################################
def mainMenu():
    li = xbmcgui.ListItem('[COLOR F0F0F0F0] LeTV 乐视网 - 搜索:[/COLOR][COLOR FF00FF00]【点此进入】[/COLOR]')
    u = sys.argv[0] + "?mode=31"
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
     
    link = getHttpData('http://list.letv.com/listn/c1_t-1_a-1_y-1_s1_lg-1_ph-1_md_o9_d1_p.html')
    match = re.compile('<div class="channel_list.+?">(.+?)</div>').findall(link)[0]
    ugclist = re.compile('href="(.+?)".*?>(.+?)</a>').findall(match)
    
    totalItems = len(ugclist)
    listpage = ""
    cat = "全部"
    p_url = 'http://list.letv.com'
    i = 0

    # fetch the url from ugclist for video channels, for those in VIDEO_LIST
    for x_url, name in ugclist:
        for catx, namex, filtrs in VIDEO_LIST: 
            if (name == namex):
                i = i + 1
                if name == '明星':
                    mode = '4'
                else:
                    mode = '1'
                url = p_url + x_url

                ilist = "[COLOR FF00FFFF]%s. %s[/COLOR]" % (i, name)
                li = xbmcgui.ListItem(ilist)
                u = sys.argv[0] + "?mode=" + mode + "&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&cat=" + urllib.quote_plus(cat) + "&filtrs=" + urllib.quote_plus(filtrs) + "&page=1" + "&listpage=" + listpage
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    
    # fetch the url from ugclist for ugc channels, for those in UGC_LIST
    for x_url, name in ugclist:
        for catx, namex, filtrs in UGC_LIST: 
            if (name == namex):
                i = i + 1
                url = p_url + x_url
                ilist = "[COLOR FF00FFFF]%s. %s[/COLOR]" % (i, name)
                li = xbmcgui.ListItem(ilist)
                u = sys.argv[0] + "?mode=8" + "&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&cat=" + urllib.quote_plus(cat) + "&filtrs=" + urllib.quote_plus(filtrs) + "&page=1" + "&listpage=" + listpage
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))  

##################################################################################
# Routine to fetch and build the video selection menu
# - selected page & filters (user selectable)
# - video items list
# - user selectable pages
# http://list.letv.com/apin/chandata.json?c=1&d=1&md=&o=9&p=3&s=1
##################################################################################
def progListMovie(name, url, cat, filtrs, page, listpage):
    fltrCategory = fetchID(VIDEO_LIST, name)
    if page == None: page = '1'
    p_url = "http://list.letv.com/apin/chandata.json?c=%s&d=2&md=&p=%s%s"
    
    if (listpage == None):
        link = getHttpData(url)
        listpage = re.compile('<ul class="label_list.+?>(.+?)</ul>').findall(link)[0]
        match = re.compile('<div class="sort_navy.+?">(.+?)</div>').findall(link)
        if len(match):
            listpage += match[0].replace('li', 'lo')
        cat = updateListSEL(name, url, cat, filtrs, 0, listpage)    
    p_url = p_url % (fltrCategory, page, filtrs)
    
    # Fetch & build video titles list for user selection, highlight user selected filtrs  
    li = xbmcgui.ListItem(name + '（第' + str(page) + '页）【' + cat + '】（按此选择)')
    u = sys.argv[0] + "?mode=9&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&cat=" + urllib.quote_plus(cat) + "&filtrs=" + urllib.quote_plus(filtrs) + "&page=1" + "&listpage=" + urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    link = getHttpData(p_url)
    if link == None: return
    
    # Movie, Video, Series, Variety & Music titles need different routines
    if (name in SERIES_LIST):
        isDir = True
        mode = '2'
    elif (name in MOVIE_LIST):
        isDir = False
        mode = '10'

    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['album_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        p_name = vlist[i]['name'].encode('utf-8')
        # get series listing of the video
        if (name in SERIES_LIST):
            aid = str(vlist[i]['aid'])
            if (name == '电视剧'): v_url = 'http://www.letv.com/tv/%s.html' % aid
            else: v_url = 'http://www.letv.com/comic/%s.html' % aid
        # get first video link for direct play back
        else:
            vid = str(vlist[i]['vids'].split(',')[0])
            v_url = 'http://www.letv.com/ptv/vplay/%s.html' % vid

        try: 
            p_thumb = vlist[i]['images']['150*200']
        except KeyError:
            p_thumb = vlist[i]['images']['160*120']
        except: p_thumb = ''

        p_title = p_name
        p_list = str(i + 1) + '. ' + p_title + ' '

        try:  # Extract rating information
            p_rating = float(vlist[i]['rating'])
            if (p_rating != None and p_rating > 0.01):
                p_rating = "%0.1f" % p_rating
                p_list += '[COLOR FFFF00FF][' + p_rating + '][/COLOR]'
        except:
            pass
        
        try:  # get language + area information
            p_lang = ''
            if (name in MOVIE_LIST):
                p_lang = vlist[i]['lgName'] + '-'
            p_area = vlist[i]['areaName']
            p_list += '[COLOR FF00FFFF][' + (p_lang + p_area).encode('utf-8') + '][/COLOR]'
        except:
            pass

        p_sdx = vlist[i]['duration']
        if ((p_sdx != None) and (len(p_sdx) > 0) and (int(p_sdx) > 0)):
            p_dx = int(p_sdx)
            p_duration = "[%02d:%02d]" % (int(p_dx / 60), (p_dx % 60))
            p_list += '[COLOR FFFFFF00]' + p_duration + '[/COLOR]'
            
        p_artists = vlist[i]['starring']
        if ((p_artists != None) and len(p_artists)):
            p_artist = ""
            p_list += '['
            for key in p_artists:
                p_artist += p_artists[key].encode('utf-8') + ' '
            p_list += p_artist[:-1] + ']'            
        else:
            p_subcategory = vlist[i]['subCategoryName']
            if ((p_subcategory != None)):
                p_list += '[' + p_subcategory.encode('utf-8') + ']'

        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        # li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_artist})
        u = sys.argv[0] + "?mode=" + mode + "&name=" + urllib.quote_plus(p_name) + "&url=" + urllib.quote_plus(v_url) + "&thumb=" + urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isDir, totalItems)
        
    p_itemCount = content['album_count']
    pages = getPages(p_itemCount, page)

    for page in pages:
        li = xbmcgui.ListItem("... 第" + str(page) + "页")
        u = sys.argv[0] + "?mode=1" + "&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&cat=" + urllib.quote_plus(cat) + "&filtrs=" + urllib.quote_plus(filtrs) + "&page=" + str(page) + "&listpage=" + urllib.quote_plus(listpage)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    

##################################################################################
# Routine to fetch and build the video series selection menu
# - for 电视剧  & 动漫
# - selected page & filters (user selectable)
# - Video series list
# - user selectable pages
##################################################################################
def progListSeries(name, url, thumb):
    link = getHttpData(url)
    match = re.compile('<i class="i-t">(.+?)</i>').findall(link)
    episodes = ''
    if match: 
        episodes = ' (' + ' '.join(match[0].split()) + ')'
    
    li = xbmcgui.ListItem('【[COLOR FFFFFF00]' + name + '[/COLOR]' + episodes + ' | [COLOR FF00FFFF][选择: ' + name + '][/COLOR]】', iconImage='', thumbnailImage=thumb)
    u = sys.argv[0] + "?mode=2&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) 
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    # fetch and build the video series list
    match = re.compile('<div.+?data-tabct="j-tab[1-9]+_child".+?statectn="n_list[1-9]+">(.+?)</div>').findall(link)
    # special handling for '动漫'
    if match is None:
        match = re.compile('<div.+?data-tabct="j-tab[1-9]+_child"(.+?)</div>').findall(link)
    else:
        matchp = re.compile('<dl class="w96">(.+?)</dl>').findall(match[0])
        if len(matchp):  # not the right one, so re-fetch             
            match = re.compile('<div.+?data-tabct="j-tab[1-9]+_child"(.+?)</div>').findall(link)
     
    for j in range(0, len(match)):
        matchp = re.compile('<dl class="w120">(.+?)</dl>').findall(match[j])              
        totalItems = len(matchp)
        for i in range(0, len(matchp)):
            match1 = re.compile('<img.+?src="(.+?)"').findall(matchp[i])
            p_thumb = match1[0]
            match1 = re.compile('<p class="p1">.+?href="(.+?)"[\s]*title="(.+?)".+?>(.+?)</a>').findall(matchp[i])
            p_url = match1[0][0]
            p_name = match1[0][1]
            sn = match1[0][2]
            p_list = sn + ': ' + p_name
            
            match1 = re.compile('class="time">(.+?)</span>').findall(matchp[i])
            if match1:
                p_list += ' [COLOR FFFFFF00][ ' + match1[0].strip() + ' ][/COLOR]'

            li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
            u = sys.argv[0] + "?mode=10&name=" + urllib.quote_plus(p_name) + "&url=" + urllib.quote_plus(p_url)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)

    xbmcplugin.setContent(int(sys.argv[1]), 'movie')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Routine to display Singer list for selection
# - for 明星
# - selected page & filtrs
# - Video series list
# - user selectable pages 
##################################################################################
def progListStar(name, url, cat, filtrs, page, listpage):
    fltrCategory = fetchID(VIDEO_LIST, name)
    if page == None: page = '1'
    p_url = "http://list.letv.com/apin/stardata.json?d=%s&p=%s%s"
    
    if (listpage == None):
        link = getHttpData(url)
        listpage = re.compile('<ul class="label_list.+?>(.+?)</ul>').findall(link)[0]
        match = re.compile('<div class="sort_navy.+?">(.+?)</div>').findall(link)
        if len(match):
            listpage += match[0].replace('li', 'lo')
        cat = updateListSEL(name, url, cat, filtrs, 0, listpage)    
    p_url = p_url % (fltrCategory, page, filtrs)    
    
    # Fetch & build video titles list for user selection, highlight user selected filter  
    li = xbmcgui.ListItem(name + '（第' + str(page) + '页）【' + cat + '】（按此选择)')
    u = sys.argv[0] + "?mode=9&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&cat=" + urllib.quote_plus(cat) + "&filtrs=" + urllib.quote_plus(filtrs) + "&page=1" + "&listpage=" + urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    link = getHttpData(p_url)
    if link == None: return
 
    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['star_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        p_name = vlist[i]['name'].encode('utf-8')
        # v_url = 'http://so.letv.com/star?wd=%s&from=list' % p_name
        v_url = 'http://so.letv.com/s?wd=%s' % p_name
        p_thumb = vlist[i]['postS1']
        p_list = str(i + 1) + '. [COLOR FF00FF00]' + p_name + '[/COLOR] '
           
        match = vlist[i]['professional']
        p_prof = re.compile('":"(.+?)"').findall(match)
        if ((p_prof != None) and len(p_prof)):
            p_list += '[COLOR FF00FFFF]['
            for prof in p_prof:
                p_list += prof.encode('utf-8') + ' '
            p_list = p_list[:-1] + '][/COLOR] '

        p_area = vlist[i]['areaName']
        if (p_area != None):
            p_list += '[COLOR FFFFFF00][' + p_area.encode('utf-8') + '][/COLOR] '

        p_birthday = vlist[i]['birthday']
        if (p_birthday != None and len(p_birthday)):
            p_list += '[COLOR FFFF00FF][' + p_birthday.encode('utf-8') + '][/COLOR]'

        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        # li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_name})
        u = sys.argv[0] + "?mode=5" + "&name=" + urllib.quote_plus(p_name) + "&url=" + urllib.quote_plus(v_url) + "&thumb=" + urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
        
    p_itemCount = content['star_count']
    pages = getPages(p_itemCount, page)

    for page in pages:
        li = xbmcgui.ListItem("... 第" + str(page) + "页")
        u = sys.argv[0] + "?mode=4" + "&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&cat=" + urllib.quote_plus(cat) + "&filtrs=" + urllib.quote_plus(filtrs) + "&page=" + str(page) + "&listpage=" + urllib.quote_plus(listpage)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    
          
##################################################################################
# Routine to extract video series selection menu for user playback
# - for 明星
# filtrs: movie cg=1; series cg=2; pn=pageNumber; ps=pageSize
# p_url = 'http://open.api.letv.com/ms?hl=1&dt=2&ph=420001&from=pcjs
# p_url += '&cg=1&pn=%s&ps=30&wd=%s&_=1391387253932' % (page, name)
##################################################################################
def progListStarVideo(name, url, page, thumb):
    if (page == None): page = '1' 
    p_url = 'http://open.api.letv.com/ms?hl=1&dt=2&pn=%s&ps=30&wd=%s' % (page, name)

    li = xbmcgui.ListItem('【[COLOR FF00FFFF][' + name + '][/COLOR] | [COLOR FFFFFF00]（第' + page + '页）[/COLOR]】', iconImage='', thumbnailImage=thumb)
    u = sys.argv[0] + "?mode=5&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) 
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
   
    link = getHttpData(p_url)
    if link == None: return
    
    # mplaylist = xbmc.PlayList(0)  # use Music playlist for temporary storage
    mplaylist.clear()
     
    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['data_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        p_title = vlist[i]['name'].encode('utf-8')
        
        # aid = str(vlist[i]['aid'])
        vid = str(vlist[i]['vid'])
        v_url = 'http://www.letv.com/ptv/vplay/%s.html' % vid
        
        try: 
            p_thumb = vlist[i]['images']['150*200']
        except KeyError:
            p_thumb = vlist[i]['images']['160*120']
        except: p_thumb = ''
        
        p_name = p_list = str(i + 1) + '. ' + p_title + ' '
        p_category = vlist[i]['categoryName']
        if ((p_category != None) and len(p_category)):
            p_subcategory = '-' + vlist[i]['subCategoryName']
            p_list += '[COLOR FF00FFFF][' + (p_category + p_subcategory).encode('utf-8') + '][/COLOR] '
        
        try:
            p_rating = float(vlist[i]['rating'])
            if (p_rating != None and p_rating > 0.01):
                p_rating = "%0.1f" % p_rating
                p_list += '[COLOR FFFF00FF][' + p_rating + '][/COLOR]'
        except:
            pass

        p_dx = int(vlist[i]['duration'])
        if ((p_dx != None) and (p_dx > 0)):
            p_duration = "[%02d:%02d]" % (int(p_dx / 60), (p_dx % 60))
            p_list += '[COLOR FFFFFF00]' + p_duration + '[/COLOR]'

        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        # li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_name})
        u = sys.argv[0] + "?mode=10" + "&name=" + urllib.quote_plus(p_name) + "&url=" + urllib.quote_plus(v_url) + "&thumb=" + urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
        mplaylist.add(v_url, li)
        
    # Fetch and build page selection menu
    p_itemCount = content['data_count']
    pages = getPages(p_itemCount, page)

    for page in pages:
        li = xbmcgui.ListItem("... 第" + str(page) + "页")
        u = sys.argv[0] + "?mode=5" + "&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&page=" + str(page) + "&thumb=" + urllib.quote_plus(thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    
    
##################################################################################
# Routine to fetch and build the ugc selection menu
# - for categories not in VIDEO_LIST
# - selected page & filtrs (user selectable)
# - ugc items list
# - user selectable pages
# http://list.letv.com/apin/chandata.json?a=50006&c=3&d=2&md=&o=9&p=2&vt=440141
##################################################################################
def progListUgc(name, url, cat, filtrs, page, listpage):
    fltrCategory = fetchID(UGC_LIST, name)
    if page == None: page = '1'
    p_url = "http://list.letv.com/apin/chandata.json?c=%s&d=2&md=&p=%s%s"
    
    if (listpage == None):
        link = getHttpData(url)
        listpage = re.compile('<ul class="label_list.+?>(.+?)</ul>').findall(link)[0]
        listpage += re.compile('<div class="sort_navy.+?">(.+?)</div>').findall(link)[0].replace('li', 'lo')
        cat = updateListSEL(name, url, cat, filtrs, 0, listpage)    
    p_url = p_url % (fltrCategory, page, filtrs)    
    
    # Fetch & build video titles list for user selection, highlight user selected filter  
    li = xbmcgui.ListItem(name + '（第' + str(page) + '页）【' + cat + '】（按此选择)')
    u = sys.argv[0] + "?mode=9&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&cat=" + urllib.quote_plus(cat) + "&filtrs=" + urllib.quote_plus(filtrs) + "&page=1" + "&listpage=" + urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    link = getHttpData(p_url)
    if link == None: return

    # mplaylist = xbmc.PlayList(0)  # use Music playlist for temporary storage
    mplaylist.clear()

    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['data_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        vid = str(vlist[i]['vid'])
        v_url = 'http://www.letv.com/ptv/vplay/%s.html' % vid
        p_title = vlist[i]['name'].encode('utf-8')

        try: 
            p_thumb = vlist[i]['images']['150*200']
        except KeyError:
            p_thumb = vlist[i]['images']['160*120']
        except: pass
            
        p_list = p_name = str(i + 1) + '. ' + p_title + ' '
        p_artist = vlist[i]['actor']
        if ((p_artist != None) and len(p_artist)):
            p_list += '[COLOR FFFF00FF]['
            for actor in p_artist:
                p_list += actor.encode('utf-8') + ' '
            p_list = p_list[:-1] + '][/COLOR]'

        p_dx = int(vlist[i]['duration'])
        if (p_dx != None):
            p_duration = "[%02d:%02d]" % (int(p_dx / 60), (p_dx % 60))
            p_list += '[COLOR FFFFFF00]' + p_duration + '[/COLOR]'

        p_album = vlist[i]['albumName']
        if (p_album != None):
            p_album = p_album.encode('utf-8') 
            p_list += '[COLOR FF00FFFF][' + p_album + '][/COLOR]'
       
        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        # li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_artist})
        u = sys.argv[0] + "?mode=20" + "&name=" + urllib.quote_plus(p_list) + "&url=" + urllib.quote_plus(v_url) + "&thumb=" + urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
        mplaylist.add(v_url, li)
        
    # Fetch and build page selection menu
    p_itemCount = content['data_count']
    pages = getPages(p_itemCount, page)

    for page in pages:
        li = xbmcgui.ListItem("... 第" + str(page) + "页")
        u = sys.argv[0] + "?mode=8" + "&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&cat=" + urllib.quote_plus(cat) + "&filtrs=" + urllib.quote_plus(filtrs) + "&page=" + str(page) + "&listpage=" + urllib.quote_plus(listpage)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    
    
#################################################################################
# Get user input for LeTV site 
# http://open.api.letv.com/ms?hl=1&dt=2&ph=420001&from=pcjs&pn=1&ps=25&wd=%E7%88%B1%E4%BA%BA&_=1392364710043 
##################################################################################
def searchLetv():
    result = ''
    
    keyboard = Apps('', '请输入搜索内容')
    # keyboard.setHiddenInput(hidden)
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        letvSearchList(keyword, '1')
    else: return
        
##################################################################################
# Routine to search LeTV site based on user given keyword for:
##################################################################################
def letvSearchList(name, page):
    p_url = 'http://open.api.letv.com/ms?hl=1&dt=2&ph=420001&from=pcjs&pn=%s&ps=30&wd=%s'
    p_url = p_url % (page, urllib.quote(name))
    link = getHttpData(p_url)
    
    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索: 第' + page + '页[/COLOR][COLOR FFFFFF00] (' + name + ')[/COLOR]【[COLOR FF00FF00]' + '点此输入新搜索内容' + '[/COLOR]】')
    u = sys.argv[0] + "?mode=31&name=" + urllib.quote_plus(name) + "&page=" + page
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    if link == None:
        li = xbmcgui.ListItem('  抱歉，没有找到[COLOR FFFF0000] ' + name + ' [/COLOR]的相关视频')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return
    
    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['data_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        vid = str(vlist[i]['vid'])
        v_url = 'http://www.letv.com/ptv/vplay/%s.html' % vid
        p_title = vlist[i]['name'].encode('utf-8')

        try: 
            p_thumb = vlist[i]['images']['150*200']
        except KeyError:
            p_thumb = vlist[i]['images']['160*120']
        except: pass
            
        p_categoryName = vlist[i]['categoryName']
        if (p_categoryName != None):
            p_list = p_name = str(i + 1) + '. [COLOR FF00FFFF][' + p_categoryName.encode('utf-8') + '][/COLOR] ' + p_title + ' '
        else:
            p_list = p_name = str(i + 1) + '. ' + p_title + ' '
            
        try:
            p_rating = float(vlist[i]['rating'])
            if (p_rating != None and p_rating > 0.01):
                p_rating = "%0.1f" % p_rating
                p_list += '[COLOR FFFF00FF][' + p_rating + '][/COLOR]'
        except:
            pass            
        
        p_dx = int(vlist[i]['duration'])
        if (p_dx != None):
            p_duration = "[%02d:%02d]" % (int(p_dx / 60), (p_dx % 60))
            p_list += '[COLOR FFFFFF00]' + p_duration + '[/COLOR]'

        p_artists = vlist[i]['actor']
        if ((p_artists != None) and len(p_artists)):
            p_artist = ""
            p_list += '['
            for key in p_artists:
                p_artist += p_artists[key].encode('utf-8') + ' '
            p_list += p_artist[:-1] + ']'

        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0] + "?mode=10" + "&name=" + urllib.quote_plus(p_list) + "&url=" + urllib.quote_plus(v_url) + "&thumb=" + urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
        
    # Fetch and build page selection menu
    p_itemCount = content['video_count']
    pages = getPages(p_itemCount, page)

    for page in pages:
        li = xbmcgui.ListItem("... 第" + str(page) + "页")
        u = sys.argv[0] + "?mode=32" + "&name=" + urllib.quote_plus(name) + "&page=" + str(page)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))       

##################################################################################
# LeTV Video Link Decode Algorithm
# Extract all the video list and start playing first found valid link
# http://www.letv.com/ptv/vplay/1967644.html
##################################################################################
def calcTimeKey(t):
    ror = lambda val, r_bits, : ((val & (2 ** 32 - 1)) >> r_bits % 32) | (val << (32 - (r_bits % 32)) & (2 ** 32 - 1))
    return ror(ror(t, 773625421 % 13) ^ 773625421, 773625421 % 17)

# # --- decrypt m3u8 data --------- ##
def decode(data):
    version = data[0:5]
    if version.lower() == b'vc_01':
        # get real m3u8
        loc2 = bytearray(data[5:])
        length = len(loc2)
        loc4 = [0] * (2 * length)
        for i in range(length):
            loc4[2 * i] = loc2[i] >> 4
            loc4[2 * i + 1] = loc2[i] & 15;
        loc6 = loc4[len(loc4) - 11:] + loc4[:len(loc4) - 11]
        loc7 = [0] * length
        for i in range(length):
            loc7[i] = (loc6[2 * i] << 4) + loc6[2 * i + 1]
        return ''.join([chr(i) for i in loc7])
    else:
        # directly return
        return data

# # ------ video links decryptio ---------------------- ##
def decrypt_url(url):
    videoRes = int(__addon__.getSetting('video_resolution'))
    vparamap = {0:'1300', 1:'720p', 2:'1080p'}
    
    t_url = 'http://api.letv.com/mms/out/video/playJson?id={}&platid=1&splatid=101&format=1&tkey={}&domain=www.letv.com'
    t_url2 = '&ctv=pc&m3v=1&termid=1&format=1&hwtype=un&ostype=Linux&tag=letv&sign=letv&expect=3&tn={}&pay=0&iscpn=f9051&rateid={}'

    try:
        vid = re.compile('/vplay/(\d+).html').findall(url)[0]
        j_url = t_url.format(vid, calcTimeKey(int(time.time())))
        link = getHttpData(j_url)
        info = simplejson.loads(link)
        playurl = info['playurl']
    except:
        return ''

    stream_id = None
    support_stream_id = info["playurl"]["dispatch"].keys()
#     print("Current Video Supports:")
#     for i in support_stream_id:
#         print("\t--format",i,"<URL>")
    if "1080p" in support_stream_id:
        stream_id = '1080p'
    elif "720p" in support_stream_id:
        stream_id = '720p'
    else:
        stream_id = sorted(support_stream_id, key=lambda i: int(i[1:]))[-1]
        
    domain = playurl['domain'][0]
    vodRes = playurl['dispatch']
    vod = None
    while ((vod == None) and (videoRes >= 0)):
        vRes = vparamap.get(videoRes, 0)
        try:
            vod = vodRes.get(vRes)[0]
        except: pass
        videoRes -= 1
    if vod == None:
        try:
            vod = playurl['dispatch']['1000'][0]
        except KeyError:
            vod = playurl['dispatch']['350'][0]
        except:
            return ''

    url = domain + vod
    url += t_url2.format(random.random(), vRes)
    ext = vodRes[stream_id][1].split('.')[-1]

    r2 = getHttpData(url)
    # try:
    info2 = simplejson.loads(r2)

    # need to decrypt m3u8 (encoded)
    m3u8 = getHttpData(info2["location"])
    m3u8_list = decode(m3u8)
	# urls contains array of v_url video links for playback
    urls = re.findall(r'^[^#][^\r]*', m3u8_list, re.MULTILINE)
    return urls   
    
    # except:
        # if '解析失败' in link:
    #    return ''

##################################################################################
def playVideoLetv(name, url, thumb):
    dialog = xbmcgui.Dialog()
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
    
    v_urls = decrypt_url(url)
    pDialog.close()

    vLen = len(v_urls)
    if len(v_urls):
        xplayer.play(name, thumb, v_urls)
        while xplayer.is_active:
            xbmc.sleep(100)
    else:
        # if '解析失败' in link: (license constraint etc)
    	dialog.ok(__addonname__, '无法播放：未匹配到视频文件，请选择其它视频')
   
##################################################################################
# Continuous Player start playback from user selected video
# User backspace to previous menu will not work - playlist = last selected
##################################################################################
def playVideoUgc(name, url, thumb):
    videoplaycont = __addon__.getSetting('video_vplaycont')
    
    dialog = xbmcgui.Dialog()
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')

    # check selected url and abort if failed and single time playback
    try:
        v_urls = decrypt_url(url)
    except:
        pass
    pDialog.close()
    if len(v_urls):
        xplayer.play(name, thumb)
        while xplayer.is_active:
            xbmc.sleep(100)
    else:
        # if '解析失败' in link:
        dialog.ok(__addonname__, '无法播放：未匹配到视频文件，请选择其它视频')

##################################################################################    
# Routine to extra video link using flvcd - not use (url link fetech problem)
##################################################################################
def playVideoLetvx(name, url, thumb):
    videoRes = int(__addon__.getSetting('video_resolution'))
    vparamap = {0:'normal', 1:'high', 2:'super'}
    
    dialog = xbmcgui.Dialog()
    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
    
    # p_url = "http://www.flvcd.com/parse.php?kw="+url+"&format="+str(videoRes)
    p_url = "http://www.flvcd.com/parse.php?kw=" + url + "&format=" + vparamap.get(videoRes, 0)
    for i in range(5):  # Retry specified trials before giving up (seen 9 trials max)
        if (pDialog.iscanceled()):
            pDialog.close() 
            return
        pDialog.update(20 * i)

        try:  # stop xbmc from throwing error to prematurely terminate video search
            link = getHttpData(p_url)
            if '加密视频' in link:
                ok = dialog.ok(__addonname__, '无法播放：该视频为加密视频')
                return
            elif '付费视频' in link:
                ok = dialog.ok(__addonname__, '无法播放：该视频为付费视频')
                return
            else:
                match = re.compile('下载地址：\s*<a href="(.+?)" target="_blank" class="link"').findall(link)
                if not len(match):
                    match = flvcd(link)
                break
        except:
           pass   
    
    if len(match):
        pDialog.close() 
        playlist = xbmc.PlayList(1)
        playlist.clear()
        for i in range(0, len(match)):
            # print "video link: " + match[i]
            listitem = xbmcgui.ListItem(name, thumbnailImage=__addonicon__)
            listitem.setInfo(type="Video", infoLabels={"Title":name + " 第" + str(i + 1) + "/" + str(len(match)) + " 节"})
            playlist.add(match[i], listitem)
        xbmc.Player().play(playlist)
    else:
        # if '解析失败' in link:
        pDialog.close() 
        ok = dialog.ok(__addonname__, '无法播放：多次未匹配到视频文件，请选择其它视频')

def flvcd(urlData):
    flvDnLink = "http://wwwa.flvcd.com/downparse.php?t=%s&name=%s&url=%s&tsn=%s&msKey=%s&passport=%s"

    # get hidden values in form
    mform = re.compile('<form name="mform" action="(.+?)"(.+?)</form>').findall(urlData)
    attrs = re.compile('<input type="hidden" name="(.+?)" value="(.*?)">').findall(mform[0][1])
    
    if not len(mform):
        return ""
    
    flvDn = mform[0][0] + "?"
    for attr in attrs:
        flvDn += attr[0] + "=" + attr[1] + "&" 
    
    data = getHttpData(flvDn[:-1])
    flvcd_id = re.compile('xdown\.php\?id=(\d+)').findall(data)
    if len(flvcd_id) <= 0:
        return []

    data = getHttpData(FLVCD_DIY_URL + flvcd_id[0] + '.htm')
    p_url = re.compile('<U>(.+?)<C>').findall(data)
    if len(p_url) <= 0:
        return ""
    else:
        link = getHttpData(p_url[0])
        link = link.replace("\/", "/")
        match = re.compile('{.+?"location": "(.+?)" }').findall(link)
        return match        

##################################################################################
def playVideoUgcx(name, url, thumb):
    videoRes = int(__addon__.getSetting('video_resolution'))
    videoplaycont = __addon__.getSetting('video_vplaycont')

    playlistA = xbmc.PlayList(0)
    playlist = xbmc.PlayList(1)
    playlist.clear()

    v_pos = int(name.split('.')[0]) - 1
    psize = playlistA.size()
    ERR_MAX = 10
    errcnt = 0
    k = 0
    
    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
    
    for x in range(psize):
        # abort if ERR_MAX or more access failures and no video playback
        if (errcnt >= ERR_MAX and k == 0):
            pDialog.close() 
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '无法播放：多次未匹配到视频文件，请选择其它视频')
            break 
        
        if x < v_pos: continue
        p_item = playlistA.__getitem__(x)
        p_url = p_item.getfilename(x)
        p_list = p_item.getdescription(x)

        # li = xbmcgui.ListItem(p_list, iconImage = '', thumbnailImage = thumb)
        li = xbmcgui.ListItem(p_list)
        li.setInfo(type="Video", infoLabels={"Title":p_list})  
        
        if re.search('http://www.letv.com/', p_url):  # fresh search
            f_url = "http://www.flvcd.com/parse.php?kw=" + p_url + "&format=" + str(videoRes)
            for i in range(5):  # Retry specified trials before giving up (seen 9 trials max)
                if (pDialog.iscanceled()):
                    pDialog.close() 
                    x = psize  # terminate any old thread
                    return
                pDialog.update(errcnt * 100 / ERR_MAX + 100 / ERR_MAX / 5 * i)
                try:  # stop xbmc from throwing error to prematurely terminate video search
                    link = getHttpData(f_url)
                    v_url = ''
                    if '加密视频' in link: break
                    elif '付费视频' in link: break
                    elif '解析失败' in link: break
                    # print "skip:", re.compile('(提示.+?)</td>').findall(link)[0]
                    
                    v_url = re.compile('下载地址：\s*<a href="(.+?)" target="_blank" class="link"').findall(link)
                    # v_url=re.compile('location:\s*<a href="(.+?)" target="_blank" class="link"').findall(link)
                    if len(v_url):
                        v_url = v_url[0]
                        break
                    else:
                        print "flvcd link error: " + f_url
                except:
                    pass

            if not len(v_url):
                errcnt += 1  # increment consequetive unsuccessful access
                continue
            err_cnt = 0  # reset error count
            playlistA.remove(p_url)  # remove old url
            playlistA.add(v_url, li, x)  # keep a copy of v_url in Audio Playlist
        else:
            v_url = p_url
            
        playlist.add(v_url, li, k)
        k += 1
        if k == 1:
            pDialog.close() 
            xbmc.Player(1).play(playlist)
        if videoplaycont == 'false': break
           
##################################################################################    
# Routine to extra parameters from xbmc
##################################################################################
def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

params = get_params()
url = None
name = None
id = None
page = '1'
cat = None
filtrs = None
thumb = None
listpage = None
mode = None

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    id = urllib.unquote_plus(params["id"])
except:
    pass
try:
    page = urllib.unquote_plus(params["page"])
except:
    pass
try:
    cat = urllib.unquote_plus(params["cat"])
except:
    pass
try:
    filtrs = urllib.unquote_plus(params["filtrs"])
except:
    pass
try:
    thumb = urllib.unquote_plus(params["thumb"])
except:
    thumb = ' '
    pass
try:
    listpage = urllib.unquote_plus(params["listpage"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass

if mode == None:
    mainMenu()
elif mode == 1:
    progListMovie(name, url, cat, filtrs, page, listpage)
elif mode == 2:
    progListSeries(name, url, thumb)
elif mode == 4:
    progListStar(name, url, cat, filtrs, page, listpage)
elif mode == 5:
    progListStarVideo(name, url, page, thumb)
elif mode == 8:
    progListUgc(name, url, cat, filtrs, page, listpage)

elif mode == 9:
    updateListSEL(name, url, cat, filtrs, page, listpage)
elif mode == 10:
    playVideoLetv(name, url, thumb)
    # # playVideo(name,url,thumb)
elif mode == 12:
    playVideoLetv(name, url, thumb)
elif mode == 20:
    playVideoUgc(name, url, thumb)

elif mode == 31:
    searchLetv()
elif mode == 32:
    letvSearchList(name, page)
