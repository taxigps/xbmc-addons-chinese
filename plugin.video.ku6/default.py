# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, string, sys, os, gzip, StringIO

# 酷6云中剧场(www.juchang.com) by wow1122(wht9000@gmail.com), 2011

# Plugin constants 
__addonname__ = "酷6云中剧场(www.juchang.com)"
__addonid__ = "plugin.video.ku6"
__addon__ = xbmcaddon.Addon(id=__addonid__)
__addonicon__ = os.path.join( __addon__.getAddonInfo('path'), 'icon.png' )

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

RATE_LIST = [['超清','1500'], ['高清','600'], ['标清','300'], ['流畅','170'],]
ORDER_LIST = [['更新时间','4'], ['上映时间','1'], ['播放次数','2'], ['热门评分','3'],]
ORDER_DICT = dict(ORDER_LIST)

MOVIE_AREA_LIST = {}
MOVIE_AREA_LIST['1'] = [['全部','0'],['内地','17'],['香港','18'],['台湾','37'],['欧美','1001'],['日本','21'],['韩国','22'],['法国','26'],['其他','3002'],]
MOVIE_AREA_LIST['2'] = [['全部','0'],['内地','118'],['香港','117'],['台湾','119'],['欧美','1003'],['日本','116'],['韩国','115'],['其他','3002'],]
MOVIE_AREA_LIST['3'] = [['全部','0'],['日本','1'],['内地','7'],['欧美','1005'],['其他','3002'],]
MOVIE_AREA_LIST['4'] = [['全部','0'],['内地','10'],['台湾','8'],['其他','3002'],]

MOVIE_YEAR_LIST = {}
MOVIE_YEAR_LIST['1'] = [['全部','0'],['2011年','2011'],['2010年','2010'],['2009年','2009'],['2008年','2008'],['2007年','2007年'],['2006年','2006'],['2005年','2005'],['2004年','2004'],['2003年','2003'],['2002年','2002'],['2001年','2001'],['更早','3001'],]
MOVIE_YEAR_LIST['2'] = [['全部','0'],['2011年','2011'],['2010年','2010'],['2009年','2009'],['2008年','2008'],['2007年','2007年'],['2006年','2006'],['2005年','2005'],['2004年','2004'],['2003年','2003'],['2002年','2002'],['2001年','2001'],['更早','3001'],]
MOVIE_YEAR_LIST['3'] = [['全部','0'],['已完结','1'],['未完结','2'],]
MOVIE_YEAR_LIST['4'] = [['全部','0'],['2011年','2011'],['2010年','2010'],['2009年','2009'],['更早','3001'],]

MOVIE_TYPE_LIST = {}
MOVIE_TYPE_LIST['1'] = [['全部','0'],['爱情','59'],['恐怖','60'],['动作','61'],['动画','63'],['科幻','64'],['喜剧','65'],['剧情','68'],['惊悚','67'],['犯罪','69'],['奇幻','70'],['青春','74'],['战争','75'],['西部','77'],['伦理','84'],['神秘','81'],['传记','80'],['曲折','76'],['艺术','87'],['其他','3002'],]
MOVIE_TYPE_LIST['2'] = [['全部','0'],['偶像','170'],['都市','177'],['伦理','171'],['爱情','174'],['剧情','188'],['网剧','207'],['谍战','182'],['战争','179'],['年代','173'],['历史','172'],['武侠','175'],['古装','176'],['警匪','183'],['悬疑','180'],['魔幻','181'],['农村','178'],['苦情','184'],['商战','185'],['喜剧','186'],['其他','3002'],]
MOVIE_TYPE_LIST['3'] = [['全部','0'],['情感','1'],['科幻','4'],['热血','7'],['推理','9'],['搞笑','10'],['冒险','13'],['萝莉','18'],['校园','133'],['动作','3'],['机战','163'],['运动','164'],['耽美','165'],['机战','163'],['战争','166'],['少年','167'],['少女','168'],['社会','169'],['原创','189'],['原创','3002'],]
MOVIE_TYPE_LIST['4'] = [['全部','0'],['真人秀','29'],['脱口秀','30'],['晚会','200'],['生活','206'],['情感','57'],['交友','199'],['益智','34'],['游戏','43'],['时尚','54'],['其他','3002'],]
ZM_LIST = [['全部','0'],['A','1'], ['B','2'], ['C','3'], ['D','4'],['E','5'],['F','6'],['G','7'],['H','8'],['I','9'],['G','10'],['K','11'],['L','12'],['M','13'],['N','14'],['O','15'],['P','16'],['Q','17'],['R','18'],['S','19'],['T','20'],['U','21'],['V','22'],['V','23'],['X','24'],['Y','25'],['Z','26'],]

