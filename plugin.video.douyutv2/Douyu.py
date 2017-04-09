#!/usr/bin/env python2
import thread
import urllib2
import SocketServer
import time
import threading
from SimpleHTTPServer import SimpleHTTPRequestHandler
import logging

#Initialize logging
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(levelname)s][%(funcName)s] %(message)s')

#Global variables
douyu_proxy_handler = None
douyu_http_server_idle_event = threading.Event()

class Douyu_Proxy_Handler(object):
    response = None
    headers = ''
    data_buffer = ''
    buffer_max = 1024 * 1024
    read_size = 10 * 1024

    def start(self, url):
        if ((self.response is None) or
            (self.headers == '')):
            try:
                self.response = urllib2.urlopen(urllib2.Request(url, headers={'User-Agent': 'kodi'}))
                self.headers = 'HTTP/1.1 200 OK\r\n' + ''.join(self.response.info().headers) + '\r\n'
                logging.debug('Connected to %s' % (url))
                return True
            except:
                self.response = None
                self.headers = ''
                logging.debug('Unable to connect to %s' %(url))
                return False
        else:
            logging.debug('Already connected to %s' %(url))
            return True

    def send_header(self, request_handler):
        if (self.headers == ''):
            logging.debug('No header')
            request_handler.send_error(404)
            return False
        else:
            request_handler.wfile.write(self.headers)
            return True
        
    def do_head(self, request_handler, url):
        if (self.start(url) == False):
            return

        self.send_header(request_handler)


    def do_get(self, request_handler, url):
        if (self.start(url) == False):
            return

        if (self.send_header(request_handler) == False):
            return

        offset = 0
        try:
            while True:
                self.data_buffer += self.response.read(self.read_size) 
                request_handler.wfile.write(self.data_buffer[offset:])

                if (len(self.data_buffer) > self.buffer_max):
                    logging.debug('Reset buffer')
                    self.data_buffer = ''
                    self.headers = ''
                    offset = 0
                else:
                    offset = len(self.data_buffer)

        except:
            logging.debug('Done')


class HTTP_Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global douyu_proxy_handler
        global douyu_http_server_idle_event
        douyu_http_server_idle_event.set()
        if (douyu_proxy_handler is None):
            douyu_proxy_handler = Douyu_Proxy_Handler()
        douyu_proxy_handler.do_get(self, self.path[1:])
        douyu_http_server_idle_event.clear()

    def do_HEAD(self):
        global douyu_proxy_handler
        global douyu_http_server_idle_event
        douyu_http_server_idle_event.set()
        if (douyu_proxy_handler is None):
            douyu_proxy_handler = Douyu_Proxy_Handler()
        douyu_proxy_handler.do_head(self, self.path[1:])
        douyu_http_server_idle_event.clear()

class Douyu_HTTP_Server(object):
    def thread_entry(self):
        self.httpd.serve_forever()

    def proxy(self, douyu_url, address = 'localhost', start_port = 10000):
        while True:
            try:
                self.httpd = SocketServer.TCPServer(('', start_port), HTTP_Handler)
                break
            except:
                logging.debug('Unable to bind to %d' % (start_port))
                start_port += 1
                if (start_port > 65535):
                    logging.error('No available port')
                    return ''
        thread.start_new_thread(self.thread_entry, ())
        url = 'http://%s:%d/%s' % (address, start_port, douyu_url)
        logging.info('Douyu URL: %s' % (url))
        return url

    def wait_for_idle(self, wait_option):
        global douyu_http_server_idle_event
        while (douyu_http_server_idle_event.wait(wait_option) == True):
            time.sleep(wait_option)
        self.exit()

    def exit(self):
        self.httpd.shutdown()
        logging.info('Proxy exit')
