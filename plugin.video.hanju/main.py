# -*- coding:utf-8 -*-
import re
import requests
from collections import OrderedDict
import xbmcplugin, xbmcgui
# https://kodi.wiki/view/Add-on_development

# 当前句柄
_handle=int(sys.argv[1])
# 当前插件地址
_plugin_address =sys.argv[0]
# 问号以后的内容
_wh_url =sys.argv[2]
# 接口域名
_site ='http://www.hanju.cc'
_site_18 = False
_close_keyword = '伦理片,操'
_encoding = 'gb2312'
print('爬虫调试_cj:' + str(_handle))
print('爬虫调试_cj_address:' + _plugin_address)
print('爬虫调试_cj_wh_url:' + _wh_url)
UA_head = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
    'referer': 'http://www.hanju.cc',
}
# 【获取频道列表】
def load_typelist(url):
    res = requests.get(url, headers=UA_head)
    res.encoding = _encoding
    code = res.text
    re_z = re.compile(r'<li><a.href=./hanju/list_(.*?)_1.html.>(.*?)</a>')  # 正则
    types = re_z.findall(code)
    if len(types) > 0:
        for type in types:
            # 构造带问号的kodi专属插件url地址，便于识别，?kodi_type=2.k
            type_url = '?kodi_type=' + type[0] + '.k'
            type_name = type[1]
            # KODI代码嵌入开始
            if _site_18 == True:
                if type_name in _close_keyword:
                    continue
                else:
                    listitem = xbmcgui.ListItem(type_name)
                    xbmcplugin.addDirectoryItem(_handle, _plugin_address + type_url, listitem, True)
            else:
                listitem = xbmcgui.ListItem(type_name)
                xbmcplugin.addDirectoryItem(_handle, _plugin_address + type_url, listitem, True)
            # KODI代码嵌入完毕
    else:
        print('爬虫调试_index: 暂无电影分类列表提供')

# 【获取栏目列表】
def load_list(type_url):
    print('爬虫调试_type_list:'+type_url)
    res = requests.get(type_url, headers=UA_head)
    res.encoding = _encoding
    html_code = res.text
    gz = re.compile(r'<li.+>\s*.+href="(.+)".class="img.playico"><img.src="(.+)".alt="(.+?)">.+desc">(.+?)</label')
    videos = gz.findall(html_code)
    if len(videos) > 0:
        for video in videos:
            # 构造带问号的插件网址，以便于后面kodi识别：?kodi_video=/hanju/174606.html
            v_url = '?kodi_video=' + video[0]
            v_images = _site + video[1]
            v_title = video[2]
            v_note = video[3]
            v_name = v_title + '(' + v_note + ')'
            #KODI代码嵌入开始
            listitem=xbmcgui.ListItem(v_name, iconImage=v_images, thumbnailImage=v_images)
            xbmcplugin.addDirectoryItem(_handle, _plugin_address + v_url, listitem, True)
            #KODI代码嵌入完毕
    else:
        print('爬虫调试_type_list:暂时无法获取到本栏目下的电影列表')

# 【获取电影播放节目列表】
def load_video_play_list(video_url):
    # python2中遍历字典时键值对返回的顺序与存储顺序不同，而python3.6+则更改了字典算法会自动按照存储顺序排序，因此此处定义字典为OrderedDict对象
    play_list = OrderedDict()
    print('爬虫调试_play_list：' + video_url)
    res1 = requests.get(video_url, headers=UA_head)
    res1.encoding = _encoding
    text = res1.text
    # vcard['playlist']
    gz1 = re.compile(r'<dt><a.href="(.+?)".target="_blank">(.+?)</a></dt>')
    p_lists = gz1.findall(text)
    if len(p_lists) > 0:
        for v_card in p_lists:
            # 提取播放名称，此处为中文，会被系统转换为unicode存储
            v_play_title = v_card[1]
            # 构造kodi视频播放地址 ?kodi_play=/hanju/174362/7.html
            v_play_url = '?kodi_play=' + v_card[0]
            play_list[v_play_title] = v_play_url
    else:
        print('爬虫调试_play_list:本视频暂无播放地址')
        play_list.clear()
    return play_list
#kodi search keyboard
try:
    from ChineseKeyboard import Keyboard
except Exception as e:
    from xbmc import Keyboard
#搜索模块
def start_search():
    keyboard = xbmc.Keyboard('', '请输入影片关键词')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        print('爬虫调试_关键词:' + keyword)
        # url = p_url + urllib.quote_plus(keyword.decode('utf-8').encode('gb2312'))
        load_dy_search(keyword)
    else:
        return
