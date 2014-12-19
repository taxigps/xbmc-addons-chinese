# -*- coding: utf-8 -*-

#v1.0.0 2009/11/08 by robinttt, initial release
#v1.1.0 2011/12/04 by d744000, full web scraping, added search.

import urllib,urllib2,os,re,sys
import gzip,StringIO #playvideo
import hashlib,time

#if 'XBMC' in os.path.realpath('.'):
if not sys.modules.has_key('idlelib'):
    import xbmc
else:
    xbmc = None

if xbmc:
    import xbmcplugin,xbmcgui,xbmcaddon
    from BeautifulSoup import BeautifulSoup
else:
    from myBeautifulSoup import BeautifulSoup
    urlparams = []

xbmc_release = True
support_MV = False


UserAgent = 'Mozilla/5.0 (Windows NT 5.1; rv:8.0) Gecko/20100101 Firefox/8.0'
URL_BASE = 'http://yinyue.kuwo.cn'

#
# Web process engine
#
def getUrlTree(url, data=None):
    def getUrl(url, data=None):
        headers = { 
            'User-Agent': UserAgent,
        }
        if data:
            if type(data) != str:
                # 2-item tuple or param dict, assume utf-8
                data = urllib.urlencode(data)
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        httpdata = response.read()
        response.close()
        if response.headers.get('content-encoding', None) == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        # BeautifulSoup handles encoding, thus skip transcoding here.
        return httpdata

    data = getUrl(url, data)
    tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree


def processWebPage(tagHandler):
    global tree
    url = params['url']
    if params.has_key('urlpost'):
        post = params['urlpost']
    else:
        post = None
    tree = getUrlTree(url, post)
    driller(tree, tagHandler)
    endDir()


def processStoredPage(tagHandler):
    global tree
    data = params['url']
    tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
    driller(tree, tagHandler)
    endDir()


context_params = {}
def driller(tree, lCont):
    #global item
    global context_params
    if type(lCont) != list:
        lCont = [lCont]
    for cont in lCont:
        result = None
        if cont.has_key('context'):
            context_params = cont['context']
        else:
            context_params = {}
        items = tree.findAll(*cont['tag'])
        for item in items:
            if not xbmc_release:
                if cont['vect']:
                    result = cont['vect'](item)
            else:
                if cont['vect']:
                    try:
                        result = cont['vect'](item)
                    except:
                        pass
            if result != 'DRILLER_NO_DEEPER' and cont['child']:
                driller(item, cont['child'])


#
# Keyboard for search
#
def searchDefaultKeyboard(key=None, mode='all'):
    if not key:
        if xbmc:
            keyb = xbmc.Keyboard('', '搜索(可用拼音)')
            keyb.doModal()
            if keyb.isConfirmed():
                key = keyb.getText()
    if not key:
        return
    url = 'http://sou.kuwo.cn/ws/NSearch?key='+urllib.quote_plus(key)+'&type='+mode
    params['url'] = url
    params['indent'] = str(True)
    params['search_key'] = key
    processWebPage(hSearchResult)


def searchChineseKeyboard(key=None, mode='all'):
    if key:
        #print('search input: %s, type %s' % (key, type(key)))
        url = 'http://sou.kuwo.cn/ws/NSearch?key='+urllib.quote_plus(key)+'&type='+mode
        params['url'] = url
        params['indent'] = str(True)
        params['search_key'] = key
        processWebPage(hSearchResult)
    else:
        # Somehow, current chinese keyboard implementation works differently than the default keyboard.
        # The doModal doesn't prevent xbmcplugin from popping up the directory-scanning window, which
        # covers up the keyboard window.
        # A workaround is to terminate the directory, doModal, pass in keyboard input as new param of 
        # the container, then relaunch the container.
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        #中文输入法
        keyboard = ChineseKeyboard.Keyboard('', '搜索')
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            keyword = keyboard.getText()
            if not keyword:
                return
            u=sys.argv[0]+"?url="+urllib.quote_plus('')+"&mode="+urllib.quote_plus('search("'+keyword+'")')
            xbmc.executebuiltin('Container.Update(%s,replace)' % u)

# Choose ChineseKeyboard if script.module.keyboard.chinese is installed.
try:
    import ChineseKeyboard
    search = searchChineseKeyboard
except:
    search = searchDefaultKeyboard


