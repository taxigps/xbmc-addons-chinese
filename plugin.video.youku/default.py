# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, string, sys, os, gzip, StringIO, math, urlparse
import base64, time, cookielib
import simplejson

# Plugin constants 
__addon__     = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__profile__   = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")

UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
ORDER_LIST1 = [['1','最多播放'], ['2','最多评论'], ['4','最受欢迎'], ['5','最近上映'], ['6','最近更新']]
DAYS_LIST1  = [['1','今日'], ['2','本周'], ['4','历史']]
ORDER_LIST2 = [['1','最多播放'], ['2','最新发布'], ['3','最多评论'], ['4','最多收藏'], ['5','最受欢迎']]
DAYS_LIST2  = [['1','今日'], ['2','本周'], ['3','本月'], ['4','历史']]

class youkuDecoder:
    def __init__( self ):
        return

    def getFileIDMixString(self,seed):  
        mixed = []  
        source = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\:._-1234567890")  
        seed = float(seed)  
        for i in range(len(source)):  
            seed = (seed * 211 + 30031 ) % 65536  
            index = math.floor(seed /65536 *len(source))  
            mixed.append(source[int(index)])  
            source.remove(source[int(index)])  
        return mixed  

    def getFileId(self,fileId,seed):  
        mixed = self.getFileIDMixString(seed)  
        ids = fileId.split('*')  
        realId = []  
        for i in range(0,len(ids)-1):
            realId.append(mixed[int(ids[i])])  
        return ''.join(realId)

    def trans_e(self, a, c):
        b = range(256)
        f = 0
        result = ''
        h = 0
        while h < 256:
            f = (f + b[h] + ord(a[h % len(a)])) % 256
            b[h], b[f] = b[f], b[h]
            h += 1
        q = f = h = 0
        while q < len(c):
            h = (h + 1) % 256
            f = (f + b[h]) % 256
            b[h], b[f] = b[f], b[h]
            result += chr(ord(c[q]) ^ b[(b[h] + b[f]) % 256])
            q += 1
        return result

    def trans_f(self, a, c):
        """
        :argument a: list
        :param c:
        :return:
        """
        b = []
        for f in range(len(a)):
            i = ord(a[f][0]) - 97 if "a" <= a[f] <= "z" else int(a[f]) + 26
            e = 0
            while e < 36:
                if c[e] == i:
                    i = e
                    break
                e += 1
            v = i - 26 if i > 25 else chr(i + 97)
            b.append(str(v))
        return ''.join(b)

    f_code_1 = 'becaf9be'
    f_code_2 = 'bf7e5f01'

    def _calc_ep(self, sid, fileId, token):
        ep = self.trans_e(self.f_code_2, '%s_%s_%s' % (sid, fileId, token))
        return base64.b64encode(ep)

    def _calc_ep2(self, vid, ep):
        e_code = self.trans_e(self.f_code_1, base64.b64decode(ep))
        sid, token = e_code.split('_')
        new_ep = self.trans_e(self.f_code_2, '%s_%s_%s' % (sid, vid, token))
        return base64.b64encode(new_ep), token, sid

    def get_sid(self, ep):
        e_code = self.trans_e(self.f_code_1, base64.b64decode(ep))
        return e_code.split('_')

    def generate_ep(self, no, fileid, sid, token):
        ep = urllib.quote(self._calc_ep(sid, fileid, token).encode('latin1'),
            safe="~()*!.'"
        )
        return ep

def log(txt):
    message = '%s: %s' % (__addonname__, txt)
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def GetHttpData(url, referer=''):
    log("%s::url - %s" % (sys._getframe().f_code.co_name, url))
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    if referer:
        req.add_header('Referer', referer)
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

def searchDict(dlist,idx):
    for i in range(0,len(dlist)):
        if dlist[i][0] == idx:
            return dlist[i][1]
    return ''

def getCurrent(text,list,id):
    match = re.compile('<li class="current"\s*><span>(.+?)</span>').search(text)
    if match:
        list.append([id, match.group(1)])

