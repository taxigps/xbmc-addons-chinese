#coding=utf-8
from xbmcswift2 import Plugin, xbmc, xbmcgui
import resources.lib.bilibili as bilibili


plugin = Plugin()

@plugin.route('/play/<cid>')
def play(cid):
    urls = bilibili.get_video_urls(cid)
    if (len(urls) > 1):
        plugin.set_resolved_url('stack://' + ' , '.join(urls))
    else:
        plugin.set_resolved_url(urls[0])

@plugin.route('/av_list/<aid>')
def av_list(aid):
    items = bilibili.get_av_list(aid)
    select = 0
    if len(items) > 1:
        select = xbmcgui.Dialog().select(u'选择播放文件', [item['title'] for item in items])
        if select < 0:
            return
    plugin.redirect(plugin.url_for('play', cid = items[select]['cid']))

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
        'path': plugin.url_for('av_list', aid = item['aid']),
        'is_playable': True,
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
