#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
from xbmcswift2 import Plugin
import requests
from bs4 import BeautifulSoup
import xbmcgui
import base64
import json
import urllib2
import sys
import HTMLParser
import re
import time



def unescape(string):
    string = urllib2.unquote(string).decode('utf8')
    quoted = HTMLParser.HTMLParser().unescape(string).encode('utf-8')
    #转成中文
    return re.sub(r'%u([a-fA-F0-9]{4}|[a-fA-F0-9]{2})', lambda m: unichr(int(m.group(1), 16)), quoted)


plugin = Plugin()

reqid = 0
uid = '_26187_'
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
his = plugin.get_storage('his')
cache = plugin.get_storage('cache')

def del_kr(txt):
    while True:
        if re.search('\[(.*?)\]/(http|https):\/\/([\w.]+\/?)\S*/',txt):
            txt = txt.replace(re.search('\[(.*?)\]/(http|https):\/\/([\w.]+\/?)\S*/',txt).group(),'(图片)')
        else:
            if re.search('\[(.*?)\]',txt):
                txt = txt.replace(re.search('\[(.*?)\]',txt).group(),'（表情）')
            else:
                break
    return txt

def get_categories():
    return [{'name':'综合','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'番剧','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=155&subChannelId=&rankLimit=30&rankPeriod=WEEK'},
            {'name':'动画','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=1&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'娱乐','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=60&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'生活','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=201&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'音乐','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=58&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'舞蹈·偶像','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=123&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'游戏','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=59&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'科技','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=70&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'影视','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=68&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'体育','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=69&subChannelId=&rankLimit=100&rankPeriod=WEEK'},
            {'name':'鱼塘','link':'https://www.acfun.cn/rest/pc-direct/rank/channel?channelId=125&subChannelId=&rankLimit=100&rankPeriod=WEEK'}]

@plugin.cached(TTL=2)
def get_search(keyword, page):
    serachUrl = 'https://www.acfun.cn/rest/pc-direct/search/video?keyword=' + keyword + '&pCursor=' + str(page)

    r = requests.get(serachUrl, headers=headers)
    r.encoding = 'UTF-8'
    rtext = r.text
    j = json.loads(rtext)
    #dialog = xbmcgui.Dialog()
    #ok = dialog.ok('错误提示', str(j['videoList'][0]['id']))
    videos = []
    if 'videoList' in j:
        for index in range(len(j['videoList'])):
            videoitem = {}
            videoitem['name'] = j['videoList'][index]['title']
            videoitem['href'] = 'https://www.acfun.cn/v/ac'+ str(j['videoList'][index]['id'])
            videoitem['thumb'] = j['videoList'][index]['coverUrl']
            videos.append(videoitem)
        dialog = xbmcgui.Dialog()
        dialog.notification('当前'+ str(page) + '/' + str(j['pageNum']) + '页', '总共'+ str(j['totalNum']) + '个视频', xbmcgui.NOTIFICATION_INFO, 5000,False)
    else:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('错误提示', '搜索结果为空')
    return videos

@plugin.cached(TTL=2)
def get_bgm_search(keyword,page):
    serachUrl = 'https://www.acfun.cn/search?type=bgm&keyword=' + keyword + '&pCursor=' +str(page)
    videos = []
    r = requests.get(serachUrl, headers=headers)
    r.encoding = 'UTF-8'
    rtext = r.text
    rtext = rtext.encode('utf-8')
    soup = BeautifulSoup(rtext,'html.parser')
    bgmlist = soup.find('div',class_='bangumi-list')
    vlist = bgmlist.find_all('div',class_='search-bangumi')
    for index in range(len(vlist)):
        ahref = vlist[index].a['href']
        img = vlist[index].find('div',class_='bangumi__cover')
        title = img.img['alt']
        img = img.img['src']
        img = img.split('?')
        videoitem = {}
        videoitem['name'] = title
        videoitem['href'] = 'https://www.acfun.cn'+ ahref
        videoitem['thumb'] = img[0]
        videos.append(videoitem)
    return videos

@plugin.cached(TTL=2)
def get_up(uid,page):
    videos = []
    apiurl = 'https://www.acfun.cn/space/next?uid='+str(uid)+'&type=video&orderBy=2&pageNo=' +str(page)
    rec = requests.get(apiurl,headers=headers)
    #print(rec.text)
    j = json.loads(rec.text)
    dialog = xbmcgui.Dialog()
    dialog.notification('当前'+ str(j['data']['page']['pageNo']) + '/' + str(j['data']['page']['totalPage']) + '页', '总共'+ str(j['data']['page']['totalCount']) + '个视频', xbmcgui.NOTIFICATION_INFO, 5000,False)
    html = j['data']['html']
    soup = BeautifulSoup(html,'html.parser')
    #print(html)
    fig = soup.find_all('figure')
    #print(len(fig))
    for index in range(len(fig)):
        videoitem = {}
        videoitem['name'] = fig[index]['data-title']
        videoitem['href'] = 'https://www.acfun.cn'+fig[index]['data-url']
        videoitem['thumb'] = fig[index].img['src']
        videos.append(videoitem)
    return videos

@plugin.cached(TTL=2)
def get_comm(val,st):
    url = 'https://www.acfun.cn/rest/pc-direct/comment/list?sourceId=' + val + '&sourceType=' + st + '&page=1&pivotCommentId=&newPivotCommentId=&t=' +str(time.time())
    rec = requests.get(url,headers=headers)
    rec.encoding ='utf-8'
    #print(rec.text)

    j = json.loads(rec.text)
    n = '\n'
    text = ('*-'*20)+'热门评论'+('*-'*20) + '\n' +n
    hc = j['hotComments']
    scm = j['subCommentsMap']
    for index in range(len(hc)):
        text +='-----'*30 +n
        text +=hc[index]['userName'].encode('utf-8') + '      - 发表于'+ hc[index]['postDate'].encode('utf-8') +'\n' +n
        text +=del_kr(hc[index]['content'].encode('utf-8'))+'\n' +n
        text +='赞 '+hc[index]['likeCountFormat'].encode('utf-8')+ '      - 来自'+ hc[index]['deviceModel'].encode('utf-8') +n
        text +='-----'*30 +n
        if str(hc[index]['commentId']) in scm.keys():
            sc = scm[str(hc[index]['commentId'])]['subComments']
            for index in range(len(sc)):
                text +='-----'*30 +n
                text +=(' '*10)+sc[index]['userName'].encode('utf-8') + '      - 发表于'+ sc[index]['postDate'].encode('utf-8') +'\n' +n
                text +=(' '*10)+del_kr(sc[index]['content'].encode('utf-8'))+'\n' +n
                text +=(' '*10)+'赞 '+sc[index]['likeCountFormat'].encode('utf-8')+ '      - 来自'+ sc[index]['deviceModel'].encode('utf-8') +n
                text +='-----'*30 +n
    text +=('*-'*20)+'最新评论'+('*-'*20) +n
    rc = j['rootComments']
    for index in range(len(rc)):
        text +='-----'*30 +n
        text +=rc[index]['userName'].encode('utf-8') + '      - 发表于'+ rc[index]['postDate'].encode('utf-8') +'\n' +n
        text +=del_kr(rc[index]['content'].encode('utf-8'))+'\n' +n
        text +='赞 '+rc[index]['likeCountFormat'].encode('utf-8')+ '      - 来自'+ rc[index]['deviceModel'].encode('utf-8') +n
        text +='-----'*30
        if str(rc[index]['commentId']) in scm.keys():
            sc = scm[str(rc[index]['commentId'])]['subComments']
            for index in range(len(sc)):
                text +='-----'*30 +n
                text +=(' '*10)+sc[index]['userName'].encode('utf-8') + '      - 发表于'+ sc[index]['postDate'].encode('utf-8') +'\n' +n
                text +=(' '*10)+del_kr(sc[index]['content'].encode('utf-8'))+'\n' +n
                text +=(' '*10)+'赞 '+sc[index]['likeCountFormat'].encode('utf-8')+ '      - 来自'+ sc[index]['deviceModel'].encode('utf-8') +n
                text +='-----'*30 +n
    return text

@plugin.cached(TTL=2)
def get_bangumi(page):
    url = 'https://www.acfun.cn/bangumilist?pageNum=' + str(page)
    videos = []
    rec = requests.get(url,headers=headers)
    soup = BeautifulSoup(rec.text,'html.parser')
    li = soup.find_all('li',class_='ac-mod-li')
    for index in range(len(li)):
        span = li[index].find('span')
        em = li[index].find('em')
        img = li[index].a.div.img['src']
        img = img.split('?')
        videoitem = {}
        videoitem['name'] = span.text + '['+em.text+']'
        videoitem['href'] = plugin.url_for('sources', url=li[index].a['href'])
        videoitem['thumb'] = img[0]
        videos.append(videoitem)
    return videos

@plugin.cached(TTL=2)
def get_videos(category):
#爬视频列表的
    pageurl = category
    r = requests.get(pageurl, headers=headers)
    r.encoding = 'UTF-8'
    rtext= r.text
    j = json.loads(rtext.encode('utf-8'))

    k = j['rankList']
    
    videos = []
    for index in range(len(k)):
            item = k[index]
            videoitem = {}
            videoitem['name'] = item['contentTitle']
            videoitem['href'] = 'https://www.acfun.cn/v/ac' + item['dougaId']
            videoitem['thumb'] = item['coverUrl']
            videos.append(videoitem)
    return videos

@plugin.cached(TTL=2)
def get_sources(url):
    #ifmurl = re.match('https://m.acfun.cn',url)
    #if ifmurl != None:
        #url = 'https://www' + url[9:21] + 'ac' + url[25:]
    
    sources = []
    #dialog = xbmcgui.Dialog()
    #ok = dialog.ok('错误提示', url)
    rec = requests.get(url,headers=headers)
    rec.encoding = 'utf-8'
    soup = BeautifulSoup(rec.text, "html5lib")
    if404 = soup.find_all('div', class_='img404')
    
        
        #print(rec.text)
    rectext = rec.text

    cutjson = rectext.encode('utf-8')
    if cutjson.find('window.pageInfo = window.videoInfo = ') != -1:
        str1 = cutjson.find('window.pageInfo = window.videoInfo = ')

        try:
            str2 = cutjson.find('window.videoResource =')
            videoinfo = cutjson[str1+37:str2-10]
            # dialog = xbmcgui.Dialog()
            # dialog.textviewer('错误提示', videoinfo)
            j = json.loads(videoinfo)
            if len(j['videoList']) == 1:
                videosource = {}
                #print('视频标题：')
                videosource['name'] = j['title']
                #print('视频图片：')
                #videosource['thumb'] = '12'
                #print('视频地址：')
                videosource['href'] = plugin.url_for('play', url=url)
                #videosource['category'] = '番剧'
                sources.append(videosource)
                
            else:
                for index in range(len(j['videoList'])):
                    videosource = {}
                    videosource['name'] = j['videoList'][index]['title']
                    videosource['href'] = plugin.url_for('play', url=url + '_' +str(index+1))
                    sources.append(videosource)
                
        except ValueError:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('错误提示', '错误404，咦？世界线变动了，你好像来到了奇怪的地方。看看其他内容吧~')
            
    if cutjson.find('window.pageInfo = window.bangumiData = ') != -1:
        #番剧
        str1 = cutjson.find('window.bangumiList')
        str2 = cutjson.find('window.abtestConfig = ')
        bgm = cutjson[str1+21:str2-28]
        j = json.loads(bgm)
        for index in range(len(j['items'])):
            videosource = {}
            videosource['name'] = j['items'][index]['episodeName']
            videosource['href'] = plugin.url_for('play', url=url+uid+str(j['items'][index]['itemId']) + '_' +str(index+1))
            sources.append(videosource)
        #dialog = xbmcgui.Dialog()
        #dialog.textviewer('错误提示',vid)
    return sources


@plugin.route('/sources/<url>/')
def sources(url):
    sources = get_sources(url)
    items = [{
        'label': source['name'],
        'path': source['href'],
        #'thumbnail': source['thumb'],
        #'icon': source['thumb'],
    } for source in sources]
    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items


@plugin.route('/category/<url>/')
def category(url):
    #dialog = xbmcgui.Dialog()
    #ok = dialog.ok('错误提示', url)


    videos = get_videos(url)
    items = [{
        'label': video['name'],
        'path': plugin.url_for('sources', url=video['href']),
	'thumbnail': video['thumb'],
	'icon': video['thumb'],
    } for video in videos]

    sorted_items = items
    #sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items

@plugin.route('/bamgumi/<page>/')
def bangumi(page):
    #dialog = xbmcgui.Dialog()
    #ok = dialog.ok('错误提示', url)

    
    videos = get_bangumi(page)
    
    items = [{
        'label': video['name'],
        'path': video['href'],
	'thumbnail': video['thumb'],
	'icon': video['thumb'],
    } for video in videos]
    num = len(items)
    if num == 42:
        items.append({
        'label': u'[COLOR yellow]下一页[/COLOR]',
        'path': plugin.url_for('bangumi',page=str(int(page)+1)),
    })
    sorted_items = items
    #sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items

@plugin.route('/')
def index():
    categories = get_categories()
    items = [{
        'label': category['name'],
        'path': plugin.url_for('category', url=category['link']),
    } for category in categories]
    items.append({
        'label': u'[COLOR yellow]真·番剧[/COLOR]',
        'path': plugin.url_for('bangumi',page=1),
    })
    items.append({
        'label': u'[COLOR yellow]搜索（视频）[/COLOR]',
        'path': plugin.url_for('history',name='输入关键词搜索视频',url='search'),
    })
    items.append({
        'label': u'[COLOR yellow]搜索（番剧）[/COLOR]',
        'path': plugin.url_for('history',name='输入关键词搜索番剧',url='bgmsearch'),
    })
    items.append({
        'label': u'[COLOR yellow]输入ac号[/COLOR]',
        'path': plugin.url_for('history',name='输入ac号',url='ac'),
    })
    return items

@plugin.route('/search/<value>/<page>/')
def search(value,page):
    if value != 'null' and int(page) != 1:
        keyword = value
    else:
        keyboard = xbmc.Keyboard('', '请输入搜索内容')
        xbmc.sleep(1500)
        hi = his['search']
        if value != 'null':
            keyboard.setDefault(value)
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            keyword = keyboard.getText()
            if keyword != '':
                hi[keyword] = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) )
    videos = get_search(keyword, page)
    items = [{
        'label': video['name'],
        'path': plugin.url_for('sources', url=video['href']),
        'thumbnail': video['thumb'],
        'icon': video['thumb']
    } for video in videos]

    
    if len(videos) == 30:
        nextpage = {'label': ' 下一页', 'path': plugin.url_for('search', value=keyword, page=str(int(page)+1))}
        items.append(nextpage)
    return items