def getList(listpage,id,genre,area,year):
    if id == 'c_95':
        str1 = '风格：'
        str3a = '发行：'
        str3b = 'r'
    elif id == 'c_84' or id == 'c_87':
        str1 = '类型：'
        str3a = '出品：'
        str3b = 'pr'
    else:
        str1 = '类型：'
        str3a = '时间：'
        str3b = 'r'
    match = re.compile('<label>%s</label>(.+?)</ul>' % (str1), re.DOTALL).search(listpage)
    genrelist = re.compile('_g_([^_\.]*)[^>]*>([^<]+)</a>').findall(match.group(1))
    getCurrent(match.group(1), genrelist, genre)
    if id == 'c_84' or id == 'c_87':
        arealist = []
    else:
        match = re.compile('<label>地区：</label>(.+?)</ul>', re.DOTALL).search(listpage)
        arealist = re.compile('_a_([^_\.]*)[^>]*>([^<]+)</a>').findall(match.group(1))
        getCurrent(match.group(1), arealist, area)
    match = re.compile('<label>%s</label>(.+?)</ul>' % (str3a), re.DOTALL).search(listpage)
    yearlist = re.compile('_%s_([^_\.]*)[^>]*>([^<]+)</a>' % (str3b)).findall(match.group(1))
    getCurrent(match.group(1), yearlist, year)
    return genrelist,arealist,yearlist

def getList2(listpage,genre):
    match = re.compile('<label>类型：</label>(.+?)</ul>', re.DOTALL).search(listpage)
    if match:
        genrelist = re.compile('<li><a href=".*?/category/video/[^g]*g_([0-9]+)[^\.]*\.html"[^>]*>(.+?)</a></li>').findall(match.group(1))
        getCurrent(match.group(1), genrelist, genre)
    else:
        genrelist = []
    return genrelist

def rootList():
    link = GetHttpData('http://list.youku.com/')
    match0 = re.compile('<label>分类：</label>(.+?)</ul>', re.DOTALL).search(link)
    match = re.compile('<li><a\s*href="/category/([^/]+)/([^\.]+)\.html">(.+?)</a></li>', re.DOTALL).findall(match0.group(1))
    totalItems = len(match)
    for path, id, name in match:
        if path == 'show':
            u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre=&area=&year=&order=1&days=1&page=1"
        else:
            u = sys.argv[0]+"?mode=11&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre=0&year=1&order=1&days=1&page=1"
        li = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def progList(name,id,page,genre,area,year,order,days):
    url = 'http://list.youku.com/category/show/%s_g_%s_a_%s_s_%s_d_%s_r_%s_p_%s.html' % (id, genre, area, order, days, year, page)
    link = GetHttpData(url)
    match = re.compile('<ul class="yk-pages">(.+?)</ul>', re.DOTALL).search(link)
    plist = []
    if match:
        match1 = re.compile('<li.+?>([0-9]+)(</a>|</span>)</li>', re.DOTALL).findall(match.group(1))
        if match1:
            for num, temp in match1:
                if (num not in plist) and (num != page):
                    plist.append(num)
            totalpages = int(match1[len(match1)-1][0])
    else:
        totalpages = 1
    match = re.compile('<div class="yk-filter" id="filter">(.+?)<div class="yk-filter-handle">', re.DOTALL).search(link)
    if match:
        listpage = match.group(1)
    else:
        listpage = ''
    if id == 'c_95':
        match = re.compile('<div class="yk-pack p-list"(.+?)</ul></div>', re.DOTALL).findall(link)
    else:
        match = re.compile('<div class="yk-pack pack-film">(.+?)</ul></div>', re.DOTALL).findall(link)
    totalItems = len(match) + 1 + len(plist)
    currpage = int(page)

    genrelist,arealist,yearlist = getList(listpage,id,genre,area,year)
    if genre:
        genrestr = searchDict(genrelist,genre)
    else:
        genrestr = '全部类型'
    if area:
        areastr = searchDict(arealist,area)
    else:
		    areastr = '全部地区'
    if year:
        yearstr = searchDict(yearlist,year)
    else:
        if id == 'c_84' or id == 'c_87':
            yearstr = '全部出品'
        else:
            yearstr = '全部年份'
    li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）【[COLOR FFFF0000]' + genrestr + '[/COLOR]/[COLOR FF00FF00]' + areastr + '[/COLOR]/[COLOR FFFFFF00]' + yearstr  + '[/COLOR]/[COLOR FF00FF00]' + searchDict(DAYS_LIST1,days) + '[/COLOR]/[COLOR FF00FFFF]' + searchDict(ORDER_LIST1,order) + '[/COLOR]】（按此选择）')
    u = sys.argv[0]+"?mode=4&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre="+urllib.quote_plus(genre)+"&area="+urllib.quote_plus(area)+"&year="+urllib.quote_plus(year)+"&order="+order+"&days="+days+"&page="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    for i in range(0,len(match)):
        if id in ('c_96','c_95'):
            mode = 2
            isdir = False
        else:
            mode = 3
            isdir = True
        match1 = re.compile('/id_(.+?).html"').search(match[i])   
        p_id = match1.group(1)
        match1 = re.compile('<img class="quic".*?src="(.+?)"').search(match[i])
        p_thumb = match1.group(1)
        match1 = re.compile('<li class="title"><a .*?">(.+?)</a>').search(match[i])
        p_name = match1.group(1)
        match1 = re.compile('<li class="status hover-hide"><span .*?<span>(.+?)</span>').search(match[i])
        if match1:
            p_name1 = p_name + '（' + match1.group(1) + '）'
        else:
            p_name1 = p_name
        match1 = re.compile('<span class="vip-free">(.+?)</span>').search(match[i])
        if match1:
            p_name1 = p_name1 + '[' + match1.group(1) + ']'
        li = xbmcgui.ListItem(str(i + 1) + '. ' + p_name1, iconImage = '', thumbnailImage = p_thumb)
        u = sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(p_name)+"&id="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)
        #li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Cast":p_cast, "Tagline":p_tagline})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isdir, totalItems)
        
    for num in plist:
        li = xbmcgui.ListItem("... 第" + num + "页")
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre="+urllib.quote_plus(genre)+"&area="+urllib.quote_plus(area)+"&year="+year+"&order="+order+"&days="+days+"&page="+str(num)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)         
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getMovie(name,id,thumb):
    if len(id)==21:
        link = GetHttpData('http://www.youku.com/show_page/id_' + id + '.html')
        match = re.compile('<a class="btnShow btnplayposi".*?href="http://v.youku.com/v_show/id_(.+?)\.html[^"]*"', re.DOTALL).search(link)
        if not match:
            match = re.compile('<div class="btnplay">.*?href="http://v.youku.com/v_show/id_(.+?)\.html[^"]*"', re.DOTALL).search(link)
        if match:
            # 播放正片
            PlayVideo(name, match.group(1), thumb)
        else:
            # 解析预告片
            match = re.compile('class="btnShow btnplaytrailer".*?href="http://v.youku.com/v_show/id_(.+?)\.html[^"]*"', re.DOTALL).search(link)
            if match:
                PlayVideo(name, match.group(1), thumb)
            else:
                xbmcgui.Dialog().ok(__addonname__, '解析地址异常，可能是收费节目，无法播放')
    else:
        PlayVideo(name, id, thumb)

