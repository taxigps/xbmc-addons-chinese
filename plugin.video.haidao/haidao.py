# -*- coding:utf-8 -*-
import re
import requests
import xbmcplugin, xbmcgui

# 【一些经常用到的变量】
_handle=int(sys.argv[1]) #当前句柄
_pluginurl = sys.argv[0] #当前地址
_url = sys.argv[2]
_site = 'http://www.okzyw.com'#接口域名
_site_search = 'http://www.okzyw.com/index.php?m=vod-search'
_site_18 = False
close_keyword = '伦理片,好姐姐'
_site_close_keyword = close_keyword.decode('utf-8')
_movieinfo = True #启用视频信息

print('malimaliao：' + str(_handle) + _pluginurl)

UA_head = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
    'referer': 'http://www.okzyw.com',
}

# 【获取频道栏目列表】
def load_typelist(dianying_url):
    #提取 网站域名 + 电影标识id
    GZ_sites = re.compile(r'(http://|https://)(.+?)/.*type-id-(.+?).html')
    sites = GZ_sites.findall(dianying_url)
    if len(sites) > 0:
        for site in sites:
            dy_domain = site[0] + site[1]
            #print('网站域名：' + dy_domain)
            dy_id = site[2]
            ziyuan = requests.get(dianying_url, headers=UA_head)
            htmlcode = ziyuan.text
            id_html = re.search(r'<div.id="m' + dy_id + '".*>\s*.+?\s*</div>', htmlcode)  # 提取局部html(电影分类列表)
            if id_html:
                htmlcode_html = id_html.group()
                GZ_type = re.compile(r'<a.href="(.+?)">(.+?)</a>')  # 栏目规则
                types = GZ_type.findall(htmlcode_html)
                if len(types) > 0:
                    for type in types:
                        type_url = dy_domain + type[0]
                        type_name = type[1]
                        #KODI代码嵌入开始
                        if _site_18 == True:
                            if type_name in _site_close_keyword:
                                continue #跳过
                            else:
                                listitem = xbmcgui.ListItem(type_name)
                                xbmcplugin.addDirectoryItem(_handle, _pluginurl + type[0], listitem, True)
                        else:
                            listitem = xbmcgui.ListItem(type_name)
                            xbmcplugin.addDirectoryItem(_handle, _pluginurl + type[0], listitem, True)
                        #KODI代码嵌入完毕
                else:
                    print('暂无电影分类列表提供')
            else:
                print('无法获取电影分类列表')
    else:
        print('电影URL地址不合法')

# 【获取栏目电影列表】
def load_videolist(dianying_type_url):
    print(dianying_type_url)
    res = requests.get(dianying_type_url, headers=UA_head)
    htmlcode = res.text
    #print(htmlcode)
    GZ_videos = re.compile(r'<li>[\s\S]*?<a.href="(.+?)".*>(.+?)</a>\s*</span>\s*<span.*>(.+?)</span>\s*<span.*>(.+?)</span>')
    videos = GZ_videos.findall(htmlcode)
    if len(videos) > 0:
        for video in videos:
            #print video
            v_url = video[0]
            v_title = video[1]
            #KODI代码嵌入开始
            listitem=xbmcgui.ListItem(v_title)
            xbmcplugin.addDirectoryItem(_handle, _pluginurl + v_url, listitem, True)
            #KODI代码嵌入完毕
    else:
        print('暂时无法获取到本栏目下的电影列表')

