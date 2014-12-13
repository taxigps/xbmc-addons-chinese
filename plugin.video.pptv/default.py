# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, gzip, datetime, StringIO, urlparse
try:
	import json
except:
	import simplejson as json
import ChineseKeyboard

# Plugin constants
__addonname__ = "PPTV视频"
__addonid__ = "plugin.video.pptv"
__addon__ = xbmcaddon.Addon(id=__addonid__)

UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent_IE = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'

PPTV_LIST = 'http://list.pptv.com/'
PPTV_WEBPLAY_XML = 'http://web-play.pptv.com/'
PPTV_TV_LIST = 'http://live.pptv.com/list/tv_list'
PPTV_META_JSON = 'http://svcdn.pptv.com/show/v2/meta.json'
PPTV_PLAYLIST_JSON = 'http://svcdn.pptv.com/show/v2/playlist.json'
FLVCD_PARSER_PHP = 'http://www.flvcd.com/parse.php'
FLVCD_DIY_URL = 'http://www.flvcd.com/diy/diy00'
PPTV_SEARCH_URL = 'http://search.pptv.com/s_video/q_'
PPTV_TV_AREA_URL = 'http://live.pptv.com/api/tv_list?area_id='
PPTV_SUBJECT_LIST = 'http://live.pptv.com/api/subject_list?'

PPTV_CURRENT = '当前'
PPTV_SORT = '排序：'
PPTV_TTH = '第'
PPTV_FIELD = '节'
PPTV_PAGE = '页'
PPTV_SELECT = '按此选择'
PPTV_FIRST_PAGE = '第一页'
PPTV_LAST_PAGE = '最后一页'
PPTV_PREV_PAGE = '上一页'
PPTV_NEXT_PAGE = '下一页'
PPTV_MSG_GET_URL_FAILED = '无法获取视频地址!'
PPTV_MSG_INVALID_URL = '无效的视频地址, 可能不是PPTV视频!'
PPTV_MSG_NO_VIP = '暂时无法观看PPTV VIP视频!'
PPTV_SEARCH = '按此进行搜索...'
PPTV_SEARCH_DESC = '请输入搜索内容'
PPTV_SEARCH_RES = '搜索结果'

# PPTV video qualities
PPTV_VIDEO_NORMAL = 0
PPTV_VIDEO_HD = 1
PPTV_VIDEO_FHD = 2
PPTV_VIDEO_BLUER = 3

# PPTV video quality values
# Note: Blue ray video is currently only available to VIP users, so pity
PPTV_VIDEO_QUALITY_VALS = ('normal', 'high', 'super', '')

PPTV_EM_QUALITY_VALS = ('收费', '超清', '蓝光', 'VIP', '登录', '独家', '首播', '最新', '直播')

PPTV_TV_AREAS = 35
PPTV_LIVE_TYPES = { 'http://live.pptv.com/list/sports_program/' : '35', 'http://live.pptv.com/list/game_program/' : '5', 'http://live.pptv.com/list/finance/' : '47' }

##### Common functions #####

dbg = False
dbglevel = 3

def GetHttpData(url, agent = UserAgent_IPAD):
	#print "getHttpData: " + url
	req = urllib2.Request(url)
	req.add_header('Accept-encoding', 'gzip')
	req.add_header('User-Agent', agent)
	try:
		response = urllib2.urlopen(req)
		httpdata = response.read()
		if response.headers.get('content-encoding', None) == 'gzip':
			try:
				tmpdata = gzip.GzipFile(fileobj = StringIO.StringIO(httpdata)).read()
				httpdata = tmpdata
			except:
				print "Invalid gzip content on: " + url
		charset = response.headers.getparam('charset')
		response.close()
	except:
		print 'GetHttpData Error: %s' % url
		return ''
	match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
	if len(match)>0:
		charset = match[0]
	if charset:
		charset = charset.lower()
		if (charset != 'utf-8') and (charset != 'utf8'):
			httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')
	return httpdata

def _getDOMContent(html, name, match, ret):  # Cleanup
	log("match: " + match, 3)

	endstr = u"</" + name  # + ">"

	start = html.find(match)
	end = html.find(endstr, start)
	pos = html.find("<" + name, start + 1 )

	log(str(start) + " < " + str(end) + ", pos = " + str(pos) + ", endpos: " + str(end), 8)

	while pos < end and pos != -1:  # Ignore too early </endstr> return
		tend = html.find(endstr, end + len(endstr))
		if tend != -1:
			end = tend
		pos = html.find("<" + name, pos + 1)
		log("loop: " + str(start) + " < " + str(end) + " pos = " + str(pos), 8)

	log("start: %s, len: %s, end: %s" % (start, len(match), end), 3)
	if start == -1 and end == -1:
		result = u""
	elif start > -1 and end > -1:
		result = html[start + len(match):end]
	elif end > -1:
		result = html[:end]
	elif start > -1:
		result = html[start + len(match):]

	if ret:
		endstr = html[end:html.find(">", html.find(endstr)) + 1]
		result = match + result + endstr

	log("done result length: " + str(len(result)), 3)
	return result

