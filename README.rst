Python WebServer
================
A EPOLL event driven web server, it's not enough completed for production, just for study.

Hello World Example
-------------------

.. code:: python

    import argparse
    from webserver import *


    class IndexHandler(RequestHandler):

        def get(self):
            self.write('<h1>Hello, world!</h1>')


    def main(unix_sock, bind, port):
        application = Application([
            ('/', IndexHandler)
        ])
        http_server = TCPServer(application, unix_sock, bind, port)
        http_server.start()


    if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument('--unix_sock', default=None,
                            help='Run as unix socket')
        parser.add_argument('--bind', '-b', default='',
                            help='Specify alternate bind address ')
        parser.add_argument('--port', '-p', default=8080,
                            help='Specify alternate port [default: 8080]')
        args = parser.parse_args()
        main(unix_sock=args.unix_sock, bind=args.bind, port=args.port)

Start
-----

``$: python3 app.py -p 8888``
OR
``$: python3 app.py --unix_sock /tmp/test.sock``

Application
-----------

实例化Application加载handler，并传入TCPServer

.. code:: python

    application = Application([
        ('/', IndexHandler)
    ])
    http_server = TCPServer(application, unix_sock, bind, port)

处理请求时会在Application的_get_host_handlers方法里匹配handler

.. code:: python

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

TCP Server接受请求后执行Application.__call__

.. code:: python

    class TCPServer(object):
        
        ...

        def _handle_request(self, fileno):
            ...
            self.responses[fileno] = self.application(self.request)
            ...

    ...

    class Application(object):

        ...

        def __call__(self, request):
            handler = self._get_host_handlers(request)
            ...

最后执行RequestHandler的工厂函数

.. code:: python

    class RequestHandler(object):
        
        ...

        def _execute(self, fileno):
            ...
            getattr(self, self.request.method.lower())()
            ...
