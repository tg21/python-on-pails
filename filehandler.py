# this is helper file for server.py

from pathlib import Path
import os
import subprocess

#function to run python files
def runPy(file):
    proc = subprocess.Popen(['python', file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return str(proc.communicate()[0],"utf-8")

#function to run php files

def runPHP(file):
    proc = subprocess.Popen(['php', file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return str(proc.communicate()[0],"utf-8")




#function to read simple text files

def read_text(file):
    with open(file,"r") as nfile:
        return nfile.read()
    
#function to read multimedia files

def read_media(file):
    with open(file,"rb") as nfile:
        return nfile.read()
    
    
#function to list directories files as a table
def showDir(dirPath):
    files = os.listdir(dirPath)
    if "index.py" in files:
        content = runPy(dirPath+"/index.py")
    elif "index.php" in files:
        content = runPHP(dirPath+"/index.php")
    elif "index.html" in files:
        content = read_text(dirPath+"/index.html")
        
     #listing directory content   
    else:
        mimType = "text/html"
        fileLinks = "<ul>"
        for i in range(len(files)):         
            if Path(dirPath+files[i]).is_file():
                fileLinks += "<li><a href = "+files[i]+">"+files[i]+"</a></li>"
            else:
                fileLinks += "<li><a href = "+files[i]+"/>"+files[i]+"</a></li>"
        content = "<html><head><title>PyOP</title></head><body>"+fileLinks+"</ul></body></html>"
        
    return content
    
    
#function to handle requests

def response(requested_file):
    mimeType = "text/html"
    isMedia = False #if file is media then we do not encode it
    errorCode = 200
    if Path(requested_file).is_file():
        try:
            if requested_file.endswith('.css'):
                content = read_text(requested_file)
                mimeType = "text/css"
            elif requested_file.endswith('.jpg'):
                content = read_media(requested_file)
                mimeType = "image/jpeg"
                isMedia = True
            elif requested_file.endswith('.jpeg'):
                content = read_media(requested_file)
                mimeType = "image/jpeg"
                isMedia = True            
            elif requested_file.endswith(".js"):
                content = read_text(requested_file)
                mimeType = "application/javascript"
            elif requested_file.endswith("py"):
                content = runPy(requested_file)
                mimeType = "text/html"
            elif requested_file.endswith(".php"):
                content = runPHP(requested_file)
                mimeType = "text/html"
            else:
                content = read_text(requested_file)
                mimeType = "text/html"

        except Exception as e:
            mimeType = "text/html"
            print("error ::-- ",e )
            content = str(e)
            errorCode = 300

    elif Path(requested_file).is_dir():
        content = showDir(requested_file)
        mimeType = "text/html"
        errorCode = 200

    else:
        errorCode  = 200 #wildcard response
        content = read_text("./default/404.html")
        mimeType = "text/html"
        
    return content,mimeType,errorCode,isMedia