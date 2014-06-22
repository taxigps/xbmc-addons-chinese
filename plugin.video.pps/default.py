# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import urllib2, urllib, re, sys, os
import zipfile
import ChineseKeyboard

########################################################################
# PPS影音(PPS.tv)
# Version 1.1.10 2014-02-16 (cmeng)
# - Skip prompt user for single selectable item
# - Provide second retrial and remove DeprecationWarning in read_xml

# See changelog.txt for previous history
########################################################################

# Plugin constants 
__addonname__ = "PPS影音(PPS.tv)"
__addonid__   = "plugin.video.pps"
__addon__ = xbmcaddon.Addon(id=__addonid__)
__addonicon__ = os.path.join( __addon__.getAddonInfo('path'), 'icon.png' )
__settings__  = xbmcaddon.Addon(id=__addonid__)
__cwd__       = xbmc.translatePath( __settings__.getAddonInfo('path') )

RESOURCES_PATH = os.path.join(__cwd__ , "resources" )
sys.path.append( os.path.join( RESOURCES_PATH, "lib" ) )
import etree as etree
from etree import ElementTree

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
COLOR_LIST = ['[COLOR FFFF0000]','[COLOR FF00FF00]','[COLOR FFFFFF00]','[COLOR FF00FFFF]','[COLOR FFFF00FF]']
ListOmit ="爱频道 - 我的频道"

#REMOTE_DBG = True
#
## append pydev remote debugger
#if REMOTE_DBG:
#    # Make pydev debugger works for auto reload.
#    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
#    try:
#        import pysrc.pydevd as pydevd
#    # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
#        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
#    except ImportError:
#        sys.stderr.write("Error: " +
#            "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
#        sys.exit(1)

##################################################################################
# Routine to fetech url site data using Mozilla browser
# - deletc '\r|\n' for easy re.compile
# - do not delete '\t', xml uses tabe for string seperation
# - do not delete ' ' i.e. <space> as some url include spaces
# - unicode with 'replace' option to avoid exception on some url
# - translate to utf8 if possible
##################################################################################
def getHttpData(url):
    print "getHttpData: " + url
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    req.add_header("Referer","www.soso.com")
    try:
        response = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        httpdata = e.read()
    except urllib2.URLError, e:
        httpdata = "IO Timeout Error"
    else:
        httpdata = response.read()
        response.close()

    httpdata = re.sub('\r|\n', '', httpdata)
    match = re.compile('<meta.+?charset=["]*(.+?)"').findall(httpdata)
    if len(match):
        charset = match[0].lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = unicode(httpdata, charset,'replace').encode('utf8')
    return httpdata

##################################################################################
# Routine to fetch PPS video file in xml.zip format
# GENERAS_URL = 'http://list1.ppstream.com/class/generas.xml.zip'
# SUB_URL = 'http://list1.pps.tv/class/%d.xml.zip'
# MOVIE_URL = 'http://list1.ppstv.com/schs/%d.xml.zip'
# SEARCH_URL = 'http://listso.ppstream.com/search.php?acp=936&w='
# http://api.pps.tv/video/get_resource.php?tvid=394427&app_key=10007&app_secret=d073c391368e4fd4e49813e6d276ff82&stat_city=&stat_client=client&stat_isp=
# http://api.tuijian.pps.tv/api.php?act=nextplay&client=pc&uid=2028212&scene=autoplay&fistinstall=1
##################################################################################
def read_xml(id,type=1):
#   dialog = xbmcgui.Dialog()
    if type :
        #url= "http://list1.pps.tv/class/"+id+".xml.zip" #目录    
        #url= "http://list1.ppstream.com/class/"+id+".xml.zip" #目录    
        url= "http://list3.pps.tv/class/"+id+".xml.zip" #目录    
    else :
        #url= "http://list1.pps.tv/schs/"+id+".xml.zip" #文件列表    
        #url= "http://list1.ppstv.com/schs/"+id+".xml.zip" #文件列表    
        #url= "http://list3.ppstv.com/schs/"+id+".xml.zip" #文件列表    
        url= "http://list3.pps.tv/schs/"+id+".xml.zip" #文件列表    
    print 'xml_zip: ' + url
    
    try:
        dfile=urllib.urlretrieve(url, 'tmpxml.zip')
        z = zipfile.ZipFile(dfile[0],'r')    
    except: # second trial
        dfile=urllib.urlretrieve(url, 'tmpxml.zip')
        z = zipfile.ZipFile(dfile[0],'r')
        
    text = z.read(id+".xml")
    text = unicode(text, 'gb18030','replace').encode('utf8')
    #text = text.decode('GB18030').encode('UTF-8')
    text = text.replace('gb18030', 'utf-8')
    text = text.replace('GB18030', 'utf-8')
    return(text)

