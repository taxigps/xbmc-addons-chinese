# -*- coding: utf-8 -*-

import xbmc
import os
import datetime
import traceback
import urllib2
import re
import simplejson

from resources.lib.utils import *

def updateChannelCCTV(fHandle, channelID, channelName):
    try:
        log("Updating channel " + channelID)

        dateInChina = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).replace(hour=0, minute=0) #UTC +0800

        #Get data
        request = urllib2.Request("http://api.cntv.cn/epg/epginfo?serviceId=tvcctv&c=%s&d=%s" % (channelID, dateInChina.strftime("%Y%m%d")))
        request.add_header("Referer", "http://tv.cntv.cn/epg")
        resp = urllib2.urlopen(request)
        data = resp.read().decode("utf-8")
        programmes = simplejson.loads(data)[channelID]['program']

        #Write channel data
        fHandle.write('  <channel id="{0}">\n'.format(channelID))
        fHandle.write('    <display-name lang="cn">{0}</display-name>\n'.format(channelName))
        fHandle.write('  </channel>\n'.format(channelID))

        #Write programme data
        for entry in programmes:
            startTime = datetime.datetime.fromtimestamp(entry['st'])
            stopTime  = datetime.datetime.fromtimestamp(entry['et'])

            fHandle.write('  <programme start="{0}" stop="{1}" channel="{2}">\n'.format(formatDate(startTime), formatDate(stopTime), channelID))
            fHandle.write('    <title lang="cn">{0}</title>\n'.format(entry['t'].encode("utf-8")))
            fHandle.write('  </programme>\n')
    except Exception:
        log(traceback.format_exc())

def updateChannelPHNX(fHandle, channelID, siteID, channelName):
    try:
        log("Updating channel " + channelID)

        dateInChina = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).replace(hour=0, minute=0) #UTC +0800

        #Get data
        request = urllib2.Request("https://www.tvsou.com/epg/%s" % (siteID))
        resp = urllib2.urlopen(request)
        data = resp.read().decode("utf-8")
        programmes = re.compile('<li class="relative cur.*?data-mainstars="([\d:]+)-([\d:]+).*?data-content="([^"]+)".*?title="([^"]+)"', re.DOTALL).findall(data)

        #Write channel data
        fHandle.write('  <channel id="{0}">\n'.format(channelID))
        fHandle.write('    <display-name lang="cn">{0}</display-name>\n'.format(channelName))
        fHandle.write('  </channel>\n'.format(channelID))

        #Write programme data
        for entry in programmes:
            startTime = dateInChina.replace(hour=int(entry[0].split(':')[0]), minute=int(entry[0].split(':')[1]))
            if entry[1] == '24:00':
                stopTime  = dateInChina.replace(hour=23, minute=59)
            else:
                stopTime  = dateInChina.replace(hour=int(entry[1].split(':')[0]), minute=int(entry[1].split(':')[1]))

            fHandle.write('  <programme start="{0}" stop="{1}" channel="{2}">\n'.format(formatDate(startTime), formatDate(stopTime), channelID))
            fHandle.write('    <title lang="cn">{0}</title>\n'.format(entry[3].encode("utf-8").strip()))
            fHandle.write('    <desc lang="cn">{0}</desc>\n'.format(entry[2].encode("utf-8").strip()))
            fHandle.write('  </programme>\n')
    except Exception:
        log(traceback.format_exc())

def formatDate(obj):
    return obj.strftime("%Y%m%d%H%M00 +0800")

def doUpdate():
    log("Updating EPG")

    try:
        epgfile = os.path.join(data_dir(), "epg.xml")
        fHandle = open(epgfile, "w")
        fHandle.write('<?xml version="1.0" encoding="utf-8" ?>\n')
        fHandle.write('<tv>\n')

        if getSetting("epg_cctv") == "true":
            for id, name in CHANNEL_CCTV:
                updateChannelCCTV(fHandle, id, name)

        if getSetting("epg_province") == "true":
            for id, name in CHANNEL_PROV:
                updateChannelCCTV(fHandle, id, name)

        if getSetting("epg_phoenix") == "true":
            for id, id2, name in CHANNEL_PHNX:
                updateChannelPHNX(fHandle, id, id2, name)

        fHandle.write('</tv>\n')
        fHandle.close()

    except Exception:
        log(traceback.format_exc())

    log("Finished updating EPG")

    #Set a timer for the next update
    startTimer(60)

def startTimer(delay): #minutes
    xbmc.executebuiltin("AlarmClock({0},RunScript({1}),{2},True)".format("EPGUpdate", os.path.join(addon_dir(), "epgservice.py"), delay))

if getSetting("epg") == "true":
    doUpdate()
