# import pydevd
# pydevd.settrace('192.168.1.3', port=63612, stdoutToServer=True, stderrToServer=True)
import urllib2, urllib, time, gzip, StringIO, sys, re, simplejson
import xbmc

UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'


def _log(txt):
    message = 'youku api: %s' % txt
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


def _GetHttpData(url, referer=''):
    _log("%s::url - %s" % (sys._getframe().f_code.co_name, url))
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    if referer:
        req.add_header('Referer', referer)
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        response.close()
    except:
        _log("%s (%d) [%s]" % (
            sys.exc_info()[2].tb_frame.f_code.co_name,
            sys.exc_info()[2].tb_lineno,
            sys.exc_info()[1]
        ))
        return ''
    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(
        httpdata)
    if match:
        charset = match[0]
    else:
        match = re.compile('<meta charset="(.+?)"').findall(httpdata)
        if match:
            charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')
    return httpdata


def getMov(vid):
    # vid = "XNTcyMjAwMjA0"
    res = urllib2.urlopen('https://log.mmstat.com/eg.js')
    cna = res.headers['etag'][1:-1]
    query = urllib.urlencode(dict(
        vid=vid,
        ccode='0401',
        client_ip='192.168.1.1',
        utid=cna,
        client_ts=time.time() / 1000
    ))
    url = 'https://ups.youku.com/ups/get.json?%s' % (query)
    link = _GetHttpData(url, referer='http://static.youku.com/')
    json_response = simplejson.loads(link)
    if 'data' not in json_response or 'error' in json_response['data']:
        return False
    else:
        return json_response['data']

if __name__ == '__main__':
    print(getMov('XNTcyMjAwMjA0'))