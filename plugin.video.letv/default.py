# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, string, sys, os, gzip, StringIO
import math, os.path, httplib, time
import cookielib

try:
    from ChineseKeyboard import Keyboard as Apps
except:
    from xbmc import Keyboard as Apps

try:
    import simplejson
except ImportError:
    import json as simplejson

########################################################################
# 乐视网(LeTv) by cmeng
########################################################################
# Version 1.3.8 2014-12-06 (cmeng)
# - Change settings for dual languages support
# - Retry if "Exception" in json data fetch

# See changelog.txt for previous history
########################################################################

# Plugin constants 
__addonname__   = "乐视网 (LeTV)"
__addonid__     = "plugin.video.letv"
__addon__ = xbmcaddon.Addon(id=__addonid__)
__addonicon__   = os.path.join( __addon__.getAddonInfo('path'), 'icon.png' )
__settings__    = xbmcaddon.Addon(id=__addonid__)
__profile__     = xbmc.translatePath( __settings__.getAddonInfo('profile') )
cookieFile = __profile__ + 'cookies.letv'

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
VIDEO_LIST = [['1','电影','&o=9'],['2','电视剧','&o=9'],['5','动漫','&o=9'],['11','综艺','&o=9&s=1'],['3','明星','&a=-1']]
UGC_LIST = [['4','体育','&o=1'],['3','娱乐','&o=9'],['9','音乐','&o=17'],['20','风尚','&o=1'],['16','纪录片','&o=1'],['22','财经','&o=1'],['14','汽车','&o=1'],['23','旅游','&o=1']]

VIDEO_RES = [["标清",'sd'],["高清",'hd'],["普通",''],["未注","null"]]
CLASS_MODE = [['10','电影'],['5','电视剧'],['5','动漫'],['11','综艺'],['21','明星'],['11','娱乐'],['10','音乐']]
COLOR_LIST = ['[COLOR FFFF0000]','[COLOR FF00FF00]','[COLOR FFFFFF00]','[COLOR FF00FFFF]','[COLOR FFFF00FF]']

##################################################################################
# Routine to fetech url site data using Mozilla browser
# - deletc '\r|\n|\t' for easy re.compile
# - do not delete ' ' i.e. <space> as some url include spaces
# - unicode with 'replace' option to avoid exception on some url
# - translate to utf8
##################################################################################
def getHttpData(url):
    print "getHttpData: " + url
    # setup proxy support
    proxy = __addon__.getSetting('http_proxy')
    type = 'http'
    if proxy <> '':
        ptype = re.split(':', proxy)
        if len(ptype)<3:
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
    
    for k in range(3): # give 3 trails to fetch url data
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
            if not (httpdata[2:11] == "exception") :
                cj.save(cookieFile, ignore_discard=True, ignore_expires=True)
                break

    httpdata = re.sub('\r|\n|\t', '', httpdata)
    match = re.compile('<meta.+?charset=["]*(.+?)"').findall(httpdata)
    if len(match):
        charset = match[0].lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = unicode(httpdata, charset,'replace').encode('utf8')
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
            itemList  = [[x[0],x[1].strip()] for x in itemLists]
    
            item1 = itemList[0][0].split('_')
            item2 = itemList[1][0].split('_')
            ilist = len(item1)
            # find the variable location
            for j in range(ilist):
                if (item1[j] == item2[j]): continue
                break
            icnt = len(itemList)
            for i in range (icnt):
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
        itemList  = [[x[0],x[1].strip()] for x in itemLists]

    catlist.append(itemList)
    return titlelist, catlist   

