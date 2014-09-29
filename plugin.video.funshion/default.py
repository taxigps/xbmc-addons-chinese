# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, string, sys, os, gzip, StringIO
import math, os.path, httplib, time
from random import randrange
import cookielib
try:
    import simplejson
except ImportError:
    import json as simplejson
    
########################################################################
# 风行视频(Funshion)"
########################################################################
# v1.0.11 2014.06.15 (cmeng)
# - Add handler for unsupported catalog in seriesList

# Plugin constants 
__addon__     = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__profile__     = xbmc.translatePath(__addon__.getAddonInfo('profile'))
cookieFile = __profile__ + 'cookies.funshion'

CHANNEL_LIST = [['电影','movie'],['电视剧','tv'],['动漫','cartoon'],['综艺','variety'],['新闻','news'],['娱乐','ent'],['体育','sports'],['搞笑','joke'],['时尚','fashion'],['生活','life'],['旅游','tour'],['科技','tech']]
ORDER_LIST = [['mo','最近更新'], ['z4','最受欢迎'], ['ka','评分最高'], ['re','最新上映']]
COLOR_LIST = ['[COLOR FFFF0000]','[COLOR FF00FF00]','[COLOR FFFFFF00]','[COLOR FF00FFFF]','[COLOR FFFF00FF]']

RES_LIST = [['tv','标清'], ['dvd','高清'], ['high-dvd','超清']]
LANG_LIST = [['chi','国语'], ['arm','粤语'], ['und','原声']]
TYPES1 = ('movie','tv','cartoon','variety') # 电影,电视剧,动漫,综艺
TYPES2 = ('ent','video') # 娱乐, 视频
TYPES3 = ('ent','news','sports','joke','fashion','life','tour','tech') # 娱乐,新闻,体育,搞笑,时尚,生活,旅游,科技 
UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'

########################################################################
def log(txt):
    message = '%s: %s' % (__addonname__, txt)
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

########################################################################
def getHttpData(url):
    print "url-link: " + url
    log("%s::url - %s" % (sys._getframe().f_code.co_name, url))
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        response.close()
    except:
        log( "%s (%d) [%s]" % (
               sys.exc_info()[2].tb_frame.f_code.co_name,
               sys.exc_info()[2].tb_lineno,
               sys.exc_info()[1]
               ))
        return ''
    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    if match:
        charset = match[0]
    else:
        match = re.compile('<meta charset="(.+?)"').findall(httpdata)
        if match:
            charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')
    return httpdata

########################################################################
def searchDict(dlist,idx):
    for i in range(0,len(dlist)):
        if dlist[i][0] == idx:
            return dlist[i][1]
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
    match = re.compile('<div class="sort-.+?fix">(.+?)</ul>', re.DOTALL).findall(listpage)
    for k, list in enumerate(match):
        title = re.compile('<div class="select-subtitle">(.+?)</div>').findall(list)
        itemLists = re.compile('<a href="/[a-z]+?/[a-z]+?/(.+?)/".+?>(.+?)</a>').findall(list)
        if (len(itemLists) > 1):
            itemList  = [[x[0],x[1].strip()] for x in itemLists]
    
            item1 = itemList[0][0].split('.')
            item2 = itemList[1][0].split('.')
            ilist = len(item1)
            # find the variable location
            for j in range(ilist):
                if (item1[j] == item2[j]): continue
                break

            icnt = len(itemList)
            for i in range (icnt-1, -1, -1): # must do in reverse to remove item
                if (itemList[i][1] == "取消选中"):
                    itemList.remove(itemList[i])
                    continue
                itemx = itemList[i][0].split('.')
                itemList[i][0] = itemx[j]
            titlelist.append(title[0])
            catlist.append(itemList)

    # extract order selection if any
    matchp = re.compile('<div class="sort-tab-line bgcfff fix">(.+?)</div>', re.DOTALL).findall(listpage)
    if len(matchp):
        titlelist.append('排序方式')
        itemLists = re.compile('<a href="/[a-z]+?/[a-z]+?/(.+?)\..+?><span>(.+?)</span>').findall(matchp[0])
        itemList  = [[x[0],x[1].strip()] for x in itemLists]
    catlist.append(itemList)

    # print titlelist, catlist
    return titlelist, catlist   

