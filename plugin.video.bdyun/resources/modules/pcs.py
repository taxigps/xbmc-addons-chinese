#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author is LiuLang <gsushzhsosgsu@gmail.com>
# Use of this source code is governed by GPLv3 license that can be found
# in http://www.gnu.org/licenses/gpl-3.0.html


import json, os, re, time, random
import requests


PAN_URL = 'http://pan.baidu.com/'
PAN_API_URL = PAN_URL + 'api/'
timestamp = str(int(time.time() * 1000))
latency = str(random.random())
CONTENT_FORM = 'application/x-www-form-urlencoded'
CONTENT_FORM_UTF8 = CONTENT_FORM + '; charset=UTF-8'
# 一般的服务器名
PCS_URL = 'http://pcs.baidu.com/rest/2.0/pcs/'
# 下载的服务器名
PCS_URL_D = 'http://d.pcs.baidu.com/rest/2.0/pcs/'
## HTTP 请求时的一些常量
ACCEPT_HTML = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'


RAPIDUPLOAD_THRESHOLD = 256 * 1024  # 256K


default_headers = {
    'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0',
    'Referer': 'http://pan.baidu.com/disk/home',
    'Accept': 'application/json, text/javascript, */*; q=0.8',
    'Accept-language': 'zh-cn, zh;q=0.5',
    'Accept-encoding': 'gzip, deflate',
    'Pragma': 'no-cache',
    'Cache-Control': 'max-age=0',
}


def get_user_uk(cookie, tokens):
    '获取用户的uk'
    url = 'http://yun.baidu.com'
    headers_merged = default_headers.copy()
    req = requests.get(url, cookies=cookie, headers=headers_merged)
    if req:
        content = req.text
        match = re.findall('/share/home\?uk=(\d+)" target=', content)
        if len(match) == 1:
            return match[0]
        else:
            print('pcs.get_user_uk(), failed to parse uk')
    return None



def get_user_info(tokens, uk):
    '''获取用户的部分信息.

    比如头像, 用户名, 自我介绍, 粉丝数等.
    这个接口可用于查询任何用户的信息, 只要知道他/她的uk.
    '''
    url = 'http://yun.baidu.com/pcloud/user/getinfo'
    url_params = {
            'channel': 'chunlei',
            'clienttype': '0',
            'web': '1',
            'bdstoken': tokens['bdstoken'],
            'query_uk': uk,
            't': timestamp,
            }
    headers_merged = default_headers.copy()
    headers_merged['Referer'] = 'http://yun.baidu.com/share/home?uk=' + uk
    headers_merged['Host'] = 'yun.baidu.com'
    req = requests.get(url, headers=headers_merged, params=url_params)
    if req:
        info = json.loads(req.text)
        if info and info['errno'] == 0:
            return info['user_info']
    return None


def get_pcs_info(cookie, tokens):
    uk = get_user_uk(cookie, tokens)
    pcs_info = get_user_info(tokens, uk)
    return pcs_info


def list_dir_all(cookie, tokens, path):
    '''得到一个目录中所有文件的信息, 并返回它的文件列表'''
    pcs_files = []
    page = 1
    while True:
        content = list_dir(cookie, tokens, path, page)
        if not content:
            return None
        if not content['list']:
            return pcs_files
        pcs_files.extend(content['list'])
        page = page + 1


def list_dir(cookie, tokens, path, page=1, num=100):
    '''得到一个目录中的所有文件的信息(最多100条记录).'''
    '''每页100条记录是网页规定'''
    url = PAN_API_URL + 'list'
    url_params = {
            'order': 'time',
            'desc': '1',
            'showempty': '0',
            'web': '1',
            'page': str(page),
            'num': str(num),
            'dir': path,
            't': str(random.random()),
            'bdstoken': tokens['bdstoken'],
            'channel': 'chunlei',
            'app_id': '250528',
            'clienttype': '0',
            }

    headers_merged = default_headers.copy()
    headers_merged.update({'Content-type': CONTENT_FORM_UTF8})

    req = requests.get(url, headers=headers_merged, cookies=cookie, params=url_params)
    if req:
        content = req.text
        return json.loads(content)
    else:
        return None