##################################################################################
# Routine to fetch & build PPS 客户端 main menu
# 主目录
##################################################################################
def menu_main(id,category=''):
    text = read_xml(id,1)
    root = ElementTree.fromstring(text)

    elemroot = root.iter('Gen')
    j = 0
    for elem in elemroot:
        name = elem.attrib['name']
        if re.search(ListOmit, name.encode('utf-8')): continue
        id = elem.attrib['id']
        se = elem.attrib['enableSearch']
        if se=="1":
            catType = elem.attrib['search'][:-1].encode('utf-8') #change unicode to str
        else:
            catType = ""
        orderID = int(elem.attrib['orderid'][:5]) #xbmc cannot sort >10000

        j += 1
        li=xbmcgui.ListItem('[COLOR FF00FF00][ ' + name + ' ][/COLOR]')
        li.setInfo( type="Video", infoLabels={"Title":name, "Episode":orderID})
        u=sys.argv[0]+"?mode=gen&name="+urllib.quote_plus(name.encode('utf-8'))+"&id="+id+"&category="+urllib.quote_plus(catType)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)

    #添加一个“PPS搜索”
    li = xbmcgui.ListItem('[COLOR FFFF00FF]PPS.TV 网络电视[/COLOR][COLOR FFFFFF00] (主页) [/COLOR][COLOR FF00FFFF]共计：'+str(j)+'[/COLOR]【[COLOR FF00FF00]点此输入搜索内容[/COLOR]】')
    li.setInfo(type="Video", infoLabels={"Title":name, "Episode":1})
    u=sys.argv[0]+"?mode=search&name="+urllib.quote_plus('PPS搜索')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

