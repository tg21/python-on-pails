import os
import signal
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
dir_path = (str(os.path.dirname(os.path.realpath(__file__))) + "/")
from server.settings import config,server_info
from server.misc import jsonify,dict2obj,parseJsonToClass
from server.internalModels import Req,ResponseClass,PyopReq
from server.http import Headers, Request as PyopRequest, split_path_query

from mvc.views.views import views
from mvc.controllers.routes import getRoutes,postRoutes
from http import HTTPStatus
from socket import timeout
from socketserver import ThreadingMixIn


def e(x):
    a = 3


# Shared dispatch instance: same layer used by WSGI/ASGI adapters.
# Imported lazily so route edits are picked up on reload.
_application = None

def get_application():
    global _application
    if _application is None:
        from server.application import PyopApplication
        _application = PyopApplication()
    return _application


class PyOPSever(BaseHTTPRequestHandler):
    server_version = server_info.server_name + ' ' + server_info.server_version
    protocol_version = 'HTTP/1.1'

    def FormatRequestData(self,model,types=None,argsCount=0):
        queryString = self.path.split("?")
        if(self.command == "GET"):
            if len(queryString) > 1:
                data = str(queryString[1])
            else:
                data = ""
        else:
            length = int(self.headers.get('Content-Length', 0) or 0)
            data = str(self.rfile.read(length), 'utf-8') if length else ""

        data = self.ParseRequestDataInToObject(data,model,types,argsCount)
        return data


    def ParseRequestDataInToObject(self,data,model,types=None,argsCount=0):
        if(type(data) == str and data!=""):
            try:
                data = json.loads(data)
            except Exception as e:
                print(e)
                data = jsonify(data)
        elif(type(data) is not dict):
            #TODO: Better Exception for unsupported format data
            raise Exception
        if model is not None:
            if types is None:
                # making object based on inputmodel key in route's dictionary
                data = parseJsonToClass(data,model)
            else:
                # making object based on parameters of controller function
                output = []
                if(argsCount == 1): # mapping one dict to one class object (most common case of POST APIs)
                    tp = types.get(model[0],None)
                    output.append(parseJsonToClass(data,tp))
                else:
                    for i in range(argsCount): # mapping members in one dict to multiple function arguments (common case for GET APIs)
                        tp = types.get(model[i],None)
                        if tp is None:
                            output.append(data[i])
                        elif tp is PyopReq:
                            output.append(self)
                        else:
                            output.append(parseJsonToClass(data[model[i]],tp))
                return output
        else:
            # data = jso
            data = dict2obj(data)
        return data

    def _build_protocol_request(self):
        """Convert handler state into a protocol-neutral Request."""
        path, qbytes = split_path_query(self.path)
        headers = Headers()
        total = 0
        for k, v in self.headers.items():
            headers.add(k, v)
            total += len(k) + len(v)
        max_hdr = getattr(config, 'max_header_size', 16384)
        body = b""
        if self.command not in ("GET", "HEAD", "OPTIONS", "DELETE"):
            try:
                length = int(self.headers.get('Content-Length', 0) or 0)
            except Exception:
                length = 0
            if length:
                max_body = getattr(config, 'max_body_size', 1024 * 1024)
                if length > max_body:
                    # drain nothing; let dispatch return 413 with empty body
                    return None, 413
                try:
                    body = self.rfile.read(length)
                except Exception:
                    raise ValueError("bad body")
        scheme = 'https' if getattr(config, 'enableTLS', False) else 'http'
        host = self.headers.get('Host', '')
        return PyopRequest(self.command, path, qbytes, headers, body or b"",
                           tuple(self.client_address), scheme, host), total

    def GETPOST(self):  # rtype stands for request type
        try:
            built, extra = self._build_protocol_request()
        except ValueError:
            self._send_protocol_error(400, "Bad Request")
            return
        if built is None and extra == 413:
            # body too large: still build minimal request so app returns 413
            path, qbytes = split_path_query(self.path)
            headers = Headers([(k, v) for (k, v) in self.headers.items()])
            built = PyopRequest(self.command, path, qbytes, headers, b"x" * (getattr(config, 'max_body_size', 1024 * 1024) + 1),
                                tuple(self.client_address), 'http', self.headers.get('Host', ''))
        app = get_application()
        resp = app(built)
        # buffer streams: dev server does not chunk-encode
        if resp.is_stream:
            resp = resp.buffered()
        self._send_protocol_response(resp, head_only=(self.command == "HEAD"))

    def _send_protocol_response(self, resp, head_only=False):
        # Preserve repeated headers (e.g. Set-Cookie).
        self.log_request(resp.status)
        self.send_response_only(resp.status)
        # Map protocol headers; ensure date/server/content-length semantics.
        sent_ct = False
        sent_cl = False
        for (k, v) in resp.headers.items():
            lname = k.lower()
            if lname == 'content-length':
                sent_cl = True
            if lname == 'content-type':
                sent_ct = True
            self.send_header(k, v)
        body = resp.body if not resp.is_stream else b"".join(resp.iter_bytes())
        if not sent_cl:
            self.send_header('content-length', str(len(body)))
        if not sent_ct:
            self.send_header('content-type', 'text/html')
        self.send_header('server', server_info.server_name + ' ' + server_info.server_version)
        self.end_headers()
        if not head_only and body:
            if isinstance(body, str):
                body = body.encode('utf-8')
            self.wfile.write(bytes(body))

    def _send_protocol_error(self, code, message):
        body = "{} {}".format(code, message).encode('utf-8')
        self.log_request(code)
        self.send_response_only(code)
        self.send_header('date', self.date_time_string())
        self.send_header('content-type', 'text/plain')
        self.send_header('content-length', str(len(body)))
        self.send_header('server', server_info.server_name + ' ' + server_info.server_version)
        self.end_headers()
        self.wfile.write(body)

    def send_custom_response(self,content:bytes,responseCode=200,mimeType='text/html'):
        self.log_request(responseCode)
        self.send_response_only(responseCode)
        self.send_header('date',self.date_time_string())
        self.send_header('content-type', mimeType)
        self.send_header('server',server_info.server_name + ' '+ server_info.server_version)
        self.end_headers()
        if(type(content) is not bytes):
            if(type(content) is not str):
                content = bytes(str(content), 'utf-8')
            else:
                content = bytes(content, 'utf-8')
        self.wfile.write(content)

    def handle_one_request(self):
        """Handle a single HTTP request.
        Overridden from base class

        """
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            max_url = getattr(config, 'max_url_length', 8192)
            if len(self.path or "") > max_url:
                self._send_protocol_error(414, "URI Too Long")
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                if getattr(config, 'production', False) or not config.fool_nmap:
                    self.send_error(
                        HTTPStatus.NOT_IMPLEMENTED,
                        "Unsupported method (%r)" % self.command)
                else:
                    self.send_custom_response(config.fool_nmap_content,200,'application/json')
                return
            method = getattr(self, mname)
            method()
            self.wfile.flush() #actually send the response if not already done.
        except timeout as e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

    # Explicit standard methods; all dispatch through the shared layer.
    def do_GET(self):
        self.GETPOST()
        return

    def do_POST(self):
        self.GETPOST()
        return

    def do_PUT(self):
        self.GETPOST()
        return

    def do_PATCH(self):
        self.GETPOST()
        return

    def do_DELETE(self):
        self.GETPOST()
        return

    def do_HEAD(self):
        self.GETPOST()
        return

    def do_OPTIONS(self):
        self.GETPOST()
        return

