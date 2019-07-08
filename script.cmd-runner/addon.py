import xbmcaddon
import xbmcgui
 
addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
 
cmd = addon.getSetting("cmd").split(';')
names = []
cmds = []
for d in cmd:
    one = d.split(',')
    names.append(one[0])
    cmds.append(one[-1])

if(len(names) > 1):
    choice = xbmcgui.Dialog().select("Select Command:", names)
    name = names[choice]
    cmd = cmds[choice]
#xbmcgui.Dialog().ok("You choice:","11")

if(xbmcgui.Dialog().yesno(addonname, "Run command?", name, cmd)):
    xbmc.executebuiltin('System.Exec(' + cmd + ')')