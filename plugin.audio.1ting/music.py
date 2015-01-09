#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, re, json
from bs4 import BeautifulSoup
from xml.sax.saxutils import unescape

webHtml = "http://www.1ting.com"
SingerHtml = "/group.html"
randHtml = "/rand.php"
rankHtml = "/rank.html"
tagHtml = "/tag"
genreHtml = "/genre"

imgBaseHtml = "http://img.1ting.com/images/singer/s"
#songJsBaseHtml = "/json2010_"
songBasehtml = "http://f.1ting.com"
rankImgBaseHtml = "/api/client/images"
searchHtml = "http://so.1ting.com"

MODE_NONE = ""
MODE_MENU = "menu"

MODE_SINGER_GROUP = "singer_group"
MODE_SINGER_ALL = "singer_all"
MODE_SINGER = "singer"
MODE_SONG = "song"
MODE_SONGLIST = "songList"
MODE_PLAYLIST = "playlist"
MODE_ALBUM = "album"
MODE_ALBUMLIST = "albumList"
MODE_SINGERLIST = "singerList"

MODE_RAND = "rand"
MODE_RANK = "rank"
MODE_TAG_LIST = "tag_list"
MODE_TAG = "tag"

MODE_SEARCH = "search"
MODE_SEARCH_LIST = "search_list"

#name, mode, url, icon, info
menu = [('搜索', MODE_SEARCH), 
        ('歌手', MODE_SINGER_GROUP), 
        ('排行榜', MODE_RANK),
        ('标签', MODE_TAG_LIST, tagHtml),
        ('曲风', MODE_TAG_LIST, genreHtml),
        ('随便一听', MODE_RAND)]

def getMenu():
    return menu

def isFolder(mode):
    return mode not in (MODE_NONE, MODE_SONG, MODE_PLAYLIST)

def request(url, soup = True, album = False):
    if not url.startswith('http'): url = webHtml + url
    print('request', url)
    req = urllib2.Request(url)           # create one connection
    try:
        response = urllib2.urlopen(req)      # get the response
        cont = response.read()        # get all the webpage html data in string
        if album: # 修正html标签错误
            cont = cont.replace('</span></a> </li>', '</a></span> </li>')
        response.close()
    except:
        return
    return BeautifulSoup(cont, 'html.parser') if soup else cont

def getSongUrl(url):
    if not url: return
    req = urllib2.Request(songBasehtml + url)
    req.add_header("Cookie", "PIN=cnGQFFSRmPRxcDj2aUSnAg==")
    url = urllib2.urlopen(req).geturl()
    return url

def getSearchUrl(q, domain = "song"):
    return "%s/%s?q=%s" % (searchHtml, domain, q)

def href(a):
    return a['href'].encode('utf-8')

def bannerItem(h, soup = True):
    if soup:
        h = h.text.encode('utf-8')
    h = '[COLOR FFDEB887]【%s】[/COLOR]' % h
    return (h,)

def linkItem(a, mode, link = True, baseurl = '', title = ''):
    if title:
        name = title.encode('utf-8')
    else:
        name = a.text.encode('utf-8')
    if link:
        name = '[COLOR FF1E90FF]%s[/COLOR]' % (name)
    return (name, mode, baseurl + href(a))

def singerItem(a):
    name = a.text.encode('utf-8')
    mode = MODE_SINGER
    url = href(a)
    icon = getSingerIcon(url)
    return (name, mode, url, icon)

def playItem(a):
    name = a.text.encode('utf-8')
    mode = MODE_PLAYLIST
    url = href(a)
    icon = ''
    d = {'title': name}
    return (name, mode, url, icon, d)

def songItem(title, url, artist, album, icon):
    title = title.encode('utf-8')
    mode = MODE_SONG
    artist = artist.encode('utf-8')
    album = album.encode('utf-8')
    d = {'title': title, 'artist': artist, 'album': album}
    url = url.encode('utf-8')
    icon = icon.encode('utf-8')
    if artist:
        name = '%s - %s' % (artist, title)
    else:
        name = title
    return (name, mode, url, icon, d)

def pageList(tree, mode, lists, baseurl = ''):
    soup = tree.find('div', {'class': ['cPages', 'pages']})
    if soup:
        a = soup.find('a', text=['上一页', '«上一页'])
        if a: lists.insert(0, linkItem(a, mode, True, baseurl))
        a = soup.find('a', text=['下一页', '下一页»'])
        if a: lists.append(linkItem(a, mode, True, baseurl))
    return lists

