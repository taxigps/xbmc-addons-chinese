#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2017年6月2日

@author: debo.zhang
'''
from bs4 import BeautifulSoup
import mechanize
import cookielib
import re,sys

class NoHistory(object): 
    def add(self, *a, **k): pass 
    def clear(self): pass 
    
def getBrowers():
    br = mechanize.Browser(history=NoHistory())
    #options
    br.set_handle_equiv(True)
    #br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    cj = cookielib.LWPCookieJar()  
    br.set_cookiejar(cj)##关联cookies  
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.set_debug_http(False)
    br.set_debug_redirects(False)
    br.set_debug_responses(False)
    br.addheaders = [("User-agent","Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36")]
    return br


            
if __name__ == "__main__":
    br = getBrowers()
    r = br.open("http://www.meijumao.net/alltvs")
    html = r.read()
#     print html
    #分类
    soup = BeautifulSoup(html,"html5lib")
    will_page = soup.find("ul",attrs={"id":"will_page"}).find_all("li")
    if len(will_page) > 0:
        print will_page[0].get("class"),will_page[0].find("a").get("href")
    current_page = soup.find("ul",attrs={"id":"will_page"}).find("li",attrs={"class":"active"})
    if current_page:
        print current_page.a.get_text()
    sys.exit(0)
    categories = {}
    for urls in  soup.find_all("a",attrs={"data-remote":"true"}):
        categories[urls.get("href").replace("http://www.meijumao.net","")] = urls.div.get_text()
#     print categories
    #剧
    sect = br.open("http://www.meijumao.net/sections/4")
    html = sect.read()
    soup_sections = BeautifulSoup(html,"html5lib")
    for section in soup_sections.find_all("article"):
#         print section.div.a.get("href"), section.div.a.img.get("src"),section.div.a.img.get("alt")
        pass
    
    #剧集
    tvs = br.open("http://www.meijumao.net/tvs/184")
    soup_ju = BeautifulSoup(tvs.read(),"html5lib")
    for juji in soup_ju.find_all("div",attrs={"class":"col-lg-1 col-md-2 col-sm-4 col-xs-4"}):
#         print juji.a.get("href"),juji.a.get_text().replace(" ","").replace("\n","")
        pass
    
    episode = br.open("http://www.meijumao.net/tvs/130/show_episode?episode=1839")
    soup_source = BeautifulSoup(episode.read(),"html5lib")
    for source in soup_source.find_all("a",attrs={"class":"button button-small button-rounded"}):
        print(source.get("href"),source.get_text())
#         print juji
    final = br.open("http://www.meijumao.net/tvs/130/play_episode?episode=1839&type=0")
    soup_js = BeautifulSoup(final.read(),"html5lib")
    print(soup_js.find_all("li",attrs={"class":"active"})[0].get_text())
    pattern = re.compile('var video=[.*?];')
    for script in soup_js.find_all('script'):
        matched = re.search('http.*m3u8.*\"', script.get_text())
        if matched:
            #print matched.group().replace("\"","")
            pass
    search = br.open("http://www.meijumao.net/search?q=Game")
    soup_search = BeautifulSoup(search.read(),"html5lib")
    print(soup_search)
    for section in soup_search.find_all("article"):
        print(section.div.a.get("href"), section.div.a.img.get("src"),section.div.a.img.get("alt"))
        pass
    
#http://www.meijumao.net/tvs/130/show_episode?episode=1839
#http://www.meijumao.net/tvs/130/play_episode?episode=1839&type=0    