# import os
# import sys
# c = sys.path
# b = os.getcwd()
# print(c)
# print(b)
# import mvc.models.inputModels as md
from server.helper import getRequestData
data = getRequestData()
def main():
    print( 
    """
        <html>
            <head>
                <title>
                    PyOP
                </title>
            </head>

            <body>
                <h1>Hello There</h1>
                <h3>{}</h3>
                <h4>Age : {}</h4>
            </body>
        </html>
    """.format(data.name,data.age)
    )

main()