def albumList(soup):
    lists = []
    mode = MODE_ALBUM
    if soup:
        for li in soup.find_all('li'):
            albumName = li.find('span', {'class': 'albumName'})
            if not albumName: continue
            singerName = li.find('span', {'class': 'singerName'})
            albumDate = li.find('span', {'class': 'albumDate'})
            albumPic = li.find('img', {'class': 'albumPic'})
            name = albumName.text
            if singerName:
                name = '%s - %s' % (name, singerName.text)
            if albumDate:
                name = '%s (%s)' % (name, albumDate.text)
            name = name.encode('utf-8')
            a = li.find('a', {'class': 'albumPlay'})
            url = href(a)
            icon = ''
            if albumPic:
                icon = albumPic['src']
            lists.append((name, mode, url, icon))
    return lists

def singerList(soup):
    lists = []
    for i in soup.find_all(['a', 'li'], {'class': 'singerName'}):
        a = i.a if i.name == 'li' else i
        lists.append(singerItem(a))
    return lists

def songList(soup):
    lists = []
    for li in soup.find_all('li'):
        lists.append(playItem(li.a))
    return lists

def getSongList(url):
    lists = []
    tree = request(url)
    if tree:
        soup = tree.find('div', {'class': 'songList'})
        for i in soup.find_all('ul'):
            lists += songList(i)
        mode = MODE_SONGLIST
        lists = pageList(tree, mode, lists)
    else:
        lists.append(bannerItem('该歌手不存在或者由于版权到期而下线!', False))
    return lists

def getAlbumList(url):
    lists = []
    tree = request(url, album = True)
    soup = tree.find('div', {'class': 'albumList'})
    lists += albumList(soup)
    mode = MODE_ALBUMLIST
    lists = pageList(tree, mode, lists)
    return lists

def getSingerList(url):
    lists = []
    tree = request(url)
    soup = tree.find('div', {'class': 'singerList'})
    for li in soup.find_all('li'):
        a = li.find('a', {'class': 'singerName'})
        if a:
            lists.append(singerItem(a))
    mode = MODE_SINGERLIST
    lists = pageList(tree, mode, lists)
    return lists

def getPlayList(url):
    lists = []
    resHttpData = request(url, False)
    match = re.search("\[\[.*?\]\]", resHttpData)
    if match:
        result = json.loads(unescape(match.group()))
        for i in result:
            artist, title, album, url = i[1:8:2]
            icon = i[8]
            lists.append(songItem(title, url, artist, album, icon))
    else:
        lists.append(bannerItem('该歌曲不存在或者由于版权到期而下线!', False))
    return lists

def getRand():
    lists = []
    resHttpData = request(randHtml, False)
    match = re.search("Jsonp\((.*?)\)    </script>", resHttpData)
    if not match: return
    info = json.loads(match.group(1))
    result = info.get('results', [])
    for i in result:
        title = i['song_name']
        artist = i['singer_name']
        album = i['album_name']
        url = i['song_filepath']
        icon = i['album_cover']
        lists.append(songItem(title, url, artist, album, icon))
    return lists

def getSingerGroup(url = SingerHtml):
    lists = []
    tree = request(url)
    soup = tree.find_all('div', {'class':'group-menu-component'})
    for i in soup:
        for a in i.find_all('a'):
            url = href(a)
            if url == '#':
                item = bannerItem(a)
            else:
                item = linkItem(a, MODE_SINGER_ALL, False)
            lists.append(item)
    return lists

def getSingerIcon(url, size = 210):
    match = re.search("singer_(.*?)\.html", url)
    if not match: return
    num = match.group(1)
    return "%s%d_%s.jpg" % (imgBaseHtml, size, num)

def getRankIcon(url):
    icon = webHtml + rankImgBaseHtml + url.replace('/rank', '').replace('.html', '.png')
    return icon

def getSingerAll(url = SingerHtml):
    lists = []
    tree = request(url)
    soup = tree.find('div', {'class': 'singerCommend'})
    if soup:
        lists.append(bannerItem('推荐', False))
    soup = soup.find_all('a', {'class': 'singerName'})
    for a in soup:
        lists.append(singerItem(a))
    soup = tree.find_all('ul', {'class': 'allSinger'})
    if soup:
        lists.append(bannerItem('全部', False))
    for i in soup:
        for a in i.find_all('a'):
            lists.append(singerItem(a))
    return lists

