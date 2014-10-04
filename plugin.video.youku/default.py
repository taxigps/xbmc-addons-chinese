# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, string, sys, os, gzip, StringIO, math
import base64, time
try:
    import simplejson
except ImportError:
    import json as simplejson

# Plugin constants 
__addon__     = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
ORDER_LIST = [['7','今日增加播放'], ['6','本周增加播放'], ['1','历史最多播放'], ['3','上映时间'], ['9','近期上映'], ['10','近期更新'], ['5','最多评论'], ['11','用户好评']]
ORDER_LIST2 = [['1','最新发布'], ['2','最多播放'], ['3','最多评论'], ['8','最具争议'], ['4','最多收藏'], ['5','最广传播']]
YEAR_LIST2 = [['4','不限'], ['1','今日'], ['2','本周'], ['3','本月']]
UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'

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

    def _calc_ep2(self, vid, ep):
        e_code = self.trans_e(self.f_code_1, base64.b64decode(ep))
        sid, token = e_code.split('_')
        new_ep = self.trans_e(self.f_code_2, '%s_%s_%s' % (sid, vid, token))
        return base64.b64encode(new_ep), token, sid

def log(txt):
    message = '%s: %s' % (__addonname__, txt)
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def GetHttpData(url):
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
        str1 = '风格'
        str3a = '发行'
        str3b = 'r'
    elif id == 'c_84' or id == 'c_87':
        str1 = '类型'
        str3a = '出品'
        str3b = 'pr'
    else:
        str1 = '类型'
        str3a = '时间'
        str3b = 'r'
    match = re.compile('<label>%s</label>(.+?)</ul>' % (str1), re.DOTALL).search(listpage)
    genrelist = re.compile('_g_([^_\.]*)[^>]*>([^<]+)</a>').findall(match.group(1))
    getCurrent(match.group(1), genrelist, genre)
    if id == 'c_84' or id == 'c_87':
        arealist = []
    else:
        match = re.compile('<label>地区</label>(.+?)</ul>', re.DOTALL).search(listpage)
        arealist = re.compile('_a_([^_\.]*)[^>]*>([^<]+)</a>').findall(match.group(1))
        getCurrent(match.group(1), arealist, area)
    match = re.compile('<label>%s</label>(.+?)</ul>' % (str3a), re.DOTALL).search(listpage)
    yearlist = re.compile('_%s_([^_\.]*)[^>]*>([^<]+)</a>' % (str3b)).findall(match.group(1))
    getCurrent(match.group(1), yearlist, year)
    return genrelist,arealist,yearlist

def getList2(listpage,genre):
    match = re.compile('<label>类型</label>(.+?)</ul>', re.DOTALL).search(listpage)
    if match:
        genrelist = re.compile('<li><a href=".*?/v_showlist/[^g]*g([0-9]+)[^\.]*\.html"[^>]*>(.+?)</a></li>').findall(match.group(1))
        getCurrent(match.group(1), genrelist, genre)
    else:
        genrelist = []
    return genrelist