#
# Media player
#
def get_content_by_tag(tree, tag):
    f = tree.find(tag)
    if f and f.contents:
        return f.contents[0].encode('utf-8')
    else:
        return ''

def PlayMusic():
    mids = params['url']
    if xbmc:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
    mids = mids.split('/')
    for mid in mids:
        if mid == '':
            continue
        tree = getUrlTree('http://player.kuwo.cn/webmusic/st/getNewMuiseByRid?rid=MUSIC_'+mid)
        title = get_content_by_tag(tree, 'name')
        # kuwo has names like "song name(抢听版)", causing lyrics look up failure
        true_title = title.split('(')[0].rstrip()
        artist = get_content_by_tag(tree, 'artist')

        # prefer AAC or WMA, somehow it starts or loads faster than the mp3 link,
        # change AAC to the first download.  edit by runner6502@gamil.com
        path = get_content_by_tag(tree, 'aacpath')
        dl = get_content_by_tag(tree, 'aacdl')
        if not (path and dl):
            path = get_content_by_tag(tree, 'path')
            dl = get_content_by_tag(tree, 'wmadl')
            if not (path and dl):
                path = get_content_by_tag(tree, 'mp3path')
                dl = get_content_by_tag(tree, 'mp3dl')

        if path and dl:
            timestamp = ("%x" % int(time.time()))[:8]
            hashstr = hashlib.md5("kuwo_web@1906/resource/%s%s" % (path, timestamp)).hexdigest()
            url = 'http://%s/%s/%s/resource/%s' % (dl, hashstr, timestamp, path)
            if xbmc:
                listitem=xbmcgui.ListItem(title)
                listitem.setInfo( type="Music", infoLabels={ "Title": true_title, "Artist": artist} )
                playlist.add(url, listitem)
            if not xbmc:
                print('PlayMusic: %s - %s, %s' % (title, artist, url))
    if xbmc:
        xbmc.Player().play(playlist)


def PlayVideo():
    # play MV need more decipher, currently it ask for kuwobox app, seems the app send a http GET first, 
    return  # function not supported yet.
    mids = params['url']
    if xbmc:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
    mids = mids.split('/')
    for mid in mids:
        if mid == '':
            continue
        tree = getUrlTree('http://plugin.kuwo.cn/mbox/st/FlashData?rid='+mid)
        title = get_content_by_tag(tree, 'name')
        true_title = title.split('(')[0].rstrip()
        artist = get_content_by_tag(tree, 'artist')

        path = get_content_by_tag(tree, 'path')
        # Kuwo requires Windows client sw to play video, mbox://.
        # Don't know how to make it work yet.
        url = 'http://dl.cdn.kuwo.cn' + path #+'MV_38.mp4'
        if xbmc:
            listitem=xbmcgui.ListItem(title)
            listitem.setInfo( type="Video", infoLabels={ "Title": true_title, "Artist": artist} )
            listitem.setProperty('IsPlayable', 'true')
            playlist.add(url, listitem)
        if not xbmc:
            print('PlayVideo: %s - %s, %s' % (title, artist, url))
    if xbmc:
        xbmc.Player().play(playlist)


#
# Utilities
#
def tag_na_feature(sName):
    ''' Add ARGB tag to gray out features not supported yet. '''
    # 80% tranparent, light gray.
    return '[COLOR 33D3D3D3]' + sName + '[/COLOR]'


def addBanner(name):
    ''' Add a banner, a button without action, but to separate groups of other buttons. '''
    # Burlywood color
    if name:
        name = '[COLOR FFDEB887]' + '【' + name + '】' + '[/COLOR]' 
        addDir(name, '', 'pass', '', folder=False)

#
# Kuwo tag handlers
#
def addCategoryFast():
    addDir('搜索', '', 'search()', folder=True)
    addDir('排行榜', 'http://yinyue.kuwo.cn/billboard_index.htm', 'processWebPage(hFrame)')
    addDir('歌手', 'http://yinyue.kuwo.cn/artist.htm', 'processWebPage(hFrame)')
    addDir('分类', 'http://yinyue.kuwo.cn/category.htm', 'processWebPage(hFrame)')
    addDir('专辑', 'http://yinyue.kuwo.cn/album.htm', 'processWebPage(hFrame)')
    addDir('淘歌单', 'http://fang.kuwo.cn',
           "addDir('淘歌单分类', 'http://fang.kuwo.cn/p/st/PlCat', 'processWebPage(hFrame)');"
           "processWebPage(hPlaylistFrame)")
    endDir()


