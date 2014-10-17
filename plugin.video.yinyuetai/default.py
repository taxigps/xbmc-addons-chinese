# -*- coding: utf-8 -*-
import urllib,urllib2,re,os,xbmcplugin,xbmcgui,xbmc
import xbmcaddon
import datetime
import gzip, StringIO
import cookielib
import base64

try:
    import simplejson
except ImportError:
    import json as simplejson

##########################################################################
# 音悦台MV
##########################################################################
# Version 1.7.5 2014-06-15 (cmeng)
# Replace embedded unicode with ascii in get_vurl
##########################################################################

__addonname__ = "音悦台MV"
__addonid__   = "plugin.video.yinyuetai"
__addon__     = xbmcaddon.Addon(id=__addonid__)
__addonicon__ = os.path.join( __addon__.getAddonInfo('path'), 'icon.png' )
__settings__  = xbmcaddon.Addon(id=__addonid__)
__icon__      = xbmc.translatePath( __settings__.getAddonInfo('icon') )
__profile__   = xbmc.translatePath( __settings__.getAddonInfo('profile') )

cookieFile    = __profile__ + 'cookies.yinyuetai'
UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

#FCS_LIST = [['','首播'],['index-ml','内地'],['index-ht','港台'],['index-us','欧美'],['index-kr','韩语'],['index-jp','日语'],['index-yyman','音悦人'],['index-elite','热门推荐']]
FCS_LIST = [['all','全部'],['ml','内地'],['ht','港台'],['us','欧美'],['kr','韩国'],['jp','日本']]
MVR_LIST = [['all','全部推荐'],['ML','内地推荐'],['HT','港台推荐'],['US','欧美推荐'],['KR','韩语推荐'],['JP','日语推荐']]
MVR_DATE = [['today','今日'],['week','本周'],['month','本月']]

MVF_LIST = [['newRecommend','最新推荐'],['newFavorite','最新收藏'],['newComment','最新评论'],['hotView','热门播放'],['hotRecommend','热门推荐'],['hotFavorite','热门收藏'],['hotComment','热门评论'],['promo','编辑推荐'],['all','全部悦单']]
MVO_LIST = [['all','全部热门'],['today','24小时热门'],['week','本周热门'],['month','本月热门']]
AREA_LIST = [['','全部地区'],['ML','内地'],['HT','港台'],['US','欧美'],['KR','韩国'],['JP','日本']]
PAGE_LIST = [['1','TOP:1-20'],['2','TOP:21-40'],['3','TOP:41-50']]
VCHART_LIST = [['ML','内地篇'],['HT','港台篇'],['US','欧美篇'],['KR','韩国篇'],['JP','日本篇']]
GS_LIST = [['','全部歌手'],['Girl','女歌手'],['Boy','男歌手'],['Combo','乐队/组合']]

##################################################################################
# Routine to fetch url site data using Mozilla browser
# - delete '\r|\n|\t' for easy re.compile
# - do not delete \s <space> as some url include spaces
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
        cj.load(ignore_discard=False, ignore_expires=False)
    else:
        if not os.path.isdir(os.path.dirname(cookieFile)):
            os.makedirs(os.path.dirname(cookieFile))

    # create opener for both proxy and cookie
    opener = urllib2.build_opener(proxy_support, urllib2.HTTPCookieProcessor(cj))
    charset=''
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)

    try:
        response = opener.open(req)
        #response = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        httpdata = e.read()
    except urllib2.URLError, e:
        httpdata = "IO Timeout Error"
    else:
        httpdata = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        cj.save(cookieFile, ignore_discard=True, ignore_expires=True)
        response.close()

    httpdata = re.sub('\r|\n|\t', '', httpdata)
    match = re.compile('<meta.+?charset=["]*(.+?)"').findall(httpdata)
    if len(match):
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')

    return httpdata

##################################################################################
def get_flv_url(url):
    # http://www.flvcd.com/parse.php?flag=&format=&kw=http://3A%2F%2Fwww.yinyuetai.com%2Fvideo%2F389970&sbt=%BF%AA%CA%BCGO%21
    videoRes = int(__addon__.getSetting('video_resolution'))
    vparamap = {0:'normal', 1:'high', 2:'super'}

    p_url = "http://www.flvcd.com/parse.php?kw="+url+"&format="+vparamap.get(videoRes,0)
    for i in range(5): # Retry specified trials before giving up (seen 9 trials max)
       try: # stop xbmc from throwing error to prematurely terminate video queuing
            link = getHttpData(p_url)
            match=re.compile('下载地址：\s*<a href="(.+?)" target="_blank" class="link"').findall(link)
            if len(match): return match[0]
       except:
            pass

# facing slow response
def get_flv_urlx(url):
    videoRes = int(__addon__.getSetting('video_resolution'))
    vparamap = {0:'[流畅]', 1:'[高清]', 2:'[超清]'}

    encodedUri = base64.b64encode(url)
    p_url = "http://www.flvxz.com/getFlv.php?url="+encodedUri

    for i in range(5): # Retry specified trials before giving up (seen 9 trials max)
       try: # stop xbmc from throwing error to prematurely terminate video queuing
            link = getHttpData(p_url)
            match=re.compile('<span style="color:red">'+vparamap.get(videoRes,0)+'</span>.+?<a target="_blank" href="(.+?)">Preview this part</a>').findall(link)
            if len(match):
                return match[0]
       except:
           pass

