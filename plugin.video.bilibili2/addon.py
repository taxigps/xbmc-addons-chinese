#coding=utf-8
from xbmcswift2 import Plugin, xbmc, xbmcgui
from resources.lib.bilibili import Bilibili
import time
import string, random, os

try:
    from resources.lib.login_dialog import LoginDialog
except:
    #Debug for xbmcswift2 run from cli
    pass


plugin = Plugin()
bilibili = Bilibili()
tempdir = xbmc.translatePath('special://home/temp')

def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        page = str(int(page) - 1)
        return [{'label': u'上一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page = page, **kwargs)}]
    else:
        return []

def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        page = str(int(page) + 1)
        return [{'label': u'下一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page = page, **kwargs)}]
    else:
        return []

def get_av_item(aid, **kwargs):
    result = bilibili.get_av_list(aid)
    item = dict(**kwargs)
    if len(result) == 1:
        item['is_playable'] = True
        item['path'] = plugin.url_for('play', cid = result[0]['cid'])
    else:
        item['path'] = plugin.url_for('list_video', aid = aid)
    return item

@plugin.route('/play/<cid>/')
def play(cid):
    urls = bilibili.get_video_urls(cid)
    for i in range(len(urls)):
        urls[i] = urls[i] + '|Referer=http://www.bilibili.com/'
    if (len(urls) > 1):
        plugin.set_resolved_url('stack://' + ' , '.join(urls))
    else:
        plugin.set_resolved_url(urls[0])

@plugin.route('/list_video/<aid>/')
def list_video(aid):
    plugin.set_content('videos')
    result = bilibili.get_av_list(aid)
    items = []
    for  item in result:
        items.append({
            'label': item['pagename'], 
            'path': plugin.url_for('play', cid = item['cid']),
            'is_playable': True,
            })
    return items

@plugin.route('/search/')
def search():
    return []

@plugin.route('/dynamic/<page>/')
def dynamic(page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_dynamic(page)
    items = previous_page('dynamic', page, total_page)
    items = []
    for item in result:
        duration = 0
        for t in item['addition']['duration'].split(':'):
            duration = duration * 60 + int(t)
        info = {
            'genre': item['addition']['typename'],
            'writer': item['addition']['author'],
            'plot': item['addition']['description'],
            'duration': duration,
            }
        try:
            info['year'] = int(item['addition']['create'][:4])
        except:
            pass
        items.append(get_av_item(item['addition']['aid'], label = item['addition']['title'], thumbnail = item['addition']['pic'], info = info))

    items += next_page('dynamic', page, total_page)
    return items

@plugin.route('/fav_box/')
def fav_box():
    items = [{
        'label': item['name'], 
        'path': plugin.url_for('fav', fav_box = item['fav_box'], page = '1')
        } for item in bilibili.get_fav_box()]
    if len(items) == 1:
        plugin.redirect(items[0]['path'])
    else:
        return items

@plugin.route('/fav/<fav_box>/<page>/')
def fav(fav_box, page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_fav(fav_box, page)
    items = previous_page('fav', page, total_page, fav_box = fav_box)
    items = []
    for item in result:
        info = {
            'genre': item['tname'],
            'writer': item['owner']['name'],
            'plot': item['desc'],
            'duration': item['duration']
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['ctime'])))
        except:
            pass
        items.append(get_av_item( item['aid'], label = item['title'], thumbnail = item['pic'], info = info))
    items += next_page('fav', page, total_page, fav_box = fav_box)
    return items

@plugin.route('/season/<season_id>/')
def season(season_id):
    plugin.set_content('videos')
    result = bilibili.get_bangumi_detail(season_id)
    items = []
    bangumi_info = {
        'genre': '|'.join([tag['tag_name'] for tag in result['tags']]),
        'episode': len(result['episodes']),
        'castandrole': [u'{}|{}'.format(actor['actor'], actor['role']) for actor in result['actor']],
        'director': result['staff'],
        'plot': result['evaluate'],
        }
    for item in result['episodes']:
        info = dict(bangumi_info)
        try:
            info['year'] = int(item['update_time'][:4])
        except:
            pass
        title = u'【第{}话】'.format(item['index'])
        title += item['index_title']
        if item.get('is_new', '0') == '1':
            title += u'【新】'
        items.append(get_av_item(item['av_id'], label = title, thumbnail = item['cover'], info = info))
    return items

@plugin.route('/bangumi_chase/<page>/')
def bangumi_chase(page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_bangumi_chase(page)
    items = []
    for item in result:
        info = {
            'plot': item['brief'],  
            }
        title = item['title']
        if item['is_finish'] == 0:
            title += u'【更新至第{0}集】'.format(item['newest_ep_index'])
        else:
            title += u'【已完结】'
        items.append({
            'label': title,
            'path': plugin.url_for('season', season_id = item['season_id']),
            'thumbnail': item['cover'],
            'info': info,
            })
    items += next_page('bangumi_chase', page, total_page)
    return items

@plugin.route('/attention_video/<mid>/<tid>/<page>/')
def attention_video(mid, tid, page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_attention_video(mid, tid, page)
    items = []
    for item in result['vlist']:
        duration = 0
        for t in item['length'].split(':'):
            duration = duration * 60 + int(t)
        info = {
            'writer': item['author'],
            'plot': item['description'],
            'duration': duration,
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['created'])))
        except:
            pass
        try:
            info['genre'] = bilibili.get_category_name(item['typeid'])
        except:
            pass
        items.append(get_av_item(item['aid'], label = item['title'], thumbnail = item['pic'], info = info))
    items += next_page('attention_video', page, total_page, mid = mid, tid = tid)
    return items 

@plugin.route('/attention_channel_list/<mid>/<cid>/<page>/')
def attention_channel_list(mid, cid, page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_attention_channel_list(mid, cid, page)
    items = []
    for item in result:
        info = {
            'genre': item['info']['tname'],
            'plot': item['info']['desc'],
            'duration': item['info']['duration'],
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['info']['ctime'])))
        except:
            pass
        items.append(get_av_item(item['info']['aid'], label = item['info']['title'], thumbnail = item['info']['pic'], info = info))
    items += next_page('attention_channel_list', page, total_page, mid = mid, cid = cid)
    return items 

@plugin.route('/attention_channel/<mid>/')
def attention_channel(mid):
    result = bilibili.get_attention_channel(mid)
    items = []
    for item in result:
        title = u'{} ({}个视频) ({}更新)'.format(item['name'], str(item['count']), item['modify_time'][:10])
        items.append({
            'label': title,
            'path': plugin.url_for('attention_channel_list', mid = mid, cid = item['id'], page = '1'),
            })
    return items

@plugin.route('/user_info/<mid>/')
def user_info(mid):
    result, total_page = bilibili.get_attention_video(mid, 0, 1, 1)
    items = []
    items.append({
        'label': u'频道',
        'path': plugin.url_for('attention_channel', mid = mid),
        })
    title = u'{} ({}个视频)'.format(u'全部', str(result['count']))
    items.append({
        'label': title,
        'path': plugin.url_for('attention_video', mid = mid, tid = '0', page = '1'),
        })
    for item in result['tlist'].values():
        title = u'{} ({}个视频)'.format(item['name'], str(item['count']))
        items.append({
            'label': title,
            'path': plugin.url_for('attention_video', mid = mid, tid = item['tid'], page = '1'),
            })
    return items

@plugin.route('/attention/<page>/')
def attention(page):
    result, total_page = bilibili.get_attention(page)
    items = []
    for item in result:
        items.append({
            'label': item['uname'],
            'path': plugin.url_for('user_info', mid = item['fid']),
            'thumbnail': item['face'],
            })
    items += next_page('attention', page, total_page)
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
        filename = tempdir + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)) + '.jpg'
        captcha = LoginDialog(captcha = bilibili.get_captcha(filename)).get()
        os.remove(filename)
        result, msg = bilibili.login(username, password, captcha)
        if result == True:
            plugin.notify('登陆成功', delay=2000)
        else:
            plugin.notify(msg, delay=2000)

@plugin.route('/logout/')
def logout():
    bilibili.logout()

@plugin.route('/history/<page>/')
def history(page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_history(page)
    items = []
    for item in result:
        info = {
            'genre': item['tname'],
            'writer': item['owner']['name'],
            'plot': item['desc'],
            'duration': item['duration']
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['ctime'])))
        except:
            pass
        items.append(get_av_item(item['aid'], label = item['title'], thumbnail = item['pic'], info = info))
    items += next_page('history', page, total_page)
    return items

