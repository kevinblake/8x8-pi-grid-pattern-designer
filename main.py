import tornado.httpserver
import tornado.ioloop
import tornado.web
import threading
import GridThread

g = GridThread.GridThread()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
		self.render("grid.html")

class SendIcon(tornado.web.RequestHandler):
    def post(self):
		pattern = self.request.arguments.get("v")
		arrayPattern = eval(pattern[0])
		hexdata = [chr(item) for item in arrayPattern]
		self.write("Done")
		g.ActivatePattern(arrayPattern)

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/SendIcon", SendIcon),
])

if __name__ == "__main__":
	try:
		g.begin()
		http_server = tornado.httpserver.HTTPServer(application)
		http_server.listen(8888)
		tornado.ioloop.IOLoop.instance().start()
	except	 (KeyboardInterrupt, SystemExit):
		g.stop()
