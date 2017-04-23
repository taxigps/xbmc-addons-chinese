# -*- coding: utf-8 -*-
# default.py

import xbmcgui, xbmcaddon, xbmc
import json, sys, urllib, urllib2, gzip, StringIO, re, os, time, threading, socket, base64, math, cookielib
from video_concatenate import video_concatenate
try:
   import StorageServer
except:
   import storageserverdummy as StorageServer

__addonid__ = "plugin.video.youkutv"
__addon__ = xbmcaddon.Addon(id=__addonid__)
__cwd__ = __addon__.getAddonInfo('path')
__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
sys.path.append (__resource__)
cache = StorageServer.StorageServer(__addonid__, 87600)
m3u8_file = __cwd__ + '/v.m3u8'
vc = video_concatenate()

#Set timeout of socket
socket.setdefaulttimeout(10)

#URL base
HOST = 'http://tv.api.3g.youku.com/'
IDS = 'pid=0ce22bfd5ef5d2c5&guid=12d60728bd267e3e0b6ab4d124d6c5f0&ngdid=357e71ee78debf7340d29408b88c85c4&ver=2.6.0&operator=T-Mobile_310260&network=WIFI&launcher=0'

#Fixed tabs
Navigation  = ['首页', '频道', '排行']
ContentID   = [520, 560, 580]
TopData=['播放排行榜', '搜索排行榜', '特色排行榜']
ChannelData={'97': {'icon': 'channel_tv_icon.png', 'title': '电视剧'},
             '669': {'icon': 'channel_child_icon.png', 'title': '少儿'},
             '96': {'icon': 'channel_movie_icon.png', 'title': '电影'},
             '100': {'icon': 'channel_anime_icon.png', 'title': '动漫'},
             '85': {'icon': 'channel_variety_icon.png', 'title': '综艺'},
             '84': {'icon': 'channel_documentary_icon.png', 'title': '纪录片'},
             '87': {'icon': 'channel_education_icon.png', 'title': '教育'},
             }
mainData = [{'title': '搜索', 'image': 'yk_search.jpg', 'mtype': 'search'},
            {'title': '观看记录', 'image': 'yk_history.jpg', 'mtype': 'history'},
            {'title': '收藏', 'image': 'yk_favor.jpg', 'mtype': 'favor'}]
settings_data = {'resolution':[u'1080P', u'超清', u'高清', u'标清', u'标清(3GP)'],
                 'resolution_type':[['hd3','mp4hd3'], ['hd2','mp4hd2'], ['mp4','mp4hd'], ['flv','flvhd'], ['3gphd']],
                 'language':[u'默认', u'国语', u'粤语', u'英语'],
                 'language_code':[u'', u'guoyu', u'yue', u'yingyu'],
                 'play':['整合(试验阶段)', '分段', '堆叠'],
                 'play_type':['concatenate', 'list', 'stack']}
settings={'resolution':0, 'language':0, 'play':0}
resolution_map = {'3gphd':  '3gp',
                  'flv':    'flv',
                  'flvhd':  'flv',
                  'mp4':    'mp4',
                  'mp4hd':  'mp4',
                  'hd2':    'flv',
                  'mp4hd2': 'flv',
                  'hd3':    'flv',
                  'mp4hd3': 'flv'}


ACTION_MOVE_LEFT      = 1
ACTION_MOVE_RIGHT     = 2
ACTION_MOVE_UP        = 3
ACTION_MOVE_DOWN      = 4
ACTION_PAGE_UP        = 5
ACTION_PAGE_DOWN      = 6
ACTION_SELECT_ITEM    = 7
ACTION_HIGHLIGHT_ITEM = 8
ACTION_PARENT_DIR_OLD = 9
ACTION_PARENT_DIR     = 92
ACTION_PREVIOUS_MENU  = 10
ACTION_SHOW_INFO      = 11
ACTION_PAUSE          = 12
ACTION_STOP           = 13
ACTION_NEXT_ITEM      = 14
ACTION_PREV_ITEM      = 15
ACTION_SHOW_GUI       = 18
ACTION_PLAYER_PLAY    = 79
ACTION_MOUSE_LEFT_CLICK = 100
ACTION_MOUSE_MOVE     = 107
ACTION_CONTEXT_MENU   = 117


class MyPlayer(xbmc.Player):
    def __init__(self):
        self.vid = None
        self.rollback = 3
        xbmc.Player.__init__(self)

    def play(self, item='', listitem=None, windowed=False, startpos=-1, arg=None):

        self.vid = arg
        offset = 0
        startpos = 0
        self.base = 0
        self.last = 0
        self.lastpos = 0
        if item[0].getfilename() == m3u8_file:
            self.isM3U8 = True
        else:
            self.isM3U8 = False
        try:
            ret = eval(cache.get(self.vid))
            offset = ret['offset']
            if offset > self.rollback:
                offset -= self.rollback
            else:
                offset = 0
            self.base = offset
            self.last = offset
            startpos = ret['startpos']
            if startpos >= item.size():
                startpos = item.size() - 1
            self.lastpos = startpos
        except:
            pass

        if offset > 0:
            item[startpos].setProperty('StartOffset', str(offset))

        t = threading.Timer(1, self.timeEntry)
        t.start()

        try:
            xbmc.Player.play(self, item, listitem, windowed, startpos)
        except:
            xbmc.Player.play(self, item, listitem, windowed)

    def timeEntry(self):
        self.updateHistory()

        try:
            if self.isPlaying():
                t = threading.Timer(1, self.timeEntry)
                t.start()
        except:
            pass

    def onPlayBackStarted(self):
        self.updateHistory(False)
        xbmc.Player.onPlayBackStarted(self)

    def onPlayBackSeek(self, time, seekOffset):
        self.updateHistory(False, time/1000)
        xbmc.Player.onPlayBackSeek(self, time, seekOffset)

    def onPlayBackSeekChapter(self, chapter):
        self.updateHistory(False)
        xbmc.Player.onPlayBackSeek(self, chapter)

    def onPlayBackEnded(self):
        try:
            cache.delete(self.vid)
        except:
            pass
        xbmc.Player.onPlayBackEnded(self)
        vc.stop()

    def onPlayBackStopped(self):
        cache.set(self.vid, repr({'offset':self.last, 'startpos':self.lastpos}))
        vc.stop()


    def updateHistory(self, check=True, base=-1):
        if self.isPlaying() == True:
            if check == True and self.isM3U8 == True:
                offset = self.getTime()
                if (offset > self.base) and (offset < self.base + 1.5):
                    self.last += offset - self.base
                self.base = offset
            elif base == -1 or self.isM3U8 == False:
                self.last = self.getTime()
                self.base = self.last
            else:
                self.last = base
                self.base = base

            self.lastpos = xbmc.PlayList(1).getposition()

player = MyPlayer()


class BaseWindowDialog(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs):
        self.session = None
        self.oldWindow = None
        self.busyCount = 0
        xbmcgui.WindowXML.__init__( self )

    def doClose(self):
        self.session.window = self.oldWindow
        self.close()

    def onInit(self):
        if player.isPlaying():
            player.stop()
        if self.session:
            self.session.window = self
        else:
            try:
                self.session = VstSession(self)
            except:
                self.close()
        self.setSessionWindow()

    def onFocus( self, controlId ):
        self.controlId = controlId

    def setSessionWindow(self):
        try:
            self.oldWindow = self.session.window
        except:
            self.oldWindow=self
        self.session.window = self

    def onAction(self,action):
        if action.getId() == ACTION_PARENT_DIR or action.getId() == ACTION_PREVIOUS_MENU:
            if player.isPlaying():
                player.stop()
            self.doClose()
        else:
            return False

        return True

    def showBusy(self):
        if self.busyCount > 0:
            self.busyCount += 1
        else:
            self.busyCount = 1
            xbmc.executebuiltin("ActivateWindow(busydialog)")


    def hideBusy(self):
        if self.busyCount > 0:
            self.busyCount -= 1
        if self.busyCount == 0:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )


class ConfirmWindow(BaseWindowDialog):
    def __init__( self, *args, **kwargs):
        self.selected = -1
        BaseWindowDialog.__init__( self )

    def onClick( self, controlId ):
        BaseWindowDialog.onClick(self, controlId)
        if (controlId == 1410):
            self.selected = 0
            self.doClose()
        elif (controlId == 1411):
            self.selected = 1
            self.doClose()

    def select(self):
        self.doModal()
        return self.selected


