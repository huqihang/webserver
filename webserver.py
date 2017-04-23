#!/usr/bin/env python

# Author: huqihang
# E-mail: huqihang@outlook.com
# Date: 2016/09/30


"""A EPOLL event driven web server."""


import time
import socket
import select


class TCPServer(object):

    def __init__(self, application, unix_sock, bind, port):
        self.application = application
        self.connections = {}
        self.requests = {}
        self.responses = {}
        if unix_sock:
            self.address_family = socket.AF_UNIX
            self.server_address = unix_sock
        else:
            self.address_family = socket.AF_INET
            self.server_address = (bind, int(port))
        self.server_bind()

    def server_bind(self):
        """bind the server to the address."""
        self.socket = socket.socket(self.address_family, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def start(self):
        """start the server."""
        self.socket.listen(5)
        print('Listening at:', self.socket.getsockname())
        self.epoll = select.epoll()
        self.epoll.register(self.fileno(), select.EPOLLIN)
        self._handle_events()

    def _handle_events(self):
        try:
            while True:
                events = self.epoll.poll(20)
                for fileno, event in events:
                    if fileno == self.fileno():
                        self._handle_accept()
                    elif event & select.EPOLLIN:
                        self._handle_request(fileno)
                    elif event & select.EPOLLOUT:
                        self._handle_response(fileno)
                    elif event & select.EPOLLHUP:
                        self._handle_finish(fileno)
        finally:
            self.epoll.unregister(self.fileno())
            self.epoll.close()
            self._server_close()

    def _handle_accept(self):
        """handle new connection."""
        client, addr = self.socket.accept()
        client.setblocking(0)
        self.connections[client.fileno()] = client
        self.epoll.register(client.fileno(), select.EPOLLIN)

    def _handle_request(self, fileno):
        """handle request event."""
        data = self.connections[fileno].recv(1024)
        host = self.connections[fileno].getsockname()[0]
        self.request = HTTPRequest(bytes.decode(data), host)
        self.responses[fileno] = self.application(self.request)
        self.epoll.modify(fileno, select.EPOLLOUT)

    def _handle_response(self, fileno):
        """handle response event."""
        self.connections[fileno].send(self.responses[fileno])
        self.connections[fileno].shutdown(socket.SHUT_RDWR)
        self.epoll.modify(fileno, 0)

    def _handle_finish(self, fileno):
        """handle finish event."""
        self.epoll.unregister(fileno)
        self.connections[fileno].close()
        del self.connections[fileno]
        del self.responses[fileno]

    def fileno(self):
        return self.socket.fileno()

    def _server_close(self):
        """close socket fd."""
        self.socket.close()


class HTTPRequest(object):

    def __init__(self, data, host):
        self.data = data
        self.host = host
        self._parse_request()

    def _parse_request(self):
        """parase request data"""
        eol = self.data.find('\r\n')
        start_line = self.data[:eol]
        if len(start_line.split(' ')) == 3:
            self.method, self.uri, self.version = start_line.split(' ')
        else:
            self.uri = None


class Application(object):

    def __init__(self, handlers):
        self.handlers = handlers

    def _get_host_handlers(self, request):
        """match the handler."""
        if request.uri:
            uri = request.uri.lower().rstrip('/')
        else:
            return None
        if uri == '': uri = '/'
        for pattern, handler in self.handlers:
            if pattern == uri:
                return handler
        return None

    def _log(self, request, code):
        """print access info."""
        print("%s - - [%s] %s %s" %
                (request.host, time.strftime("%Y-%m-%d %H:%M:%S"), code, request.uri))

    def __call__(self, request):
        handler = self._get_host_handlers(request)
        if handler:
            response = handler(request)._execute()
            self._log(request, '200')
        else:
            response = b'HTTP/1.1 404 OK\r\n'
            self._log(request, '404')
        return response


class RequestHandler(object):

    def __init__(self, request):
        self.request = request
        self.headers_buffer = b'HTTP/1.1 200 OK\r\n'

    def head(self):
        pass

    def get(self):
        pass

    def post(self):
        pass

    def delete(self):
        pass

    def put(self):
        pass

    def options(self):
        pass

    def add_header(self, keyword, value):
        """add response header."""
        self.headers_buffer += str.encode("%s: %s\r\n" % (keyword, value))

    def write(self, response_data):
        """write response body content."""
        self.add_header('server', 'app')
        self.headers_buffer += b"\r\n"  # end header
        self.response_data = self.headers_buffer + str.encode(response_data)

    def _execute(self):
        """execute factory method."""
        getattr(self, self.request.method.lower())()
        return self.response_data