def getSinger(url):
    lists = []
    tree = request(url, album = True)
    if tree:
        soup = tree.find('dl', {'class': 'singerInfo'})
        a = soup.find('a', {'class': 'allSong'})
        if a:
            lists.append(linkItem(a, MODE_SONGLIST))
        a = soup.find('a', {'class': 'allAlbum'})
        if a:
            lists.append(linkItem(a, MODE_ALBUMLIST))
        soup = tree.find('table', {'class': 'songList'})
        h = soup.find_previous_sibling().h3
        lists.append(bannerItem(h))
        for a in soup.find_all('a', {'class': 'songName'}):
            lists.append(playItem(a))
        soups = tree.find_all('div', {'class': 'albumList'})
        for soup in soups:
            h = soup.find_previous_sibling().h3
            lists.append(bannerItem(h))
            lists += albumList(soup)
    else:
        lists.append(bannerItem('该歌手不存在或者由于版权到期而下线!', False))
    return lists

def getRank():
    lists = []
    tree = request(rankHtml)
    soup = tree.find('div', {'class': 'lbar'})
    for dl in soup.find_all('dl'):
        lists.append(bannerItem(dl.dt))
        for a in dl.dd.ul.find_all('a'):
            name = a.text.encode('utf-8')
            url = href(a)
            icon = getRankIcon(url)
            if '唱片' in name or '专辑' in name: mode = MODE_ALBUMLIST
            elif '歌手' in name: mode = MODE_SINGERLIST
            else: mode = MODE_SONGLIST
            lists.append((name, mode, url, icon))
    return lists

def getTagList(url):
    lists = []
    if url == tagHtml: tag = 'allTagList'
    elif url == genreHtml: tag = 'allGenre'
    else: return
    tree = request(url)
    soup = tree.find('div', {'class': tag})
    for dl in soup.find_all('dl'):
        lists.append(bannerItem(dl.dt))
        for a in dl.find_all('a'):
            lists.append(linkItem(a, MODE_TAG, False))
    return lists

def tagHeadList(soup, mode):
    head = soup.find_previous_sibling()
    if head:
        return [linkItem(head.p.a, mode), bannerItem(head.h3)]
    return []

def getTag(url):
    lists = []
    tree = request(url, album = True)
    if tree:
        soups = tree.find_all('div', {'class': [MODE_SONGLIST, MODE_ALBUMLIST, MODE_SINGERLIST]})
        for soup in soups:
            className = soup['class'][0]
            lists += tagHeadList(soup, className)
            func = globals()[className]
            lists += func(soup)
    return lists

def getSearchList(url):
    lists = []
    mode = MODE_SEARCH_LIST
    tree = request(url)
    if tree:
        soup = tree.find('div', {'class': 'nav_center'})
        if soup:
            soup = soup.find_all('li', {'class': ['type_song', 'type_album', 'type_singer']})
            for li in soup:
                if li.span.text != '(0)':
                    lists.append(linkItem(li.a, mode, True, searchHtml, title=li.text))
        soup = tree.find('div', {'class': 'songList'})
        if soup:
            soup = soup.table.tbody
            for td in soup.find_all('td', {'class': 'song'}):
                lists.append(playItem(td.a))
        soup = tree.find('ul', {'class': 'albumList'})
        if soup:
            lists += albumList(soup)
        soups = tree.find_all('div', {'class': 'singerList'})
        for soup in soups:
            lists += singerList(soup)
        baseurl = url.split('?')[0]
        lists = pageList(tree, mode, lists, baseurl)
    return lists

def getList(mode, url):
    l = []

    if mode == MODE_MENU:
        l = getMenu()
    elif mode == MODE_SONGLIST:
        l = getSongList(url)
    elif mode == MODE_ALBUMLIST:
        l = getAlbumList(url)
    elif mode == MODE_ALBUM:
        l = getPlayList(url)

    elif mode == MODE_SINGERLIST:
        l = getSingerList(url)
    elif mode == MODE_SINGER_GROUP:
        l = getSingerGroup()
    elif mode == MODE_SINGER_ALL:
        l = getSingerAll(url)
    elif mode == MODE_SINGER:
        l = getSinger(url)

    elif mode == MODE_RAND:
        l = getRand()
    elif mode == MODE_RANK:
        l = getRank()

    elif mode == MODE_TAG_LIST:
        l = getTagList(url)
    elif mode == MODE_TAG:
        l = getTag(url)
    elif mode == MODE_SEARCH_LIST:
        l = getSearchList(url)

    return l

if __name__ == '__main__':
    for i in getSearchList('http://so.1ting.com/singer?q=dzq'):
        print i