#搜索视频信息
def load_dy_search(keyword):
    print('爬虫调试_处理搜索:' + keyword)
    so_url = _site + '/plus/search.php?kwtype=0&keyword=' + keyword + '&channeltype=4'
    zy = requests.post(url=so_url,headers=UA_head)
    code = zy.text
    gz = re.compile(r'<h3><a.href="(.+?)".target="_blank">(.+?)</a></h3>')
    sos = gz.findall(code)
    if len(sos) > 0:
        for so in sos:
            # 构造带问号的插件网址，以便于后面kodi识别：?kodi_video=/hanju/174606.html
            v_url = '?kodi_video=' + so[0]
            v_title = so[1]#搜索结果的标题
            v_title = v_title.replace("<font color='red'>", '')
            v_title = v_title.replace('</font>', '')
            if _site_18 == True:
                if v_title in _close_keyword:
                    continue
                else:
                    listitem = xbmcgui.ListItem(v_title)
                    xbmcplugin.addDirectoryItem(_handle, _plugin_address + v_url, listitem, True)
            else:
                listitem = xbmcgui.ListItem(v_title)
                xbmcplugin.addDirectoryItem(_handle, _plugin_address + v_url, listitem, True)
    else:
        print('爬虫调试_处理搜索:找不到')
#当前为首页，为用户【建立主栏目菜单】
if _wh_url == '':
    # 先做一个搜索按钮
    listitem=xbmcgui.ListItem('[COLOR yellow]韩剧搜索[/COLOR]')
    xbmcplugin.addDirectoryItem(_handle, _plugin_address+'?so=sogou', listitem, True)
    # 载入分类列表，并生成分类栏目菜单
    load_typelist(_site+'/hanju/')
#当前为搜索按钮位置
if '?so=sogou' in _wh_url:
    print('爬虫调试_start_search：' + _wh_url)
    start_search()

#当前为栏目列表，提取typeid，为用户【建立视频列表】
if '?kodi_type=' in _wh_url:
    # ?kodi_type=3.k，由上层构造的kodi url地址，_通过wh_url来辨认
    print('爬虫调试_type:' + _wh_url)
    GZ_tid = re.compile(r'kodi_type=(.+?).k')
    tids = GZ_tid.findall(_wh_url)
    if len(tids) > 0:
        for tid in tids:
            # 载入指定typeid的视频列表
            load_list(_site + '/hanju/list_' + tid + '_1.html')
    else:
        print('爬虫调试_type:无法提取分类ID')

#当前为视频标题URL，但是插件访问时会做URL编码因此需要解码 %2f 代表/
if '?kodi_video=' in _wh_url:
    print('爬虫调试_video：' + _wh_url)
    # 栏目规则 ?kodi_video=/hanju/174606.html 但kodi访问的实际是?kodi_video=%2fhanju%2f173276.html
    GZ_vid = re.compile(r'kodi_video=%2fhanju%2f(.+?).html')
    vids = GZ_vid.findall(_wh_url)
    if len(vids) > 0:
        for vid in vids:
            print('爬虫调试_load vid:' + vid)
            #载入指定vid的视频信息，重新拼接URL地址
            this_url = _site + '/hanju/' + vid + '.html'
            this_list = load_video_play_list(this_url)
            for t_play, t_url in this_list.items():
                listitem = xbmcgui.ListItem(t_play)
                xbmcplugin.addDirectoryItem(_handle, _plugin_address + t_url, listitem, True)
    else:
        print('爬虫调试_video:无法提取vid')
#当前为播放URL
if '?kodi_play=' in _wh_url:
    print('爬虫调试_play：' + _wh_url)
    # 栏目规则 ?kodi_play=/hanju/174362/4.html 但kodi访问的实际是?kodi_play=%2fhanju%2f173276%2f4.html
    GZ_vid = re.compile(r'kodi_play=%2fhanju%2f(.+?)%2f(.+?).html')
    tt = GZ_vid.findall(_wh_url)
    if len(tt) > 0:
        for t in tt:
            print('爬虫调试_load pid:' + t[1])
            # 载入指定vid的视频信息，重新拼接URL地址
            play_url = _site + '/hanju/' + t[0] + '/' + t[1] + '.html'
            print('爬虫调试_play:' + play_url)
            res = requests.get(play_url, headers=UA_head)
            res.encoding = _encoding
            code = res.text
            # m3u8 var.vid=.(.+?).;
            GZ_videos = re.compile(r'<h1><a.+>(.*?)</a>(.*?)</h1>[\s\S]*?.+vid=.(.+?).;')
            bofang = GZ_videos.findall(code)
            if len(bofang) > 0:
                for b in bofang:
                    # 字符传入kodi需要做unicode转码
                    play_names = b[0] + b[1] + u'【播放】'
                    play_m3u8 = b[2]
                    # KODI代码嵌入开始
                    listitem = xbmcgui.ListItem(play_names)
                    xbmcplugin.addDirectoryItem(_handle, play_m3u8, listitem, False)
                    # KODI代码嵌入完毕
            else:
                print('爬虫调试_play:找不到播放地址')
    else:
        print('爬虫调试_play:无法提取pid')

# 目录构建完了，退出菜单布局
xbmcplugin.endOfDirectory(_handle)