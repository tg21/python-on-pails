"""
=======================================================================
Specify view routes in this file.
give path to html file, python file or python functions.
no parameters will be passed to python files or functions.(use routes.py in controllers folder if you need to do so)
results obatined from these files witll be retured as text/html
************************************************************************
remove this placeholder routes and make your own
=======================================================================
"""
def properResponseForHelloThere():
    return "General Kenobi !"
views = {
    '/helloThere': properResponseForHelloThere,
    '/hello': 'html/welcome.html',
    '/': 'html/welcome.html',#this url is relative
}



