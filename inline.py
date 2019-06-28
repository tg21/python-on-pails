file = ""
with open("www/alpha.html","r") as f:
    file = f.read()

print(file)
from html.parser import HTMLParser
import os
import subprocess
py = "python "
if(os.name=="posix"):
    py = "python3 "

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
            print("Encountered some data  :", data)
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
            print(res)
            global file 
            file = file.replace(place,res.rstrip())


parser = MyHTMLParser()
parser.feed(file)
print(file)