# 【获取电影信息】
def load_videoinfo(dianying_detail_url,detail_info=False):
    videoinfo = {}
    res_info = requests.get(dianying_detail_url, headers=UA_head)
    htmlcode_info = res_info.text
    #playimg
    GZ_images = re.compile(r'vodImg">\s*.+lazy..src="(.*?)"')
    images = GZ_images.findall(htmlcode_info)
    if len(images) > 0:
        for img in images:
            videoinfo['image'] = img
    else:
        videoinfo['image'] = ''
    #playlist
    GZ_playlists = re.compile(r'/>(.+?)\$(.+?).m3u8</li>')
    playlists = GZ_playlists.findall(htmlcode_info)
    if len(playlists) > 0:
        playurllist = {}
        for play in playlists:
            # print(play[0] + play[1] + '.m3u8')
            play_title = play[0]
            play_m3u8 = play[1] + '.m3u8'
            playurllist[play_title] = play_m3u8
        #print(playurllist)
        videoinfo['playlist'] = playurllist
    else:
        print('本视频暂无播放地址')
        videoinfo['playlist'] ={}
    #playinfo
    if detail_info == True:
        # vodhs
        GZ_vodhs = re.compile(r'vodh">\s*<h2>(.+?)</h2>\s*<span>(.*?)</span>\s*<label>(.*?)</label>')  # 筛选图片
        vodhs = GZ_vodhs.findall(htmlcode_info)
        if len(vodhs) > 0:
            for vodh in vodhs:
                videoinfo['title'] = vodh[0]
                videoinfo['status'] = vodh[1]
                videoinfo['rating'] = float(vodh[2])
        else:
            videoinfo['title'] = ''
            videoinfo['status'] = ''
            videoinfo['rating'] = 0
        # vodinfobox
        GZ_vodinfobox = re.compile(r'\u522b\u540d\uff1a<span>(.*?)<[\s\S]*?\u5bfc\u6f14\uff1a<span>(.*?)<[\s\S]*?\u4e3b\u6f14\uff1a<span>(.*?)<[\s\S]*?\u7c7b\u578b\uff1a<span>(.*?)<[\s\S]*?\u5730\u533a\uff1a<span>(.*?)<[\s\S]*?\u8bed\u8a00\uff1a<span>(.*?)<[\s\S]*?\u4e0a\u6620\uff1a<span>(.*?)<[\s\S]*?txt="(.+?)</span>')  # 筛选box一堆的信息
        vodinfobox = GZ_vodinfobox.findall(htmlcode_info)
        if len(vodinfobox) > 0:
            for vodinfo in vodinfobox:
                videoinfo['originaltitle'] = vodinfo[0]  # 别名
                videoinfo['director'] = vodinfo[1]  # 导演
                zhuyan = vodinfo[2]  # 主演 list
                videoinfo['cast'] = zhuyan.split(',')  # 将主演成员，以逗号分割变成list，植入cast
                videoinfo['genre'] = vodinfo[3]  # 类型
                # videoinfo['originaltitle'] = vodinfo[4]  # 地区
                # videoinfo['originaltitle'] = vodinfo[5]  # 语言
                videoinfo['year'] = int(vodinfo[6])  # 上映时间
                videoinfo['plot'] = vodinfo[7]  # 描述
        else:
            videoinfo['originaltitle'] = ''
            videoinfo['director'] = ''
            videoinfo['cast'] = []
            videoinfo['genre'] = ''
            # videoinfo['originaltitle'] = ''
            # videoinfo['originaltitle'] = ''
            videoinfo['year'] = 1899
            videoinfo['plot'] = ''  # 描述
    return videoinfo
#搜索视频信息
def load_dy_search(keyword):
    print('搜索词处理：'+keyword)
    postdata = {'wd':keyword,'submit':'search'}
    soziyuan = requests.post(url=_site_search,data=postdata,headers=UA_head)
    sohtmlcode = soziyuan.text
    #print(sohtmlcode)
    GZ_so = re.compile(r'vb4">\s*<a.href="(.+?)".+>(.+?)</a>\s*</span>\s*<span.+vb5.>(.+?)</span>')
    sos = GZ_so.findall(sohtmlcode)
    if len(sos) > 0:
        for so in sos:
            v_url = so[0]
            v_title = so[1]
            v_area = so[2]
            #kodi code
            if _site_18 == True:
                if v_title in _site_close_keyword:
                    continue  #片名过滤
                elif v_area in _site_close_keyword:
                    continue  #分类过滤
                else:
                    listitem = xbmcgui.ListItem(v_title + '(' + v_area + ')')
                    xbmcplugin.addDirectoryItem(_handle, _pluginurl + v_url, listitem, True)
            else:
                listitem = xbmcgui.ListItem(v_title + '(' + v_area + ')')
                xbmcplugin.addDirectoryItem(_handle, _pluginurl + v_url, listitem, True)
    else:
        print('暂时无法搜索到资源')

