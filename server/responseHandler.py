from server.settings import config
from html.parser import HTMLParser
from server.mimeTypes import mimeTypes
class ResponseHandler:

    def __init__(self,request,requestType,reqData,customResponse=None):
        self.request = request
        self.requestType = requestType
        self.reqData = reqData
        self.customResponse = customResponse

    #for views
    def _serveStatic(self,request):
        return _read_text(request)

    def _serverStaticPythonFunction(self,request):
        return request()
    
    def _serverStaticPythonFile(self,request):
        return _run_python_file(request)
    
    def _serverStaticPyHtml(self,request):
        return _processPyHtml(request)

    #for controllers
    def _executeAndServeFunction(self,request,reqData):
        return request(reqData)

    def _executeAndServeFile(self,request,reqData):
        pass

    def respond(self):
        try:
            if(self.requestType == 'static'):
                if(self.request.endswith('.html')):
                    self.response = _ResoponseClass(self._serveStatic(self.request),200,'text/html')
                elif(self.request.endswith('.py')):
                    self.response = _ResoponseClass(self._serverStaticPythonFile(self.request),200,'text/html')
                elif(self.request.endswith('.pyhtml')):
                    self.response = _ResoponseClass(self._serverStaticPyHtml(self.request),200,'text/html')
                else:
                    self.response = _ResoponseClass(self._serveStatic(self.request),200,mimeTypes.get('.'+self.request.split('.')[-1],'application/octet-stream'))            
            elif(self.requestType == 'staticFunction'):
                self.response = _ResoponseClass(self._serverStaticPythonFunction(self.request),200,'text/html')
            elif(self.requestType == 'controllerFunction'):
                if(self.customResponse == None):
                    self.response = _ResoponseClass(self._executeAndServeFunction(self.request,self.reqData),200,'application/json')
                else:
                    res = self._executeAndServeFunction(self.request,self.reqData)
                    self.response = _ResoponseClass(res.get('content'),res.get('code',200),res.get('mimeType','application/json'))
            elif(self.requestType == 'controllerFile'):
                self.response = _ResoponseClass(self._executeAndServeFile(self.request),200,'application/json')
            else:
                raise BaseException
        except Exception as e:
            if config.logging:
                print(e)
            self.response = _ResoponseClass(type(e).__name__,500,'text/html')
        return self.response
       

def _read_text(file):
    with open(file,"rb") as nfile:
        return nfile.read()

def _run_python_file(file):
    ## not using read-text function here because not reading as binary here.
    readFile:str
    with open(file,"r") as f:
        readFile = f.read()
    exec(readFile,globals())
    return main()

def _processPyHtml(file):
    ## not using read-text function here because not reading as binary here.
    readFile:str
    with open(file,"r") as f:
        readFile = f.read()
    parser = MyHTMLParser(readFile)
    parser.feed(readFile)
    return parser.processed_file

### class to process inline python
class MyHTMLParser(HTMLParser):
    def __init__(self,file):
        HTMLParser.__init__(self)
        self.recording = 0
        self.processed_file = file
        # self.sdata = []
    def handle_starttag(self, tag, attrs):
        if tag=="py":
            self.recording += 1
    
    def handle_endtag(self, tag):
        if tag=="py":
            self.recording -= 1

    def handle_data(self,data):
        if self.recording == 1:
            place = data
            data = data.split("\n")
            data = list(filter(lambda x:x.strip()!="",data))
            min_tabs = 999
            for i in range(0,len(data)):
                tabs = len(data[i]) - len(data[i].lstrip(' '))
                if(tabs<min_tabs):
                    min_tabs = tabs
            # temp = open("temp.py","w")
            lcla = {}
            toExec = "def execFun():\n"
            for i in range(0,len(data)):
                toExec += "\t"+data[i].rstrip(' ')[min_tabs:]+"\n"
            exec(toExec,globals())
            a = [globals(),locals()]
            res = execFun()
            self.processed_file = self.processed_file.replace(place,res.rstrip())
    
class _ResoponseClass:
    def __init__(self,response,responseCode,mimeType):
        self.content = response
        self.responseCode = responseCode
        self.mimeType = mimeType


