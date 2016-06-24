#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os, sys, re, json 
from resources.modules import auth

dialog = xbmcgui.Dialog()


class VcodeWindow(xbmcgui.WindowDialog):
    def __init__(self, vcode_path):
        self.image = xbmcgui.ControlImage(80, 100, 500, 200, vcode_path)
        self.button = xbmcgui.ControlButton(100, 330, 140, 50, label=u'输入验证码', font='font20', textColor='0xFFFFFFFF')
        self.addControl(self.image)
        self.addControl(self.button)
        self.setFocus(self.button)

    def onControl(self, event):
        if event == self.button:
            self.close()


def run(username,password):
    cookie = auth.get_BAIDUID()
    token = auth.get_token(cookie)
    tokens = {'token': token}
    ubi = auth.get_UBI(cookie,tokens)
    cookie = auth.add_cookie(cookie,ubi,['UBI','PASSID'])
    key_data = auth.get_public_key(cookie,tokens)
    pubkey = key_data['pubkey']
    rsakey = key_data['key']
    password_enc = auth.RSA_encrypt(pubkey, password)
    err_no,query = auth.post_login(cookie,tokens,username,password_enc,rsakey)
    if err_no == 257:
        vcodetype = query['vcodetype']
        codeString = query['codeString']
        vcode_path = auth.get_signin_vcode(cookie, codeString)

        win = VcodeWindow(vcode_path)
        win.doModal()

        verifycode = dialog.input(u'验证码', type=xbmcgui.INPUT_ALPHANUM)
        if len(verifycode) == 4:
            err_no,query = auth.post_login(cookie,tokens,username,password_enc,rsakey,verifycode,codeString)
            if err_no == 0:
                temp_cookie = query
                auth_cookie, bdstoken = auth.get_bdstoken(temp_cookie)
                if bdstoken:
                    tokens['bdstoken'] = bdstoken
                    return auth_cookie,tokens

            elif err_no == 4:
                dialog.ok('Error',u'密码错误')

            elif err_no == 6:
                dialog.ok('Error',u'验证码错误')

            else:
                dialog.ok('Error',u'未知错误，请重试')
        else:
            dialog.ok('Error',u'验证码为四位数')
    
    elif err_no == 4:
        dialog.ok('Error',u'密码错误')

    elif err_no == 0:
        auth_cookie = query
        bdstoken = auth.get_bdstoken(auth_cookie)
        if bdstoken:
            tokens['bdstoken'] = bdstoken
            return auth_cookie,tokens

    else:
        dialog.ok('Error',u'未知错误，请重试')
    
    return None,None