def addCategory(item):
    SUPPORTED_CATEGORIES = ['排行榜', '歌手', '分类', '专辑', '淘歌']
    name = str(item.span.contents[0])
    if name in SUPPORTED_CATEGORIES:
        url =  item['href']
        if name == '淘歌':
            addDir('淘歌单分类', 'http://fang.kuwo.cn/p/st/PlCat', 'processWebPage(hFrame)')
            addDir(name, url, 'processWebPage(hPlaylistFrame)')
        else:            
            addDir(name, url, 'processWebPage(hFrame)')


def extractName(item):
    if not item:
        return ''
    name = ''
    span_name = item.find('span')
    if span_name:
        name = span_name.contents[0].encode('utf-8')
    elif item.has_key('title'):
        name = item['title'].encode('utf-8')
    elif item.contents:
        content = item.contents[0]
        if 'String' in str(type(content)):
            #BeautifulSoup NavigableString
            name = content.encode('utf-8')
        else:
            try:
                name = content['title'].encode('utf-8')
            except:
                pass
    if not name:
        if not xbmc_release:
            print('listFrames, name not found in %s' % str(item))
    return name

def extractHref(item):
    if not item:
        return ''
    if item.has_key('href'):
        item_url = item['href'].encode('utf-8')
    else:
        item_url = ''
    return item_url
    
def extractImg(item):
    if not item:
        return ''
    for k in ['src', 'sr', 'lazy_src', 'init_src']:
        if item.has_key(k):
            return item[k].encode('utf-8')
    return ''

def extractImgSearch(item, name=''):
    iconimage = extractImg(item.find('img'))
    if (not iconimage) and name:
        attrs={'title':unicode(name,'utf-8')}
        iconimage = extractImg(item.findChild('img', attrs))
        if not iconimage:
            iconimage = extractImg(item.findPreviousSibling('img', attrs))
        if not iconimage:
            iconimage = extractImg(item.findParent().findPreviousSibling('img', attrs))
    return iconimage

def addFrame(item):
    name = extractName(item)
    if not name:
        return
    item_url = extractHref(item)
    if item_url:
        iconimage = extractImgSearch(item, name)
        if context_params.has_key('onclick'):
            mode = context_params['onclick']
        else:
            mode = 'processWebPage(hPage)'
        addDir(name, item_url, mode, iconimage)


def addPlayList(item):
    ''' playlist item '''
    url = extractHref(item.a)
    name = extractName(item.a)
    img_item = item.findPreviousSibling()
    if img_item:
        iconimg = extractImg(img_item.find('img'))
    else:
        iconimg = ''
    context = {'indent':str(True), 'playall_title':('播放【' + name + '】所含曲目')}
    addDir('    ' + name, url, 'processWebPage(hPlayListPage)', iconimg, context=context)

def addPlayListFocus(item):
    ''' playlist item in the flash hightlighter '''
    name = extractName(item)
    if not name:
        return
    url = extractHref(item)
    iconimg = extractImg(item.find('img'))
    context = {'indent':str(True), 'playall_title':('播放【' + name + '】所含曲目')}
    addDir('    ' + name, url, 'processWebPage(hPlayListPage)', iconimg, context=context)


def addPlayListBanner(item):
    names = {'focusDiv':'闪亮歌单', 'FrmRecPl':'推荐歌单', 'FrmHotPl':'人气歌单', 'focusDiv':'闪亮歌单'}
            # These requires login, 'FrmMyPl': '我制作的歌单', 'FrmMyColPl':'我收藏的歌单'}
    if item.has_key('id') and (not names.has_key(item['id'])):
        return
    name = ''
    if item.has_key('id') and names.has_key(item['id']):
        name = names[item['id']]
    if not name:
        h3 = item.findParent().find('span', attrs={'class':'repairTit'})
        if h3 and h3.contents and ('String' in str(type(h3.contents[0]))):
            name = re.sub('\s', '', h3.contents[0]).encode('utf-8')
    if not name:
        h3 = item.findParent().find('h3')
        if h3 and h3.contents and ('String' in str(type(h3.contents[0]))):
            name = re.sub('\s', '', h3.contents[0]).encode('utf-8')
            
    if name:
        addBanner(name)