##################################################################################
# 次目录
##################################################################################
def menu_sub(name,id,category):
    text = read_xml(id,1)
    root = ElementTree.fromstring(text)

    # Fetch & build video titles list for user selection, highlight user selected filter  
    eList='[COLOR FF00FF00]类型:全部[/COLOR]'
    if category:
        catFilter = updateFilter(category, True)
        eList = ''
        sfltr=[]
        xlist = catFilter.split(';')
        for i in range(0, len(xlist)):
            eList += COLOR_LIST[i%5]+xlist[i]+'[/COLOR]|'
            item = xlist[i].split(':')[1]
            if item != '全部':
                #sfltr.append(unicode(item,'utf-8'))
                sfltr.append(item)
        eList = eList[:-1]       

    j = 0
    image_en = __addon__.getSetting('image_en')
    elemroot = root.iter("Sub")
    for elem in elemroot:
        if category:
            catType = elem.attrib['search'].encode('utf-8') # convert unicode to str
            find = 1
            for ifltr in sfltr:
                if re.search(ifltr, catType) == None:
                    find = 0
                    break
            if find == 0: continue # search not match, skip to next item

        name = elem.attrib['name']
        p_id = elem.attrib['id']
        cnt = elem.attrib['op']
        
        try:
            p_url = elem.attrib['dj']
            continue
        except: dj=''

        try: p_url = elem.attrib['image']
        except: p_url=''
        try: tag = elem.attrib['tags']
        except: tag = ''
        try: on = int(get_params2(cnt)['on'])
        except: on = 1
        try: vm = float(get_params2(cnt)['vm'])
        except: vm = ''
        
        catShow=''
        if category:
            types = catType.decode('utf-8').split(';')
            for i in range(0, len(types)-2):
                catShow += types[i].split(':')[1]+';'
            catShow = catShow[:-1]
            
        catType = ''
        # category search not required at sub menu
        try:
            if elem.attrib['enableSearch2'] == '1':
                catType = elem.attrib['search'][:-1].encode('utf-8') #change unicode to str
        except:
            pass
        
        p_list='[COLOR FF00FF00]'+name+'[/COLOR][COLOR FF00FFFF] ['+str(on)+'][/COLOR]'
        if vm: p_list += '[COLOR FFFF00FF]['+str(vm)+'][/COLOR]'
        if not catType and tag: p_list += '[COLOR FFFFFF00]['+tag+'][/COLOR]'
        p_list += ' '+catShow
                
        if image_en == 'true':
            p_thumb=''
            if p_url: p_thumb = "http://image1.webscache.com/baike/haibao/navi/" + p_url
            li=xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        else:
            li=xbmcgui.ListItem(p_list)
  
        li.setInfo( type="Video", infoLabels={"Title":name, "count":on, "Rating":vm})
        u=sys.argv[0]+"?mode=sub&name="+name+"&id="+p_id+"&rating="+str(vm)+"&category="+urllib.quote_plus(catType)+"&thumb="+p_thumb
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
        j+=1 # increment only if everything is OK

    li = xbmcgui.ListItem(' [COLOR FFFF00FF]当前选择: [/COLOR][COLOR FFFFFF00]('+eList+') [/COLOR][COLOR FF00FFFF]共计：'+str(j)+'[/COLOR]【[COLOR FF00FF00]'+'按此选择'+'[/COLOR]】')
    li.setInfo( type="Video", infoLabels={"Title":name, "count":1000000000, "Rating":10.0})
    u=sys.argv[0]+"?mode=gen&id="+id+"&category="+category
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    #sort = [名称|评价|播放次数]
    sortOrder = __addon__.getSetting('sort')
    if sortOrder=='0':
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    elif sortOrder=='1':
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
    else:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)