@plugin.route('/bgmsearch/<value>/<page>/')
def bgmsearch(value,page):
    if value != 'null' and int(page) != 1:
        keyword = value
    else:
        keyboard = xbmc.Keyboard('', '请输入搜索内容')
        xbmc.sleep(1500)
        hi = his['bgmsearch']
        if value != 'null':
            keyboard.setDefault(value)
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            keyword = keyboard.getText()
            if keyword != '':
                hi[keyword] = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) )
    videos = get_bgm_search(keyword,page)
    items = [{
        'label': video['name'],
        'path': plugin.url_for('sources', url=video['href']),
        'thumbnail': video['thumb'],
        'icon': video['thumb']
    } for video in videos]
    if len(videos) == 30:
        nextpage = {'label': ' 下一页', 'path': plugin.url_for('bgmsearch', value=keyword, page=str(int(page)+1))}
        items.append(nextpage)
    return items

def get_key (dict, value):
  return [k for k, v in dict.items() if v == value]

@plugin.route('/history/<name>/<url>/')
def history(name,url):
    items = []
    if url == 'search' or url == 'bgmsearch':
        items.append({
            'label': '[COLOR yellow]'+ name +'[/COLOR]',
            'path': plugin.url_for(url,value='null',page=1),
        })
    else:
        items.append({
            'label': '[COLOR yellow]'+ name +'[/COLOR]',
            'path': plugin.url_for(url,value='null'),
        })
    #his[url] ={'aaa':'2019-01-23 10:00:00','bbb':'2019-01-23 09:01:00','ccc':'2019-01-23 09:00:59'}
    if url in his:
        hi = his[url]
        
    else:
        his[url] = {}
        hi = his[url]
        
    #hi = []
    if hi:
        val = list(hi.values())
        val = sorted(val,reverse=True)
        for index in range(len(val)):
            if url == 'search' or url == 'bgmsearch':
                items.append({
                    'label': name+ ':' +get_key(hi,val[index])[0] + ' - [查询时间：' + val[index] +']',
                    'path': plugin.url_for(url,value=get_key(hi,val[index])[0],page=1),
                })
            else:
                items.append({
                    'label': name+ ':' +get_key(hi,val[index])[0] + ' - [查询时间：' + val[index] +']',
                    'path': plugin.url_for(url,value=get_key(hi,val[index])[0]),
                })
        #for index in range(len(hi)):
            #items.append({
                #'label': name+ ':' +hi[index],
                #'path': plugin.url_for(url,value=hi[index]),
            #})
        items.append({
            'label': '[COLOR yellow]清除历史记录[/COLOR]',
            'path': plugin.url_for('cleanhis',url=url),
        })
    else:
        items.append({
            'label': '[COLOR yellow]历史记录为空[/COLOR]',
            'path': plugin.url_for(ok,value='历史记录为空'),
        })

    return items

