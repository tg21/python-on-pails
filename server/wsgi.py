"""WSGI adapter (PEP 3333, stdlib only).

Usage with Gunicorn / uWSGI / Waitress (not required at runtime)::

    # gunicorn server.wsgi:application --workers 3
    from server.wsgi import application
"""
from server.application import PyopApplication, application as _default_app
from server.http import Headers, Request, split_path_query


def _headers_from_environ(environ):
    items = []
    for k, v in environ.items():
        if k.startswith("HTTP_"):
            name = k[5:].replace("_", "-")
            items.append((name, v))
        elif k in ("CONTENT_TYPE", "CONTENT_LENGTH") and v not in ("", None):
            name = "Content-Type" if k == "CONTENT_TYPE" else "Content-Length"
            items.append((name, v))
    # cookies arrive as single HTTP_COOKIE header; preserved as-is
    return Headers(items)


def request_from_environ(environ, max_body=None):
    target = environ.get("RAW_URI") or environ.get("REQUEST_URI") or environ.get("PATH_INFO", "/")
    qs = environ.get("QUERY_STRING", "")
    if "?" in target:
        path, qbytes = split_path_query(target)
    else:
        path = target or "/"
        qbytes = qs.encode("latin-1") if isinstance(qs, str) else (qs or b"")
    method = environ.get("REQUEST_METHOD", "GET")
    headers = _headers_from_environ(environ)
    body = b""
    try:
        length = int(environ.get("CONTENT_LENGTH", 0) or 0)
    except Exception:
        length = 0
    inp = environ.get("wsgi.input")
    if inp is not None and length > 0:
        try:
            body = inp.read(length)
        except Exception:
            raise ValueError("bad body")
    elif inp is not None and headers.get("transfer-encoding", "").lower() == "chunked":
        try:
            body = inp.read()
        except Exception:
            raise ValueError("bad body")
    scheme = environ.get("wsgi.url_scheme", "http")
    host = environ.get("HTTP_HOST") or environ.get("SERVER_NAME", "")
    client = (environ.get("REMOTE_ADDR", "unknown"), int(environ.get("REMOTE_PORT", 0) or 0))
    return Request(method, path, qbytes, headers, body or b"", client, scheme, host)


def wsgi_app_factory(app=None):
    pyop = app or _default_app

    def wsgi_app(environ, start_response):
        try:
            req = request_from_environ(environ)
        except ValueError:
            status = "400 Bad Request"
            body = b"400 Bad Request"
            headers = [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))]
            start_response(status, headers)
            return [body]
        resp = pyop(req)
        if resp.is_stream:
            body = b"".join(resp.iter_bytes())
            # set accurate content length when buffering was possible
            resp.headers.set("content-length", str(len(body)))
        else:
            body = resp.body
        if req.method == "HEAD":
            body = b""
        status_text = "{} {}".format(resp.status, _reason(resp.status))
        start_response(status_text, resp.headers.to_wsgi_list())
        return [body]

    return wsgi_app


def _reason(status):
    from http.client import responses
    return responses.get(int(status), "Unknown")


application = wsgi_app_factory()
