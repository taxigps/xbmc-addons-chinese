# -*- coding: utf-8 -*-
# main import's 
import sys, os, re
import xbmc, xbmcaddon, xbmcgui
from xml.dom import minidom

# Script constants 
__addon__     = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode("utf-8")
__language__  = __addon__.getLocalizedString

# Shared resources
BASE_RESOURCE_PATH = os.path.join(__cwd__, 'resources', 'lib')
sys.path.append (BASE_RESOURCE_PATH)

def fixed_writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        if len(self.childNodes) == 1 \
          and self.childNodes[0].nodeType == minidom.Node.TEXT_NODE:
            writer.write(">")
            self.childNodes[0].writexml(writer, "", "", "")
            writer.write("</%s>%s" % (self.tagName, newl))
            return
        writer.write(">%s"%(newl))
        for node in self.childNodes:
            if node.nodeType is not minidom.Node.TEXT_NODE:
                node.writexml(writer,indent+addindent,addindent,newl)
        writer.write("%s</%s>%s" % (indent,self.tagName,newl))
    else:
        writer.write("/>%s"%(newl))
# replace minidom's function with ours
minidom.Element.writexml = fixed_writexml

def getres(addonid):
    filepath = os.path.join(addonspath, addonid, 'addon.xml')
    doc = minidom.parse(filepath)
    root = doc.documentElement
    items = root.getElementsByTagName('extension')
    for item in items:
        point = item.getAttribute('point')
        if point == 'xbmc.gui.skin':
            ress = item.getElementsByTagName('res')
            list = []
            for res in ress:
                list.append(res.getAttribute('folder'))
            return list
    return []

def addfont(addonid, folder):
    filepath = os.path.join(addonspath, addonid, folder, 'Font.xml')
    doc = minidom.parse(filepath)
    root = doc.documentElement
    fontsets = root.getElementsByTagName('fontset')
    list = []
    for i in range(0,len(fontsets)):
        id = fontsets[i].getAttribute('id')
        if id.lower() == 'arial':
            ret = xbmcgui.Dialog().yesno('Skin Font', 'Arial皮肤字体已存在。', '要重新生成Arial字体吗？')
            if not ret:
                return
            root.removeChild(fontsets[i])
            del fontsets[i]
        else:
            list.append(id)
    sel = xbmcgui.Dialog().select('请选择参照字体(%s)' % (folder.encode('utf-8')), list)
    xml = fontsets[sel].toxml()
    xml = re.sub('<filename>.*?</filename>', '<filename>arial.ttf</filename>', xml)
    xml = re.sub('<fontset id=[^>]*>', '<fontset id="Arial">', xml, 1)
    arial = minidom.parseString(xml)
    root.appendChild(arial.documentElement)
    f = open(filepath, 'w')
    doc.writexml(f, addindent="    ", newl="\n")
    f.close()
    xbmc.executebuiltin('Notification(%s,%s,%s)' % (__addonname__, 'Arial皮肤字体已生成(%s)' % (folder.encode('utf-8')), "1000")) 

addonspath = os.path.dirname(__cwd__)
addonlist = []
for addonid in os.listdir(addonspath):
    if addonid[:4] == 'skin':
        addon = xbmcaddon.Addon(id=addonid)
        addonname = addon.getAddonInfo('name')
        addonlist.append((addonid, addonname))

list = [x[1] for x in addonlist]
if not list:
    xbmcgui.Dialog().ok('Skin Font', '未找到可用皮肤！')
else:
    sel = xbmcgui.Dialog().select('请选择要增加字体的皮肤', list)
    if sel != -1:
        addonid = addonlist[sel][0]
        for folder in getres(addonid):
            addfont(addonid, folder)