def addCategoryBanner(item):
    if item['class'] in (tagBanners + tagSubBanners):
        name = [x for x in item.contents if 'String' in str(type(x))]
        if name:
            addBanner(name[0].encode('utf-8'))
 

def addBillboardPhase(item):
    nxt_idx = None
    if params.has_key('billboard_idx'):
        cur_idx = params['billboard_idx']
    else:
        cur_idx = item.find('li')['idx'].encode('utf-8')
    cur_item = item.find('li', {'idx':cur_idx})
    if cur_item:
        tabDef = cur_item.find('p')
        if tabDef and tabDef.contents:
            params['playall_title'] = ('播放' + tabDef.contents[0].encode('utf-8') + '歌曲')
        nxt_item = cur_item.findNextSibling('li')
        if nxt_item:
            nxt_idx = nxt_item['idx'].encode('utf-8')

    # previous billboard phase
    if nxt_idx:
        rgtArrow = item.find(attrs={'id':"goRight", 'class':"jtRig"})
        if rgtArrow and rgtArrow.has_key('onclick'):
            catId = re.search("getData\((\d+),1\)", rgtArrow['onclick'])
            if catId:
                catId = catId.groups()[0].encode('utf-8')
                url='http://yinyue.kuwo.cn/yy/dd/BillBoardIndex'
                post='cat='+catId+'&phase='+nxt_idx
                context = {'urlpost':post, 'billboard_idx':nxt_idx, 'billboard_phases':str(item)}
                addDir('查看前一期', url, 'processWebPage([songList])', '', context=context)


def addPlayAll(item):
    if params.has_key('billboard_phases'):
        print(params['billboard_phases'])
        phase_item = BeautifulSoup(params['billboard_phases'], convertEntities=BeautifulSoup.HTML_ENTITIES)
        addBillboardPhase(phase_item)
    mids = item.findAll(attrs={'type':'checkbox'})
    mids = [x['mid'].encode('utf-8') for x in mids if x.has_key('mid')]
    mids = '/'.join(mids)
    if params.has_key('playall_title'):
        disp_title = params['playall_title']
    else:
        h5 = item.findPreviousSibling('h5')
        if h5 and h5.contents and ('String' in str(type(h5.contents[0]))): #<class 'BeautifulSoup.NavigableString'>
            disp_title = '播放' + re.sub('\s', '', h5.contents[0]).encode('utf-8')
        elif h5 and h5.findChild('a') and h5.findChild('a').has_key('title'):
            disp_title = '播放' + h5.a['title'].encode('utf-8')
        elif params.has_key('playall_adjust'):
            disp_title = '播放' + params['playall_adjust'] + '歌曲'
        else:
            disp_title = '播放全部歌曲'
    addDir(disp_title,mids,'PlayMusic()','',folder=False)


def addSong(item):
    mid = item.find(attrs={'type':'checkbox'})
    if not (mid and mid.has_key('mid')):
        return
    mid = mid['mid']
    title = item.find(attrs={'class':'songName'}).a['title'].encode('utf-8')
    # artist page has album name in 'class songer', not artist name
    artist = ''
    if params.has_key('artist'):
        artist = params['artist']
    if not artist:
        chld = item.find(attrs={'class':'songer'})
        if chld and chld.findChild('a'):
            chld = chld.findChild('a')
            if chld.has_key('title'):
                artist = chld['title'].encode('utf-8')
    iconimage = ''
    addLink(title,artist,mid,'PlayMusic()',iconimage)


def addArtist(item):
    # artist item
    url = extractHref(item.a)
    name = extractName(item.a)
    iconimg = extractImg(item.find('img'))
    context = {'indent':str(True)}
    if params.has_key('indent'):
        name = '    ' + name
    addDir(name, url, 'processWebPage(hArtistPage)', iconimg, context=context)


def listArtistFromStr():
    # artist item
    data = params['url']
    tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
    artists = tree.findAll(attrs={'otype':'art'})
    for item in artists:
        url = extractHref(item)
        name = extractName(item)
        context = {'indent':str(True), 'playall_adjust':(name + '热门')}
        addDir(name, url, 'processWebPage(hArtistPage)', '', context=context)
    endDir()

    
