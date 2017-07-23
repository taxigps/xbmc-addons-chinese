# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon

__addon__     = xbmcaddon.Addon()
__addon__id__ = __addon__.getAddonInfo('id')

CHANNEL_CCTV = [
	["cctv1",       "CCTV-1 综合"],
	["cctv2",       "CCTV-2 财经"],
	["cctv3",       "CCTV-3 综艺"],
	["cctv4",       "CCTV-4 (亚洲)"],
	["cctveurope",  "CCTV-4 (欧洲)"],
	["cctvamerica", "CCTV-4 (美洲)"],
	["cctv5",       "CCTV-5 体育"],
	["cctv5plus",   "CCTV体育赛事"],
	["cctv6",       "CCTV-6 电影"],
	["cctv7",       "CCTV-7 军事 农业"],
	["cctv8",       "CCTV-8 电视剧"],
	["cctvjilu",    "CCTV-9 纪录"],
	["cctvdoc",     "CCTV-9 纪录(英)"],
	["cctv10",      "CCTV-10 科教"],
	["cctv11",      "CCTV-11 戏曲"],
	["cctv12",      "CCTV-12 社会与法"],
	["cctv13",      "CCTV-13 新闻"],
	["cctvchild",   "CCTV-14 少儿"],
	["cctv15",      "CCTV-15 音乐"],
	["cctv9",       "CCTV-NEWS"],
]
CHANNEL_PROV = [
	["anhui",       "安徽卫视"],
	["btv1",        "北京卫视"],
	["bingtuan",    "兵团卫视"],
	["chongqing",   "重庆卫视"],
	["dongfang",    "东方卫视"],
	["dongnan",     "东南卫视"],
	["gansu",       "甘肃卫视"],
	["guangdong",   "广东卫视"],
	["guangxi",     "广西卫视"],
	["guizhou",     "贵州卫视"],
	["hebei",       "河北卫视"],
	["henan",       "河南卫视"],
	["heilongjiang", "黑龙江卫视"],
	["hubei",       "湖北卫视"],
	["hunan",       "湖南卫视"],
	["jilin",       "吉林卫视"],
	["jiangsu",     "江苏卫视"],
	["jiangxi",     "江西卫视"],
	["kangba",      "康巴卫视"],
	["liaoning",    "辽宁卫视"],
	["neimenggu",   "内蒙古卫视"],
	["ningxia",     "宁夏卫视"],
	["qinghai",     "青海卫视"],
	["shandong",    "山东卫视"],
	["sdetv",       "山东教育台"],
	["shenzhen",    "深圳卫视"],
	["shan1xi",     "山西卫视"],
	["shan3xi",     "陕西卫视"],
	["shenzhen",    "深圳卫视"],
	["sichuan",     "四川卫视"],
	["tianjin",     "天津卫视"],
	["travel",      "旅游卫视"],
	["xizang",      "西藏卫视"],
	["xiamen",      "厦门卫视"],
	["xianggangweishi", "香港卫视"],
	["xinjiang",    "新疆卫视"],
	["yanbian",     "延边卫视"],
	["yunnan",      "云南卫视"],
	["zhejiang",    "浙江卫视"],
]

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addon__id__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

def data_dir():
    return xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")

def addon_dir():
    return xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")

def openSettings():
    __addon__.openSettings()

def getSetting(name):
    return __addon__.getSetting(name)

def setSetting(name,value):
    __addon__.setSetting(name,value)

def getString(string_id):
    return __addon__.getLocalizedString(string_id)