def seriesList(name,id,thumb):
    url = "http://v.youku.com/v_show/id_%s.html" % (id)
    data = GetHttpData(url)
    #pages = re.compile('<li data="(point_reload_[0-9]+)"', re.DOTALL).findall(data)
    #if len(pages)>1:
    #    for i in range(1,len(pages)):
    #        url = "http://www.youku.com/show_point/id_%s.html?dt=json&divid=%s&tab=0&__rt=1&__ro=%s" % (id, pages[i], pages[i])
    #        link = GetHttpData(url)
    #        data += link
    match = re.compile('class="item(.+?)</div>', re.DOTALL).findall(data)
    totalItems = len(match)

    for i in range(0,len(match)):
        match1 = re.compile('//v.youku.com/v_show/id_(.+?)\.html').search(match[i])
        if match1:
            p_id = match1.group(1)
        else:
            continue
        #match1 = re.compile('<div class="thumb"><img .*?src="(.+?)"').search(match[i])
        p_thumb = thumb
        match1 = re.compile('title="(.+?)"').search(match[i])
        p_name = "%s %s" % (name, match1.group(1))
        p_name1 = p_name
        li = xbmcgui.ListItem(p_name1, iconImage = '', thumbnailImage = p_thumb)
        u = sys.argv[0]+"?mode=10&name="+urllib.quote_plus(p_name)+"&id="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)
        #li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Cast":p_cast, "Tagline":p_tagline})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def progList2(name,id,page,genre,order,days):
    url = 'http://list.youku.com/category/video/%s_g_%s_s_%s_d_%s_p_%s.html' % (id, genre, order, days, page)
    link = GetHttpData(url)
    match = re.compile('<ul class="yk-pages">(.+?)</ul>', re.DOTALL).search(link)
    plist = []
    if match:
        match1 = re.compile('<li.+?>([0-9]+)(</a>|</span>)</li>', re.DOTALL).findall(match.group(1))
        if match1:
            for num, temp in match1:
                if (num not in plist) and (num != page):
                    plist.append(num)
            totalpages = int(match1[len(match1)-1][0])
    else:
        totalpages = 1
    match = re.compile('<div class="yk-filter\s*" id="filter">(.+?)<div class="yk-filter-handle">', re.DOTALL).search(link)
    if match:
        listpage = match.group(1)
    else:
        listpage = ''
    match = re.compile('<div class="yk-pack p-list"(.+?)</ul></div>', re.DOTALL).findall(link)

    totalItems = len(match) + 1 + len(plist)
    currpage = int(page)

    genrelist = getList2(listpage, genre)
    if genre == '0':
        genrestr = '全部类型'
    else:
        genrestr = searchDict(genrelist,genre)
    li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）【[COLOR FFFF0000]' + genrestr + '[/COLOR]/[COLOR FF00FF00]' + searchDict(DAYS_LIST2,days) + '[/COLOR]/[COLOR FF00FFFF]' + searchDict(ORDER_LIST2,order) + '[/COLOR]】（按此选择）')
    u = sys.argv[0]+"?mode=12&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre="+urllib.quote_plus(genre)+"&order="+order+"&days="+days+"&page="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    for i in range(0,len(match)):
        match1 = re.compile('/id_(.+?).html"').search(match[i])
        p_id = match1.group(1)
        match1 = re.compile('<img class="quic".*?src="(.+?)"').search(match[i])
        p_thumb = match1.group(1)
        match1 = re.compile('<li class="title"><a .*?">(.+?)</a>').search(match[i])
        p_name = match1.group(1)
        p_name1 = p_name
        li = xbmcgui.ListItem(str(i + 1) + '. ' + p_name1, iconImage = '', thumbnailImage = p_thumb)
        u = sys.argv[0]+"?mode=10&name="+urllib.quote_plus(p_name)+"&id="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)
        #li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Cast":p_cast, "Tagline":p_tagline})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)

    for num in plist:
        li = xbmcgui.ListItem("... 第" + num + "页")
        u = sys.argv[0]+"?mode=11&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre="+urllib.quote_plus(genre)+"&order="+order+"&days="+days+"&page="+str(num)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)         
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def selResolution(streamtypes):
    ratelist = []
    for i in range(0,len(streamtypes)):
        if streamtypes[i] in ('flv', 'flvhd'): ratelist.append([4, '标清', i, 'flv']) # [清晰度设置值, 清晰度, streamtypes索引]
        if streamtypes[i] in ('mp4', 'mp4hd'): ratelist.append([3, '高清', i, 'mp4'])
        if streamtypes[i] in ('hd2', 'hd2v2', 'mp4hd2', 'mp4hd2v2'): ratelist.append([2, '超清', i, 'hd2'])
        if streamtypes[i] in ('hd3', 'hd3v2', 'mp4hd3', 'mp4hd3v2'): ratelist.append([1, '1080P', i, 'hd3'])
    ratelist.sort()
    if len(ratelist) > 1:
        resolution = int(__addon__.getSetting('resolution'))
        if resolution == 0:    # 每次询问视频清晰度
            list = [x[1] for x in ratelist]
            sel = xbmcgui.Dialog().select('清晰度（低网速请选择低清晰度）', list)
            if sel == -1:
                return None, None, None, None
        else:
            sel = 0
            while sel < len(ratelist)-1 and resolution > ratelist[sel][0]: sel += 1
    else:
        sel = 0
    return streamtypes[ratelist[sel][2]], ratelist[sel][1], ratelist[sel][2], ratelist[sel][3]

