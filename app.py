import argparse
from webserver import *


class IndexHandler(RequestHandler):

    def get(self):
        self.write('<h1>Hello, world!</h1>')


class ABCHandler(RequestHandler):

    def get(self):
        self.write('<h1>Hello, abc!</h1>')


def main(unix_sock, bind, port):
    application = Application([
        ('/', IndexHandler),
        ('/abc', ABCHandler),
    ])
    http_server = TCPServer(application, unix_sock, bind, port)
    http_server.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--unix_sock', default=None,
                        help='Run as unix socket')
    parser.add_argument('--bind', '-b', default='',
                        help='Specify alternate bind address ')
    parser.add_argument('--port', '-p', default=8080,
                        help='Specify alternate port [default: 8080]')
    args = parser.parse_args()
    main(unix_sock=args.unix_sock, bind=args.bind, port=args.port)
