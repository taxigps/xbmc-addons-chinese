#coding=utf-8
from xbmcswift2 import Plugin, xbmc, xbmcgui
from resources.lib.bilibili import Bilibili
try:
    from resources.lib.login_dialog import LoginDialog
except:
    #Debug for xbmcswift2 run from cli
    pass


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

@plugin.route('/play/<aid>')
def play(aid):
    items = bilibili.get_av_list(aid)
    select = 0
    if len(items) > 1:
        select = xbmcgui.Dialog().select(u'选择播放文件', [item['pagename'] for item in items])
        if select < 0:
            return
    cid = items[select]['cid']
    urls = bilibili.get_video_urls(cid)
    print urls
    if (len(urls) > 1):
        plugin.set_resolved_url('stack://' + ' , '.join(urls))
    else:
        plugin.set_resolved_url(urls[0])

@plugin.route('/search/')
def search():
    return []

@plugin.route('/dynamic/<page>')
def dynamic(page):
    items = previous_page('dynamic', page)
    items = []
    items += [{
        'label': item['addition']['title'], 
        'path': plugin.url_for('play', aid = item['addition']['aid']),
        'thumbnail': item['addition']['pic'],
        'info': ('video ', {'plot': 'test'}),
        'is_playable': True,
        } for item in bilibili.get_dynamic()]
    items += next_page('dynamic', page)
    return items

@plugin.route('/fav_box/')
def fav_box():
    items = [{
        'label': item['name'], 
        'path': plugin.url_for('fav', fav_box = item['fav_box'])
        } for item in bilibili.get_fav_box()]
    if len(items) == 1:
        plugin.redirect(items[0]['path'])
    else:
        return items

@plugin.route('/bangumi/')
def bangumi():
    return []

@plugin.route('/fav/<fav_box>/')
def fav(fav_box):
    items = [{
        'label': item['title'], 
        'path': plugin.url_for('play', aid = item['aid']),
        'is_playable': True,
        } for item in bilibili.get_fav(fav_box)]
    return items

@plugin.route('/login/')
def login():
    if bilibili.is_login == False:
        username=plugin.addon.getSetting('username')
        password=plugin.addon.getSetting('password')
        if username=='' or password=='':
            plugin.notify('请设置用户名密码', delay=2000)
            plugin.addon.openSettings()
            username=plugin.addon.getSetting('username')
            password=plugin.addon.getSetting('password')
            if username=='' or password=='':
                plugin.notify('用户名或密码为空', delay=2000)
                return
        captcha = LoginDialog(captcha = bilibili.get_captcha()).get()
        if bilibili.login(username, password, captcha) == True:
            plugin.notify('登陆成功', delay=2000)
        else:
            plugin.notify('登陆失败', delay=2000)

@plugin.route('/logout/')
def logout():
    bilibili.logout()

@plugin.route('/history/')
def history():
    return []

@plugin.route('/timeline/')
def timeline():
    return []

@plugin.route('/category/')
def category():
    items = [{
        'label': item['title'], 
        'path': plugin.url_for('category_order', tid = item['tid'])
        } for item in bilibili.get_category()]
    return items

@plugin.route('/category_order/<tid>')
def category_order(tid):
    items = [{
        'label': item['title'], 
        'path': plugin.url_for('category_list', page = '1', order = item['value'], tid = tid, days = item['days'])
        } for item in bilibili.get_order()]
    return items

@plugin.route('/category_list/<page>/<order>/<tid>/<days>/')
def category_list(order, tid, page, days):
    items = previous_page('category_list', page, order = order, tid = tid, days = days)
    items = []
    items += [{
        'label': item['title'], 
        'path': plugin.url_for('play', aid = item['aid']),
        'thumbnail': item['pic'],
        'is_playable': True,
        } for item in bilibili.get_category_list(tid = tid, order = order, page = page, days = days)]
    items += next_page('category_list', page, order = order, tid = tid, days = days)
    return items

@plugin.route('/')
def root():
    items = [
        {'label': u'搜索(暂不支持)', 'path': plugin.url_for('search')},
        {'label': u'放送表(暂不支持)', 'path': plugin.url_for('timeline')},
        {'label': u'分类', 'path': plugin.url_for('category')},
    ]
    if bilibili.is_login:
        items += [
            {'label': u'我的动态', 'path': plugin.url_for('dynamic', page = '1')},
            {'label': u'我的收藏', 'path': plugin.url_for('fav_box')},
            {'label': u'我的追番(暂不支持)', 'path': plugin.url_for('bangumi')},
            {'label': u'我的历史(暂不支持)', 'path': plugin.url_for('history')},
            {'label': u'退出登陆', 'path': plugin.url_for('logout')},
            ]
    else:
        items += [
            {'label': u'登陆账号', 'path': plugin.url_for('login')},
            ]
    return items


if __name__ == '__main__':
    plugin.run()
