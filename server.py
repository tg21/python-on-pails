# import socket
# host = ""
# port = 8080

# c = socket.socket(socket.AF_INET, socke.SOCK_STREAM)
# c.setsocketopt(socket.SOL_SOCKET, socket.SO_REUSEADDR , 1)

# c.bind((host,port))
# c.listen(1)
# while 1:
# 	csock , caddr = c.accept()
# 	cfile = csock.makefile('rw',0)

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import os

#HTTPReuestHandler class

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    #GET
    def do_GET(self):
        self.send_response(200)
        
        
        message = "<html><head><title>pyServer</title></head><body>hello there</body></html>"
        
        self.send_header('Content-type','text/html')
        self.end_headers()
        print(self.path)
        requested_file = "./public_html"+self.path
        if Path(requested_file).is_file():
            try:
                file = open(requested_file,"r")
                html_content = file.read()
                file.close()
            except Exception as e:
                print("error ",e )
                #html_content = "<html><head><title>pyServer</title></head><body>404 : not found</body></html>"  
                html_content = str(e)
                
        elif Path(requested_file).is_dir():
            html_content = "<html><head><title>pyServer</title></head><body>"+str(os.listdir(requested_file))+"</body></html>"
            
        else:
            self.send_response(400)
            html_content = "<html><head><title>pyServer</title></head><body>404 : not found</body></html>"
            
        
        message = html_content
        self.wfile.write(bytes(message,"utf8"))
        return
    
def run():
    print("Starting server ...")
    server_address = ("0.0.0.0",80)
    httpd = HTTPServer(server_address,testHTTPServer_RequestHandler)
    print("running server at ",server_address)
    httpd.serve_forever()
    
    
run()