##################################################################################
# Get imgae from local storage if available
# Fetch from Web if none found - currently disabled
##################################################################################
def get_Thumb(icon):
    if len(icon) < 2:
        return __icon__

    url = icon.split('?')[0]
    len_http = len(url.split('/')[2]) + 8
    pic = __profile__ + url[len_http:]

    if not os.path.isfile(pic):
        if not os.path.isdir(os.path.dirname(pic)):
            os.makedirs(os.path.dirname(pic))
        try:
            pic=urllib.urlretrieve(url, pic)[filename]
        except:
            pass
    return pic

##################################################################################
# Routine to extract url ID from array based on given selected filter
##################################################################################
def fetchID(dlist, idx):
    for i in range(0, len(dlist)):
        if dlist[i][1] == idx:
            return dlist[i][0]
    return ''

##################################################################################
# Routine to fetch and build video filter list
# tuple to list conversion and strip spaces    
# - 按类型  (Categories)
# - 按地区 (Countries/Areas)
# - 按年份 (Year)
# - etc
##################################################################################
def getListMV(listpage):
    match = re.compile('<ul name="area">(.+?)</ul>').findall(listpage)
    arealist = re.compile('<a href=".+?name="(.+?)".+?>[\s]*(.+?)</a>',re.DOTALL).findall(match[0])
    if len(arealist)>0:
         #arealist.pop(0)
         arealist.insert(0,['','全部地区'])
    
    match = re.compile('<ul name="artist">(.+?)</ul>').findall(listpage)
    artistlist = re.compile('<a href=".+?name="(.+?)".+?>(.+?)</a>',re.DOTALL).findall(match[0])
    if len(artistlist)>0:
         #artistlist.pop(0)
         artistlist.insert(0,['','全部类别'])

    match = re.compile('<ul name="version">(.+?)</ul>').findall(listpage)
    versionlist = re.compile('<a href=".+?name="(.+?)".+?>(.+?)</a>',re.DOTALL).findall(match[0])
    if len(versionlist)>0:
         #versionlist.pop(0)
         versionlist.insert(0,['','全部视频'])

    match = re.compile('<ul name="tag">(.+?)</ul>').findall(listpage)
    taglist = re.compile('<a href=".+?name="(.+?)".+?>(.+?)</a>',re.DOTALL).findall(match[0])
    if len(taglist)>0:
         #taglist.pop(0)
         taglist.insert(0,['','全部标签'])
    
    match = re.compile('<ul name="genre">(.+?)</ul>').findall(listpage)
    genrelist = re.compile('<a href=".+?name="(.+?)".+?>(.+?)</a>',re.DOTALL).findall(match[0])
    if len(genrelist)>0:
         #genrelist.pop(0)
         genrelist.insert(0,['','全部流派'])

    return arealist,artistlist,versionlist,taglist,genrelist

##################################################################################
# Routine to fetch and build VChart filter list
# http://www.yinyuetai.com/vchart/video-rank-week-date?area=ML&year=2012
# {"year":0,"dateCode":20111219,"periods":"07","beginDateText":"12.19","endDateText":"12.25"}
# <a href="javascript:void(0)" val="20120709">29期(07.09-07.15)</a>
##################################################################################
def getTimeList(area):
    yearlist=[]
    year = datetime.datetime.now().year
    yearlist.append(year)
    yearlist.append(year-1)

    timelist=[]
    for x in yearlist: # get 2 years worth of data only
        p_url = 'http://vchart.yinyuetai.com/vchart/video-rank-week-date?area='+area+'&year='+str(x)
        link=getHttpData(p_url)

        xlist = re.compile('{"year":.+?,"dateCode":(.+?),"periods":"(.+?)","beginDateText":"(.+?)","endDateText":"(.+?)"}').findall(link)
        if len(xlist) == 0: continue
        for datecode, period, begindate, enddate in xlist:
            xstr = period+'期('+begindate+'-'+enddate+')'
            #xstr = period+'('+begindate+'-'+enddate+')'
            timelist.append([datecode,xstr,str(x)])
    #print 'datelist', datelist
    return timelist

##################################################################################
def addDir(name,url,mode,pic,isDir=True,sn=''):
    if sn != '': sn=str(sn)+". "
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    li=xbmcgui.ListItem(sn+name,'', pic, pic)
    li.setInfo( type="Video", infoLabels={ "Title": name } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=li,isFolder=isDir)
    return ok

##################################################################################
# Yinyuetai Main Menu
##################################################################################
def MainMenu(ctl):
    vlist = [x for x in ctl[None][2]]
    j=0
    for mode in vlist:
        j+=1
        name = ctl[mode][1]
        url = 'http://www.yinyuetai.com'+ctl[mode][2]
        isDir = ctl[mode][3]
        pic = __addonicon__
        addDir(name,url,mode,pic,isDir,j)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