def _getDOMAttributes(match, name, ret):
	log("", 3)
	lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
	ret = []
	for tmp in lst:
		cont_char = tmp[0]
		if cont_char in "'\"":
			log("Using %s as quotation mark" % cont_char, 3)

			# Limit down to next variable.
			if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
				tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

			# Limit to the last quotation mark
			if tmp.rfind(cont_char, 1) > -1:
				tmp = tmp[1:tmp.rfind(cont_char)]
		else:
			log("No quotation mark found", 3)
			if tmp.find(" ") > 0:
				tmp = tmp[:tmp.find(" ")]
			elif tmp.find("/") > 0:
				tmp = tmp[:tmp.find("/")]
			elif tmp.find(">") > 0:
				tmp = tmp[:tmp.find(">")]

		ret.append(tmp.strip())

	log("Done: " + repr(ret), 3)
	if len(ret) <= 0:
		ret.append('')
	return ret

def _getDOMElements(item, name, attrs):
	log("", 3)
	lst = []
	for key in attrs:
		lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
		if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
			lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

		if len(lst) == 0:
			log("Setting main list " + repr(lst2), 5)
			lst = lst2
			lst2 = []
		else:
			log("Setting new list " + repr(lst2), 5)
			test = range(len(lst))
			test.reverse()
			for i in test:  # Delete anything missing from the next list.
				if not lst[i] in lst2:
					log("Purging mismatch " + str(len(lst)) + " - " + repr(lst[i]), 3)
					del(lst[i])

	if len(lst) == 0 and attrs == {}:
		log("No list found, trying to match on name only", 3)
		lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
		if len(lst) == 0:
			lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

	log("Done: " + str(type(lst)), 3)
	return lst

def parseDOM(html, name=u"", attrs={}, ret=False):
	log("Name: " + repr(name) + " - Attrs:" + repr(attrs) + " - Ret: " + repr(ret) + " - HTML: " + str(type(html)), 3)

	if isinstance(html, str): # Should be handled
		html = [html]
	elif isinstance(html, unicode):
		html = [html]
	elif not isinstance(html, list):
		log("Input isn't list or string/unicode.")
		return u""

	if not name.strip():
		log("Missing tag name")
		return u""

	ret_lst = []
	for item in html:
		temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
		for match in temp_item:
			item = item.replace(match, match.replace("\n", " "))

		lst = _getDOMElements(item, name, attrs)

		if isinstance(ret, str):
			log("Getting attribute %s content for %s matches " % (ret, len(lst) ), 3)
			lst2 = []
			for match in lst:
				lst2 += _getDOMAttributes(match, name, ret)
			lst = lst2
		else:
			log("Getting element content for %s matches " % len(lst), 3)
			lst2 = []
			for match in lst:
				log("Getting element content for %s" % match, 4)
				temp = _getDOMContent(item, name, match, ret).strip()
				item = item[item.find(temp, item.find(match)) + len(temp):]
				lst2.append(temp)
			lst = lst2
		ret_lst += lst

	log("Done: " + repr(ret_lst), 3)
	return ret_lst

def log(description, level=0):
	if dbg and dbglevel > level:
		print description

##### Common functions end #####

def GetPPTVCatalogs():
	cat_list = []
	links = []
	names = []

	data = GetHttpData(PPTV_TV_LIST)
	chl = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'li', attrs = { 'class' : 'level_1 ' }))
	if len(chl) > 0:
		links = parseDOM(chl, 'a', ret = 'href')
		names = parseDOM(chl, 'a')

	data = GetHttpData(PPTV_LIST)
	chl = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'div', attrs = { 'class' : 'detail_menu' }))
	if len(chl) > 0:
		links.extend(parseDOM(chl, 'a', ret = 'href'))
		names.extend(parseDOM(chl, 'a'))

	cat_list.extend([{ 'link' : re.sub('\.pptv\.com\?', '.pptv.com/?', i.encode('utf-8')), 'name' : j.encode('utf-8') } for i, j in zip(links, names)])
	return cat_list

