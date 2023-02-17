# -*- coding:utf-8 -*-
import sys, json, base64
import requests
import urllib.parse
from collections import OrderedDict
# https://codedocs.xyz/xbmc/xbmc/
import xbmc, xbmcplugin, xbmcgui
import xbmcvfs , xbmcaddon
import os, datetime

# plugin base config
_plugin_name = '哆啦搜索'
_plugin_player_mimes = ['.m3u8','.mp4','.flv','.ts', '.ogg', '.mp3']
_plugin_handle = int(sys.argv[1])  # 当前插件句柄
_plugin_address = sys.argv[0]  # 当前插件地址
_plugin_parm = sys.argv[2]  # 问号以后的内容
_plugin_dialog = xbmcgui.Dialog()
_plugin_player_style = int(xbmcplugin.getSetting(_plugin_handle, 'Duola_play_style'))
# 系统会追加 ?addons=[_plugin_address]
# 镜像接口：https://raw.githubusercontent.com/malimaliao/kodi/matrix/api/plugin.video.duolasousuo/v1.json
_plugin_cloud_url = 'https://gitee.com/beijifeng/kodi/raw/matrix/api/plugin.video.duolasousuo/v1.json'

# bot config
UA_head = { 
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36',
 }

# global debug
print('duola_debug: [' + str(_plugin_handle)+']'+ _plugin_address+' || '+ _plugin_parm)

# custom function
def check_json(input_str):
    try:
        json.loads(input_str)
        return True
    except:
        return False
def check_url_mime(url):
    hz = '.' + url.split('.')[-1]
    if hz in _plugin_player_mimes:
        return True
    else:
        return False

# request: https://123.com/api/provide/vod/?wd={keyword}
# return: 
def Web_load_search(_api_url, keyword):
    get_url = _api_url + '?wd=' + keyword
    try:
        res = requests.get(url=get_url,headers=UA_head)
        res_text = res.text
        # print('duola_debug:'+get_url, res.text)
        #_plugin_dialog.ok(_plugin_name + 'debug', get_url)
    except requests.exceptions.RequestException as e:
        res_text = ''
        _plugin_dialog.notification(heading=_plugin_name, message='搜索获取失败，暂不可用', time=3000)
        print('duola_debug: Web_load_search => bad', e)
    if check_json(res.text):
        res_json = json.loads(res.text)
        if res_json['code'] == 1:
            if len(res_json['list']) > 0:
                for video in res_json['list']:
                    vod_id = str(video['vod_id'])
                    vod_name = '[COLOR yellow]' + video['vod_name'] + '[/COLOR] '
                    vod_remarks = video['vod_remarks']
                    vod_typename = video['type_name']
                    # 建立kodi菜单
                    list_item = xbmcgui.ListItem(vod_name+' ('+ vod_typename+' / '+vod_remarks+')')
                    # list_item.setArt({'icon': '123.JPG'})
                    # list_item.setInfo('video', {'year': vod['year'], 'title':vod['name'], 'episodeguide': play['name'], 'tracknumber': i})
                    a_url = urllib.parse.quote(_api_url)
                    xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address + '?Bot_search_return=' + a_url + '&read_detail='+vod_id, list_item, True)
                # 退出kodi菜单布局
                xbmcplugin.endOfDirectory(handle=_plugin_handle, succeeded=True, updateListing=False, cacheToDisc=True)
            else:
                print('duola_debug:找不到资源')
                _plugin_dialog.notification(heading=_plugin_name, message='抱歉，找不到相关资源', time=3000)
        else:
            print('duola_debug:无法解析json')
            _plugin_dialog.notification(heading=_plugin_name, message='抱歉，由于无法解析返回的数据，服务暂时不可用，请稍后重试', time=3000)
    else:
        print('duola_debug:目标服务器返回的数据无法解析')
        _plugin_dialog.notification(heading=_plugin_name, message='抱歉，目标服务器返回的数据无法响应，服务暂不可用', time=3000)

