#! /bin/env python

from SensorRequestHandler import SensorRequestHandler
from ThreadingHTTPServer import ThreadingHTTPServer
import queue
import time

PORT = 5000
MAX_BUFFER_SIZE = 1000

def run(port, handler_class, server_class=ThreadingHTTPServer):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting HTTP server on port {0}'.format(port))
    httpd.serve_forever()

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        PORT=int(argv[1])
    run(port=PORT, handler_class=SensorRequestHandler)
