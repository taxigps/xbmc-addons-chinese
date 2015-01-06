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

def request(url):
    url = webHtml + url
    req = urllib2.Request(url)     # create one connection
    response = urllib2.urlopen(req)      # get the response        
    resHttpData = response.read()        # get all the webpage html data in string 
    return resHttpData

def getSongUrl(url):
    if url:
        req = urllib2.Request(songBasehtml + url)
        req.add_header("Cookie", "PIN=cnGQFFSRmPRxcDj2aUSnAg==")
        url = urllib2.urlopen(req).geturl()
    return url

def getSongAddr(audioUrl):
    resHttpData = request(audioUrl).replace('\r\n', '')
    match = re.findall("\[(\[.*?\])\]", resHttpData)
    if not match: return
    info = json.loads(unescape(match[0]))
    d = {}
    d['artist'] = info[1].encode('utf-8')
    d['title'] = info[3].encode('utf-8')
    d['album'] = info[5].encode('utf-8')
    d['icon'] = info[8].encode('utf-8')
    d['url'] = getSongUrl(info[7].encode('utf-8'))
    return d

def getRandList():
    resHttpData = request(randHtml)
    match = re.findall("Jsonp\((.*?)\)    </script>", resHttpData)[0]
    info = json.loads(match)
    result = info.get('results', [])
    songList = []
    for i in result:
        d = {}
        d['artist'] = i['singer_name'].encode('utf-8')
        d['title'] = i['song_name'].encode('utf-8')
        d['album'] = i['album_name'].encode('utf-8')
        d['icon'] = i['album_cover'].encode('utf-8')
        d['song_filepath'] = i['song_filepath'].encode('utf-8')
        songList.append(d)
    return songList

def getSingerGroup():
    resHttpData = request(SingerHtml)
    tree = BeautifulSoup(resHttpData)
    soup = tree.find_all('div', {'class':'group-menu-component'})
    lists = []
    for i in soup:
        for a in i.find_all('a'):
            lists.append((a['href'].strip('#'), a.text.encode('utf-8')))
    return lists

def getSingerIcon(url, size = 210):
    num = re.findall("singer_(.*?)\.html", url)[0]
    return "%s%d_%s.jpg" % (imgBaseHtml, size, num)

def getSingerList(url):
    resHttpData = request(url)
    tree = BeautifulSoup(resHttpData)
    singerList = []
    soup = tree.find('div', {'class': 'singerCommend'})
    soup = tree.find_all('a', {'class': 'singerName'})
    if soup:
        singerList.append(('', '推荐'))
    for a in soup:
        d = (a['href'], a.text)
        singerList.append(d)
    soup = tree.find_all('ul', {'class':'allSinger'})
    singerMatch = re.compile('<a href="([\s\S]*?)">([\s\S]*?)</a></li>', re.DOTALL)
    if soup:
        singerList.append(('', '全部'))
    for i in soup:
        singerList += singerMatch.findall(unescape(str(i)))      #get the listitem of all singer
    return singerList

def getSongList(pUrl, page = 1):
    paramSinger = re.findall("singer_(.*?)\.html", pUrl)[0] #/singer/b6/singer_2299.html
    UrlSinger = "/singer/%s/song/%d/index.html" % (paramSinger, page)   # get the url of the singer's songs
    resHttpData = request(UrlSinger)
    songMatch = re.compile('<li><input name="checked" type="checkbox" value="[\s\S]*?"/><a href="([\s\S]*?)" target="_1ting" title="[\s\S]*?">([\s\S]*?)</a></li>', re.DOTALL)
    songList = songMatch.findall(resHttpData)  # get the listitem of all song's id, the id of song is used to find the song, use the id to find the song when play the song 
    if '上一页' in resHttpData:          # this isn't the first page, has prior page
        songList.insert(0, ('-100','上一页'))              # add the prior page in songlist
    if '下一页' in resHttpData:          # this isn't the first page, has prior page
        songList.append(('-300', '下一页'))                 
    return songList

if __name__ == '__main__':
    getSingerList(SingerHtml)
    #print getSongList('/singer/b6/singer_2299.html')
