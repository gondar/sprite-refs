import http.server, functools, sys
d=sys.argv[1]; p=int(sys.argv[2])
http.server.ThreadingHTTPServer(('127.0.0.1',p),functools.partial(http.server.SimpleHTTPRequestHandler,directory=d)).serve_forever()