def get_category(cookie, tokens, category, page=1):
    '''获取一个分类中的所有文件信息, 比如音乐/图片

    目前的有分类有:
      视频 - 1
      音乐 - 2
      图片 - 3
      文档 - 4
      应用 - 5
      其它 - 6
      BT种子 - 7
    '''
    url = ''.join([
        PAN_API_URL,
        'categorylist?channel=chunlei&clienttype=0&web=1',
        '&category=', str(category),
        '&pri=-1&num=100',
        '&t=', timestamp,
        '&page=', str(page),
        '&order=time&desc=1',
        '&_=', timestamp,
        '&bdstoken=', cookie['STOKEN'],
    ])
    headers_merged = default_headers.copy()
    req = requests.get(url, cookies=cookie, headers=headers_merged)
    if req:
        content = req.text
        return json.loads(content)
    else:
        return None


def get_download_link(cookie, tokens, path):
    '''在下载之前, 要先获取最终的下载链接.

    path - 一个文件的绝对路径.

    @return red_url, red_url 是重定向后的URL, 如果获取失败,
            就返回原来的dlink;
    '''
    metas = get_metas(cookie, tokens, path)
    if (not metas or metas.get('errno', -1) != 0 or
            'info' not in metas or len(metas['info']) != 1):
        print('pcs.get_download_link(): %s' % metas)
        return None
    dlink = metas['info'][0]['dlink']
    url = '{0}&cflg={1}'.format(dlink, cookie['cflag'])
    headers_merged = default_headers.copy()
    headers_merged.update({'Accept': ACCEPT_HTML})
    req = requests.get(url, headers=headers_merged, cookies=cookie, allow_redirects=False)
    if not req:
        return url
    else:
        return req.headers['location']


def stream_download(cookie, tokens, path):
    '''下载流媒体文件.

    path - 流文件的绝对路径.
    '''
    url = ''.join([
        PCS_URL_D,
        'file?method=download',
        '&path=', path,
        '&app_id=250528',
    ])
    req = requests.get(url, cookies=cookie, allow_redirects=False)
    if req:
        return req
    else:
        return None


def get_streaming_playlist(cookie, path, video_type='M3U8_AUTO_480'):
    '''获取流媒体(通常是视频)的播放列表.

    默认得到的是m3u8格式的播放列表, 因为它最通用.
    path       - 视频的绝对路径
    video_type - 视频格式, 可以根据网速及片源, 选择不同的格式.
    '''
    url = ''.join([
        PCS_URL,
        'file?method=streaming',
        '&path=', path,
        '&type=', video_type,
        '&app_id=250528',
    ])
    headers_merged = default_headers.copy()
    req = requests.get(url, cookies=cookie, headers=headers_merged)
    if req.status_code == 200:
        return req.text
    else:
        return None


def get_metas(cookie, tokens, filelist, dlink=True):
    '''获取多个文件的metadata.

    filelist - 一个list, 里面是每个文件的绝对路径.
               也可以是一个字符串, 只包含一个文件的绝对路径.
    dlink    - 是否包含下载链接, 默认为True, 包含.

    @return 包含了文件的下载链接dlink, 通过它可以得到最终的下载链接.
    '''
    if isinstance(filelist, str):
        filelist = [filelist, ]
    url = ''.join([
        PAN_API_URL,
        'filemetas?channel=chunlei&clienttype=0&web=1',
        '&bdstoken=', tokens['bdstoken'],
    ])
    if dlink:
        data = {'dlink':'1',
                'target':json.dumps(filelist),
                }
    else:
        data = {'dlink':'0',
                'target':json.dumps(filelist),
                }
    headers_merged = default_headers.copy()
    headers_merged.update({'Content-type': CONTENT_FORM})
    req = requests.post(url, headers=headers_merged, cookies=cookie, data=data)
    if req:
        content = req.text
        return json.loads(content)
    else:
        return None


def search(cookie, tokens, key, path='/'):
    '''搜索全部文件, 根据文件名.

    key - 搜索的关键词
    path - 如果指定目录名的话, 只搜索本目录及其子目录里的文件名.
    '''
    url = ''.join([
        PAN_API_URL,
        'search?channel=chunlei&clienttype=0&web=1',
        '&dir=', path,
        '&key=', key,
        '&recursion',
        '&timeStamp=', latency,
        '&bdstoken=', tokens['bdstoken'],
    ])
    headers_merged = default_headers.copy()
    req = requests.get(url, cookies=cookie, headers=headers_merged)
    if req:
        content = req.text
        return json.loads(content)
    else:
        return None