##################################################################################
# Routine to update video list as per user selected filtrs
##################################################################################
def updateListSEL(name, type, cat, filtrs, page, listpage):
    dialog = xbmcgui.Dialog()
    titlelist, catlist  = getListSEL(listpage)
    fltr = filtrs[1:].split('.')

    cat =''
    selection = ''
    for icat, title in enumerate(titlelist):
        fltrList = [x[0] for x in catlist[icat]]
        list = [x[1] for x in catlist[icat]]
        sel = -1
        if (page): # page=0: auto extract cat only
            sel = dialog.select(title, list)
        if sel == -1:
            # return last choice selected if ESC by user
            if len(fltr) == len(titlelist):
                sel = fltrList.index(fltr[icat])
            else: # default for first time entry
                sel = 0
        ctype = catlist[icat][sel][1]
        if (ctype == '全部'):
            ctype += title
        cat += COLOR_LIST[icat%5] + ctype + '[/COLOR]|'
        selx = catlist[icat][sel][0]
        selection += '.'+selx
    filtrs = selection
    cat = cat[:-1]
    
    if (not page): return(cat)
    else:
        progList(name, type, cat, filtrs, page, listpage)        

##################################################################################
def rootList():
    totalItems = len(CHANNEL_LIST)
    cat = "全部"
    for name, type in CHANNEL_LIST:
        li = xbmcgui.ListItem(name)
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&type="+urllib.quote_plus(type)+"&cat="+cat+"&filtrs=&page=1"+"&listpage="
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
def progList(name, type, cat, filtrs, page, listpage):
    if page is None: page = 1
    # p_url = 'http://list.funshion.com/%s/pg-%s%s/'
    p_url = 'http://www.funshion.com/list/%s/pg-%s%s/'
    if  (listpage == None):
        url = p_url % (type, page, '.s-e6ada3e78987')
        link = getHttpData(url)

        match = re.compile('<div class="select-title"(.+?</div>)</div>', re.DOTALL).findall(link)
        if match:
            listpage = match[0]
        match = re.compile('<div class="sort-tab fix">(.+?</div>)', re.DOTALL).findall(link)
        if len(match):
            listpage += match[0]
        cat = updateListSEL(name, type, cat, filtrs, 0, listpage)
    else:
        url = p_url % (type, page, filtrs)
        link=getHttpData(url)

    # Fetch & build video titles list for user selection, highlight user selected filtrs  
    li = xbmcgui.ListItem(name + '（第' + str(page) + '页）【' + cat + '】（按此选择)')
    u = sys.argv[0]+"?mode=10&name="+urllib.quote_plus(name)+"&type="+type+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page=1"+"&listpage="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    if link == None: return
    # Movie, Video, Series, Variety & Music types need different routines
    if type in ('tv', 'cartoon', 'variety'): # 电视剧, 动漫,  综艺
        isdir = True
        mode = 2
    elif type in ('movie'): # 电影
        isdir = False
        mode = 3
    else: # 娱乐,新闻,体育,搞笑,时尚,生活,旅游,科技
        isdir = False
        mode = 4
        playlist=xbmc.PlayList(0) # use Music playlist for temporary storage
        playlist.clear()
 
    match = re.compile("<div class='item-unit fx-.+?'>(.+?)</div></div>", re.DOTALL).findall(link)
    totalItems = len(match) + 1
    
    for i in range(0,len(match)):
        match1 = re.compile("/vplay/[a-z]+-(.+?)/").findall(match[i])
        p_id = match1[0]
 
        match1 = re.compile('<img src=.+?_lazysrc=[\'|"]+(.+?)[\'|"]+.+?title="(.+?)"').findall(match[i])
        p_thumb = match1[0][0]
        p_name = match1[0][1].replace('&quot;','"')

        p_name1 = str(i+1) + '. ' + p_name + ' '
        match1 = re.compile("<span class='sright'>(.+?)</span>").findall(match[i])
        if len(match1):
            p_name1 += '(' + match1[0] + ') '

        match1 = re.compile('class="item-score">(.+?)</span>').findall(match[i])
        if len(match1):
            p_rating = match1[0]
            p_name1 += '[COLOR FFFF00FF][' + p_rating + '][/COLOR]'
            
        if match[i].find("class='ico-dvd spdvd'")>0:
            p_name1 += ' [COLOR FFFFFF00][超清][/COLOR]'
        elif match[i].find("class='ico-dvd hdvd'")>0:
            p_name1 += ' [COLOR FF00FFFF][高清][/COLOR]'
    
        match1 = re.compile('<i class="mark-update">(.+?)</i>').findall(match[i])
        if len(match1):
            p_duration = match1[0]
            p_name1 += ' [COLOR FF00FF00][' + p_duration + '][/COLOR]'
        
        match1 = re.compile('<p class="item-dp">(.+?)</p>').findall(match[i])
        if len(match1):
            p_desp = match1[0]
            p_name1 += ' (' + p_desp + ')'

        li = xbmcgui.ListItem(p_name1, iconImage = '', thumbnailImage = p_thumb)
        u = sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(p_name1)+"&id="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)+"&type="+urllib.quote_plus(type)
        li.setInfo(type = "Video", infoLabels = {"Title":p_name})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isdir, totalItems)
        if (mode == 4): playlist.add(p_id, li)

    # Construct page selection
    match = re.compile('class="page-index">(.+?)<span class=\'pglast\'>', re.DOTALL).findall(link)
    if match:
        match1 = re.compile("<a href='.+?'>(\d+)</a>", re.DOTALL).findall(match[0])
        plist=[str(page)]
        for num in match1:
            if (num not in plist):
                plist.append(num)
                li = xbmcgui.ListItem("... 第" + num + "页")
                u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&type="+urllib.quote_plus(type)+"&cat="+urllib.quote_plus(cat)+"&filtrs="+urllib.quote_plus(filtrs)+"&page="+num+"&listpage="+urllib.quote_plus(listpage)
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems) 

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
def seriesList(name,id,thumb):
    # url = 'http://api.funshion.com/ajax/get_web_fsp/%s/mp4?isajax=1' % (id)
    url = 'http://api.funshion.com/ajax/vod_panel/%s/w-1?isajax=1' % (id) #&dtime=1397342446859
    link = getHttpData(url)
    json_response = simplejson.loads(link)
    if json_response['status'] == 404:
        ok = xbmcgui.Dialog().ok(__addonname__, '本片暂不支持网页播放')
        return

    items = json_response['data']['fsps']['mult']
    totalItems = len(items)
    for item in items:
        p_name = item['full'].encode('utf-8')
        # p_number = str(item['number'])
        p_id2 = item['hashid']

        p_thumb = item['imagepath'].encode('utf-8')
        if not p_thumb:
            p_thumb = thumb
        
        li = xbmcgui.ListItem(p_name, iconImage = '', thumbnailImage = p_thumb)
        u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(p_name) + "&id=" + urllib.quote_plus(id)+ "&thumb=" + urllib.quote_plus(p_thumb) + "&id2=" + urllib.quote_plus(p_id2)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
