#coding=utf-8

import utils
import json
import hashlib
import urllib
import re
import xml.dom.minidom as minidom

CATEGORY = [
    {
        'title': u'全部',
        'name': 'douga',
        'tid': 0,
    },
    {
        'title': u'动画',
        'name': 'douga',
        'tid': 1,
    },
    {
        'title': u'音乐',
        'name': 'music',
        'tid': 3,
    },
    {
        'title': u'番剧',
        'name': 'bangumi',
        'tid': 13,
    },
    {
        'title': u'舞蹈',
        'name': 'dance',
        'tid': 129,
    },
    {
        'title': u'游戏',
        'name': 'game',
        'tid': 4,
    },
    {
        'title': u'科技',
        'name': 'technology',
        'tid': 36,
    },
    {
        'title': u'生活',
        'name': 'life',
        'tid': 160,
    },
    {
        'title': u'鬼畜',
        'name': 'kichiku',
        'tid': 119,
    },
    {
        'title': u'娱乐',
        'name': 'ent',
        'tid': 5,
    },
    {
        'title': u'电影',
        'name': 'movie',
        'tid': 23,
    },
    {
        'title': u'电视剧',
        'name': 'teleplay',
        'tid': 11,
    },
    {
        'title': u'时尚',
        'name': 'fashion',
        'tid': 155,
    },
]

ORDER = [
    {
        'title': u'日排行榜',
        'value': 'hot',
        'days': 1,
    },
    {
        'title': u'周排行榜',
        'value': 'hot',
        'days': 7,
    },
    {
        'title': u'月排行榜',
        'value': 'hot',
        'days': 30,
    },
    {
        'title': u'最新',
        'value': 'default',
        'days': 30,
    },
#    {
#        'title': u'按新评论排序',
#        'value': 'new'
#    },
#    {
#        'title': u'按评论数从高至低排序',
#        'value': 'review'
#    },
#    {
#        'title': u'按弹幕数从高至低排序',
#        'value': 'damku'
#    },
#    {
#        'title': u'按推荐数从高至低排序',
#        'value': 'comment'
#    },
#    {
#        'title': u'按宣传数排序（硬币）',
#        'value': 'default'
#    },
]

APPKEY = '19bf1f1192873efa'
APPSECRET = '87677fc06b0afc08cb86e008183390e5'
VIEW_URL = 'http://api.bilibili.cn/view?{0}'
LIST_URL = 'http://api.bilibili.cn/list?{0}'
INTERFACE_URL = r'http://interface.bilibili.com/playurl?cid={0}&from=miniplay&player=1&sign={1}'
INTERFACE_PARAMS = r'cid={0}&from=miniplay&player=1{1}'
SECRETKEY_MINILOADER = r'1c15888dc316e05a15fdd0a02ed6584f'

class Bilibili():
    def __init__(self, appkey = APPKEY, appsecret = APPSECRET):
        self.appkey = appkey
        self.appsecret = appsecret

    def api_sign(self, params):
        """
        获取新版API的签名，不然会返回-3错误
        """
        params['appkey']=self.appkey
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
        if self.appsecret == None:
            return data
        m = hashlib.md5()
        m.update(data + self.appsecret)
        return data + '&sign=' + m.hexdigest()

    def get_category(self):
        return CATEGORY

    def get_order(self):
        return ORDER

    def get_category_list(self, tid = 0, order = 'default', days = 30, page = 1, pagesize = 30):
        params = {'tid': tid, 'order': order, 'days': days, 'page': page, 'pagesize': pagesize}
        url = LIST_URL.format(self.api_sign(params))
        result = json.loads(utils.get_page_content(url))
        results = []
        for i in range(pagesize):
            if result['list'].has_key(str(i)):
                results.append(result['list'][str(i)])
            else:
                break

        return results

    def get_av_list(self, aid, page = 1, fav = 0):
        params = {'id': aid, 'page': page}
        if fav != 0:
            params['fav'] = fav
        url = VIEW_URL.format(self.api_sign(params))
        result = json.loads(utils.get_page_content(url))
        results = [result]
        if (page < result['pages']):
            results += self.get_av_list(aid, page + 1, fav)
        return results

    def get_video_urls(self, cid):
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
    print (Bilibili().get_category_list(order='hot'))
