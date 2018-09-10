import sys


#function to read data sent by server
def pyGet(key):
    data  = sys.argv[1].replace('"',"")
    if data == "":
        print("no data sent")
        return "no data"+data
    else:
        pairs = data.split("&")
        for i in range(len(pairs)):
            if key == pairs[i].split("=")[0]:
                return pairs[i].split("=")[1]
        return "no value found"
            
        