# request: https://123.com/api/provide/vod/?ac=detail&ids={detail_id}
# return: play list
def Web_load_detail_one(_api_url, detail_id):
    get_url = _api_url + '?ac=detail&ids=' + detail_id
    try:
        res = requests.get(url=get_url,headers=UA_head)
        res_text = res.text
        # print('duola_debug:'+get_url, res.text)
    except requests.exceptions.RequestException as e:
        res_text = ''
        _plugin_dialog.notification(heading=_plugin_name, message='内容获取失败，暂不可用', time=3000)
        print('duola_debug: Web_load_detail_one => bad', e)
    if check_json(res.text):
        res_json = json.loads(res.text)
        if res_json['code'] == 1:
            if len(res_json['list']) > 0:
                video = res_json['list'][0] # 仅提取一个
                v_id = str(video['vod_id'])
                v_name = video['vod_name']
                v_remarks = video['vod_remarks']
                v_typename = video['type_name']
                v_picture = video['vod_pic']
                v_list_text = video['vod_play_url'] # 多地址合集
                v_infos = {}
                try:
                    v_infos['title'] = video['vod_name']
                    v_infos['originaltitle'] = video['vod_name']
                    v_infos['tag'] = video['vod_remarks']
                    v_infos['status'] = 'n/a'
                    v_infos['country'] = video['vod_area']
                    v_infos['year'] = video['vod_year']
                    v_infos['director'] = video['vod_director']
                    v_infos['cast'] = video['vod_actor'].split(',')
                    v_infos['plot'] = video['vod_content']
                    v_infos['rating'] = float(video['vod_score'])
                except IndexError as e:
                    pass
                # dialog.select
                V_name_list = []
                V_m3u8_list = []
                playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                # 按$$$分隔不同的[播放来源]数据
                # 第01集$http://abc.com/1.mp4#第02集$http://abc.com/2.mp4$$$第01集$http://abc.com/1.flv#第02集$http://abc.com/2.flv
                V_class_data = v_list_text.split('$$$')
                if len(V_class_data) > 0:
                    select_title = v_name + ':请选择播放源开始播放'
                    for V_list in V_class_data:
                        # 按#分隔相同的[播放来源]数据中的不同[播放地址/剧集]
                        # 第01集$http://abc.com/1.flv#第02集$http://abc.com/2.flv
                        V_playlist = V_list.split('#')
                        V_i = 0
                        for V_play in V_playlist:
                            # 按#分隔，将vod_title与vod_url区分
                            # 第01集$http://abc.com/1.flv
                            V = V_play.split('$')
                            if len(V) == 2 and check_url_mime( V[1].strip() ):
                                _v_play_label = V[0].strip() # 去除首尾空格
                                _v_play_url = V[1].strip() # 去除首尾空格
                                V_name_list.append(_v_play_label) # 播放标签
                                V_m3u8_list.append(_v_play_url) # 播放地址
                                # listitem
                                list_item = xbmcgui.ListItem(v_name + ':' + _v_play_label, v_typename)
                                list_item.setArt({'thumb': v_picture, 'poster': v_picture})
                                list_item.setInfo('video', v_infos)
                                playlist.add(url= _v_play_url, listitem=list_item, index=V_i)
                                V_i = V_i + 1
                            else:
                                pass # 不符合条件的播放地址跳过
                else:
                   select_title = '此视频暂时没有播放源'
                # 播放方式
                print('dlxx', v_picture)
                # player_style -------------------------------------------------
                if _plugin_player_style == 0:
                    a = -1
                    for x in V_name_list:
                        a = a + 1
                        list_item = xbmcgui.ListItem('[COLOR yellow]【播放】[/COLOR]' + v_name + ' (' + V_name_list[a] +')' )
                        list_item.setArt({'thumb': v_picture, 'poster': v_picture})
                        list_item.setInfo('video', v_infos)
                        xbmcplugin.addDirectoryItem(_plugin_handle, V_m3u8_list[a] , list_item, False)
                    xbmcplugin.endOfDirectory(handle=_plugin_handle, succeeded=True, updateListing=False, cacheToDisc=True)
                # player_style -------------------------------------------------
                if _plugin_player_style == 1:
                    dialog = xbmcgui.Dialog()
                    select_i = dialog.select(select_title, V_name_list)
                    print('duola_debug: select_i '+str(select_i))
                    if select_i >= 0:
                        list_item = xbmcgui.ListItem('[COLOR yellow]【播放】[/COLOR]' + v_name, v_typename, V_m3u8_list[select_i], offscreen=False)
                        list_item.setArt({'thumb': v_picture, 'poster': v_picture})
                        list_item.setInfo('video', v_infos)
                        #_plugin_dialog.info(list_item) # 显示视频信息，含播放按钮
                        xbmc.Player().play(item=V_m3u8_list[select_i], listitem=list_item) # 立即播放视频
                        _plugin_dialog.notification(heading=_plugin_name,message = '视频即将播放，请稍候', time=6000, sound=False)
                # player_style -------------------------------------------------
                if _plugin_player_style == 2:
                    dialog = xbmcgui.Dialog()
                    select_i = dialog.select(select_title, V_name_list)
                    print('duola_debug: select_i '+str(select_i))
                    if select_i >= 0:
                        xbmc.Player().play(item=playlist, listitem=list_item, windowed=False, startpos=select_i) # 立即播放列表
                        _plugin_dialog.notification(heading = _plugin_name,message = '视频即将播放，请稍候',time=6000,sound=False)
            else:
                print('duola_debug:没有数据')
                _plugin_dialog.notification(heading=_plugin_name, message='抱歉，找不到播放列表', time=3000)
        else:
            print('duola_debug:无法解析json')
            _plugin_dialog.notification(heading=_plugin_name, message='抱歉，由于无法解析返回的数据，服务暂时不可用，请稍后重试', time=3000)
    else:
        print('duola_debug:目标服务器返回的数据无法解析')
        _plugin_dialog.notification(heading=_plugin_name, message='抱歉，目标服务器返回的数据无法响应，服务暂不可用', time=3000)

