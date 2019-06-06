# Python-On-Pails(PyOP)
![](https://tg21.github.io/assets/img/pyop/PyOP_small.png)
## You all have seen Ruby on Rails now get ready for python on pails.
#### So what is Python on Pails?
Q: Is it something like Ruby on Rails ,but in python?\
Answer :No Idea(Maybe). Never used Rails. All I can say is this program is a "framework wannabe".

##### [Visit Official Website for more Information](https://tg21.github.io)
- Python-On-Pails(PyOP) is just a simple "kind of a framework" programmed in python. It is cool and it also  eliminates the need to install apache2, xampp ,wamp or lamp on systems that already have python(Python3 to be precise) installed.
- PyOP can use python3 as the main server side language, so you won't have to rely on PHP.(Not that I think anything is wrong with you using PHP but other programmers might make jokes on you.
- PyOP can serve almost all(more than 500) mimeTypes as it should, and on plus point It can run PHP too if you want(not encouraged).

# New Features!

  - Every feature is "new" feature as this is recently baked code.
  - Express links feature is now live.(add your links in /config/express.json)
  - PyOP has wildcard response enabled by default.(but hackers can exploit other vulnerabilities and this project has many).

## Changelog
- fixed a bug where python files were not being served on unix based systems.
- Added a feature to serve files from anywhere.
- added some new bugs to hunt later.

### Installation
PyOP requires [python3](https://www.python.org/) to run.

add your project files in www folder.\
run server.py to start the server.\
all files presnent in www folder will be served to client.\


```sh
$ cd python-on-pails
$ sudo python3 server.py
```

For production environments...

```sh
do the same as above but at your own risk.
```

## Also, a new feature
instead of using only one folder to serve files.\
run surver.py from whichever folder you want, and that server's file will be served.
```sh
$ cd folder/with/your/project/files
$ sudo python3 ~/path_to_pyop_directory/server.py -g
```

## Additional Instructions
PyOP can run PHP too but If you wish to use that , then you you'll need to install it yourself and make sure that you can access those files from terminal.\
e.g.-In windows you add path of directories(containing the executable) to environment variables.

 \
 If you want to access GET/POST data sent by server in you python file then you'll need to import pyGet() from /helperfiles/receiver.py. and then simply call the function with variable name as argument.





### Development

Want to contribute? Great!

I'd like that but I don't know how you can(new to GitHub and all this VCS thing)\
If you know how and want to contribute [contact]("https://tg21.githib.io/contact.html") me.\
Help is always welcome.

### TODOs

 - Add easy express links feature(Now added)
 - Add a GUI for to start and manage server
 - package for pypi
 - Easy TLS encryption
 - Make things like cookies and $_SERVER kind of thing available
 - find and better name and logo for this project.

License
----

It has none.(what is this deal with all license stuff and how do I get one?)


**Free Software, yeah enjoy!**