def rootList():
    link = GetHttpData('http://www.youku.com/v/')
    match0 = re.compile('<label>分类</label>(.+?)</ul>', re.DOTALL).search(link)
    match = re.compile('<li><a\s*href="/([^/]+)/([^\.]+)\.html"[^>]+>(.+?)</a></li>').findall(match0.group(1))
    totalItems = len(match)
    for path, id, name in match:
        if path == 'v_olist':
            u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre=&area=&year=&order=7&page=1"
        else:
            u = sys.argv[0]+"?mode=11&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre=0&year=1&order=2&page=1"
        li = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def progList(name,id,page,genre,area,year,order):
    url = 'http://www.youku.com/v_olist/%s_a_%s_s__g_%s_r_%s_o_%s_p_%s.html' % (id, area, genre, year, order, page)
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
        match = re.compile('<div class="v">(.+?)</div>\s*</div>\s*</div>\s*</div>', re.DOTALL).findall(link)
    else:
        match = re.compile('<div class="p p-small">(.+?)</div>\s*</div>\s*</div>\s*</div>', re.DOTALL).findall(link)
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
    li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）【[COLOR FFFF0000]' + genrestr + '[/COLOR]/[COLOR FF00FF00]' + areastr + '[/COLOR]/[COLOR FFFFFF00]' + yearstr + '[/COLOR]/[COLOR FF00FFFF]' + searchDict(ORDER_LIST,order) + '[/COLOR]】（按此选择）')
    u = sys.argv[0]+"?mode=4&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre="+urllib.quote_plus(genre)+"&area="+urllib.quote_plus(area)+"&year="+urllib.quote_plus(year)+"&order="+order+"&page="+urllib.quote_plus(listpage)
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
        if id == 'c_95':
            match1 = re.compile('<div class="v-thumb">\s*<img src="(.+?)"').search(match[i])
            p_thumb = match1.group(1)
            match1 = re.compile('<div class="v-meta-title">\s*<a [^>]+>(.+?)</a>').search(match[i])
            p_name = match1.group(1)
        else:
            match1 = re.compile('<div class="p-thumb">\s*<img src="(.+?)"').search(match[i])
            p_thumb = match1.group(1)
            match1 = re.compile('<div class="p-meta-title"><a .*?">(.+?)</a>').search(match[i])
            p_name = match1.group(1)
        match1 = re.compile('<span class="p-status">(.+?)</span>').search(match[i])
        if match1:
            if match1.group(1) == '资料':
                mode = 99
            p_name1 = p_name + '（' + match1.group(1) + '）'
        else:
            p_name1 = p_name
        if match[i].find('<i class="ico-1080P"')>0:
            p_name1 += '[1080P]'
            p_res = 1
        elif match[i].find('<i class="ico-SD"')>0:
            p_name1 += '[超清]'
            p_res = 2
        elif match[i].find('<i class="ico-HD"')>0:
            p_name1 += '[高清]'
            p_res = 3
        else:
            p_res = 4
        if match[i].find('<i class="ico-ispay"')>0:
            p_name1 += '[付费节目]'
        li = xbmcgui.ListItem(str(i + 1) + '. ' + p_name1, iconImage = '', thumbnailImage = p_thumb)
        u = sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(p_name)+"&id="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)+"&res="+str(p_res)
        #li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Cast":p_cast, "Tagline":p_tagline})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isdir, totalItems)
        
    for num in plist:
        li = xbmcgui.ListItem("... 第" + num + "页")
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre="+urllib.quote_plus(genre)+"&area="+urllib.quote_plus(area)+"&year="+year+"&order="+order+"&page="+str(num)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)         
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getMovie(name,id,thumb,res):
    if len(id)==21:
        link = GetHttpData('http://www.youku.com/show_page/id_' + id + '.html')
        match = re.compile('<a class="btnShow btnplayposi".*?href="http://v.youku.com/v_show/id_(.+?)\.html"', re.DOTALL).search(link)
        if not match:
            match = re.compile('<div class="btnplay">.*?href="http://v.youku.com/v_show/id_(.+?)\.html"', re.DOTALL).search(link)
        if match:
            # 播放正片
            PlayVideo(name, match.group(1), thumb, res)
        else:
            # 解析预告片
            match = re.compile('class="btnShow btnplaytrailer".*?data="\{videoId:(\d+),', re.DOTALL).search(link)
            if match:
                PlayVideo(name, match.group(1), thumb, res)
    else:
        PlayVideo(name, id, thumb, res)

