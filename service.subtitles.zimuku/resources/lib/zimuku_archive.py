# -*- coding: UTF-8 -*-
"""
Archive module for service.subtitle.zimuku.

Help to support more archive formats.
kodi_six.xbmcvfs supports a lot of formats but it will went wrong if the file name in archive is not UTF-8 encoded.

zimuku.la only use .rar, .zip and .7z (few) as compressing formats, so support for these 3 is enough for service.subtitle.zimuku.
But not enough for a general lib.
"""

import os
import sys
import json
import urllib
from kodi_six import xbmc, xbmcvfs, xbmcaddon

__addon__      = xbmcaddon.Addon()
__scriptname__ = __addon__.getAddonInfo('name')

def log(module, msg, level=xbmc.LOGDEBUG):
    if isinstance(msg, unicode): msg = msg.encode("utf-8")
    xbmc.log("{0}::{1} - {2}".format(__scriptname__,module,msg) ,level=level )

def unpack(file_path):
    """
    Get the file list from archive file.
    
    Params:
        file_path   The path to the archive file.
        
    Return:
        tuple(whole_path:str, subfiles:list)
            whole_path  The quoted path to the subfiles.
            subfiles    The list of subtitle files.
            
    Raise:
        TypeError   The file type is unsupported. Some of the files is theoretically supported, such as 7z/tar.
                    However, some encoding (Chinese chars for example) in file names may cause failure, even crash,
                    so raise TypeError to avoid the worst condition.
    """
    exts = ( ".srt", ".sub", ".smi", ".ssa", ".ass", ".sup" )
    supported_archive_exts = ( ".zip", ".7z", ".tar", ".bz2", ".rar", ".gz", ".xz", ".iso", ".tgz", ".tbz2", ".cbr" )
    self_archive_exts = ( ".zip", ".rar" )

    if not file_path.endswith(supported_archive_exts):
        log(sys._getframe().f_code.co_name, "Unknown file ext: %s" % (os.path.basename(file_path)), level=xbmc.LOGERROR)
        raise TypeError, "Not supported file!"

    file_path = file_path.rstrip('/')
    if file_path.endswith(self_archive_exts):
        archive_file = urllib.quote_plus(xbmc.translatePath(file_path))
        ext = file_path[file_path.rfind('.') + 1:]
        archive_path = '%(protocol)s://%(archive_file)s' % {'protocol':ext, 'archive_file': archive_file}
        log(sys._getframe().f_code.co_name, "Get %s archive: %s" % (ext, archive_path), level=xbmc.LOGDEBUG)

        dirs, files = xbmcvfs.listdir(archive_path)
        if ('__MACOSX') in dirs:
            dirs.remove('__MACOSX')
        if len(dirs) > 0:
            archive_path = os.path.join(archive_path, dirs[0], '').replace('\\','/')
            dirs, files = xbmcvfs.listdir(archive_path)

        list = []
        for subfile in files:
            if subfile.endswith(exts):
                list.append(subfile.decode('utf-8'))

        subtitle_list = list
    
    elif file_path.endswith('.7z'):
        archive_path, subtitle_list = unpack_7z(file_path)

    else:
        log(sys._getframe().f_code.co_name, "Skip: Danger file ext: %s" % (archive_path), level=xbmc.LOGERROR)
        raise TypeError, "Skip: unstable file format!"

    return archive_path, subtitle_list

def unpack_7z(file_path):
    """
    Stub function.
    Get the file list from 7z file.

    xbmcvfs can't correctly handle the 7z file if there are chinese chars in filename .
    TODO ( YK-Samgo 20201023): Now it is only a stub function to skip the 7z format.
                                Use some way else to decompress the 7z archive, 
                                then use the decompressed path and decompressed files as the return.
    
    Params:
        file_path   The path to the archive file.
        
    Return:
        tuple(whole_path:str, subfiles:list)
            whole_path  The quoted path to the subfiles.
            subfiles    The list of subtitle files.
    """
    decompress_path = ''
    subtitle_list = []
    return decompress_path, subtitle_list