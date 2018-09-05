from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import os
import sys
from filehandler import showDir,response
#HTTPReuestHandler class

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):		
	#GET
	def do_GET(self):
		print(self.path)
		requested_file = "."+self.path
		content,mimeType,errorCode = response(requested_file)
		self.send_response(errorCode)
		self.send_header('content-type',mimeType)
		self.end_headers()
		try:
			self.wfile.write(content)
		except TypeError as e:
			self.wfile.write(bytes(content,'utf-8'))
		return
	
def run():
	print("Starting server ...")
	server_address = ("0.0.0.0",80)
	httpd = HTTPServer(server_address,testHTTPServer_RequestHandler)
	print("running server at ",server_address)
	httpd.serve_forever()
	
	
run()