def seriesList(name,id,thumb,res):
    url = "http://www.youku.com/show_point_id_%s.html?dt=json&__rt=1&__ro=reload_point" % (id)
    data = GetHttpData(url)
    pages = re.compile('<li data="(point_reload_[0-9]+)"', re.DOTALL).findall(data)
    if len(pages)>1:
        for i in range(1,len(pages)):
            url = "http://www.youku.com/show_point/id_%s.html?dt=json&divid=%s&tab=0&__rt=1&__ro=%s" % (id, pages[i], pages[i])
            link = GetHttpData(url)
            data += link
    match = re.compile('<div class="item">(.+?)</div><!--.item-->', re.DOTALL).findall(data)
    totalItems = len(match)

    for i in range(0,len(match)):
        match1 = re.compile('<div class="link"><a .*?href="http://v.youku.com/v_show/id_(.+?)\.html"').search(match[i])
        if match1:
            p_id = match1.group(1)
        else:
            continue
        match1 = re.compile('<div class="thumb"><img .*?src="(.+?)"').search(match[i])
        p_thumb = match1.group(1)
        match1 = re.compile('<div class="title">[\s]*<a [^>]+>(.+?)</a>').search(match[i])
        p_name = match1.group(1)
        p_name1 = p_name
        if match[i].find('<i class="ico-1080P"')>0:
            p_name1 += '[1080P]'
            p_res = 1
        elif match[i].find('<i class="ico-SD"')>0:
            p_name1 += '[超清]'
            p_res = 2
        elif match[i].find('<i class="ico-HD"')>0:
            p_name1 += '[高清]'
            p_res = 3
        else:
            p_res = 4
        li = xbmcgui.ListItem(p_name1, iconImage = '', thumbnailImage = p_thumb)
        u = sys.argv[0]+"?mode=10&name="+urllib.quote_plus(p_name)+"&id="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)+"&res="+str(p_res)
        #li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Cast":p_cast, "Tagline":p_tagline})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def progList2(name,id,page,genre,year,order):
    url = 'http://www.youku.com/v_showlist/t%sd%s%sg%sp%s.html' % (order, year, id, genre, page)
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
    match = re.compile('<div class="v">(.+?)</div>\s*</div>\s*</div>\s*</div>', re.DOTALL).findall(link)
    totalItems = len(match) + 1 + len(plist)
    currpage = int(page)

    genrelist = getList2(listpage, genre)
    if genre == '0':
        genrestr = '全部类型'
    else:
        genrestr = searchDict(genrelist,genre)
    li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）【[COLOR FFFF0000]' + genrestr + '[/COLOR]/[COLOR FF00FF00]' + searchDict(YEAR_LIST2,year) + '[/COLOR]/[COLOR FF00FFFF]' + searchDict(ORDER_LIST2,order) + '[/COLOR]】（按此选择）')
    u = sys.argv[0]+"?mode=12&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre="+urllib.quote_plus(genre)+"&year="+urllib.quote_plus(year)+"&order="+order+"&page="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    for i in range(0,len(match)):
        match1 = re.compile('<div class="v-link">\s*<a href="http://v.youku.com/v_show/id_(.+?)\.html"').search(match[i])
        p_id = match1.group(1)
        match1 = re.compile('<div class="v-thumb">\s*<img src="(.+?)"').search(match[i])
        p_thumb = match1.group(1)
        match1 = re.compile('<div class="v-meta-title">\s*<a [^>]+>(.+?)</a>').search(match[i])
        p_name = match1.group(1).replace('&quot;','"')
        p_name1 = p_name
        if match[i].find('<i class="ico-1080P"')>0:
            p_name1 += '[1080P]'
            p_res = 1
        elif match[i].find('<i class="ico-SD"')>0:
            p_name1 += '[超清]'
            p_res = 2
        elif match[i].find('<i class="ico-HD"')>0:
            p_name1 += '[高清]'
            p_res = 3
        else:
            p_res = 4
        li = xbmcgui.ListItem(str(i + 1) + '. ' + p_name1, iconImage = '', thumbnailImage = p_thumb)
        u = sys.argv[0]+"?mode=10&name="+urllib.quote_plus(p_name)+"&id="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)+"&res="+str(p_res)
        #li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Cast":p_cast, "Tagline":p_tagline})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)

    for num in plist:
        li = xbmcgui.ListItem("... 第" + num + "页")
        u = sys.argv[0]+"?mode=11&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&genre="+urllib.quote_plus(genre)+"&year="+year+"&order="+order+"&page="+str(num)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)         
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def selResolution(streamtypes):
    ratelist = []
    for i in range(0,len(streamtypes)):
        if streamtypes[i] == 'flv': ratelist.append([4, '标清', i]) # [清晰度设置值, 清晰度, streamtypes索引]
        if streamtypes[i] == 'mp4': ratelist.append([3, '高清', i])
        if streamtypes[i] == 'hd2': ratelist.append([2, '超清', i])
        if streamtypes[i] == 'hd3': ratelist.append([1, '1080P', i])
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
    return streamtypes[ratelist[sel][2]], ratelist[sel][1]

