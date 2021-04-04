"""
================================================================================================
Specify routes in this file to handle API calls.
**NOTE: if views.py in views folder has a same route then that will be given preference **
give python file or python functions for their corresponding routes.
python files must defin main(req) method
every function or python file should accept atleast one parameter(req object)
results obatined from these files witll be retured as text/html
*************************************************************************************************
remove this placeholder routes and make your own
=================================================================================================
"""

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
routes = {
    '/sum': sum,
    '/greet': sum,
}

# def sum(req):
#     a,b = req.data['a'],req.data['b']
#     return a+b
#print(services.greet.main(req))