def CheckJSLink(link):
	return (link[:11] != 'javascript:' and link or '')

def CheckValidList(val):
	return (len(val) > 0 and val[0] or '')

def GetPPTVVideoList(url, only_filter = False):
	data = GetHttpData(url)

	filter_list = []
	# get common video filters like: type/year/location...
	tmp = parseDOM(unicode(data, 'utf-8', 'ignore'), 'div', attrs = { 'class' : 'sear-menu' })
	if len(tmp) > 0:
		filters = parseDOM(tmp[0], 'dt')
		dd = parseDOM(tmp[0], 'dd')
		for k in range(len(filters)):
			links = parseDOM(dd[k], 'a', ret = 'href')
			names = parseDOM(dd[k], 'a')
			label = re.sub('^按', '', filters[k].encode('utf-8'))
			# remove dummy string after colon
			pos = label.find('：')
			if pos > 0:
				label = label[0:pos+3]
			# ugly, try two different class to get selected one
			selected_name = CheckValidList(parseDOM(dd[k], 'a', attrs = { 'class' : ' all' })).encode('utf-8')
			if len(selected_name) <= 0:
				selected_name = CheckValidList(parseDOM(dd[k], 'a', attrs = { 'class' : 'all' })).encode('utf-8')
			# select first type if can't get selected one
			if len(selected_name) <= 0 and len(names) > 0:
				selected_name = names[0].encode('utf-8')
			filter_list.append( { 
				'label' : label, 
				'selected_name' : selected_name, 
				'options' : [{ 'link' : re.sub('\.pptv\.com\?', '.pptv.com/?', i.encode('utf-8')), 'name' : j.encode('utf-8') } for i, j in zip(links, names)]
			} )

	# get special video filters like: update time
	tmp = parseDOM(unicode(data, 'utf-8', 'ignore'), 'div', attrs = { 'class' : 'sort-result-container' })
	if len(tmp) > 0:
		s_dict = { 'label' : PPTV_SORT, 'selected_name' : '', 'options' : [] }
		filters = parseDOM(tmp[0], 'li')
		sclass = parseDOM(tmp[0], 'li', ret = 'class')
		for i, j in zip(filters, sclass):
			sname = CheckValidList(parseDOM(i, 'a')).encode('utf-8')
			slink = re.sub('\.pptv\.com\?', '.pptv.com/?', CheckValidList(parseDOM(i, 'a', ret = 'href')).encode('utf-8'))
			if j == 'now':
				s_dict['selected_name'] = sname
			s_dict['options'].append({ 'link' : slink, 'name' : sname })
		filter_list.append(s_dict)

	# whether just need to get filter
	if only_filter:
		return filter_list

	# get non-live videos
	video_list = []
	videos = parseDOM(unicode(data, 'utf-8', 'ignore'), 'a', attrs = { 'class' : 'ui-list-ct' })
	video_names = parseDOM(unicode(data, 'utf-8', 'ignore'), 'a', attrs = { 'class' : 'ui-list-ct' }, ret = 'title')
	video_links = parseDOM(unicode(data, 'utf-8', 'ignore'), 'a', attrs = { 'class' : 'ui-list-ct' }, ret = 'href')
	for i in range(len(videos)):
		tmp = CheckValidList(parseDOM(videos[i], 'p', attrs = { 'class' : 'ui-pic' }))
		spcs = []
		# get mask
		mask = CheckValidList(parseDOM(videos[i], 'span', attrs = { 'class' : 'msk-txt' })).encode('utf-8')
		mask.strip()
		# get video quality
		em_class = CheckValidList(parseDOM(tmp, 'em', ret = 'class')).encode('utf-8')
		if len(em_class) > 0:
			em_class = CheckValidList(re.compile('cover ico_(\d+)').findall(em_class))
			if len(em_class) > 0:
				spcs.append('[' + PPTV_EM_QUALITY_VALS[int(em_class) - 1] + ']')
		# get video updates
		if len(mask) > 0:
			spcs.append('(' + mask + ')')
		video_list.append( { 
			'link' : video_links[i].encode('utf-8'), 
			'name' : video_names[i].encode('utf-8'), 
			'image' : CheckValidList(parseDOM(videos[i], 'img', ret = 'data-src2')).encode('utf-8'), 
			'isdir' : 1, 
			'spc' : ' '.join(spcs) 
		} )

	# get TV list
	if url == PPTV_TV_LIST:
		for i in range(PPTV_TV_AREAS):
			tmp = GetHttpData(PPTV_TV_AREA_URL + str(i + 1))
			tmp = re.sub('\s*\(', '', tmp)
			tmp = re.sub('\)\s*$', '', tmp)
			pptmp = json.loads(tmp)
			channel = parseDOM(pptmp['html'], 'td', attrs = { 'class' : 'show_channel' })
			playing = parseDOM(pptmp['html'], 'td', attrs = { 'class' : 'show_playing' })
			for i, j in zip(channel, playing):
				name = CheckValidList( [ t for t in parseDOM(i, 'a') if t.find('<img') < 0 ] ).encode('utf-8')
				image = CheckValidList(parseDOM(i, 'img', ret = 'src')).encode('utf-8')
				link = CheckValidList(parseDOM(j, 'a', ret = 'href')).encode('utf-8')
				if len(parseDOM(j, 'span', attrs = { 'class' : 'titme' })) <= 0:
					spc = ''
				else:
					spc = parseDOM(j, 'span')[-1].encode('utf-8')
				video_list.append( { 
					'link' : link, 
					'name' : name, 
					'image' : image, 
					'isdir' : 0, 
					'spc' : (len(spc) > 0 and '(' + spc + ')' or '') 
				} )
	elif url in PPTV_LIVE_TYPES:
		tmp = GetHttpData(PPTV_SUBJECT_LIST + 'date=' + datetime.datetime.now().strftime('%Y-%m-%d') + '&type=' + PPTV_LIVE_TYPES[url])
		tmp = re.sub('\s*\(', '', tmp)
		tmp = re.sub('\)\s*$', '', tmp)
		pptmp = json.loads(tmp)
		stime = parseDOM(pptmp['html'], 'td', attrs = { 'class' : 'show_time' })
		ssort = parseDOM(pptmp['html'], 'td', attrs = { 'class' : 'show_sort' })
		stitle = parseDOM(pptmp['html'], 'div', attrs = { 'class' : 'show_box' })
		for i, j, k in zip(stime, ssort, stitle):
			sname = parseDOM(j, 'a')
			slist = parseDOM(k, 'div', attrs = { 'class' : 'studio_list' })
			if len(sname) > 0 and len(slist) > 0:
				name = sname[-1].encode('utf-8')
				image = CheckValidList(parseDOM(j, 'img', ret = 'src')).encode('utf-8')
				link = re.sub('".*$', '', CheckValidList(parseDOM(slist[0], 'a', ret = 'href'))).encode('utf-8')
				spc = i.encode('utf-8') + ' ' + re.sub('\n.*', '', re.sub('<[^>]*>', '', k)).encode('utf-8')
				video_list.append( { 
					'link' : link, 
					'name' : name, 
					'image' : image, 
					'isdir' : 0, 
					'spc' : (len(spc) > 0 and '(' + spc + ')' or '') 
				} )

	# get page lists
	page = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'p', attrs = { 'class' : 'pageNum' })).encode('utf-8')
	pages_attr = {}
	if len(page) > 0:
		pages_attr['last_page'] = int(CheckValidList(re.compile('.*/\s*(\d+)').findall(page)))
		params = urlparse.parse_qs(urlparse.urlparse(url).query)
		if 'page' in params.keys():
			pages_attr['selected_page'] = int(params['page'][0])
		else:
			pages_attr['selected_page'] = 1
		tmp = re.sub('&page=\d+', '', url)
		if pages_attr['selected_page'] > 1:
			pages_attr['prev_page_link'] = tmp + '&page=' + str(pages_attr['selected_page'] - 1)
		else:
			pages_attr['prev_page_link'] = ''
		if pages_attr['selected_page'] < pages_attr['last_page']:
			pages_attr['next_page_link'] = tmp + '&page=' + str(pages_attr['selected_page'] + 1)
		else:
			pages_attr['next_page_link'] = ''
		# get first and last page
		pages_attr['first_page_link'] = tmp + '&page=1'
		pages_attr['last_page_link'] = tmp + '&page=' + str(pages_attr['last_page'])

	return (filter_list, video_list, pages_attr)