def GetHttpData(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    if response.headers.get('content-encoding', None) == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    response.close()
    match = re.compile('<meta http-equiv="[Cc]ontent-[Tt]ype" content="text/html; charset=(.+?)"').findall(httpdata)
    if len(match)<=0:
        match = re.compile('meta charset="(.+?)"').findall(httpdata)
    if len(match)>0:
        charset = match[0].lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = unicode(httpdata, charset).encode('utf8')
    return httpdata
  
def rootList():
    li=xbmcgui.ListItem('电影')
    u=sys.argv[0]+"?mode=1&name="+urllib.quote_plus('电影')+"&type="+urllib.quote_plus('1')+"&cat="+urllib.quote_plus('0')+"&area="+urllib.quote_plus('0')+"&year="+urllib.quote_plus('0')+"&order="+urllib.quote_plus('4')+"&page="+urllib.quote_plus('1')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
    li=xbmcgui.ListItem('电视剧')
    u=sys.argv[0]+"?mode=1&name="+urllib.quote_plus('电视剧')+"&type="+urllib.quote_plus('2')+"&cat="+urllib.quote_plus('0')+"&area="+urllib.quote_plus('0')+"&year="+urllib.quote_plus('0')+"&order="+urllib.quote_plus('4')+"&page="+urllib.quote_plus('1')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
    li=xbmcgui.ListItem('动漫')
    u=sys.argv[0]+"?mode=1&name="+urllib.quote_plus('动漫')+"&type="+urllib.quote_plus('3')+"&cat="+urllib.quote_plus('0')+"&area="+urllib.quote_plus('0')+"&year="+urllib.quote_plus('0')+"&szm="+urllib.quote_plus('0')+"&order="+urllib.quote_plus('4')+"&page="+urllib.quote_plus('1')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
    li=xbmcgui.ListItem('综艺')
    u=sys.argv[0]+"?mode=1&name="+urllib.quote_plus('综艺')+"&type="+urllib.quote_plus('4')+"&cat="+urllib.quote_plus('0')+"&area="+urllib.quote_plus('0')+"&year="+urllib.quote_plus('0')+"&order="+urllib.quote_plus('4')+"&page="+urllib.quote_plus('1')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def searchDict(dlist,idx):
    for i in range(0,len(dlist)):
        if dlist[i][1] == idx:
            return dlist[i][0]
    return ''

def progList(name,type,cat,area,year,szm,order,page):
    baseurl='http://list.juchang.com/jcl/'+type+'-'
    if page:
        currpage = int(page)
    else:
        currpage = 1
    if type=='3':url = baseurl + cat +'-'+ area + '-' + year + '-0-'+szm+'-4-' +order +'-1-'+ str(currpage) +'-12.html'
    else:url = baseurl + cat +'-'+ area + '-' + year + '-0-1-' +order +'-1-'+ str(currpage) +'-12.html'
    print url
    link = GetHttpData(url)
    match = re.compile('<li ><div class="box01_ln(.+?)</li>', re.DOTALL).findall(link)
    totalItems = len(match)
    catstr=searchDict(MOVIE_TYPE_LIST[type],cat)
    orderstr=searchDict(ORDER_LIST,order)
    areastr=searchDict(MOVIE_AREA_LIST[type],area)
    yearstr=searchDict(MOVIE_YEAR_LIST[type],year)
        
    orderstr=searchDict(ORDER_LIST,order)
    
    if type=='3':
        szmstr=searchDict(ZM_LIST,szm)
        li = xbmcgui.ListItem('首字母[COLOR FFFF0000]【' + szmstr + '】[/COLOR] 类型[COLOR FFFF0000]【' + catstr + '】[/COLOR] 地区[COLOR FFFF0000]【' + areastr + '】[/COLOR] 年份[COLOR FFFF0000]【' + yearstr + '】[/COLOR] 排序[COLOR FFFF0000]【' + orderstr + '】[/COLOR]（按此选择）')
    else:
        li = xbmcgui.ListItem('类型[COLOR FFFF0000]【' + catstr + '】[/COLOR] 地区[COLOR FFFF0000]【' + areastr + '】[/COLOR] 年份[COLOR FFFF0000]【' + yearstr + '】[/COLOR] 排序[COLOR FFFF0000]【' + orderstr + '】[/COLOR]（按此选择）')
    u = sys.argv[0] + "?mode=5&name="+urllib.quote_plus(name)+"&type="+urllib.quote_plus(type)+"&cat="+urllib.quote_plus(cat)+"&area="+urllib.quote_plus(area)+"&year="+urllib.quote_plus(year)+"&order="+urllib.quote_plus(order)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    for i in range(0,len(match)):
        match1 = re.compile('<div class="modht_ln"><h1>(.+?)</h1>').search(match[i])
        p_name = match1.group(1)
        match1 = re.compile('<img src="(.+?)"/>').search(match[i])
        p_thumb = match1.group(1)
        match1 = re.compile('<a target="_blank" href="(.+?)" title').search(match[i])
        p_id = match1.group(1)
        li = xbmcgui.ListItem(p_name, iconImage = '', thumbnailImage = p_thumb)
        isDir=False
        if type=='1':
            u = sys.argv[0]+"?mode=10&name="+urllib.quote_plus(p_name)+"&type="+urllib.quote_plus(type)+"&url="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)
        else:
            isDir=True
            u = sys.argv[0]+"?mode=2&name="+urllib.quote_plus(p_name)+"&type="+urllib.quote_plus(type)+"&url="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isDir, totalItems)
    if currpage > 1:
        li = xbmcgui.ListItem('上一页')
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&type="+urllib.quote_plus(type)+"&cat="+urllib.quote_plus(cat)+"&area="+urllib.quote_plus(area)+"&year="+urllib.quote_plus(year)+"&order="+urllib.quote_plus(order)+"&page="+urllib.quote_plus(str(currpage-1))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    if len(match) > 11:
        li = xbmcgui.ListItem('下一页')
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&type="+urllib.quote_plus(type)+"&cat="+urllib.quote_plus(cat)+"&area="+urllib.quote_plus(area)+"&year="+urllib.quote_plus(year)+"&order="+urllib.quote_plus(order)+"&page="+urllib.quote_plus(str(currpage+1))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def listA(name,type,url,thumb):
    link = GetHttpData(url)
    match1 = re.compile('<!-- 剧集列表 start -->(.+?)<!-- 剧集列表 end -->', re.DOTALL).findall(link)
    match2 = re.compile('<div class="left">(.+?)</div>', re.DOTALL).findall(match1[0])
    if match2:
        match=re.compile(r"'videoListCon', '(.+?)'", re.DOTALL).findall(match2[0])
        if match:
            FindItems(type,match1[0])
            for url in match:
                link = GetHttpData('http://www.juchang.com'+url)
                link=link.decode('gbk').encode('utf8') 
                FindItems(type,link)
                match2 = re.compile('<a href="#" class="one"(.+?)<a class="two"', re.DOTALL).findall(link)
                if match2:
                    match3=re.compile(r"'videoListCon','(.+?)'", re.DOTALL).findall(match2[0])
                    for urla in match3:
                        link = GetHttpData('http://www.juchang.com'+urla)
                        link=link.decode('gbk').encode('utf8') 
                        FindItems(type,link)
        else:
            FindItems(type,match1[0])  
    else:
       FindItems(type,match1[0])  
       
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def FindItems(type,link):
   #link = GetHttpData('http://www.juchang.com'+url)
   #link=link.decode('gbk').encode('utf8') 
   if type =='4':
       match1=re.compile('<ul class="xq_r_jjbox cfix"(.+?)</ul>', re.DOTALL).findall(link)
       match =re.compile('<span class="shadow">(.+?)</span> <a href="(.+?)" target="show_v" title=""><span class="icoVideo"> </span><img class="pic1" src="(.+?)" alt=', re.DOTALL).findall(match1[0]) 
       if not match:
           match = re.compile('<p class="pic rel one"> <a href="(.+?)".+?src="(.+?)" alt="(.+?)" /></a>', re.DOTALL).findall(link)
           totalItems=len(match)
           for p_url,p_thumb,p_name  in match:

                li = xbmcgui.ListItem(name+'-'+p_name, iconImage = '', thumbnailImage = p_thumb)
                u = sys.argv[0] + "?mode=10&name="+urllib.quote_plus(name+'- '+p_name)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)
                #li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Cast":p_cast, "Tagline":p_tagline})
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
           return             
   else:
       match = re.compile('> <span class="shadow">(.+?)</span> <a href="(.+?)" target="show_v" title=".+?"><span class="icoVideo"> </span><img class="pic1" src="(.+?)"', re.DOTALL).findall(link) 
   totalItems=len(match)
   for p_name,p_url,p_thumb  in match:
        li = xbmcgui.ListItem(name+'-'+p_name, iconImage = '', thumbnailImage = p_thumb)
        u = sys.argv[0] + "?mode=10&name="+urllib.quote_plus(name+'- '+p_name)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)
        #li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Cast":p_cast, "Tagline":p_tagline})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)  
             