##################################################################################
# http://www.yinyuetai.com/vchart/include/trends-list?page=1&area=ML&trendUrl=/vchart/trends?page=1&area=ML
# http://www.yinyuetai.com/vchart/ajax/trends-list?page=2&area=ML&currentUrl=%2Fvchart%2Ftrends%3Farea%3DML%23!page%3D2
# http://www.yinyuetai.com/vchart/ajax/trends-list?page=2&area=ML&currentUrl=/vchart/trends?area=ML#!page=2
##################################################################################
def listVChart(name,area,date,timelist):   
    # fetch user specified parameters
    if area is None: area = '内地篇'
    fltrArea  = fetchID(VCHART_LIST, area)
    
    if timelist is None:
        timelist = getTimeList(fltrArea)
    if date is None: date = timelist[0][1]
    fltrDate  = fetchID(timelist, date)
    year = fltrDate[:4]
    
    # Fetch & build video titles list for user selection, highlight user selected filter  
    li = xbmcgui.ListItem('[COLOR FF00FFFF]'+name+'[/COLOR]【[COLOR FFFF0000]'+area+'[/COLOR]/[COLOR FF00FF00]'+year+'[/COLOR]/[COLOR FF5555FF]'+date+'[/COLOR]】（按此选择）')
    u = sys.argv[0] + "?mode=11&name="+urllib.quote_plus(name)+"&area="+area+"&date="+date
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    url = 'http://vchart.yinyuetai.com/vchart/ajax/vchart?date='+fltrDate+'&area='+fltrArea+'&currentUrl=/vchart/v/area='+fltrArea+'%26date='+fltrDate  
    link = getHttpData(url)
    if link == None: return

    matchli = re.compile('<li name="vlist_li".+?>(.+?)</ul></div></div></li>').findall(link)
    if len(matchli):
        totalItems=len(matchli)
        playlist=xbmc.PlayList(0) # use Music playlist for temporary storage
        playlist.clear()
        j=0
        for item in matchli:
            matchp=re.compile('<a href="(.+?)" target="_blank"><img src="(.+?)" alt="(.+?)"/>').findall(item)
            p_url = matchp[0][0]              
            p_thumb = matchp[0][1]
            p_thumb += '|Referer=http://www.yinyuetai.com'
            p_name = matchp[0][2]

            artist=re.compile('<a href=".+?/fanclub.+?target="_blank">(.+?)</a>').findall(item)
            p_artist = artist[0]
                
            matchp=re.compile('<div class="number" name="data_info">(.+?)</div>').findall(item)
            p_score = matchp[0].strip()

            matchp=re.compile('<li>发布时间：(.+?)</li>').findall(item)
            p_date = matchp[0]

            j+=1
            p_list = str(j)+'. '+p_name+' [COLOR FFFF55FF]['+p_artist+'][/COLOR][COLOR FFFFFF55] ('+p_score+') [/COLOR]['+p_date+']'
                     
            li = xbmcgui.ListItem(p_list, iconImage = '', thumbnailImage = p_thumb)
            li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_artist.split(',')})
            u = sys.argv[0]+"?mode=10"+"&name="+urllib.quote_plus(p_list)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
            playlist.add(p_url, li)

        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Routine to update video list as per user selected filters
##################################################################################
def performChangeVChart(name,area,date,timelist):
    change = False
    dialog = xbmcgui.Dialog()
    list = [x[1] for x in VCHART_LIST]        
    sel = dialog.select('悦单', list)
    if sel != -1:
        area = VCHART_LIST[sel][1]
        change = True

    list=[]
    timelist = getTimeList(VCHART_LIST[sel][0])
    year  = fetchID(timelist, date)[:4]
    for x in timelist:
        if x[2] not in list: list.append(x[2])
    if len(list) > 2:
        sel = dialog.select('年份', list)
        if sel != -1:
            year = list[sel]
            change = True
    else:
        year = list[0]

    list=[]
    list = [x[1] for x in timelist if x[2] == year]        
    sel = dialog.select(year+' 期份', list)
    if sel != -1:
        date = list[sel]
        change = True
        
    if change: listVChart(name,area,date,timelist)

##################################################################################
# Routine to update video list as per user selected filters
##################################################################################
def performChangeVChartx(name,area,page):
    change = False
    dialog = xbmcgui.Dialog()
    list = [x[1] for x in VCHART_LIST]        
    sel = dialog.select('悦单', list)
    if sel != -1:
        area = VCHART_LIST[sel][1]
        change = True

    list = [x[1] for x in PAGE_LIST]        
    sel = dialog.select('排名', list)
    if sel != -1:
        page = PAGE_LIST[sel][1]
        change = True
 
    if change: listVChart(name,area,page)
    
##################################################################################
# http://www.yinyuetai.com/index-ml
##################################################################################
def listFocusMV(name,p_url,cat):
    # fetch user specified parameters
    if cat == None: cat = '全部'
    fltrCat  = fetchID(FCS_LIST, cat)
    # url = 'http://www.yinyuetai.com/ajax/zhengliuxing?area=' + fltrCat    
    # url = 'http://www.yinyuetai.com/ajax/shoubo?area=' + fltrCat    
    url = p_url + fltrCat    

    # Fetch & build video titles list for user selection, highlight user selected filter  
    li = xbmcgui.ListItem('[COLOR FF00FFFF]'+name+'[/COLOR]【[COLOR FF00FF00]'+cat+'[/COLOR]】（按此选择）')
    u = sys.argv[0] + "?mode=12&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(p_url)+"&cat="+cat
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    link=getHttpData(url)
    if link == None: return

    playlist=xbmc.PlayList(0) # use Music playlist for temporary storage
    playlist.clear()

    # fetch and build the video series episode list
    vlist = simplejson.loads(link)
    totalItems = len(vlist)
    for i in range(0, totalItems):
        vid = str(vlist[i]['videoId'])
        #v_url  = 'http://www.yinyuetai.com/mv/get-video-info?videoId=' + vid
        v_url = 'http://www.yinyuetai.com/video/' + vid

        p_thumb = vlist[i]['image']
        p_title = vlist[i]['title'].encode('utf-8')

        p_artists = vlist[i]['artists']
        p_artist =''
        for j in range(0, len(p_artists)):
            p_artist += p_artists[j]['artistName'].encode('utf-8') + ', '

        p_list = p_name = str(i+1) + '. ' + p_title
        p_list += ' [COLOR FF00FFFF][' + p_artist[:-2] + '][/COLOR]'
       
        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_artist.split(',')})
        u = sys.argv[0]+"?mode=10"+"&name="+urllib.quote_plus(p_list)+"&url="+urllib.quote_plus(v_url)+"&thumb="+urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
        playlist.add(v_url, li)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Routine to update video list as per user selected filters
