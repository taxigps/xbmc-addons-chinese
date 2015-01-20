#!/usr/bin/python
# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------
# Name: niconvert
# Desc: 弹幕字幕下载和转换工具
# Usage: ./niconvert -h
# ----------------------------------------------------------------------------

import re
import json
import logging
import urllib2
import gzip
import zlib
import colorsys
from StringIO import StringIO

ASS_HEADER_TPL = '''[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: %(video_width)s
PlayResY: %(video_height)s

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: NicoDefault, %(font_name)s, %(font_size)s, &H00FFFFFF, &H00FFFFFF, &H00000000, &H00000000, 0, 0, 0, 0, 100, 100, 0.00, 0.00, 1, 1, 0, 2, 20, 20, 20, 0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2'

def get_logger(logger_name):
    format_string = '%(asctime)s %(levelname)5s %(message)s'
    level = logging.WARNING
    logging.basicConfig(format=format_string, level=level)
    logger = logging.getLogger(logger_name)
    return logger

logger = get_logger('niconvert')

def fetch_url(url):
    #opener = urllib2.build_opener()
    #opener.addheaders = [
        #('User-Agent', USER_AGENT),
        #('Accept-Encoding', 'gzip')
    #]
    #resp = opener.open(url)
    #content = resp.read()
    resp = urllib2.urlopen(url)
    content = resp.read()
    content_encoding = resp.headers.get('content-encoding', None)
    if content_encoding == 'gzip':
        content = gzip.GzipFile(fileobj=StringIO(content), mode='rb').read()
    elif content_encoding == 'deflate':
        content = zlib.decompressobj(-zlib.MAX_WBITS).decompress(content)
    return content

class NicoSubtitle:

    (SCROLL, TOP, BOTTOM, NOT_SUPPORT) = range(4)
    FLASH_FONT_SIZE = 25 # office flash player font size

    def __init__(self):
        self.index = None
        self.start_seconds = None
        self.font_size = None
        self.font_color = None
        self.white_border = False
        self.style = None
        self.text = None

    def __unicode__(self):
        return u'#%05d, %d, %d, %s, %s, %s' % (
                self.index, self.style,
                self.font_size, self.font_color, self.white_border,
                self.start_seconds, self.text)

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    @staticmethod
    def to_style(attr):
        if attr == 1:
            style = NicoSubtitle.SCROLL
        elif attr == 4:
            style = NicoSubtitle.BOTTOM
        elif attr == 5:
            style = NicoSubtitle.TOP
        else:
            style = NicoSubtitle.NOT_SUPPORT
        return style

    @staticmethod
    def to_rgb(integer):
        return hex(integer).upper()[2:].zfill(6)

    @staticmethod
    def to_bgr(integer):
        rgb = NicoSubtitle.to_rgb(integer)
        NicoSubtitle.to_hls(integer)
        bgr = rgb[4:6] + rgb[2:4] + rgb[0:2] # ass use bgr
        return bgr

    @staticmethod
    def to_hls(integer):
        rgb = NicoSubtitle.to_rgb(integer)
        rgb_decimals = map(lambda x: int(x, 16), (rgb[0:2], rgb[2:4], rgb[4:6]))
        rgb_coordinates = map(lambda x: x / 255, rgb_decimals)
        hls_corrdinates = colorsys.rgb_to_hls(*rgb_coordinates)
        hls = hls_corrdinates[0] * 360, hls_corrdinates[1] * 100, hls_corrdinates[2] * 100
        return hls

    @staticmethod
    def need_white_border(integer):
        if integer == 0:
            return True

        hls = NicoSubtitle.to_hls(integer)
        hue, lightness = hls[0:2]
        if (hue > 30 and hue < 210) and lightness < 33:
            return True
        if (hue < 30 or hue > 210) and lightness < 66:
            return True
        return False

class AssSubtitle:

    top_subtitles = {}
    bottom_subtitles = {}

    def __init__(self, nico_subtitle,
                 video_width, video_height,
                 base_font_size, line_count,
                 bottom_margin, tune_seconds):

        self.nico_subtitle = nico_subtitle
        self.video_width = video_width
        self.video_height = video_height
        self.base_font_size = base_font_size
        self.line_count = line_count
        self.bottom_margin = bottom_margin
        self.tune_seconds = tune_seconds

        self.text_length = self.init_text_length()
        self.start = self.init_start()
        self.end_seconds = self.init_end_seconds()
        self.end = self.init_end()
        self.font_size = self.init_font_size()
        (self.x1, self.y1,
         self.x2, self.y2) = self.init_position();
        self.styled_text = self.init_styled_text()

    @staticmethod
    def to_hms(seconds):
        if seconds < 0:
            return '0:00:00.00'

        i, d = divmod(seconds, 1)
        m, s = divmod(i, 60)
        h, m = divmod(m, 60)
        return '%d:%02d:%02d.%02d' % (h, m, s, d * 100)

    def init_text_length(self):
        return float(len(self.nico_subtitle.text))

    def init_start(self):
        return AssSubtitle.to_hms(self.nico_subtitle.start_seconds)

    def init_end_seconds(self):
        if self.nico_subtitle.style in (NicoSubtitle.TOP, NicoSubtitle.BOTTOM):
            return self.nico_subtitle.start_seconds + 4

        if self.text_length < 5:
            end_seconds = self.nico_subtitle.start_seconds + 7 + (self.text_length / 1.5)
        elif self.text_length < 12:
            end_seconds = self.nico_subtitle.start_seconds + 7 + (self.text_length / 2)
        else:
            end_seconds = self.nico_subtitle.start_seconds + 13
        end_seconds += self.tune_seconds
        return end_seconds

    def init_end(self):
        return AssSubtitle.to_hms(self.end_seconds)

    def init_font_size(self):
        return self.nico_subtitle.font_size - NicoSubtitle.FLASH_FONT_SIZE + self.base_font_size

    def init_position(self):

        def choose_line_count(style_subtitles, start_seconds):
            for last_top_line_index, last_top_end_seconds in \
                    style_subtitles.copy().items():
                if last_top_end_seconds <= start_seconds:
                    del style_subtitles[last_top_line_index]

            exists_line_index = style_subtitles.keys()
            exists_line_length = len(exists_line_index)
            if exists_line_length == 0:
                line_index = 0
            elif exists_line_length == max(exists_line_index):
                line_index = min(style_subtitles.items(), key=lambda x: x[1])[0]
            else:
                line_index = 0
                for i in range(max(exists_line_index)):
                    if i not in exists_line_index:
                        line_index = i
                        break
                if line_index == 0:
                    line_index = exists_line_length
            return line_index

        if self.nico_subtitle.style == NicoSubtitle.SCROLL:
            x1 = self.video_width + (self.base_font_size * self.text_length) / 2
            x2 = -(self.base_font_size * self.text_length) / 2
            y = (self.nico_subtitle.index % self.line_count + 1) * self.base_font_size

            if y < self.font_size:
                y = self.font_size
            y1, y2 = y, y
        elif self.nico_subtitle.style == NicoSubtitle.BOTTOM:
            line_index = choose_line_count(AssSubtitle.bottom_subtitles, self.nico_subtitle.start_seconds)
            AssSubtitle.bottom_subtitles[line_index] = self.end_seconds

            x = self.video_width / 2
            y = self.video_height - (self.base_font_size * line_index + self.bottom_margin)

            x1, x2 = x, x
            y1, y2 = y, y
        else: # TOP
            line_index = choose_line_count(AssSubtitle.top_subtitles, self.nico_subtitle.start_seconds)
            AssSubtitle.top_subtitles[line_index] = self.end_seconds

            x = self.video_width / 2
            y = self.base_font_size * line_index + 1

            x1, x2 = x, x
            y1, y2 = y, y

        return (x1, y1, x2 , y2)

    def init_styled_text(self, ):
        if self.nico_subtitle.font_color == 'FFFFFF':
            color_markup = ''
        else:
            color_markup = '\\c&H%s' % self.nico_subtitle.font_color
        if self.nico_subtitle.white_border:
            border_markup = '\\3c&HFFFFFF'
        else:
            border_markup = ''
        if self.font_size == self.base_font_size:
            font_size_markup = ''
        else:
            font_size_markup = '\\fs%d' % self.font_size
        if self.nico_subtitle.style == NicoSubtitle.SCROLL:
            style_markup = '\\move(%d, %d, %d, %d)' % (self.x1, self.y1, self.x2, self.y2)
        else:
            style_markup = '\\a6\\pos(%d, %d)' % (self.x1, self.y1)
        markup = ''.join([style_markup, color_markup, border_markup, font_size_markup]) + '\\alpha&H7F&'
        return '{%s}%s' % (markup, self.nico_subtitle.text)

    @property
    def ass_line(self):
        return 'Dialogue: 3,%(start)s,%(end)s,NicoDefault,,0000,0000,0000,,%(styled_text)s' % dict(
                start=self.start,
                end=self.end,
                styled_text=self.styled_text)

class Downloader:

    TITLE_RE = re.compile('<title>(.*)</title>')

    def __init__(self, url):
        self.url = url
        self.html = self.get_html()
        self.title = self.get_title()
        self.comment_url = self.get_comment_url()
        self.comment_text = self.get_comment_text()

    def get_html(self):
        raise NotImplementedError

    def get_title(self):
        title = Downloader.TITLE_RE.findall(self.html)[0].split(' - ')[0]
        if isinstance(title, str):
            title = title.decode('utf-8')
        logger.info(u'视频标题: %s', title)
        return title

    def get_comment_url(self):
        raise NotImplementedError

    def get_comment_text(self):
        return fetch_url(self.comment_url)

class BilibiliDownloader(Downloader):
    URL_PARAMS = re.compile('cid=(\d+)&aid=\d+')
    URL_PARAMS2 = re.compile("cid:'(\d+)'")

    def __init__(self, url):
        Downloader.__init__(self, url)

    def get_html(self):
        return fetch_url(self.url).decode('UTF-8')

    def get_comment_url(self):
        try:
            cids = self.URL_PARAMS.findall(self.html)
            if not cids:
                cids = self.URL_PARAMS2.findall(self.html)
            comment_url = 'http://comment.bilibili.tv/%s.xml' % cids[0]
            print comment_url
            logger.info(u'评论地址: %s', comment_url)
            return comment_url
        except:
            return ''

class BilibiliDownloaderAlt(Downloader):

    def __init__(self, url):
        Downloader.__init__(self, url)

    def get_html(self):
        return ''

    def get_title(self):
        faketitle = self.url.split('tv/')[1]
        logger.info(u'视频标题: %s', faketitle)
        return faketitle

    def get_comment_url(self):
        logger.info(u'评论地址: %s', self.url)
        return self.url

    def get_comment_text(self):
        return fetch_url(self.comment_url)

class AcfunDownloader(Downloader):

    VIDEO_UID_RE = re.compile('\[video\](.+?)\[/video\]', re.IGNORECASE)
    VIDEO_UID_RE2 = re.compile('src="/newflvplayer/player.swf\?id=(.+?)&', re.IGNORECASE)
    VIDEO_UID_RE3 = re.compile('flashvars=".*id=(.+?)"', re.IGNORECASE)

    def __init__(self, url):
        Downloader.__init__(self, url)

    def get_html(self):
        return fetch_url(self.url)

    def get_comment_url(self):
        try:
            vid = AcfunDownloader.VIDEO_UID_RE.findall(self.html)[0]
        except IndexError:
            try:
                vid = AcfunDownloader.VIDEO_UID_RE2.findall(self.html)[0]
            except IndexError:
                vid = AcfunDownloader.VIDEO_UID_RE3.findall(self.html)[0]

        info_url = 'http://www.acfun.tv/api/player/vids/' + vid + '.aspx'
        try:
            video_uid = json.loads(fetch_url(info_url))['cid']
        except KeyError:
            video_uid = vid
        comment_url = 'http://comment.acfun.tv/%s.json' % video_uid
        logger.info(u'评论地址: %s', comment_url)
        return comment_url

class AcfunDownloaderAlt(Downloader):

    def __init__(self, url):
        Downloader.__init__(self, url)

    def get_html(self):
        return ''

    def get_title(self):
        faketitle = self.url.split('.json')[0].split('/')[-1]
        logger.info(u'视频标题: %s', faketitle)
        return faketitle

    def get_comment_url(self):
        logger.info(u'评论地址: %s', self.url)
        return self.url

    def get_comment_text(self):
        return fetch_url(self.comment_url)

class Website:

    def __init__(self, url):
        self.url = url
        self.downloader = self.create_downloader()
        self.nico_subtitles = self.create_nico_subtitles()

    def create_downloader(self):
        raise NotImplementedError

    def create_nico_subtitles(self):
        raise NotImplementedError

    def unescape(self, text):
        return text.replace('/n', '\\N')

    def ass_subtitles_text(self, font_name, font_size, resolution, line_count, bottom_margin, tune_seconds):

        video_width, video_height = map(int, resolution.split(':'))

        ass_subtitles = []
        for nico_subtitle in self.nico_subtitles:
            ass_subtitle = AssSubtitle(nico_subtitle,
                                       video_width, video_height,
                                       font_size, line_count,
                                       bottom_margin, tune_seconds)
            ass_subtitles.append(ass_subtitle)

        ass_lines = []
        for ass_subtitle in ass_subtitles:
            ass_lines.append(ass_subtitle.ass_line)

        ass_header = ASS_HEADER_TPL % dict(video_width=video_width,
                                           video_height=video_height,
                                           font_name=font_name,
                                           font_size=font_size)
        text = ass_header + '\n'.join(ass_lines)
        return text

class Bilibili(Website):

    XML_NODE_RE = re.compile('<d p="([^"]*)">([^<]*)</d>')

    def __init__(self, url):
        Website.__init__(self, url)

    def create_downloader(self):
        if self.url.startswith('http://comment.bilibili.tv/'):
            return BilibiliDownloaderAlt(self.url)
        else:
            return BilibiliDownloader(self.url)

    def create_nico_subtitles(self):

        nico_subtitles = []
        nico_subtitle_lines = Bilibili.XML_NODE_RE.findall(self.downloader.comment_text)
        for line in nico_subtitle_lines:
            attributes = line[0].split(',')

            nico_subtitle = NicoSubtitle()
            nico_subtitle.start_seconds = float(attributes[0])
            nico_subtitle.style = NicoSubtitle.to_style(int(attributes[1]))
            nico_subtitle.font_size = int(attributes[2])
            nico_subtitle.font_color = NicoSubtitle.to_bgr(int(attributes[3]))
            nico_subtitle.white_border = NicoSubtitle.need_white_border(int(attributes[3]))
            nico_subtitle.text = self.unescape(line[1].decode('UTF-8'))

            if nico_subtitle.style != NicoSubtitle.NOT_SUPPORT:
                nico_subtitles.append(nico_subtitle)
        nico_subtitles.sort(key=lambda x: x.start_seconds)

        for i, nico_subtitle in enumerate(nico_subtitles):
            nico_subtitle.index = i

        logger.info(u'字幕数量: (%d/%d)', len(nico_subtitles), len(nico_subtitle_lines))
        return nico_subtitles

class Acfun(Website):

    def __init__(self, url):
        Website.__init__(self, url)

    def create_downloader(self):
        if self.url.find('.json') == -1:
            return AcfunDownloader(self.url)
        else:
            return AcfunDownloaderAlt(self.url)

    def create_nico_subtitles(self):

        nico_subtitles = []
        nico_subtitle_json_list = json.loads(self.downloader.comment_text)
        for element in nico_subtitle_json_list:
            attributes = element['c'].split(',')

            nico_subtitle = NicoSubtitle()
            nico_subtitle.start_seconds = float(attributes[0])
            nico_subtitle.font_color = NicoSubtitle.to_bgr(int(attributes[1]))
            nico_subtitle.style = NicoSubtitle.to_style(int(attributes[2]))
            nico_subtitle.font_size = int(attributes[3])
            nico_subtitle.text = self.unescape(element['m'])

            if nico_subtitle.style != NicoSubtitle.NOT_SUPPORT:
                nico_subtitles.append(nico_subtitle)
        nico_subtitles.sort(key=lambda x: x.start_seconds)

        for i, nico_subtitle in enumerate(nico_subtitles):
            nico_subtitle.index = i

        logger.info(u'字幕数量: (%d/%d)', len(nico_subtitles), len(nico_subtitle_json_list))
        return nico_subtitles


def create_website(url):
    if url.find('bilibili') != -1:
        return Bilibili(url)
    elif url.find('acfun') != -1:
        return Acfun(url)
    else:
        return None