##################################################################################
# Routine to update video list as per user selected filtrs
##################################################################################
def updateListSEL(name, url, cat, filtrs, page, listpage):
    dialog = xbmcgui.Dialog()
    titlelist, catlist  = getListSEL(listpage)
    fltr = filtrs[1:].replace('=','').split('&')

    cat =''
    selection = ''
    for icat, title in enumerate(titlelist):
        fltrList = [x[0] for x in catlist[icat]]
        list = [x[1] for x in catlist[icat]]
        sel = -1
        if (page): # 0: auto extract cat only
            sel = dialog.select(title, list)
        if sel == -1:
            # return last choice selected if ESC by user
            if len(fltr) == len(titlelist):
                sel = fltrList.index(fltr[icat])
            else: # default for first time entry
                sel = 0
        selx = catlist[icat][sel][0]
        ctype = catlist[icat][sel][1]
        if (ctype == '全部'):
            ctype += title[1:]
        # filtrs.append([catlist[icat][sel][0], catlist[icat][sel][1]])
        cat += COLOR_LIST[icat%5] + ctype + '[/COLOR]|'
        selcat = re.compile('([a-z]+)').findall(selx)[0]
        catlen = len(selcat)
        selection += '&'+selcat+'='+selx[catlen:]
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
# Routine to fetch & build LeTV 网络电视 main menu
# - video list as per [VIDEO_LIST]
# - ugc list as per [UGC_LIST]
# - movie, series, star & ugc require different sub-menu access methods
##################################################################################
def mainMenu():
    li = xbmcgui.ListItem('[COLOR F0F0F0F0] LeTV 乐视网 - 搜索:[/COLOR][COLOR FF00FF00]【点此进入】[/COLOR]')
    u=sys.argv[0]+"?mode=31"
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
     
    link = getHttpData('http://list.letv.com/listn/c1_t-1_a-1_y-1_s1_lg-1_ph-1_md_o9_d1_p.html')
    match = re.compile('<div class="channel_list.+?">(.+?)</div>').findall(link)[0]
    ugclist = re.compile('href="(.+?)".*?>(.+?)</a>').findall(match)
    
    totalItems = len(ugclist)
    listpage=""
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

                li = xbmcgui.ListItem(str(i) + '. ' + name)
                u = sys.argv[0]+"?mode="+mode+"&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page=1"+"&listpage="+listpage
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    
    # fetch the url from ugclist for ugc channels, for those in UGC_LIST
    for x_url, name in ugclist:
        for catx, namex, filtrs in UGC_LIST: 
            if (name == namex):
                i = i + 1
                url = p_url + x_url
                li = xbmcgui.ListItem(str(i) + '. ' + name)
                u = sys.argv[0]+"?mode=8"+"&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page=1"+"&listpage="+listpage
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))  

