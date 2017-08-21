# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, string, sys, os, zlib
from uuid import uuid4
from random import random,randint
from math import floor
import hashlib
import time
import simplejson

# Plugin constants
__addonname__ = "奇艺视频(QIYI)"
__addonid__   = "plugin.video.qiyi"
__addon__     = xbmcaddon.Addon(id=__addonid__)

CHANNEL_LIST = [['电影','1'], ['电视剧','2'], ['纪录片','3'], ['动漫','4'], ['音乐','5'], ['综艺','6'], ['娱乐','7'], ['旅游','9'], ['片花','10'], ['教育','12'], ['时尚','13']]
ORDER_LIST = [['4','更新时间'], ['11','热门']]
PAYTYPE_LIST = [['','全部影片'], ['0','免费影片'], ['1','会员免费'], ['2','付费点播']]

def GetHttpData(url):
    print "getHttpData: " + url
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)')
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            httpdata = zlib.decompress(httpdata, zlib.MAX_WBITS|32)
        charset = response.headers.getparam('charset')
        response.close()
    except:
        xbmc.log( "%s: %s (%d) [%s]" % (
            __addonname__,
            sys.exc_info()[ 2 ].tb_frame.f_code.co_name,
            sys.exc_info()[ 2 ].tb_lineno,
            sys.exc_info()[ 1 ]
            ), level=xbmc.LOGERROR)
        return ''
    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    if len(match)>0:
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')
    return httpdata

def urlExists(url):
    try:
        resp = urllib2.urlopen(url)
        result = True
        resp.close()
    except:
        result = False
    return result

def searchDict(dlist,idx):
    for i in range(0,len(dlist)):
        if dlist[i][0] == idx:
            return dlist[i][1]
    return ''

def getcatList(listpage, id, cat):
    # 类型(电影,纪录片,动漫,娱乐,旅游), 分类(电视剧,综艺,片花), 流派(音乐), 一级分类(教育), 行业(时尚)
    match = re.compile('<h3>(类型|分类|流派|一级分类|行业)：</h3>(.*?)</ul>', re.DOTALL).findall(listpage)
    if id in ('3','9'):   # 纪录片&旅游
        catlist = re.compile('/www/' + id + '/(\d*)-[^>]+>(.*?)</a>').findall(match[0][1])
    elif id in ('5','10'):   # 音乐&片花
        catlist = re.compile('/www/' + id + '/\d*-\d*-\d*-(\d*)-[^>]+>(.*?)</a>').findall(match[0][1])
    elif id == '12':  # 教育
        catlist = re.compile('/www/' + id + '/\d*-\d*-(\d*)-[^>]+>(.*?)</a>').findall(match[0][1])
    elif id == '13':  # 时尚
        catlist = re.compile('/www/' + id + '/\d*-\d*-\d*-\d*-(\d*)-[^>]+>(.*?)</a>').findall(match[0][1])
    else:
        catlist = re.compile('/www/' + id + '/\d*-(\d*)-[^>]+>(.*?)</a>').findall(match[0][1])
    match1 = re.compile('<a href="#">(.*?)</a>').search(match[0][1])
    if match1:
        catlist.append((cat, match1.group(1)))
    return catlist

def getareaList(listpage, id, area):
    match = re.compile('<h3>地区：</h3>(.*?)</ul>', re.DOTALL).findall(listpage)
    if id == '7':   # 娱乐
        arealist = re.compile('/www/' + id + '/\d*-\d*-(\d*)-[^>]+>(.*?)</a>').findall(match[0])
    elif id in ('9','10'):   # 旅游&片花
        arealist = re.compile('/www/' + id + '/\d*-(\d*)-[^>]+>(.*?)</a>').findall(match[0])
    else:
        arealist = re.compile('/www/' + id + '/(\d*)-[^>]+>(.*?)</a>').findall(match[0])
    match1 = re.compile('<a href="#">(.*?)</a>').search(match[0])
    if match1:
        arealist.append((area, match1.group(1)))
    return arealist

def getyearList(listpage, id, year):
    match = re.compile('<h3>年代：</h3>(.*?)</ul>', re.DOTALL).findall(listpage)
    yearlist = re.compile('/www/' + id + '/\d*-\d*---------\d*-([\d_]*)-[^>]+>(.*?)</a>').findall(match[0])
    match1 = re.compile('<a href="#">(.*?)</a>').search(match[0])
    if match1:
        yearlist.append((year, match1.group(1)))
    return yearlist

