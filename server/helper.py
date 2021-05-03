import sys
import pickle

def getRequestData():
    if(len(sys.argv) > 1):
        return pickle.loads(eval(sys.argv[1]))
    else:
        return None