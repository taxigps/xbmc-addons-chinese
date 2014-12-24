# -*- coding: utf-8 -*-
import urllib,urllib2,re,os,sys
import xbmcplugin,xbmcgui,xbmc

#BaiduRadio - by Robinttt 2009.

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
URL = 'http://list.mp3.baidu.com/radio/iframe.html'
BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'

def request(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', UserAgent)
	response = urllib2.urlopen(req)
	link = response.read()
	response.close()
	try:
		link = link.decode("gbk").encode("utf-8")
	except:
		pass
	link = re.sub('\s','',link)
	return link

def addLink(name, url, iconimage = '', title = None, isFolder = False):
	li=xbmcgui.ListItem(name,iconImage=iconimage, thumbnailImage=iconimage)
	if not title: title = name
	print('url:',url)
	li.setInfo(type= 'Video' if 'm3u' in url else 'Music',infoLabels={"Title":title})
	xbmcplugin.addDirectoryItem(int(sys.argv[1]),url,li, isFolder)

def addDir(name, url = '', mode = 0, iconimage = ''):
	query = {'name': name, 'url': url, 'mode': mode}
	u = "%s?%s" % (sys.argv[0], urllib.urlencode(query))
	addLink(name, u, iconimage, isFolder = True)

def Roots(url):
	link = request(url)
	match = re.findall('</a><h3>(.+?)</h3>', link)
	for name in match:
		addDir(name, url, 1)

def addChina():
	#央广网
	url = 'http://bfq.cnr.cn/zhibo/'
	link = request(url)
	urls=re.compile('http://.*?/playlist\.m3u8').findall(link)
	nms=re.compile('(?<!-)<td><ahref="javascript:onclick=changeTab1\(\d*?\);">(.*?)</a></td>').findall(link)
	for i, item in enumerate(urls):
		addLink('%d.%s'%(i+1, nms[i]), item)

def addBeijing():
	#北广网
	url = 'http://listen.rbc.cn/baidu/'
	link = request(url)
	match=re.compile('varaddrs=newArray\("","(.+?)"\);').findall(link)
	ids=match[0].split('","')
	match=re.compile('varstation=newArray\("","(.+?)"\);').findall(link)
	nms=match[0].split('","')
	for i, item in enumerate(ids):
		addLink('%d.%s'%(i+1, nms[i]), 'mms://alive.rbc.cn/'+item)

def Lists(url,name):
	link = request(url)
	name1=name.replace('(','\(').replace(')','\)')
	name=re.sub('\((.+?)\)','',name)
	addDir(BANNER_FMT % ('当前类别：'+name), '', 20)

	if '国家' in name: addChina()
	elif '北京' in name: addBeijing()
	else:
		match=re.findall('<h3>'+name1+'</h3>(.+?)</div></div>', link) 
		match0=re.findall('<imgsrc="(.+?)".+?<div><ahref="(.+?)">(.+?)</a>', match[0]) 
		num=0
		for img1,url1,name1 in match0:
			img1=img1.replace('./','http://list.mp3.baidu.com/radio/')
			num+=1
			addLink('%d.%s'%(num, name1), url1, img1, name1)

def get_params():
	params=sys.argv[2]
	param = {}
	if len(params) >= 2:
		cleanedparams = params.rsplit('?',1)
		if len(cleanedparams) == 2:
			cleanedparams = cleanedparams[1]
		else:
			cleanedparams = params.replace('?','')
		param = dict(urllib2.urlparse.parse_qsl(cleanedparams))
	print(param)
	return param

params=get_params()
url=params.get('url', URL)
name=params.get('name', '')
mode=int(params.get('mode', 0))

if mode == 0:
	Roots(url)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 1:
	Lists(url,name)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
