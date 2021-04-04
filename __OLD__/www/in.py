from receiver import pyGet, pyClient, pyAll
print("hello there<br>")
print(pyGet("batsy"),"<br>")
print(pyGet("self"),"<br>")
print(pyAll(),"<br>")
#print("<br>client",pyClient())

obj = pyClient()
print("objstr is : ",str(obj))
print("<br>client is ",obj.client_address)
