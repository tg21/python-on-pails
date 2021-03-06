# this is helper file for server.py

from pathlib import Path
import os
import subprocess
from html.parser import HTMLParser

### global variables
processed_file = ""


### class to process inline python
class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.recording = 0 
        self.sdata = []
    def handle_starttag(self, tag, attrs):
        if tag=="py":
            self.recording =1
    
    def handle_endtag(self, tag):
        if tag=="py":
            self.recording = 0

    def handle_data(self,data):
        if self.recording:
            place = data
            data = data.split("\n")
            data = list(filter(lambda x:x.strip()!="",data))
            min_tabs = 999
            for i in range(0,len(data)):
                tabs = len(data[i]) - len(data[i].lstrip(' '))
                if(tabs<min_tabs):
                    min_tabs = tabs
            temp = open("temp.py","w")
            for i in range(0,len(data)):
                data[i] = data[i].rstrip(' ')[min_tabs:]
                temp.write(data[i]+"\n")
            temp.close()
            proc = subprocess.Popen(py+" temp.py",stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True)
            res = (str(proc.communicate()[0],"utf-8"))
            global processed_file 
            processed_file = processed_file.replace(place,res.rstrip())


### most important function
def testfun():
    print("hello there")


dir_path = os.path.dirname(os.path.realpath(__file__))

# two different command for windows and linux respectively
py = "python "
if(os.name=="posix"):
    py = "python3 "


#function to run python files
def runPy(file,data):
    print("Entered runpy")
    data = data.replace("'","\'")
    data = data.replace('"','\"')
    proc = subprocess.Popen(py+ file+' "'+data+'"', stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True)

    return str(proc.communicate()[0],"utf-8")

### function to handle html files with inline python
def runHTML(file):
    global processed_file
    ## not using read-text function here because not reading as binary here.
    with open(file,"r") as f:
        processed_file = f.read()
    parser = MyHTMLParser()
    parser.feed(processed_file)
    return processed_file


#function to run php files
def runPHP(file,data):
    data = data.replace("'","\'")
    data = data.replace('"','\"')    
    proc = subprocess.Popen(['php', file,'"'+data+'"'], stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True)
    return str(proc.communicate()[0],"utf-8")

#redirecting pages
# def redirect(url):
#     self.send_response(302)
    
    



#function to read simple text files

def read_text(file):
    with open(file,"rb") as nfile:
        return nfile.read()
    
    
#function to list directories files as a table
def showDir(dirPath):
    files = os.listdir(dirPath)
    if "index.py" in files:
        content = runPy(dirPath+"/index.py","")
    elif "index.php" in files:
        content = runPHP(dirPath+"/index.php","")
    elif "index.html" in files:
        content = read_text(dirPath+"/index.html")
        
     #listing directory content   
    else:
        fileLinks = "<ul>"
        if dirPath.endswith("/"):
            for i in range(len(files)):         
                if Path(dirPath+files[i]).is_file():
                    fileLinks += "<li><a href = "+files[i]+">"+files[i]+"</a></li>"
                else:
                    fileLinks += "<li><a href = "+files[i]+"/>"+files[i]+"</a></li>"
        else:
            for i in range(len(files)):         
                if Path(dirPath+"/"+files[i]).is_file():
                    fileLinks += "<li><a href = /"+files[i]+">"+files[i]+"</a></li>"
                else:
                    fileLinks += "<li><a href = /"+files[i]+"/>"+files[i]+"</a></li>"            
        content = "<html><head><title>PyOP</title></head><body>"+fileLinks+"</ul></body></html>"
        
    return content
    
    
#function to handle requests

def response(requested_file,data,mimeTypes):
    mimeType = "text/html"
    errorCode = 200
    if Path(requested_file).is_file():
        extension = os.path.splitext(requested_file)[1]
        try:
            if extension ==".py":
                content = runPy(requested_file,data)
                print("exit runpy ",content)
                mimeType = "text/html"
            elif extension == ".php":
                content = runPHP(requested_file,data)
                mimeType = "text/html"
            elif extension == ".html":
                content = runHTML(requested_file)
                mimeType = "text/html"
            else:
                content = read_text(requested_file)
                mimeType = mimeTypes.get(extension)
                
        except Exception as e:
            mimeType = "text/html"
            print("error ::-- ",e )
            content = str(e)
            errorCode = 500

    elif Path(requested_file).is_dir():
        content = showDir(requested_file)
        mimeType = "text/html"
        errorCode = 200

    else:
        errorCode  = 200 #wildcard response
        content = read_text(dir_path+"/default/404.html")
        mimeType = "text/html"
        
    return content,mimeType,errorCode