##################################################################################
def performChangeFocus(name,url,cat):
    change = False
    dialog = xbmcgui.Dialog()
    list = [x[1] for x in FCS_LIST]        
    sel = dialog.select(name, list)
    if sel != -1:
        cat = FCS_LIST[sel][1]
        change = True

    if change: listFocusMV(name,url,cat)
        
#############################################################################################
# Routine to fetch and build the video selection menu
# - selected page & filters (user selectable)
# - video items list
# - user selectable pages
# #### url parameter decode #####
# http://www.yinyuetai.com/mv/all?area=ML&artist=Girl&version=concert&tag=%E7%BB%8F%E5%85%B8&genre=1&enName=A&page=1
# area: 艺人地区       = 全部 内地 港台 欧美 韩语 日语 其他
# artist: 艺人类别   = 全部 女艺人 男艺人 乐队组合 其他 
# version: 视频分类 = 全部 官方版 演唱会 现场版 饭团视频 字幕版 其他
# tag: 视频标签         = 全部 超清 首播 热门 经典 励志 搞笑 影视 创意 爱情 伤感 热舞 翻唱 演唱会 
# genre:艺人流派       = 全部 流行 民谣 蓝调 古典 乡村 舞曲 电子 嘻哈/说唱 独立 爵士 拉丁 金属 R&B 摇滚  电影原声
#                    世界音乐 环境音乐 另类 放克 硬核 朋克 轻音乐 搞笑 儿童音乐 雷鬼 中国风 灵魂 后摇 民族风 
# enName: A-Z
# page: page number
#############################################################################################
def listAllMV(name,url,area,artist,version,tag, genre,fname,order,page,listpage):
    if listpage is None:
        link=getHttpData(url)
        if link == None: return
        match = re.compile('<div class="allCategory" id="allCategory">(.+?)<div id="mvlist" class="mv_list_vertical">').findall(link)
        listpage = match[0]
    arealist,artistlist,versionlist,taglist,genrelist = getListMV(listpage)   
    
    # fetch user specified parameters
    if area == None:
        area = '全部地区'
    fltrArea  = fetchID(arealist, area)

    if artist == None:
        artist = '全部类别'
    fltrArtist  = fetchID(artistlist, artist)
    
    if version == None:
        version = '全部视频'
    fltrVersion = fetchID(versionlist,version)

    if tag == None:
        tag = '全部标签'
    fltrTag  = fetchID(taglist, tag)

    if genre == None:
        genre = '全部流派'
    fltrGenre = fetchID(genrelist,genre )

    if fname == None: fname = '全部'
    if page is None: page = 1

    # Fetch & build video titles list for user selection, highlight user selected filter  
    url = 'http://mv.yinyuetai.com/all?&sort=pubdate&area='+fltrArea+'&artist='+fltrArtist+'&version='+fltrVersion+'&tag='+urllib.quote(fltrTag)+'&genre='+fltrGenre
    if fname <> '全部':
        url += '&enName='+fname 
    url += '&page='+str(page)
    
    li = xbmcgui.ListItem('[COLOR FF00FFFF]'+name+'[/COLOR]（第'+str(page)+'页）【[COLOR FFFF0000]'+area+'[/COLOR]/[COLOR FF00FF00]'+artist+'[/COLOR]/[COLOR FF5555FF]'+version+'[/COLOR]/[COLOR FFFFFF00]'+tag+'[/COLOR]/[COLOR FFFF55FF]'+genre+'[/COLOR]/[COLOR FFFF5555]姓:'+fname+'[/COLOR]】（按此选择）')
    u = sys.argv[0]+"?mode=13&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&area="+area+"&artist="+artist+"&area="+area+"&version="+version+"&tag="+urllib.quote(tag)+"&genre="+genre+"&fname="+urllib.quote(fname)+"&order="+"&page="+str(page)+"&listpage="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)    
    
    link=getHttpData(url)
    if link == None: return
            
    matchs=re.compile('<div id="mvlist".+?class="mv_list_vertical">(.+?)</ul>').findall(link)
    matchli=re.compile('<li>(.+?)</li>').findall(matchs[0])

    totalItems=len(matchli)
    if totalItems == 0:
        li=xbmcgui.ListItem('[COLOR FFFF0000]非常抱歉 ![/COLOR] 您选择的查询条件暂无结果')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
    else:
        playlist=xbmc.PlayList(0) # use Music playlist for temporary storage
        playlist.clear()
        j=0
        for item in matchli:
            item = item.replace('\\"','\'')
            match=re.compile('<a href="(.+?)" target="_blank">').findall(item)
            #p_url = 'http://www.yinyuetai.com' + match[0]
            p_url = match[0]
            match=re.compile('<img src="(.+?)" alt="(.+?)"').findall(item)
            p_thumb = match[0][0]
            p_thumb += '|Referer=http://www.yinyuetai.com'

            p_name = match[0][1]
            
            p_artist=''
            match=re.compile('target="_blank" class="c3" title="(.+?)">').findall(item)
            if len(match): p_artist = match[0]
               
            j +=1
            p_list = str(j)+'. '+p_name
            if p_artist: p_list+=' ['+p_artist +']'
              
            li = xbmcgui.ListItem(p_list, iconImage = '', thumbnailImage = p_thumb)
            li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_artist.split(',')})
            u = sys.argv[0]+"?mode=10"+"&name="+urllib.quote_plus(p_list)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
            playlist.add(p_url, li)
      
            # Fetch and build page selection menu
        matchp=re.compile('<div class="page-nav"(.+?)</div>').findall(link)
        if len(matchp):   
            matchp1=re.compile('<a href=".+?>([0-9]+)</a>', re.DOTALL).findall(matchp[0])    
            plist=[str(page)]
            for num in matchp1:
               if num not in plist:
                    plist.append(num)
                    li = xbmcgui.ListItem("... 第" + num + "页")
                    u = sys.argv[0]+"?mode=3&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&area="+area+"&artist="+artist+"&area="+area+"&version="+version+"&tag="+urllib.quote(tag)+"&genre="+genre+"&fname="+fname+"&order="+"&page="+num+"&listpage="+urllib.quote_plus(listpage)
                    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Routine to update video list as per user selected filters