class SettingsWindow(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs):
        self.resolution = settings['resolution']
        self.language = settings['language']
        self.play = settings['play']
        self.inited = False
        #BaseWindowDialog.__init__( self )
        xbmcgui.WindowXMLDialog.__init__(self)


    def onInit(self):
        #BaseWindowDialog.onInit(self)
        xbmcgui.WindowXMLDialog.onInit(self)
        self.init()


    def init(self):
        if self.inited:
            return

        selected = 0
        for i in range(len(settings_data['resolution'])):
            listitem = xbmcgui.ListItem(label=settings_data['resolution'][i])
            self.getControl(1720).addItem(listitem)
            if settings['resolution'] == i:
                listitem.select(True)
                selected = i
        self.getControl(1720).selectItem(selected)

        selected = 0
        for i in range(len(settings_data['language'])):
            listitem = xbmcgui.ListItem(label=settings_data['language'][i])
            self.getControl(1721).addItem(listitem)
            if settings['language'] == i:
                listitem.select(True)
                selected = i
        self.getControl(1721).selectItem(selected)

        selected = 0
        for i in range(len(settings_data['play'])):
            listitem = xbmcgui.ListItem(label=settings_data['play'][i])
            self.getControl(1722).addItem(listitem)
            if settings['play'] == i:
                listitem.select(True)
                selected = i
        self.getControl(1722).selectItem(selected)

        self.inited = True


    def updateSelection(self, controlId):
        if controlId == 1720 or controlId == 1721 or controlId == 1722:
            selected = self.getControl(controlId).getSelectedPosition()
            for index in  range(self.getControl(controlId).size()):
                if index != selected and self.getControl(controlId).getListItem(index).isSelected() == True:
                    self.getControl(controlId).getListItem(index).select(False)
            self.getControl(controlId).getSelectedItem().select(True)
            if controlId == 1720:
                self.resolution = self.getControl(controlId).getSelectedPosition()
            elif controlId == 1721:
                self.language = self.getControl(controlId).getSelectedPosition()
            else:
                self.play = self.getControl(controlId).getSelectedPosition()


    def onClick( self, controlId ):
        if controlId == 1710:
            self.resolution = 0
            self.language = 0
            self.play = 0

        settings['resolution'] = self.resolution
        settings['language'] = self.language
        settings['play'] = self.play
        writeSettings()
        if player.isPlaying():
            play(cache.get('currentVID'), True)
            while player.isPlaying() == False:
                xbmc.sleep(1000)
        self.close()


    def onAction(self,action):
        #BaseWindowDialog.onAction(self, action)
        xbmcgui.WindowXMLDialog.onAction(self, action)
        Id = action.getId()
        if Id == ACTION_MOVE_LEFT or  Id == ACTION_MOVE_RIGHT or Id == ACTION_MOUSE_MOVE:
            self.updateSelection(self.getFocusId())
        elif Id == ACTION_PARENT_DIR or Id == ACTION_PREVIOUS_MENU:
            self.close()
        else:
            return False


class FilterWindow(BaseWindowDialog):
    def __init__( self, *args, **kwargs):
        self.cancel = True
        self.inited = False
        self.sdata = kwargs.get('sdata')
        self.pdata = None
        BaseWindowDialog.__init__( self )


    def onInit(self):
        self.showBusy()
        try:
            BaseWindowDialog.onInit(self)
            self.init()
        except:
            pass

        self.hideBusy()

    def init(self):
        if self.inited:
            return

        data = GetHttpData(HOST + 'layout/smarttv/filter_order?' + IDS + '&cid=' + self.sdata['cid'] + '&type=show')
        data = json.loads(data)
        if data.has_key('status') == False:
            return
        if data['status'] != 'success':
            return

        self.pdata = data['results']

        for index in range(len(data['results'])):

            selected = 0
            cl = self.getControl(1620 + index)
            if data['results'][index]['cat'] != 'ob':
                listitem = xbmcgui.ListItem(label=u'全部' + data['results'][index]['title'], label2='')
                cl.addItem(listitem)

            if self.sdata.has_key(data['results'][index]['cat']):
                selectedValue = self.sdata[data['results'][index]['cat']]
            elif data['results'][index]['cat'] != 'ob':
                selectedValue = ''
                listitem.select(True)

            for i in range(len(data['results'][index]['items'])):
                item = data['results'][index]['items'][i]
                listitem = xbmcgui.ListItem(label=item['title'], label2=item['value'])
                cl.addItem(listitem)
                if item['value'] == selectedValue:
                    if data['results'][index]['cat'] == 'ob':
                        selected = i
                    else:
                        selected = i + 1
                    listitem.select(True)

            if data['results'][index]['cat'] == 'ob':
                if self.sdata.has_key(data['results'][index]['cat']) == False:
                    cl.getListItem(0).select(True)

            cl.selectItem(selected)

        if len(data['results']) < 4:
            self.getControl(1623).setEnabled(False)

        self.inited = True

    def select(self):
        self.doModal()

        if self.cancel == True:
            return self.sdata

        for i in range(4):
            cl = self.getControl(1620 + i)
            for index in  range(0, cl.size()):
                if cl.getListItem(index).isSelected():
                    if self.pdata[i]['cat'] == 'ob':
                        self.sdata[self.pdata[i]['cat']] = self.pdata[i]['items'][index]['value']
                    elif index > 0:
                        self.sdata[self.pdata[i]['cat']] = self.pdata[i]['items'][index - 1]['value']
                    else:
                        if self.sdata.has_key(self.pdata[i]['cat']):
                            del(self.sdata[self.pdata[i]['cat']])

        return self.sdata


    def updateSelection(self, controlId):
        if controlId >= 1620 and controlId <= 1623:
            selected = self.getControl(controlId).getSelectedPosition()
            for index in  range(self.getControl(controlId).size()):
                if index != selected and self.getControl(controlId).getListItem(index).isSelected() == True:
                    self.getControl(controlId).getListItem(index).select(False)
            self.getControl(controlId).getSelectedItem().select(True)

    def onClick( self, controlId ):
        if controlId == 1610:
            for i in range(4):
                cl = self.getControl(1620 + i)
                for index in  range(1, cl.size()):
                    cl.getListItem(index).select(False)
                cl.getListItem(0).select(True)

        self.cancel = False
        self.doClose()

    def onAction(self,action):
        BaseWindowDialog.onAction(self, action)
        Id = action.getId()
        if Id == ACTION_MOVE_LEFT or  Id == ACTION_MOVE_RIGHT or Id == ACTION_MOUSE_MOVE:
            self.updateSelection(self.getFocusId())


class BaseWindow(xbmcgui.WindowXML):
    def __init__( self, *args, **kwargs):
        self.session = None
        self.oldWindow = None
        self.busyCount = 0
        xbmcgui.WindowXML.__init__( self )

    def doClose(self):
        self.session.window = self.oldWindow
        self.close()

    def onInit(self):
        if player.isPlaying():
            player.stop()
        if self.session:
            self.session.window = self
        else:
            try:
                self.session = VstSession(self)
            except:
                self.close()
        self.setSessionWindow()


    def onFocus( self, controlId ):
        self.controlId = controlId

    def setSessionWindow(self):
        try:
            self.oldWindow = self.session.window
        except:
            self.oldWindow=self
        self.session.window = self

    def onAction(self,action):
        if action.getId() == ACTION_PARENT_DIR or action.getId() == ACTION_PREVIOUS_MENU:
            if player.isPlaying():
                player.stop()
            self.doClose()
        else:
            return False

        return True

    def showBusy(self):
        if self.busyCount > 0:
            self.busyCount += 1
        else:
            self.busyCount = 1
            xbmc.executebuiltin("ActivateWindow(busydialog)")


    def hideBusy(self):
        if self.busyCount > 0:
            self.busyCount -= 1
        if self.busyCount == 0:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )


class MainWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.navInited = False
        self.mainInited = False
        self.channelInited = False
        BaseWindow.__init__(self, args, kwargs)


    def onInit(self):
        BaseWindow.onInit(self)

        self.showBusy()

        try:
            self.initNavigation()
            self.initMain()
            self.initChannelTop()
        except:
            pass

        self.hideBusy()


    def initNavigation(self):
        if self.navInited:
            return

        for Id in ContentID[1:]:
            self.getControl(Id).setVisible(False)

        for item in Navigation:
            listitem = xbmcgui.ListItem(label=item)
            self.getControl(510).addItem(listitem)

        self.selectedNavigation = 0
        self.getControl(510).getListItem(0).select(True)
        self.setFocusId(510)

        self.navInited = True


    def initMain(self):
        if self.mainInited:
            return

        data = GetHttpData(HOST + 'tv/main?' + IDS)
        data = json.loads(data)
        if data.has_key('status') == False:
            return
        if data['status'] != 'success':
            return

        #for item in data['results']['m1']:
        for item in mainData:
            listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['image'])
            setProperties(listitem, item)
            self.getControl(521).addItem(listitem)

        for item in data['results']['m2']:
            listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['big_vertical_image'])
            setProperties(listitem, item)
            self.getControl(522).addItem(listitem)

        item = data['results']['m3'][0]
        listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['big_horizontal_image'])
        setProperties(listitem, item)
        self.getControl(524).addItem(listitem)

        for item in data['results']['m3'][1:]:
            listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['big_vertical_image'])
            setProperties(listitem, item)
            self.getControl(525).addItem(listitem)

        item = data['results']['m4'][0]
        listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['big_horizontal_image'])
        setProperties(listitem, item)
        self.getControl(527).addItem(listitem)

        for item in data['results']['m4'][1:]:
            listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['big_vertical_image'])
            setProperties(listitem, item)
            self.getControl(528).addItem(listitem)

        self.mainInited = True


    def initChannelTop(self):
        if self.channelInited:
            return

        data = GetHttpData(HOST + 'tv/main/top?' + IDS)
        data = json.loads(data)
        if data.has_key('status') == False:
            return
        if data['status'] != 'success':
            return

        #Channel
        for i in range(0, len(data['results']['channel']), 2):
            item = data['results']['channel'][i]
            listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['image'])
            setProperties(listitem, item)
            self.getControl(560).addItem(listitem)

        for i in range(1, len(data['results']['channel']), 2):
            item = data['results']['channel'][i]
            listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['image'])
            setProperties(listitem, item)
            self.getControl(560).addItem(listitem)

        #Top
        for item in data['results']['top']:
            listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['image'])
            setProperties(listitem, item)
            self.getControl(580).addItem(listitem)

        self.channelInited = True


    def onClick( self, controlId ):
        if controlId == 510:
            self.updateNavigation()
        elif controlId == 512:
            openWindow('mysettings', self.session)
        else:
            item = self.getControl(controlId).getSelectedItem()
            if item.getProperty('mtype') == 'show':
                openWindow('detail', self.session, sdata=item.getProperty('showid'))
            elif item.getProperty('mtype') == 'channel':
                openWindow('channel', self.session, sdata=item.getProperty('cid'))
            elif item.getProperty('mtype') == 'all_videos':
                openWindow('other', self.session)
            elif item.getProperty('mtype') == 'favor':
                openWindow('favor', self.session)
            elif item.getProperty('mtype') == 'history':
                openWindow('history', self.session)
            elif item.getProperty('mtype') == 'search':
                openWindow('search', self.session)
            elif item.getProperty('mtype') == 'top':
                openWindow('top', self.session, sdata=item.getProperty('top_id'))
            else:
                xbmcgui.Dialog().ok('提示框', '此功能暂未实现，尽请期待')


    def onAction(self, action):
        BaseWindow.onAction(self, action)
        #if action.getId() == ACTION_MOVE_LEFT or action.getId() == ACTION_MOVE_RIGHT or action.getId() == ACTION_MOUSE_MOVE:
        if action.getId() == ACTION_MOVE_LEFT or action.getId() == ACTION_MOVE_RIGHT:
            self.updateNavigation()


    def updateNavigation(self):
        if self.getFocusId() == 510:
            if self.selectedNavigation != self.getControl(510).getSelectedPosition():
                #Disable old selection
                self.getControl(510).getListItem(self.selectedNavigation).select(False)
                self.getControl(ContentID[self.selectedNavigation]).setEnabled(False)
                self.getControl(ContentID[self.selectedNavigation]).setVisible(False)

                #Enable new selection
                self.selectedNavigation = self.getControl(510).getSelectedPosition()
                if self.selectedNavigation == 0:
                    self.initMain()
                elif self.selectedNavigation == 1:
                    self.initChannelTop()
                self.getControl(ContentID[self.selectedNavigation]).setEnabled(True)
                self.getControl(ContentID[self.selectedNavigation]).setVisible(True)
                self.getControl(510).getSelectedItem().select(True)


class TopWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.subInited = False
        self.conInited = False
        self.urlArgs = {'menu_id':'1', 'pl':'50'}
        self.sdata = kwargs.get('sdata')
        BaseWindow.__init__(self, args, kwargs)


    def onInit(self):
        BaseWindow.onInit(self)

        self.showBusy()

        try:
            self.initSubChannel()
            self.initContent()
        except:
            pass

        self.hideBusy()


    def initSubChannel(self):
        if self.subInited:
            return

        #Title
        self.getControl(1502).setLabel(TopData[int(self.sdata) - 1])

        #Catagory
        data = GetHttpData(HOST + 'tv/top/menu?' + IDS + '&top_id=' + self.sdata)
        data = json.loads(data)
        if data.has_key('status') == False:
            return
        if data['status'] != 'success':
            return

        for item in data['results']:
            listitem = xbmcgui.ListItem(label=item['title'])
            setProperties(listitem, item)
            self.getControl(1510).addItem(listitem)

        self.selectedNavigation = 0
        self.getControl(1510).getListItem(0).select(True)
        self.setFocusId(1510)

        self.subInited = True


    def initContent(self):
        if self.conInited:
            return

        self.getControl(1520).reset()
        self.updateContent()

        self.conInited = True


    def updateContent(self):
        self.showBusy()

        try:
            url = HOST + 'tv/top/shows?' + IDS + '&top_id=' + self.sdata
            for k in self.urlArgs:
                url = url + '&' + k + '=' + urllib.quote_plus(self.urlArgs[k])

            data = GetHttpData(url)
            data = json.loads(data)
            if data.has_key('status') == False:
                self.hideBusy()
                return
            if data['status'] != 'success':
                self.hideBusy()
                return

            for item in data['results']:
                listitem = xbmcgui.ListItem(label=item['showname'], thumbnailImage=item['show_vthumburl_hd'])
                setProperties(listitem, item)
                self.getControl(1520).addItem(listitem)
        except:
            pass

        self.hideBusy()


    def updateSelection(self):
        if self.getFocusId() == 1510:
            if self.selectedNavigation != self.getControl(1510).getSelectedPosition():
                #Disable old selection
                self.getControl(1510).getListItem(self.selectedNavigation).select(False)
                #Enable new selection
                self.selectedNavigation = self.getControl(1510).getSelectedPosition()
                self.getControl(1510).getSelectedItem().select(True)


    def onClick( self, controlId ):
        if controlId == 1510:
            self.urlArgs['menu_id'] = getProperty(self.getControl(1510).getSelectedItem(), 'menu_id')

            self.updateSelection()

            self.conInited = False
            self.initContent()
            self.setFocusId(1520)
        elif controlId == 1520:
            item = self.getControl(controlId).getSelectedItem()
            openWindow('detail', self.session, sdata=item.getProperty('showid'))
        else:
            xbmcgui.Dialog().ok('提示框', '此功能暂未实现，尽请期待')


class ChannelWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.subInited = False
        self.conInited = False
        self.urlArgs = {'pz':'100', 'pg':'1', 'filter':''}
        self.sdata = kwargs.get('sdata')
        self.filterArgs = {'cid':self.sdata}
        BaseWindow.__init__(self, args, kwargs)


    def onInit(self):
        BaseWindow.onInit(self)

        self.showBusy()

        try:
            self.initSubChannel()
            self.initContent()
        except:
            pass

        self.hideBusy()


    def initSubChannel(self):
        if self.subInited:
            return

        #Title
        channel=ChannelData[self.sdata]
        self.getControl(601).setImage(channel['icon'])
        self.getControl(602).setLabel(channel['title'])

        #Catagory
        data = GetHttpData(HOST + 'tv/v2_0/childchannel/list?' + IDS + '&cid=' + self.sdata)
        data = json.loads(data)
        if data.has_key('status') == False:
            return
        if data['status'] != 'success':
            return


        #Add hot except child channel
        listitem = xbmcgui.ListItem(label='热播')
        self.getControl(610).addItem(listitem)

        for item in data['results']['result']:
            listitem = xbmcgui.ListItem(label=item['sub_channel_title'])
            setProperties(listitem, item)
            self.getControl(610).addItem(listitem)

        self.selectedNavigation = 0
        self.getControl(610).getListItem(0).select(True)
        self.setFocusId(620)

        self.subInited = True


    def initContent(self):
        if self.conInited:
            return

        self.urlArgs['pg'] = '1'
        self.getControl(620).reset()
        self.updateContent()

        self.conInited = True


    def updateContent(self):
        self.showBusy()

        try:
            url = HOST + 'layout/smarttv/item_list?' + IDS + '&cid=' + self.sdata
            for k in self.urlArgs:
                url = url + '&' + k + '=' + urllib.quote_plus(self.urlArgs[k])

            data = GetHttpData(url)
            data = json.loads(data)
            if data.has_key('status') == False:
                self.hideBusy()
                return
            if data['status'] != 'success':
                self.hideBusy()
                return

            for item in data['results']:
                listitem = xbmcgui.ListItem(label=item['showname'], label2=item['stripe_bottom'], thumbnailImage=item['show_vthumburl_hd'])
                setProperties(listitem, item)
                self.getControl(620).addItem(listitem)
        except:
            pass

        self.hideBusy()


    def updateSelection(self):
        if self.getFocusId() == 610:
            if self.selectedNavigation != self.getControl(610).getSelectedPosition():
                #Disable old selection
                self.getControl(610).getListItem(self.selectedNavigation).select(False)
                #Enable new selection
                self.selectedNavigation = self.getControl(610).getSelectedPosition()
                self.getControl(610).getSelectedItem().select(True)


    def onClick( self, controlId ):
        if controlId == 610:
            self.urlArgs['filter'] = getProperty(self.getControl(610).getSelectedItem(), 'filter')

            self.updateSelection()

            self.conInited = False
            self.initContent()
            self.setFocusId(620)
        elif controlId == 620:
            item = self.getControl(controlId).getSelectedItem()
            if item.getProperty('type') == 'show':
                openWindow('detail', self.session, sdata=item.getProperty('showid'))
        elif controlId == 603:
            self.filterArgs = openWindow('filter', self.session, sdata=self.filterArgs)

            self.getControl(610).selectItem(0)

            filterData = []
            for k in self.filterArgs:
                try:
                    filterData.append((unicode(k) + u':' + unicode(self.filterArgs[k])).encode('utf8)'))
                except:
                    filterData.append(k + ':' + self.filterArgs[k])
            self.urlArgs['filter'] = '|'.join(filterData)

            self.conInited = False
            self.initContent()
            self.setFocusId(620)
        else:
            xbmcgui.Dialog().ok('提示框', '此功能暂未实现，尽请期待')


    def onAction(self, action):
        BaseWindow.onAction(self, action)
        #if action.getId() == ACTION_MOVE_DOWN and self.getFocusId() == 620:
        if self.getFocusId() == 620:
            oldPos = self.getControl(620).getSelectedPosition()
            total = self.getControl(620).size()
            if total - oldPos <= 10:
                pg = int(self.urlArgs['pg']) + 1
                self.urlArgs['pg'] = str(pg)
                self.updateContent()
                self.getControl(620).selectItem(oldPos)


class OtherWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.subInited = False
        self.typeInited = False
        self.conInited = False
        self.urlArgs = {'pz':'100', 'pg':'1', 'cid':'', 'ob':'2'}
        BaseWindow.__init__(self, args, kwargs)


    def onInit(self):
        BaseWindow.onInit(self)

        self.showBusy()

        try:
            self.initType()
            self.initSubChannel()
            self.initContent()
        except:
            pass

        self.hideBusy()


    def initType(self):
        if self.typeInited:
            return

        listitem = xbmcgui.ListItem(label='最新上线')
        self.getControl(903).addItem(listitem)
        listitem = xbmcgui.ListItem(label='最多播放')
        self.getControl(903).addItem(listitem)
        self.getControl(903).getListItem(1).select(True)

        self.typeInited = True


    def initSubChannel(self):
        if self.subInited:
            return

        #Title
        self.getControl(901).setImage('channel_member_icon.png')
        self.getControl(902).setLabel('其它')

        #Catagory
        data = GetHttpData(HOST + 'openapi-wireless/layout/smarttv/channellist?' + IDS)
        data = json.loads(data)
        if data.has_key('status') == False:
            return
        if data['status'] != 'success':
            return

        for item in data['results']:
            listitem = xbmcgui.ListItem(label=item['title'])
            setProperties(listitem, item)
            self.getControl(910).addItem(listitem)

        self.selectedNavigation = 0
        self.getControl(910).getListItem(0).select(True)
        self.setFocusId(910)
        self.urlArgs['cid'] = getProperty(self.getControl(910).getListItem(0), 'cid')

        self.subInited = True


    def initContent(self):
        if self.conInited:
            return

        self.urlArgs['pg'] = '1'
        self.getControl(920).reset()
        self.updateContent()

        self.conInited = True


    def updateContent(self):
        self.showBusy()

        try:
            url = HOST + 'layout/smarttv/item_list?' + IDS
            for k in self.urlArgs:
                url = url + '&' + k + '=' + urllib.quote_plus(self.urlArgs[k])

            data = GetHttpData(url)
            data = json.loads(data)
            if data.has_key('status') == False:
                self.hideBusy()
                return
            if data['status'] != 'success':
                self.hideBusy()
                return

            for item in data['results']:
                if item.has_key('show_thumburl_hd'):
                    listitem = xbmcgui.ListItem(label=item['showname'], label2=item['duration'], thumbnailImage=item['show_thumburl_hd'])
                else:
                    listitem = xbmcgui.ListItem(label=item['showname'], label2=item['duration'], thumbnailImage=item['show_thumburl'])
                setProperties(listitem, item)
                self.getControl(920).addItem(listitem)
        except:
            pass

        self.hideBusy()


    def updateSelection(self):
        if self.getFocusId() == 910:
            if self.selectedNavigation != self.getControl(910).getSelectedPosition():
                #Disable old selection
                self.getControl(910).getListItem(self.selectedNavigation).select(False)
                #Enable new selection
                self.selectedNavigation = self.getControl(910).getSelectedPosition()
                self.getControl(910).getSelectedItem().select(True)


    def onClick( self, controlId ):
        if controlId == 910:
            self.urlArgs['cid'] = getProperty(self.getControl(910).getSelectedItem(), 'cid')

            self.updateSelection()

            self.conInited = False
            self.initContent()
            self.setFocusId(920)
        elif controlId == 903:
            if self.getControl(903).getSelectedItem().isSelected() == False:
                self.getControl(903).getListItem(int(self.urlArgs['ob']) - 1).select(False)
                self.urlArgs['ob'] = str(self.getControl(903).getSelectedPosition() + 1)
                self.getControl(903).getSelectedItem().select(True)
                self.conInited = False
                self.initContent()
                self.setFocusId(920)
        else:
            item = self.getControl(controlId).getSelectedItem()
            if item.getProperty('type') == 'show':
                openWindow('detail', self.session, sdata=item.getProperty('tid'))
            elif item.getProperty('type') == 'video':
                play(item.getProperty('tid'))
            else:
                xbmcgui.Dialog().ok('提示框', '此功能暂未实现，尽请期待')


    def onAction(self, action):
        BaseWindow.onAction(self, action)
        #if action.getId() == ACTION_MOVE_DOWN and self.getFocusId() == 920:
        if self.getFocusId() == 920:
            oldPos = self.getControl(920).getSelectedPosition()
            total = self.getControl(920).size()
            if total - oldPos <= 10:
                pg = int(self.urlArgs['pg']) + 1
                self.urlArgs['pg'] = str(pg)
                self.updateContent()
                self.getControl(920).selectItem(oldPos)


class ResultWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.filterInited = False
        self.typeInited = False
        self.conInited = False
        self.showInited = False
        self.selectAll = True
        self.selectDuration = 0
        self.selectOrder = 0
        self.sdata = kwargs.get('sdata')
        self.urlArgs = {'pz':'20', 'pg':'1', 'seconds':'0', 'seconds_end': '0', 'ob':'0'}
        BaseWindow.__init__(self, args, kwargs)


    def onInit(self):
        BaseWindow.onInit(self)

        self.showBusy()

        try:
            self.initType()
            self.initFilter()
            self.initContent()
            self.initShow()
        except:
            pass

        self.hideBusy()


    def initType(self):
        if self.typeInited:
            return

        listitem = xbmcgui.ListItem(label='节目')
        self.getControl(1304).addItem(listitem)
        listitem = xbmcgui.ListItem(label='视频')
        self.getControl(1304).addItem(listitem)
        self.getControl(1304).getListItem(1).select(True)

        self.typeInited = True


    def initFilter(self):
        if self.filterInited:
            return

        #Title
        self.getControl(1301).setLabel('搜索结果')
        self.getControl(1302).setLabel('时长')
        self.getControl(1303).setLabel('排序')

        self.getControl(1310).reset()
        listitem = xbmcgui.ListItem(label='全部结果')
        self.getControl(1310).addItem(listitem)

        #Catagory
        data = GetHttpData(HOST + 'layout/android3_0/searchfilters?' + IDS)
        data = json.loads(data)
        if data.has_key('status') == False:
            return
        if data['status'] != 'success':
            return

        for item in data['results']['duration']:
            listitem = xbmcgui.ListItem(label=item['title'])
            setProperties(listitem, item)
            self.getControl(1311).addItem(listitem)

        for item in data['results']['order']:
            listitem = xbmcgui.ListItem(label=item['title'])
            setProperties(listitem, item)
            self.getControl(1312).addItem(listitem)

        self.setFocusId(1310)
        self.getControl(1310).getSelectedItem().select(True)
        self.selectAll = True
        self.selectDuration = 0
        self.selectOrder = 0

        self.filterInited = True


    def initContent(self):
        if self.conInited:
            return

        self.urlArgs['pg'] = '1'
        self.getControl(1322).reset()
        if self.getControl(1304).getListItem(0).isSelected():
            self.getControl(1321).setVisible(True)
            self.getControl(1322).setVisible(False)
        else:
            self.getControl(1321).setVisible(False)
            self.getControl(1322).setVisible(True)
        self.updateContent()

        self.conInited = True


    def initShow(self):
        if self.showInited:
            return

        url = HOST + 'layout/smarttv/showsearch?copyright_status=1&video_type=1&keyword=' + urllib.quote_plus(self.sdata) + '&' + IDS

        data = GetHttpData(url)
        data = json.loads(data)
        if data.has_key('status') == False:
            return
        if data['status'] != 'success':
            return

        for item in data['results']:
            if item.has_key('show_vthumburl_hd'):
                listitem = xbmcgui.ListItem(label=item['showname'], thumbnailImage=item['show_vthumburl_hd'])
            else:
                listitem = xbmcgui.ListItem(label=item['showname'], thumbnailImage=item['show_vthumburl'])
            setProperties(listitem, item)
            self.getControl(1321).addItem(listitem)

        self.showInited = True


    def updateContent(self):
        self.showBusy()

        try:
            url = HOST + 'openapi-wireless/videos/search/' + urllib.quote_plus(self.sdata) + '?' + IDS
            for k in self.urlArgs:
                url = url + '&' + k + '=' + urllib.quote_plus(self.urlArgs[k])

            data = GetHttpData(url)
            data = json.loads(data)
            if data.has_key('status') == False:
                self.hideBusy()
                return
            if data['status'] != 'success':
                self.hideBusy()
                return

            for item in data['results']:
                if item.has_key('img_hd'):
                    listitem = xbmcgui.ListItem(label=item['title'], label2=item['duration'], thumbnailImage=item['img_hd'])
                else:
                    listitem = xbmcgui.ListItem(label=item['title'], label2=item['duration'], thumbnailImage=item['img'])
                setProperties(listitem, item)
                self.getControl(1322).addItem(listitem)
        except:
            pass

        self.hideBusy()


    def updateSelection(self, Id):
        if Id == 1310:
            self.getControl(1310).getSelectedItem().select(True)
            self.getControl(1311).getListItem(self.selectDuration).select(False)
            self.getControl(1312).getListItem(self.selectOrder).select(False)
            self.selectAll = True
            self.urlArgs['seconds'] = '0'
            self.urlArgs['seconds_end'] = '0'
            self.urlArgs['ob'] = '0'
        elif Id == 1311:
            self.getControl(1311).getListItem(self.selectDuration).select(False)
            self.selectDuration = self.getControl(1311).getSelectedPosition()
            self.getControl(1311).getListItem(self.selectDuration).select(True)
            if self.selectAll == True:
                self.selectAll = False
                self.getControl(1310).getSelectedItem().select(False)
            value = getProperty(self.getControl(1311).getListItem(self.selectDuration), "value")
            try:
                self.urlArgs['seconds'] = value.split('-')[0]
                self.urlArgs['seconds_end'] = value.split('-')[1]
            except:
                pass
        elif Id == 1312:
            self.getControl(1312).getListItem(self.selectOrder).select(False)
            self.selectOrder = self.getControl(1312).getSelectedPosition()
            self.getControl(1312).getListItem(self.selectOrder).select(True)
            if self.selectAll == True:
                self.selectAll = False
                self.getControl(1310).getSelectedItem().select(False)
            self.urlArgs['ob'] = getProperty(self.getControl(1312).getListItem(self.selectOrder), "value")


    def onClick( self, controlId ):
        if controlId == 1310 or controlId == 1311 or controlId == 1312:

            self.updateSelection(controlId)

            self.conInited = False
            self.initContent()
            self.setFocusId(1320)
        elif controlId == 1304:
            if self.getControl(1304).getSelectedPosition() == 0:
                self.getControl(1304).getListItem(0).select(True)
                self.getControl(1304).getListItem(1).select(False)
            else:
                self.getControl(1304).getListItem(0).select(False)
                self.getControl(1304).getListItem(1).select(True)

            if self.getControl(1304).getListItem(0).isSelected():
                self.getControl(1321).setVisible(True)
                self.getControl(1322).setVisible(False)
            else:
                self.getControl(1321).setVisible(False)
                self.getControl(1322).setVisible(True)
        elif controlId == 1321:
            item = self.getControl(controlId).getSelectedItem()
            openWindow('detail', self.session, sdata=item.getProperty('showid'))
        elif controlId == 1322:
            item = self.getControl(controlId).getSelectedItem()
            play(item.getProperty('videoid'))
        else:
            xbmcgui.Dialog().ok('提示框', '此功能暂未实现，尽请期待')


    def onAction(self, action):
        BaseWindow.onAction(self, action)
        #if action.getId() == ACTION_MOVE_DOWN and self.getFocusId() == 1322:
        if self.getFocusId() == 1322:
            oldPos = self.getControl(1322).getSelectedPosition()
            total = self.getControl(1322).size()
            if total - oldPos <= 10:
                pg = int(self.urlArgs['pg']) + 1
                self.urlArgs['pg'] = str(pg)
                self.updateContent()
                self.getControl(1322).selectItem(oldPos)


class SearchWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.subInited = False
        self.conInited = False
        self.inputs = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        self.keywords = ''
        BaseWindow.__init__(self, args, kwargs)


    def onInit(self):
        BaseWindow.onInit(self)
        self.initSubChannel()
        self.initContent()


    def initSubChannel(self):
        if self.subInited:
            return

        self.getControl(1201).setLabel('中文')
        self.getControl(1202).setLabel('空格')
        self.getControl(1203).setLabel('清空')
        self.getControl(1204).setLabel('退格')
        self.getControl(1205).setLabel('搜索')

        for ch in self.inputs:
            listitem = xbmcgui.ListItem(label=ch)
            self.getControl(1210).addItem(listitem)

        self.subInited = True


    def initContent(self):
        if self.conInited:
            return

        if len(self.keywords) == 0:
            self.getControl(1212).setLabel('大家都在搜:')
            self.getControl(1211).setLabel('[COLOR=grey]输入搜索内容[/COLOR]')
        else:
            self.getControl(1212).setLabel('猜你想搜:')
            self.getControl(1211).setLabel(self.keywords)

        self.getControl(1220).reset()
        self.updateContent()

        self.conInited = True


    def updateContent(self):
        self.showBusy()

        try:
            if len(self.keywords) == 0:
                data = GetHttpData(HOST + 'openapi-wireless/keywords/recommend?' + IDS)
                title_key = 'title'
            else:
                data = GetHttpData(HOST + 'openapi-wireless/keywords/suggest?' + IDS + '&keywords=' + urllib.quote_plus(self.keywords))
                title_key = 'keyword'

            data = json.loads(data)
            if data.has_key('status') == False:
                self.hideBusy()
                return
            if data['status'] != 'success':
                self.hideBusy()
                return

            for item in data['results']:
                listitem = xbmcgui.ListItem(label=item[title_key])
                self.getControl(1220).addItem(listitem)
        except:
            pass

        self.hideBusy()


    def onClick( self, controlId ):
        if controlId == 1210:
            ch = self.inputs[self.getControl(1210).getSelectedPosition()]
            self.keywords = self.keywords + ch
        elif controlId == 1201:
            return
        elif controlId == 1202:
            self.keywords = self.keywords + ' '
        elif controlId == 1203:
            self.keywords = ''
        elif controlId == 1204:
            self.keywords = self.keywords[:-1]
        elif controlId == 1205:
            if len(self.keywords) == 0:
                self.getControl(1211).setLabel('[COLOR=grey]搜索内容不能为空[/COLOR]')
                return
            else:
                openWindow('result', self.session, sdata=self.keywords)
        elif controlId == 1220:
            openWindow('result', self.session, sdata=self.getControl(1220).getSelectedItem().getLabel())
        else:
            xbmcgui.Dialog().ok('提示框', '此功能暂未实现，尽请期待')
            return

        self.conInited = False
        self.initContent()


class FavorWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.subInited = False
        self.conInited = False
        BaseWindow.__init__(self, args, kwargs)


    def onInit(self):
        BaseWindow.onInit(self)
        self.initSubChannel()
        self.initContent()


    def initSubChannel(self):
        if self.subInited:
            return

        #Title
        self.getControl(1001).setImage('icon_my_collect.png')
        self.getControl(1002).setLabel('收藏')

        #Catagory
        listitem = xbmcgui.ListItem(label='节目')
        self.getControl(1010).addItem(listitem)
        listitem = xbmcgui.ListItem(label='视频')
        self.getControl(1010).addItem(listitem)

        self.selectedNavigation = 0
        self.getControl(1010).getListItem(0).select(True)
        self.setFocusId(1010)

        self.subInited = True


    def initContent(self):
        if self.conInited:
            return

        self.getControl(1020).reset()
        if self.selectedNavigation == 0:
            self.updateContent()

        self.conInited = True


    def updateContent(self):
        try:
            ret = eval(cache.get('favor'))
        except:
            ret = None
        if ret == None:
            return
        ret = sorted(ret.values(), lambda y,x: cmp(x['addedTime'], y['addedTime']))
        for item in ret:
            listitem = xbmcgui.ListItem(label=item['title'], thumbnailImage=item['img'])
            setProperties(listitem, item)
            self.getControl(1020).addItem(listitem)


    def updateSelection(self):
        if self.getFocusId() == 1010:
            if self.selectedNavigation != self.getControl(1010).getSelectedPosition():
                #Disable old selection
                self.getControl(1010).getListItem(self.selectedNavigation).select(False)
                #Enable new selection
                self.selectedNavigation = self.getControl(1010).getSelectedPosition()
                self.getControl(1010).getSelectedItem().select(True)


    def onClick( self, controlId ):
        if controlId == 1010:
            self.updateSelection()
            self.conInited = False
            self.initContent()
            if self.getControl(1020).size() > 0:
                self.setFocusId(1020)
        elif controlId == 1020:
            try:
                retOld = cache.get('favor')
            except:
                retOld = None
            showid = self.getControl(1020).getSelectedItem().getProperty('showid')
            openWindow('detail', self.session, sdata=showid)
            try:
                ret = cache.get('favor')
            except:
                ret = None

            if retOld != ret:
                self.conInited = False
                self.initContent()
                self.setFocusId(1020)
        else:
            xbmcgui.Dialog().ok('提示框', '此功能暂未实现，尽请期待')


class HistoryWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.subInited = False
        self.conInited = False
        BaseWindow.__init__(self, args, kwargs)


    def onInit(self):
        BaseWindow.onInit(self)
        self.initSubChannel()
        self.initContent()


    def initSubChannel(self):
        if self.subInited:
            return

        #Title
        self.getControl(1101).setImage('icon_my_history.png')
        self.getControl(1102).setLabel('历史')

        self.subInited = True


    def initContent(self):
        if self.conInited:
            return

        self.getControl(1110).reset()
        self.updateContent()
        self.setFocusId(1110)

        self.conInited = True


    def updateContent(self):
        try:
            ret = eval(cache.get('history'))
        except:
            ret = None
        if ret == None:
            return
        ret = sorted(ret.values(), lambda y,x: cmp(x['addedTime'], y['addedTime']))
        for item in ret:
            listitem = xbmcgui.ListItem(label=item['title'], label2=item['vid'], thumbnailImage=item['logo'])
            self.getControl(1110).addItem(listitem)


    def onClick( self, controlId ):
        try:
            oldret = eval(cache.get('history'))
        except:
            oldret = None
        play(self.getControl(1110).getSelectedItem().getLabel2())
        try:
            ret = eval(cache.get('history'))
        except:
            ret = None

        if oldret != ret:
            self.conInited = False
            self.initContent()
            self.setFocusId(1110)


class DetailWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.inited = False
        self.sdata = kwargs.get('sdata')
        self.pdata = None
        BaseWindow.__init__(self, args, kwargs)


    def onInit(self):
        BaseWindow.onInit(self)
        self.init()


    def init(self):
        if self.inited:
            return

        self.showBusy()

        try:
            data = GetHttpData(HOST + 'layout/smarttv/play/detail?' + IDS + '&id=' + self.sdata)
            data = json.loads(data)
            if data.has_key('status') == False:
                self.hideBusy()
                return
            if data['status'] != 'success':
                self.hideBusy()
                return

            data = data['detail']
            self.pdata = data
            self.getControl(701).setImage(data['img'])
            setLabel(self.getControl(702), data, 'title', '', '', '', '')
            setLabel(self.getControl(703), data, 'reputation', '0.0', '', u'分', '')
            setLabel(self.getControl(704), data, 'showdate', u'未知', u'上映：', '', '')
            setLabel(self.getControl(705), data, 'stripe_bottom', u'未知', u'集数：', '', '')
            setLabel(self.getControl(706), data, 'area', u'未知', u'地区：', '', '/')
            setLabel(self.getControl(707), data, 'genre', u'未知', u'类型：', '', '/')
            setLabel(self.getControl(708), data, 'director', u'未知', u'导演：', '', '/')
            setLabel(self.getControl(709), data, 'performer', u'未知', u'演员：', '', '/')
            self.getControl(710).setLabel('简介：')
            setLabel(self.getControl(711), data, 'desc', '', '', '', '')
            xbmcgui.Window(xbmcgui.getCurrentWindowId()).setProperty('detail_pay', str(data.get('paid', 0)))

            self.getControl(721).setLabel('选集')
            added = True
            try:
                ret = eval(cache.get('favor'))
            except:
                ret = None
            if ret != None:
                if ret.has_key(self.sdata):
                    added = False
            if added:
                self.getControl(722).setLabel('收藏')
            else:
                self.getControl(722).setLabel('已收藏')
            self.getControl(723).setLabel(getNumber(data, 'total_vv'))
            self.getControl(724).setLabel(getNumber(data, 'total_fav'))

            try:
                if data['episode_total'] == '1':
                    #self.getControl(721).setVisible(False)
                    self.getControl(721).setEnabled(False)
            except:
                pass

            self.getControl(740).reset()

            data = GetHttpData(HOST + 'common/shows/relate?' + IDS + '&id=' + self.sdata)
            data = json.loads(data)
            if data.has_key('status') == False:
                self.hideBusy()
                return
            if data['status'] != 'success':
                self.hideBusy()
                return

            for item in data['results']:
                listitem = xbmcgui.ListItem(label=item['showname'], thumbnailImage=item['show_vthumburl'])
                setProperties(listitem, item)
                self.getControl(740).addItem(listitem)
        except:
            pass

        self.hideBusy()

        self.inited = True


    def onClick( self, controlId ):
        if controlId == 740:
            self.sdata = getProperty(self.getControl(740).getSelectedItem(), 'showid')
            self.inited = False
            self.init()
        elif controlId == 720:
            play(self.pdata['videoid'])
        elif controlId == 721:
            openWindow('select', self.session, sdata=self.sdata)
        elif controlId == 722:
            self.changeFavor()
        else:
            xbmcgui.Dialog().ok('提示框', '此功能暂未实现，尽请期待')


    def changeFavor(self):
        try:
            ret = eval(cache.get('favor'))
        except:
            ret = None
        if ret == None:
            self.pdata['addedTime'] = time.time()
            cache.set('favor', repr({self.sdata:  self.pdata}))
            self.getControl(722).setLabel('已收藏')
        elif ret.has_key(self.sdata):
            del(ret[self.sdata])
            cache.set('favor', repr(ret))
            self.getControl(722).setLabel('收藏')
        else:
            self.pdata['addedTime'] = time.time()
            ret[self.sdata] = self.pdata
            cache.set('favor', repr(ret))
            self.getControl(722).setLabel('已收藏')