##################################################################################
# Routine to fetch and build the video selection menu
# - selected page & filters (user selectable)
# - video items list
# - user selectable pages
##################################################################################
def progListMovie(name, url, cat, filtrs, page, listpage):
    fltrCategory = fetchID(VIDEO_LIST, name)
    if page == None: page ='1'
    p_url = "http://list.letv.com/apin/chandata.json?c=%s&d=2&md=&p=%s%s"
    
    if (listpage == None):
        link = getHttpData(url)
        listpage = re.compile('<ul class="label_list.+?>(.+?)</ul>').findall(link)[0]
        match = re.compile('<div class="sort_navy.+?">(.+?)</div>').findall(link)
        if len(match):
            listpage += match[0].replace('li','lo')
        cat = updateListSEL(name, url, cat, filtrs, 0, listpage)    
    p_url = p_url % (fltrCategory, page, filtrs)
    
    # Fetch & build video titles list for user selection, highlight user selected filtrs  
    li = xbmcgui.ListItem(name + '（第' + str(page) + '页）【' + cat + '】（按此选择)')
    u = sys.argv[0]+"?mode=9&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page=1"+"&listpage="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    link=getHttpData(p_url)
    if link == None: return
    
    # Movie, Video, Series, Variety & Music titles need different routines
    if ((name == '电视剧') or (name == '动漫')):
        isDir = True
        mode = '2'
    elif ((name == '电影') or (name == '综艺')):
        isDir = False
        mode = '10'

    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['data_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        p_name = vlist[i]['name'].encode('utf-8')
        if ((name == '电视剧') or (name == '动漫')):
            aid = str(vlist[i]['aid'])
            if (name == '电视剧'): v_url = 'http://www.letv.com/tv/%s.html' % aid
            else: v_url = 'http://www.letv.com/comic/%s.html' % aid
        else:
            if (name == '综艺'):
                vid = str(vlist[i]['vid'])
                p_name = p_name.split("：")[0]
            else: # '电影'
                vid = str(vlist[i]['vids'].split(',')[0])
            v_url  = 'http://www.letv.com/ptv/vplay/%s.html' % vid

        try: 
            p_thumb = vlist[i]['images']['150*200']
        except KeyError:
            p_thumb = vlist[i]['images']['160*120']
        except: p_thumb = ''

        p_title = p_name
        p_list = str(i+1) + '. ' + p_title + ' '
        try:
            p_rating = float(vlist[i]['rating'])
            if (p_rating != None and p_rating > 0.01):
                p_rating = "%0.1f" % p_rating
                p_list += '[COLOR FFFF00FF][' + p_rating + '][/COLOR]'
        except:
            pass

        if ((name == '电影') or (name == '动漫')):
            p_lang = vlist[i]['lgName']
            if (p_lang != None):
                p_list += '[COLOR FF00FFFF][' + p_lang.encode('utf-8') + '][/COLOR]'
        else:
            p_area = vlist[i]['areaName']
            if (p_area != None):
                p_list += '[COLOR FF00FFFF][' + p_area.encode('utf-8') + '][/COLOR]'

        p_dx = int(vlist[i]['duration'])
        if ((p_dx != None) and (p_dx > 0)):
            p_duration= "[%02d:%02d]" %  (int(p_dx / 60), (p_dx % 60))
            p_list += '[COLOR FFFFFF00]' + p_duration +'[/COLOR]'
            
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
        u = sys.argv[0]+"?mode="+mode+"&name="+urllib.quote_plus(p_name)+"&url="+urllib.quote_plus(v_url)+"&thumb="+urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isDir, totalItems)
        
    # Fetch and build page selection menu
    p_itemCount= content['data_count']
    p_pageSize = 30
    p_pageTotal = (p_itemCount + 29) / p_pageSize
    p_pageMid = int(p_pageTotal / 2)
    
    p_pageNum = int(page)
    if (p_pageNum <= p_pageMid):
        p_pageEnd = min(8, p_pageTotal)
        pages = range(0, p_pageEnd)
        p_pageFromEnd = max((p_pageTotal - 2), (p_pageEnd + 1))
    else:
        pages = range(2)
        p_pageFromEnd = max((p_pageTotal - 8), 2)
    for x in range(p_pageFromEnd, p_pageTotal): pages.append(x) 

    for num in pages:
        page = num + 1
        if (page) != p_pageNum:
            li = xbmcgui.ListItem("... 第" + str(page) + "页")
            u = sys.argv[0]+"?mode=1"+"&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page="+str(page)+"&listpage="+urllib.quote_plus(listpage)
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
    episodes=''
    if match: 
        episodes = ' (' + ' '.join(match[0].split()) + ')'
    
    li = xbmcgui.ListItem('【[COLOR FFFFFF00]'+name+'[/COLOR]'+episodes+' | [COLOR FF00FFFF][选择: '+name+'][/COLOR]】', iconImage='', thumbnailImage=thumb)
    u = sys.argv[0]+"?mode=2&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&thumb="+urllib.quote_plus(thumb) 
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    # fetch and build the video series list
    match = re.compile('<div.+?data-tabct="j-tab[1-9]+_child".+?statectn="n_list[1-9]+">(.+?)</div>').findall(link)
    # special handling for '动漫'
    if match is None:
        match = re.compile('<div.+?data-tabct="j-tab[1-9]+_child"(.+?)</div>').findall(link)
    else:
        matchp = re.compile('<dl class="w96">(.+?)</dl>').findall(match[0])
        if len(matchp): # not the right one, so re-fetch             
            match = re.compile('<div.+?data-tabct="j-tab[1-9]+_child"(.+?)</div>').findall(link)
     
    for j in range(0, len(match)):
        matchp = re.compile('<dl class="w120">(.+?)</dl>').findall(match[j])              
        totalItems = len(matchp)
        for i in range(0, len(matchp)):
            match1 = re.compile('<img.+?src="(.+?)"').findall(matchp[i])
            p_thumb = match1[0]
            match1 = re.compile('<p class="p1">.+?href="(.+?)"[\s]*title="(.+?)">(.+?)</a>').findall(matchp[i])
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
    if page == None: page ='1'
    p_url = "http://list.letv.com/apin/stardata.json?d=%s&p=%s%s"
    
    if (listpage == None):
        link = getHttpData(url)
        listpage = re.compile('<ul class="label_list.+?>(.+?)</ul>').findall(link)[0]
        match = re.compile('<div class="sort_navy.+?">(.+?)</div>').findall(link)
        if len(match):
            listpage += match[0].replace('li','lo')
        cat = updateListSEL(name, url, cat, filtrs, 0, listpage)    
    p_url = p_url % (fltrCategory, page, filtrs)    
    
    # Fetch & build video titles list for user selection, highlight user selected filter  
    li = xbmcgui.ListItem(name + '（第' + str(page) + '页）【' + cat + '】（按此选择)')
    u = sys.argv[0]+"?mode=9&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page=1"+"&listpage="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    link=getHttpData(p_url)
    if link == None: return
 
    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['data_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        p_name = vlist[i]['name'].encode('utf-8')
        #v_url = 'http://so.letv.com/star?wd=%s&from=list' % p_name
        v_url = 'http://so.letv.com/s?wd=%s' % p_name
        p_thumb = vlist[i]['postS1']
        p_list = str(i+1) + '. [COLOR FF00FF00]' + p_name + '[/COLOR] '

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
        u = sys.argv[0]+"?mode=5"+"&name="+urllib.quote_plus(p_name)+"&url="+urllib.quote_plus(v_url)+"&thumb="+urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
        
    # Fetch and build page selection menu
    p_itemCount= content['video_count']
    p_pageSize = 30
    p_pageTotal = (p_itemCount + 29) / p_pageSize
    p_pageMid = int(p_pageTotal / 2)
    
    p_pageNum = int(page)
    if (p_pageNum <= p_pageMid):
        p_pageEnd = min(8, p_pageTotal)
        pages = range(0, p_pageEnd)
        p_pageFromEnd = max((p_pageTotal - 2), (p_pageEnd + 1))
    else:
        pages = range(2)
        p_pageFromEnd = max((p_pageTotal - 8), 2)
    for x in range(p_pageFromEnd, p_pageTotal): pages.append(x) 

    for num in pages:
        page = num + 1
        if (page) != p_pageNum:
            li = xbmcgui.ListItem("... 第" + str(page) + "页")
            u = sys.argv[0]+"?mode=4"+"&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page="+str(page)+"&listpage="+urllib.quote_plus(listpage)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    
          
##################################################################################
# Routine to extract video series selection menu for user playback
# - for 明星
# filtrs: movie cg=1; series cg=2; pn=pageNumber; ps=pageSize
#p_url = 'http://open.api.letv.com/ms?hl=1&dt=2&ph=420001&from=pcjs
#p_url += '&cg=1&pn=%s&ps=30&wd=%s&_=1391387253932' % (page, name)
##################################################################################
def progListStarVideo(name, url, page, thumb):
    if (page == None): page = '1' 
    p_url = 'http://open.api.letv.com/ms?hl=1&dt=2&pn=%s&ps=30&wd=%s' % (page, name)

    li = xbmcgui.ListItem('【[COLOR FF00FFFF]['+name+'][/COLOR] | [COLOR FFFFFF00]（第'+page+'页）[/COLOR]】', iconImage='', thumbnailImage=thumb)
    u = sys.argv[0]+"?mode=5&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&thumb="+urllib.quote_plus(thumb) 
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
   
    link = getHttpData(p_url)
    if link == None: return
    
    playlist=xbmc.PlayList(0) # use Music playlist for temporary storage
    playlist.clear()
     
    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['data_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        p_title = vlist[i]['name'].encode('utf-8')
        
        # aid = str(vlist[i]['aid'])
        vid = str(vlist[i]['vid'])
        v_url  = 'http://www.letv.com/ptv/vplay/%s.html' % vid
        
        try: 
            p_thumb = vlist[i]['images']['150*200']
        except KeyError:
            p_thumb = vlist[i]['images']['160*120']
        except: p_thumb = ''

        p_name = p_list = str(i+1) + '. ' + p_title + ' '
        p_category = vlist[i]['categoryName']
        if ((p_category != None) and len(p_category)):
            # p_cat = p_category.encode('utf-8')
            # if(p_cat != '电影' and p_cat != '电视剧'): continue 
            p_list += '[COLOR FF00FFFF][' + p_category.encode('utf-8') + '][/COLOR] '
        
        try:
            p_rating = float(vlist[i]['rating'])
            if (p_rating != None and p_rating > 0.01):
                p_rating = "%0.1f" % p_rating
                p_list += '[COLOR FFFF00FF][' + p_rating + '][/COLOR]'
        except:
            pass

        p_dx = int(vlist[i]['duration'])
        if ((p_dx != None) and (p_dx > 0)):
            p_duration= "[%02d:%02d]" %  (int(p_dx / 60), (p_dx % 60))
            p_list += '[COLOR FFFFFF00]' + p_duration +'[/COLOR]'

        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        # li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_name})
        u = sys.argv[0]+"?mode=20"+"&name="+urllib.quote_plus(p_name)+"&url="+urllib.quote_plus(v_url)+"&thumb="+urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
        playlist.add(v_url, li)
        
    # Fetch and build page selection menu
    p_itemCount= content['data_count']
    p_pageSize = 30
    p_pageTotal = (p_itemCount + 29) / p_pageSize
    p_pageMid = int(p_pageTotal / 2)
    
    p_pageNum = int(page)
    if (p_pageNum <= p_pageMid):
        p_pageEnd = min(8, p_pageTotal)
        pages = range(0, p_pageEnd)
        p_pageFromEnd = max((p_pageTotal - 2), (p_pageEnd + 1))
    else:
        pages = range(2)
        p_pageFromEnd = max((p_pageTotal - 8), 2)
    for x in range(p_pageFromEnd, p_pageTotal): pages.append(x) 

    for num in pages:
        page = num + 1
        if (page) != p_pageNum:
            li = xbmcgui.ListItem("... 第" + str(page) + "页")
            u = sys.argv[0]+"?mode=5"+"&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&page="+str(page)+"&thumb="+urllib.quote_plus(thumb)
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
    if page == None: page ='1'
    p_url = "http://list.letv.com/apin/chandata.json?c=%s&d=2&md=&p=%s%s"
    
    if (listpage == None):
        link = getHttpData(url)
        listpage = re.compile('<ul class="label_list.+?>(.+?)</ul>').findall(link)[0]
        listpage += re.compile('<div class="sort_navy.+?">(.+?)</div>').findall(link)[0].replace('li','lo')
        cat = updateListSEL(name, url, cat, filtrs, 0, listpage)    
    p_url = p_url % (fltrCategory, page, filtrs)    
    
    # Fetch & build video titles list for user selection, highlight user selected filter  
    li = xbmcgui.ListItem(name + '（第' + str(page) + '页）【' + cat + '】（按此选择)')
    u = sys.argv[0]+"?mode=9&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page=1"+"&listpage="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    link=getHttpData(p_url)
    if link == None: return

    playlist=xbmc.PlayList(0) # use Music playlist for temporary storage
    playlist.clear()

    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['data_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        vid = str(vlist[i]['vid'])
        v_url  = 'http://www.letv.com/ptv/vplay/%s.html' % vid
        p_title = vlist[i]['name'].encode('utf-8')

        try: 
            p_thumb = vlist[i]['images']['150*200']
        except KeyError:
            p_thumb = vlist[i]['images']['160*120']
        except: pass
            
        p_list = p_name = str(i+1) + '. ' + p_title + ' '
        p_artist = vlist[i]['actor']
        if ((p_artist != None) and len(p_artist)):
            p_list += '[COLOR FFFF00FF]['
            for actor in p_artist:
                p_list +=  actor.encode('utf-8') + ' '
            p_list = p_list[:-1] + '][/COLOR]'

        p_dx = int(vlist[i]['duration'])
        if (p_dx != None):
            p_duration= "[%02d:%02d]" %  (int(p_dx / 60), (p_dx % 60))
            p_list += '[COLOR FFFFFF00]' + p_duration +'[/COLOR]'

        p_album = vlist[i]['albumName']
        if (p_album != None):
            p_album = p_album.encode('utf-8') 
            p_list += '[COLOR FF00FFFF][' + p_album + '][/COLOR]'
       
        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        # li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_artist})
        u = sys.argv[0]+"?mode=20"+"&name="+urllib.quote_plus(p_list)+"&url="+urllib.quote_plus(v_url)+"&thumb="+urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
        playlist.add(v_url, li)
        
    # Fetch and build page selection menu
    p_itemCount= content['data_count']
    p_pageSize = 30
    p_pageTotal = (p_itemCount + 29) / p_pageSize
    p_pageMid = int(p_pageTotal / 2)
    
    p_pageNum = int(page)
    if (p_pageNum <= p_pageMid):
        p_pageEnd = min(8, p_pageTotal)
        pages = range(0, p_pageEnd)
        p_pageFromEnd = max((p_pageTotal - 2), (p_pageEnd + 1))
    else:
        pages = range(2)
        p_pageFromEnd = max((p_pageTotal - 8), 2)
    for x in range(p_pageFromEnd, p_pageTotal): pages.append(x) 

    for num in pages:
        page = num + 1
        if (page) != p_pageNum:
            li = xbmcgui.ListItem("... 第" + str(page) + "页")
            u = sys.argv[0]+"?mode=8"+"&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page="+str(page)+"&listpage="+urllib.quote_plus(listpage)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    
    
#################################################################################
# Get user input for LeTV site 
# http://open.api.letv.com/ms?hl=1&dt=2&ph=420001&from=pcjs&pn=1&ps=25&wd=%E7%88%B1%E4%BA%BA&_=1392364710043 
##################################################################################
def searchLetv():
    result=''
    
    keyboard = Apps('','请输入搜索内容')
    # keyboard.setHiddenInput(hidden)
    xbmc.sleep( 1500 )
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
    link=getHttpData(p_url)
    
    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索: 第' + page + '页[/COLOR][COLOR FFFFFF00] ('+name+')[/COLOR]【[COLOR FF00FF00]' + '点此输入新搜索内容' + '[/COLOR]】')
    u = sys.argv[0] + "?mode=31&name=" + urllib.quote_plus(name) + "&page=" + page
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    if link == None:
        li=xbmcgui.ListItem('  抱歉，没有找到[COLOR FFFF0000] '+name+' [/COLOR]的相关视频')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return
    
    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['data_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        vid = str(vlist[i]['vid'])
        v_url  = 'http://www.letv.com/ptv/vplay/%s.html' % vid
        p_title = vlist[i]['name'].encode('utf-8')

        try: 
            p_thumb = vlist[i]['images']['150*200']
        except KeyError:
            p_thumb = vlist[i]['images']['160*120']
        except: pass
            
        p_categoryName = vlist[i]['categoryName']
        if (p_categoryName != None):
            p_list = p_name = str(i+1) + '. [COLOR FF00FFFF][' + p_categoryName.encode('utf-8') +'][/COLOR] ' + p_title + ' '
        else:
            p_list = p_name = str(i+1) + '. ' + p_title + ' '
            
        try:
            p_rating = float(vlist[i]['rating'])
            if (p_rating != None and p_rating > 0.01):
                p_rating = "%0.1f" % p_rating
                p_list += '[COLOR FFFF00FF][' + p_rating + '][/COLOR]'
        except:
            pass            
        
        p_dx = int(vlist[i]['duration'])
        if (p_dx != None):
            p_duration= "[%02d:%02d]" %  (int(p_dx / 60), (p_dx % 60))
            p_list += '[COLOR FFFFFF00]' + p_duration +'[/COLOR]'

        p_artists = vlist[i]['actor']
        if ((p_artists != None) and len(p_artists)):
            p_artist = ""
            p_list += '['
            for key in p_artists:
                p_artist += p_artists[key].encode('utf-8') + ' '
            p_list += p_artist[:-1] + ']'

        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0]+"?mode=10"+"&name="+urllib.quote_plus(p_list)+"&url="+urllib.quote_plus(v_url)+"&thumb="+urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
        
    # Fetch and build page selection menu
    p_itemCount= content['video_count']
    p_pageSize = 30
    p_pageTotal = (p_itemCount + 29) / p_pageSize
    p_pageMid = int(p_pageTotal / 2)
    
    p_pageNum = int(page)
    if (p_pageNum <= p_pageMid):
        p_pageEnd = min(8, p_pageTotal)
        pages = range(0, p_pageEnd)
        p_pageFromEnd = max((p_pageTotal - 2), (p_pageEnd + 1))
    else:
        pages = range(2)
        p_pageFromEnd = max((p_pageTotal - 8), 2)
    for x in range(p_pageFromEnd, p_pageTotal): pages.append(x) 

    for num in pages:
        page = num + 1
        if (page) != p_pageNum:
            li = xbmcgui.ListItem("... 第" + str(page) + "页")
            u = sys.argv[0]+"?mode=32"+"&name="+urllib.quote_plus(name)+"&page="+str(page)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    
    
##################################################################################
# LeTV Video Link Decode Algorithm & Player
# Extract all the video list and start playing first found valid link
# User may press <SPACE> bar to select video resolution for playback
##################################################################################
def playVideoLetv(name,url,thumb):
    VIDEO_CODE=[['bHY=','bHY/'],['dg==','dj9i'],['dg==','dTgm'],['Zmx2','Zmx2']]
    dialog = xbmcgui.Dialog()

    link = getHttpData(url)
    match = re.compile('{v:\[(.+?)\]').findall(link)
    # link[0]:"标清-SD" ; link[1]:"高清-HD"
    if match:
        matchv = re.compile('"(.+?)"').findall(match[0])
        if matchv:
            playlist=xbmc.PlayList(1)
            playlist.clear()
            if videoRes == 1: # Play selected HD and fallback to SD if HD failed
                vlist = reversed(range(len(matchv)))
            else: # Play selected SD and HD as next item in playlist
                vlist = range(len(matchv))
                
            for j in vlist:
                if matchv[j] == "": continue
                #algorithm to generate the video link code
                vidx = matchv[j].find('MT')
                vidx = -1 # force to start at 24
                if vidx < 0:
                    vid = matchv[j][24:+180]  # extract max VID code length
                else:
                    vid = matchv[j][vidx:+180]
                    
                for k in range(0, len(VIDEO_CODE)):
                    vidcode = re.split(VIDEO_CODE[k][1], vid)
                    if len(vidcode) > 1 :                 
                        vid = vidcode[0] + VIDEO_CODE[k][0]
                        break
                    
                # fail to decipher, use alternate method to play    
                if len(vidcode) == 1:
                    #print 'vidcode: ', vidcode
                    #print "Use alternative player"
                    playVideo(name,url,thumb)
                    return
                #else:                        
                p_url = 'http://g3.letv.cn/vod/v1/' + vid + '?format=1&b=388&expect=3&host=www_letv_com&tag=letv&sign=free'
                link = getHttpData(p_url)
                link = link.replace("\/", "/")
                match = re.compile('{.+?"location": "(.+?)" }').findall(link)
                if match:
                    for i in range(len(match)):
                        p_name = name +' ['+ VIDEO_RES[j][0] +']' 
                        listitem = xbmcgui.ListItem(p_name, thumbnailImage = __addonicon__)
                        listitem.setInfo(type="Video",infoLabels={"Title":p_name})
                        playlist.add(match[i], listitem)
                        break # skip the rest if any (1 of 3) video links access successful
                    break # play user selected video resolution only
                else:
                    ok = dialog.ok(__addonname__, '无法播放：未匹配到视频文件，请选择其它视频')
            xbmc.Player().play(playlist)
        else:
            ok = dialog.ok(__addonname__, '无法播放：需收费，请选择其它视频')  
    else:
        match = re.compile('<dd class="ddBtn1">.+?title="(.+?)" class="btn01">').findall(link)
        if match and match[0] == "点播购买":
            ok = dialog.ok(__addonname__, '无法播放：需收费，请选择其它视频')
        else:
            ok = dialog.ok(__addonname__, '无法播放：未匹配到视频文件，请选择其它视频')

##################################################################################
def playVideo(name,url,thumb):
    videoRes = int(__addon__.getSetting('video_resolution'))
    vparamap = {0:'normal', 1:'high', 2:'super'}
    
    dialog = xbmcgui.Dialog()
    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
    
    # p_url = "http://www.flvcd.com/parse.php?kw="+url+"&format="+str(videoRes)
    p_url = "http://www.flvcd.com/parse.php?kw="+url+"&format="+vparamap.get(videoRes,0)
    for i in range(5): # Retry specified trials before giving up (seen 9 trials max)
       if (pDialog.iscanceled()):
           pDialog.close() 
           return
       pDialog.update(20*i)

       try: # stop xbmc from throwing error to prematurely terminate video search
            link = getHttpData(p_url)
            if '加密视频' in link:
                ok = dialog.ok(__addonname__, '无法播放：该视频为加密视频')
                return
            elif '付费视频' in link:
                ok = dialog.ok(__addonname__, '无法播放：该视频为付费视频')
                return
            else:
                match=re.compile('下载地址：\s*<a href="(.+?)" target="_blank" class="link"').findall(link)
                if len(match): break
       except:
           pass   
    
    if len(match):
        pDialog.close() 
        playlist=xbmc.PlayList(1)
        playlist.clear()
        for i in range(0,len(match)):
            listitem = xbmcgui.ListItem(name, thumbnailImage = __addonicon__)
            listitem.setInfo(type="Video",infoLabels={"Title":name+" 第"+str(i+1)+"/"+str(len(match))+" 节"})
            playlist.add(match[i], listitem)
        xbmc.Player().play(playlist)
    else:
        #if '解析失败' in link:
        pDialog.close() 
        ok = dialog.ok(__addonname__, '无法播放：多次未匹配到视频文件，请选择其它视频')

##################################################################################
# Continuous Player start playback from user selected video
# User backspace to previous menu will not work - playlist = last selected
##################################################################################
def playVideoUgc(name,url,thumb):
    videoRes = int(__addon__.getSetting('video_resolution'))
    videoplaycont = __addon__.getSetting('video_vplaycont')

    playlistA=xbmc.PlayList(0)
    playlist=xbmc.PlayList(1)
    playlist.clear()

    v_pos = int(name.split('.')[0])-1
    psize = playlistA.size()
    ERR_MAX = 10
    errcnt = 0
    k=0
    
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
        p_item=playlistA.__getitem__(x)
        p_url=p_item.getfilename(x)
        p_list =p_item.getdescription(x)

        #li = xbmcgui.ListItem(p_list, iconImage = '', thumbnailImage = thumb)
        li = xbmcgui.ListItem(p_list)
        li.setInfo(type = "Video", infoLabels = {"Title":p_list})  
        
        if re.search('http://www.letv.com/', p_url):  #fresh search
            f_url = "http://www.flvcd.com/parse.php?kw="+p_url+"&format="+str(videoRes)
            for i in range(5): # Retry specified trials before giving up (seen 9 trials max)
                if (pDialog.iscanceled()):
                    pDialog.close() 
                    x = psize # terminate any old thread
                    return
                pDialog.update(errcnt*100/ERR_MAX + 100/ERR_MAX/5*i)
                try: # stop xbmc from throwing error to prematurely terminate video search
                    link = getHttpData(f_url)
                    v_url=''
                    if '加密视频' in link: break
                    elif '付费视频' in link: break
                    elif '解析失败' in link: break
                    #print "skip:", re.compile('(提示.+?)</td>').findall(link)[0]
                    
                    v_url=re.compile('下载地址：\s*<a href="(.+?)" target="_blank" class="link"').findall(link)
                    # v_url=re.compile('location:\s*<a href="(.+?)" target="_blank" class="link"').findall(link)
                    if len(v_url):
                        v_url = v_url[0]
                        break
                    else:
                        print "flvcd link: " + f_url
                except:
                    pass

            if not len(v_url):
                errcnt += 1 # increment consequetive unsuccessful access
                continue
            err_cnt = 0 # reset error count
            playlistA.remove(p_url) # remove old url
            playlistA.add(v_url, li, x)  # keep a copy of v_url in Audio Playlist
        else:
            v_url = p_url
            
        playlist.add(v_url, li, k)
        k +=1
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
    playVideo(name,url,thumb)
elif mode == 12:
    playVideoLetv(name,url,thumb)
elif mode == 20:
    playVideoUgc(name,url,thumb)

elif mode == 31:
    searchLetv()
elif mode == 32:
    letvSearchList(name, page)