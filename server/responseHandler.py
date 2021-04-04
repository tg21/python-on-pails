from server.settings import config
class ResponseHandler:

    def _serveStatic(self,request):
        return _read_text(request)

    def _serverStaticPythonFunction(self,request):
        pass
    
    def _serverStaticPythonFile(self,request):
        pass
    
    def _executeAndServeFunction(self,request,input):
        pass

    def _executeAndServeFunction(self,request,input):
        pass

    def respond(self):
        try:
            if(self.requestType == 'static'):
                self.response = _ResoponseClass(self._serveStatic(self.request),200,'text/html')
        except Exception as e:
            if config.logging:
                print(e)
            self.response = _ResoponseClass(str(e),500,'text/html')
        return self.response

    def __init__(self,request,requestType,input):
        self.request = request
        self.requestType = requestType
        self.input = input
       

def _read_text(file):
    with open(file,"rb") as nfile:
        return nfile.read()
    
class _ResoponseClass:
    def __init__(self,response,responseCode,mimeType):
        self.content = response
        self.responseCode = responseCode
        self.mimeType = mimeType