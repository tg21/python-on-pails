import sys
import os

#function to read data sent by server using get or post method
def pyGet(key):
    data  = sys.argv[1].replace('"',"")#trying to tackle sql injection
    if data == "":
        return False
    else:
        pairs = data.split("&")
        for i in range(len(pairs)):
            if key == pairs[i].split("=")[0]:
                return pairs[i].split("=")[1]
        return False

def pyAll(key):
    return sys.argv[1]
            
        
def pyClient(key):
    return False