def selResolution(items):
    ratelist = []
    for i in range(0,len(items)):
        if items[i][0] == RES_LIST[0][0]: ratelist.append([3, RES_LIST[0][1], i]) # [清晰度设置值, 清晰度, items索引]
        if items[i][0] == RES_LIST[1][0]: ratelist.append([2, RES_LIST[1][1], i])
        if items[i][0] == RES_LIST[2][0]: ratelist.append([1, RES_LIST[2][1], i])
    ratelist.sort()
    if len(ratelist) > 1:
        resolution = int(__addon__.getSetting('resolution'))
        if resolution == 0:    # 每次询问视频清晰度
            list = [x[1] for x in ratelist]
            sel = xbmcgui.Dialog().select('清晰度（低网速请选择低清晰度）', list)
            if sel == -1:
                return None, None
        else:
            sel = 0
            while sel < len(ratelist)-1 and resolution > ratelist[sel][0]: sel += 1
    else:
        sel = 0
    return items[ratelist[sel][2]][1], ratelist[sel][1]

##################################################################################
def PlayVideo(name,id,thumb,id2):
    if (id2 == '1'):
        # url = 'http://api.funshion.com/ajax/get_webplayinfo/%s/%s/mp4' % (id, id2)
        url = 'http://api.funshion.com/ajax/get_web_fsp/%s/mp4' % (id)
        link = getHttpData(url)
        json_response = simplejson.loads(link)
        if not json_response['data']:
            ok = xbmcgui.Dialog().ok(__addonname__, '没有可播放的视频')
            return
    
        # idx = (id2 - 1) # may also fetch with array index for a given id2 number
        try:
            hashid = json_response['data']['fsps']['mult'][0]['hashid'].encode('utf-8')
        except:
            ok = xbmcgui.Dialog().ok(__addonname__, '没有可播放的视频')
            return
    else:
        # hashid provided by series - feteching no required
        hashid = id2 # provided by series
        
    # url = 'http://jobsfe.funshion.com/query/v1/mp4/c847d5281686aab8bb3f4b338802c29fd236f8b2.json?clifz=fun&mac=&tm=1399766798&token=OVKHzVc57+mVfV1qDkAtYcmYKqbLRsoR2Uyv6aaI8vqW4IaC0VO+iWV0rXmhiMoRXXYhrI1/6J2dgg=='
    url = 'http://jobsfe.funshion.com/query/v1/mp4/%s.json' % (hashid)
    
    link = getHttpData(url)
    json_response = simplejson.loads(link)
    if json_response['return'].encode('utf-8') == 'succ':
        listitem = xbmcgui.ListItem(name,thumbnailImage=thumb)

        #xbmc.Player().play(json_response['playlist'][0]['urls'][0], listitem)
        # Randomly pick a server to stream video
        v_urls = json_response['playlist'][0]['urls']   #json_response['data']['fsps']['mult']
        # print "streamer servers: ", len(v_urls), v_urls, link, json_response['playlist'][0]
        try:
            i_url = randrange(len(v_urls)-1)
        except:
            i_url = 0
        v_url = v_urls[i_url]
        xbmc.Player().play(v_url, listitem)
    else:
        ok = xbmcgui.Dialog().ok(__addonname__, '没有可播放的视频')