def GetPPTVEpisodesList(name, url, thumb):
	# check whether is VIP video
	if re.match('^http://.*vip\.pptv\.com/.*$', url):
		xbmcgui.Dialog().ok(__addonname__, PPTV_MSG_NO_VIP)
		return (None, [], None)

	data = GetHttpData(url)

	# get channel ID
	cid = CheckValidList(re.compile('var webcfg\s*=.*\s*["\']id["\']\s*:\s*(\d+)\s*,').findall(data))
	pid = CheckValidList(re.compile('var webcfg\s*=.*\s*["\']pid["\']\s*:\s*["\']?\s*(\d+)["\']?\s*,').findall(data))
	channel_id = CheckValidList(re.compile('var webcfg\s*=.*\s*["\']channel_id["\']\s*:\s*["\']?\s*(\d+)["\']?\s*,').findall(data))

	if len(cid) > 0 or len(pid) > 0 or len(channel_id) > 0:
		video_list = []

		tmpid = (len(cid) > 0 and cid or channel_id)
		tmp = GetHttpData(PPTV_META_JSON + '?cid=' + tmpid)
		pptmp = json.loads(tmp)
		if pptmp['err'] != 0 or 'count' in pptmp['data']:
			tmp = GetHttpData(PPTV_PLAYLIST_JSON + '?pindex=1&psize=' + str('count' in pptmp['data'] and pptmp['data']['count'] or 500) + '&sid=' + (int(pid) <= 0 and tmpid or pid))
			ppvideos = json.loads(tmp)
			for video in ppvideos['data']['videos']:
				link = re.sub('\[URL\]', video['url'], ppvideos['data']['urlFormat'])
				image = re.sub('\[SN\]', str(video['sn']), ppvideos['data']['picUrlFormat'])
				image = re.sub('\[PIC\]', str(video['cid']), image)
				video_list.append( { 
					'link' : link.encode('utf-8'), 
					'name' : video['title'].encode('utf-8'), 
					'image' : image.encode('utf-8'), 
					'isdir' : -1, 
					'spc' : '' 
				} )
			return (None, video_list, None)

	# no channel ID, maybe only contain one video link
	tmp = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'p', attrs = { 'class' : 'btn_play' }))
	if len(tmp) > 0:
		links = parseDOM(tmp, 'a', ret = 'href');
		return (None, [ { 'link' : i.encode('utf-8'), 'name' : name, 'image' : thumb, 'isdir' : 0, 'spc' : '' } for i in links], None)
	else:
		return None

