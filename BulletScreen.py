# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import os
import threading
import logging

#Initialize logging
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(module)s][%(funcName)s] %(message)s')

WINDOW_FULLSCREEN_VIDEO = 12005
class BulletLabel(object):
    def __init__(self, text, label, timeout, line):
        self.label = label
        self.timeout = timeout
        self.line = line
        self.delay = self.showtime(text, timeout)

    def showtime(self, text, timeout):
        length = self.strlen(text)
        delay = int(length * timeout / 200) 
        if delay > timeout:
            delay = timeout
        return delay

    def strlen(self, text):
        length = len(text)
        utf8_length = len(text.encode('utf-8'))
        return (utf8_length - length) / 2 + length


class BulletScreen(object):
    def __init__(self,  *args, **kwargs):
        self.window = xbmcgui.Window(WINDOW_FULLSCREEN_VIDEO)
        viewport_w, viewport_h = self._get_skin_resolution()
        self.running = False
        self.thread = threading.Thread(target = self.run)
        self.texts = []
        self.labels = []
        self.textColor = kwargs.get("textColor", "0xFFFFFFFF")
        fontSize = kwargs.get("fontSize", "normal")
        position = kwargs.get("position", "up")
        self.left =int(viewport_w) 
        self.width = int(viewport_w)
        self.speed = kwargs.get("speed", 10000)
        if fontSize == "normal":
            self.fontSize = "font13"
            self.fontHeight = int(viewport_h * 0.03)
        else: 
            self.fontSize = "font16"
            self.fontHeight = int(viewport_h * 0.04)
        if position == "up":
            self.direction = 1
            self.top = int(viewport_h * 0.01)
        else:
            self.direction = -1
            self.top = int(viewport_h * 0.99 - self.fontHeight)

        self.available_line = []
        self.lines = 0

    def run(self):
        interval = 100
        while self.running:
            while len(self.texts) >= (2 << self.lines):
                self.available_line.append(self.lines)
                self.lines += 1

            while ((len(self.available_line) > 0) and (len(self.texts) > 0)):
                #Add texts
                text = self.texts.pop(0)
                line = self.available_line.pop(0) 
                top = self.top + self.direction * self.fontHeight * line
                label = xbmcgui.ControlLabel(self.left, top, self.width, self.fontHeight, text, 
                                             self.fontSize, self.textColor)
                self.labels.append(BulletLabel(text, label, self.speed, line)) 
                self.window.addControl(label)
                label.setAnimations([('conditional', 'condition=true effect=slide start=%d,0 end=%d,0 time=%d' % 
                                                     (0, -(self.width * 2), self.speed))])
                logging.debug('Add label: ' + text)

            for label in self.labels:
                #Check for available line
                if label.delay != 0:
                    if label.delay > interval:
                        label.delay -= interval
                    else:
                        self.available_line.append(label.line)
                        while (self.lines > 0) and (len(self.texts) < (2 << (self.lines - 1))) and ((self.lines - 1) in self.available_line):
                            self.lines -= 1
                            self.available_line.remove((self.lines))
                        label.delay = 0

                #Remove label that is timeout
                if label.timeout > interval:
                    label.timeout -= interval
                else:
                    logging.debug('Remove text: ' + label.label.getLabel())
                    self.window.removeControl(label.label)
                    self.labels.remove(label)

            xbmc.sleep(interval)

        logging.info('BulletScreen thread exit')

        #Remove labels
        for label in  self.labels:
            self.window.removeControl(label.label)


    def addText(self, text):
        logging.debug('Add text: ' + text)
        self.texts.append(text) #pending

        if self.running == False:
            self.running = True
            self.thread.start()

    def exit(self):
        if self.running == True:
            self.running = False
            self.thread.join()


    # This is so hackish it hurts.
    def _get_skin_resolution(self):
        import xml.etree.ElementTree as ET
        skin_path = xbmc.translatePath("special://skin/")
        tree = ET.parse(os.path.join(skin_path, "addon.xml"))
        res = tree.findall("./extension/res")[0]
        return int(res.attrib["width"]), int(res.attrib["height"])


if __name__ == '__main__':
    import xbmcgui
    import xbmcplugin
    import sys
    from urlparse import parse_qsl
    from douyudanmu import douyudanmu
    if 0:
        from addon import router
        router(sys.argv[2][1:])
    else:
        __handle__ = int(sys.argv[1])
        params = dict(parse_qsl(sys.argv[2][1:]))
        if 'test' in params:
            xbmcplugin.setResolvedUrl(__handle__, True, xbmcgui.ListItem(path='d:\empty.mpeg'))
            player = xbmc.Player()
            bs = BulletScreen()
            #danmu=douyudanmu('138286')
            danmu=douyudanmu('321358')
            while not player.isPlaying():
                xbmc.sleep(1000)
            while not xbmc.abortRequested and player.isPlaying():
                s=danmu.get_danmu()
                if len(s)!=0:
                    bs.addText(s)
            bs.exit()
        else:
            item = xbmcgui.ListItem(label='Play')
            item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(__handle__, sys.argv[0]+'?test=1', item)
            xbmcplugin.endOfDirectory(__handle__) 
