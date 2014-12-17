# -*- coding: utf-8 -*-

import xbmc, xbmcgui, urllib, xbmcplugin, sys, urllib2, re
# This Python file uses the following encoding: utf-8

mainDirec = ['歌手'] 
webHtml = "http://www.1ting.com"
SingerHtml = "http://www.1ting.com/group.html" 
songJsBaseHtml = "http://www.1ting.com/json2010_"
songBasehtml = "http://f.1ting.com"

def log(txt):     #record the log
    message = '%s: %s' % ('qij added this', txt)
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


def addMainDerec():        #add top directory
    totalItems = len(mainDirec)
    for name in mainDirec:
       li = xbmcgui.ListItem(name)
       u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)
       xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def addSecDerec(name):           #add the second direcdory, get the directory name from the web page, the directory deal with the singers
    if name == '歌手':
        req = urllib2.Request(SingerHtml)    # create one connection
        response = urllib2.urlopen(req)      # get the response
        resHttpData = response.read()           # get all the webpage html data in string
        singerMatch = '<div class="singerList">([\s\S]*?)</div>'
        singerList = re.compile(singerMatch, re.DOTALL).findall(resHttpData)   #get the listitem includes all singer
        allSinger = ''.join(singerList)    #create one string includes all singers
        singerMatch = '<li><a href=[\s\S]*?>([\s\S]*?)</a></li>'    
        singerList = re.compile(singerMatch, re.DOTALL).findall(allSinger)      #get the listitem of all singer
        singerWebMatch = '<li><a href="([\s\S]*?)">[\s\S]*?</a></li>'    
        singerWebList = re.compile(singerWebMatch, re.DOTALL).findall(allSinger)   # get the listitem of all singer web address
        if len(singerList) <> len(singerWebList):         # the quantity of singer not equals to the web address
            log("some singer information is wrong")
            return
        for i in range(len(singerList)):
            li = xbmcgui.ListItem(singerList[i])
            u = sys.argv[0]+"?mode=2&name="+urllib.quote_plus(name) + "&url=" + singerWebList[i] + "&page=1"
            xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True,len(singerList))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))                   
    if name == '专辑':
        log("zhuanji")
        
def addThirdDerec(name, pUrl, page):           #add the third direcdory, get the directory name from the web page
    if name == '歌手':                   # deal with all the songs of the singer
        indexF = pUrl.find('singer_') + 7
        indexL = pUrl.find('.html')
        paramSinger = pUrl[indexF:indexL]
        UrlSinger = webHtml + '/singer/' + paramSinger + '/song/' + str(page) + '/index.html'   # get the url of the singer's songs
        req = urllib2.Request(UrlSinger)     # create one connection
        response = urllib2.urlopen(req)      # get the response        
        resHttpData = response.read()        # get all the webpage html data in string       
        songMatch = '<li><input name="checked" type="checkbox" value="[\s\S]*?"/><a href="[\s\S]*?" target="_1ting" title="[\s\S]*?">([\s\S]*?)</a></li>'
        songList = re.compile(songMatch, re.DOTALL).findall(resHttpData)   # get the songs name of current page               
        songWebIDMatch = '<li><input name="checked" type="checkbox" value="[\s\S]*?"/><a href="([\s\S]*?)" target="_1ting" title="[\s\S]*?">[\s\S]*?</a></li>'    
        songWebIDList = re.compile(songWebIDMatch, re.DOTALL).findall(resHttpData)  # get the listitem of all song's id, the id of song is used to find the song, use the id to find the song when play the song 
        if len(songList) <> len(songWebIDList):                              # the quantity not equals to the web address
            log("some singer information is wrong")
            return
        resHttpData.replace('\r\n', '')
        if resHttpData.find('上一页') <> -1:          # this isn't the first page, has prior page
            songList.insert(0, '上一页')              # add the prior page in songlist
            songWebIDList.insert(0, str(-100))                # add the prior web address id, to avoid system failer later
        if resHttpData.find('下一页') <> -1:          # this isn't the first page, has prior page
            songList.append('下一页')                 
            songWebIDList.append(str(-300))           # add the next web address id, to avoid system failer later
        for i in range(len(songList)):
            li = xbmcgui.ListItem(str(songList[i]))     # get the song name, or just the prior or next page
            u = sys.argv[0]+"?mode=3&name="+urllib.quote_plus(name) + "&url=" + songWebIDList[i] + "&page=0&songName=" + songList[i]     # set the song play 'address' 
            isFolder = False
            if (str(songList[i]) == '上一页'):     # if it's the prior page, deal with the prior page directory, if user click the prior page
                u = sys.argv[0]+"?mode=2&name="+urllib.quote_plus(name) + "&url=" + pUrl + "&page=" + str(page - 1)                
                isFolder = True
            if (str(songList[i]) == '下一页'):     # if it's the next page, deal with the next page directory, if user click the next page
                u = sys.argv[0]+"?mode=2&name="+urllib.quote_plus(name) + "&url=" + pUrl + "&page=" + str(page + 1)  
                isFolder = True      
            xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,isFolder,len(songList))
        xbmcplugin.endOfDirectory(int(sys.argv[1])) 
    if name == '专辑':
        log("zhuanji")   
        
def playAudio(audioUrl, songName):           # play the song according the part url information
    UrlPlaySong = webHtml + audioUrl   # get the url of playing song address
    req = urllib2.Request(UrlPlaySong)     # create one connection
    response = urllib2.urlopen(req)      # get the response        
    resHttpData = response.read()        # get all the webpage html data in string 
    resHttpData.replace('\r\n', '')
    songMatch = '''"[^"]*wma"'''
    match = re.compile(songMatch, re.DOTALL).search(resHttpData)
    if match:
        songAddress = match.group()
        songAddress = songAddress.replace('"', '')
        songAddress = songAddress.replace('\\', '')     # delete the special charater
        songAddress = songBasehtml + songAddress        # get the whole song download address
        listitem = xbmcgui.ListItem(songName)
        log("songname is " + str(songName))
        listitem.setInfo(type="Music",infoLabels={"Title":songName})
        xbmc.Player().play(songAddress, listitem)            
        
def get_params():         # get part of the url, help to judge the param of the url, direcdory
    param = {}            # create the dictionary, not list
    tailParam = sys.argv[2]
    if len(tailParam) > 2:           #has some other para
        tempParam = tailParam.replace("?", "")    #delete the character "?"
        paramList = tempParam.split("&")   
        for i in range(len(paramList)):
            tempParam = paramList[i].split("=") 
            if len(tempParam) == 2:
                param[tempParam[0]] = tempParam[1]     #fill the dictionary    
    return param

pMode = None
pName = None
partUrl = None
pPage = 1
nameOfSong = None

paramlist = get_params()
try:
    pName = urllib.unquote_plus(paramlist["name"])
except:
    pass
try:
    pMode = int(paramlist["mode"])
except:
    pass
try:
    partUrl = urllib.unquote_plus(paramlist["url"])
except:
    pass
try:
    pPage = int(paramlist["page"])
except:
    pass
try:
    nameOfSong = urllib.unquote_plus(paramlist["songName"])
except:
    pass




if pMode == None:
    addMainDerec()
if pMode == 1:
    addSecDerec(pName)
if pMode == 2:
    addThirdDerec(pName, partUrl, pPage)
if pMode == 3:
    playAudio(partUrl, nameOfSong)

    

    
    