def youku_ups(id):
    res = urllib2.urlopen('https://log.mmstat.com/eg.js')
    cna = res.headers['etag'][1:-1]
    query = urllib.urlencode(dict(
        vid       = id,
        ccode     = '0502',
        client_ip = '192.168.1.1',
        utid      = cna,
        client_ts = time.time() / 1000,
        ckey      = 'DIl58SLFxFNndSV1GFNnMQVYkx1PP5tKe1siZu/86PR1u/Wh1Ptd+WOZsHHWxysSfAOhNJpdVWsdVJNsfJ8Sxd8WKVvNfAS8aS8fAOzYARzPyPc3JvtnPHjTdKfESTdnuTW6ZPvk2pNDh4uFzotgdMEFkzQ5wZVXl2Pf1/Y6hLK0OnCNxBj3+nb0v72gZ6b0td+WOZsHHWxysSo/0y9D2K42SaB8Y/+aD2K42SaB8Y/+ahU+WOZsHcrxysooUeND'
    ))
    url = 'https://ups.youku.com/ups/get.json?%s' % (query)
    link = GetHttpData(url, referer='http://v.youku.com/')
    json_response = simplejson.loads(link)
    api_data = json_response['data']
    data_error = api_data.get('error')
    if data_error:
        api_error_code = data_error.get('code')
        api_error_msg = data_error.get('note').encode('utf-8')
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__,'地址解析错误（%d）：\n%s' % (api_error_code,api_error_msg))
        return {}
    else:
        return api_data

