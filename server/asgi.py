"""ASGI HTTP adapter (stdlib only, no third-party packages).

Usage with Uvicorn / Hypercorn (not required at runtime)::

    # uvicorn server.asgi:application
    from server.asgi import application
"""
from server.application import PyopApplication, application as _default_app
from server.http import Headers, Request, split_path_query


def _headers_from_scope(scope):
    items = []
    for k, v in scope.get("headers", []):
        try:
            items.append((k.decode("latin-1"), v.decode("latin-1")))
        except Exception:
            continue
    return Headers(items)


def request_from_scope(scope, body):
    target = scope.get("raw_path")
    if target is None:
        target = scope.get("path", "/")
        if isinstance(target, bytes):
            target = target.decode("latin-1")
    else:
        if isinstance(target, bytes):
            target = target.decode("latin-1")
    qs = scope.get("query_string", b"")
    if isinstance(qs, str):
        qs = qs.encode("latin-1")
    if "?" in str(target):
        path, qbytes = split_path_query(str(target))
    else:
        path = str(target) or "/"
        qbytes = bytes(qs or b"")
    method = scope.get("method", "GET")
    headers = _headers_from_scope(scope)
    scheme = scope.get("scheme", "http")
    host = headers.get("host", "") or scope.get("server", ["", 0])[0]
    client = tuple(scope.get("client", ("unknown", 0)) or ("unknown", 0))
    return Request(method, path, qbytes, headers, body or b"", client, scheme, host)


def asgi_app_factory(app=None):
    pyop = app or _default_app

    async def asgi_app(scope, receive, send):
        if scope.get("type") == "lifespan":
            while True:
                msg = await receive()
                if msg.get("type") == "lifespan.startup":
                    try:
                        pyop.startup()
                        await send({"type": "lifespan.startup.complete"})
                    except Exception as exc:
                        await send({"type": "lifespan.startup.failed", "message": str(exc)})
                elif msg.get("type") == "lifespan.shutdown":
                    try:
                        pyop.shutdown()
                    finally:
                        await send({"type": "lifespan.shutdown.complete"})
                    return
            return
        if scope.get("type") != "http":
            return
        body = b""
        more = True
        while more:
            msg = await receive()
            if msg.get("type") == "http.request":
                body += msg.get("body", b"") or b""
                more = msg.get("more_body", False)
            elif msg.get("type") == "http.disconnect":
                return
            else:
                more = False
        try:
            req = request_from_scope(scope, body)
        except ValueError:
            await send({"type": "http.response.start", "status": 400,
                        "headers": [(b"content-type", b"text/plain"),
                                    (b"content-length", b"15")]})
            await send({"type": "http.response.body", "body": b"400 Bad Request"})
            return
        resp = pyop(req)
        if resp.is_stream:
            chunks = list(resp.iter_bytes())
            body_out = b"".join(chunks)
            resp.headers.set("content-length", str(len(body_out)))
        else:
            body_out = resp.body
        if req.method == "HEAD":
            body_out = b""
        raw_headers = [(k.lower().encode("latin-1"), v.encode("latin-1"))
                       for (k, v) in resp.headers.items()]
        await send({"type": "http.response.start", "status": resp.status,
                    "headers": raw_headers})
        await send({"type": "http.response.body", "body": body_out})

    return asgi_app


application = asgi_app_factory()
