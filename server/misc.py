# from inspect import getmembers

# creates dictionary from query string a=1&b=2&c=sample 
def jsonify(data:str) -> dict:
    output = {}
    data = data.strip().split('&')
    for kv in data:
        kv = kv.strip().split('=')
        if(len(kv) == 2):
            output[kv[0]] = kv[1]
    return output

class C:
    pass

def dict2obj(d):
      
    # checking whether object d is a
    # instance of class list
    if isinstance(d, list):
           d = [dict2obj(x) for x in d] 
  
    # if d is not a instance of dict then
    # directly object is returned
    if not isinstance(d, dict):
           return d
    # constructor of the class passed to obj
    obj = C()
   
    for k in d:
        obj.__dict__[k] = dict2obj(d[k])
   
    return obj


def isSequence(ob):
    a = type(ob)
    if(type(ob) is list or type(ob) is tuple or type(ob) is set or type(ob) is frozenset):
        return True
    return False


## to get types and names of parameters NOTE: won't work without types
# a.__annotations__
# > {'b': <class 'int'>, 'c': <class 'int'>}

# just names of parameters
# a.__code__.co_varnames

def parseJsonToClass(input,model):
    output = None
    try:
        if(model is None or input is None):
            output = input
        elif isSequence(model) and isSequence(input):
            output = []
            for i in range(len(input)):
                # if(i > len(input) - 1):
                #     obj = None
                # else:
                obj = parseJsonToClass(input[i],model[0])
                output.append(obj)
        elif type(model) is type and type(input) is dict:
            output = mapDictToClass(input,model)
        elif callable(model) and type(input) is not dict and not isSequence(input):
            output =  model(input)
        else:
            output = None
    except Exception:
        #TODO:better Exceptions
        output = None
    return output
    
def mapDictToClass(dic,cls):
    try:
        obj = cls()
        if(type(obj) is dict):
            return dic
        for prop,value in getattr(cls,'__dict__').items():
            if(not prop.startswith('_') and not callable(prop)):
                obj.__dict__[prop] = parseJsonToClass(dic.get(prop,None),value)
        return obj
    except Exception as ex:
        print(str(ex))
        #TODO:better Exceptions
        return None




# objectFortype = {
#     'str' : str,
#     'int' : int,
#     'float' : float,
#     'complex' : complex,
#     'list' : list,
#     'tuple' : list,
#     'dict' : dict,
#     'set' : set,
#     'frozenset' : frozenset,
#     'bool' : bool,
#     # 'bytes' : bytes,
#     # 'bytearry' : bytearray,
#     # 'memoryview' : memoryview,
# }