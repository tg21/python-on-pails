"""
===================================================================================================================================
Specify routes in this file to handle API calls.
**NOTE: if views.py in views folder has a same route then that will be given preference **
give python file or python functions for their corresponding routes.
python files must defin main(req) method
every function or python file should accept atleast one parameter(req object)
results obatined from these files will be serialized and retured as application/json unless customResponse in toggled for a route
***********************************************************************************************************************************
remove this placeholder routes and make your own
===================================================================================================================================
"""
import mvc.models.inputModels as md
from server.internalModels import PyopReq
# how files are executed
# x = """
# def main(n):
# 	return "hello {}".format(n)
# """

# exec(x)
# print(main("batman"))
# class dat:
#     name = 'batman'
# class req:
#     data = dat
# from services.greet import main

def sumNum(req):
    # data = req.data
    a, b = req.a, req.b
    return a+b

def sumNum1(a: int, b: int):
    return a+b

def sumCustom(req:md.productInputModel):
    #data = req.data
    res = req.a + req.b + req.c + sum(req.d)
    res = "<h1>{}<h1>".format(res)
    return {
        'content' : res,
        'mimeType' : 'text/html',
        'code': 200,
    }

def typeCastedProduct(a:int,b:int,c:str,d:[int]):
    return(c + " :-> " + str((a*b)/sum(d)))

def typeCastedProductFullControll(a:int,b:int,c:str,d:[int],req:PyopReq):
    client = str(req.client_address) # getting url
    content = "responding to request: "+ client + " \n " + c + " :-> " + str((a*b)/sum(d))
    # req.send_custom_response(content) # using default code(200) and mimeType(text/html)
    # req.send_custom_response(content,200) # using default mimeType
    req.send_custom_response(content,200,'text/html') #sepecifying all parameters

    req.close_connection = True
    

postRoutes = {
    '/sum': {'action':sumNum,'input':md.sumInputModel},
    '/sumCustom': {'action':sumCustom,'customResponse': True},
    '/product': typeCastedProductFullControll,
    '/greet': {'action':'services/greet.py','input':md.UserDetails,'customResponse':{'mimeType':'text/html'}},

}
getRoutes = {
    '/sum': sumNum1,
    '/sumCustom': {'action':sumCustom,'input':md.sumInputModel,'customResponse': True},
    '/product': typeCastedProduct,
    '/greet': 'services/greet.py',

}


#print(services.greet.main(req))
