#!/usr/bin/python
# -*- coding: utf-8 -*-
# Authors are caasiu and LiuLang <gsushzhsosgsu@gmail.com>
# Use of this source code is governed by GPLv3 license that can be found
# in http://www.gnu.org/licenses/gpl-3.0.html


import time, json, base64, re, random, urlparse, os
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from resources.modules import utils


#some base url and information needed by service
timestamp = str(int(time.time()*1000))
ppui_logintime = str(random.randint(52000, 58535))
PASSPORT_BASE = 'https://passport.baidu.com/'
PASSPORT_URL = PASSPORT_BASE + 'v2/api/'
ACCEPT_HTML = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
REFERER = PASSPORT_BASE + 'v2/?login'
PASSPORT_LOGIN = PASSPORT_BASE + 'v2/api/?login'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0'
PAN_REFERER = 'http://pan.baidu.com/disk/home'
ACCEPT_JSON = 'application/json, text/javascript, */*; q=0.8'


default_headers = {
    'User-agent': USER_AGENT,
    'Referer': PAN_REFERER,
    'Accept': ACCEPT_JSON,
    'Accept-language': 'zh-cn, zh;q=0.5',
    'Accept-encoding': 'gzip, deflate',
    'Pragma': 'no-cache',
    'Cache-control': 'no-cache',
}


def json_loads_single(s):
    return json.loads(s.replace("'",'"').replace('\t',''))


def RSA_encrypt(public_key, message):
    rsakey = RSA.importKey(public_key)
    rsakey = PKCS1_v1_5.new(rsakey)
    encrypted = rsakey.encrypt(message.encode('utf-8'))
    return base64.encodestring(encrypted).decode('utf-8').replace('\n', '')


def add_cookie(cookie,string,keys):
    str_list = re.split('[,;]\s*', string)
    for key in keys:
        for item in str_list:
            if re.match(key,item):
                s = re.search('=(.+)', item)
                cookie[key] = s.group(1)
    return cookie


def get_BAIDUID():
    url = ''.join([
                    PASSPORT_URL,
                    '?getapi&tpl=mn&apiver=v3',
                    '&tt=', timestamp,
                    '&class=login&logintype=basicLogin',
                    ])
    req = requests.get(url, headers={'Referer': ''}, timeout=50)
    if req:
        cookie = req.cookies.get_dict()
        cookie['cflag'] = '65535%3A1'
        cookie['PANWEB'] = '1'
        return cookie
    else:
        return None


def get_token(cookie):
    url = ''.join([
                    PASSPORT_URL,
                    '?getapi&tpl=mn&apiver=v3',
                    '&tt=', timestamp,
                    '&class=login&logintype=basicLogin',
                    ])

    headers={
            'Accept': ACCEPT_HTML,
            'Cache-control': 'max-age=0',
            }

    headers_merged = default_headers.copy()
    #merge the headers
    for key in headers.keys():
        headers_merged[key] = headers[key]

    req = requests.get(url, headers=headers_merged, cookies=cookie, timeout=50)
    if req:
        hosupport = req.headers['Set-Cookie']
        content_obj = json_loads_single(req.text)
        if content_obj:
            token = content_obj['data']['token']
            return token
    return None


def get_UBI(cookie, tokens):
    url = ''.join([

                    PASSPORT_URL,
                    '?loginhistory',
                    '&token=', tokens['token'],
                    '&tpl=pp&apiver=v3',
                    '&tt=', timestamp,
                    ])
    headers={'Referer': REFERER,}

    headers_merged = default_headers.copy()
    #merge the headers
    for key in headers.keys():
        headers_merged[key] = headers[key]

    req=requests.get(url, headers=headers_merged, cookies=cookie, timeout=50)
    if req:
        ubi=req.headers['Set-Cookie']
        return ubi
    return None


def get_public_key(cookie, tokens):
    url = ''.join([
                    PASSPORT_BASE,
                    'v2/getpublickey',
                    '?token=', tokens['token'],
                    '&tpl=pp&apiver=v3&tt=', timestamp,

                    ])

    headers={'Referer': REFERER,}

    headers_merged = default_headers.copy()
    #merge the headers
    for key in headers.keys():
        headers_merged[key] = headers[key]

    req = requests.get(url, headers=headers_merged, cookies=cookie, timeout=50)
    if req:
        data = json_loads_single(req.text)
        return data
    return None


