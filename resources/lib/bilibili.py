#coding=utf-8

import utils
import json
import hashlib
import urllib
import re
import xml.dom.minidom as minidom

CATEGORY = [
    {
        'label': u'全部',
        'name': 'douga',
        'zone': 1,
    },
    {
        'label': u'动画',
        'name': 'douga',
        'zone': 1,
    },
    {
        'label': u'音乐',
        'name': 'music',
        'zone': 3,
    },
    {
        'label': u'番剧',
        'name': 'bangumi',
        'zone': 13,
    },
    {
        'label': u'舞蹈',
        'name': 'dance',
        'zone': 129,
    },
    {
        'label': u'游戏',
        'name': 'game',
        'zone': 4,
    },
    {
        'label': u'科技',
        'name': 'technology',
        'zone': 36,
    },
    {
        'label': u'生活',
        'name': 'life',
        'zone': 160,
    },
    {
        'label': u'鬼畜',
        'name': 'kichiku',
        'zone': 119,
    },
    {
        'label': u'娱乐',
        'name': 'ent',
        'zone': 5,
    },
    {
        'label': u'电影',
        'name': 'movie',
        'zone': 23,
    },
    {
        'label': u'电视剧',
        'name': 'teleplay',
        'zone': 11,
    },
    {
        'label': u'时尚',
        'name': 'fashion',
        'zone': 155,
    },
]

APPKEY = '19bf1f1192873efa'
APPSECRET = '87677fc06b0afc08cb86e008183390e5'
TOP_URL = 'http://www.bilibili.com/index/rank/all-0{0}-{1}.json'
VIEW_URL = 'http://api.bilibili.cn/view?{0}'
INTERFACE_URL = r'http://interface.bilibili.com/playurl?cid={0}&from=miniplay&player=1&sign={1}'
INTERFACE_PARAMS = r'cid={0}&from=miniplay&player=1{1}'
SECRETKEY_MINILOADER = r'1c15888dc316e05a15fdd0a02ed6584f'

def api_sign(params, appkey, appsecret = None):
    """
    获取新版API的签名，不然会返回-3错误
    """
    params['appkey']=appkey
    data = ""
    keys = params.keys()
    keys.sort()
    for key in keys:
        if data != "":
            data += "&"
        value = params[key]
        if type(value) == int:
            value = str(value)
        data += key + "=" + str(urllib.quote(value))
    if appsecret == None:
        return data
    m = hashlib.md5()
    m.update(data + appsecret)
    return data + '&sign=' + m.hexdigest()

def get_category():
    return CATEGORY[1:]

def get_top():
    return CATEGORY

def get_top_list(zone, days = 3):
    url = TOP_URL.format(str(days), str(zone))
    result = json.loads(utils.get_page_content(url))
    return result['rank']['list']

def get_av_list(aid, page = 1, fav = 0, appkey = APPKEY, appsecret = APPSECRET):
    params = {'id': aid, 'page': page}
    if fav != 0:
        params['fav'] = fav
    url = VIEW_URL.format(api_sign(params, appkey, appsecret))
    result = json.loads(utils.get_page_content(url))
    results = [result]
    if (page < result['pages']):
        results += get_av_list(aid, page + 1, fav, appkey, appsecret)
    return results

def get_video_urls(cid):
    m = hashlib.md5()
    m.update(INTERFACE_PARAMS.format(str(cid), SECRETKEY_MINILOADER))
    url = INTERFACE_URL.format(str(cid), m.hexdigest())
    doc = minidom.parseString(utils.get_page_content(url))
    urls = [durl.getElementsByTagName('url')[0].firstChild.nodeValue for durl in doc.getElementsByTagName('durl')]
    urls = [url 
            if not re.match(r'.*\.qqvideo\.tc\.qq\.com', url)
            else re.sub(r'.*\.qqvideo\.tc\.qq\.com', 'http://vsrc.store.qq.com', url)
            for url in urls]
    return urls


if __name__ == '__main__':
    print (get_video_urls(13095037))
