#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os, sys, re, json 
from resources.modules import auth, cnkeyboard

dialog = xbmcgui.Dialog()


class VcodeWindow(xbmcgui.WindowDialog):
    def __init__(self, cookie, tokens, vcodetype, codeString, vcode_path):
        self.cookie = cookie
        self.tokens = tokens
        self.vcodetype = vcodetype
        self.codeString = codeString
        self.vcode_path = vcode_path

        # windowItems
        self.image = xbmcgui.ControlImage(80, 100, 500, 200, self.vcode_path)
        self.buttonInput = xbmcgui.ControlButton(100, 330, 140, 50, label=u'输入验证码', font='font20', textColor='0xFFFFFFFF')
        self.buttonRefresh = xbmcgui.ControlButton(290, 330, 140, 50, label=u'刷新验证码', font='font20', textColor='0xFFFFFFFF')
        self.addControls([self.image, self.buttonInput, self.buttonRefresh])
        self.setFocus(self.buttonInput)


    def onControl(self, event):
        if event == self.buttonInput:
            self.close()
        elif event == self.buttonRefresh:
            (self.codeString, self.vcode_path) = auth.refresh_vcode(self.cookie, self.tokens, self.vcodetype)
            if self.codeString and self.vcode_path:
                self.removeControl(self.image)
                self.image = xbmcgui.ControlImage(80, 100, 500, 200, self.vcode_path)
                self.addControl(self.image)
            else:
                dialog.ok('Error', u'无法刷新验证码，请重试')



# Authorisation Process
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

        win = VcodeWindow(cookie, tokens, vcodetype, codeString, vcode_path)
        win.doModal()
        codeString = win.codeString

        verifycode = cnkeyboard.keyboard(heading=u'验证码')
        if verifycode:
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
            dialog.ok('Error',u'请输入验证码')
    
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
