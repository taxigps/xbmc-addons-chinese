#coding=utf-8

import base64
import utils
import json
import hashlib
import urllib, urllib2
import re
import os
import tempfile
import xml.dom.minidom as minidom
from cookielib import LWPCookieJar
import requests

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
API_URL = 'http://api.bilibili.com'
BANGUMI_URL = 'http://space.bilibili.com/ajax/Bangumi/getList?mid={0}&page={1}'
VIEW_URL = API_URL + '/view?{0}'
LIST_URL = API_URL + '/list?{0}'
DYNAMIC_URL = API_URL + '/x/feed/pull?type=0&ps={0}&pn={1}'
LOGIN_URL = 'http://passport.bilibili.com/ajax/miniLogin/login'
LOGIN_CAPTCHA_URL = 'https://passport.bilibili.com/captcha'
LOGIN_HASH_URL = 'http://passport.bilibili.com/login?act=getkey'
HISTORY_URL = 'http://space.bilibili.com/ajax/viewhistory/gethistory'
FAV_BOX_URL = 'http://space.bilibili.com/ajax/fav/getBoxList?mid={0}'
FAV_URL = 'http://space.bilibili.com/ajax/fav/getList?mid={0}&pagesize={1}&fid={2}'
TIMELINE_URL = 'http://bangumi.bilibili.com/jsonp/timeline_v2.ver?callback=timeline'
MY_INFO_URL = 'http://space.bilibili.com/ajax/member/MyInfo'
AV_URL = 'http://www.bilibili.com/widget/getPageList?aid={0}'
INTERFACE_URL = r'http://interface.bilibili.com/playurl?cid={0}&from=miniplay&player=1&sign={1}'
INTERFACE_PARAMS = r'cid={0}&from=miniplay&player=1{1}'
SECRETKEY_MINILOADER = r'1c15888dc316e05a15fdd0a02ed6584f'

class Bilibili():
    def __init__(self, appkey = APPKEY, appsecret = APPSECRET):
        self.appkey = appkey
        self.appsecret = appsecret
        cookie_path = os.path.dirname(os.path.abspath(__file__)) + '/.cookie'
        self.cj = LWPCookieJar(cookie_path)
        if os.path.isfile(cookie_path):
            self.cj.load()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(opener)

    def get_captcha(self):
        result = utils.get_page_content(LOGIN_CAPTCHA_URL, 
                                        headers = {'Referer':'https://passport.bilibili.com/ajax/miniLogin/minilogin'})
        path = tempfile.gettempdir() + '/captcha.jpg'
        with open(path, 'w+') as f:
            f.write(result)
        captcha = raw_input('Captcha: ')
        return captcha

    def get_encryped_pwd(self, pwd):
        import rsa
        result = json.loads(utils.get_page_content(LOGIN_HASH_URL, 
                                                   headers={'Referer':'https://passport.bilibili.com/ajax/miniLogin/minilogin'}))
        pwd = result['hash'] + pwd
        key = result['key']
        pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(key)
        pwd = rsa.encrypt(pwd.encode('utf-8'), pub_key)
        pwd = base64.b64encode(pwd)
        pwd = urllib.quote(pwd)
        return pwd


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

    def get_my_info(self):
        if not requests.utils.dict_from_cookiejar(self.cj).has_key('DedeUserID'):
            return []
        result = json.loads(utils.get_page_content(MY_INFO_URL))
        return result['data']

    def get_dynamic(self, page = 1, pagesize = 30):
        if not requests.utils.dict_from_cookiejar(self.cj).has_key('DedeUserID'):
            return []
        url = DYNAMIC_URL.format(pagesize, page)
        result = json.loads(utils.get_page_content(url))
        return result['data']['feeds']

    def get_fav_box(self):
        cookie_dict = requests.utils.dict_from_cookiejar(self.cj)
        if not cookie_dict.has_key('DedeUserID'):
            return []
        url = FAV_BOX_URL.format(str(cookie_dict['DedeUserID']))
        result = json.loads(utils.get_page_content(url))
        return result['data']['list']

    def get_fav(self, fav_box, pagesize = 30):
        cookie_dict = requests.utils.dict_from_cookiejar(self.cj)
        if not cookie_dict.has_key('DedeUserID'):
            return []
        url = FAV_URL.format(str(cookie_dict['DedeUserID']), pagesize, fav_box)
        result = json.loads(utils.get_page_content(url))
        return result['data']['vlist']

    def login(self, userid, pwd):
        #utils.get_page_content('http://www.bilibili.com')
        if requests.utils.dict_from_cookiejar(self.cj).has_key('DedeUserID'):
            return True
        utils.get_page_content('https://passport.bilibili.com/login')
        captcha = self.get_captcha()
        pwd = self.get_encryped_pwd(pwd)
        data = 'userid={0}&pwd={1}&keep=1&captcha={2}'.format(userid, pwd, captcha)
        result = utils.get_page_content(LOGIN_URL, data, 
                                        {'Origin':'https://passport.bilibili.com', 
                                         'Referer':'https://passport.bilibili.com/ajax/miniLogin/minilogin'})
        if not requests.utils.dict_from_cookiejar(self.cj).has_key('DedeUserID'):
            return False
        self.cj.save()
        return True

    #def get_av_list(self, aid, page = 1, fav = 0):
        #params = {'id': aid, 'page': page}
        #if fav != 0:
        #    params['fav'] = fav
        #url = VIEW_URL.format(self.api_sign(params))
        #result = json.loads(utils.get_page_content(url))
        #results = [result]
        #if (page < result['pages']):
        #    results += self.get_av_list(aid, page + 1, fav)
        #return results

    def get_av_list(self, aid):
        url = AV_URL.format(aid)
        result = json.loads(utils.get_page_content(url))
        return result

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
    b = Bilibili()
    b.login(u'catro@foxmail.com', u'')
    print b.get_my_info()
