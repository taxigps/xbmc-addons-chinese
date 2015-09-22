# UpdateChannels.sh
#   the url for different channels varies with the channel number
#   But not all channels are valid. This scans for 4s from 1 to 1000
#   If a channel is valid, it will start download, if not it will time-out

wget http://www.tvonlinestreams.com
mv -f index.html free_playlist_0.txt
for i in {1..555}; do 
  wget http://www.tvonlinestreams.com/page/$i/
  mv -f index.html free_playlist_$i.txt
done
cat free_playlist_*.txt > free_playlist.txt
grep ".m3u8\|flv\|.smil" free_playlist.txt > free_playlist1.txt
sed -i 's/.m3u8/.m3u8\n/g' free_playlist1.txt
sed -i 's/.smil/.smil\n/g' free_playlist1.txt
sed -i 's/.flv/.flv\n/g'   free_playlist1.txt
sort -u free_playlist1.txt > free_playlist.txt
  