##################################################################################
# Retrieve json file not further support ['dub_one'] key
##################################################################################
def PlayVideox(name,id,thumb,id2):
    url = 'http://api.funshion.com/ajax/get_webplayinfo/%s/%s/mp4' % (id, id2)
    link = getHttpData(url)
    json_response = simplejson.loads(link)
    if not json_response['playinfos']:
        ok = xbmcgui.Dialog().ok(__addonname__, '没有可播放的视频')
        return

    langlist = set([x['dub_one'].encode('utf-8') for x in json_response['playinfos']])
    langlist = [x for x in langlist]
    langid = json_response['playinfos'][0]['dub_one'].encode('utf-8')
    lang_select = int(__addon__.getSetting('lang_select')) # 默认|每次选择|自动首选
    if lang_select != 0 and len(langlist) > 1:
        if lang_select == 1:
            list = [searchDict(LANG_LIST,x) for x in langlist]
            sel = xbmcgui.Dialog().select('选择语言', list)
            if sel ==-1:
                return
            langid = langlist[sel]
        else:
            lang_prefer = __addon__.getSetting('lang_prefer') # 国语|粤语
            for i in range(0,len(LANG_LIST)):
                if LANG_LIST[i][1] == lang_prefer:
                    if LANG_LIST[i][0] in langlist:
                        langid = LANG_LIST[i][0]
                    break

    items = [[x['clarity'].encode('utf-8'), x['hashid'].encode('utf-8')]for x in json_response['playinfos'] if x['dub_one'].encode('utf-8') == langid]
    hashid, res = selResolution(items)
    lang = searchDict(LANG_LIST,langid)
    name = '%s(%s %s)' % (name, lang, res)
    url = 'http://jobsfe.funshion.com/query/v1/mp4/%s.json' % (hashid)
    link = getHttpData(url)
    json_response = simplejson.loads(link)
    if json_response['return'].encode('utf-8') == 'succ':
        listitem = xbmcgui.ListItem(name,thumbnailImage=thumb)
        xbmc.Player().play(json_response['playlist'][0]['urls'][0], listitem)
    else:
        ok = xbmcgui.Dialog().ok(__addonname__, '没有可播放的视频')

