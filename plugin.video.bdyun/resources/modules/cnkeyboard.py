#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
this module is for supporting chinese input
the ChineseKeyboard is from script.module.keyboard.chinese
if can not load chinese keyboard then use enlish keyboard
'''

try:
    import ChineseKeyboard as _xbmc
except ImportError as e:
    import xbmc as _xbmc


def keyboard(default='', heading='', hidden=False):
    kb = _xbmc.Keyboard(default,heading)
    kb.doModal()
    if kb.isConfirmed():
        text = kb.getText()
        return unicode(text, 'utf-8')
