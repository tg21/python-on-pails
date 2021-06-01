from http.server import BaseHTTPRequestHandler
class ResoponseClass:
    def __init__(self,response,responseCode,mimeType):
        self.content = response
        self.responseCode = responseCode
        self.mimeType = mimeType

class Req:
    def __init__(self,method,data):
        self.method = method
        self.data = data

class PyopReq(BaseHTTPRequestHandler):
    """Abstract class for usage as argument type in routes"""

    def FormatRequestData(self,model,types=None,argsCount=0):
        pass

    def ParseRequestDataInToObject(self,data,model,types=None,argsCount=0):
        pass

    def GETPOST(self):
        pass

    def send_custom_response(self,response:ResoponseClass):
        pass

    def handle_one_request(self):
        """Handle a single HTTP request.
        Overridden from base class
        """
        pass

    # GET
    def do_GET(self):
        pass

    def do_POST(self):
        pass