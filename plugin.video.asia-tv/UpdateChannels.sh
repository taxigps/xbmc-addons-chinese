# UpdateChannels.sh
#   the url for different channels varies with the channel number
#   But not all channels are valid. This scans for 4s from 1 to 1000
#   If a channel is valid, it will start download, if not it will time-out
for i in {1..1000}; do 
  timeout 4  wget --tries=1 http://fms.cntv.lxdns.com/live/flv/channel$i.flv
done
ls *flv|awk '{print "rm -f",$1,"; touch", $1}' | sh


