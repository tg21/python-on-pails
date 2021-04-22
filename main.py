import sys
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer # ,HTTPServer,
import json
dir_path = (str(os.path.dirname(os.path.realpath(__file__))) + "/")
# sys.path.insert(0, '{}/server'.format(dir_path))
from server.settings import config
from server.responseHandler import ResponseHandler
from server.misc import jsonify,dict2obj,parseJsonToClass,Req
# sys.path.insert(0, '{}/{}'.format(dir_path,config.views))
# sys.path.insert(0, '{}/{}'.format(dir_path,config.controllers))

from mvc.views.views import views
from mvc.controllers.routes import getRoutes,postRoutes
import ssl


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
        # data = dict2obj({
        #     'method':rtype,
        #     'data':data,
        # })
        return Req(self.command,data)

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
                        response = ResponseHandler(route,'controllerFunction',self.FormatRequestData(params,types),customResponse,unpack=True).respond()
                    else:
                        response = ResponseHandler(route,'controllerFunction',self.FormatRequestData(inputModel),customResponse,unpack=False).respond()
                elif(type(route) == str and route.endswith('.py')):
                    response = ResponseHandler(route,'controllerFile',self.FormatRequestData(inputModel),customResponse).respond()
                else:
                    #TODO:better exception here
                    raise Exception
            else:
                request = dir_path+config.static+queryString[0]
                response = ResponseHandler(request,'static',None).respond()

        self.send_response(response.responseCode)
        self.send_header('content-type', response.mimeType)
        self.end_headers()
        if(type(response.content) is not bytes):
            if(type(response.content) is not str):
                response.content = bytes(str(response.content), 'utf-8')
            else:
                response.content = bytes(response.content, 'utf-8')
        self.wfile.write(response.content)

    # GET
    def do_GET(self):
        self.GETPOST()
        return

    def do_POST(self):
        self.GETPOST()
        return


def run():
    print("Starting server ...")
    server_address = (config.host, config.port)
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