# request: https://123.com/api/provide/vod/?ac=list
# return: channels list
def Web_load_channels(_api_url):
    get_url = _api_url + '?ac=list'
    try:
        res = requests.get(url=get_url,headers=UA_head)
        res_text = res.text
    except requests.exceptions.RequestException as e:
        res_text = ''
        _plugin_dialog.notification(heading=_plugin_name, message='栏目获取失败，暂不可用', time=3000)
        print('duola_debug: Web_load_channels => bad', e)
    if check_json(res.text):
        res_json = json.loads(res.text)
        if res_json['code'] == 1:
            if len(res_json['class']) > 0:
                for channel in res_json['class']:
                    type_id = str(channel['type_id'])
                    type_name = channel['type_name']
                    '''
                    type_pid = str(channel['type_pid'])
                    if type_pid != '0':
                        list_item = xbmcgui.ListItem(type_name)
                        a_url = urllib.parse.quote(_api_url)
                        xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address + '?Bot_channel=' + a_url + '&channel_id='+type_id, list_item, True)
                    '''
                    list_item = xbmcgui.ListItem(type_name)
                    a_url = urllib.parse.quote(_api_url)
                    xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address + '?Bot_channel=' + a_url + '&channel_id='+type_id, list_item, True)
                xbmcplugin.endOfDirectory(handle=_plugin_handle, succeeded=True, updateListing=False, cacheToDisc=True)
            else:
                print('duola_debug:暂无栏目')
                _plugin_dialog.notification(heading=_plugin_name, message='当前引擎暂无栏目', time=3000)
        else:
            print('duola_debug:栏目暂时无法获取')
            _plugin_dialog.notification(heading=_plugin_name, message='当前引擎栏目暂时无法获取', time=3000)
    else:
        print('duola_debug:无法解析json')
        _plugin_dialog.notification(heading=_plugin_name, message='抱歉，无法解析返回的数据，服务暂时不可用，请稍后重试', time=3000)