def addAlphaBeta(item):
    # artist alphabeta item
    try:
        name = item.input['rel'].upper()
        addDir(name, str(item), 'listArtistFromStr()', '')
    except:
        pass


def addMV(item):
    if not support_MV:
        return
    url = extractHref(item.a)
    mid = re.findall('(MV_\d+)', url)
    if not mid:
        return
    else:
        mid = mid[0]
    title = item.a['title']
    if params.has_key('artist'):
        artist = params['artist']
    else:
        artist = ''
    iconimg = extractImg(item.find('img'))
    title = tag_na_feature(title)   # Kuwo requires kuwo_music_box Windows client, don't know how to workaround that.
    addLink(title,artist,mid,'PlayVideo()',iconimg,video=True)

def addPlayAllMV(item):
    if not support_MV:
        return
    mids = item.findAll('li')
    pat = re.compile('(MV_\d+)')
    mids = [pat.findall(x.a['href'])[0] for x in mids if x.find('a') and x.a.has_key('href') and pat.findall(x.a['href'])]
    mids = '/'.join(mids)
    if params.has_key('playall_title'):
        disp_title = params['playall_title']
    else:
        h5 = item.findPreviousSibling('h5')
        if h5 and h5.contents and ('String' in str(type(h5.contents[0]))):
            disp_title = '播放' + re.sub('\s', '', h5.contents[0]).encode('utf-8')
        elif h5 and h5.findChild('a') and h5.findChild('a').has_key('title'):
            disp_title = '播放' + h5.a['title'].encode('utf-8')
        elif params.has_key('playall_adjust'):
            disp_title = '播放' + params['playall_adjust'] + 'MV'
        else:
            disp_title = '播放全部MV'
    disp_title = tag_na_feature(disp_title)
    addDir(disp_title,mids,'PlayVideo()','',folder=False)


def addAlbum(item):
    # album item
    url = extractHref(item.a)
    title = extractName(item.a)
    iconimg = extractImg(item.find('img'))
    albumCont = item.findNextSibling(attrs={'class':'albumCont'})
    try:
        artist = albumCont.li.findChildren('a')[-1]['title'].encode('utf-8')
    except:
        artist = ''
    if artist:
        playall_title = '播放【' + artist + ' - ' + title + '】所含曲目'
        dispname = artist + ' - ' + title
    else:
        playall_title = '播放【' + title + '】所含曲目'
        dispname = title
    context = {'indent':str(True), 'playall_title':playall_title}
    if params.has_key('indent'):
        dispname = '    ' + dispname

    addDir(dispname, url, 'processWebPage(hAlbumPage)', iconimg, context=context)


def addPlayAllAlbum(item):
    # just a banner for now
    h5 = item.findPreviousSibling('h5')
    if h5 and h5.contents and ('String' in str(type(h5.contents[0]))):
        disp_title = re.sub('\s', '', h5.contents[0]).encode('utf-8')
    elif h5 and h5.findChild('a') and h5.findChild('a').has_key('title'):
        disp_title = h5.a['title'].encode('utf-8')
    elif params.has_key('playall_adjust'):
        disp_title = params['playall_adjust'] + '专辑'
    else:
        disp_title = '全部专辑'
    addDir(disp_title,'','pass','',folder=False)


def addPlayAllArtist(item):
    if item['class'] == 'picFrm':
        if item.has_key('id') and item['id']=="recent_listener": # skip 最近谁在听
            return
    if item['class'] == 'f14b':
        addCategoryBanner(item)
        return
    # just a banner for now
    h5 = item.findPreviousSibling('h5')
    if h5 and h5.contents and ('String' in str(type(h5.contents[0]))):
        disp_title = re.sub('\s', '', h5.contents[0]).encode('utf-8')
    elif h5 and h5.findChild('a') and h5.findChild('a').has_key('title'):
        disp_title = h5.a['title'].encode('utf-8')
    elif params.has_key('playall_adjust'):
        disp_title = params['playall_adjust'] + '歌手'
    else:
        try:
            # picFrm of 热门歌手 in Genre, 与xxx相似的歌手 in Artist page
            disp_title = item.findPreviousSibling('h3').contents[2].contents[0].encode('utf-8')
        except:
            disp_title = '全部歌手'
    addDir(disp_title,'','pass','',folder=False)


