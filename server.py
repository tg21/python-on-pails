from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import os
import sys

#HTTPReuestHandler class

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):		
	#function to read/write html
	def read_text(self,file):
		with open(file,"r") as new_file:
			return new_file.read()
		
	#function to read binary files		
	def read_images(self,file):
		with open(file,"rb") as new_file:
			#return str.encode(new_file.read())
			return new_file.read()

	#GET
	def do_GET(self):
		#self.send_response(200)
		
		
		message = "<html><head><title>pyServer</title></head><body>hello there</body></html>"
		isMedia = False
		
		#self.send_header('Content-type','text/html')
		#self.end_headers()
		print(self.path)
		requested_file = "./public_html"+self.path
		if Path(requested_file).is_file():
			try:
				#file = open(requested_file,"r",)
				#html_content = file.read()
				#file.close()
				self.send_response(200)
				if requested_file.endswith('.css'):
					html_content = self.read_text(requested_file)
					self.send_header('Content-type','text/css')
					self.end_headers()
				elif requested_file.endswith('.jpg'):
					html_content = self.read_images(requested_file)
					self.send_header('Content-type','image/jpeg')
					#self.send_header("Content-length", os.path.getsize(requested_file))
					#self.send_header("content-length",sys.getsizeof(html_content))
					self.end_headers()
					isMedia = True
				elif requested_file.endswith(".js"):
					html_content = self.read_text(requested_file)
					self.send_header('content-type','application/javascript')
				else:
					html_content = self.read_text(requested_file)
					self.send_header('Content-type','text/html')
					self.end_headers()
				
			except Exception as e:
				self.send_response(300)
				self.send_header('Content-type','text/html')
				self.end_headers()
				print("error ",e )
				#html_content = "<html><head><title>pyServer</title></head><body>404 : not found</body></html>"  
				html_content = str(e)
				
		elif Path(requested_file).is_dir():
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			html_content = "<html><head><title>pyServer</title></head><body>"+str(os.listdir(requested_file))+"</body></html>"
			
		else:
			self.send_response(400)
			self.send_header('Content-type','text/html')
			self.end_headers()
			html_content = "<html><head><title>pyServer</title></head><body>404 : not found</body></html>"
		
		message = html_content
		if isMedia:
			self.wfile.write(message)
		else:
			self.wfile.write(bytes(message,"utf8"))
		return
	
def run():
	print("Starting server ...")
	server_address = ("0.0.0.0",80)
	httpd = HTTPServer(server_address,testHTTPServer_RequestHandler)
	print("running server at ",server_address)
	httpd.serve_forever()
	
	
run()