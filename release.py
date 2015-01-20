#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" plugin release tool"""

import os, sys, re, zipfile, shutil

def cp(src, dst):
    if os.path.exists(src):
        shutil.copyfile(src, dst)

def release(plugin, version):
    # zip dir
    zipdir = 'repo/%s' % (plugin)
    if not os.path.exists(zipdir):
        os.mkdir(zipdir)

    # zip repo
    zipname = 'repo/%s/%s-%s.zip' % (plugin, plugin, version)
    f = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(plugin):
        for filename in filenames:
            f.write(os.path.join(dirpath,filename))
    f.close()

    # copy icon
    src = '%s/icon.png' % (plugin)
    dst = 'repo/%s/icon.png' % (plugin)
    cp(src, dst)

    # copy change log
    src = '%s/changelog.txt' % plugin
    dst = 'repo/%s/changelog-%s.txt' % (plugin, version)
    cp(src, dst)

def getVersion(plugin):
    name = '%s/addon.xml' % plugin
    cont = open(name).read()
    addon = re.findall('<addon.*?version="(.*?)"', cont, re.DOTALL)
    if addon:
        return addon[0]

argc = len(sys.argv)
if argc >= 2:
    plugin = sys.argv[1].rstrip('/')
    version = getVersion(plugin) if argc == 2 else sys.argv[2]
    release(plugin, version)
else:
    print('usage: %s plugin_dir [plugin_version]' % sys.argv[0])
