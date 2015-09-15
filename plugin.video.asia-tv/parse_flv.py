#!/usr/bin/python
import os

new_dict={} # for newly generated live channles
old_dict={} # for channels that are in the url_list.txt 
old_list=[]
f=open('url_map.txt')
# create old_dic
for i in f:
    if not (i.startswith('Y') or i.startswith('N')):
        continue
    S, n, url = i.split()
    j=url.split('/')
    for k in j:
        if k.startswith('channel'):
            old_list.append(k)
            old_dict[k]=[S,n,url]
f.close

# genetate new dict and add new channels
new_list=os.listdir('./') # get the file list 
for l in new_list:
    if l.startswith('channel'):
        new_dict[l]='Y'
        if not (l in old_dict):
            name,flv=l.split('.')
            print 'echo "Y'+' '+name+' http://fms.cntv.lxdns.com/live/flv/' + l +'">> url_map.txt'

# these in old_list but not on new shall be disabled
print '##########'
for i in old_dict:
    if not (i in new_dict):
        if old_dict[i][0]=='Y':
            print 'disable '+i
            # old_line=old_dict[i][0]+' '+old_dict[i][1] +' '+old_dict[i][2]
            # new_line='N'           +' '+old_dict[i][1] +' '+old_dict[i][2]  
            # print "sed -i 's/" + old_line+'/' + new_line +"/' url_map.txt"













