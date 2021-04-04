def main(req):
    return( 
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
            </body>
        </html>
    """.format(req.data.name)
    )