##################################################################################
# 文件
##################################################################################
def menu_ch(name,id,category,rating,thumb):
    text = read_xml(id,0)
    root = ElementTree.fromstring(text)
    elemroot = root.iter("Ch")
    
    # Fetch & build video titles list for user selection, highlight user selected filter  
    #eList='[COLOR FF00FF00]类型:全部[/COLOR]'
    eList='[COLOR FF00FF00]'+name+'[/COLOR]'
    if category:
        catFilter = updateFilter(category, False)
        #catFilter = category
        #category=""
        eList = ''
        sfltr=[]
        xlist = catFilter.split(';')
        for i in range(0, len(xlist)):
            eList += COLOR_LIST[i%5]+xlist[i]+'[/COLOR]|'
            item = xlist[i].split(':')[1]
            if item != '全部':
                #sfltr.append(unicode(item,'utf-8'))
                sfltr.append(item)
        eList = eList[:-1]       

    i = 0
    image_en = __addon__.getSetting('image_en')

    # required if series contains zero item.
    p_order=1000

    for node in elemroot:
        elemtop = node.find('ID')
        if category:
            catType = elemtop.attrib['search'].encode('utf-8') # convert unicode to str
            find = 1
            for ifltr in sfltr:
                if re.search(ifltr, catType) == None:
                    find = 0
                    break
            if find == 0: continue # search not match, skip to next item
        
        CHON=0
        CHBKID=""
        if rating: CHBKVM=float(rating)
        else: CHBKVM=0
        year='1990'
        p_order=1000

        #elemtop = node.find('ID')
        CHID=elemtop.attrib['ID']

        try: CHON=int(node.attrib['ON'])               
        except: pass
        try: p_url = elemtop.attrib['image']
        except: p_url=''
        try: p_order = int(elemtop.attrib['ordnum'])
        except: pass
        try: CHBKID=elemtop.attrib['BKID']
        except: pass
        try: CHBKVM=float(elemtop.attrib['VM'])
        except: pass
        try: Tag=elemtop.attrib['tag'].encode('utf-8')
        except: Tag=''

        try:
            cs=elemtop.attrib['search']
            yy=re.compile('.+?:.+?:.+?:(.+?);').findall(cs)
            # (类型):(动作,惊怵,犯罪,剧情;产地):(中国香港;年份):(2005); | 年份:80年代
            if yy: year=yy[0]
        except: pass
            
        elemtop = node.find("Name")
        CHName = elemtop.text
        if re.search('高清', Tag): CHName = '[COLOR FF00FFFF]['+CHName+'][/COLOR]'
        elif re.search('国语', Tag) or re.search('粤语', Tag):
             CHName = '[COLOR FFFFFF00]['+CHName+'][/COLOR]'
        #else: CHName = '[COLOR FF00FF00]['+CHName+'][/COLOR]'
        if CHBKVM: CHName += ' [COLOR FFFF00FF]['+str(CHBKVM)+'][/COLOR]'
        elemtop = node.find("URL")
        CHURL = elemtop.text
                  
        if image_en == 'true':
            p_thumb=''
            if p_url: p_thumb = "http://image1.webscache.com/baike/haibao/navi/" + p_url
            li=xbmcgui.ListItem(CHName, iconImage='', thumbnailImage=p_thumb)
        else:
            li=xbmcgui.ListItem(CHName)
        
        try: # some contains no CHURL
            li.setInfo( type="Video", infoLabels={"Title":CHName, "count": CHON, "Rating":CHBKVM, "CODE":CHBKID,"Year":year, "Episode":p_order})
            u=sys.argv[0]+"?mode=ch&name="+CHName+"&id="+CHID+"&url="+urllib.quote_plus(CHURL.encode('gb18030'))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,False)       
            i+=1 # increment only if everything is OK
        except: pass
        
    li = xbmcgui.ListItem('[COLOR FFFF00FF]当前选择: [/COLOR][COLOR FFFFFF00]('+eList+') [/COLOR][COLOR FF00FFFF]共计：'+str(i)+'[/COLOR]【[COLOR FF00FF00]'+'按此选择'+'[/COLOR]】')
    li.setInfo( type="Video", infoLabels={"Title":" ", "count":1000000, "Rating":10.0})
    u=sys.argv[0]+"?mode=sub&name="+name+"&id="+id+"&category="+category+"&rating="+rating+"&thumb="+thumb
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if p_order == 1000:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    else:  # sort episode
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

##################################################################################
# Routine to fetch user defined video list filter
# category:
# 类型:电子竞技,角色扮演,战争策略;产地:中国大陆,中国台湾,韩国,中国香港,美国,日本;
# 年份:2011,2010,2009,2008,2005,2001;
# 首字母:A,B,C,D,F,G,H,I,J,K,L,M,N,O,P,R,S,T,V,W,X,Y,Z,数字;
# 时长:30分钟以内,30分钟-60分钟,60分钟-90分钟,90分钟-120分钟,120分钟以上; 
##################################################################################
def updateFilter(category, subCatEn):
    change = False
    dialog = xbmcgui.Dialog()
    xlist = catlist = list = []
    catFilter =''
    
    xlist = category.split(';')
    for icat in xlist:
        cat = icat.split(':')
        if cat[0]=='时长': continue #skip 时长 selection

        catlist = cat[1].split(',')
        list = [x for x in catlist]
        list.insert(0, '全部')
