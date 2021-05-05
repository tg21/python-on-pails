import sys
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer # ,HTTPServer,
import json
dir_path = (str(os.path.dirname(os.path.realpath(__file__))) + "/")
# sys.path.insert(0, '{}/server'.format(dir_path))
from server.settings import config,server_info
from server.responseHandler import ResponseHandler
from server.misc import jsonify,dict2obj,parseJsonToClass
from server.internalModels import Req,ResoponseClass
# sys.path.insert(0, '{}/{}'.format(dir_path,config.views))
# sys.path.insert(0, '{}/{}'.format(dir_path,config.controllers))

from mvc.views.views import views
from mvc.controllers.routes import getRoutes,postRoutes
import ssl
from http import HTTPStatus
import socket


# from filehandler import response
# from extraFunctions import initials


# HTTPReuestHandler class
# if(len(sys.argv) > 1 or True):
#     if(True or sys.argv[1] == "-g"):  # g for global
#         dir_path = os.getcwd()
#         project_dir = ""


class PyOPSever(BaseHTTPRequestHandler):

    def FormatRequestData(self,model,types=None):
        queryString = self.path.split("?")
        if(self.command == "GET"):
            if len(queryString) > 1:
                data = str(queryString[1])
            else:
                data = ""
        else:
            data = str(self.rfile.read(int(self.headers['Content-Length'])), 'utf-8')
        if(data != None and data!=""):
            try:
                data = json.loads(data)
            except Exception:
                data = jsonify(data)
        if model is not None:
            if types is None:
                data = parseJsonToClass(data,model)
            else:
                output = []
                for i in model:
                    tp = types.get(i,None)
                    if tp is None:
                        output.append(data[i])
                    else:
                        output.append(parseJsonToClass(data[i],tp))
                return output
        else:
            # data = jso
            data = dict2obj(data)
        # data = dict2obj({
        #     'method':rtype,
        #     'data':data,
        # })
        return data
        # return Req(self.command,data)

    def GETPOST(self):  # rtype stands for request type
        # print("obj addr after int is :: ",id(self),"==>",int(str(id(self))))
        # print("Client= ",self.client_address)
        response:ResponseHandler = None
        queryString = self.path.split("?")

        
        #checking routes in views.py
        route = views.get(queryString[0], False)
        if route:
            if(callable(route)):
                response = ResponseHandler(route,'staticFunction',None).respond()
            elif(type(route) is str):
                request = dir_path+config.static+route
                response = ResponseHandler(request,'static',None).respond()
        else:
            #checking routes in routes.py(controllers)
            if(self.command == "GET"):
                route =  getRoutes.get(queryString[0], False)
            else:
                route =  postRoutes.get(queryString[0], False)
            if route:
                inputModel = None
                customResponse = None
                if(type(route) == dict):
                    route,inputModel,customResponse = route.get('action'),route.get('input',object),route.get('customResponse',None)
                if(callable(route)):
                    if inputModel is None:
                        params = route.__code__.co_varnames
                        types = route.__annotations__
                        response = ResponseHandler(route,'controllerFunction',self.FormatRequestData(params,types),customResponse,unpack=True).respond()
                    else:
                        response = ResponseHandler(route,'controllerFunction',self.FormatRequestData(inputModel),customResponse,unpack=False).respond()
                elif(type(route) == str and route.endswith('.py')):
                    request = dir_path+config.controllers+route
                    response = ResponseHandler(request,'controllerFile',self.FormatRequestData(inputModel),customResponse).respond()
                else:
                    #TODO:better exception here
                    raise Exception
            else:
                request = dir_path+config.static+queryString[0]
                response = ResponseHandler(request,'static',None).respond()

        self.send_custom_response(response)
        

    def send_custom_response(self,response:ResoponseClass):
        self.log_request(response.responseCode)
        self.send_response_only(response.responseCode)
        self.send_header('date',self.date_time_string())
        self.send_header('content-type', response.mimeType)
        self.send_header('server',server_info.server_name + ' '+ server_info.server_version)
        self.end_headers()
        if(type(response.content) is not bytes):
            if(type(response.content) is not str):
                response.content = bytes(str(response.content), 'utf-8')
            else:
                response.content = bytes(response.content, 'utf-8')
        self.wfile.write(response.content)

    def handle_one_request(self):
        """Handle a single HTTP request.
        Overridden from base class

        """
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                if(config.fool_nmap):
                    self.send_custom_response(ResoponseClass(config.fool_nmap_content,200,'application/json'))
                else:
                    self.send_error(
                        HTTPStatus.NOT_IMPLEMENTED,
                        "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            method()
            self.wfile.flush() #actually send the response if not already done.
        except socket.timeout as e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

    # GET
    def do_GET(self):
        self.GETPOST()
        return

    def do_POST(self):
        self.GETPOST()
        return

def run():
    print("Starting server ...")
    server_address = (config.host, 443)
    #httpd = HTTPServer(server_address, PyOPSever)
    httpd = ThreadingHTTPServer(server_address, PyOPSever)
    print("running server at ", server_address)
    print("WD :- ", dir_path + config.static)
    if config.enableTLS:
        httpd.socket = ssl.wrap_socket (httpd.socket, 
            keyfile= config.PATH_TLS_KEY_FILE, 
            certfile= config.PATH_TLS_CERT_FILE, server_side=True)
        print("Listening Securely")
    httpd.serve_forever()


run()
