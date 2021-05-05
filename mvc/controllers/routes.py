"""
================================================================================================
Specify routes in this file to handle API calls.
**NOTE: if views.py in views folder has a same route then that will be given preference **
give python file or python functions for their corresponding routes.
python files must defin main(req) method
every function or python file should accept atleast one parameter(req object)
results obatined from these files will be serialized and retured as application/json
*************************************************************************************************
remove this placeholder routes and make your own
=================================================================================================
"""
import mvc.models.inputModels as md
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
    data = req.data
    a,b = data.a,data.b
    return a+b

def sumNum1(a:int,b:int):
    return a+b

def sumCustom(req):
    data = req.data
    res = data.a + data.b + data.c + data.d
    res = "<h1>{}<h1>".format(res)
    return {
        'content' : res,
        'mimeType' : 'text/html',
        'code': 200,
    }

def typeCastedProduct(a:int,b:int,c:str,d:[int]):
    return(c + " :-> " + str((a*b)/sum(d)))

postRoutes = {
    '/sum': {'action':sumNum,'input':md.sumInputModel},
    '/sumCustom': {'action':sumCustom,'input':md.sumInputModel,'customResponse': True},
    '/product': typeCastedProduct,
    '/greet': {'action':'services/greet.py','input':md.UserDetials,'customResponse':{'mimeType':'text/html'}},

}
getRoutes = {
    '/sum': sumNum1,
    '/sumCustom': {'action':sumCustom,'input':md.sumInputModel,'customResponse': True},
    '/product': typeCastedProduct,
    '/greet': 'services/greet.py',

}


#print(services.greet.main(req))