# request: https://123.com/api/provide/vod/?ac=list&t={type_id}&pg={page}
# return: list list
def Web_load_list(_api_url, type_id, page):
    get_url = _api_url + '?ac=list&t=' + type_id + '&pg=' + page
    print('dlt', get_url)
    try:
        res = requests.get(url=get_url,headers=UA_head)
        res_text = res.text
    except requests.exceptions.RequestException as e:
        res_text = ''
        _plugin_dialog.notification(heading=_plugin_name, message='列表获取失败，暂不可用', time=3000)
        print('duola_debug: Web_load_list => bad', e)
    if check_json(res.text):
        res_json = json.loads(res.text)
        if res_json['code'] == 1:
            if len(res_json['list']) > 0:
                for video in res_json['list']:
                    vod_id = str(video['vod_id'])
                    vod_name = video['vod_name']
                    vod_remarks = video['vod_remarks']
                    vod_typename = video['type_name']
                    # 建立kodi菜单
                    list_item = xbmcgui.ListItem(vod_name+' ('+ vod_typename+' / '+vod_remarks+')')
                    # list_item.setArt({'icon': '123.JPG'})
                    # list_item.setInfo('video', {'year': vod['year'], 'title':vod['name'], 'episodeguide': play['name'], 'tracknumber': i})
                    a_url = urllib.parse.quote(_api_url)
                    xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address + '?Bot_search_return=' + a_url + '&read_detail=' + vod_id, list_item, True)
                # 退出kodi菜单布局
                page = str(int(page) + 1)
                list_item = xbmcgui.ListItem('[COLOR yellow]下一页[/COLOR][COLOR blue]【当前第：' + str(res_json['page']) + '页，共计：' + str(res_json['pagecount']) + '页】[/COLOR]')
                xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address + '?Bot_page=' + _api_url + '&channel_id=' + type_id + '&page_id='+ page, list_item, True)
                xbmcplugin.endOfDirectory(handle=_plugin_handle, succeeded=True, updateListing=False, cacheToDisc=True)
            else:
                print('duola_debug:暂无列表')
                _plugin_dialog.notification(heading=_plugin_name, message='当前栏目下列表是空的，请稍后重试', time=3000)
        else:
            print('duola_debug:列表暂时无法获取')
            _plugin_dialog.notification(heading=_plugin_name, message='当前栏目下节目列表暂时无法获取', time=3000)
    else:
        print('duola_debug:无法解析json')
        _plugin_dialog.notification(heading=_plugin_name, message='抱歉，无法解析返回的数据，服务暂时不可用，请稍后重试', time=3000)

# API->engine get new
def API_get_Cloud_Engine_new(Cache_save_path):
    tj_agent = xbmc.getUserAgent()
    tj_agent += ' Kodi-Plugin:' +  _plugin_address
    tj_ua = { 'User-Agent': tj_agent }
    # print('duola_debug: api=>' + _plugin_cloud_url, res.text)
    try:
        res = requests.get(url = _plugin_cloud_url + '?addons=', headers = tj_ua)
        cloud_engine_text = res.text
        # 写入缓存，降低服务器请求数
        expires_in = 3600 # 初始有效时间为1小时
        if check_json(cloud_engine_text):
            api_json = json.loads(cloud_engine_text)
            if 'expires_in' in api_json:
                expires_in = float(api_json['expires_in']) # 使用服务器限定的有效期
            next_time = datetime.datetime.now() + datetime.timedelta(seconds=expires_in) # 设定时间有效期在n秒后失效
            next_timestamp = str(int(next_time.timestamp()))
            with xbmcvfs.File(Cache_save_path, 'w') as f:
                time_value = 'next_timestamp=' + next_timestamp # 有效时间
                f.write(time_value) # time
                f.write('\n--------\n') # 此处分隔符
                f.write(cloud_engine_text) # json
    except requests.exceptions.RequestException as e:
        cloud_engine_text = ''
        print('duola_debug: API_get_Cloud_Engine_new => BAD', e)
    return cloud_engine_text