#making seperate class and not using one in http libary to support backward compatiblity with python versions
class ThreadedPyOPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def run():
    print("Starting server ...")
    app = get_application()
    app.startup()
    server_address = (config.host, config.port)
    httpd = ThreadedPyOPServer(server_address, PyOPSever)
    httpd.timeout = getattr(config, 'request_timeout', 30) or 30
    print("running server at ", server_address)
    print("WD :- ", dir_path + config.static)
    if config.enableTLS:
        from ssl import wrap_socket
        httpd.socket = wrap_socket (httpd.socket,
            keyfile= config.PATH_TLS_KEY_FILE,
            certfile= config.PATH_TLS_CERT_FILE, server_side=True)
        print("Listening Securely")

    # NOTE: BaseServer.shutdown() blocks until the serve_forever() loop
    # exits, so it MUST be called from a different thread than the one
    # running serve_forever() (here: the main thread). Calling it directly
    # inside the signal handler deadlocks and the process appears stuck at
    # "Shutting down ...". Hence the handler only flips state and kicks off
    # a daemon thread that performs the blocking shutdown().
    state = {"stopping": False}

    def _graceful(signum, frame):
        if state["stopping"]:
            print("Second interrupt: forcing exit ...")
            try:
                httpd.server_close()
            finally:
                import os as _os
                _os._exit(1)
            return
        state["stopping"] = True
        print("Shutting down: draining active requests ...")
        deadline = getattr(config, 'shutdown_drain_seconds', 10) or 10
        app.shutdown()

        def _stop():
            try:
                httpd.shutdown()
            except Exception as exc:
                print("shutdown error: {}".format(exc))

        t = threading.Thread(target=_stop, daemon=True)
        t.start()
        # Drain deadline: if serve_forever() has not exited by then, force
        # the listening socket closed so the process can exit. Daemon
        # request threads (daemon_threads=True) do not block exit.
        def _force():
            if t.is_alive():
                print("Drain deadline exceeded: forcing close ...")
                try:
                    httpd.server_close()
                except Exception:
                    pass
        timer = threading.Timer(deadline, _force)
        timer.daemon = True
        timer.start()

    try:
        signal.signal(signal.SIGTERM, _graceful)
        signal.signal(signal.SIGINT, _graceful)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        # Fallback when signals are unavailable (e.g. Windows): same
        # non-blocking shutdown path as _graceful.
        if not state["stopping"]:
            state["stopping"] = True
            print("Shutting down: draining active requests ...")
            app.shutdown()
            threading.Thread(target=httpd.shutdown, daemon=True).start()
    finally:
        app.shutdown()
        try:
            httpd.server_close()
        except Exception:
            pass
        print("Server stopped.")

if __name__ == '__main__':
    run()