def addDirMore(item):
    title = ''
    context = {}
    if params.has_key('search_key'):
        types = {'musicRs':'歌曲', 'artistRs':'歌手', 'albumRs':'专辑', 'lyricRs':'歌词', 'mvRs':'MV', 'playlistRs':'歌单'}
        if item.has_key('id'):
            search_type = item['id'].encode('utf-8')
            if types.has_key(search_type):
                title = '更多' + params['search_key'] + '的相关' + types[search_type]
                context = {'search_type':search_type, 'search_key':params['search_key']}
    if not title:
        if item.h2 and item.h2.contents:
            title = item.h2.contents[0].encode('utf-8')
    if not title:
        h2 = item.findPreviousSibling('h2')
        if h2 and h2.contents:
            title = h2.contents[0].encode('utf-8')
    if (not support_MV) and (title.endswith('MV')):
        return
    addDir(title, str(item), 'processStoredPage(hNextPage)', '', context=context)


def filterSearchPage(item):
    if params.has_key('search_type') and item.has_key('id'):
        if params['search_type'] != item['id'].encode('utf-8'):
            return 'DRILLER_NO_DEEPER'


def addPage(item):
    url = item['href']
    if url == '#@':
        # linking to current page
        return
    title = item.contents[0].encode('utf-8')
    if title in ['上一页']:
        # XBMC '..' button goes to previous page, and much faster as it doesn't retrieve the http page.
        return
    context = {}
    if 'javascript:getCategoryData' in url:
        # u"javascript:getCategoryData('music',2,25,'','artistSong','lp','\u6d41\u884cPop','\u6d41\u884cPop');"
        url = url.replace("\'", '')
        m = re.search('javascript:getCategoryData\((.*),(.*),(.*),(.*),(.*),(.*),(.*),(.*)\)', url)
        if m:
            (dataType,pn,ps,order,contId,ctype,cat1,cat2) = m.groups()
        else:
            return
        url='http://yinyue.kuwo.cn/yy/st/getCatData'
        if not pn:
            pn = '1'
        if not ps:
            ps = '8'
        post = 'cat1Name='+cat1.encode('utf-8')
        post += '&cat2Name='+cat2.encode('utf-8')
        post += '&ctype='+ctype.encode('utf-8')
        post += '&type='+dataType.encode('utf-8')
        post += '&pn='+pn.encode('utf-8')
        post += '&ps='+ps.encode('utf-8')
        post += '&order='+order.encode('utf-8')
        post += '&contId='+contId.encode('utf-8')
        context = {'urlpost':post}
    elif 'javascript:getData' in url:
        #"javascript:getData('music',2,25,'time','artistSong','周杰伦');"
        #name=%E5%88%98%E5%BE%B7%E5%8D%8E&type=music&pn=2&ps=25&order=time&contId=artistSong
        url = url.replace("\'", '')
        m = re.search('javascript:getData\((.*),(.*),(.*),(.*),(.*),(.*)\)', url)
        if m:
            (dataType,pn,ps,order,contId,name) = m.groups()
        else:
            print('Failed javascript:getData, %s' % url)
            return
        url='http://yinyue.kuwo.cn/yy/st/getData'
        if not pn:
            pn = '1'
        if not ps:
            ps = '8'
        post = 'name='+name.encode('utf-8')
        post += '&type='+dataType.encode('utf-8')
        post += '&pn='+pn.encode('utf-8')
        post += '&ps='+ps.encode('utf-8')
        post += '&order='+order.encode('utf-8')
        post += '&contId='+contId.encode('utf-8')
        try:
            context = {'urlpost':post}
        except:
            print(post)

    if params.has_key('search_type'):
        context['search_type'] = params['search_type']
        context['search_key'] = params['search_key']
        addDir(title, url, 'processWebPage(hSearchMorePage)', '', context=context)
    else:
        addDir(title, url, 'processWebPage(hNextPage)', '', context=context)



#
# Kuwo html tags
#
tagBanners = ['mTitBg', 'titYh', 'titYh titLr']
tagSubBanners = ['f14b']

topMenuItem = {'tag':('a',{}), 'vect':addCategory, 'child':None} 
topMenu = {'tag':(None,{'class':'navLeft'}), 'vect':None, 'child':topMenuItem} 