def GetPPTVVideoURL_Flash(url, quality):
	data = GetHttpData(url, UserAgent_IE)
	# get video ID
	vid = CheckValidList(re.compile('"id"\s*:\s*(\d+)\s*,').findall(data))
	if len(vid) <= 0:
		return []

	# get data
	data = GetHttpData(PPTV_WEBPLAY_XML + 'webplay3-0-' + vid + '.xml&ft=' + str(quality) + '&version=4&type=web.fpp')

	# get current file name and index
	rid = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'channel', ret = 'rid'))
	cur = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'file', ret = 'cur'))

	if len(rid) <= 0 or len(cur) <= 0:
		return []

	dt = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'dt', attrs = { 'ft' : cur.encode('utf-8') }))
	if len(dt) <= 0:
		return []

	# get server and file key
	sh = CheckValidList(parseDOM(dt, 'sh'))
	f_key = CheckValidList(parseDOM(dt, 'key'))
	if len(sh) <= 0:
		return []

	# get segment list
	dragdata = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'dragdata', attrs = { 'ft' : cur.encode('utf-8') }))
	if len(dragdata) <= 0:
		return []
	sgms = parseDOM(dragdata, 'sgm', ret = 'no')
	if len(sgms) <= 0:
		return []

	# get key from flvcd.com, sorry we can't get it directly by now
	data = GetHttpData(FLVCD_PARSER_PHP + '?format=' + PPTV_VIDEO_QUALITY_VALS[int(cur.encode('utf-8'))] + '&kw=' + url)
	forms = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'form', attrs = { 'name' : 'mform' }))
	if len(forms) <= 0:
		return []
	downparseurl = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'form', attrs = { 'name' : 'mform' }, ret = 'action'))
	# get hidden values in form
	input_names = parseDOM(forms.encode('utf-8'), 'input', attrs = { 'type' : 'hidden' }, ret = 'name')
	input_values = parseDOM(forms.encode('utf-8'), 'input', attrs = { 'type' : 'hidden' }, ret = 'value')
	if min(len(input_names), len(input_names)) <= 0:
		return []

	data = GetHttpData(downparseurl + '?' + urllib.urlencode(zip(input_names, input_values)))
	flvcd_id = CheckValidList(re.compile('xdown\.php\?id=(\d+)').findall(data))
	if len(flvcd_id) <= 0:
		return []

	data = GetHttpData(FLVCD_DIY_URL + flvcd_id + '.htm')
	#xbmcgui.Dialog().ok(__addonname__, data)
	key = CheckValidList(re.compile('<U>.*&(key=[^&\n]*)').findall(data))
	if len(key) <= 0:
		return []

	url_list = []
	# add segments of video
	for sgm in sgms:
		url_list.append('http://' + sh.encode('utf-8') + '/' + sgm.encode('utf-8') + '/' + rid.encode('utf-8') + '?type=fpp&' + key + '&k=' + f_key.encode('utf-8'))
	return url_list