def rootList():
    for name, id in CHANNEL_LIST:
        li = xbmcgui.ListItem(name)
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&cat="+urllib.quote_plus("")+"&area="+urllib.quote_plus("")+"&year="+urllib.quote_plus("")+"&order="+urllib.quote_plus("11")+"&page="+urllib.quote_plus("1")+"&paytype="+urllib.quote_plus("0")
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

#         id   c1   c2   c3   c4   c5     c11  c12   c14
# 电影     1 area  cat                paytype year order
# 电视剧   2 area  cat                paytype year order
# 纪录片   3  cat                     paytype      order
# 动漫     4 area  cat  ver  age      paytype      order
# 音乐     5 area lang       cat  grp paytype      order
# 综艺     6 area  cat                paytype      order
# 娱乐     7       cat area           paytype      order
# 旅游     9  cat area                paytype      order
# 片花    10      area       cat      paytype      order
# 教育    12            cat           paytype      order
# 时尚    13                      cat paytype      order
def progList(name,id,page,cat,area,year,order,paytype):
    c1 = ''
    c2 = ''
    c3 = ''
    c4 = ''
    if id == '7':          # 娱乐
        c3 = area
    elif id in ('9','10'): # 旅游&片花
        c2 = area
    elif id != '3':        # 非纪录片
        c1 = area
    if id in ('3','9'):    # 纪录片&旅游
        c1 = cat
    elif id in ('5','10'): # 音乐&片花
        c4 = cat
    elif id == '12':       # 教育
        c3 = cat
    elif id == '13':       # 时尚
        c5 = cat
    else:
        c2 = cat
    url = 'http://list.iqiyi.com/www/' + id + '/' + c1 + '-' + c2 + '-' + c3 + '-' + c4 + '-------' +\
                           paytype + '-' + year + '--' + order + '-' + page + '-1-iqiyi--.html'
    currpage = int(page)
    link = GetHttpData(url)
    match1 = re.compile('data-key="([0-9]+)"').findall(link)
    if len(match1) == 0:
        totalpages = 1
    else:
        totalpages = int(match1[len(match1) - 1])
    match = re.compile('<!-- 分类 -->(.+?)<!-- 分类 end-->', re.DOTALL).findall(link)
    if match:
        listpage = match[0]
    else:
        listpage = ''
    match = re.compile('<div class="wrapper-piclist"(.+?)<!-- 页码 开始 -->', re.DOTALL).findall(link)
    if match:
        match = re.compile('<li[^>]*>(.+?)</li>', re.DOTALL).findall(match[0])
    totalItems = len(match) + 1
    if currpage > 1: totalItems = totalItems + 1
    if currpage < totalpages: totalItems = totalItems + 1

    
    if cat == '':
        catstr = '全部类型'
    else:
        catlist = getcatList(listpage, id, cat)
        catstr = searchDict(catlist, cat)
    selstr = '[COLOR FFFF0000]' + catstr + '[/COLOR]'
    if not (id in ('3','12','13')):
        if area == '':
            areastr = '全部地区'
        else:
            arealist = getareaList(listpage, id, area)
            areastr = searchDict(arealist, area)
        selstr += '/[COLOR FF00FF00]' + areastr + '[/COLOR]'
    if id in ('1', '2'):
        if year == '':
            yearstr = '全部年份'
        else:
            yearlist = getyearList(listpage, id, year)
            yearstr = searchDict(yearlist, year)
        selstr += '/[COLOR FFFFFF00]' + yearstr + '[/COLOR]'
    selstr += '/[COLOR FF00FFFF]' + searchDict(ORDER_LIST, order) + '[/COLOR]'
    selstr += '/[COLOR FFFF00FF]' + searchDict(PAYTYPE_LIST, paytype) + '[/COLOR]'
    li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）【'+selstr+'】（按此选择）')
    u = sys.argv[0]+"?mode=4&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&cat="+urllib.quote_plus(cat)+"&area="+urllib.quote_plus(area)+"&year="+urllib.quote_plus(year)+"&order="+order+"&paytype="+urllib.quote_plus(paytype)+"&page="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    for i in range(0,len(match)):
        p_name = re.compile('alt="(.+?)"').findall(match[i])[0]
        p_thumb = re.compile('src\s*=\s*"(.+?)"').findall(match[i])[0]
        #p_id  = re.compile('data-qidanadd-albumid="(\d+)"').search(match[i]).group(1)
        p_id  = re.compile('href="([^"]*)"').search(match[i]).group(1)

        try:
            p_episode = re.compile('data-qidanadd-episode="(\d)"').search(match[i]).group(1) == '1'
        except:
            p_episode = False
        match1 = re.compile('<span class="icon-vInfo">([^<]+)</span>').search(match[i])
        if match1:
            msg = match1.group(1).strip()
            p_name1 = p_name + '（' + msg + '）'
            if (msg.find('更新至') == 0) or (msg.find('共') == 0):
                p_episode = True
        else:
            p_name1 =  p_name

        if p_episode:
            mode = 2
            isdir = True
            p_id  = re.compile('data-qidanadd-albumid="(\d+)"').search(match[i]).group(1)
        else:
            mode = 3
            isdir = False
        match1 = re.compile('<p class="dafen2">\s*<strong class="fRed"><span>(\d*)</span>([\.\d]*)</strong><span>分</span>\s*</p>').search(match[i])
        if match1:
            p_rating = float(match1.group(1)+match1.group(2))
        else:
            p_rating = 0
        match1 = re.compile('<span>导演：</span>(.+?)</p>', re.DOTALL).search(match[i])
        if match1:
            p_director = ' / '.join(re.compile('<a [^>]+>([^<]*)</a>').findall(match1.group(1)))
        else:
            p_director = ''
        match1 = re.compile('<em>主演:</em>(.+?)</div>', re.DOTALL).search(match[i])
        if match1:
            p_cast = re.compile('<a [^>]+>([^<]*)</a>').findall(match1.group(1))
        else:
            p_cast = []
        match1 = re.compile('<span>类型：</span>(.+?)</p>', re.DOTALL).search(match[i])
        if match1:
            p_genre = ' / '.join(re.compile('<a [^>]+>([^<]*)</a>').findall(match1.group(1)))
        else:
            p_genre = ''
        match1 = re.compile('<p class="s1">\s*<span>([^<]*)</span>\s*</p>').search(match[i])
        if match1:
            p_plot = match1.group(1)
        else:
            p_plot = ''
        li = xbmcgui.ListItem(str(i + 1) + '.' + p_name1, iconImage = '', thumbnailImage = p_thumb)
        li.setArt({ 'poster': p_thumb })
        u = sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(p_name)+"&id="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)
        li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Genre":p_genre, "Plot":p_plot, "Cast":p_cast, "Rating":p_rating})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isdir, totalItems)

    if currpage > 1:
        li = xbmcgui.ListItem('上一页')
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&cat="+urllib.quote_plus(cat)+"&area="+urllib.quote_plus(area)+"&year="+urllib.quote_plus(year)+"&order="+order+"&page="+urllib.quote_plus(str(currpage-1))+"&paytype="+paytype
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    if currpage < totalpages:
        li = xbmcgui.ListItem('下一页')
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&cat="+urllib.quote_plus(cat)+"&area="+urllib.quote_plus(area)+"&year="+urllib.quote_plus(year)+"&order="+order+"&page="+urllib.quote_plus(str(currpage+1))+"&paytype="+paytype
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def seriesList(name,id,thumb,page):
    url = 'http://cache.video.qiyi.com/a/%s' % (id)
    link = GetHttpData(url)
    data = link[link.find('=')+1:]
    json_response = simplejson.loads(data)
    if json_response['data']['tvYear']:
        p_year = int(json_response['data']['tvYear'])
    else:
        p_year = 0
    p_director = ' / '.join(json_response['data']['directors']).encode('utf-8')
    p_cast = [x.encode('utf-8') for x in json_response['data']['mainActors']]
    p_plot = json_response['data']['tvDesc'].encode('utf-8')

    albumType = json_response['data']['albumType']
    sourceId = json_response['data']['sourceId']
    if albumType in (1, 6, 9, 12, 13) and sourceId<>0:
        url = 'http://cache.video.qiyi.com/jp/sdvlst/%d/%d/?categoryId=%d&sourceId=%d' % (albumType, sourceId, albumType, sourceId)
        link = GetHttpData(url)
        data = link[link.find('=')+1:]
        json_response = simplejson.loads(data)
        totalItems = len(json_response['data'])
        for item in json_response['data']:
            tvId = str(item['tvId'])
            videoId = item['vid'].encode('utf-8')
            p_id = '%s,%s' % (tvId, videoId)
            p_thumb = item['aPicUrl'].encode('utf-8')
            p_name = item['videoName'].encode('utf-8')
            p_name = '%s %s' % (p_name, item['tvYear'].encode('utf-8'))
            li = xbmcgui.ListItem(p_name, iconImage = '', thumbnailImage = p_thumb)
            li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Cast":p_cast, "Plot":p_plot, "Year":p_year})
            u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(p_name) + "&id=" + urllib.quote_plus(p_id)+ "&thumb=" + urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
    else:
        url = 'http://cache.video.qiyi.com/avlist/%s/%s/' % (id, page)
        link = GetHttpData(url)
        data = link[link.find('=')+1:]
        json_response = simplejson.loads(data)
        totalItems = len(json_response['data']['vlist']) + 1
        totalpages = json_response['data']['pgt']
        currpage = int(page)
        if currpage > 1: totalItems = totalItems + 1
        if currpage < totalpages: totalItems = totalItems + 1
        li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）')
        u = sys.argv[0]+"?mode=99"
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)

        for item in json_response['data']['vlist']:
            tvId = str(item['id'])
            videoId = item['vid'].encode('utf-8')
            p_id = '%s,%s' % (tvId, videoId)
            p_thumb = item['vpic'].encode('utf-8')
            p_name = item['vn'].encode('utf-8')
            if item['vt']:
                p_name = '%s %s' % (p_name, item['vt'].encode('utf-8'))
            li = xbmcgui.ListItem(p_name, iconImage = '', thumbnailImage = p_thumb)
            li.setArt({ 'poster': thumb })
            li.setInfo(type = "Video", infoLabels = {"Title":p_name, "Director":p_director, "Cast":p_cast, "Plot":p_plot, "Year":p_year})
            u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(p_name) + "&id=" + urllib.quote_plus(p_id)+ "&thumb=" + urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)

        if currpage > 1:
            li = xbmcgui.ListItem('上一页')
            u = sys.argv[0]+"?mode=2&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&thumb="+urllib.quote_plus(thumb)+"&page="+urllib.quote_plus(str(currpage-1))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
        if currpage < totalpages:
            li = xbmcgui.ListItem('下一页')
            u = sys.argv[0]+"?mode=2&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&thumb="+urllib.quote_plus(thumb)+"&page="+urllib.quote_plus(str(currpage+1))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, totalItems)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def selResolution(items):
    # stream_types = [
    #     {'id': '4k', 'container': 'm3u8', 'video_profile': '4k'},
    #     {'id': 'BD', 'container': 'm3u8', 'video_profile': '1080p'},
    #     {'id': 'TD', 'container': 'm3u8', 'video_profile': '720p'},
    #     {'id': 'TD_H265', 'container': 'm3u8', 'video_profile': '720p H265'},
    #     {'id': 'HD', 'container': 'm3u8', 'video_profile': '540p'},
    #     {'id': 'HD_H265', 'container': 'm3u8', 'video_profile': '540p H265'},
    #     {'id': 'SD', 'container': 'm3u8', 'video_profile': '360p'},
    #     {'id': 'LD', 'container': 'm3u8', 'video_profile': '210p'},
    # ]
    # vd_2_id = {10: '4k', 19: '4k', 5:'BD', 18: 'BD', 21: 'HD_H265', 2: 'HD', 4: 'TD', 17: 'TD_H265', 96: 'LD', 1: 'SD', 14: 'TD'}
    # id_2_profile = {'4k':'4k', 'BD': '1080p','TD': '720p', 'HD': '540p', 'SD': '360p', 'LD': '210p', 'HD_H265': '540p H265', 'TD_H265': '720p H265'}

    ratelist = []
    for i in range(0,len(items)):
        if items[i] == 96: ratelist.append([7, '极速', i])    # 清晰度设置值, 清晰度, match索引
        elif items[i] == 1: ratelist.append([6, '流畅', i])
        elif items[i] == 2: ratelist.append([5, '标清', i])
        elif items[i] == 21: ratelist.append([5, '标清 H265', i])
        elif items[i] == 3: ratelist.append([4, '超清', i])
        elif items[i] in (4, 14): ratelist.append([3, '720P', i])
        elif items[i] == 17: ratelist.append([3, '720p H265', i])
        elif items[i] in (5, 12, 18): ratelist.append([2, '1080P', i])
        elif items[i] in (10, 19): ratelist.append([1, '4K', i])
        else:
            ratelist.append([8, '未知', i])
    ratelist.sort()
    if len(ratelist) > 1:
        resolution = int(__addon__.getSetting('resolution'))
        if resolution == 0:    # 每次询问点播视频清晰度
            dialog = xbmcgui.Dialog()
            list = [x[1] for x in ratelist]
            sel = dialog.select('清晰度（低网速请选择低清晰度）', list)
            if sel == -1:
                return -1
        else:
            sel = 0
            while sel < len(ratelist)-1 and resolution > ratelist[sel][0]: sel =  sel + 1
    else:
        sel = 0
    return ratelist[sel][2]