# - 按类型  (Categories)
# - 按地区 (Areas)
# - 按年份 (Year)
# - 排序方式 (Selection Order) etc
##################################################################################
def performChangesAllMV(name,url,area,artist,version,tag, genre,fname,order,page,listpage):
    change = False
    dialog = xbmcgui.Dialog()
    arealist,artistlist,versionlist,taglist,genrelist = getListMV(listpage)
    
    if len(arealist)>0:
        list = [x[1] for x in arealist]
        sel = dialog.select('艺人地区', list)
        if sel != -1:
            area = arealist[sel][1]
            change = True         
  
    if len(artistlist)>0:
        list = [x[1] for x in artistlist]
        sel = dialog.select('艺人类别', list)
        if sel != -1:
            artist = artistlist[sel][1]
            change = True 

    if len(versionlist)>0:
        list = [x[1] for x in versionlist]
        sel = dialog.select('视频分类', list)
        if sel != -1:
            version = versionlist[sel][1]
            change = True 

    if len(taglist)>0:
        list = [x[1] for x in taglist]
        sel = dialog.select('视频标签', list)
        if sel != -1:
            tag = taglist[sel][1]
            change = True 

    if len(genrelist)>0:
        list = [x[1] for x in genrelist]
        sel = dialog.select('艺人流派', list)
        if sel != -1:
            genre = genrelist[sel][1]
            change = True 

    list = [chr(i) for i in xrange(ord('A'),ord('Z')+1)]
    list.insert(0,'全部')      
    sel = dialog.select('姓', list)
    if sel != -1:
       fname = list[sel]
       change = True

    if change:
        listAllMV(name,url,area,artist,version,tag, genre,fname,order,'1',listpage)

##################################################################################
# http://www.yinyuetai.com/lookVideo-area/ML/4
# http://www.yinyuetai.com/mv/include/recommend-list?area=ML&page=1&pageType=page
# http://mv.yinyuetai.com/ajax/recommend-list?page=1
##################################################################################
def listRecommendMV(name, page):
    if page == None: page ='1'
    p_url = "http://mv.yinyuetai.com/ajax/recommend-list?page="    
    url = p_url + page    

    # Fetch & build video titles list for user selection, highlight user selected filter  
    li = xbmcgui.ListItem('[COLOR FF00FFFF]'+name+'[/COLOR]【[COLOR FF00FF00]Page: '+page+'[/COLOR]】')
    u = sys.argv[0] + "?mode=4&name="+urllib.quote_plus(name)+"&page="+page
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    link=getHttpData(url)
    if link == None: return

    playlist=xbmc.PlayList(0) # use Music playlist for temporary storage
    playlist.clear()

    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['output']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        vid = str(vlist[i]['id'])
        #v_url  = 'http://www.yinyuetai.com/mv/get-video-info?videoId=' + vid
        v_url = 'http://www.yinyuetai.com/video/' + vid

        p_thumb = vlist[i]['bigHeadImg']
        p_title = vlist[i]['filterTitle'].encode('utf-8')
        p_artist = vlist[i]['artistName'].encode('utf-8') 

        p_list = p_name = str(i+1) + '. ' + p_title
        p_list += ' [COLOR FF00FFFF][' + p_artist + '][/COLOR]'
       
        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_artist.split(',')})
        u = sys.argv[0]+"?mode=10"+"&name="+urllib.quote_plus(p_list)+"&url="+urllib.quote_plus(v_url)+"&thumb="+urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
        playlist.add(v_url, li)
        
    # Fetch and build page selection menu
    p_itemCount= content['count']
    p_pageNum = content['pageNum']
    p_pageSize = content['pageSize']
    p_pageTotal = p_itemCount / p_pageSize 
        
    for num in range(p_pageTotal):
        page = num + 1
        if (page) != p_pageNum:
            li = xbmcgui.ListItem("... 第" + str(page) + "页")
            u = sys.argv[0] + "?mode=4&name="+urllib.quote_plus(name)+"&page="+str(page)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Routine to update video list as per user selected filters
##################################################################################
def performChangesMV(name,area,page):
    change = False
    dialog = xbmcgui.Dialog()
    list = [x[1] for x in MVR_LIST]        
    sel = dialog.select('地区', list)
    if sel != -1:
        area = MVR_LIST[sel][1]
        change = True

    list = [x[1] for x in MVR_DATE]        
    sel = dialog.select('日期', list)
    if sel != -1:
        page = MVR_DATE[sel][1]
        change = True
    
    if change: listRecommendMV(name,area,page)

