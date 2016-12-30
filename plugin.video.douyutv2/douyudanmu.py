# -*- coding: utf-8 -*-
#adopted from https://github.com/zephyrzoom/douyu/blob/master/comment-douyu.py
import struct
import socket
import hashlib
import time
import random
import threading
import json
import sys
import os
import urllib2 as request
import HTMLParser
pars=HTMLParser.HTMLParser()

class douyudanmu():
  def exit(self):
      self.g_exit=True
  def is_exit(self):
      return self.g_exit
  g_exit= False
  def get_danmu(self):
        bmsg= recvmsg(self.s)
        if not bmsg:
            self.g_exit= True
            return('connection break')

        msg= unpackage(bmsg)
        msgtype= msg.get(b'type',b'undefined')

        if msgtype==b'chatmsg':
                nick= msg[b'nn'].decode('utf8')
                content=msg.get(b'txt',b'undefined')
                try:
                  content= content.decode('utf8')
                except UnicodeDecodeError:
                  content=content.decode('latin-1')
                  return('')
                return(content)
                #return(u'{0}:{1}'.format(nick, content))
        elif msgtype==b'gift_title':
            message=u'{0}成为主播{1}级粉丝'.format(msg[b'uname'].decode('utf8'),msg[b'gt'].decode('utf8'))
            return(message)
        elif msgtype==b'pet_info':
            #message=u'{0}赠送了主播？'.format(msg[b'mname'].decode('utf8'))
            pass
        elif msgtype==b'ggbb':
            message=u'{0}收到{1}赠送的{2}鱼丸'.format(msg[b'dnk'].decode('utf8'),msg[b'snk'].decode('utf8'),int(msg[b'sl']))
            return(message)
        elif msgtype==b'bc_buy_deserve':
            sui= unpackage(msg.get(b'sui',b'nick@=undifined//00'))
            nick= sui[b'nick'].decode('utf8')
            message=u'{0}赠送高级酬勤成为高级会员'
        elif msgtype==b'upgrade':
            message=u'{0}升到{1}级'.format(msg[b'nn'].decode('utf8'),int(msg[b'level']))
            return(message)
        elif msgtype==b'onlinegift':
            message=u'{0}获得了{1}个酬勤专享鱼丸'.format(msg[b'nn'].decode('utf8'),int(msg[b'sil']))
            return(message)
        elif msgtype==b'dgn':
            gfiddict={b'78':u'100鱼丸',b'79':u'520鱼丸',b'80':u'0.1鱼翅',b'81':u'6鱼翅',b'82':u'100鱼翅',b'83':u'500鱼翅',b'50':u'100鱼丸',b'53':u'520鱼丸',b'57':u'0.1鱼翅',b'52':u'6鱼翅',b'54':u'100鱼翅',b'59':u'500鱼翅'}
            gift=gfiddict[msg[b'gfid']] if msg[b'gfid'] in gfiddict else u'礼物'
            message=u'{0}赠送{1}'.format(msg[b'src_ncnm'].decode('utf8'),gift)
            hit=int(msg[b'hits'])
            if hit>1:
              message+=u',{0}连击'.format(hit)
            return(message)
        elif msgtype==b'spbc':
            message=u'{0}收到{1}赠送的{2}'.format(msg[b'dn'].decode('utf8'),msg[b'sn'].decode('utf8'),msg[b'gn'].decode('utf8'))
            return(message)
        elif msgtype==b'blackres':
            message=u'{0}被管理员{1}禁言{2}小时'.format(msg[b'dnick'].decode('utf8'),msg[b'snick'].decode('utf8'),int(msg[b'limittime'])/3600.)
            return(message)
        elif msgtype==b'donateres':
            sui= unpackage(msg.get(b'sui',b'nick@=undifined//00'))
            nick= sui[b'nick'].decode('utf8')
            return( u'{0}赠送给主播{1}鱼丸'.format(nick, int(msg[b'ms'])))
        elif msgtype==b'ranklist':
            pass
        elif msgtype==b'keeplive':
            pass
        elif msgtype in (b'userenter'):
            pass
        else:
            return('')
        return('')
  def __init__(self,roomid):
      self.s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.s.settimeout(120)
      self.s.connect((socket.gethostbyname('openbarrage.douyutv.com'),8601))
      sendmsg(self.s,b'type@=loginreq/\x00')
      loginres= unpackage(recvmsg(self.s))
      sendmsg(self.s,b'type@=joingroup/rid@='+roomid+b'/gid@=-9999/\x00')

      def keepalive():
          while not self.is_exit():
              sendmsg(self.s,b'type@=keeplive/tick@='+str(random.randint(20,60)).encode('ascii')+b'/\x00')
              time.sleep(35)
          self.s.close()
      threading.Thread(target=keepalive).start()



def sendmsg(s,msg,code=689):
    data_length= len(msg)+8
    s.send(struct.pack("<I",data_length))
    s.send(struct.pack("<I",data_length))
    s.send(struct.pack("<I",code))
    sent=0
    while sent<len(msg):
        tn= s.send(msg[sent:])
        sent= sent + tn

def recvmsg(s):
    head_length=12
    bdata_length=[]
    while True:
        msg= s.recv(head_length)
        if not msg: break
        head_length= head_length - len(msg)
        bdata_length.append(msg)
    bdata_length=b''.join(bdata_length)
    data_length= struct.unpack("<I",bdata_length[:4])[0]-8
    if data_length<=0:
        return None
    total_data=[]
    while True:
        msg= s.recv(data_length)
        if not msg: break
        data_length= data_length - len(msg)
        total_data.append(msg)
        if data_length==0:
          break
    ret= b''.join(total_data)
    return ret

def unpackage(data):
    ret={}
    lines= data.split(b'/')
    lines.pop() # pop b''
    for line in lines:
        kv= line.split(b'@=')
        if len(kv)==2:
            ret[kv[0]]= kv[1].replace(b'@S',b'/').replace(b'@A',b'@')
        else:
            ret[len(ret)]= kv[0].replace(b'@S',b'/').replace(b'@A',b'@')

    return ret

def main(roomid='633144'):
    danmu=douyudanmu(roomid)
    while True:
      s=danmu.get_danmu()
      if len(s)!=0:
        print s

if __name__=='__main__':
    url= sys.argv[1] if len(sys.argv)>1 else '633144'
    main(url)