@plugin.route('/ac/<value>/')
def ac(value):
    if value == 'null':
        keyboard = xbmc.Keyboard('', '请输入ac号：')
        xbmc.sleep(1500)
        keyboard.doModal()

        hi = his['ac']
        if (keyboard.isConfirmed()):
            keyword = keyboard.getText()
            hi[keyword] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
    else:
        if keyword != '':
            keyword = value
    sources = get_sources('https://www.acfun.cn/v/ac'+str(keyword))
    items = [{
        'label': source['name'],
        'path': source['href'],
        #'thumbnail': source['thumb'],
        #'icon': source['thumb'],
    } for source in sources]
    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items

@plugin.route('/conn/<value>/<st>/')
def conn(value,st):
    text = get_comm(value,st)
    dialog = xbmcgui.Dialog()
    dialog.textviewer('评论区',text)

@plugin.route('/ok/<value>/')
def ok(value):
    dialog = xbmcgui.Dialog()
    ok = dialog.ok('提示', value)

@plugin.route('/cleanhis/<url>/')
def cleanhis(url):
    his[url] = {}
    dialog = xbmcgui.Dialog()
    ok = dialog.ok('提示', '清理历史记录成功')

@plugin.cached(TTL=2)
@plugin.route('/play/<url>/')
def play(url):

    rec = requests.get(url,headers=headers)
    rec.encoding = 'utf-8'
    #print(rec.text)
    rectext = rec.text
    cutjson = rectext.encode('utf-8')
    if cutjson.find('window.pageInfo = window.videoInfo = ') != -1:
        str1 = cutjson.find('window.pageInfo = window.videoInfo = ')
        str2 = cutjson.find('window.videoResource =')
        videoinfo = cutjson[str1+37:str2-10]
        j = json.loads(videoinfo)
        mp4info = {}
        mp4info['title'] = j['title']
        st = '1'
        #简介 plot
        #ac = ac.encode('utf-8')
        uptime = str(j['createTimeMillis'])
        uptime = uptime[:-3]
        uptime = int(uptime)
        #转换成localtime
        time_local = time.localtime(uptime)
        #转换成新的时间格式(2016-05-05 20:28:54)
        uptime = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
        data = time.strftime("%Y-%m-%d",time_local)
        #ac号 显示评论区用
        pinglunqu = j['commentCountShow'].encode('utf-8')
        vid = j['dougaId'].encode('utf-8')

        jianjie =  j['viewCountShow'].encode('utf-8') + '播放 | ' + j['danmakuCountShow'].encode('utf-8') + '弹幕 | ' + j['commentCountShow'].encode('utf-8') +'评论\n'
        jianjie += str(j['likeCount']).encode('utf-8') + '赞 | ' + j['stowCountShow'].encode('utf-8') + '收藏 | ' + j['bananaCountShow'].encode('utf-8')  + '香蕉'
        jianjie += '\n--------------------------\n'
        jianjie += '发布时间：' + uptime +' \nac号：ac' +j['dougaId'].encode('utf-8')
        jianjie += '\n--------------------------\n'
        try:
            mp4info['plot'] = jianjie  + j['description'].encode('utf-8')
        except AttributeError:
            mp4info['plot'] = jianjie 

        #分类 genre	
        genre = [j['channel']['parentName'],j['channel']['name']]
        mp4info['genre'] = genre
    
        #发布时间
        mp4info['aired'] = data
        #up主 cast
        fan = str(j['user']['fanCount'].encode('utf-8')) + '粉丝'
        fan = fan.decode('utf-8')
        mp4info['cast'] = [(j['user']['name'],fan)]
        #tag
        tag = []
        if 'tagList' in j:
            for index in range(len(j['tagList'])):
                tag.append(j['tagList'][index]['name'])
        mp4info['tag'] = tag
        #设置类型
        mp4info['mediatype'] = 'video'
        videojson =j ['currentVideoInfo']['ksPlayJson']
        j2 = json.loads(videojson)


        items = []
        if len(j2['adaptationSet']['representation']) == 1 :
            title = '['+j2['adaptationSet']['representation'][0]['qualityType'] + ']' + j['title']
            path = j2['adaptationSet']['representation'][0]['url']
            item = {'label': title,'path':path,'is_playable': True,'info':mp4info,'info_type':'video','thumbnail': j['coverCdnUrls'][0]['url'],'icon': j['coverCdnUrls'][0]['url']}
        
            items.append(item)
        #return items
        else:
            for index in range(len(j2['adaptationSet']['representation'])):
                #print(j2['adaptationSet']['representation'][index]['qualityType'])
                #print(j2['adaptationSet']['representation'][index]['url'])
                title = '['+j2['adaptationSet']['representation'][index]['qualityType'] + ']' + j['title']
                path = j2['adaptationSet']['representation'][index]['url']
                item = {'label': title,'path':path,'is_playable': True,'info':mp4info,'info_type':'video','thumbnail': j['coverCdnUrls'][0]['url'],'icon': j['coverCdnUrls'][0]['url']}
        
                items.append(item)
        items.append({
            'label': '[COLOR yellow]查看UP主 [/COLOR]'+j['user']['name'].encode('utf-8')+'[COLOR yellow] 的更多视频[/COLOR]',
            'path': plugin.url_for(up,uid=j['user']['id'],page=1),
        })
    if cutjson.find('window.pageInfo = window.bangumiData = ') != -1:
        #番剧
        str1 = cutjson.find('window.pageInfo = window.bangumiData = ')
        str2 = cutjson.find('window.qualityConfig = ')
        bgm = cutjson[str1+39:str2-10]
        #dialog = xbmcgui.Dialog()
        #dialog.textviewer('错误提示',bgm)
        j = json.loads(bgm)
        bgmjson =j ['currentVideoInfo']['ksPlayJson']
        j2 = json.loads(bgmjson)
        items = []
        mp4info = {}
        mp4info['title'] = j['bangumiTitle']
        st = '2'
        #简介 plot
        #ac = ac.encode('utf-8')
        uptime = str(j['currentVideoInfo']['uploadTime'])
        uptime = uptime[:-3]
        uptime = int(uptime)
        #转换成localtime
        time_local = time.localtime(uptime)
        #转换成新的时间格式(2016-05-05 20:28:54)
        uptime = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
        data = time.strftime("%Y-%m-%d",time_local)


        jianjie =  j['playCountShow'].encode('utf-8') + '播放 | ' + j['currentVideoInfo']['danmakuCountShow'].encode('utf-8') + '弹幕 | ' + j['commentCountShow'].encode('utf-8') +'评论\n'
        jianjie += j['extendsStatus'].encode('utf-8') + ' | ' + j['latestItem'].encode('utf-8') + ' | ' + j['stowCountShow'].encode('utf-8')  + '追番'
        jianjie += '\n--------------------------\n'
        jianjie += '发布时间：' + uptime +' \n链接：' +j['shareUrl'].encode('utf-8')
        jianjie += '\n--------------------------\n'
        try:
            mp4info['plot'] = jianjie  + j['bangumiIntro'].encode('utf-8')
        except AttributeError:
            mp4info['plot'] = jianjie 
        #pinglunqu
        pinglunqu = j['commentCountShow'].encode('utf-8')

        #分类 genre	
        genre = []
        for index in range(len(j['bangumiStyleList'])):
            genre.append(j['bangumiStyleList'][index]['name'])

        mp4info['genre'] = genre
    
        #发布时间
        mp4info['aired'] = data
        #追番人数 cast
        fan = j['stowCountShow'].encode('utf-8') + '追番'
        fan = fan.decode('utf-8')
        mp4info['cast'] = [(j['bangumiTitle'],fan)]
        #tag
        mp4info['tag'] = genre
        #设置类型
        mp4info['mediatype'] = 'video'
        #img
        img = j['bangumiCoverImageV'].split('?')
        img = img[0]
        vid = str(j['bangumiId']).encode('utf-8')
        for index in range(len(j2['adaptationSet']['representation'])):
            #print(j2['adaptationSet']['representation'][index]['qualityType'])
            #print(j2['adaptationSet']['representation'][index]['url'])
            title = '['+j2['adaptationSet']['representation'][index]['qualityType'] + ']' + j['bangumiTitle']
            path = j2['adaptationSet']['representation'][index]['url']
            item = {'label': title,'path':path,'is_playable': True,'info':mp4info,'info_type':'video','thumbnail': img,'icon': img}
        
            items.append(item)
    items.append({
        'label': '[COLOR yellow]评论区[/COLOR]  '+str(pinglunqu),
        'path': plugin.url_for(conn,value=vid,st=st),
    })
    
    
    #dialog = xbmcgui.Dialog()
    #dialog.textviewer('评论区',st)
    return items
     
@plugin.route('/up/<uid>/<page>/')
def up(uid,page):
    videos = get_up(uid,page)
    items = [{
        'label': video['name'],
        'path': plugin.url_for('sources', url=video['href']),
	'thumbnail': video['thumb'],
	'icon': video['thumb'],
    } for video in videos]
    if len(videos) == 20:
        items.append({
            'label': '[COLOR yellow]下一页[/COLOR]  ',
            'path': plugin.url_for(up,uid=uid,page=int(page)+1),
        })
    
    
    return items

@plugin.route('/labels/<label>/')
def show_label(label):
    # 写抓取视频类表的方法
    #
    items = [
        {'label': label},
    ]
    return items

if __name__ == '__main__':
    plugin.run()