##################################################################################
# http://www.yinyuetai.com/pl/playlist_newRecommend/all
##################################################################################
def listFavouriteMV(name,cat,order,page):
    # fetch user specified parameters
    if cat == None: cat = '最新推荐'
    fltrCat  = fetchID(MVF_LIST, cat)
    if order == None:
        order = '全部热门'
    fltrOrder  = fetchID(MVO_LIST, order)
    if page is None: page = 1

    if re.search('热门',cat):
        url = 'http://pl.yinyuetai.com/playlist_'+fltrCat+'/'+fltrOrder+'/'+str(page)
        li = xbmcgui.ListItem('[COLOR FF00FFFF]'+name+'[/COLOR]（第'+str(page)+'页）【[COLOR FFFF0000]'+cat+'[/COLOR]/[COLOR FF00FF00]'+order+'[/COLOR]】（按此选择）')
    else:
        url = 'http://pl.yinyuetai.com/playlist_'+fltrCat+'?page='+str(page)
        li = xbmcgui.ListItem('[COLOR FF00FFFF]'+name+'[/COLOR]（第'+str(page)+'页）【[COLOR FF00FF00]'+cat+'[/COLOR]】（按此选择）')
  
    # Fetch & build video titles list for user selection, highlight user selected filter  
    u = sys.argv[0] + "?mode=15&name="+urllib.quote_plus(name)+"&cat="+cat+"&order="+order+"&page="+str(page)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    link=getHttpData(url)
    if link == None: return

    matchs=re.compile('<div id="main">(.+?)</ul>').findall(link)
    matchli=re.compile('<div class="thumb_box">(.+?)</li>').findall(matchs[0])

    if len(matchli):        
        totalItems=len(matchli)
        playlist=xbmc.PlayList(0) # use Music playlist for temporary storage
        playlist.clear()
        j=0
        for item in matchli:
            match=re.compile('<a href="(.+?)" target="_blank" title="(.+?)">[\s]*<img src="(.+?)"').findall(item)
            #p_url = 'http://www.yinyuetai.com' + match[0][0]
            p_url = match[0][0]
            p_name = match[0][1]
            p_name = p_name.replace("&lt;", "<").replace("&gt;", ">")
            p_thumb = match[0][2]
            p_thumb += '|Referer=http://www.yinyuetai.com'
            
            p_artist=''
            match=re.compile('target="_blank">(.+?)</a>：').findall(item)
            if len(match): p_artist = match[0]
               
            j+=1
            p_list = str(j)+'. '+p_name
            if p_artist: p_list+=' ['+p_artist +']'
            
            li = xbmcgui.ListItem(p_list, iconImage = '', thumbnailImage = p_thumb)
            li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_artist.split(',')})
            u = sys.argv[0]+"?mode=10"+"&name="+urllib.quote_plus(p_list)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
            playlist.add(p_url, li)
    
        # Fetch and build page selection menu
        matchp=re.compile('<div class="page-nav">(.+?)</div>').findall(link)   
        if len(matchp):   
            matchp1=re.compile('<a href=".+?>([0-9]+)</a>', re.DOTALL).findall(matchp[0])    
            plist=[str(page)]
            for num in matchp1:
                if num not in plist:
                    plist.append(num)
                    li = xbmcgui.ListItem("... 第" + num + "页")
                    u = sys.argv[0] + "?mode=5&name="+urllib.quote_plus(name)+"&cat="+cat+"&order="+order+"&page="+num
                    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
##################################################################################
# Routine to update video list as per user selected filters
##################################################################################
def performChangeFavourite(name,cat,order,page):
    change = False
    dialog = xbmcgui.Dialog()
    list = [x[1] for x in MVF_LIST]        
    sel = dialog.select('悦单', list)
    if sel != -1:
        cat = MVF_LIST[sel][1]
        change = True

    if re.search('热门',cat):
        list = [x[1] for x in MVO_LIST]        
        sel = dialog.select('排序方式', list)
        if sel != -1:
           order = MVO_LIST[sel][1]
           change = True
           
    if change: listFavouriteMV(name,cat,order,1)

##################################################################################
# http://www.yinyuetai.com/fanAll?area=ML&property=Girl&enName=F&page=1
##################################################################################
def listArtist(name,area,geshou,fname,page):
    # fetch user specified parameters
    if area == None: area = '全部地区'
    fltrArea  = fetchID(AREA_LIST, area)
    if geshou == None:
        geshou = '全部歌手'
    fltrGeshou  = fetchID(GS_LIST, geshou)
    
    if fname == None: fname = '全部'
    if page is None: page = 1
    
    # Fetch & build video titles list for user selection, highlight user selected filter  
    url = 'http://www.yinyuetai.com/fanAll?area='+fltrArea+'&property='+fltrGeshou
    if fname <> '全部':
        url += '&enName='+fname 
    url += '&page='+str(page)

    li = xbmcgui.ListItem('[COLOR FF00FFFF]'+__addonname__+'[/COLOR]（第'+str(page)+'页）【[COLOR FFFF0000]'+area+'[/COLOR]/[COLOR FF00FF00]'+geshou+'[/COLOR]/[COLOR FFFF5555]姓:'+fname+'[/COLOR]】（按此选择）')
    u = sys.argv[0]+"?mode=16&name="+urllib.quote_plus(name)+"&area="+urllib.quote_plus(area)+"&geshou="+urllib.quote_plus(geshou)+"&fname="+fname+"&page="+str(page)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)    
    
    link=getHttpData(url)
    if link == None: return
    
    match=re.compile('<span class="groupcover"(.+?)</li>').findall(link)
    if len(match):        
        totalItems = len(match)
        for i in range(0, len(match)):
            match1 = re.compile('fanid=.+?<a href="(.+?)"').findall(match[i])
            p_url1 = match1[0]
            artistid = p_url1.split('/')[2]
            p_url = 'http://www.yinyuetai.com/fanclub/mv-all/'+artistid+'/toNew'
        
            match1 = re.compile('<img.+?src="(.+?)"/>').findall(match[i])
            if match1: 
                p_thumb = match1[0]
                p_thumb += '|Referer=http://www.yinyuetai.com'
            else: p_thumb =''          

            match1 = re.compile('<div class="info">.+?<a href="(.+?)"').findall(match[i])
            p_url2 = match1[0]

            match1 = re.compile('class="song" title="(.+?)">').findall(match[i])
            p_name = match1[0]
               
            p_list = str(i+1)+'. '+p_name
            p_name += ' [[COLOR FFFF5555]'+area+'[/COLOR]/[COLOR FF5555FF]'+geshou+'[/COLOR]]'
                
            li = xbmcgui.ListItem(p_list, iconImage = '', thumbnailImage = p_thumb)  #name,area,geshou,fname,page
            u = sys.argv[0]+"?mode=7"+"&name="+urllib.quote_plus(p_name)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)+"&page=1"
            li.setInfo(type = "Video", infoLabels = {"Title":p_name})
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
   
        matchp=re.compile('<div class="page-nav">(.+?)</div>').findall(link)   
        if len(matchp):   
            matchp1=re.compile('<a href=".+?>([0-9]+)</a>', re.DOTALL).findall(matchp[0])    
            plist=[str(page)]
            for num in matchp1:
                if num not in plist:
                    plist.append(num)
                    li = xbmcgui.ListItem("... 第" + num + "页")
                    u = sys.argv[0]+"?mode=6"+"&name="+urllib.quote_plus(p_name)+"&area="+urllib.quote_plus(area)+"&geshou="+urllib.quote_plus(geshou)+"&fname="+fname+"&page="+num
                    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# http://www.yinyuetai.com/fanAll?area=ML&property=Girl&page=1
