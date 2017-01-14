#coding=utf-8
from xbmcswift2 import Plugin, xbmc, xbmcgui
import resources.lib.bilibili as bilibili


plugin = Plugin()

@plugin.route('/play/<cid>')
def play(cid):
    urls = bilibili.get_video_urls(cid)
    playlist = xbmc.PlayList(1)
    playlist.clear()
    i = 1
    for url in urls:
        list_item = xbmcgui.ListItem(u'播放')
        list_item.setInfo(type='video', infoLabels={"Title": "第"+str(i)+"/"+str(len(urls))+" 节"})
        playlist.add(url, listitem=list_item)
        i += 1
    plugin.set_resolved_url(playlist)

@plugin.route('/av_list/<aid>')
def av_list(aid):
    items = [{
        'label': item['title'], 
        'path': plugin.url_for('play', cid = item['cid']), 
        'is_playable': True,
        } for item in bilibili.get_av_list(aid)]
    return items 

@plugin.route('/search/')
def search():
    return []

@plugin.route('/mine/')
def mine():
    return []

@plugin.route('/top/')
def top():
    items = [{
        'label': item['label'], 
        'path': plugin.url_for('top_zone', zone = item['zone'])
        } for item in bilibili.get_top()]
    return items

@plugin.route('/top/<zone>/')
def top_zone(zone):
    items = [{
        'label': item['title'], 
        'path': plugin.url_for('av_list', aid = item['aid'])
        } for item in bilibili.get_top_list(zone)]
    return items 

@plugin.route('/timeline/')
def timeline():
    return []

@plugin.route('/category/')
def category():
    items = [{
        'label': item['label'], 
        'path': plugin.url_for('category_zone', zone = item['zone'])
        } for item in bilibili.get_category()]
    return items

@plugin.route('/category/<zone>/')
def category_zone(zone):
    return []

@plugin.route('/')
def root():
    items = [
        {'label': u'搜索', 'path': plugin.url_for('search')},
        {'label': u'我的', 'path': plugin.url_for('mine')},
        {'label': u'排行榜', 'path': plugin.url_for('top')},
        {'label': u'分类', 'path': plugin.url_for('category')},
        {'label': u'放送表', 'path': plugin.url_for('timeline')},
    ]
    return items


if __name__ == '__main__':
    plugin.run()
