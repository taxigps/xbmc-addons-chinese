#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket, select, threading, urllib2, time, struct

class flv:
    @staticmethod
    def generate_header(original_header, durations, positions, times):
        header = ''
        offset_script_len = 14
        offset_durations = original_header.find('duration')
        offset_positions = original_header.find('filepositions')
        offset_count = offset_positions + 14
        offset_prev_len = len(original_header) - 4

        s1, s2, s3 = struct.unpack('BBB', original_header[offset_script_len: offset_script_len + 3])
        script_len = (s1 << 16) | (s2 << 8) | s3

        #Adjust positions and times
        total_duration = 0
        for i in range(len(durations)):
            total_duration += durations[i]

        #Calculate the size of new header
        count = struct.unpack('>I', original_header[offset_count: offset_count + 4])[0]
        offset_times_end = offset_positions + 30 + 2 * 9 * count 
        script_len += 2 * 9 * (len(positions) - count)     #Each position and time takes 9 bytes
        count = len(positions)

        #Data before script len
        header = original_header[:offset_script_len]

        #New script len
        s1 = (script_len >> 16) & 0xFF
        s2 = (script_len >> 8) & 0xFF
        s3 = script_len & 0xFF
        header += struct.pack('BBB', s1, s2, s3)

        #Data before duration
        header += original_header[offset_script_len + 3: offset_durations + 9]

        #New duration
        header += struct.pack('>d', total_duration)

        #Data before filepositions
        header += original_header[offset_durations + 17: offset_positions]
        
        #New filepositions
        header += 'filepositions'
        header += struct.pack('B', 0x0A)
        header += struct.pack('>I', count)
        for p in positions:
            header += struct.pack('B', 0x00)
            header += struct.pack('>d', p)
        header += struct.pack('BB', 0x00, 0x05)
        
        #New times
        header += 'times'
        header += struct.pack('B', 0x0A)
        header += struct.pack('>I', count)
        for t in times:
            header += struct.pack('B', 0x00)
            header += struct.pack('>d', t)

        header += original_header[offset_times_end: offset_prev_len]

        #Previous TAG len
        script_len += 11
        header += struct.pack('>I', script_len)

        return header


    @staticmethod
    def find_index(data):
        positions = []
        times = []
        offset = data.find('filepositions')
        assert(offset != -1)

        pos_count = struct.unpack('>I', data[offset + 14: offset + 18])[0]
        offset += 18
        assert(offset + pos_count * 9 <= len(data))

        for i in range(pos_count):
            positions.append(struct.unpack('>d', data[offset + 1: offset + 9])[0])
            offset += 9

        offset = data.find('times' + '0A'.decode('hex'))
        assert(offset != -1)

        times_count = struct.unpack('>I', data[offset + 6: offset + 10])[0]
        assert(times_count == pos_count)

        offset += 10
        assert(offset + times_count * 9 <= len(data))

        for i in range(times_count):
            times.append(struct.unpack('>d', data[offset + 1: offset + 9])[0])
            offset += 9

        return positions, times


    @staticmethod
    def find_info(data):
        i = data.find('duration')
        if i == -1 or i + 17 > len(data):
            return False, [], 0, [], []
        else:
            duration = struct.unpack('>d', data[i + 9: i + 17])[0]

        start = data.find('FLV')
        offset = start
        if offset == -1:
            return False, [], 0, [], []

        offset += 13
        while offset + 15 < len(data):
            t, s1, s2, s3 = struct.unpack('BBBB', data[offset: offset + 4])
            size = (s1 << 16) | (s2 << 8) | s3
            
            if offset + 15 + size > len(data):
                return False, [], 0, [], []

            if t != 0x12:
                positions, times = flv.find_index(data)
                return True, data[start: offset], duration, positions, times

            offset += 15 + size

        return False, [], 0, [], []


    @staticmethod
    def modify_timestamp(data, starting_timestamp):
        offset = 0
        ready_data = ''

        while offset + 11 < len(data):
            t, s1, s2, s3, t1, t2, t3, t4 = struct.unpack('BBBBBBBB', data[offset: offset + 8])
            size = (s1 << 16) | (s2 << 8) | s3

            if t != 8 and t != 9 and t != 0x12:
                #Data incorrect
                return data
            
            if offset + 15 + size > len(data):
                return ready_data

            original_timestamp = (t4 << 24) | (t1 << 16) | (t2 << 8) | t3
            modified_timestamp = original_timestamp + starting_timestamp

            s4 = (modified_timestamp >> 24) & 0xFF
            s1 = (modified_timestamp >> 16) & 0xFF
            s2 = (modified_timestamp >> 8) & 0xFF
            s3 = modified_timestamp & 0xFF

            ready_data += data[offset: offset + 4] 
            ready_data += struct.pack('BBBB', s1, s2, s3, s4)
            ready_data += data[offset + 8: offset + 15 + size]

            offset += 15 + size

        return ready_data