# http://www.yinyuetai.com/fanclub/27
##################################################################################
def listArtistMV(name,url,thumb,page):
    # fetch user specified parameters
    if page is None: page = 1
    p_url = url+'/?page='+str(page)
    
    li = xbmcgui.ListItem('[COLOR FF00FFFF]'+__addonname__+'[/COLOR]（第'+str(page)+'页）【[COLOR FF00FF00]'+name+'[/COLOR]】')
    # Fetch & build video titles list for user selection, highlight user selected filter  
    u = sys.argv[0]+"?mode=7&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(thumb)+"&page="+str(page)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    link=getHttpData(p_url)
    if link == None: return

    vlist=re.compile('<div class="mv_list"><ul>(.+?)</ul></div>').findall(link)
    match=re.compile('<div class="thumb"><a target="_blank" title="(.+?)" href="(.+?)"><img.+?src="(.+?)"').findall(vlist[0])    

    if len(match):        
        totalItems=len(match)
        playlist=xbmc.PlayList(0) # use Music playlist for temporary storage
        playlist.clear()
        j=0

        artist=re.compile('<h1>(.+?)</h1>').findall(link)
        p_artist = artist[0]
        for p_name,p_url,p_thumb in match:
            p_url = 'http://www.yinyuetai.com' + p_url              
            j+=1
            p_list = str(j)+'. '+p_name+' ['+p_artist +']'
            
            #p_thumb += '|User-Agent='+UserAgent
            p_thumb += '|Referer=http://www.yinyuetai.com'
                
            li = xbmcgui.ListItem(p_list, iconImage = '', thumbnailImage = p_thumb)
            li.setInfo(type = "Video", infoLabels = {"Title":p_list, "Artist":p_artist.split(',')})
            u = sys.argv[0]+"?mode=10"+"&name="+urllib.quote_plus(p_list)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
            playlist.add(p_url, li)
    
        # Fetch and build page selection menu
        matchp=re.compile('<div class="page-nav">(.+?)</div>').findall(link)   
        if len(matchp):   
            matchp1=re.compile('<a href=".+?>([0-9]+)</a>', re.DOTALL).findall(matchp[0])    
            plist=[str(page)]
            for num in matchp1:
                if num not in plist:
                    plist.append(num)
                    li = xbmcgui.ListItem("... 第" + num + "页")
                    u = sys.argv[0]+"?mode=7"+"&name="+urllib.quote_plus(name)+"&url="+urllib.quote_plus(url)+"&thumb="+urllib.quote_plus(thumb)+"&page="+num
                    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Routine to update video list as per user selected filters
##################################################################################
def performChangeGs(name,area,geshou,fname,page):
    change = False
    dialog = xbmcgui.Dialog()
    list = [x[1] for x in AREA_LIST]        
    sel = dialog.select('地区', list)
    if sel != -1:
        area = AREA_LIST[sel][1]
        change = True

    list = [x[1] for x in GS_LIST]        
    sel = dialog.select('歌手', list)
    if sel != -1:
       geshou = GS_LIST[sel][1]
       change = True

    list = [chr(i) for i in xrange(ord('A'),ord('Z')+1)]
    list.insert(0,'全部')      
    sel = dialog.select('姓', list)
    if sel != -1:
       fname = list[sel]
       change = True

    if change:listArtist(name,area,geshou,fname,1)

##################################################################################
# http://hc.yinyuetai.com/uploads/videos/common/D15E013E4B0CA991DBBD9FCFDECDE167.flv?sc=441d14c6ded1de37&br=776&ptp=mv&rd=yinyuetai.com&json=1
##################################################################################
def get_vurl(url):
    link=getHttpData(url)
    if link == None: 
        return url
    
    match=re.compile('\[\{"videoUrl":"(.+?)"').findall(link)
    if len(match):
        purl = match[0].replace("\\u003d", '=') + "&br=684&ptp=mv&rd=yinyuetai.com&json=1"
        link=getHttpData(purl)
        if link == None: 
            return url
        else:
            matchv=re.compile('"url":"(.+?)"').findall(link)
            vurl = re.sub('\\\\\\\\\u003d', '=', matchv[0])
            return vurl 
    else:
        return url

