from server.settings import config
from html.parser import HTMLParser
from server.mimeTypes import mimeTypes
import subprocess
from os import name as py,getcwd,environ
import pickle
from server.internalModels import ResoponseClass
if(py=="posix"):
    py = "python3"
else:
    py = "python"
class ResponseHandler:

    def __init__(self,request,requestType,reqData,customResponse=None,unpack=None):
        self.request = request
        self.requestType = requestType
        self.reqData = reqData
        self.customResponse = customResponse
        self.unpack = unpack

    #for views
    def _serveStatic(self,request):
        return _read_bin(request)

    def _serverStaticPythonFunction(self,request):
        return request()
    
    def _serverStaticPythonFile(self,request):
        return _run_python_file(request)
    
    def _serverStaticPyHtml(self,request):
        return _processPyHtml(request)

    #for controllers
    def _executeAndServeFunction(self,request,reqData,unpack):
        if unpack:
            return request(*reqData)
        else:
            return request(reqData)

    def _executeAndServeFile(self,request,reqData):
        return subprocessPyFile(request,reqData)

    def respond(self):
        try:
            if(self.requestType == 'static'):
                if(self.request.endswith('.html')):
                    self.response = ResoponseClass(self._serveStatic(self.request),200,'text/html')
                elif(self.request.endswith('.py')):
                    self.response = ResoponseClass(self._serverStaticPythonFile(self.request),200,'text/html')
                elif(self.request.endswith('.pyhtml')):
                    self.response = ResoponseClass(self._serverStaticPyHtml(self.request),200,'text/html')
                else:
                    self.response = ResoponseClass(self._serveStatic(self.request),200,mimeTypes.get('.'+self.request.split('.')[-1],'application/octet-stream'))            
            elif(self.requestType == 'staticFunction'):
                self.response = ResoponseClass(self._serverStaticPythonFunction(self.request),200,'text/html')
            elif(self.requestType == 'controllerFunction'):
                res = self._executeAndServeFunction(self.request,self.reqData,self.unpack)
                self.handleCustomResponse(res)
            elif(self.requestType == 'controllerFile'):
                res = self._executeAndServeFile(self.request,self.reqData)
                self.handleCustomResponse(res)
            else:
                raise BaseException
        except Exception as e:
            if config.logging:
                print(e)
            self.response = ResoponseClass(type(e).__name__,500,'text/html')
        return self.response
       
    def handleCustomResponse(self,res):
        if(self.customResponse == None):
            self.response = ResoponseClass(res,200,'application/json')
        elif(self.customResponse == True):
            self.response = ResoponseClass(res.get('content'),res.get('code',200),res.get('mimeType','application/json'))
        elif(type(self.customResponse) is dict):
            self.response = ResoponseClass(res,self.customResponse.get('code',200),self.customResponse.get('mimeType','application/json'))
        else:
            # TODO:Raise Custome Reponse Exception
            raise Exception

def subprocessPyFile(request,reqData):
    # return sp.check_output([py, request,reqData])
    reqData = pickle.dumps(reqData,protocol=pickle.HIGHEST_PROTOCOL)
    # to access this reqData in file do "from server.helper import reqData"
    # res =  subprocess.run(['python',request,str(reqData)])#stderr=subprocess.STDOUT,capture_output=True
    try:
        en = {
            **environ,
            "PYTHONPATH":getcwd()
        }
        # "export PYTHONPATH=$PYTHONPATH:{} && ".format(getcwd())+py,
        res = subprocess.run([py,request,str(reqData)],capture_output=True,env=en)
    except Exception as e:
        print(e)
        raise(e)
    return res.stdout

def _read_bin(file):
    with open(file,"rb") as nfile:
        return nfile.read()

def _run_python_file(file):
    ## not using read-text function here because not reading as binary here.
    readFile:str
    with open(file,"r") as f:
        readFile = f.read()
    lcl = {'main':None}
    exec(readFile,{},lcl)
    return lcl['main']()

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
            lcl = {'execFun':None}
            toExec = "def execFun():\n"
            for i in range(0,len(data)):
                toExec += "\t"+data[i].rstrip(' ')[min_tabs:]+"\n"
            exec(toExec,{},lcl)
            #a = [globals(),locals()]
            res = lcl['execFun']()
            self.processed_file = self.processed_file.replace(place,res.rstrip())
    



