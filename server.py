from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import requests
import urlparse
import urllib
from sys import argv
from node import Node
from threading import Thread
from time import sleep


class NodeRequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse.urlparse(self.path)
        path = parsed.path
        global node
        print("REQ PATH: {}".format(path))
        if path == "/ping":
            self._set_headers()
            resp = {'type': 'ACK', 'incarnation': node.incarnation}
            self.wfile.write(json.dumps(resp))
        elif path == "/ping_req":
            print("=======PING REQ======")
            params = dict(urlparse.parse_qs(parsed.query))
            target = params['target'][0]
            resp = node.process_ping_req(target)
            self._set_headers()
            self.wfile.write(json.dumps(resp))
        # elif self.path = "/join":

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        self._set_headers()
        self.wfile.write("<html><body><h1>POST!</h1></body></html>")


def ping():
    global node
    while True:
        sleep(3)
        node.ping()


def setup_node_thread():
    node_thread = Thread(target=ping)
    node_thread.setDaemon(True)
    node_thread.start()
    return node_thread


def run(server_class=HTTPServer, handler_class=NodeRequestHandler, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()

if __name__ == "__main__":
    if len(argv) == 2:
        config_file = argv[1]
        node = Node(config_file)
        node_thread = setup_node_thread()
        run()
    else:
        config_file = argv[1]
        port = int(argv[2])
        node = Node(config_file)
        node_thread = setup_node_thread()
        run(port=port)
    node_thread.join()
