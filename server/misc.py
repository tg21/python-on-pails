# creates dictionary from query string a=1&b=2&c=sample 
def jsonify(data:str) -> dict:
    output = {}
    data = data.strip().split('&')
    for kv in data:
        kv = kv.strip().split('=')
        output[kv[0]] = kv[1]
    return output

def dict2obj(d):
      
    # checking whether object d is a
    # instance of class list
    if isinstance(d, list):
           d = [dict2obj(x) for x in d] 
  
    # if d is not a instance of dict then
    # directly object is returned
    if not isinstance(d, dict):
           return d
   
    # declaring a class
    class C:
        pass
   
    # constructor of the class passed to obj
    obj = C()
   
    for k in d:
        obj.__dict__[k] = dict2obj(d[k])
   
    return obj