def change_cdn(url):
    # if the cnd_url starts with an ip addr, it should be youku's old CDN
    # which rejects http requests randomly with status code > 400
    # change it to the dispatcher of aliCDN can do better
    # at least a little more recoverable from HTTP 403
    dispatcher_url = 'vali.cp31.ott.cibntv.net'
    if dispatcher_url in url:
        return url
    elif 'k.youku.com' in url:
        return url
    else:
        url_seg_list = list(urlparse.urlsplit(url))
        url_seg_list[1] = dispatcher_url
        return urlparse.urlunsplit(url_seg_list)

def PlayVideo(name,id,thumb):
    movdat = youku_ups(id)
    if not movdat:
        return

    vid = id
    lang_select = int(__addon__.getSetting('lang_select')) # 默认|每次选择|自动首选
    if lang_select != 0 and movdat.has_key('dvd') and 'audiolang' in movdat['dvd']:
        langlist = movdat['dvd']['audiolang']
        if lang_select == 1:
            list = [x['lang'] for x in langlist]
            sel = xbmcgui.Dialog().select('选择语言', list)
            if sel ==-1:
                return
            vid = langlist[sel]['vid'].encode('utf-8')
            name = '%s %s' % (name, langlist[sel]['lang'].encode('utf-8'))
        else:
            lang_prefer = __addon__.getSetting('lang_prefer') # 国语|粤语
            for i in range(0,len(langlist)):
                if langlist[i]['lang'].encode('utf-8') == lang_prefer:
                    vid = langlist[i]['vid'].encode('utf-8')
                    name = '%s %s' % (name, langlist[i]['lang'].encode('utf-8'))
                    break
    if vid != id:
        movdat = youku_ups(vid)
        if not movdat:
            return

    streamtypes = [stream['stream_type'].encode('utf-8') for stream in movdat['stream']]
    typeid, typename, streamno, resolution = selResolution(streamtypes)
    if typeid:
        '''
        oip = movdat['security']['ip']
        ep = movdat['security']['encrypt_string']
        sid, token = youkuDecoder().get_sid(ep)
        play_method = int(__addon__.getSetting('play_method'))
        if play_method != 0: # m3u8方式
            query = urllib.urlencode(dict(
                vid=vid, ts=int(time.time()), keyframe=1, type=resolution,
                ep=ep, oip=oip, ctype=12, ev=1, token=token, sid=sid,
            ))
            cookie = ['%s=%s' % (x.name, x.value) for x in cj][0]
            movurl = 'http://pl.youku.com/playlist/m3u8?%s|Cookie=%s' % (query, cookie)

        else: # 默认播放方式
            if typeid in ('mp4', 'mp4hd'):
                type = 'mp4'
            else:
                type = 'flv'
            urls = []
            segs = movdat['stream'][streamno]['segs']
            total = len(segs)
            for no in range(0, total):
                k = segs[no]['key']
                if k == -1:
                    dialog = xbmcgui.Dialog()
                    ok = dialog.ok(__addonname__,'会员节目，无法播放')
                    return
                fileid = segs[no]['fileid']
                ep = youkuDecoder().generate_ep(no, fileid, sid, token)
                query = urllib.urlencode(dict(
                    ctype = 12,
                    ev    = 1,
                    K     = k,
                    ep    = urllib.unquote(ep),
                    oip   = oip,
                    token = token,
                    yxon  = 1
                ))
                url = 'http://k.youku.com/player/getFlvPath/sid/{sid}_00/st/{container}/fileid/{fileid}?{query}'.format(
                    sid       = sid,
                    container = type,
                    fileid    = fileid,
                    query     = query
                )
                link = GetHttpData(url)
                json_response = simplejson.loads(link)
                urls.append(json_response[0]['server'].encode('utf-8'))
            movurl = 'stack://' + ' , '.join(urls)
        '''
        movurl = movdat['stream'][streamno]['m3u8_url']
        #urls = []
        #is_preview = False
        #for seg in movdat['stream'][streamno]['segs']:
        #    if seg.get('cdn_url'):
        #        urls.append(change_cdn(seg['cdn_url'].encode('utf-8')))
        #    else:
        #        is_preview = True
        #if not is_preview:
        #    movurl = 'stack://' + ' , '.join(urls)
        name = '%s[%s]' % (name, typename)
        listitem=xbmcgui.ListItem(name,thumbnailImage=thumb)
        listitem.setInfo(type="Video",infoLabels={"Title":name})
        xbmc.Player().play(movurl, listitem)