def getVMS(tvid, vid):
    t = int(time.time() * 1000)
    src = '76f90cbd92f94a2e925d83e8ccd22cb7'
    key = 'd5fb4bd9d50c4be6948c97edd7254b0e'
    sc = hashlib.md5(str(t) + key  + vid).hexdigest()
    vmsreq = 'http://cache.m.iqiyi.com/tmts/{0}/{1}/?t={2}&sc={3}&src={4}'.format(tvid,vid,t,sc,src)
    print vmsreq
    return simplejson.loads(GetHttpData(vmsreq))

def PlayVideo(name,id,thumb):
    id = id.split(',')
    if len(id) == 1:
        try:
            if ("http:" in id[0]):
                link = GetHttpData(id[0])
                tvId = re.compile('data-player-tvid="(.+?)"', re.DOTALL).findall(link)[0]
                videoId = re.compile('data-player-videoid="(.+?)"', re.DOTALL).findall(link)[0]
            else:
                url = 'http://cache.video.qiyi.com/avlist/%s/' % (id[0])
                link = GetHttpData(url)
                data = link[link.find('=')+1:]
                json_response = simplejson.loads(data)
                tvId = str(json_response['data']['vlist'][0]['id'])
                videoId = json_response['data']['vlist'][0]['vid'].encode('utf-8')
        except:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '未能获取视频地址')
            return
    else:
         tvId = id[0]
         videoId = id[1]

    info = getVMS(tvId, videoId)
    if info["code"] != "A00000":
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__, '无法播放此视频')
        return

    vs = info["data"]["vidl"]
    sel = selResolution([x['vd'] for x in vs])
    if sel == -1:
        return

    video_links = vs[sel]["m3u"]

    listitem = xbmcgui.ListItem(name,thumbnailImage=thumb)
    listitem.setInfo(type="Video",infoLabels={"Title":name})
    xbmc.Player().play(video_links, listitem)

