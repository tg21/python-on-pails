class server_info:
    server_name = "python-on-pails"
    server_version = "2.0"
class project_info:
    name = 'Sample_Name'
    version= 1.0

class scripts:
    run = 'python3 main.py'

class config:
    entry = 'main.py'
    host = '0.0.0.0'
    port = 80 #http port
    enctyption=False # set true for to enable TLS
    sPort=443 #secure/https port
    wildcard_response='on'

    models='mvc/models/'
    controllers='mvc/controllers/'
    views='mvc/views/'
    static='mvc/views/static/'
    logging=False

    enableTLS = False
    PATH_TLS_KEY_FILE = None #give path to key file here (string)
    PATH_TLS_CERT_FILE = None #give path to CERT file here (string)




