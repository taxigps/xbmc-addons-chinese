#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" plugin release tool"""

import os, sys, zipfile, shutil

def release(plugin, version):
    # zip dir
    plugin = plugin.strip('/')
    zipname = 'repo/%s/%s-%s.zip' % (plugin, plugin, version)
    f = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(plugin):
        for filename in filenames:
            f.write(os.path.join(dirpath,filename))
    f.close()

    # copy change log
    src = '%s/changelog.txt' % plugin
    dst = 'repo/%s/changelog-%s.txt' % (plugin, version)
    shutil.copyfile(src, dst)

if len(sys.argv) == 3:
    release(sys.argv[1], sys.argv[2])
else:
    print('usage: %s plugin_dir plugin_version' % sys.argv[0])