def performChanges(name,id,listpage,cat,area,year,order,paytype):
    change = False
    catlist= getcatList(listpage, id, cat)
    dialog = xbmcgui.Dialog()
    if len(catlist)>0:
        list = [x[1] for x in catlist]
        sel = dialog.select('类型', list)
        if sel != -1:
            cat = catlist[sel][0]
            change = True
    if not (id in ('3','12','13')):
        arealist = getareaList(listpage, id, area)
        if len(arealist)>0:
            list = [x[1] for x in arealist]
            sel = dialog.select('地区', list)
            if sel != -1:
                area = arealist[sel][0]
                change = True       
    if id in ('1','2'):
        yearlist = getyearList(listpage, id, year)
        if len(yearlist)>0:
            list = [x[1] for x in yearlist]
            sel = dialog.select('年份', list)
            if sel != -1:
                year = yearlist[sel][0]
                change = True
    list = [x[1] for x in ORDER_LIST]
    sel = dialog.select('排序方式', list)
    if sel != -1:
        order = ORDER_LIST[sel][0]
        change = True
    if change:
        progList(name,id,'1',cat,area,year,order,paytype)

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
order = '3'
paytype = '0'
num = '1'
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
    num = urllib.unquote_plus(params["num"])
except:
    pass
try:
    res = urllib.unquote_plus(params["paytype"])
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
    progList(name,id,page,cat,area,year,order,paytype)
elif mode == 2:
    seriesList(name,id,thumb,page)
elif mode == 3:
    PlayVideo(name,id,thumb)
elif mode == 4:
    performChanges(name,id,page,cat,area,year,order,paytype)
