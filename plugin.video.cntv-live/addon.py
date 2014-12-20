# -*- coding: utf-8 -*-

import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import urllib2

addon = xbmcaddon.Addon(id="plugin.video.cntv-live")
addon_path = xbmc.translatePath(addon.getAddonInfo("path"))
addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, "movies")

param = sys.argv[2]

if param.startswith("?stream="):
	resp = urllib2.urlopen("http://vdn.live.cntv.cn/api2/liveHtml5.do?channel=pa://cctv_p2p_hd" + param[8:] + "&client=html5")
	data = resp.read().decode("utf-8")

	url = data[data.index('"hls3":"') + 8:]
	url = url[:url.index('"')]
	url = url.replace("master.m3u8", "index_500_av-p.m3u8")
	
	xbmc.Player().play(url)

elif param.startswith("?city="):
	city = param[6:]
	
	def addStream(channelID, channelName):
		li = xbmcgui.ListItem(channelName, iconImage=addon_path + "/resources/media/" + city + ".png")
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=sys.argv[0] + "?stream=" + channelID, listitem=li)
	
	if city == "beijing":
		addStream("btv2", "BTV文艺")
		addStream("btv3", "BTV科教")
		addStream("btv4", "BTV影视")
		addStream("btv5", "BTV财经")
		addStream("btv6", "BTV体育")
		addStream("btv7", "BTV生活")
		addStream("btv8", "BTV青少")
		addStream("btv9", "BTV新闻")
	if city == "tianjin":
		addStream("tianjinbh", "滨海新闻综合")
		addStream("tianjinbh2", "滨海综艺频道")
	if city == "guangxi":
		addStream("gxzy", "广西综艺")
	if city == "guangdong":
		addStream("cztv1", "潮州综合")
		addStream("cztv2", "潮州公共")
		addStream("foshanxinwen", "佛山新闻综合")
		addStream("shaoguanzonghe", "韶关综合")
		addStream("zhuhaiyitao", "珠海一套")
		addStream("zhuhaiertao", "珠海二套")
	if city == "sichuan":
		addStream("cdtv1", "成都新闻综合")
		addStream("cdtv5", "成都公共")
	if city == "liaoning":
		addStream("daliannews", "大连一套")
	if city == "hubei":
		addStream("hubeigonggong", "湖北公共")
		addStream("hubeijiaoyu", "湖北教育")
		addStream("hubeiyingshi", "湖北影视")
		addStream("hubeijingshi", "湖北经视")
		addStream("hubeigouwu", "湖北购物")
		addStream("jznews", "荆州新闻频道")
		addStream("jzlongs", "湖北垄上频道")
		addStream("xiangyangtai", "襄阳广播电视台")
	if city == "xinjiang":
		addStream("xjtv2", "维语新闻综合")
		addStream("xjtv3", "哈语新闻综合")
		addStream("xjtv5", "维语综艺")
		addStream("xjtv8", "哈语综艺")
		addStream("xjtv9", "维语经济生活")
	if city == "hebei":
		addStream("shijiazhuangsantao", "石家庄三套")
		addStream("xingtaizonghe", "邢台综合")
		addStream("xingtaishenghuo", "邢台生活")
		addStream("xingtaigonggong", "邢台公共")
		addStream("xingtaishahe", "邢台沙河")
	if city == "shandong":
		addStream("jinannews", "济南新闻")
	if city == "yunnan":
		addStream("lijiangnews", "丽江新闻综合频道")
		addStream("lijiangpublic", "丽江公共频道")
	if city == "neimenggu":
		addStream("neimenggu2", "蒙语频道")
	if city == "jiangsu":
		addStream("nanjingnews", "南京新闻")
		addStream("nantongxinwen", "南通新闻频道")
		addStream("nantongshejiao", "南通社教频道")
	if city == "zhejiang":
		addStream("nbtv1", "宁波一套")
		addStream("nbtv2", "宁波二套")
		addStream("nbtv3", "宁波三套")
		addStream("nbtv4", "宁波四套")
		addStream("nbtv5", "宁波五套")
	if city == "shanghai":
		addStream("shnews", "上海新闻综合")
	if city == "fujian":
		addStream("xiamen1", "厦门一套")
		addStream("xiamen2", "厦门二套")
		addStream("xiamen3", "厦门三套")
		addStream("xiamen4", "厦门四套")
	if city == "shaanxi":
		addStream("xiannews", "西安新闻")
	if city == "xizang":
		addStream("xizang2", "藏语频道")
	
	xbmcplugin.endOfDirectory(addon_handle)

