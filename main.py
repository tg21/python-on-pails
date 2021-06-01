import sys
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
dir_path = (str(os.path.dirname(os.path.realpath(__file__))) + "/")
# sys.path.insert(0, '{}/server'.format(dir_path))
from server.settings import config,server_info
from server.responseHandler import ResponseHandler
from server.misc import jsonify,dict2obj,parseJsonToClass
from server.internalModels import Req,ResoponseClass,PyopReq
# sys.path.insert(0, '{}/{}'.format(dir_path,config.views))
# sys.path.insert(0, '{}/{}'.format(dir_path,config.controllers))

from mvc.views.views import views
from mvc.controllers.routes import getRoutes,postRoutes
from http import HTTPStatus
from socket import timeout
from socketserver import ThreadingMixIn


# from filehandler import response
# from extraFunctions import initials


# HTTPReuestHandler class
# if(len(sys.argv) > 1 or True):
#     if(True or sys.argv[1] == "-g"):  # g for global
#         dir_path = os.getcwd()
#         project_dir = ""

def e(x):
    a = 3


class PyOPSever(BaseHTTPRequestHandler):

    def FormatRequestData(self,model,types=None,argsCount=0):
        queryString = self.path.split("?")
        if(self.command == "GET"):
            if len(queryString) > 1:
                data = str(queryString[1])
            else:
                data = ""
        else:
            data = str(self.rfile.read(int(self.headers['Content-Length'])), 'utf-8')

        data = self.ParseRequestDataInToObject(data,model,types,argsCount)
        # data = dict2obj({
        #     'method':rtype,
        #     'data':data,
        # })
        return data
        # return Req(self.command,data)


    def ParseRequestDataInToObject(self,data,model,types=None,argsCount=0):
        if(type(data) == str and data!=""):
            try:
                data = json.loads(data)
            except Exception as e:
                print(e)
                data = jsonify(data)
        elif(type(data) is not dict):
            #TODO: Better Exception for unsupported format data
            raise Exception
        if model is not None:
            if types is None:
                # making object based on inputmodel key in route's dictionary
                data = parseJsonToClass(data,model)
            else:
                # making object based on parameters of controller function
                output = []
                if(argsCount == 1): # mapping one dict to one class object (most common case of POST APIs)
                    tp = types.get(model[0],None)
                    output.append(parseJsonToClass(data,tp))
                else:
                    for i in range(argsCount): # mapping members in one dict to multiple function arguments (common case for GET APIs)
                        tp = types.get(model[i],None)
                        if tp is None:
                            output.append(data[i])
                        elif tp is PyopReq:
                            output.append(self)
                        else:
                            output.append(parseJsonToClass(data[model[i]],tp))
                return output
        else:
            # data = jso
            data = dict2obj(data)
        return data

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
                    route,inputModel,customResponse = route.get('action'),route.get('input',None),route.get('customResponse',None)
                if(callable(route)):
                    if inputModel is None:
                        params = route.__code__.co_varnames
                        types = route.__annotations__
                        argsCount = route.__code__.co_argcount
                        response = ResponseHandler(route,'controllerFunction',self.FormatRequestData(params,types,argsCount),customResponse,unpack=True).respond()
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

        self.send_custom_response(response.content,response.responseCode,response.mimeType)
        

    def send_custom_response(self,content:bytes,responseCode=200,mimeType='text/html'):
        self.log_request(responseCode)
        self.send_response_only(responseCode)
        self.send_header('date',self.date_time_string())
        self.send_header('content-type', mimeType)
        self.send_header('server',server_info.server_name + ' '+ server_info.server_version)
        self.end_headers()
        if(type(content) is not bytes):
            if(type(content) is not str):
                content = bytes(str(content), 'utf-8')
            else:
                content = bytes(content, 'utf-8')
        self.wfile.write(content)

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
                    self.send_custom_response(config.fool_nmap_content,200,'application/json')
                else:
                    self.send_error(
                        HTTPStatus.NOT_IMPLEMENTED,
                        "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            method()
            self.wfile.flush() #actually send the response if not already done.
        except timeout as e:
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

#making seperate class and not using one in http libary to support backward compatiblity with python versions
class ThreadedPyOPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def run():
    print("Starting server ...")
    server_address = (config.host, config.port)
    # httpd = HTTPServer(server_address, PyOPSever)
    httpd = ThreadedPyOPServer(server_address, PyOPSever)
    print("running server at ", server_address)
    print("WD :- ", dir_path + config.static)
    if config.enableTLS:
        from ssl import wrap_socket
        httpd.socket = wrap_socket (httpd.socket, 
            keyfile= config.PATH_TLS_KEY_FILE, 
            certfile= config.PATH_TLS_CERT_FILE, server_side=True)
        print("Listening Securely")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
