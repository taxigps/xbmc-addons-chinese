#coding: utf8
import urllib2
import zlib
import gzip
from io import BytesIO

def _get_gzip_content(content):
    bytes_buffer = BytesIO(content)
    return gzip.GzipFile(fileobj=bytes_buffer).read()

def _get_zlib_content(content):
    page_content = zlib.decompress(content)
    return page_content

def get_page_content(page_full_url, data = None, headers = {}):
    try:
        ua = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0.2) Gecko/20100101 Firefox/6.0.2'}
        ua.update(headers)
        req = urllib2.Request(page_full_url, headers=ua, data = data)
        print (req.headers.items())
        response = urllib2.urlopen(req)
        print(response.info())
        if response.headers.get('content-encoding', '') == 'gzip':
            return _get_gzip_content(response.read())
        elif response.headers.get('content-encoding', '') == 'deflate':
            return _get_zlib_content(response.read())
        else:
            return response.read()
    except:
        return ''