def post_login(cookie, tokens, username, password_enc, rsakey='', verifycode='', codeString=''):
    url=PASSPORT_LOGIN
    headers={
            'Accept': ACCEPT_HTML,
            'Referer': REFERER,
            'Connection': 'Keep-Alive',
    }

    headers_merged = default_headers.copy()
    #merge the headers
    for key in headers.keys():
        headers_merged[key] = headers[key]

    data={
        'staticpage':'https%3A%2F%2Fpassport.baidu.com%2Fstatic%2Fpasspc-account%2Fhtml%2Fv3Jump.html',
        'charset':'UTF-8',
        'token':tokens['token'],
        'tpl':'pp',
        'subpro':'',
        'apiver':'v3',
        'tt': timestamp,
        'codestring':codeString,
        'safeflg':'0',
        'u':'http%3A%2F%2Fpassport.baidu.com%2F',
        'isPhone':'',
        'quick_user':'0',
        'logintype':'basicLogin',
        'logLoginType':'pc_loginBasic&idc=',
        'loginmerge':'true',
        'username':username,
        'password':password_enc,
        'verifycode':verifycode,
        'mem_pass':'on',
        'rsakey':rsakey,
        'crypttype':'12',
        'ppui_logintime':ppui_logintime,
        'callback':'parent.bd__pcbs__28g1kg',

        }
    req = requests.post(url, headers=headers_merged, cookies=cookie, data=data, timeout=50)
    content = req.text
    if content:
        match = re.search('"(err_no[^"]+)"', content)
        if not match:
            return (-1, None)
        query = dict(urlparse.parse_qsl(match.group(1)))
        query['err_no'] = int(query['err_no'])
        err_no = query['err_no']
        if err_no == 0 or err_no == 18:
            auth_cookie = req.headers['Set-Cookie']
            keys = ['STOKEN','HOSUPPORT','BDUSS','BAIDUID','USERNAMETYPE','PTOKEN','PASSID','UBI','PANWEB','HISTORY','cflag','SAVEUSERID']
            auth_cookie = add_cookie(cookie,auth_cookie,keys)
            return (0, auth_cookie)
        elif err_no == 257:
            return (err_no, query)
        elif err_no == 400031:
            return (err_no, query)
        else:
            return (err_no, query)
    else:
        return (-1, None)


def get_signin_vcode(cookie, codeString):
        url=''.join([
                        PASSPORT_BASE,
                        'cgi-bin/genimage?',
                        codeString,
                    ])
        headers={'Referer':REFERER,}

        headers_merged = default_headers.copy()
        #merge the headers
        for key in headers.keys():
            headers_merged[key] = headers[key]
        req=requests.get(url, headers=headers_merged, cookies=cookie, timeout=50)
        #vcode_data is bytes
        vcode_data=req.content
        if vcode_data:
            vcode_path = os.path.join(utils.data_dir(), 'vcode.png')
            with open(vcode_path, 'wb') as fh:
                fh.write(vcode_data)

        return vcode_path


def parse_bdstoken(content):
    bdstoken = ''
    bds_re = re.compile('"bdstoken"\s*:\s*"([^"]+)"', re.IGNORECASE)
    bds_match = bds_re.search(content)
    if bds_match:
        bdstoken = bds_match.group(1)
        return bdstoken
    else:
        return None


#get baidu accout token
def get_bdstoken(temp_cookie):
    url = PAN_REFERER
    headers_merged = default_headers.copy()

    req = requests.get(url, headers=headers_merged, cookies=temp_cookie, timeout=50)
    req.encoding = 'utf-8'
    if req:
        _cookie = req.headers['Set-Cookie']
        key = ['STOKEN','SCRC','PANPSC']
        auth_cookie = add_cookie(temp_cookie, _cookie, key)
        return (auth_cookie, parse_bdstoken(req.text))
    else:
        return None