def GetPPTVVideoURL(url, quality):
	# check whether is PPTV video
	domain = CheckValidList(re.compile('^http://(.*\.pptv\.com)/.*$').findall(url))
	if len(domain) <= 0:
		xbmcgui.Dialog().ok(__addonname__, PPTV_MSG_INVALID_URL)
		return []

	data = GetHttpData(url)

	# new key for query XML
	kk = CheckValidList(re.compile('%26kk%3D([^"\']*)["\'],').findall(data))

	# try to directly get iPad live video URL
	ipadurl = CheckValidList(re.compile(',\s*["\']ipadurl["\']\s*:\s*["\']([^"\']*)["\']').findall(data))
	if len(ipadurl) > 0:
		ipadurl = re.sub('\\\/', '/', ipadurl)
		# remove unneeded character if needed
		ipadurl = ipadurl.replace('}', '')
		if ipadurl.find('?type=') < 0:
			ipadurl += '?type=m3u8.web.pad'
		if len(kk) > 0:
			ipadurl += '&kk=' + kk
		ipadurl += '&o=' + domain
		return [ipadurl]

	# get sports iPad live URL
	ipadurl = CheckValidList(re.compile('["\']pbar_video_(\d+)["\']').findall(data))
	if len(ipadurl) > 0:
		return [ PPTV_WEBPLAY_XML + 'web-m3u8-' + ipadurl + '.m3u8?type=m3u8.web.pad&o=' + domain ]

	# try to get iPad non-live video URL
	if 'true' == __addon__.getSetting('ipad_video'):
		vid = CheckValidList(re.compile('"id"\s*:\s*(\d+)\s*,').findall(data))
		if len(vid) <= 0:
			return []

		if len(kk) <= 0:
			return []

		# get data
		ipadurl = PPTV_WEBPLAY_XML + 'webplay3-0-' + vid + '.xml&version=4&type=m3u8.web.pad'
		if len(kk) > 0:
			ipadurl += '&kk=' + kk
		data = GetHttpData(ipadurl)

		# get quality
		tmp = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'file'))
		if len(tmp) <= 0:
			return []
		items = parseDOM(tmp, 'item', ret = 'rid')
		if len(items) <= 0:
			return []

		if quality >= len(items):
			# if specified quality is not in qualities list, use the last existing one
			quality = len(items) - 1

		rid = items[quality]
		cur = str(quality)

		if len(rid) <= 0 or len(cur) <= 0:
			return []

		dt = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'dt', attrs = { 'ft' : cur.encode('utf-8') }))
		if len(dt) <= 0:
			return []

		# get server and file key
		sh = CheckValidList(parseDOM(dt, 'sh'))
		f_key = CheckValidList(parseDOM(dt, 'key'))
		if len(sh) <= 0:
			return []

		rid = CheckValidList(re.compile('([^\.]*)\.').findall(rid))

		return ['http://' + sh.encode('utf-8') + '/' + rid.encode('utf-8') + '.m3u8?type=m3u8.web.pad&k=' + f_key.encode('utf-8')]
	else:
		return GetPPTVVideoURL_Flash(url, quality)