class video_concatenate:
    def __init__(self, 
                 bind_address = ('0.0.0.0', 0),
                 user_agent = 'video_concatenate',
                 exit_timeout = 1,
                 mss = 1460,
                 debug = True,
                ):


        self.server = None
        self.agent_server = None
        self.agent_client = None

        self.total_size = 0
        self.total_seconds = 0
        self.videos = []

        self.config = {'la': bind_address,
                       'ua': user_agent,
                       'timeout': exit_timeout,
                       'mss': mss,
                       'debug': debug,
                      }

        self.thread = threading.Thread(target = self._run)
        self.running = False



    def _cleanup(self):
        if self.server:
            self.log('server closed.')
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.bind(('', 0))
            try:
                s.connect(self.server.getsockname())
            except:
                pass
            if self.thread and self.thread.isAlive():
                self.thread.join()
            s.close()
            self.server.close()
            self.server = None
        if self.agent_server:
            self.agent_server.close()
            self.agent_server = None
        if self.agent_client:
            self.agent_client.close()
            self.agent_client = None


    def __del__(self):
        self.log('Service deleted')
        self.stop()


    def _get_info(self, urls, timeout):
        infos = []
        threads = []

        def __get_info(url, info):
            s = self._connect_to_url(url)
            data = ''
            inputs = []
            outputs = [s]
            length = 0
            t = ''

            while True:
                readable, writable, _ = select.select(inputs, outputs, [], timeout)
                if len(readable) == 0 and len(writable) == 0:
                    self.log('get info error due to timeout')
                    break
                if s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR):
                    self.log('get info error due to socket error')
                    break

                if len(writable) == 1:
                    self._send_get(s, 0, url)
                    inputs = [s]
                    outputs = []

                if len(readable) == 1:
                    try:
                        tmp = s.recv(self.config['mss'])
                    except:
                        tmp = ''

                    if len(tmp) == 0:
                        self.log('get info error due to server close the socket.')
                        break

                    data += tmp
                    if length == 0 or t == '':
                        if data.find('\r\n\r\n') == -1:
                            continue
                        i = data.upper().find('CONTENT-LENGTH')
                        if i == -1:
                            self.log('get info error due to no content-length')
                            break
                        length = int(data[i:].split('\r\n')[0].replace(' ', '').split(':')[1])

                        i = data.upper().find('CONTENT-TYPE')
                        if i == -1:
                            self.log('get info error due to no content-type')
                            break
                        t = data[i:].split('\r\n')[0].replace(' ', '').split(':')[1]

                    ret, header, duration, positions, times = flv.find_info(data)
                    if ret == False:
                        continue

                    info.append(length)
                    info.append(t)
                    info.append(header)
                    info.append(duration)
                    info.append(positions)
                    info.append(times)

                    self.log('Length: %d' % (length))
                    self.log('Meta: %d' % (len(header)))
                    self.log('Pos Count: %d' % (len(positions)))
                    output = ''
                    for i in range(len(positions)):
                        output += '{%f, %d}, ' % (times[i], int(positions[i]))
                    self.log(output)
                    break

            s.close()
            return

        if len(urls) == 0:
            return 0, [], 0, 0, 0, 0, 0

        #Get info concurrently. 
        for url in  urls:
            infos.append([])
            t = threading.Thread(target = __get_info, args = [url, infos[-1]])
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        videos = []
        total_size = 0
        total_seconds = 0
        durations = []
        positions = []
        times = []

        increased = 0
        for i in range(1, len(infos)):
            if len(infos[i]) == 0:
                return 0, [], 0, 0, 0, 0, 0
            increased += len(infos[i][4])
        increased = increased * 2 * 9
        self.log('Increased: %d' % (increased))

        #Process all infomations
        for i in range(len(infos)):
            if len(infos[i]) == 0:
                return 0, [], 0, 0, 0, 0, 0

            info = infos[i]
            length = info[0]
            
            if i != 0:
                length -= len(info[2])
                for j in range(len(info[4])):
                    positions.append(info[4][j] + total_size - len(info[2]))
                    times.append(info[5][j] + total_seconds)
            else:
                length += increased
                for j in range(len(info[4])):
                    positions.append(info[4][j] + increased)
                    times.append(info[5][j] + total_seconds)

            videos.append({'url': urls[i],
                           'size': length,
                           'content-type': info[1],
                           'header_offset': len(info[2]),
                           'duration': info[3],
                           'starting_bytes': total_size,
                           'starting_ms': int(total_seconds * 1000)})


            durations.append(info[3])

            total_size += length
            total_seconds += info[3]
            self.log(videos[-1])

        output = ''
        for i in range(len(positions)):
            output += '{%f, %d}, ' % (times[i], int(positions[i]))
        self.log(output)

        header = flv.generate_header(infos[0][2], durations, positions, times)
        self.log('Total length: %d' % (total_size))

        return increased, videos, header, total_size, total_seconds, positions, times


    def _resp_head(self, starting_bytes, content_type):
        self.log('responde starting bytes: %d' % (starting_bytes))
        header = 'HTTP/1.1 206 Partial Content\r\n' \
                 'Content-Type: %s\r\n'             \
                 'Accept-Ranges: bytes\r\n'         \
                 'Content-Length: %d\r\n'           \
                 'Content-Range: bytes %d-%d/%d\r\n'\
                 'Connection: close\r\n\r\n' % (content_type, 
                                                self.total_size - starting_bytes,
                                                starting_bytes,
                                                self.total_size - 1,
                                                self.total_size)

        return header


    def _send_get(self, s, starting_bytes, url):
        self.log('send GET request(%d) to %s' % (starting_bytes, url))

        #Calculate the host and path
        host = url.split('/')[2]
        path = '/' + '/'.join(url.split('/')[3:])

        #Send GET request
        s.send('GET %s HTTP/1.1\r\n'
               'Range: bytes=%d-\r\n'
               'Host: %s\r\n'
               'User-Agent: %s\r\n'
               'Accept: */*\r\n\r\n' % (path, starting_bytes, host, self.config['ua']))


    def _find_starting(self, data):
        requested_start = 0
        skip_bytes = 0
        i = 1
        for line in data.split('\r\n'):
            if line[:5].upper() == 'RANGE':
                requested_start = int(line.replace(' ', '').split('=')[1].split('-')[0])
                break
        self.log('')
        self.log('requested starting bytes: %d' % (requested_start))

        #Adjust the starting bytes to keyframe
        keyframe_start = requested_start
        if keyframe_start != 0:
            for i in range(1, len(self.positions)):
                if requested_start < self.positions[i]:
                    break
            keyframe_start = self.positions[i - 1]
            self.log('keyframe starting bytes: %d' % (self.positions[i - 1]))
            self.log('keyframe starting timestamp: %f' % (self.times[i - 1]))

        index = 0
        while index < len(self.videos) - 1:
            if requested_start < self.videos[index + 1]['starting_bytes']:
                break
            index += 1
        relative_start = requested_start - self.videos[index]['starting_bytes']
        self.log('video index: %d' % (index))

        if index == 0:
            if relative_start != 0:
                relative_start -= self.increased
        else:
            relative_start += self.videos[index]['header_offset']
        self.log('relative starting bytes: %d' % (relative_start))
        self.log('')

        return requested_start, relative_start, index, int(requested_start - keyframe_start)


    def _connect_to_url(self, url):
        #Get host and path
        port = 80
        host = url.split('/')[2]
        if ':' in host:
            host, port = host.split(':')
            port = int(port)

        #Connect to remote
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.bind(('', 0))
        s.setblocking(False)
        try:
            s.connect((host, port))
        except:
            pass
        return s


    def _run(self):
        self.log('running')
        inputs = [self.server]
        outputs = []
        readable = []
        writable = []
        recv_buffer = ''
        send_buffer = ''
        header = ''
        starting_bytes = 0
        index = 0
        skip_header = True
        skip_meta = True
        modify_timestamp = True
        remaining_bytes = 0

        def _clean_socket(s):
            if s is None:
                return
            for arr in [inputs, outputs, readable, writable]:
                if s in arr:
                    arr.remove(s)
            s.close()

        while True: 
            while None in inputs:
                inputs.remove(None)
            while None in outputs:
                outputs.remove(None)
                
            if len(inputs) == 0:
                self.log('no inputs')
                break

            try:
                readable, writable, _ = select.select(inputs, outputs, [], self.config['timeout'])
            except:
                self.log('select error')
                break

            if self.running == False:
                self.log('Stopped')
                break

            if not readable and not writable and self.agent_server == None and self.agent_client == None:
                #Timeouts
                self.log('select timeout')
                break

            #Loop to process all sockets in readable array
            for s in readable:
                if s == self.server:
                    self.log('new connection')
                    #Accept new connection
                    _clean_socket(self.agent_server)
                    _clean_socket(self.agent_client)
                    self.agent_server = self.server.accept()[0]
                    self.agent_server.setblocking(False)
                    self.agent_client = None
                    inputs.append(self.agent_server)
                    recv_buffer = ''
                    send_buffer = ''
                    header = ''
                    starting_bytes = 0
                    relative_starting_bytes = 0
                    index = 0
                    continue

                err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if err:
                    if s == self.agent_client:
                        self.log('agent client error: %d' % (err))
                    else:
                        self.log('agent server error: %d' % (err))
                    #Process socket error
                    _clean_socket(self.agent_server)
                    _clean_socket(self.agent_client)
                    self.agent_server = None
                    self.agent_client = None
                    continue

                if s == self.agent_client:
                    #Receive data from remote
                    try:
                        tmp = self.agent_client.recv(self.config['mss'])
                    except:
                        tmp = None

                    if not tmp:
                        #No more data from remote
                        _clean_socket(self.agent_client)
                        self.agent_client = None
                        if index + 1 < len(self.videos):
                            index += 1
                            self.log('switch to vedio %d' % (index))
                            self.log('starting timestamp: %f' % (self.videos[index]['starting_ms']))
                            url = self.videos[index]['url']
                            self.agent_client = self._connect_to_url(url)
                            outputs.append(self.agent_client)
                            relative_starting_bytes = self.videos[index]['header_offset']
                            skip_meta = False
                            modify_timestamp = True
                            skip_header = True
                            skip_bytes = 0
                        continue

                    recv_buffer += tmp

                    ready = True

                    #Skip header
                    if skip_header == True:
                        i = recv_buffer.find('\r\n\r\n')
                        if i == -1:
                            self.log('header not complete')
                            ready = False
                        else:
                            self.log('header skipped')
                            recv_buffer = recv_buffer[i + 4:]
                            skip_header = False

                    #Skip meta data
                    if ready == True and skip_meta == True:
                        if len(recv_buffer) < self.videos[index]['header_offset']:
                            ready = False
                            self.log('meta not complete (%d < %d)' % (len(recv_buffer), self.videos[index]['header_offset']))
                        else:
                            self.log('meta skipped')
                            recv_buffer = recv_buffer[self.videos[index]['header_offset']:]
                            skip_meta = False

                    if ready == True and skip_bytes > 0:
                        if len(recv_buffer) > skip_bytes:
                            recv_buffer = recv_buffer[skip_bytes:]
                            skip_bytes = 0
                        else:
                            skip_bytes -= len(recv_buffer)
                            recv_buffer = ''
                            ready = False

                    if ready == True and modify_timestamp == True:
                        ready_data = flv.modify_timestamp(recv_buffer, self.videos[index]['starting_ms'])
                    else:
                        ready_data = recv_buffer

                    #Check receive buffer
                    if len(ready_data) == 0:
                        ready = False

                    if ready == False:
                        continue

                    #Receive buffer is ready
                    send_buffer += ready_data
                    recv_buffer = recv_buffer[len(ready_data):]

                    if self.agent_server not in outputs:
                        outputs.append(self.agent_server)

                    remaining_bytes -= len(ready_data)

                    if remaining_bytes == 0:
                        _clean_socket(self.agent_client)
                        self.agent_client = None
                        if index + 1 < len(self.videos):
                            index += 1
                            self.log('switch to vedio %d' % (index))
                            self.log('starting timestamp: %f' % (self.videos[index]['starting_ms']))
                            url = self.videos[index]['url']
                            self.agent_client = self._connect_to_url(url)
                            outputs.append(self.agent_client)
                            relative_starting_bytes = self.videos[index]['header_offset']
                            skip_meta = False
                            modify_timestamp = True
                            skip_header = True
                            skip_bytes = 0

                    continue

                if s == self.agent_server:
                    try:
                        tmp = self.agent_server.recv(self.config['mss'])
                    except:
                        tmp = None
                    
                    if not tmp:
                        #Local closed the socket
                        _clean_socket(self.agent_server)
                        _clean_socket(self.agent_client)
                        self.agent_server = None
                        self.agent_client = None
                        continue

                    #Append to header
                    header += tmp

                    if header.find('\r\n\r\n') == -1:
                        #Header not complete
                        continue

                    starting_bytes, relative_starting_bytes, index, skip_bytes = self._find_starting(header)

                    if starting_bytes < self.total_size:
                        if header[:3].upper() == 'GET':
                            send_buffer = self._resp_head(starting_bytes, self.videos[index]['content-type'])
                            url = self.videos[index]['url']
                            _clean_socket(self.agent_client)
                            self.agent_client = self._connect_to_url(url)
                            outputs.append(self.agent_client)

                            if starting_bytes == 0:
                                send_buffer += self.header
                                skip_meta = True
                            else:
                                skip_meta = False

                            if index == 0:
                                modify_timestamp = False
                            else:
                                modify_timestamp = True

                            skip_header = True
                            header = ''
                            continue

                        if header[:4].upper() == 'HEAD':
                            self.agent_server.send(self._resp_head(starting_bytes, self.videos[index]['content-type']))

                    header = ''
                    _clean_socket(self.agent_server)
                    self.agent_server = None

                    continue

                if s in inputs:
                    inputs.remove(s)

            #Loop to process all sockets in readable array
            for s in writable:
                if s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR):
                    #Process socket error
                    _clean_socket(self.agent_client)
                    _clean_socket(self.agent_server)
                    self.agent_client = None
                    self.agent_server = None
                    continue

                if s == self.agent_client:
                    #Send GET request
                    self._send_get(self.agent_client, relative_starting_bytes, url)
                    remaining_bytes = self.videos[index]['size'] - relative_starting_bytes
                    if index == 0:
                        remaining_bytes -= self.increased
                    outputs.remove(self.agent_client)
                    if self.agent_client not in inputs:
                        inputs.append(self.agent_client)
                    continue

                if s == self.agent_server:
                    #Send data to local socket
                    sent = self.agent_server.send(send_buffer)

                    if sent == len(send_buffer):
                        #All data sent
                        outputs.remove(self.agent_server)

                        if self.agent_client == None:
                            _clean_socket(self.agent_server)
                            self.agent_server = None
                        elif self.agent_client not in inputs:
                            inputs.append(self.agent_client)
                        send_buffer = ''

                    else:
                        #Partial data sent
                        send_buffer = send_buffer[sent:]
                        if self.agent_client in inputs:
                            inputs.remove(self.agent_client)

                    continue

                if s in inputs:
                    inputs.remove(s)


        if self.running == True:
            #Cleanup
            self.server.close()
            self.server = None
            self._cleanup()

        self.log('thread exit')


    #APIs
    def log(self, s):
        if self.config['debug'] == 1:
            print('[%s][video_concatenate]%s' % (time.time(), s))


    #Start agent thread
    def start(self, urls, get_timeout = 30):
        self.stop()
        self.running = True

        #Create server socket
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.server.bind(self.config['la'])
        self.server.listen(5)
        self.server.setblocking(False)

        address, port = self.server.getsockname()
        self.log('server listen at %s:%d' % (address, port))

        #Get size and content type
        self.increased, self.videos, self.header, self.total_size, self.total_seconds, self.positions, self.times = self._get_info(urls, get_timeout)

        if len(self.videos) == 0 or len(self.videos) != len(urls):
            self.log('Failed to process urls.')
            raise

        #Set video variables

        #Start thread.
        self.thread = threading.Thread(target = self._run)
        self.thread.start()


    def stop(self):
        self.running = False
        self._cleanup()
        self.thread = None


    def get_port(self):
        try:
            return self.server.getsockname()[1]
        except:
            return 0


if __name__ == '__main__':
    urls = [line.rstrip('\n') for line in open('urls.txt')]
    urls = urls[0:]
    vc = video_concatenate(('0.0.0.0', 7777), exit_timeout = 10)
    vc.start(urls)
    #vc.stop()

    #vc.add_agent(urls)
    #vc.delete_agent(url)
    #vc.delete_agent(url)
    #vc.add_agent(urls)
    #ss = StreamServer()
    #url = ss.start(urls)
    #print(url)
    ##print(ss.getSizes(urls))

    #port = 80
    #host = url.split('/')[2]
    #path = '/' + '/'.join(url.split('/')[3:])
    #if ':' in host:
    #    host, port = host.split(':')
    #    port = int(port)

    #c = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    #c.bind(('', 0))
    #c.connect((host, port))
    #c.send('GET / HTTP/1.1\r\n'
    #       'Range: bytes=0-\r\n')
    #c.close()