@plugin.route('/timeline/')
def timeline():
    return []

@plugin.route('/category/<tid>/')
def category(tid):
    items = []
    for data in bilibili.get_category(tid):
        tid = data.keys()[0]
        value = data.values()[0]
        if len(value['subs']) == 0:
            path = plugin.url_for('category_order', tid = tid)
        else:
            path = plugin.url_for('category', tid = tid)
        items.append({'label': value['title'].decode('utf-8'), 'path': path})
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
    plugin.set_content('videos')
    result, total_page = bilibili.get_category_list(tid = tid, order = order, page = page, days = days)
    items = previous_page('category_list', page, total_page, order = order, tid = tid, days = days)
    items = []
    for item in result:
        duration = 0
        for t in item['duration'].split(':'):
            duration = duration * 60 + int(t)
        info = {
            'genre': item['typename'],
            'writer': item['author'],
            'plot': item['description'],
            'duration': duration,
            }
        try:
            info['year'] = int(item['create'][:4])
        except:
            pass

        items.append(get_av_item(item['aid'], label = item['title'], thumbnail = item['pic'], info = info))
    items += next_page('category_list', page, total_page, order = order, tid = tid, days = days)
    return items

@plugin.route('/')
def root():
    items = [
        #{'label': u'搜索(暂不支持)', 'path': plugin.url_for('search')},
        {'label': u'视频分类', 'path': plugin.url_for('category', tid = '0')},
    ]
    if bilibili.is_login:
        items += [
            {'label': u'我的动态', 'path': plugin.url_for('dynamic', page = '1')},
            {'label': u'我的历史', 'path': plugin.url_for('history', page = '1')},
            {'label': u'我的收藏', 'path': plugin.url_for('fav_box')},
            {'label': u'我的追番', 'path': plugin.url_for('bangumi_chase', page = '1')},
            {'label': u'我的关注', 'path': plugin.url_for('attention', page = '1')},
            {'label': u'退出登陆', 'path': plugin.url_for('logout')},
            ]
    else:
        items += [
            {'label': u'登陆账号', 'path': plugin.url_for('login')},
            ]
    return items


if __name__ == '__main__':
    plugin.run()
