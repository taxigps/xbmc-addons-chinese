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
_plugin_player_mimes = ['.m3u8','.mp4','.flv','.ts']
_plugin_handle = int(sys.argv[1])  # 当前插件句柄
_plugin_address = sys.argv[0]  # 当前插件地址
_plugin_parm = sys.argv[2]  # 问号以后的内容
_plugin_dialog = xbmcgui.Dialog()
_plugin_player_style = int(xbmcplugin.getSetting(_plugin_handle, 'Duola_play_style'))
# 系统会追加 ?addons=[_plugin_address]
_plugin_cloud_url = 'https://raw.githubusercontent.com/malimaliao/kodi-addons/matrix/api/plugin.video.duolasousuo/v1.json'

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
    res = requests.get(url=get_url,headers=UA_head)
    #print('duola_debug:'+get_url, res.text)
    #_plugin_dialog.ok(_plugin_name + 'debug', get_url)
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
                    xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address + '?from_engine=' + a_url + '&read_detail='+vod_id, list_item, True)
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
    res = requests.get(url=get_url,headers=UA_head)
    #print('duola_debug:'+get_url, res.text)
    #_plugin_dialog.ok(_plugin_name + 'debug', get_url)
    if check_json(res.text):
        res_json = json.loads(res.text)
        if res_json['code'] == 1:
            if len(res_json['list']) > 0:
                video = res_json['list'][0] # 仅提取一个
                v_id = str(video['vod_id'])
                v_name = '[COLOR yellow]' + video['vod_name'] + '[/COLOR] '
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
                # player_style -------------------------------------------------
                if _plugin_player_style == 0:
                    a = -1
                    for x in V_name_list:
                        a = a + 1
                        list_item = xbmcgui.ListItem(v_name + ' (' + V_name_list[a] +')' )
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
                        list_item = xbmcgui.ListItem(v_name, v_typename, V_m3u8_list[select_i], offscreen=False)
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

# API->engine get new
def API_get_Cloud_Engine_new(Cache_save_path):
    tj_agent = xbmc.getUserAgent()
    tj_agent += ' Kodi-Plugin:' +  _plugin_address
    tj_ua = { 'User-Agent': tj_agent }
    # print('duola_debug: api=>' + _plugin_cloud_url, res.text)
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
                        xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address+'?start_engine='+_api_url, listitem, True)
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

# /
if _plugin_parm == '':
    # print('duola_debug:'+ xbmcplugin.getSetting(_plugin_handle, 'Duola_Cloud_Search_Engine') )
    enable_cloud = xbmcplugin.getSetting(_plugin_handle, 'Duola_Cloud_Search_Engine')
    _b = ""
    # add cloud menu
    if enable_cloud == 'true':
        _b = ' (本地)'
        API_get_Cloud_Engine()
    # add local menu
    _local_api_url = xbmcplugin.getSetting(_plugin_handle, 'Duola_Local_Search_Engine')
    _api_url = urllib.parse.quote(_local_api_url)
    listitem=xbmcgui.ListItem('哆啦搜索' + _b)
    xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address+'?start_engine='+_api_url, listitem, True)
    # 退出kodi菜单布局（如果没有及时退出布局会被Kodi进行布局，而不响应文件夹点击）
    listitem=xbmcgui.ListItem('使用帮助')
    xbmcplugin.addDirectoryItem(_plugin_handle, _plugin_address+'?help', listitem, True)
    xbmcplugin.endOfDirectory(handle=_plugin_handle, succeeded=True, updateListing=False, cacheToDisc=True)

# /?help
if '?help' in _plugin_parm:
    _plugin_dialog.ok(_plugin_name + '使用帮助', '您只要输入您想搜索的资源关键词就可以啦')

# /?start_engine=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F
if '?start_engine=' in _plugin_parm:
    _parm_url =  urllib.parse.unquote(_plugin_parm)
    engine_url = _parm_url.split("start_engine=")[1]
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

# /?from_engine=https%3A%2F%2F123.com%2Fapi%2Fprovide%2Fvod%2F&read_detail=123
if '?from_engine=' in _plugin_parm and '&read_detail' in _plugin_parm:
    _parm_url = urllib.parse.unquote(_plugin_parm)
    engine_url = _parm_url.split("from_engine=")[1]
    detail_id = _parm_url.split("&read_detail=")[1]
    if detail_id != "":
        this_list = Web_load_detail_one(engine_url, detail_id)
    else:
        print('duola_debug:传入的 read_detail 地址为空')
        _plugin_dialog.notification(heading=_plugin_name, message='此视频信息无效', time=3000)