class SelectWindow(BaseWindow):
    def __init__( self, *args, **kwargs):
        self.inited = False
        self.sdata = kwargs.get('sdata')
        self.pdata = None
        self.selected = 0
        BaseWindow.__init__( self )


    def onInit(self):
        BaseWindow.onInit( self )

        self.showBusy()
        try:
            self.init()
        except:
            pass
        self.hideBusy()

    def init(self):
        if self.inited:
            return

        self.getControl(801).setLabel('剧集:')

        data = GetHttpData(HOST + 'layout/smarttv/shows/' + self.sdata + '/series?' + IDS)
        data = json.loads(data)
        if data.has_key('status') == False:
            return
        if data['status'] != 'success':
            return

        data = data['results']
        data.sort(lambda x,y: cmp(x['video_stage'], y['video_stage']))
        self.pdata = data

        total = len(data)
        for i in range(total, 0, -20):
            start = str(i)
            if i - 19 > 0:
                end = str(i - 19)
            else:
                end = str(1)
            listitem = xbmcgui.ListItem(label=start + '-' + end)
            listitem.setProperty('start', start)
            listitem.setProperty('end', end)
            self.getControl(810).addItem(listitem)

        self.selectRange(0)
        self.setFocusId(820)

        self.inited = True


    def selectRange(self, index):
        self.getControl(810).getListItem(self.selected).select(False)
        item = self.getControl(810).getListItem(index)
        item.select(True)
        self.selected = index

        self.getControl(820).reset()
        start = int(item.getProperty('start'))
        end = int(item.getProperty('end'))

        fromTitle = False
        if len(self.pdata) > 1:
            if self.pdata[0]['title'] != self.pdata[1]['title']:
                lastSpace = 0
                for i in range(1, len(self.pdata[0]['title'])):
                    if self.pdata[0]['title'][:i] != self.pdata[1]['title'][:i]:
                        break
                    if self.pdata[0]['title'][i - 1] == ' ':
                        lastSpace = i
                if lastSpace > 0:
                    trim = self.pdata[0]['title'][:(i-1)]
                else:
                    trim = self.pdata[0]['title'][:lastSpace]
                fromTitle = True
        for i in range(start, end - 1, -1):
            if fromTitle == True:
                listitem = xbmcgui.ListItem(label=self.pdata[i-1]['title'].replace(trim, ''), label2=str(i-1))
            else:
                listitem = xbmcgui.ListItem(label=str(self.pdata[i-1]['video_stage']), label2=str(i-1))
            self.getControl(820).addItem(listitem)


    def onClick( self, controlId ):
        BaseWindow.onClick(self, controlId)
        if controlId == 810:
            self.selectRange(self.getControl(810).getSelectedPosition())
        else:
            play(self.pdata[int(self.getControl(820).getSelectedItem().getLabel2())]['videoid'])


    def onAction(self, action):
        BaseWindow.onAction(self, action)
        if self.getFocusId() == 810:
            if action.getId() == ACTION_MOVE_LEFT or action.getId() == ACTION_MOVE_RIGHT:
                self.selectRange(self.getControl(810).getSelectedPosition())


class VstSession:
    def __init__(self,window=None):
        self.window = window

    def removeCRLF(self,text):
        return " ".join(text.split())

    def makeAscii(self,name):
        return name.encode('ascii','replace')

    def closeWindow(self):
        self.window.doClose()

    def clearSetting(self,key):
        __addon__.setSetting(key,'')

    def setSetting(self,key,value):
        __addon__.setSetting(key,value and ENCODE(value) or '')

    def getSetting(self,key,default=None):
        setting = __addon__.getSetting(key)
        if not setting: return default
        if type(default) == type(0):
            return int(float(setting))
        elif isinstance(default,bool):
            return setting == 'true'
        return setting

class youkuDecoder:
    def __init__( self ):
        return

    def getFileIDMixString(self,seed):
        mixed = []
        source = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\:._-1234567890")
        seed = float(seed)
        for i in range(len(source)):
            seed = (seed * 211 + 30031 ) % 65536
            index = math.floor(seed /65536 *len(source))
            mixed.append(source[int(index)])
            source.remove(source[int(index)])
        return mixed

    def getFileId(self,fileId,seed):
        mixed = self.getFileIDMixString(seed)
        ids = fileId.split('*')
        realId = []
        for i in range(0,len(ids)-1):
            realId.append(mixed[int(ids[i])])
        return ''.join(realId)

    def trans_e(self, a, c):
        b = range(256)
        f = 0
        result = ''
        h = 0
        while h < 256:
            f = (f + b[h] + ord(a[h % len(a)])) % 256
            b[h], b[f] = b[f], b[h]
            h += 1
        q = f = h = 0
        while q < len(c):
            h = (h + 1) % 256
            f = (f + b[h]) % 256
            b[h], b[f] = b[f], b[h]
            if isinstance(c[q], int):
                result += chr(c[q] ^ b[(b[h] + b[f]) % 256])
            else:
                result += chr(ord(c[q]) ^ b[(b[h] + b[f]) % 256])
            q += 1
        return result

    def trans_f(self, a, c):
        """
        :argument a: list
        :param c:
        :return:
        """
        b = []
        for f in range(len(a)):
            i = ord(a[f][0]) - 97 if "a" <= a[f] <= "z" else int(a[f]) + 26
            e = 0
            while e < 36:
                if c[e] == i:
                    i = e
                    break
                e += 1
            v = i - 26 if i > 25 else chr(i + 97)
            b.append(str(v))
        return ''.join(b)

    f_code_1 = 'becaf9be'
    f_code_2 = 'bf7e5f01'

    def _calc_ep(self, sid, fileId, token):
        ep = self.trans_e(self.f_code_2, '%s_%s_%s' % (sid, fileId, token))
        return base64.b64encode(ep)

    def _calc_ep2(self, vid, ep):
        e_code = self.trans_e(self.f_code_1, base64.b64decode(ep))
        sid, token = e_code.split('_')
        new_ep = self.trans_e(self.f_code_2, '%s_%s_%s' % (sid, vid, token))
        return base64.b64encode(new_ep), token, sid

    def get_sid(self, ep):
        e_code = self.trans_e(self.f_code_1, base64.b64decode(ep))
        return e_code.split('_')

    def generate_ep(self, no, fileid, sid, token):
        ep = urllib.quote(self._calc_ep(sid, fileid, token).encode('latin1'),
            safe="~()*!.'"
        )
        return ep

def getNumber(data, k):
    try:
        s = data[k]
        s = s.replace(',', '')
        n = float(s)
        if(n > 100000000):
            f = n / 100000000
            return str("%.1f"%f) + u'亿次'
        elif(n > 10000):
            f = n / 10000
            return str("%.1f"%f) + u'万次'
        else:
            return str(n)
    except:
        return '0次'


def setLabel(c, data, k, default, pre, app, sep):
    try:
        label = data[k]
        c.setLabel(pre + sep.join(label) + app)
    except:
        try:
            c.setLabel(pre + str(sep.join(label)) + app)
        except:
            try:
                c.setLabel(pre + unicode(sep.join(label)) + app)
            except:
                c.setLabel(pre + default + app)


def setProperties(listitem, item):
    for k in item:
        try:
            listitem.setProperty(k, item[k])
        except:
            try:
                listitem.setProperty(k, str(item[k]))
            except:
                listitem.setProperty(k, unicode(item[k]))


