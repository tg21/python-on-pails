class server_info:
    server_name = "python-on-pails or maybe ruby even nmap can't tell"
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

    #some options for security
    wildcard_response = True #will give 200 even from missing files
    fool_nmap = True #will send 200 and random response for arbitrary http methods , which will hopefully fool nmap
    fool_nmap_content = "Unsupported method But handled like a Pro" #change it and tell me if it has any effect

    models='mvc/models/'
    controllers='mvc/controllers/'
    views='mvc/views/'
    static='mvc/views/static/'
    logging=False

    enableTLS = False
    PATH_TLS_KEY_FILE = None #give path to key file here (string)
    PATH_TLS_CERT_FILE = None #give path to CERT file here (string)