#         if not subCatEn and cat[0] =='类型':
#             sel = 0 # return sub-category if filter allow
        if len(list) > 2: 
            sel = dialog.select(cat[0], list)
        else: # no user selectable, use default
            sel = 1
        if sel != -1:
            change = True
            catFilter += cat[0] +':'+ list[sel] + ';'
    return(catFilter[:-1])

##################################################################################
# Routine to search PPS based on user input string
##################################################################################
def Search(mname):
    keyboard = ChineseKeyboard.Keyboard('','输入所查影片中文信息-拼音或简拼(拼音首字母)')
    xbmc.sleep(1500)
    keyboard.doModal()
    keyword=keyboard.getText()
    
    url="http://listso.ppstream.com/search.php?acp=936&w="+urllib.quote_plus(keyword)
    text = getHttpData(url)
    text = unicode(text, 'gb18030','replace').encode('utf8')
    text = text.replace('gb18030', 'utf-8')
    text = text.replace('GB18030', 'utf-8')
 
    image_en = __addon__.getSetting('image_en')
    root = ElementTree.fromstring(text)
    #文件
    i = 0
    elemroot = root.iter("Ch")
    for node in elemroot:
        CHON=0
        CHBKID=""
        CHBKVM=0.0
        year='1990'

        elemtop = node.find('ID')
        CHID=elemtop.attrib['ID']

        try: CHON=int(node.attrib['ON'])               
        except: pass
        try: p_url = elemtop.attrib['image']
        except: p_url=''
        try: CHBKID=elemtop.attrib['BKID']
        except: pass
        try: CHBKVM=float(elemtop.attrib['VM'])
        except: pass

        try:
            cs=elemtop.attrib['search']
            yy=re.compile('.+?:.+?:.+?:(.+?);').findall(cs)
            if yy: year=yy[0]
        except: pass
            
        elemtop = node.find("Name")
        CHName = elemtop.text
        if CHBKVM and (CHBKVM > 0.01):
            CHName += ' [COLOR FFFF00FF]['+str(CHBKVM)+'][/COLOR]'
        elemtop = node.find("URL")
        CHURL = elemtop.text
                  
        if image_en == 'true':
            p_thumb=''
            if p_url: p_thumb = "http://image1.webscache.com/baike/haibao/navi/" + p_url
            li=xbmcgui.ListItem(CHName, iconImage='', thumbnailImage=p_thumb)
        else:
            li=xbmcgui.ListItem(CHName)
        
        try: # some contains no CHURL
            li.setInfo( type="Video", infoLabels={"Title":CHName, "count": CHON, "Rating":CHBKVM, "CODE":CHBKID,"Year":year})
            u=sys.argv[0]+"?mode=ch&name="+CHName+"&id="+CHID+"&url="+urllib.quote_plus(CHURL.encode('gb18030'))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,False)       
            i+=1 # increment only if everything is OK
        except: pass
            
    #次目录
    j = 0
    elemroot = root.iter("Gen")
    for elemx in elemroot:
        title = elemx.attrib['name']
        if re.search(ListOmit, title.encode('utf-8')): continue
        elemsub = elemx.iter("Sub")
        for elem in elemsub:
            j+=1
            name = elem.attrib['name']
            id = elem.attrib['id']
            cnt = elem.attrib['op']
        
            try: p_url = elem.attrib['image']
            except: p_url=''
            try: tag = elem.attrib['tags']
            except: tag = ''
            try: on = int(get_params2(cnt)['on'])
            except: on = 1
            try: vm = float(get_params2(cnt)['vm'])
            except: vm = ''
        
            catType = ''
            p_list=title+': '+'[COLOR FF00FF00]'+name+'[/COLOR][COLOR FF00FFFF] ['+str(on)+'][/COLOR]'
            if vm: p_list += '[COLOR FFFF00FF]['+str(vm)+'][/COLOR]'
                
            if image_en == 'true':
                p_thumb=''
                if p_url: p_thumb = "http://image1.webscache.com/baike/haibao/navi/" + p_url
                li=xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
            else:
               li=xbmcgui.ListItem(p_list)
  
            li.setInfo( type="Video", infoLabels={"Title":name, "count":on, "Rating":vm})
            u=sys.argv[0]+"?mode=sub&name="+name+"&id="+id+"&rating="+str(vm)+"&category="+urllib.quote_plus(catType)+"&thumb="+p_thumb
            xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
            
    #添加一个“PPS搜索”
    li = xbmcgui.ListItem('[COLOR FFFF00FF]当前搜索: [/COLOR][COLOR FFFFFF00]('+keyword+') [/COLOR][COLOR FF00FFFF]共计：'+str(i+j)+'[/COLOR]【[COLOR FF00FF00]'+'点此输入新搜索内容'+'[/COLOR]】')
    li.setInfo(type="Video", infoLabels={"Title":keyword, "Rating":10.0}) # Top of list
    u = sys.argv[0]+"?mode=search&name=" + urllib.quote_plus(keyword)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)