#kodi search keyboard
try:
    from ChineseKeyboard import Keyboard
except Exception as e:
    from xbmc import Keyboard
#kodi search
def search():
    keyboard = xbmc.Keyboard('','请输入搜索内容')
    xbmc.sleep( 1500 )
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        print('soso:'+keyword)
        #url = p_url + urllib.quote_plus(keyword.decode('utf-8').encode('gb2312'))
        load_dy_search(keyword)#载入搜索处理程序
    else: return
#当前为首页，为用户【建立主栏目菜单】
if _url == '':
    # 先做一个搜索按钮
    listitem=xbmcgui.ListItem('[COLOR yellow]资源搜索[/COLOR]')
    xbmcplugin.addDirectoryItem(_handle, _pluginurl+'/?sousuo', listitem, True)
    # 载入分类列表，并生成分类栏目菜单
    load_typelist(_site+'/?m=vod-type-id-1.html')
#当前为搜索按钮位置
if 'sousuo' in _url:
    print('sou')
    search()#启动搜索
#当前为栏目列表，提取typeid，为用户【建立视频列表】
if 'vod-type-id' in _url:
    print('typeurl：' + _url) #?m=vod-type-id-5.html
    GZ_tid = re.compile(r'type-id-(.+?).html')  # 栏目规则
    tids = GZ_tid.findall(_url)
    if len(tids) > 0:
        for tid in tids:
            print('tid:' + tid)
            #载入指定typeid的视频列表
            load_videolist( _site + _url )
    else:
        print('无法提取type id')

#当前为视频标题URL，提取detail id，为用户【载入视频信息】
if 'vod-detail-id' in _url:
    print('detailurl：' + _url)
    GZ_vid = re.compile(r'detail-id-(.+?).html')  # 栏目规则
    vids = GZ_vid.findall(_url)
    if len(vids) > 0:
        for vid in vids:
            print('tid:' + vid)
            #载入指定vid的视频信息
            videodata = load_videoinfo( _site + _url,_movieinfo)
            movie_image = videodata['image']
            movie_playlist = videodata['playlist']
            for playurl in videodata['playlist'].items():
                #print(playurl[0] + playurl[1])
                if _movieinfo == True:
                    movie_title = videodata['title']
                    movie_status = videodata['status']
                    movie_rating = videodata['rating']
                    movie_year = videodata['year']
                    movie_genre = videodata['genre']
                    movie_director = videodata['director']
                    movie_cast = videodata['cast']
                    movie_plot = videodata['plot']

                    listitem = xbmcgui.ListItem(movie_title + playurl[0], iconImage=movie_image, thumbnailImage=movie_image)
                    # http://mirrors.kodi.tv/docs/python-docs/13.0-gotham/xbmcgui.html#ListItem-setInfo
                    listitem.setInfo(type="video", infoLabels={"title":movie_title})  # setInfo
                    videobox = {
                        'Genre': movie_genre,
                        'year': movie_year,
                        'title':movie_title,
                        'rating':movie_rating,
                        'status':movie_status,
                        'director':movie_director,
                        'cast':movie_cast,
                        'plot':movie_plot,
                        'plotoutline': movie_plot
                    }
                    listitem.setInfo('video',videobox)
                else:
                    listitem = xbmcgui.ListItem(playurl[0],thumbnailImage=movie_image)
                xbmcplugin.addDirectoryItem(_handle, playurl[1], listitem, False)
    else:
        print('无法提取detail id')

# 目录构建完了，显示吧
xbmcplugin.endOfDirectory(_handle) #退出菜单布局
