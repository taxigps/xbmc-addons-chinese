#!/usr/bin/python
# -*- coding: utf-8 -*-
'''Author is caasiu <caasiu@outlook.com> && source code is under GPLv3'''

import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os, sys, re, json

__addon_id__= 'plugin.video.bdyun'
plugin_path = xbmcaddon.Addon(__addon_id__).getAddonInfo('path')
lib_path = os.path.join(plugin_path, 'resources', 'modules')
sys.path.append(lib_path)

from resources.modules import get_auth, pcs, utils, myplayer
from xbmcswift2 import Plugin, actions

plugin = Plugin()
dialog = xbmcgui.Dialog()


@plugin.route('/')
def main_menu():
    user_info = get_user_info()
    if user_info is None:
        items = [{
        'label': u'登入',
        'path': plugin.url_for('login_dialog'),
        'is_playable': False
        }]
    else:
        items = [{
            'label': u'## 管理当前帐号: %s' %user_info['username'],
            'path': plugin.url_for('accout_setting'),
            'is_playable': False,
        },{
            'label': u'## 搜索文件(文件夹/视频/音乐)',
            'path': plugin.url_for('search'),
            'is_playable': False
        },{
            'label': u'## 刷新',
            'path': plugin.url_for('refresh'),
            'is_playable': False
        }]

        for loopTime in range(0, 5):
            validation = pcs.token_validation(user_info['cookie'], user_info['tokens'])
            if validation:
                try:
                    homemenu = plugin.get_storage('homemenu')
                    if homemenu.get('item_list'):
                        item_list = homemenu.get('item_list')
                    else:
                        item_list = menu_cache(user_info['cookie'], user_info['tokens'])
                    items.extend(item_list)
                    break
                except (KeyError, TypeError, UnicodeError):
                    dialog.ok('Error', u'请求参数错误', u'请点击登出再重新登录')
                    items.extend([{'label': u'登出 && 重新登录', 'path': plugin.url_for('clear_cache')}])
                    break
            else:
                cookie,tokens = get_auth.run(user_info['username'], user_info['password'])
                if tokens['bdstoken']:
                    save_user_info(user_info['username'], user_info['password'], cookie, tokens)
                else:
                    items.extend([{'label': u'重新登录', 'path': plugin.url_for('relogin')}])
                    break

            if loopTime == 4:
                dialog.ok('Error', u'未知错误', u'请重新登录')
                items.extend([{'label': u'重新登录', 'path': plugin.url_for('relogin')}])

    return plugin.finish(items, update_listing=True)


