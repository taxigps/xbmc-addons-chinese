# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon,  xbmcplugin
import sys, urllib, urlparse, string

try:
	import simplejson
except ImportError:
	import json as simplejson

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo("name")

def log(txt):
	message = "%s: %s" % (__addonname__, unicode(txt).encode('utf-8'))
	print(message)
	#xbmc.log(msg = message, level = xbmc.LOGDEBUG)

class BaiduFmPlayer(xbmc.Player):
	def __init__(self):
		xbmc.Player.__init__(self)
		self.channelId = None
		self.songInfos = []
		self.songIds = []
		self.playedSongs = []
		self.playListSize = 1
		self.playing = False
	
	def genPluginUrl(self, params):
		utf8Params = {}
		for key, value in params.iteritems():
			utf8Params[key] = unicode(value).encode('utf-8')
		return self.pluginName + "?" + urllib.urlencode(utf8Params)
	
	def getParam(self, key):
		if self.params.has_key(key):
			return self.params[key]
		else:
			return None
		
	def parseArgv(self, argv):
		print argv
		self.pluginName = argv[0]
		self.windowId = int(argv[1])
		self.params = dict(urlparse.parse_qsl(argv[2][1:]))

		action = self.getParam("action")

		if action == None:
			self.loadChannelList()
		elif action == "playchannel":
			self.channelId = self.getParam("channel_id")
			self.stop()
			self.clearPlayList()
			playlist = self.fillPlayList(self.playListSize)
			self.play(playlist)
			self.playing = True
	
	def loadChannelList(self):
		html = urllib.urlopen("http://fm.baidu.com").read()
		start = html.find("{", html.find("rawChannelList"))
		end = html.find(";", start)
		json = html[start:end].strip()
		#print json
		data = simplejson.loads(json)
		self.onChannelListLoaded(data["channel_list"])

	def onChannelListLoaded(self, channelList):
		totalItems = len(channelList)
		for channel in channelList:
			channelName = channel["channel_name"]
			channelId = channel["channel_id"]
			log("%s - %s" % (channelId, channelName))
			item = xbmcgui.ListItem(channelName)
			url = self.genPluginUrl({"action":"playchannel","channel_id":channelId})
			xbmcplugin.addDirectoryItem(self.windowId, url, item, False, totalItems)
		xbmcplugin.endOfDirectory(self.windowId)

	def clearPlayList(self):
		playlist = xbmc.PlayList(0)
		playlist.clear()
	
	def fillPlayList(self, size):
		playlist = xbmc.PlayList(0)
		for i in range(size):
			song = self.nextSong()
			listItem = xbmcgui.ListItem(song["songName"], thumbnailImage=song["songPicRadio"])
			listItem.setInfo(type="Music", infoLabels={"Title":song["songName"],"Artist":song["artistName"],"Album":song["albumName"]})
			playlist.add(song["url"], listItem)
		return playlist

	def nextSong(self):
		if(len(self.songInfos) <= 0):
			while(len(self.songIds) < 10):
				self.songIds += self.loadSongList(self.channelId)
			ids = self.songIds[0:10]
			self.songIds = self.songIds[10:]
			self.songInfos += self.loadSongLinks(ids)
		return self.songInfos.pop(0)

	def loadSongList(self, channelId):
		html = urllib.urlopen("http://fm.baidu.com/dev/api/?tn=playlist&format=json&id="+urllib.quote(channelId)).read()
		json = simplejson.loads(html)
		ids = []
		for song in json["list"]:
			ids.append(song["id"])
		return ids

	def loadSongLinks(self, ids):
		ids = string.join([str(i) for i in ids], ',')
		html = urllib.urlopen("http://music.baidu.com/data/music/fmlink?type=mp3&rate=320&songIds="+urllib.quote(ids)).read()
		data = simplejson.loads(html)
		xcode = data["data"]["xcode"]
		songs = data["data"]["songList"]
		for song in songs:
			song["url"] = song["songLink"] + "?xcode=" + xcode
			log("%s - %s(%s)" % (song["songName"], song["artistName"], song["url"]))
		return songs

	def removePlayedItems(self):
		playlist = xbmc.PlayList(0)
		for song in self.playedSongs:
			playlist.remove(song)
			log("remove played:%s" % song)
		self.playedSongs = []
		return playlist
	
	def setCurrentPlaying(self):
		try:
			self.playedSongs.append(self.getPlayingFile())
			log("%s:[%s]" % ("playedSongs", string.join(self.playedSongs, ",")))
		except:
			log("setCurrentPlaying Error")

	def shouldClose(self):
		return not self.playing

	def onPlayBackEnded(self):
		log("onPlayBackEnded")
		#self.stop()
		#playlist = self.removePlayedItems()
		#self.play(playlist)

	def onPlayBackPaused(self):
		log("onPlayBackPaused")

	def onPlayBackResumed(self):
		log("onPlayBackResumed")

	def onPlayBackSeek(self):
		log("onPlayBackSeek")

	def onPlayBackSeekChapter(self):
		log("onPlayBackSeekChapter")

	def onPlayBackSpeedChanged(self):
		log("onPlayBackSpeedChanged")

	def onPlayBackStarted(self):
		log("onPlayBackStarted")
		self.playing = True
		self.fillPlayList(1)
		#self.removePlayedItems()
		#self.setCurrentPlaying()

	def onPlayBackStopped(self):
		log("onPlayBackStopped")
		self.clearPlayList()
		self.playing = False

	def onQueueNextItem(self):
		log("onQueueNextItem")


log("addon start")

player = BaiduFmPlayer()
player.parseArgv(sys.argv)

while(not player.shouldClose()):
	xbmc.sleep(1000)

log("addon quit")



