# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, urlparse, httplib, re, string, sys, os, gzip, StringIO
import cookielib, datetime, time
import ChineseKeyboard
try:
    import simplejson
except ImportError:
    import json as simplejson
       
# Plugin constants 
__addonname__ = "搜狐视频(SoHu)"
__addonid__   = "plugin.video.sohuvideo"
__addon__     = xbmcaddon.Addon(id=__addonid__)
__settings__  = xbmcaddon.Addon(id=__addonid__)
__profile__   = xbmc.translatePath( __settings__.getAddonInfo('profile') )
cookieFile    = __profile__ + 'cookies.sohu'

RATE_LIST = [['超清','3'], ['高清','2'], ['普通','1'], ]
CHANNEL_LIST = [['电影','100'],['电视剧','101'],['动漫','115'],['综艺','106'],['纪录片','107'],['音乐','121'],['教育','119'],['新闻 ','122'],['娱乐 ','112'],['星尚 ','130']]
ORDER_LIST = [['7','周播放最多'],['5','日播放最多'],['1','总播放最多'],['3','最新发布'],['4','评分最高']]

LIVEID_URL = 'http://live.tv.sohu.com/live/player_json.jhtml?lid=%s&type=1'

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

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
    charset=''
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    try:
        response = opener.open(req)
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
# Routine to extract url ID from array based on given selected filter
##################################################################################
def searchDict(dlist,idx):
    for i in range(0,len(dlist)):
        if dlist[i][0] == idx:
            return dlist[i][1]
    return ''