##################################################################################
# Routine to search PPS based on user input string
##################################################################################
def Searchx(mname):
    if (mname == "PPS搜索"):
        #kb=xbmc.Keyboard('','输入所查影片中文信息-拼音或简拼(拼音首字母)',False)
        keyboard = ChineseKeyboard.Keyboard('','输入所查影片中文信息-拼音或简拼(拼音首字母)')
        xbmc.sleep( 1500 )
        keyboard.doModal()
        keyword=keyboard.getText()
        
        #url="http://www.soso.com/wh.q?w="+keyword
        url ='http://video.soso.com/smart.php?w='+keyword
        link = getHttpData(url)
        link = link.decode('GB18030').encode('UTF-8')
        #print link

        #match=re.compile("    (.+?)    ").findall(link)
        match=re.compile("[0-9]+[,0-9]*[,0-9]*(.+?)0").findall(link)
        match.sort()
        for ix in range(0,len(match)):
            p_name = match[i].strip()
            p_list = str(i+1) + '. ' + p_name
            li=xbmcgui.ListItem(p_list)
            u=sys.argv[0]+"?mode=search&name="+urllib.quote_plus(p_name)+"&id="
            xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)        
    else:
        url="http://listso.ppstream.com/search.php?acp=936&w="+urllib.quote_plus(mname)
        
##################################################################################
# Routine to play video
##################################################################################
def KankanPlay(url):
    print 'video-link:', url
    xbmc.executebuiltin('System.ExecWait(\\"' + __cwd__ + '\\resources\\player\\pps4xbmc\\" ' + url.decode("gbk").encode("utf8") + ')')

##################################################################################
# Routine to fetch system parameters
##################################################################################
def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
        return param

def get_params2(dd):
        param=[]
        paramstring=dd
        if len(paramstring)>=2:
                params=dd
                cleanedparams=params.replace("'",'')
                pairsofparams=cleanedparams.split(';')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
        return param

params=get_params()
mode=None
name=''
url=''
id=''
category=''
thumb=''
text=''
rating=''

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    id=urllib.unquote_plus(params["id"])
except:
    pass
try:
    category=urllib.unquote_plus(params["category"])
except:
    pass
try:
    thumb=urllib.unquote_plus(params["thumb"])
except:
    pass
try:
    rating=urllib.unquote_plus(params["rating"])
except:
    pass
try:
    mode=urllib.unquote_plus(params["mode"])
except:
    pass

if mode==None:
    name = "pps"
    menu_main("generas")
elif mode=="gen":
    menu_sub(name,id,category)
elif mode=="sub":
    menu_ch(name,id,category,rating,thumb)
elif mode=="ch":
    KankanPlay(url)
elif mode=="search":
    Search(name)

xbmcplugin.setPluginCategory(int(sys.argv[1]), name )
xbmcplugin.endOfDirectory(int(sys.argv[1]))
    