def getProperty(item, key):
    try:
        value = item.getProperty(key)
    except:
        value = ''

    return value


def play(vid, playContinue=False):
    readSettings()
    playid = vid

    try:
        ret = eval(cache.get('history'))
    except:
        ret = {}

    if ret.has_key(vid):
        history = ret[vid]
    else:
        history = {}
    offset = 0
    startpos = 0
    try:
        resume = eval(cache.get(vid))
        offset = resume['offset']
        startpos = resume['startpos']
    except:
        pass

    if (offset or startpos) and playContinue == False:
        choice = openWindow('confirm')
        if choice == 1:
            try:
                cache.delete(vid)
            except:
                pass
        elif choice == -1:
            return

    xbmc.executebuiltin("ActivateWindow(busydialog)")
    try:
        movinfo = json.loads(GetHttpData('http://play.youku.com/play/get.json?vid=%s&ct=12' % playid).replace('\r\n',''))
        movdat = movinfo['data']
        movinfo = json.loads(GetHttpData('http://play.youku.com/play/get.json?vid=%s&ct=10' % playid).replace('\r\n',''))
        movdat1 = movinfo['data']
        assert 'stream' in movdat
        assert 'stream' in movdat1
    except:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        xbmcgui.Dialog().ok('提示框', '解析地址异常，无法播放')
        return

    #Select resolution.
    stream = {}
    resolution = ''
    language_code = settings_data['language_code'][settings['language']]
    try:
        for i in range(settings['resolution'], len(settings_data['resolution'])):
            for t in settings_data['resolution_type'][i]:
                for s in movdat1['stream'][::-1]:
                    if settings['language'] == 0 or language_code == s['audio_lang'] or s['audio_lang'] == 'default':
                        if t == s['stream_type']:
                            stream = s
                            resolution = settings_data['resolution_type'][i][0]
                            break
                if stream.has_key('stream_type'):
                    break
            if stream.has_key('stream_type'):
                break
    except:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        xbmcgui.Dialog().ok('提示框', '解析地址异常，无法播放')
        return

    if not stream.has_key('stream_type'):
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        xbmcgui.Dialog().ok('提示框', '解析地址异常，无法播放')
        return


    #Calculate the URLs
    try:
        urls = []
        segs = stream['segs']

        oip = movdat['security']['ip']
        ep = movdat['security']['encrypt_string']
        sid, token = youkuDecoder().get_sid(ep)

        for no in range(len(segs)):
            k = segs[no]['key']
            assert k != -1
            fileid = stream['segs'][no]['fileid']
            ep = youkuDecoder().generate_ep(no, fileid, sid, token)
            q = urllib.urlencode(dict(
                ctype = 12,
                ev    = 1,
                K     = k,
                ep    = urllib.unquote(ep),
                oip   = oip,
                token = token,
                yxon  = 1
            ))
            u = 'http://k.youku.com/player/getFlvPath/sid/{sid}_00/st/{container}/fileid/{fileid}?{q}'.format(
                    sid       = sid,
                    container = resolution_map[resolution],
                    fileid    = fileid,
                    q         = q
            )
            urls += [i['server'] for i in json.loads(GetHttpData(u))]

        playlist = xbmc.PlayList(1)
        playlist.clear()

        if settings_data['play_type'][settings['play']] == 'concatenate' and resolution_map[resolution] == 'flv':
            vc.start(urls)
            port = vc.get_port()
            assert(port != 0)
            listitem=xbmcgui.ListItem(movdat['video']['title'])
            listitem.setInfo(type="Video", infoLabels={"Title":movdat['video']['title']})
            playlist.add('http://127.0.0.1:%d' % port, listitem)
        elif settings_data['play_type'][settings['play']] == 'list':
            for i in range(len(urls)):
                title =movdat['video']['title'] + u" - 第"+str(i+1)+"/"+str(len(urls)) + u"节"
                listitem=xbmcgui.ListItem(title)
                listitem.setInfo(type="Video",infoLabels={"Title":title})
                playlist.add(urls[i], listitem)
        else:
            playurl = 'stack://' + ' , '.join(urls)
            listitem=xbmcgui.ListItem(movdat['video']['title'])
            listitem.setInfo(type="Video", infoLabels={"Title":movdat['video']['title']})
            playlist.add(playurl, listitem)
    except:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        xbmcgui.Dialog().ok('提示框', '解析地址异常，无法播放')
        return



    xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    history['title'] = movdat['video']['title']
    history['vid'] = vid
    history['logo'] = movdat['video']['logo']

    cache.set('currentVID', vid)
    if True:
        player.play(playlist, arg=vid)
    else:
        player.play(playlist, listitem, arg=vid)

    #Add to history
    history['addedTime'] = time.time()
    ret[vid] = history
    cache.set('history', repr(ret))

def openWindow(window_name,session=None,**kwargs):
    windowFile = '%s.xml' % window_name
    if window_name == 'main':
        w = MainWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'channel':
        w = ChannelWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'detail':
        w = DetailWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'select':
        w = SelectWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'other':
        w = OtherWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'favor':
        w = FavorWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'history':
        w = HistoryWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'search':
        w = SearchWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'result':
        w = ResultWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'top':
        w = TopWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'mysettings':
        w = SettingsWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    elif window_name == 'filter':
        w = FilterWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
        ret = w.select()
        del w
        return ret
    elif window_name == 'confirm':
        w = ConfirmWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
        ret = w.select()
        del w
        return ret
    else:
        w = BaseWindow(windowFile , __cwd__, "Default",session=session,**kwargs)
    w.doModal()
    del w


def GetHttpData(url):
    log('Frech: ' + url)
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) {0}{1}'.
                       format('AppleWebKit/537.36 (KHTML, like Gecko) ',
                              'Chrome/28.0.1500.71 Safari/537.36'))
        req.add_header('Accept-encoding', 'gzip')
        if (url.find('play.youku.com') != -1):
            req.add_header('referer', 'http://static.youku.com')
        response = urllib2.urlopen(req)
        httpdata = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        response.close()
        match = re.compile('encodingt=(.+?)"').findall(httpdata)
        if len(match)<=0:
            match = re.compile('meta charset="(.+?)"').findall(httpdata)
        if len(match)>0:
            charset = match[0].lower()
            if (charset != 'utf-8') and (charset != 'utf8'):
                httpdata = unicode(httpdata, charset).encode('utf8')
    except:
        if xbmcgui.Dialog().yesno('错误', '网络超时，是否继续？'):
            return GetHttpData(url)
        log('Frech fail')
        httpdata = '{"status": "Fail"}'

    return httpdata


def registerHotKey(key='F12'):
    path = xbmc.translatePath('special://userdata/keymaps')
    keymap = os.path.join(path, 'youkutv.xml')
    if os.path.exists(keymap):
        fp = open(keymap, 'r')
        if '<' + key + '>' in fp.read():
            fp.close()
            return
    fp = open(keymap, 'w')
    fp.write(r'<?xml version="1.0" encoding="UTF-8"?><keymap><global><keyboard><%s>RunScript(%s, openSetting)</%s></keyboard><remote><mytv>RunScript(%s, openSetting)</mytv></remote></global></keymap>' % (key, __addonid__, key, __addonid__))
    fp.close()
    xbmc.executebuiltin('Action(reloadkeymaps)')


def log(msg):
    print ('[YouKu TV]%s' % msg)


def readSettings():
    try:
        settings['resolution'] = int(__addon__.getSetting('resolution'))
        settings['language'] = int(__addon__.getSetting('language'))
        settings['play'] = int(__addon__.getSetting('play'))
        registerHotKey()
    except:
        __addon__.openSettings()
        readSettings()


def writeSettings():
    __addon__.setSetting('resolution', str(settings['resolution']))
    __addon__.setSetting('language', str(settings['language']))
    __addon__.setSetting('play', str(settings['play']))


def clearHistory():
    cache.set('history', repr({}))


def clearFavor():
    cache.set('favor', repr({}))


readSettings()
try:
    if sys.argv[1] == 'clearHistory':
        clearHistory()
    elif sys.argv[1] == 'clearFavor':
        clearFavor()
    elif sys.argv[1] == 'openSetting':
        openWindow('mysettings')
except:
    if __name__ == '__main__':
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('Cookie', '__ysuid={0}'.format(time.time()))]
        urllib2.install_opener(opener)
        openWindow('main')
