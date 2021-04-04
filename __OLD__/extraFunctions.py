#### Following are functions that provide some initial Variables to server.py , they are kept here so server.py would look less ugly

import json
import os
dir_path = os.path.dirname(os.path.realpath(__file__))

def initials():
    #loading express urls
    with open(dir_path+"/config/express.json","r") as read_file:
        express_dict = json.load(read_file)
    #Loading mimetypes
    with open(dir_path+"/config/mimeType.json","r") as read_file:
        mimeTypes_dict = json.load(read_file)
    #loading initial settings
    with open(dir_path+"/config/settings.json","r") as read_file:
        settings_dict = json.load(read_file)
    host = settings_dict.get("host")
    port = settings_dict.get("port")
    wildcard = settings_dict.get("wildcard_response")
    project_dir = settings_dict.get("project_dir") 
    encryption = settings_dict.get("encryption")
    logging = settings_dict.get("logging")
    return dir_path,express_dict,mimeTypes_dict,host,port,wildcard,project_dir,encryption,logging