def GetPPTVSearchList(url, matchnameonly = None):
	data = GetHttpData(url)
	videos = []
	mitems = ('movie_item  filmitem ', 'movie_item  filmitem last', 'movie_item   ', 'movie_item zyitem  ', 'movie_item zyitem  last')

	for i in mitems:
		# append video list
		tmp = parseDOM(unicode(data, 'utf-8', 'ignore'), 'li', attrs = { 'class' : i })
		if len(tmp) > 0:
			videos.extend(tmp)

	video_list = []
	for video in videos:
		thumb = parseDOM(video, 'div', attrs = { 'class' : 'movie_thumb' })
		if len(thumb) <= 0:
			continue
		names = parseDOM(thumb[0], 'a', ret = 'title')
		images = parseDOM(thumb[0], 'img', ret = 'src')
		spcs = []
		spans = parseDOM(thumb[0], 'span')
		tinfos = parseDOM(thumb[0], 'div', attrs = { 'class' : 'movie_thumb_info' })
		# get video link
		tmp = parseDOM(video, 'div', attrs = { 'class' : 'movie_title' })
		if len(tmp) <= 0:
			continue
		links = parseDOM(tmp[0], 'a', ret = 'href')

		# whether need to only match specified video name
		if matchnameonly and CheckValidList(names).encode('utf-8') == matchnameonly:
			return CheckValidList(links).encode('utf-8')

		# check whether has child
		child = parseDOM(video, 'div', attrs = { 'class' : 'movie_child_tab' }, ret = 'class')
		tmp = parseDOM(video, 'div', attrs = { 'class' : 'show_list_box' }, ret = 'class')
		child.extend(tmp)
		# get video quality
		spcs.extend(['[' + i.encode('utf-8') + ']' for i in spans])
		# get video updates
		spcs.extend(['(' + re.sub('<\?.*$', '', i.encode('utf-8').strip()) + ')' for i in tinfos])
		video_list.append( { 
			'link' : CheckValidList(links).encode('utf-8'), 
			'name' : CheckValidList(names).encode('utf-8'), 
			'image' : CheckValidList(images).encode('utf-8'), 
			'isdir' : (len(child) > 0 and len(child) or -1), 
			'spc' : ' '.join(spcs) 
		} )

	# find nothing for specified video name
	if matchnameonly:
		return ''
	return (None, video_list, None)

##### PPTV functions end #####

def get_params():
	param = []
	paramstring = sys.argv[2]
	if len(paramstring) >= 2:
		params = sys.argv[2]
		cleanedparams = params.replace('?', '')
		if (params[len(params) - 1] == '/'):
			params = params[0:len(params) - 2]
		pairsofparams = cleanedparams.split('&')
		param = {}
		for i in range(len(pairsofparams)):
			splitparams = {}
			splitparams = pairsofparams[i].split('=')
			if (len(splitparams)) == 2:
				param[splitparams[0]] = splitparams[1]
	return param

def showSearchEntry(total_items):
	# show search entry
	u = sys.argv[0] + '?mode=search'
	liz = xbmcgui.ListItem('[COLOR FF00FFFF]<' + PPTV_SEARCH + '>[/COLOR]')
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, False, total_items)