elif param.startswith("?category="):
	category = param[10:]
	
	def addStream(channelID, channelName):
		li = xbmcgui.ListItem(channelName, iconImage=addon_path + "/resources/media/" + channelID + ".png")
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=sys.argv[0] + "?stream=" + channelID, listitem=li)
	
	if category == "yangshi":
		addStream("cctv1", "CCTV-1 综合")
		addStream("cctv2", "CCTV-2 财经")
		addStream("cctv3", "CCTV-3 综艺")
		addStream("cctv4", "CCTV-4 (亚洲)")
		addStream("cctveurope", "CCTV-4 (欧洲)")
		addStream("cctvamerica", "CCTV-4 (美洲)")
		addStream("cctv5", "CCTV-5 体育")
		addStream("cctv6", "CCTV-6 电影")
		addStream("cctv7", "CCTV-7 军事农业")
		addStream("cctv8", "CCTV-8 电视剧")
		addStream("cctvjilu", "CCTV-9 纪录")
		addStream("cctvdoc", "CCTV-9 纪录(英)")
		addStream("cctv10", "CCTV-10 科教")
		addStream("cctv11", "CCTV-11 戏曲")
		addStream("cctv12", "CCTV-12 社会与法")
		addStream("cctv13", "CCTV-13 新闻")
		addStream("cctvchild", "CCTV-14 少儿")
		addStream("cctv15", "CCTV-15 音乐")
		addStream("cctv9", "CCTV-NEWS")
		addStream("cctv5plus", "CCTV体育赛事")
	if category == "weishi":
		addStream("anhui", "安徽卫视")
		addStream("btv1", "北京卫视")
		addStream("bingtuan", "兵团卫视")
		addStream("dongfang", "东方卫视")
		addStream("dongnan", "东南卫视")
		addStream("gansu", "甘肃卫视")
		addStream("guangdong", "广东卫视")
		addStream("guizhou", "贵州卫视")
		addStream("hebei", "河北卫视")
		addStream("heilongjiang", "黑龙江卫视")
		addStream("hubei", "湖北卫视")
		addStream("jilin", "吉林卫视")
		addStream("kangba", "康巴卫视")
		addStream("liaoning", "辽宁卫视")
		addStream("travel", "旅游卫视")
		addStream("ningxia", "宁夏卫视")
		addStream("qinghai", "青海卫视")
		addStream("shandong", "山东卫视")
		addStream("shan1xi", "山西卫视")
		addStream("shan3xi", "陕西卫视")
		addStream("shenzhen", "深圳卫视")
		addStream("tianjin", "天津卫视")
		addStream("xizang", "西藏卫视")
		addStream("xiamen", "厦门卫视")
		addStream("xianggangweishi", "香港卫视")
		addStream("yanbian", "延边卫视")
		addStream("yunnan", "云南卫视")
	
	if category == "shuzi":
		addStream("zhongxuesheng", "CCTV中学生")
		addStream("xinkedongman", "CCTV新科动漫")
		addStream("zhinan", "CCTV电视指南")
	
	if category == "chengshi":
		def addCity(cityID, cityName):
			li = xbmcgui.ListItem(cityName)
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=sys.argv[0] + "?city=" + cityID, listitem=li, isFolder=True)
		
		addCity("beijing", "Beijing 北京")
		addCity("fujian", "Fujian 福建")
		addCity("guangdong", "Guangdong 广东")
		addCity("guangxi", "Guangxi 广西")
		addCity("hebei", "Hebei 河北")
		addCity("hubei", "Hubei 湖北")
		addCity("jiangsu", "Jiangsu 江苏")
		addCity("liaoning", "Liaoning 辽宁")
		addCity("neimenggu", "Inner Mongolia 内蒙古")
		addCity("shandong", "Shandong 山东")
		addCity("shaanxi", "Shaanxi 陕西")
		addCity("shanghai", "Shanghai 上海")
		addCity("sichuan", "Sichuan 四川")
		addCity("tianjin", "Tianjin 天津")
		addCity("xizang", "Tibet 西藏")
		addCity("xinjiang", "Xinjiang 新疆")
		addCity("yunnan", "Yunnan 云南")
		addCity("zhejiang", "zhejiang 浙江")
	
	xbmcplugin.endOfDirectory(addon_handle)
	
else:
	def addCategory(categoryID, categoryName):
			li = xbmcgui.ListItem(categoryName)
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=sys.argv[0] + "?category=" + categoryID, listitem=li, isFolder=True)
	
	addCategory("yangshi", "央视频道")
	addCategory("weishi", "卫视频道")
	addCategory("shuzi", "数字频道")
	addCategory("chengshi", "城市频道")
	
	xbmcplugin.endOfDirectory(addon_handle)
