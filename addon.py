#coding=utf-8
from xbmcswift2 import Plugin, xbmc, xbmcgui
from resources.lib.bilibili import Bilibili


plugin = Plugin()
bilibili = Bilibili()

def previous_page(endpoint, page, **kwargs):
    if int(page) > 1:
        page = str(int(page) - 1)
        return [{'label': u'第{0}页'.format(page), 'path': plugin.url_for(endpoint, page = page, **kwargs)}]
    else:
        return []

def next_page(endpoint, page, **kwargs):
    page = str(int(page) + 1)
    return [{'label': u'第{0}页'.format(page), 'path': plugin.url_for(endpoint, page = page, **kwargs)}]

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

@plugin.route('/timeline/')
def timeline():
    return []

@plugin.route('/category/<order>/<days>')
def category(order, days):
    items = [{
        'label': item['title'], 
        'path': plugin.url_for('category_list', page = '1', order = order, tid = item['tid'], days = days)
        } for item in bilibili.get_category()]
    return items

@plugin.route('/category_list/<page>/<order>/<tid>/<days>/')
def category_list(order, tid, page, days):
    items = previous_page('category_list', page, order = order, tid = tid, days = days)
    items += [{
        'label': item['title'], 
        'path': plugin.url_for('av_list', aid = item['aid']),
        'is_playable': True,
        } for item in bilibili.get_category_list(tid = tid, order = order, page = page, days = days)]
    items += next_page('category_list', page, order = order, tid = tid, days = days)
    return items

@plugin.route('/')
def root():
    items = [
        {'label': u'搜索(暂不支持)', 'path': plugin.url_for('search')},
        {'label': u'我的(暂不支持)', 'path': plugin.url_for('mine')},
        {'label': u'放送表(暂不支持)', 'path': plugin.url_for('timeline')},
    ]
    items += [{
        'label': item['title'],
        'path': plugin.url_for('category', order = item['value'], days = item['days'])
        } for item in bilibili.get_order()]
    return items


if __name__ == '__main__':
    plugin.run()
