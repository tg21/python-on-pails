class ResoponseClass:
    def __init__(self,response,responseCode,mimeType):
        self.content = response
        self.responseCode = responseCode
        self.mimeType = mimeType

class Req:
    def __init__(self,method,data):
        self.method = method
        self.data = data