def PlayVideo(name,id,thumb,res):
    url = 'http://v.youku.com/player/getPlayList/VideoIDS/%s/ctype/12/ev/1' % (id)
    link = GetHttpData(url)
    json_response = simplejson.loads(link)

    vid = id
    lang_select = int(__addon__.getSetting('lang_select')) # 默认|每次选择|自动首选
    if lang_select != 0 and json_response['data'][0].has_key('dvd') and 'audiolang' in json_response['data'][0]['dvd']:
        langlist = json_response['data'][0]['dvd']['audiolang']
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
        url = 'http://v.youku.com/player/getPlayList/VideoIDS/%s/ctype/12/ev/1' % (vid)
        link = GetHttpData(url)
        json_response = simplejson.loads(link)

    typeid, typename = selResolution(json_response['data'][0]['streamtypes'])
    if typeid:
        video_id = json_response['data'][0]['videoid']
        oip = json_response['data'][0]['ip']
        ep = json_response['data'][0]['ep']
        ep, token, sid = youkuDecoder()._calc_ep2(video_id, ep)
        query = urllib.urlencode(dict(
            vid=video_id, ts=int(time.time()), keyframe=1, type=typeid,
            ep=ep, oip=oip, ctype=12, ev=1, token=token, sid=sid,
        ))
        movurl = 'http://pl.youku.com/playlist/m3u8?%s' % (query)

        #seed = json_response['data'][0]['seed']
        #fileId = json_response['data'][0]['streamfileids'][typeid].encode('utf-8')
        #fileId = youkuDecoder().getFileId(fileId,seed)
        #if typeid == 'mp4':
        #    type = 'mp4'
        #else:
        #    type = 'flv'
        #urls = []
        #for i in range(len(json_response['data'][0]['segs'][typeid])): 
        #    no = '%02X' % i
        #    k = json_response['data'][0]['segs'][typeid][i]['k'].encode('utf-8')
        #    urls.append('http://f.youku.com/player/getFlvPath/sid/00_00/st/%s/fileid/%s%s%s?K=%s' % (type, fileId[:8], no, fileId[10:], k))
        #stackurl = 'stack://' + ' , '.join(urls)
        name = '%s[%s]' % (name, typename)
        listitem=xbmcgui.ListItem(name,thumbnailImage=thumb)
        listitem.setInfo(type="Video",infoLabels={"Title":name})
        xbmc.Player().play(movurl, listitem)

def performChanges(name,id,listpage,genre,area,year,order):
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

    list = [x[1] for x in ORDER_LIST]
    sel = dialog.select('排序', list)
    if sel != -1:
        order = ORDER_LIST[sel][0]
        change = True

    if change:
        progList(name,id,'1',genre,area,year,order)

def performChanges2(name,id,listpage,genre,year,order):
    genrelist = getList2(listpage, genre)
    change = False
    dialog = xbmcgui.Dialog()
    if len(genrelist)>0:
        list = [x[1] for x in genrelist]
        sel = dialog.select('类型', list)
        if sel != -1:
            genre = genrelist[sel][0]
            change = True
    list = [x[1] for x in YEAR_LIST2]
    sel = dialog.select('范围', list)
    if sel != -1:
        year = YEAR_LIST2[sel][0]
        change = True
    list = [x[1] for x in ORDER_LIST2]
    sel = dialog.select('排序', list)
    if sel != -1:
        order = ORDER_LIST2[sel][0]
        change = True

    if change:
        progList2(name,id,'1',genre,year,order)

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
res = 0

try:
    res = int(params["res"])
except:
    pass
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

if mode == None:
    rootList()
elif mode == 1:
    progList(name,id,page,genre,area,year,order)
elif mode == 2:
    getMovie(name,id,thumb,res)
elif mode == 3:
    seriesList(name,id,thumb,res)
elif mode == 4:
    performChanges(name,id,page,genre,area,year,order)
elif mode == 10:
    PlayVideo(name,id,thumb,res)
elif mode == 11:
    progList2(name,id,page,genre,year,order)
elif mode == 12:
    performChanges2(name,id,page,genre,year,order)

