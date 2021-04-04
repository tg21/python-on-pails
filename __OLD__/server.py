from http.server import BaseHTTPRequestHandler, HTTPServer
from filehandler import response
from extraFunctions import initials
import os
import sys
dir_path,express_dict,mimeTypes,host,port,wildcard,project_dir,encryption,logging = initials()
#HTTPReuestHandler class
if(len(sys.argv)>1):
	if(sys.argv[1]=="-g"):#g for global
		dir_path = os.getcwd()
		project_dir=""

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
	
	def GETPOST(self,rtype):#rtype stands for request type
		# print("obj addr after int is :: ",id(self),"==>",int(str(id(self))))
		# print("Client= ",self.client_address)
		queryString = self.path.split("?")
		express = express_dict.get(queryString[0],False)
		if express:
			requested_file = dir_path+project_dir+express
		else:
			requested_file = dir_path+project_dir+queryString[0]

		if(rtype=="get"):
			if len(queryString)>1:
				data = str(queryString[1])
			else:data = ""
		else:
			data = str(self.rfile.read(int(self.headers['Content-Length'])),'utf-8')

		print(requested_file)
		data=data+"&self="+str(id(self))

		content,mimeType,errorCode = response(requested_file,data,mimeTypes)
		self.send_response(errorCode)
		self.send_header('content-type',mimeType)
		self.end_headers()
		try:
			self.wfile.write(content)
		except TypeError:
			self.wfile.write(bytes(content,'utf-8'))
		return	

	#GET
	def do_GET(self):
		self.GETPOST("get")
		return
	
	def do_POST(self):
		self.GETPOST("post")
		return		
	
def run():
	print("Starting server ...")
	server_address = (host,port)
	httpd = HTTPServer(server_address,testHTTPServer_RequestHandler)
	print("running server at ",server_address)
	print("WD :- ",dir_path+project_dir)
	httpd.serve_forever()
	
	
run()