@plugin.route('/login_dialog/')
@plugin.route('/login_dialog/', name='relogin')
def login_dialog():
    username = dialog.input(u'用户名:', type=xbmcgui.INPUT_ALPHANUM)
    password = dialog.input(u'密码:', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
    if username and password:
        cookie,tokens = get_auth.run(username,password)
        if tokens:
            save_user_info(username,password,cookie,tokens)
            homemenu = plugin.get_storage('homemenu')
            homemenu.clear()
            dialog.ok('',u'登录成功', u'点击返回首页并耐心等待')
            items = [{'label': u'<< 返回首页', 'path': plugin.url_for('main_menu')}]
            return plugin.finish(items, update_listing=True)
    else:
        dialog.ok('Error',u'用户名或密码不能为空')
    return None


@plugin.route('/accout_setting/')
def accout_setting():
    user_info = get_user_info()
    items = [{
    'label': u'<< 返回首页',
    'path': plugin.url_for('main_menu')
    },{
    'label': u'登出和清除缓存',
    'path': plugin.url_for('clear_cache'),
    'is_playable': False
    },{
    'label': u'重新登录/切换帐号',
    'path': plugin.url_for('relogin'),
    'is_playable': False
    },{
    'label': u'插件设置',
    'path': plugin.url_for('setting'),
    'is_playable': False
    }]
    if user_info:
        return plugin.finish(items, update_listing=True)
    else:
        return


@plugin.route('/setting/')
def setting():
    plugin.open_settings()


@plugin.route('/accout_setting/clear_cache/')
def clear_cache():
    info = plugin.get_storage('info')
    homemenu = plugin.get_storage('homemenu')
    pcs_info = plugin.get_storage('pcs_info')
    info.clear()
    homemenu.clear()
    pcs_info.clear()
    dialog.notification('', u'清除完毕', xbmcgui.NOTIFICATION_INFO, 3000)
    xbmc.executebuiltin('Container.Refresh')
    return


@plugin.route('/search/')
def search():
    user_info = get_user_info()
    user_cookie = user_info['cookie']
    user_tokens = user_info['tokens']
    key = dialog.input(heading=u'输入文件名/关键词')
    if key:
        s = pcs.search(user_cookie, user_tokens, key)
        items = []
        if len(s['list']) == 1:
            for result in s['list']:
                if result['isdir'] == 1:
                    item = {
                            'label': result['server_filename'],
                            'path': plugin.url_for('directory', path=result['path'].encode('utf-8')),
                            'is_playable': False
                            }
                    items.append(item)
                elif result['category'] == 1:
                    if 'thumbs' in result and 'url2' in result['thumbs']:
                        ThumbPath = result['thumbs']['url2']
                        item = {
                                'label': result['server_filename'],
                                'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                                'is_playable': False,
                                'icon': ThumbPath,
                                }
                    else:
                        item = {
                                'label': result['server_filename'],
                                'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                                'is_playable': False,
                                }
                    items.append(item)
                elif result['category'] == 2:
                    item = {
                             'label': result['server_filename'],
                             'path': plugin.url_for('play_music', filepath=result['path'].encode('utf-8')),
                             'is_playable': False,
                            }
                    items.append(item)
            if items:
                return plugin.finish(items)
            else:
                dialog.ok('',u'搜素的文件不属于文件夹、视频或音频')

        elif s['list']:
            for result in s['list']:
                if result['isdir'] == 1:
                    item = {
                            'label': result['path'],
                            'path': plugin.url_for('directory', path=result['path'].encode('utf-8')),
                            'is_playable': False
                            }
                    items.insert(0, item)
                elif result['category'] == 1:
                    if 'thumbs' in result and 'url2' in result['thumbs']:
                        ThumbPath = result['thumbs']['url2']
                        item = {
                                'label': result['path'],
                                'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                                'is_playable': False,
                                'icon': ThumbPath,
                                }
                    else:
                        item = {
                                'label': result['path'],
                                'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                                'is_playable': False,
                                }
                    items.append(item)
                elif result['category'] == 2:
                    item = {
                             'label': result['path'],
                             'path': plugin.url_for('play_music', filepath=result['path'].encode('utf-8')),
                             'is_playable': False,
                            }
                    items.append(item)
            if items:
                return plugin.finish(items)
            else:
                dialog.ok('',u'搜素的文件不属于文件夹、视频或音频')

        else:
            dialog.ok('',u'没有找到文件')
            return None

    return


@plugin.route('/directory/<path>')
def directory(path):
    if isinstance(path, str):
        path = path.decode('utf-8')
    user_info = get_user_info()
    user_cookie = user_info['cookie']
    user_tokens = user_info['tokens']
    dir_files = pcs.list_dir_all(user_info['cookie'], user_info['tokens'], path)
    item_list = MakeList(dir_files)

    previous_path = os.path.dirname(path).encode('utf-8')
    if previous_path == '/':
        item_list.insert(0,{
                'label': u'<< 返回首页',
                'path': plugin.url_for('main_menu')
            })
    else:
        item_list.insert(0,{
                'label': u'<< 返回上一目录',
                'path': plugin.url_for('directory', path=previous_path),
            })

    item_list.insert(0,{
                'label': u'## 当前目录: %s' % path,
                'path': plugin.url_for('refresh')
            })
    return plugin.finish(item_list, update_listing=True)


@plugin.route('/refresh/')
def refresh():
    homemenu = plugin.get_storage('homemenu')
    homemenu.clear()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/quality/<filepath>')
def quality(filepath):
    if plugin.get_setting('show_stream_type', bool):
        stream_type = ['M3U8_AUTO_720', 'NONE']
        choice = dialog.select(u'请选择画质', [u'流畅',u'原画'])
        if choice < 0:
            return
        elif choice == 0:
            stream = stream_type[choice]
        elif choice == 1:
            stream = False
    elif plugin.get_setting('stream_type', str) == 'NONE':
        stream = False
    else:
        stream = plugin.get_setting('stream_type', str)

    if isinstance(filepath, str):
        filepath = filepath.decode('utf-8')

    video_path = playlist_path(filepath, stream)

    name = os.path.basename(filepath)
    listitem = xbmcgui.ListItem(name)
    listitem.setInfo(type='Video', infoLabels={'Title': name})

    if video_path:
        xbmc.Player().play(video_path, listitem, windowed=False)


@plugin.route('/play_music/<filepath>')
def play_music(filepath):
    if isinstance(filepath, str):
        filepath = filepath.decode('utf-8')
    url = playlist_path(filepath, stream=False)
    name = os.path.basename(filepath)
    listitem = xbmcgui.ListItem(name)
    listitem.setInfo(type='Music', infoLabels={'Title': name})

    if url:
        xbmc.Player().play(url, listitem, windowed=False)


# cache the output of content menu
def menu_cache(cookie, tokens):
    pcs_files = pcs.list_dir_all(cookie, tokens, path='/')
    if pcs_files:
        item_list = MakeList(pcs_files)
    else:
        return [{'label': u'请点击一下「刷新」', 'path': plugin.url_for('refresh')}]
    homemenu = plugin.get_storage('homemenu', TTL=60)
    homemenu['item_list'] = item_list
    return item_list


def get_user_info():
    info = plugin.get_storage('info')
    user_info = info.get('user_info')
    return user_info


def save_user_info(username, password, cookie, tokens):
    info = plugin.get_storage('info')
    user_info = info.setdefault('user_info',{})
    user_info['username'] = username
    user_info['password'] = password
    user_info['cookie'] = cookie
    user_info['tokens'] = tokens
    info.sync()


def MakeList(pcs_files):
    item_list = []
    ContextMenu = [
        ('搜索', actions.background(plugin.url_for('search'))),
        ('刷新', actions.background(plugin.url_for('refresh'))),
        ('登出', actions.background(plugin.url_for('clear_cache'))),
    ]
    for result in pcs_files:
        if result['isdir'] == 1:
            item = {
                    'label': result['server_filename'],
                    'path': plugin.url_for('directory', path=result['path'].encode('utf-8')),
                    'is_playable': False,
                    'context_menu': ContextMenu,
                    }
            item_list.append(item)
        elif result['category'] == 1:
            if 'thumbs' in result and 'url2' in result['thumbs']:
                ThumbPath = result['thumbs']['url2']
                item = {
                        'label': result['server_filename'],
                        'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                        'is_playable': False,
                        'icon': ThumbPath,
                        'context_menu': ContextMenu,
                        }
            else:
                item = {
                        'label': result['server_filename'],
                        'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                        'is_playable': False,
                        'context_menu': ContextMenu,
                        }
            item_list.append(item)
        elif result['category'] == 2:
            item = {
                    'label': result['server_filename'],
                    'path': plugin.url_for('play_music', filepath=result['path'].encode('utf-8')),
                    'is_playable': False,
                    'context_menu': ContextMenu,
                    }
            item_list.append(item)
    return item_list


def playlist_path(pcs_file_path, stream):
    user_info = get_user_info()
    user_name = user_info['username']
    user_cookie = user_info['cookie']
    user_tokens = user_info['tokens']

    if stream:
        playlist_data = pcs.get_streaming_playlist(user_cookie, pcs_file_path, stream)
        if playlist_data:
            raw_dir = os.path.dirname(pcs_file_path)
            m = re.search('\/(.*)', raw_dir)
            dirname = m.group(1)
            basename = os.path.basename(pcs_file_path)
            r = re.search('(.*)\.(.*)$', basename)
            filename = ''.join([r.group(1), stream, '.m3u8'])
            dirpath = os.path.join(utils.data_dir(), user_name, dirname)
            if not xbmcvfs.exists(dirpath):
                xbmcvfs.mkdirs(dirpath)
            filepath = os.path.join(dirpath, filename)
            tmpFile = xbmcvfs.File(filepath, 'w')
            tmpFile.write(bytearray(playlist_data, 'utf-8'))
            return filepath
        else:
            dialog.notification('', u'无法打开视频', xbmcgui.NOTIFICATION_INFO, 4000)
            return None
    else:
        url = pcs.stream_download(user_cookie, user_tokens, pcs_file_path)
        if url:
            return url
        else:
            dialog.notification('', u'无法打开原画，请尝试流畅模式', xbmcgui.NOTIFICATION_INFO, 4000)
            return None


if __name__ == '__main__':
    plugin.run()