def listRoot():
	roots = GetPPTVCatalogs()
	if not roots:
		return
	total_items = len(roots) + 1
	showSearchEntry(total_items)
	for i in roots:
		u = sys.argv[0] + '?url=' + urllib.quote_plus(i['link']) + '&mode=videolist&name=' + urllib.quote_plus(i['name'])
		liz = xbmcgui.ListItem(i['name'])
		xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True, total_items)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def listVideo(name, url, list_ret):
	filter_list, video_list, pages_attr = list_ret
	u = ''
	total_items = len(video_list) + 2

	# show name and page index
	title = '[COLOR FFFF0000]' + PPTV_CURRENT + ':[/COLOR] ' + name + ' (' + PPTV_TTH
	if pages_attr:
		title += str(pages_attr['selected_page']) + '/' + str(pages_attr['last_page'])
		# contribute first/previous/next/last page link and name
		page_links = [ pages_attr['first_page_link'], pages_attr['prev_page_link'], pages_attr['next_page_link'], pages_attr['last_page_link'] ]
		page_strs = [ 
			'[COLOR FFFF0000]' + PPTV_FIRST_PAGE + '[/COLOR] - ' + PPTV_TTH + ' 1 ' + PPTV_PAGE, 
			'[COLOR FFFF0000]' + PPTV_PREV_PAGE + '[/COLOR] - ' + PPTV_TTH + ' ' + str(pages_attr['selected_page'] - 1) + ' ' + PPTV_PAGE, 
			'[COLOR FFFF0000]' + PPTV_NEXT_PAGE + '[/COLOR] - ' + PPTV_TTH + ' ' + str(pages_attr['selected_page'] + 1) + ' ' + PPTV_PAGE, 
			'[COLOR FFFF0000]' + PPTV_LAST_PAGE + '[/COLOR] - ' + PPTV_TTH + ' ' + str(pages_attr['last_page']) + ' ' + PPTV_PAGE 
			]
		# increate extra page items length
		total_items += len([i for i in page_links if len(i) > 0 ])
	else:
		title += '1/1'
	title += PPTV_PAGE + ')'

	# show filter conditions if needed
	if filter_list and len(filter_list) > 0:
		tmp = [ '[COLOR FF00FF00]' + i['label'] + '[/COLOR]' + i['selected_name'] for i in filter_list ]
		title += ' [' + '/'.join(tmp) + '] (' + PPTV_SELECT + ')'
		u = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=filterlist&name=' + urllib.quote_plus(name)
	# add first item
	liz = xbmcgui.ListItem(title)
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True, total_items)

	showSearchEntry(total_items)

	# show video list
	for i in video_list:
		title = i['name']
		if len(i['spc']) > 0:
			title += ' ' + i['spc']
		is_dir = False
		# check whether is an episode target
		if (i['isdir'] > 0) or ((i['isdir'] < 0) and (not re.match('^http://v\.pptv\.com/show/.*$', i['link']))):
			is_dir = True
		u = sys.argv[0] + '?url=' + urllib.quote_plus(i['link']) + '&mode=' + (is_dir and 'episodelist' or 'playvideo') + '&name=' + urllib.quote_plus(title) + '&thumb=' + urllib.quote_plus(i['image'])
		liz = xbmcgui.ListItem(title, thumbnailImage = i['image'])
		xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, is_dir, total_items)

	# show page switcher list
	if pages_attr:
		for page_link, page_str in zip(page_links, page_strs):
			if len(page_link) > 0:
				u = sys.argv[0] + '?url=' + urllib.quote_plus(page_link) + '&mode=videolist&name=' + urllib.quote_plus(name)
				liz = xbmcgui.ListItem(page_str)
				xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True, total_items)

	xbmcplugin.setContent(int(sys.argv[1]), 'movies')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def playVideo(name, url, thumb):
	ppurls = []

	# if live page without video link, try to get video link from search result
	if re.match('^http://live\.pptv\.com/list/tv_program/.*$', url):
		url = GetPPTVSearchList(PPTV_SEARCH_URL + urllib.quote_plus(name), name)

	if len(url) > 0:
		quality = int(__addon__.getSetting('movie_quality'))
		ppurls = GetPPTVVideoURL(url, quality)

	if len(ppurls) > 0:
		playlist = xbmc.PlayList(1)
		playlist.clear()
		for i in range(0, len(ppurls)):
			title = name + ' ' + PPTV_TTH + ' ' + str(i + 1) + '/' + str(len(ppurls)) + ' ' + PPTV_FIELD
			liz = xbmcgui.ListItem(title, thumbnailImage = thumb)
			liz.setInfo(type = "Video", infoLabels = { "Title" : title })
			playlist.add(ppurls[i], liz)
		xbmc.Player().play(playlist)
	else:
		xbmcgui.Dialog().ok(__addonname__, PPTV_MSG_GET_URL_FAILED)

def listFilter(name, url):
	t_url = url
	level = 0
	dialog = xbmcgui.Dialog()
	while True:
		filter_list = GetPPTVVideoList(t_url, True)
		# show last filter
		if level >= len(filter_list) - 1:
			level = -1
		sel = dialog.select(filter_list[level]['label'], [i['name'] for i in filter_list[level]['options']])
		t_url = filter_list[level]['options'][sel]['link']
		# reach last filter, just list specified videos
		if level < 0:
			listVideo(name, t_url, GetPPTVVideoList(t_url))
			return
		level += 1

def searchPPTV():
	keyboard = ChineseKeyboard.Keyboard('', PPTV_SEARCH_DESC)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		key = keyboard.getText()
		if len(key) > 0:
			u = sys.argv[0] + '?mode=searchlist&key=' + key
			xbmc.executebuiltin('Container.Update(%s)' % u)

params = get_params()
mode = None
name = None
url = None
thumb = None
key = None

try:
	name = urllib.unquote_plus(params['name'])
except:
	pass
try:
	url = urllib.unquote_plus(params['url'])
except:
	pass
try:
	thumb = urllib.unquote_plus(params['thumb'])
except:
	pass
try:
	mode = params['mode']
except:
	pass
try:
	key = params['key']
except:
	pass

if mode == None:
	listRoot()
elif mode == 'videolist':
	listVideo(name, url, GetPPTVVideoList(url))
elif mode == 'episodelist':
	pret = GetPPTVEpisodesList(name, url, thumb)
	if pret == None:
		playVideo(name, url, thumb)
	else:
		listVideo(name, url, pret)
elif mode == 'playvideo':
	playVideo(name, url, thumb)
elif mode == 'filterlist':
	listFilter(name, url)
elif mode == 'search':
	searchPPTV()
elif mode == 'searchlist':
	listVideo(PPTV_SEARCH_RES + ' - ' + key, None, GetPPTVSearchList(PPTV_SEARCH_URL + urllib.quote_plus(key)))
