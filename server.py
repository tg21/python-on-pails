from http.server import BaseHTTPRequestHandler, HTTPServer
from filehandler import response
from extraFunctions import initials
import os
dir_path,express_dict,mimeTypes,host,port,wildcard,project_dir,encryption,logging = initials()
#HTTPReuestHandler class


class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):		
	#GET
	def do_GET(self):
		print(self.path)
		queryString = self.path.split("?")
		print(queryString)
		express = express_dict.get(queryString[0],False)
		if express:
			requested_file = dir_path+project_dir+express
		else:
			requested_file = dir_path+project_dir+queryString[0]
		
			
		if len(queryString)>1:
			data = str(queryString[1])
		else:data = ""
		print("Get::requested file is ",requested_file)
		content,mimeType,errorCode = response(requested_file,data,mimeTypes)
		self.send_response(errorCode)
		self.send_header('content-type',mimeType)
		self.end_headers()
		try:
			self.wfile.write(content)
		except TypeError:
			self.wfile.write(bytes(content,'utf-8'))
		return
	
	def do_POST(self):
		print(self.path)
		express = express_dict.get(self.path,False)
		if express:
			requested_file = dir_path+project_dir+express
		else:
			requested_file = dir_path+project_dir+self.path
		print("Post::requested file is ",requested_file)
		#content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
		data = str(self.rfile.read(int(self.headers['Content-Length'])),'utf-8')# <--- Gets the data itself
		print("posted data was:::  ",data)
		content,mimeType,errorCode = response(requested_file,data,mimeTypes)
		self.send_response(errorCode)
		self.send_header('content-type',mimeType)
		self.end_headers()
		try:
			self.wfile.write(content)
		except TypeError:
			self.wfile.write(bytes(content,'utf-8'))
		return		
	
def run():
	print("Starting server ...")
	server_address = (host,port)
	httpd = HTTPServer(server_address,testHTTPServer_RequestHandler)
	print("running server at ",server_address)
	httpd.serve_forever()
	
	
run()