# API->engine get
def API_get_Cloud_Engine():
    temp_path= xbmcvfs.translatePath('special://home/temp')
    my_addon = xbmcaddon.Addon()
    my_addon_id = my_addon.getAddonInfo('id')
    my_cache_path = os.path.join(temp_path, my_addon_id, '')
    xbmcvfs.mkdirs(my_cache_path)
    if xbmcvfs.exists(my_cache_path):
        print('duola_debug: 缓存目录读取成功->' + my_cache_path )
        my_cloud_engine_cache = os.path.join(my_cache_path, 'Duola_Local_Search_Engine.txt')
        if xbmcvfs.exists(my_cloud_engine_cache):
            cloud_engine_text = ""
            with xbmcvfs.File(my_cloud_engine_cache) as f:
                cache = f.read()
                a = cache.split('--------')
                a101 = a[1] # json text
                b = a[0].split('timestamp=')
                cc = b[1].replace('\n', '') # next_timestamp=1640507115
                print(b, cc)
                next_timestamp = int(cc)
                this_timestamp = int(datetime.datetime.now().timestamp())
                print('this_timestamp:'+str(this_timestamp)+',next_timestamp:' + str(next_timestamp), cloud_engine_text)
                if this_timestamp < next_timestamp:
                    print('duola_debug: 从本地读取引擎数据->' + my_cloud_engine_cache)
                    cloud_engine_text = a101 # 使用缓存
                else:
                    print('duola_debug: 从云端刷新引擎数据->' + _plugin_cloud_url)
                    cloud_engine_text = API_get_Cloud_Engine_new(my_cloud_engine_cache) # 重新获取
        else:
            print('duola_debug: 从云端拉取引擎数据->' + _plugin_cloud_url)
            cloud_engine_text = API_get_Cloud_Engine_new(my_cloud_engine_cache)
        # ----- 解析json ------
        if check_json(cloud_engine_text):
            api = json.loads(cloud_engine_text)
            #print('duola_debug:zy code' + str(api['code'] ))
            #print('duola_debug:zy data_list' + str(len(api['data']['list'])) )
            if api['code'] == 1 and len(api['data']['list']) > 0:
                print('duola_debug:zy YES')
                for zy in api['data']['list']:
                    # print('duola_debug:zy' + zy['name'] + '@' + zy['api_url'])
                    if zy['status'] == 1:
                        _api_url = urllib.parse.quote(base64.b64decode(zy['api_url'])) # base64 解码后，再URL编码
                        _api_title = ' [COLOR yellow] (' + zy['name'] + ') [/COLOR]'
                        listitem=xbmcgui.ListItem('哆啦搜索' + _api_title)
                        xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address+'?Bot_engine='+_api_url, listitem, True)
                    else:
                        _api_title = ' [COLOR blue] (' + zy['name'] + ') ' + ' 暂不可用[/COLOR]'
                        listitem=xbmcgui.ListItem('哆啦搜索' + _api_title)
                        xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address, listitem, True)
            else:
                _plugin_dialog.notification(heading=_plugin_name, message='云端搜索引擎暂时出现故障，请稍后重试' + api['message'], time=3000)
        else:
            _plugin_dialog.notification(heading=_plugin_name, message='暂时无法连接云端搜索引擎服务器，请稍后重试', time=3000)
        # ----- 解析json ------
    else:
        print('duola_debug: 缓存目录读取失败->' + my_cache_path )
        _plugin_dialog.ok(_plugin_name, '抱歉，由于缓存无法读写，因此云端引擎不可用。文件地址：' + my_cache_path)

# API->readme
def API_get_Cloud_Readme():
    tj_agent = xbmc.getUserAgent()
    tj_agent += ' Kodi-Plugin:' +  _plugin_address
    tj_ua = { 'User-Agent': tj_agent }
    # print('duola_debug: api=>' + _plugin_cloud_url, res.text)
    try:
        res = requests.get(url = _plugin_cloud_url + '?addons=', headers = tj_ua)
        cloud_engine_text = res.text
        if check_json(cloud_engine_text):
            api_json = json.loads(cloud_engine_text)
            readme = api_json['readme']
            _plugin_dialog.notification(heading=_plugin_name, message=readme, time=4000)
    except requests.exceptions.RequestException as e:
        print('duola_debug: readme => bad', e)

# /
if _plugin_parm == '':
    # print('duola_debug:'+ xbmcplugin.getSetting(_plugin_handle, 'Duola_Cloud_Search_Engine') )
    enable_cloud = xbmcplugin.getSetting(_plugin_handle, 'Duola_Cloud_Search_Engine')
    _b = ""
    # add cloud menu
    if enable_cloud == 'true':
        _b = ' (本机内置接口)'
        API_get_Cloud_Readme()
        API_get_Cloud_Engine()
    # add local menu
    _local_api_url = xbmcplugin.getSetting(_plugin_handle, 'Duola_Local_Search_Engine')
    _api_url = urllib.parse.quote(_local_api_url)
    listitem=xbmcgui.ListItem('哆啦搜索' + _b)
    xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address+'?Bot_engine='+_api_url, listitem, True)
    # add readme menu
    listitem=xbmcgui.ListItem('[COLOR=blue]使用帮助[/COLOR]')
    xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address+'?Bot_help', listitem, True)
    # exit menu build
    xbmcplugin.endOfDirectory(handle=_plugin_handle, succeeded=True, updateListing=False, cacheToDisc=True)

