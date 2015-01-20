#coding: utf8
import tempfile
from xbmcswift2 import Plugin, xbmcgui, xbmc
from resources.lib.bilibili import Bili
from resources.lib.config import TEMP_DIR
from resources.lib.subtitle import subtitle_offset

plugin = Plugin()
bili = Bili()

def get_tmp_dir():
    if len(TEMP_DIR) != 0:
        return TEMP_DIR
    try:
        return tempfile.gettempdir()
    except:
        return TEMP_DIR

def _print_info(info):
    print '[BiliAddon]: ' + info

class BiliPlayer(xbmc.Player):
    def __init__(self):
        self.subtitle = ""
        self.show_subtitle = False

    def setSubtitle(self, subtitle):
        if len(subtitle) > 0:
            self.show_subtitle = True
        else:
            self.show_subtitle = False
        self.subtitle = subtitle

    def onPlayBackStarted(self):
        time = float(self.getTime())
        if self.show_subtitle:
            _print_info(self.subtitle)
            if time > 1:
                _print_info('offset!')
                self.setSubtitles(subtitle_offset(self.subtitle, -time))
            else:
                _print_info('no offset!')
                self.setSubtitles(self.subtitle)
        else:
            _print_info('No subtitle')
            self.showSubtitles(False)

# 分段播放
def _play_video_by_list(urls_info, show_comments='0'):
    _print_info('Play without subtitle')
    playlist = xbmc.PlayList(1)
    playlist.clear()
    i = 1
    _print_info(str(len(urls_info[0])) + ' parts found!')
    player = BiliPlayer()
    for url in urls_info[0]:
        list_item = xbmcgui.ListItem(u'播放')
        list_item.setInfo(type='video', infoLabels={"Title": "第"+str(i)+"/"+str(len(urls_info[0]))+" 节"})
        i += 1
        playlist.add(url, listitem=list_item)
    player.showSubtitles(False)
    player.show_subtitle = False
    player.play(playlist)
    #if show_comments == '1':
        #xbmc.Player().setSubtitles(get_tmp_dir() + '/' + urls_info[1])

# 播放视频
def _play_video(urls_info, show_comments='1'):
    playlist = xbmc.PlayList(1)
    playlist.clear()
    list_item = xbmcgui.ListItem(u'播放')
    list_item.setInfo(type='video', infoLabels={"Title": u"播放"})
    _print_info(str(len(urls_info[0])) + ' parts found')
    stack_url = 'stack://' + ' , '.join(urls_info[0])
    playlist.add(stack_url, list_item)
    player = BiliPlayer()
    if show_comments == '1':
        _print_info('Play with subtitle')
        player.setSubtitle(get_tmp_dir() + '/' + urls_info[1])
    else:
        _print_info('Play without subtitle')
        player.showSubtitles(False)
        player.show_subtitle = False
    player.play(playlist)
    #while(not xbmc.abortRequested):
    xbmc.sleep(100)


# 首页
@plugin.route('/')
def index():
    dir_list = [
        {
            'label': name,
            'path': plugin.url_for('show_target_items', target=name)
        } for name in bili.ROOT_PATH ]
    return dir_list

# 总列表页
@plugin.route('/items/<target>/')
def show_target_items(target):
    dir_list = [
        {
            'label': item['name'],
            'path': plugin.url_for('show_category_items', target=target, category=item['eng_name'])
        } for item in bili.get_items(target) ]
    return dir_list

# 分类列表页
@plugin.route('/items/<target>/<category>/')
def show_category_items(target, category):
    if target == 'RSS':
        dir_list = [ {
            'label': item['title'],
            'path': plugin.url_for('show_video_list', url=item['link'])
        } for item in bili.get_items(target, category) ]
    elif target == 'Index':
        dir_list = [ {
            'label': x,
            'path': plugin.url_for('show_index_items', target=target, category=category, display_type=x)
        } for x in bili.LIST_TYPE]
    else:
        dir_list = []
    return dir_list

@plugin.route('/items/<target>/<category>/<display_type>/')
def show_index_items(target, category, display_type):
    if display_type == 'Month':
         dir_list = [ {
            'label': item['title'],
            'path': plugin.url_for('show_items_by_ident', target=target, category=category, display_type=display_type, ident=item['link'])
        } for item in bili.get_index_items(category, 1) ]
    else:
         dir_list = [ {
            'label': item['title'],
            'path': plugin.url_for('show_items_by_ident', target=target, category=category, display_type=display_type, ident=item['link'])
        } for item in bili.get_index_items(category, 0) ]
    return dir_list

# 索引的列表页
@plugin.route('/items/<target>/<category>/<display_type>/<ident>/')
def show_items_by_ident(target, category, display_type, ident):
    display_type_int = 1 if display_type == 'Month' else 0
    dir_list = [ {
        'label': item['title'],
        'path': plugin.url_for('show_video_list', url=item['link'])
    } for item in bili.get_video_by_ident(category, display_type_int, ident)]
    return dir_list

# 视频列表页
@plugin.route('/videos/<url>/')
def show_video_list(url):
    dir_list = []
    for item in bili.get_video_list(url):
        try:
            dir_list.append({
                'label': item[0],
                'path': plugin.url_for('play_video', url=item[1], by_list = 0, show_comments=1),
            })
        except:
            dir_list.append({
                'label': item[0].decode('utf8'),
                'path': plugin.url_for('play_video', url=item[1], by_list = 0, show_comments=1),
            })
        try:
            dir_list.append({
                'label': item[0] + u'(无弹幕)',
                'path': plugin.url_for('play_video', url=item[1], by_list = 0, show_comments=0),
            })
        except:
            dir_list.append({
                'label': item[0].decode('utf8') + u'(无弹幕)',
                'path': plugin.url_for('play_video', url=item[1], by_list = 0, show_comments=0),
            })
        try:
            dir_list.append({
                'label': item[0] + u'(分段无弹幕)',
                'path': plugin.url_for('play_video', url=item[1], by_list = 1, show_comments=0),
            })
        except:
            dir_list.append({
                'label': item[0].decode('utf8') + u'(分段无弹幕)',
                'path': plugin.url_for('play_video', url=item[1], by_list = 1, show_comments=0),
            })

    return dir_list

# 播放视频
@plugin.route('/video/<url>/<by_list>/<show_comments>/')
def play_video(url, by_list, show_comments):
    if show_comments == '1':
        _print_info('Fetch subtitle')
        playlist = bili.get_video_urls(url, True)
    else:
        _print_info('Don\'t fetch subtitle')
        playlist = bili.get_video_urls(url, False)
    n = len(playlist[0])
    _print_info('%d videos found' % n)
    if n > 0:
        if by_list == '1':
            _play_video_by_list(playlist, show_comments)
        else:
            _play_video(playlist, show_comments)

if __name__ == '__main__':
    plugin.run()
