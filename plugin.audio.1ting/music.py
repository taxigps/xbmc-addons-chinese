#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, re, json
from bs4 import BeautifulSoup
from xml.sax.saxutils import unescape

webHtml = "http://www.1ting.com"
SingerHtml = "/group.html"
#songJsBaseHtml = "/json2010_"
songBasehtml = "http://f.1ting.com"
randHtml = "/rand.php"
imgBaseHtml = "http://img.1ting.com/images/singer/s"
rankHtml = "/rank.html"

MODE_NONE = -1
MODE_MENU = 0

MODE_SINGER_GROUP = 1
MODE_SINGER_LIST = 2
MODE_SINGER = 3
MODE_ALBUM = 5
MODE_SONG = 7
MODE_SONG_ITEM = 6

MODE_RAND = 11

MODE_RANK = 21
MODE_RANK_SONG = 22
MODE_RANK_SINGER = 23
MODE_RANK_ALBUM = 24

#name, mode, url, icon
menu = [('歌手', MODE_SINGER_GROUP), 
        ('随便一听', MODE_RAND), 
        ('排行榜', MODE_RANK)]

def hyperlink(s):
    return '[COLOR FF1E90FF]%s[/COLOR]' % s

def banner(s):
    return '[COLOR FFDEB887]【%s】[/COLOR]' % s

def getMenu():
    return menu

def isFolder(mode):
    return mode != MODE_NONE

def request(url, soup = True):
    if not url.startswith('http'): url = webHtml + url
    print('request', url)
    req = urllib2.Request(url)           # create one connection
    response = urllib2.urlopen(req)      # get the response
    if not response: return
    cont = response.read()        # get all the webpage html data in string
    response.close()
    return BeautifulSoup(cont, 'html.parser') if soup else cont

def getSongUrl(url):
    if not url: return
    req = urllib2.Request(songBasehtml + url)
    req.add_header("Cookie", "PIN=cnGQFFSRmPRxcDj2aUSnAg==")
    url = urllib2.urlopen(req).geturl()
    return url

def getSongList(url):
    lists = []
    resHttpData = request(url, False)
    match = re.search("\[\[.*?\]\]", resHttpData)
    if not match: return
    result = json.loads(unescape(match.group()))
    for info in result:
        name = info[3].encode('utf-8')
        url = info[7].encode('utf-8')
        icon = info[8].encode('utf-8')
        d = {}
        d['artist'] = info[1].encode('utf-8')
        d['title'] = name
        d['album'] = info[5].encode('utf-8')
        lists.append((name, MODE_SONG_ITEM, url, icon, d))
    return lists

def getRand():
    lists = []
    resHttpData = request(randHtml, False)
    match = re.search("Jsonp\((.*?)\)    </script>", resHttpData)
    if not match: return
    info = json.loads(match.group(1))
    result = info.get('results', [])
    for i in result:
        name = i['song_name'].encode('utf-8')
        icon = i['album_cover'].encode('utf-8')
        url = i['song_filepath'].encode('utf-8')
        d = {}
        d['title'] = name
        d['artist'] = i['singer_name'].encode('utf-8')
        d['album'] = i['album_name'].encode('utf-8')
        lists.append((name, MODE_SONG_ITEM, url, icon, d))
    return lists

def getSingerGroup():
    lists = []
    tree = request(SingerHtml)
    soup = tree.find_all('div', {'class':'group-menu-component'})
    for i in soup:
        for a in i.find_all('a'):
            name = a.text.encode('utf-8')
            url = a['href']
            mode = MODE_SINGER_LIST
            if url == '#':
                name = banner(name)
                mode = MODE_NONE
            lists.append((name, mode, url))
    return lists

def getSingerIcon(url, size = 210):
    match = re.search("singer_(.*?)\.html", url)
    if not match: return
    num = match.group(1)
    return "%s%d_%s.jpg" % (imgBaseHtml, size, num)

def getSingerList(url = SingerHtml):
    lists = []
    tree = request(url)
    soup = tree.find('div', {'class': 'singerCommend'})
    soup = tree.find_all('a', {'class': 'singerName'})
    if soup:
        lists.append((banner('推荐'),))
    for a in soup:
        url = a['href']
        icon = getSingerIcon(url)
        lists.append((a.text.encode('utf-8'), MODE_SINGER, url, icon))
    soup = tree.find_all('ul', {'class': 'allSinger'})
    if soup:
        lists.append((banner('全部'),))
    for i in soup:
        for a in i.find_all('a'):
            lists.append((a.text.encode('utf-8'), MODE_SINGER, a['href']))
    return lists