##################################################################################
# Routine to fetch and build video filter list
# tuple to list conversion and strip spaces    
# - 按类型  (Categories)
# - 按地区 (Countries/Areas)
# - 按年份 (Year)
# - etc
##################################################################################
def getcatList(listpage):
    match = re.compile('<dt>类别：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    catlist = re.compile('p2(.*?)_p3.+?>(.+?)</a>', re.DOTALL).findall(match[0])
    return catlist

def getareaList(listpage):
    match = re.compile('<dt>地区：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    arealist = re.compile('p3(.*?)_p4.+?>(.+?)</a>', re.DOTALL).findall(match[0])
    return arealist

def getyearList(listpage):    
    match = re.compile('<dt>年份：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    yearlist = re.compile('p4(.*?)_p5.+?>(.+?)</a>', re.DOTALL).findall(match[0])
    return yearlist

def getlabelList(listpage): # label & area share the same _P3   
    match = re.compile('<dt>类别：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    catlist = re.compile('p2(.*?)_p3.+?>(.+?)</a>', re.DOTALL).findall(match[0])
    return catlist

def getList16(listpage):    
    match = re.compile('<dt>篇幅：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    pflist = re.compile('p5(.*?)_p6.+?>(.+?)</a>', re.DOTALL).findall(match[0])
    match = re.compile('<dt>年龄：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    nllist = re.compile('p6(.*?)_p7.+?>(.+?)</a>', re.DOTALL).findall(match[0])
    return pflist,nllist
           
def getList24(listpage):
    match = re.compile('<dt>类别：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    lxlist = re.compile('p5(.*?)_p6.+?html">(.+?)</a>', re.DOTALL).findall(match[0])
    match = re.compile('<dt>语言：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    yylist = re.compile('_p101_p11(.+?).html">(.+?)</a>', re.DOTALL).findall(match[0])
    if len(yylist)>0: yylist.insert(0,['','全部'])
    match = re.compile('<dt>地区：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    arealist = re.compile('p3(.*?)_p4.+?>(.+?)</a>', re.DOTALL).findall(match[0])
    match = re.compile('<dt>风格：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    fglist = re.compile('p2(.*?)_p3.+?>(.+?)</a>', re.DOTALL).findall(match[0])
    return lxlist,yylist,arealist,fglist

##################################################################################
# Routine to fetch & build Sohu 网络 main menu
# - Video Search
# - 电视直播
# - video list as per [CHANNEL_LIST]
##################################################################################    
def rootList():
    # force sohu to give cookie; must use cookie for some categories fast response else timeout
    #http://pv.sohu.com/suv/?t?=1342163482 447275_1920_1200?r?=
    ticks = int(time.time())
    url_cookie = 'http://pv.sohu.com/suv/?t?='+str(ticks)+'866725_1920_1080?r?='
    link = getHttpData(url_cookie)

    li = xbmcgui.ListItem('[COLOR F0F0F0F0]0. Sohu 搜库网:[/COLOR][COLOR FF00FF00]【请输入搜索内容】[/COLOR]')
    u=sys.argv[0]+"?mode=21"
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    name='电视直播'
    li=xbmcgui.ListItem('1. ' + name)
    u=sys.argv[0]+"?mode=10&name="+urllib.quote_plus(name)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
    
    i = 1
    for name, id in CHANNEL_LIST:
        i += 1
        if id in ('130'): order = '1'
        else: order = '7'
        li=xbmcgui.ListItem(str(i) + '. ' + name)
        u=sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&page=1"+"&cat="+"&area="+"&year="+"&p5="+"&p6="+"&p11="+"&order="+order 
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Routine to fetch and build the video selection menu
# - selected page & filters (user selectable)
# - video items list
# - user selectable pages
# ########### url parameter decode ##############
# http://so.tv.sohu.com/list_p1100_p2_p3_p4_p5_p6_p7_p8_p9.html
# p1: 分类: 100=电影;电视剧=101;动漫=115;综艺=106 etc
# p2: 类型： 全部 爱情 动作 喜剧 科幻 战争 恐怖 风月 剧情 歌舞 动画 纪录   
# p3: 产地： 全部 华语 好莱坞 欧洲 日本 韩国 其他
# p4: 年份： 全部 2012 2011
# p5: 篇幅(动漫 )：全部 电影 连续剧 预告片 其他
# p6: 年龄(动漫 )：全部 5岁以下 5岁-12岁 13岁-18岁 18岁以上
# p7: 相关程度: 5=日播放最多;7=周播放最多;1=总播放最多;3=最新发布;4=评分最高    
# p8: 付费： 0=全部;2=免费;1=VIP;3=包月;4=点播
# p9: 状态: 2d2=全部;2d1=正片;2d3=非正片
# p10: page
# p11:
##################################################################################
def progList(name,id,page,cat,area,year,p5,p6,p11,order):
    url = 'http://so.tv.sohu.com/list_p1'+id+'_p2'+cat+'_p3'+area+'_p4'+year+'_p5'+p5+'_p6'+p6+'_p7'+order
    if name in ('电影','电视剧'):
        url +='_p82_p9_2d1'
    else:
        url +='_p8_p9'
    url += '_p10'+page+'_p11'+p11+'.html'

    currpage = int(page)
    link = getHttpData(url)
    match = re.compile('<div class="ssPages area">(.+?)</div>', re.DOTALL).findall(link)
    if not match:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__, '没有符合此条件的视频！')
    else:
        matchpages = re.compile('<a href="[^"]*">(\d+)</a>', re.DOTALL).findall(match[0])
        totalpages = int(matchpages[-1])
        if totalpages < currpage:
            totalpages = currpage
        match = re.compile('<div class="sort-type">(.+?)</div>', re.DOTALL).findall(link)
        if len(match):
            listpage = match[0]
        else:
            listpage = ''

        match = re.compile('<li>(.+?)</li>', re.DOTALL).findall(link)
        totalItems = len(match) + 1
        if currpage > 1: totalItems = totalItems + 1
        if currpage < totalpages: totalItems = totalItems + 1
        lxstr=''
        if id not in ('121'):
            if id in ('130'):
                catlist= getlabelList(listpage)
            else:
                catlist= getcatList(listpage)
            lxstr += '[COLOR FFFF0000]'
            if cat:
                lxstr += searchDict(catlist,cat)
            else:    
                lxstr += '全部类型'
            lxstr += '[/COLOR]'

        if id in ('100','101','106'):          
            lxstr += '/[COLOR FF00FF00]'
            arealist= getareaList(listpage)
            if area:
                lxstr += searchDict(arealist,area)
            else:
                lxstr += '全部地区'
            lxstr += '[/COLOR]'

        if id=='115':
            lxstr += '/[COLOR FFFFFF00]'
            pflist,nllist=getList16(listpage)
            if p5:
                lxstr += searchDict(pflist,p5)
            else:
                lxstr += '全部篇幅'  
            lxstr += '[/COLOR]/[COLOR FF00FF00]'
            if p6:
                lxstr += searchDict(nllist,p6)
            else:
                lxstr += '全部年龄'
            lxstr += '[/COLOR]'

        if id=='121': 
            lxstr += '[COLOR FFFF0000]'
            lxlist,yylist,arealist,fglist=getList24(listpage)
            if p5:
                lxstr += searchDict(lxlist,p5)
            else:
                lxstr += '全部类型'            
            lxstr += '[/COLOR]/[COLOR FF00FF00]'
            if p11:
                lxstr += searchDict(yylist,p11)
            else:
                lxstr += '全部语言'
            lxstr += '[/COLOR]/[COLOR FFFF5555]'
            if area:
                lxstr += searchDict(arealist,area)
            else:
                lxstr += '全部地区'
            lxstr += '[/COLOR]/[COLOR FFFF00FF]'
            if cat:
                lxstr += searchDict(fglist,cat)
            else:
                lxstr += '全部风格'
            lxstr += '[/COLOR]'
        
        if id in ('100','101','115','121'):
            lxstr += '/[COLOR FF5555FF]'
            yearlist = getyearList(listpage)
            if year=='':
                lxstr += '全部年份'
            elif year in ('80','90'):
                lxstr += year+'年代'
            elif year == '100':
                lxstr += '更早年代'
            else:
                lxstr += year+'年'
            lxstr += '[/COLOR]'
                
        li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）【' + lxstr + '/[COLOR FF00FFFF]' + searchDict(ORDER_LIST,order) + '[/COLOR]】（按此选择）')
        u = sys.argv[0]+"?mode=4&name="+urllib.quote_plus(name)+"&id="+id+"&cat="+cat+"&area="+area+"&year="+year+"&p5="+p5+"&p6="+p6+"&p11="+p11+"&order="+"&listpage="+urllib.quote_plus(listpage)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)

        for i in range(0,len(match)):
            match1 = re.compile('<a href="([^"]+)" title="([^"]+)" target="_blank"', re.DOTALL).search(match[i])
            i_url = 1
            i_name = 2
            if not match1:
                match1 = re.compile('<a title="([^"]+)" target="_blank" href="([^"]+)"', re.DOTALL).search(match[i])
                i_url = 2
                i_name = 1
            p_name = match1.group(i_name)
            p_url = match1.group(i_url)
            match1 = re.compile('<img .*?src="([^"]+)"', re.DOTALL).search(match[i])
            p_thumb = match1.group(1)
            p_rating = 0
            p_votes = ''
            p_director = ''
            p_genre = ''
            match1 = re.compile('<p class="lh-info">(.+?)</p>').search(match[i])
            if match1:
                p_plot = match1.group(1)
            else:
                p_plot = ''
            p_year = 0
 
            if id in ('101','115','106','107','119'):
                p_dir = True
                mode = 2
            else:
                p_dir = False
                mode = 3

            match1 = re.compile('<span class="maskTx">(.+?)</span>').search(match[i])
            if match1:
                p_name1 = p_name + ' [' + match1.group(1) + ']'
            else:
                p_name1 = p_name
            if match[i].find('<span class="rl-phua"></span>')>0:
                p_name1 += ' [片花]'
            elif match[i].find('<span class="rl-rep"></span>')>0:
                p_name1 += ' [预告]'
            elif match[i].find('<span class="rl-fuf"></span>')>0:
                p_name1 += ' [付费]'
            if match[i].find('<a title="超清" class="super">')>0:
                p_name1 += ' [超清]'
                p_res = 2
            elif match[i].find('<a title="原画" class="origin">')>0:
                p_name1 += ' [原画]'
                p_res = 1
            else:
                p_res = 0

            li = xbmcgui.ListItem(str(i + 1) + '. ' + p_name1, iconImage = '', thumbnailImage = p_thumb)
            u = sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(p_name)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)+"&id="+urllib.quote_plus(str(i))
            li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Rating":p_rating, "Votes":p_votes})
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, p_dir, totalItems)
    
        # Fetch and build user selectable page number
        if matchpages:
            for num in matchpages:
                li = xbmcgui.ListItem("... 第" + num + "页")
                u=sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+id+"&page="+str(num)+"&cat="+cat+"&area="+area+"&year="+year+"&p5="+p5+"&p6="+p6+"&p11="+p11+"&order="+order 
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Routine to fetch and build the video series selection menu
# - for 电视剧  & 动漫
# - selected page & filters (user selectable)
# - Video series list
# - user selectable pages
##################################################################################
def seriesList(name, id,url,thumb):
    link = getHttpData(url)
    if url.find('.shtml')>0:
        match0 = re.compile('var vrs_playlist_id="(.+?)";', re.DOTALL).findall(link)
        #print 'vrs_playlist_id:' + match0.groups()
        link = getHttpData('http://hot.vrs.sohu.com/vrs_videolist.action?playlist_id='+match0[0])
        match = re.compile('"videoImage":"(.+?)",.+?"videoUrl":"(.+?)".+?"videoOrder":"(.+?)",', re.DOTALL).findall(link)
        totalItems = len(match)

        for p_thumb,p_url,p_order in match:
            p_name = '%s第%s集' % (name, p_order)
            li = xbmcgui.ListItem(p_name, iconImage = '', thumbnailImage = p_thumb)
            li.setInfo(type="Video",infoLabels={"Title":p_name, "episode":int(p_order)})
            u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(p_name) + "&url=" + urllib.quote_plus(p_url)+ "&thumb=" + urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)       
    else:
        match0 = re.compile('var pid\s*=\s*(.+?);', re.DOTALL).findall(link)
        if len(match0)>0:
            # print 'pid=' + match0[0]
            pid = match0[0].replace('"','')
            match0 = re.compile('var vid\s*=\s*(.+?);', re.DOTALL).findall(link)
            vid = match0[0].replace('"','')
            if vid == '0':
                dialog = xbmcgui.Dialog()
                ok = dialog.ok(__addonname__,'您当前选择的节目暂不能播放，请选择其它节目')
                return
            obtype = '2'
            link = getHttpData("http://search.vrs.sohu.com/avs_i"+vid+"_pr"+pid+"_o"+obtype+"_n_p1000_chltv.sohu.com.json")
            data = link.replace('var video_album_videos_result=','').decode('raw_unicode_escape')
            match = simplejson.loads(data)['videos']
            totalItems = len(match)
            for item in match:
                p_name = item['videoName'].encode('utf-8')
                p_time = item['videoPublishTime']
                p_order = item['playOrder'].encode('utf-8')
                p_url = item['videoUrl'].encode('utf-8')
                p_thumb = item['videoBigPic'].encode('utf-8')
                p_date = datetime.date.fromtimestamp(float(p_time)/1000).strftime('%d.%m.%Y')
                li = xbmcgui.ListItem(p_name, iconImage = '', thumbnailImage = p_thumb)
                li.setInfo(type="Video",infoLabels={"Title":p_name, "date":p_date, "episode":int(p_order)})
                u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(p_name) + "&url=" + urllib.quote_plus(p_url)+ "&thumb=" + urllib.quote_plus(p_thumb)
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
        else:
            match = re.compile('<a([^>]*)><IMG([^>]*)></a>',re.I).findall(link)
            thumbDict = {}
            for i in range(0, len(match)):
                p_url = re.compile('href="(.+?)"').findall(match[i][0])
                if len(p_url)>0:
                    p_url = p_url[0]
                else:
                    p_url = match[i][0]
                p_thumb = re.compile('src="(.+?)"').findall(match[i][1])
                if len(p_thumb)>0:
                    p_thumb = p_thumb[0]
                else:
                    p_thumb = match[i][1]
                thumbDict[p_url]=p_thumb
            #for img in thumbDict.items():
            url = 'http://so.tv.sohu.com/mts?c=2&wd=' + urllib.quote_plus(name.decode('utf-8').encode('gbk'))
            html = getHttpData(url)
            match =  re.compile('class="serie-list(.+?)</div>').findall(html)
            if not match:
                return
            items = re.compile('<a([^>]*)>(.+?)</a>',re.I).findall(match[0])
            totalItems = len(items)
            for item in items:
                if item[1]=='展开>>':
                    continue
                href = re.compile('href="(.+?)"').findall(item[0])
                if len(href)>0:
                    p_url = href[0]
                    urlKey = re.compile('u=(http.+?.shtml)').search(p_url)
                    if urlKey:
                        urlKey = urllib.unquote(urlKey.group(1))
                    else:
                        urlKey = p_url
                    #print urlKey
                    p_thumb = thumb
                    try:
                        p_thumb = thumbDict[urlKey]
                    except:
                        pass
                    #title = re.compile('title="(.+?)"').findall(item)
                    #if len(title)>0:
                        #p_name = title[0]
                    p_name = name + '第' + item[1].strip() + '集'
                    li = xbmcgui.ListItem(p_name, iconImage = p_thumb, thumbnailImage = p_thumb)
                    u = sys.argv[0] + "?mode=3&name="+urllib.quote_plus(p_name)+"&id="+id+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)
                    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Routine to update video list as per user selected filters
# - 按类型  (Categories)
# - 按地区 (Areas)
# - 按年份 (Year)
# - 排序方式 (Selection Order) etc
##################################################################################
def performChanges(name,id,cat,area,year,p5,p6,p11,order,listpage):
    change = False
    dialog = xbmcgui.Dialog()
    if id not in ('121'):
        if id in ('130'):
            catlist= getlabelList(listpage)
        else:
            catlist= getcatList(listpage)
        if len(catlist)>0:
            list = [x[1] for x in catlist]
            sel = dialog.select('类型', list)
            if sel != -1:
                if sel == 0:
                    cat = ''
                else:
                    cat = catlist[sel][0]
                change = True
            
    if id in ('100','101','106'):
        arealist=getareaList(listpage)
        if len(arealist)>0:
            list = [x[1] for x in arealist]
            sel = dialog.select('地区', list)
            if sel != -1:
                if sel == 0:
                    area = ''
                else:
                    area = arealist[sel][0]
                change = True       
    if id=='115':
        pflist,nllist=getList16(listpage)
        if len(pflist)>0:
            list = [x[1] for x in pflist]
            sel = dialog.select('篇幅', list)
            if sel != -1:
                if sel == 0:
                    p5 = ''
                else:
                    p5 = pflist[sel][0]
                change = True 
        if len(nllist)>0:
            list = [x[1] for x in nllist]
            sel = dialog.select('年龄', list)
            if sel != -1:
                if sel == 0:
                    p6 = ''
                else:
                    p6 = nllist[sel][0]
                change = True
    if id=='121': 
        lxlist,yylist,arealist,fglist=getList24(listpage)
        if len(lxlist)>0:
            list = [x[1] for x in lxlist]
            sel = dialog.select('类型', list)
            if sel != -1:
                if sel == 0:
                    p5 = ''
                else:
                    p5 = lxlist[sel][0]
                change = True         
        if len(yylist)>0:
            list = [x[1] for x in yylist]
            sel = dialog.select('语言', list)
            if sel != -1:
                if sel == 0:
                    p11 = ''
                else:
                    p11 = yylist[sel][0]
                change = True 
        if len(arealist)>0:
            list = [x[1] for x in arealist]
            sel = dialog.select('地区', list)
            if sel != -1:
                if sel == 0:
                    area = ''
                else:
                    area = arealist[sel][0]
                change = True 
        if len(fglist)>0:
            list = [x[1] for x in fglist]
            sel = dialog.select('风格', list)
            if sel != -1:
                if sel == 0:
                    cat = ''
                else:
                    cat = fglist[sel][0]
                change = True 

    if id in ('100','101','115','121'):
        yearlist=getyearList(listpage)
        if len(yearlist)>0:
            list = [x[1] for x in yearlist]
            sel = dialog.select('年份', list)
            if sel != -1:
                if sel == 0:
                    year = ''
                else:
                    year = yearlist[sel][0]
                change = True

    list = [x[1] for x in ORDER_LIST]
    sel = dialog.select('排序方式', list)
    if sel != -1:
        order = ORDER_LIST[sel][0]
        change = True
    if change:
        progList(name,id,'1',cat,area,year,p5,p6,p11,order)

#################################################################################
# Get user input for Sohu site search
##################################################################################
def searchSohu():
    result=''
    keyboard = ChineseKeyboard.Keyboard('','请输入搜索内容')
    xbmc.sleep( 1500 )
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        p_url = 'http://so.tv.sohu.com/mts?chl=&tvType=-2&wd='
        url = p_url + urllib.quote_plus(keyword.decode('utf-8').encode('gb2312'))
        sohuSearchList(keyword,url,'1')
    else: return
        
##################################################################################
# Routine to search Sohu site based on user given keyword for:
# http://so.tv.sohu.com/mts?chl=&tvType=-2&wd=love&whole=1&m=1&box=1&c=100&o=1&p=2
# c: 类型：''=全部 100=电影 101=电视剧 106=综艺 121=音乐 122=新闻 112=娱乐 0=其它 
# o:排序方式： ''=相关程度 1=最多播放 3=最新发布
##################################################################################
def sohuSearchList(name, url, page):
    # construct url based on user selected item
    p_url = url + '&fee=0&whole=1&m=1&box=1&p=' + page
    link = getHttpData(p_url)

    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索: 第' + page + '页[/COLOR][COLOR FFFFFF00] (' + name + ')[/COLOR]【[COLOR FF00FF00]' + '请输入新搜索内容' + '[/COLOR]】')
    u = sys.argv[0] + "?mode=21&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&page=" + urllib.quote_plus(page)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    #########################################################################
    # Video listing for all found related episode title
    #########################################################################
    matchp=re.compile('<div class="ssItem cfix">(.+?)<div class="alike">').findall(link)
    totalItems = len(matchp)
    k = 0
    for i in range(0, len(matchp)):
        vlink = matchp[i]
        if vlink.find('<em class="pay"></em>')>0: continue

        match1 = re.compile('href="(.+?)"').findall(vlink)
        p_url = match1[0]

        match1 = re.compile('title="(.+?)"').search(vlink)
        p_name = match1.group(1)
            
        match1 = re.compile('src="(.+?)"').search(vlink)
        p_thumb = match1.group(1)

        match1 = re.compile('<span class="maskTx">(.*?)</span>').search(vlink)
        if match1 and match1.group(1)<>'':
            p_label = ' [' + match1.group(1) + ']'
        else:
            p_label =''

        p_type = ''
        isTeleplay = False
        match1 = re.compile('<span class="label-red"><em>(.+?)</em></span>').search(vlink)
        if match1:
            p_type = match1.group(1)
        if p_type=='电视剧':
            isTeleplay = True
            mode = '2'
            p_type='【[COLOR FF00FF00]电视剧[/COLOR]】'
        elif p_type=='电影':
            p_type='【[COLOR FF00FF00]电影[/COLOR]】'
            mode ='3'
        else:
            p_type = ' ' + p_type
            mode ='3'

        k+=1
        p_list = str(k) + ': ' + p_name + p_type + p_label
        li = xbmcgui.ListItem(p_list, iconImage=p_thumb, thumbnailImage=p_thumb)
        u = sys.argv[0] + "?mode=" + mode + "&name=" + urllib.quote_plus(p_name) + "&id=101" + "&url=" + urllib.quote_plus(p_url) + "&thumb=" + urllib.quote_plus(p_thumb)
  
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isTeleplay, totalItems)
 
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
 
##################################################################################
# Sohu Video Link Decode Algorithm & Player
# Extract all the video list and start playing first found valid link
# User may press <SPACE> bar to select video resolution for playback
##################################################################################
def PlayVideo(name,url,thumb):
    level = int(__addon__.getSetting('resolution'))
    site = int(__addon__.getSetting('videosite'))

    link = getHttpData(url)
    match1 = re.compile('var vid="(.+?)";').search(link)
    if not match1:
        match1 = re.compile('<a href="(http://[^/]+/[0-9]+/[^\.]+.shtml)" target="?_blank"?><img').search(link)
        if match1:
            PlayVideo(name,match1.group(1),thumb)
        return
    p_vid = match1.group(1)
    if p_vid == '0':
        match1 = re.compile('data-vid="([^"]+)"').search(link)
        if not match1:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__,'您当前选择的节目暂不能播放，请选择其它节目')
            return
        p_vid = match1.group(1)
    if p_vid.find(',') > 0 : p_vid = p_vid.split(',')[0]
       
    p_url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid='+ p_vid
    link = getHttpData(p_url)
    match = re.compile('"norVid":(.+?),"highVid":(.+?),"superVid":(.+?),"oriVid":(.+?),').search(link)
    if not match:
       dialog = xbmcgui.Dialog()
       ok = dialog.ok(__addonname__,'您当前选择的节目暂不能播放，请选择其它节目')   
       return    
    ratelist=[]
    if match.group(4)!='0':ratelist.append(['原画','4'])
    if match.group(3)!='0':ratelist.append(['超清','3'])
    if match.group(2)!='0':ratelist.append(['高清','2'])
    if match.group(1)!='0':ratelist.append(['流畅','1'])
    if level == 4:
        dialog = xbmcgui.Dialog()
        list = [x[0] for x in ratelist]
        if len(ratelist)==1:
            rate=ratelist[0][1]
        else:
            sel = dialog.select('视频清晰度（低网速请选择低清晰度-流畅）', list)
            if sel == -1:
                return
            else:
                rate=ratelist[sel][1]
    else:
        rate = int(ratelist[0][1])
        if rate > level + 1:
            rate = level + 1
    if match.group(int(rate))<>str(p_vid):
        link = getHttpData('http://hot.vrs.sohu.com/vrs_flash.action?vid='+match.group(int(rate)))
    match = re.compile('"tvName":"(.+?)"').findall(link)
    if not match:
       res = ratelist[3-int(rate)][0]
       dialog = xbmcgui.Dialog()
       ok = dialog.ok(__addonname__,'您当前选择的视频: ['+ res +'] 暂不能播放，请选择其它视频')       
       return
    name = match[0]

    match = re.compile('"clipsURL"\:\["(.+?)"\]').findall(link)
    paths = match[0].split('","')
    match = re.compile('"su"\:\["(.+?)"\]').findall(link)
    if not match:
       res = ratelist[3-int(rate)][0]
       dialog = xbmcgui.Dialog()
       ok = dialog.ok(__addonname__,'您当前选择的视频: ['+ res +'] 暂不能播放，请选择其它视频')       
       return
    newpaths = match[0].split('","')
    
    urls = []
    for i in range(0,len(paths)):
        p_url = 'http://data.vod.itc.cn/?prot=2&file='+paths[i].replace('http://data.vod.itc.cn','')+'&new='+newpaths[i]
        link = getHttpData(p_url)
        
        # http://newflv.sohu.ccgslb.net/|623|116.14.234.161|Googu7gm-8WjRTd5ZfBVPIfrtRtLE5Cn|1|0
        key=link.split('|')[3]
        if site == 0:
            url = link.split('|')[0].rstrip("/")+newpaths[i]+'?key='+key
        else:
            url = 'http://new.sohuv.dnion.com'+newpaths[i]+'?key='+key
        urls.append(url)
    stackurl = 'stack://' + ' , '.join(urls)
    listitem = xbmcgui.ListItem(name,thumbnailImage=thumb)
    listitem.setInfo(type="Video",infoLabels={"Title":name})
    xbmc.Player().play(stackurl, listitem)

##################################################################################
# Sohu 电视直播 Menu List
##################################################################################
def LiveChannel():
    url = 'http://tvimg.tv.itc.cn/live/stations.jsonp'
    link = getHttpData(url)
    match = re.compile('var par=({.+?});', re.DOTALL).search(link)
    if match:
        parsed_json = simplejson.loads(match.group(1))
        totalItems = len(parsed_json['STATIONS'])
        i = 0
        for item in parsed_json['STATIONS']:
            if item['IsSohuSource'] <> 1 or item['TV_TYPE'] <> 1:
                continue
            p_name = item['STATION_NAME'].encode('utf-8')
            p_thumb = item['STATION_PIC'].encode('utf-8')
            id = str(item['STATION_ID'])
            i += 1
            li = xbmcgui.ListItem(str(i)+ '. ' + p_name, iconImage = '', thumbnailImage = p_thumb)
            u = sys.argv[0] + "?mode=11&name=" + urllib.quote_plus(p_name) + "&id=" + urllib.quote_plus(id)+ "&thumb=" + urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

##################################################################################
# Sohu 电视直播 Player
##################################################################################
def LivePlay(name,id,thumb):
    link = getHttpData(LIVEID_URL % (id))
    parsed_json = simplejson.loads(link)
    url = 'http://' + parsed_json['data']['clipsURL'][0].encode('utf-8')
    link = getHttpData(url)
    parsed_json = simplejson.loads(link)
    url = parsed_json['url'].encode('utf-8')
    li = xbmcgui.ListItem(name,iconImage='',thumbnailImage=thumb)
    xbmc.Player().play(url, li)

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
mode = None
name = None
id = None
cat = ''
area = ''
year = ''
order = ''
page = ''
p5 = ''
p6 = ''
p11 = ''
listpage = ''
url = None
thumb = None

try:
    thumb = urllib.unquote_plus(params["thumb"])
except:
    pass
try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    page = urllib.unquote_plus(params["page"])
except:
    pass
try:
    listpage = urllib.unquote_plus(params["listpage"])
except:
    pass
try:
    p5 = urllib.unquote_plus(params["p5"])
except:
    pass
try:
    p6 = urllib.unquote_plus(params["p6"])
except:
    pass
try:
    p11 = urllib.unquote_plus(params["p11"])
except:
    pass
try:
    order = urllib.unquote_plus(params["order"])
except:
    pass
try:
    year = urllib.unquote_plus(params["year"])
except:
    pass
try:
    area = urllib.unquote_plus(params["area"])
except:
    pass
try:
    cat = urllib.unquote_plus(params["cat"])
except:
    pass
try:
    id = urllib.unquote_plus(params["id"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass

if mode == None:
    rootList()
elif mode == 1:
    progList(name,id,page,cat,area,year,p5,p6,p11,order)
elif mode == 2:
    seriesList(name,id,url,thumb)
elif mode == 3:
    PlayVideo(name,url,thumb)
elif mode == 4:
    performChanges(name,id,cat,area,year,p5,p6,p11,order,listpage)

elif mode == 10:
    LiveChannel()
elif mode == 11:
    LivePlay(name,id,thumb)
     
elif mode == 21:
    searchSohu()
elif mode == 22:
    sohuSearchList(name, url, page)