def performChanges(name,id,listpage,genre,area,year,order,days):
    genrelist,arealist,yearlist = getList(listpage,id,genre,area,year)
    change = False
    if id == 'c_95':
        str1 = '风格'
        str3 = '发行'
    elif id == 'c_84' or id == 'c_87':
        str1 = '类型'
        str3 = '出品'
    else:
        str1 = '类型'
        str3 = '时间'
    dialog = xbmcgui.Dialog()
    if len(genrelist)>0:
        list = [x[1] for x in genrelist]
        sel = dialog.select(str1, list)
        if sel != -1:
            genre = genrelist[sel][0]
            change = True
    if len(arealist)>0:
        list = [x[1] for x in arealist]
        sel = dialog.select('地区', list)
        if sel != -1:
            area = arealist[sel][0]
            change = True
    if len(yearlist)>0:
        list = [x[1] for x in yearlist]
        sel = dialog.select(str3, list)
        if sel != -1:
            year = yearlist[sel][0]
            change = True
    list = [x[1] for x in DAYS_LIST1]
    sel = dialog.select('范围', list)
    if sel != -1:
        days = DAYS_LIST1[sel][0]
        change = True
    list = [x[1] for x in ORDER_LIST1]
    sel = dialog.select('排序', list)
    if sel != -1:
        order = ORDER_LIST1[sel][0]
        change = True

    if change:
        progList(name,id,'1',genre,area,year,order,days)

def performChanges2(name,id,listpage,genre,order,days):
    genrelist = getList2(listpage, genre)
    change = False
    dialog = xbmcgui.Dialog()
    if len(genrelist)>0:
        list = [x[1] for x in genrelist]
        sel = dialog.select('类型', list)
        if sel != -1:
            genre = genrelist[sel][0]
            change = True
    list = [x[1] for x in DAYS_LIST2]
    sel = dialog.select('范围', list)
    if sel != -1:
        days = DAYS_LIST2[sel][0]
        change = True
    list = [x[1] for x in ORDER_LIST2]
    sel = dialog.select('排序', list)
    if sel != -1:
        order = ORDER_LIST2[sel][0]
        change = True

    if change:
        progList2(name,id,'1',genre,order,days)

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
name = ''
id = ''
genre = ''
area = ''
year = ''
order = ''
page = '1'
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
    order = urllib.unquote_plus(params["order"])
except:
    pass
try:
    days = urllib.unquote_plus(params["days"])
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
    genre = urllib.unquote_plus(params["genre"])
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

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)

if mode == None:
    rootList()
elif mode == 1:
    progList(name,id,page,genre,area,year,order,days)
elif mode == 2:
    getMovie(name,id,thumb)
elif mode == 3:
    seriesList(name,id,thumb)
elif mode == 4:
    performChanges(name,id,page,genre,area,year,order,days)
elif mode == 10:
    PlayVideo(name,id,thumb)
elif mode == 11:
    progList2(name,id,page,genre,order,days)
elif mode == 12:
    performChanges2(name,id,page,genre,order,days)