# /?Bot_help
if '?Bot_help' in _plugin_parm:
    help_text = '1, 选择在线搜索搜索中文时, 请确保已安装kodi中文输入法\n'
    help_text += '2, 本机内置接口允许您自由修改，可通过插件设置修改内置接口\n'
    help_text += '3, 通过插件设置开启云端搜索引擎接口可连接更多通道\n'
    help_text += '4, 首次播放缓冲较慢，耐心等待后播放就会流畅。\n'
    help_text += '更多内容请参照本插件介绍页'
    _plugin_dialog.ok(_plugin_name + '使用帮助', help_text)

# /?Bot_engine=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F :: 云引擎
if '?Bot_engine=' in _plugin_parm:
    _parm_url =  urllib.parse.unquote(_plugin_parm)
    engine_url = _parm_url.split("Bot_engine=")[1]
    listitem=xbmcgui.ListItem('[COLOR yellow]在线搜索[/COLOR]')
    xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address+'?Bot_search='+engine_url, listitem, True)
    Web_load_channels(engine_url)
    xbmcplugin.endOfDirectory(handle=_plugin_handle, succeeded=True, updateListing=False, cacheToDisc=True)

# /?Bot_search=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F
if '?Bot_search=' in _plugin_parm:
    _parm_url =  urllib.parse.unquote(_plugin_parm)
    engine_url = _parm_url.split("Bot_search=")[1]
    keyboard = xbmc.Keyboard()
    keyboard.setHeading('请输入关键词')
    keyboard.doModal()
    # xbmc.sleep(1500)
    if keyboard.isConfirmed():
        keyword = keyboard.getText()
        if len(keyword) < 1:
            msgbox = _plugin_dialog.ok(_plugin_name, '您必须输入关键词才可以搜索相关内容')
    else:
        keyword = ''
    print('duola_debug:' + keyword)
    if len(keyword) > 0:
        Web_load_search(engine_url, keyword)

# /?Bot_channel=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F&channel_id=123
if '?Bot_channel=' in _plugin_parm and '&channel_id=' in _plugin_parm:
    _parm_url = urllib.parse.unquote(_plugin_parm)
    channel_id = _parm_url.split("&channel_id=")[1]
    engine_url = _parm_url.replace('&channel_id=' + channel_id, '').split("Bot_channel=")[1]
    print('dlca', engine_url, channel_id)
    if channel_id != "":
        Web_load_list(engine_url, channel_id, '1')
    else:
        print('duola_debug:传入的 channel_id 地址为空')
        _plugin_dialog.notification(heading=_plugin_name, message='此栏目无效', time=3000)


# /?Bot_page=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F&channel_id=123&page_id=2
if '?Bot_page=' in _plugin_parm and '&channel_id=' in _plugin_parm and '&page_id=' in _plugin_parm:
    _parm_url = urllib.parse.unquote(_plugin_parm)
    page = _parm_url.split("&page_id=")[1]
    channel_id = _parm_url.replace('&page_id=' + page, '').split("&channel_id=")[1]
    engine_url = _parm_url.replace('&channel_id=' + channel_id + '&page_id=' + page, '').split("Bot_page=")[1]
    print('dlcb', engine_url, channel_id, page)
    if channel_id != "":
        Web_load_list(engine_url, channel_id, page)
    else:
        print('duola_debug:传入的 channel_id 地址为空')
        _plugin_dialog.notification(heading=_plugin_name, message='此栏目无效', time=3000)


# /?Bot_search_return=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F&read_detail=123
if '?Bot_search_return=' in _plugin_parm and '&read_detail' in _plugin_parm:
    _parm_url = urllib.parse.unquote(_plugin_parm)
    detail_id = _parm_url.split("&read_detail=")[1]
    engine_url = _parm_url.replace('&read_detail='+detail_id, '').split("Bot_search_return=")[1]
    print('dlc', engine_url, detail_id)
    if detail_id != "":
        this_list = Web_load_detail_one(engine_url, detail_id)
    else:
        print('duola_debug:传入的 read_detail 地址为空')
        _plugin_dialog.notification(heading=_plugin_name, message='此视频信息无效', time=3000)
