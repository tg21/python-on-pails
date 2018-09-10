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
		queryString = self.path.split("?")
		print(queryString)
		requested_file = "./www"+queryString[0]
		if len(queryString)>1:
			data = str(queryString[1])	
		else:data = ""
		#requested_file = "./www"+self.path
		print("Get::requested file is ",requested_file)
		content,mimeType,errorCode = response(requested_file,data)
		self.send_response(errorCode)
		self.send_header('content-type',mimeType)
		self.end_headers()
		try:
			self.wfile.write(content)
		except TypeError as e:
			self.wfile.write(bytes(content,'utf-8'))
		return
	
	def do_POST(self):
		print(self.path)
		requested_file = "./www"+self.path
		print("Post::requested file is ",requested_file)
		#content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
		data = str(self.rfile.read(int(self.headers['Content-Length'])),'utf-8')# <--- Gets the data itself
		print("posted data was:::  ",data)
		content,mimeType,errorCode = response(requested_file,data)
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