def PlayVideo(name,type,url,thumb):
    dialog = xbmcgui.Dialog()
    list = [x[0] for x in RATE_LIST]
    sel = dialog.select('类型', list)
    if sel != -1:
        rate=RATE_LIST[sel][1]
        link = GetHttpData(url)
        match = re.compile('"f":"(.+?)","').findall(link)   
        urllist=match[0]
        urllist=eval('u"'+urllist+'"').encode('utf-8')
        vidlist=urllist.split(',')       
        if len(vidlist)>0:
            playlist=xbmc.PlayList(1)
            playlist.clear()
            for i in range(len(vidlist)):
                listitem = xbmcgui.ListItem(name, thumbnailImage = __addonicon__)
                listitem.setInfo(type="Video",infoLabels={"Title":name+" 第"+str(i+1)+"/"+str(len(vidlist))+" 节"})
                playlist.add(vidlist[i]+'?rate='+rate, listitem)
                #playlist.add(vidlist[i], listitem)
            xbmc.Player().play(playlist)
        else:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '无法播放：未匹配到视频文件，请稍侯再试或联系作者')

def performChanges(name,type,cat,area,year,order):
    change = False
    dialog = xbmcgui.Dialog()
    szm=''
    if type=='3':
        list = [x[0] for x in ZM_LIST]
        sel = dialog.select('首字母', list)
        if sel != -1:
            szm=ZM_LIST[sel][1]
            change = True
    list = [x[0] for x in MOVIE_TYPE_LIST[type]]
    sel = dialog.select('类型', list)
    if sel != -1:
        cat=MOVIE_TYPE_LIST[type][sel][1]
        change = True
    list = [x[0] for x in MOVIE_AREA_LIST[type]]
    sel = dialog.select('地区', list)
    if sel != -1:
        area=MOVIE_AREA_LIST[type][sel][1]
        change = True
    list = [x[0] for x in MOVIE_YEAR_LIST[type]]
    if type=='3':
        sel = dialog.select('连载状态', list)
    else:
        sel = dialog.select('年份', list)
    if sel != -1:
        year=MOVIE_YEAR_LIST[type][sel][1]
        change = True
    list = [x[0] for x in ORDER_LIST]
    sel = dialog.select('排序方式', list)
    if sel != -1:
        order = ORDER_LIST[sel][1]
        change = True    
    if change:
        progList(name,type,cat,area,year,szm,order,page)
        
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
leftid=''
id = None
type = ''
cat = ''
area = ''
year = ''
order = None
page = '1'
url = ''
szm = ''
thumb = None
res = 0

try:
    type = urllib.unquote_plus(params["type"])
except:
    pass
try:
    res = int(params["res"])
except:
    pass
try:
    thumb = urllib.unquote_plus(params["thumb"])
except:
    pass
try:
    baseurl = urllib.unquote_plus(params["baseurl"])
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
    szm = urllib.unquote_plus(params["szm"])
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
    progList(name,type,cat,area,year,szm,order,page)
elif mode == 2:
    listA(name,type,url,thumb)
elif mode == 5:
    performChanges(name,type,cat,area,year,order)
elif mode == 10:
    PlayVideo(name,type,url,thumb)