##################################################################################
# Continuous Player start playback from user selected video
# User backspace to previous menu will not work - playlist = last selected
##################################################################################
def playVideo(name,url,thumb):
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
        # abort if 5 or more access failures and no video playback
        if (errcnt >= ERR_MAX and k == 0):
            pDialog.close() 
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '无法播放：多次未匹配到视频文件，请选择其它视频')
            break 

        if x < v_pos: continue
        p_item=playlistA.__getitem__(x)
        p_url=p_item.getfilename(x)
        p_list =p_item.getdescription(x)

        # li = xbmcgui.ListItem(p_list)
        li = p_item # pass all li items including the embedded thumb image
        li.setInfo(type = "Video", infoLabels = {"Title":p_list})   

        if (pDialog.iscanceled()):
            pDialog.close() 
            x = psize # quickily terminate any old thread
            err_cnt = 0
            return

        pDialog.update(errcnt*100/ERR_MAX + 100/ERR_MAX/TRIAL)        
        if re.search('http://www.yinyuetai.com/', p_url) or re.search('http://v.yinyuetai.com/video/', p_url):
            v_url = get_flv_url(p_url)
            if len == None:
                errcnt += 1 # increment consequetive unsuccessful access
                print "error cnt: " + str(errcnt)
                continue
            playlistA.remove(p_url) # remove old url
            playlistA.add(v_url, li, x)  # keep a copy of v_url in Audio Playlist

        elif re.search('http://v.yinyuetai.com/playlist', p_url):
            v_url = get_vurl(p_url)
            if v_url == None:
                errcnt += 1 # increment consequetive unsuccessful access
                continue
            playlistA.remove(p_url) # remove old url
            playlistA.add(v_url, li, x)  # keep a copy of v_url in Audio Playlist
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
def playVideoX(name,url,thumb):
    v_url = get_flv_url(url)
    if v_url:
        playlist=xbmc.PlayList(1)
        playlist.clear()
        listitem = xbmcgui.ListItem(name, thumbnailImage = thumb)
        listitem.setInfo(type="Video",infoLabels={"Title":name})
        playlist.add(v_url, listitem)
        xbmc.Player().play(playlist)
    else:
        if link.find('该视频为加密视频')>0:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '无法播放：该视频为加密视频')
        elif link.find('解析失败，请确认视频是否被删除')>0:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '无法播放：该视频或为收费节目')

##################################################################################
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param

##################################################################################

params=get_params()
url=None
mode=None
name=None
area=None
artist=None
version=None
tag=None
genre=None
geshou=None
cat=None
fname=None
order=None
date=None
page=None
thumb=None
listpage=None
timelist=None

try:
    mode=int(params["mode"])
except:
    pass
try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    area=urllib.unquote_plus(params["area"])
except:
    pass
try:
    artist=urllib.unquote_plus(params["artist"])
except:
    pass
try:
    version=urllib.unquote_plus(params["version"])
except:
    pass
try:
    tag=urllib.unquote_plus(params["tag"])
except:
    pass
try:
    genre=urllib.unquote_plus(params["genre"])
except:
    pass
try:
    fname=urllib.unquote_plus(params["fname"])
except:
    pass
try:
    cat=urllib.unquote_plus(params["cat"])
except:
    pass
try:
    geshou=urllib.unquote_plus(params["geshou"])
except:
    pass
try:
    order=urllib.unquote_plus(params["order"])
except:
    pass
try:
    date=urllib.unquote_plus(params["date"])
except:
    pass
try:
    thumb=urllib.unquote_plus(params["thumb"])
except:
    pass
try:
    page=urllib.unquote_plus(params["page"])
except:
    pass
try:
    listpage=urllib.unquote_plus(params["listpage"])
except:
    pass
try:
    timelist=urllib.unquote_plus(params["timelist"])
except:
    pass
ctl = {
            None : ('MainMenu(ctl)','音悦台MV',(2,8,1,3,4,5,6)),
            1    : ('listVChart(name,area,date,timelist)','音悦台 - 音悦V榜','',True),
            2    : ('listFocusMV(name,url,cat)','音悦台 - MV首播','/ajax/shoubo?area=',True),
            3    : ('listAllMV(name,url,area,artist,version,tag, genre,fname,order,page,listpage)','音悦台 - 全部MV','/mv/all',True),           
            4    : ('listRecommendMV(name, page)','音悦台 - 推荐MV','/ajax/recommend-list?page=1',True),   
            5    : ('listFavouriteMV(name,cat,order,page)','音悦台 - 全部悦单','/pl/playlist_newRecommend',True), 
            6    : ('listArtist(name,area,geshou,fname,page)','音悦台 - 歌手','/fanAll',True),
            7    : ('listArtistMV(name,url,thumb,page)','显示歌手MV','/fanAll',True),
            8    : ('listFocusMV(name,url,cat)','音悦台 - 正在流行','/ajax/zhengliuxing?area=',True),
            9    : ('listFocusMV(name,url,cat)','音悦台 - V榜','/ajax/vchart?area=',True),
            10   : ('playVideo(name,url,thumb)',''),
            
            11   : ('performChangeVChart(name,area,date,timelist)',''),
            12   : ('performChangeFocus(name,url,cat)',''),
            13   : ('performChangesAllMV(name,url,area,artist,version,tag, genre,fname,order,page,listpage)',''),
            14   : ('performChangesMV(name,area,page)',''),
            15   : ('performChangeFavourite(name,cat,order,page)',''),
            16   : ('performChangeGs(name,area,geshou,fname,page)','')
      }
exec(ctl[mode][0])