subCategory = {'tag':('a',{}), 'vect':addFrame, 'child':None}
subCategoryFrm = {'tag':(None,{'class':['borLr1', 'borLr', 'borLr botNone', 'borLr noLeft', 'chartList botNone'] + tagBanners}),
                 'vect':addCategoryBanner, 'child':subCategory}

subPlayList = {'tag':(None,{'class':['tgCont','gdCont']}), 'vect':addPlayList, 'child':None}
subCategoryPlayList = {'tag':(None,{'class':['tgFrm', "tgFrm unDis"]}), 'vect':addPlayListBanner, 'child':subPlayList}

subPlayListFocus = {'tag':('a',{}), 'vect':addPlayListFocus, 'child':None}
subCategoryPlayListFocus = {'tag':(None,{'class':'focus'}), 'vect':addPlayListBanner, 'child':subPlayListFocus}

chartTabBar = {'tag':(None,{'class':'chartTab'}), 'vect':addBillboardPhase, 'child':None} 

songItem = {'tag':(None,{'class':re.compile('itemUl\d*')}), 'vect':addSong, 'child':None}
songItem_show_artist = {'tag':(None,{'class':re.compile('itemUl\d*')}), 'vect':addSong, 'child':None, 'context':{'addlink_adjust':'show_artist'}}
songContainer = {'tag':(None,{'id':"container"}), 'vect':addPlayAll, 'child':songItem_show_artist} 

artistItem = {'tag':('li',{}), 'vect':addArtist, 'child':None}
artistContainer = {'tag':(None,{'class':['sortFrm','numList newnumList'] + tagSubBanners}), 'vect':addCategoryBanner, 'child':artistItem} 
artistAlphaBeta = {'tag':(None,{'class':"numList"}), 'vect':addAlphaBeta, 'child':None} 

pageItem = {'tag':(None,{'class':'page'}), 'vect':addPage, 'child':None}

songList = {'tag':(None,{'class':re.compile('listCont\d*')}), 'vect':addPlayAll, 'child':songItem}

albumItem = {'tag':(None,{'class':re.compile('alBg\d*')}), 'vect':addAlbum, 'child':None}
albumList = {'tag':(None,{'class':"albumFrm"}), 'vect':addPlayAllAlbum, 'child':albumItem}

mvItem = {'tag':('li',{}), 'vect':addMV, 'child':None}
mvList = {'tag':(None,{'class':re.compile("mvFrm\d*")}), 'vect':addPlayAllMV, 'child':mvItem}

artistItem = {'tag':('li',{}), 'vect':addArtist, 'child':None}
artistList = {'tag':(None,{'class':re.compile("sortFrm\d*|picFrm")}), 'vect':addPlayAllArtist, 'child':artistItem}

classMore = {'tag':(None,{'class':"mBodFrm3 unDis"}), 'vect':addDirMore, 'child':None}
artistTop10s = {'tag':(None,{'id':"top10Songs"}), 'vect':None, 'child':[songList, albumList, mvList]} 

songSearchList = {'tag':(None,{'id':'index_music'}), 'vect':addPlayAll, 'child':songItem}
lyricsSearchList = {'tag':(None,{'id':'index_lyric'}), 'vect':addPlayAll, 'child':songItem}

searchResult = {'tag':(None,{'id':"allRs"}), 'vect':None, 'child':[songSearchList, artistList, albumList, lyricsSearchList, mvList]}
resultNextPage = {'tag':(None,{'class':"bodFrm"}), 'vect':None, 'child':[songList, albumItem, mvList, pageItem]}
resultMore = {'tag':(None,{'class':"bodFrm unDis"}), 'vect':addDirMore, 'child':None}

hTop = [topMenu]
hFrame = [subCategoryFrm]
hPage = [chartTabBar,
         songContainer,
         artistContainer,
         artistAlphaBeta,
         albumItem,
         pageItem
         ]
hPlaylistFrame = [subCategoryPlayListFocus, subCategoryPlayList]
hArtistPage = [artistTop10s, artistList, classMore]
hAlbumPage = [songList, albumList] 
hNextPage = [songList, albumItem, mvList, pageItem]
hSearchMorePage = [resultNextPage]
hPlayListPage = [songList, albumList]
hSearchResult = [searchResult, resultMore]