def addPages(soup, mode, lists):
    if soup:
        a = soup.find('a', text='上一页')
        if a: lists.insert(0, (hyperlink(a.text.encode('utf-8')), mode, a['href']))
        a = soup.find('a', text='下一页')
        if a: lists.append((hyperlink(a.text.encode('utf-8')), mode, a['href']))
    return lists

def getSingerSong(url):
    match = re.search("singer_(.*?)\.html", url) #/singer/b6/singer_2299.html
    if match:
        url = "/singer/%s/song/" % (match.group(1))   # get the url of the singer's songs
    lists = []
    tree = request(url)
    soup = tree.find('div', {'class': 'songList'})
    for i in soup.find_all('ul'):
        for a in i.find_all('a'):
            lists.append((a.text.encode('utf-8'), MODE_SONG, a['href']))
    soup = soup.find_next_sibling()
    mode = MODE_SINGER
    lists = addPages(soup, mode, lists)
    return lists

def getRank():
    lists = []
    tree = request(rankHtml)
    soup = tree.find('div', {'class': 'lbar'})
    for dl in soup.find_all('dl'):
        name = banner(dl.dt.text.encode('utf-8'))
        lists.append((name,))
        for a in dl.dd.ul.find_all('a'):
            name = a.text.encode('utf-8')
            if '唱片' in name or '专辑' in name: mode = MODE_RANK_ALBUM
            elif '歌手' in name: mode = MODE_RANK_SINGER
            else: mode = MODE_RANK_SONG
            lists.append((name, mode, a['href']))
    return lists

def getRankSong(url):
    lists = []
    tree = request(url)
    soup = tree.find('div', {'class': 'songList'})
    for i in soup.find_all('ul'):
        for a in i.find_all('a'):
            lists.append((a.text.encode('utf-8'), MODE_SONG, a['href']))
    return lists

def getRankAlbum(url):
    lists = []
    tree = request(url)
    soup = tree.find('div', {'class': 'albumList'})
    soup = soup.find('ul', {'class': 'albumUL'})
    for li in soup.find_all('li'):
        title = '%s - %s (%s)' % (
                li.find('span', {'class': 'albumName'}).text,
                li.find('span', {'class': 'singerName'}).text,
                li.find('span', {'class': 'albumDate'}).text)
        a = li.find('a', {'class': 'albumPlay'})
        icon = li.find('img', {'class': 'albumPic'})['src']
        lists.append((title.encode('utf-8'), MODE_ALBUM, a['href'], icon))
    soup = soup.find_next_sibling()
    mode = MODE_RANK_ALBUM
    lists = addPages(soup, mode, lists)
    return lists

def getRankSinger(url):
    lists = []
    tree = request(url)
    soup = tree.find('div', {'class': 'singerList'})
    soup = soup.find('ul', {'class': 'singerUL'})
    for li in soup.find_all('li'):
        a = li.find('a', {'class': 'singerName'})
        url = a['href']
        icon = getSingerIcon(url)
        lists.append((a.text.encode('utf-8'), MODE_SINGER, url, icon))
    soup = soup.find_next_sibling()
    mode = MODE_RANK_SINGER
    lists = addPages(soup, mode, lists)
    return lists

def getList(pMode, url):
    l = []
    if pMode == MODE_MENU:
        l = getMenu()
    elif pMode == MODE_SINGER_GROUP:
        l = getSingerGroup()
    elif pMode == MODE_SINGER_LIST:
        l = getSingerList(url)
    elif pMode == MODE_SINGER:
        l = getSingerSong(url)
    elif pMode == MODE_RAND:
        l = getRand()
    elif pMode == MODE_RANK:
        l = getRank()
    elif pMode == MODE_RANK_SONG:
        l = getRankSong(url)
    elif pMode == MODE_RANK_SINGER:
        l = getRankSinger(url)
    elif pMode == MODE_RANK_ALBUM:
        l = getRankAlbum(url)
    elif pMode == MODE_ALBUM:
        l = getSongList(url)
    return l

if __name__ == '__main__':
    for i in getSingerAlbum("/singer/502/album/"):
        print i
