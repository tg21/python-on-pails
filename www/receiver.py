import sys
import os
import ctypes
import gc

#function to read data sent by server using get or post method
def pyGet(key):
    data  = sys.argv[1].replace('"',"")#trying to tackle s
    if data == "":
        return False
    else:
        pairs = data.split("&")
        for i in range(len(pairs)):
            if key == pairs[i].split("=")[0]:
                return pairs[i].split("=")[1]
        return False
            
        
def pyClient():
    # try:
    #     z = ctypes.cast(int(pyGet("self"),0),ctypes.py_object).value
    #     return z
    # except:
    #     return "error occured"
    for obj in gc.get_objects():
        if id(obj) == int(pyGet("self")):
            return obj
    raise Exception("No found")

def pyAll():
    return sys.argv[1]