#
# XBMC plugin
#
def addLink(title,artist,url,mode,iconimage='',total=0,video=False):
    if not xbmc:
        try:
            print('addLink(%s, %s, %s, %s, %s)' % (title,artist,url,mode,iconimage))
        except:
            print('addLink(title?, artist?, %s, %s, %s)' % (url,mode,iconimage))
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)
    if artist:
        displayname = artist + ' - ' + title
    else:
        displayname = title
    displayname = '    ' + displayname
    if video:
        itemType = "Video" 
    else:
        itemType = "Music"
    if xbmc:
        item=xbmcgui.ListItem(displayname, iconImage=iconimage, thumbnailImage=iconimage)
        item.setInfo( type=itemType, infoLabels={ "Title":title, "Artist":artist } )
        return xbmcplugin.addDirectoryItem(pluginhandle,url=u,listitem=item,isFolder=False,totalItems=total)
    else:
        print(u)
        urlparams.append(u)


def addDir(name, url, mode, iconimage='DefaultFolder.png', context={}, plot='', folder=True, total=0):
    if url == '#@':
        url = params['url']
    elif url.startswith('/'):
        url = URL_BASE + url
    if not xbmc:
        try:
            print('addDir(%d: %s, %s, %s, %s, %s)' % (len(urlparams), name,str(url)[:300],mode,iconimage,str(context)[:300]))
        except:
            print('addDir(%d: %s, ?url, ?mode, %s)' % (len(urlparams), name,iconimage))
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)
    if context:
        for k in context:
            u += ("&%s=" % k) + urllib.quote_plus(context[k])
    if xbmc:
        item=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        return xbmcplugin.addDirectoryItem(pluginhandle,url=u,listitem=item,isFolder=folder,totalItems=total)
    else:
        if len(u) > 300:
            print('addDir u len %d, saved in urlparams %d' % (len(u), len(urlparams)))
        else:
            print(u)
        urlparams.append(u)


def endDir(cache=True):
    if xbmc:
        xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=True)


def get_params():
    print(sys.argv[0] + sys.argv[2][:300])
    param={}
    params=sys.argv[2]
    if len(params)>=2:
        cleanedparams=params.rsplit('?',1)
        if len(cleanedparams) == 2:
            cleanedparams = cleanedparams[1]
        else:
            cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=urllib.unquote_plus(splitparams[1])
    return param


if not xbmc:
    pluginhandle = 1
else:
    pluginhandle = int(sys.argv[1])
##    xbmcplugin.setContent(pluginhandle, 'musicvideos')
##    addon = xbmcaddon.Addon('plugin.audio.kuwobox')
##    pluginpath = addon.getAddonInfo('path')

params = {}
def main():
    global params
    params=get_params()
    try:
        mode=params["mode"]
    except:
        mode=None
    if mode==None:
        # params['url'] = URL_BASE
        # processWebPage(hTop)
        addCategoryFast()
    else:
        exec(mode)

if xbmc:
    main()
    
if not xbmc:
    # Unit Test without XBMC environment
    urlparam = ''
    test_url = [
        'plugin://plugin.audio.kuwobox/?url=http%3A%2F%2Fyinyue.kuwo.cn%2Fcategory.htm&mode=processWebPage%28hFrame%29',
        'plugin://plugin.audio.kuwobox/?url=http%3A%2F%2Ffang.kuwo.cn%2Fp%2Fweb%2FGetWebRadio%3Frname%3D%25E7%25BA%25AF%25E7%2599%25BD%25E7%2594%25B5%25E5%258F%25B0&mode=processWebPage%28hPage%29',
        ]

    def UTP(urlparam):
        sys.argv = ['plugin://plugin.audio.kuwobox/', '-1', urlparam]
        main()

    def utp_url(index):
        sys.argv = ['plugin://plugin.audio.kuwobox/', '-1', urlparams[index]]
        main()

    def testMenu(items=[], url=None):
        global urlparams
        print('testMenu(url="%s", items=%s)\n' % (url, items))
        if url != None and type(url) == str:
            UTP(url)
        if items and type(items) != list:
            items = [items]
        for x in items:
            url = urlparams[x]
            print('\n\n\n ******* TESTING %s\n' % url[:300])
            UTP(url)

    for urlparam in test_url:
        UTP(urlparam)
    if not test_url:
        testMenu([], '')
    