##################################################################################
def PlayVideo2(name,id,thumb,type):
    videoplaycont = __addon__.getSetting('video_vplaycont')

    playlistA=xbmc.PlayList(0)
    playlist=xbmc.PlayList(1)
    playlist.clear()

    v_pos = int(name.split('.')[0])-1
    psize = playlistA.size()
    ERR_MAX = psize-1
    TRIAL = 1
    errcnt = 0
    k=0
    
    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
    pDialog.update(0)   
    
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

        li = p_item # pass all li items including the embedded thumb image
        li.setInfo(type = "Video", infoLabels = {"Title":p_list})  
        
        if not re.search('http://', p_url):  #fresh search
            if type == 'video':
                url = 'http://api.funshion.com/ajax/get_media_data/ugc/%s' % (p_url)
            else:
                url = 'http://api.funshion.com/ajax/get_media_data/video/%s' % (p_url)
                
            if (pDialog.iscanceled()):
                pDialog.close() 
                x = psize # quickily terminate any old thread
                err_cnt = 0
                return
            pDialog.update(errcnt*100/ERR_MAX + 100/ERR_MAX/TRIAL*1)        
            
            link = getHttpData(url)
            try:
                json_response = simplejson.loads(link)
                hashid = json_response['data']['hashid'].encode('utf-8')
                filename = json_response['data']['filename'].encode('utf-8')
            except:
                errcnt += 1 # increment consequetive unsuccessful access
                continue
            url = 'http://jobsfe.funshion.com/query/v1/mp4/%s.json?file=%s' % (hashid, filename)

            link = getHttpData(url)
            try: # prevent system occassion throw error
                json_response = simplejson.loads(link)
                status = json_response['return'].encode('utf-8')
            except:
                errcnt += 1 # increment consequetive unsuccessful access
                continue
            if status == 'succ':
                v_url = json_response['playlist'][0]['urls'][0]
                playlistA.remove(p_url) # remove old url
                playlistA.add(v_url, li, x)  # keep a copy of v_url in Audio Playlist
            else: 
                errcnt += 1 # increment consequetive unsuccessful access
                continue
        else:
            v_url = p_url

        err_cnt = 0 # reset error count  
        playlist.add(v_url, li, k)
        k +=1
        if k == 1:
            pDialog.close() 
            xbmc.Player(1).play(playlist)
        if videoplaycont == 'false': break
    
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
mode = None
name = None
type = ''
filtrs = ''
page = None
id = None
thumb = None
id2 = '1'
listpage = None

try:
    id2 = urllib.unquote_plus(params["id2"])
except:
    pass
try:
    thumb = urllib.unquote_plus(params["thumb"])
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
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    type = urllib.unquote_plus(params["type"])
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
    listpage = urllib.unquote_plus(params["listpage"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass

if mode == None:
    rootList()
elif mode == 1:
    progList(name, type, cat, filtrs, page, listpage)
elif mode == 2:
    seriesList(name,id,thumb)
elif mode == 3:
    PlayVideo(name,id,thumb,id2)
elif mode == 4:
    PlayVideo2(name,id,thumb,type)
elif mode == 10:
    updateListSEL(name, type, cat, filtrs, page, listpage)
