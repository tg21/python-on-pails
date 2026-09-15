"""Protocol-neutral HTTP contracts (stdlib only).

Request/Response are plain objects shared by the dev server, WSGI and ASGI
adapters so business logic never touches server-specific APIs.
"""
import json
from http.cookies import SimpleCookie
from urllib.parse import parse_qsl, urlsplit


class Headers:
    """Case-insensitive multi-value header container.

    Preserves insertion order and repeated headers (e.g. Set-Cookie).
    """

    def __init__(self, items=None):
        self._items = []  # list of (original-name, value)
        if items:
            for k, v in items:
                self.add(k, v)

    def add(self, name, value):
        self._items.append((str(name), str(value)))

    def set(self, name, value):
        lname = str(name).lower()
        self._items = [(k, v) for (k, v) in self._items if k.lower() != lname]
        self._items.append((str(name), str(value)))

    def get(self, name, default=None):
        lname = str(name).lower()
        for k, v in self._items:
            if k.lower() == lname:
                return v
        return default

    def get_all(self, name):
        lname = str(name).lower()
        return [v for (k, v) in self._items if k.lower() == lname]

    def __contains__(self, name):
        return self.get(name) is not None

    def items(self):
        return list(self._items)

    def to_wsgi_list(self):
        return list(self._items)

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return "Headers({!r})".format(self._items)


def _parse_cookies(cookie_headers):
    cookies = {}
    jar = SimpleCookie()
    for h in cookie_headers:
        try:
            jar.load(h)
        except Exception:
            continue
    for k, v in jar.items():
        cookies[k] = v.value
    return cookies


class Request:
    """Protocol-neutral inbound request."""

    def __init__(self, method, path, query_string=b"",
                 headers=None, body=b"", client=("unknown", 0),
                 scheme="http", host=""):
        self.method = (method or "GET").upper()
        self.path = path or "/"
        if isinstance(query_string, str):
            query_string = query_string.encode("latin-1")
        self.query_string = query_string or b""
        self.headers = headers if headers is not None else Headers()
        if isinstance(body, (bytes, bytearray)):
            self.body = bytes(body)
        else:
            # streaming iterables are buffered by adapters before dispatch;
            # keep reference for length checks at the adapter layer.
            self.body = body
        self.client = client  # (host, port)
        self.scheme = scheme or "http"
        self.host = host or self.headers.get("host", "")
        cookie_headers = self.headers.get_all("cookie")
        # WSGI splits Cookie into HTTP_COOKIE single value; ASGI too.
        self.cookies = _parse_cookies(cookie_headers)
        # parsed query: last value wins, like query-string fallback in misc.jsonify
        self.query = {}
        try:
            qs = self.query_string.decode("latin-1")
            for k, v in parse_qsl(qs, keep_blank_values=True):
                self.query[k] = v
        except Exception:
            self.query = {}
        self.url = self._build_url()

    def _build_url(self):
        qs = self.query_string.decode("latin-1") if self.query_string else ""
        base = "{}://{}{}".format(self.scheme, self.host, self.path)
        if qs:
            base += "?" + qs
        return base

    @property
    def text(self):
        if isinstance(self.body, (bytes, bytearray)):
            try:
                return bytes(self.body).decode("utf-8")
            except Exception:
                return bytes(self.body).decode("latin-1")
        return ""

    def json(self):
        data = self.text
        if not data:
            return {}
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, dict) else {"_body": parsed}
        except Exception:
            # fall back to a=1&b=2 query-string parse (legacy jsonify behavior)
            out = {}
            for kv in data.strip().split("&"):
                parts = kv.strip().split("=")
                if len(parts) == 2:
                    out[parts[0]] = parts[1]
            return out

    def __repr__(self):
        return "Request({} {})".format(self.method, self.url)


class Response:
    """Protocol-neutral outbound response."""

    def __init__(self, body=b"", status=200, headers=None, mime_type="text/html"):
        self.status = int(status)
        self.headers = headers if headers is not None else Headers()
        self._body_iter = None
        if hasattr(body, "__iter__") and not isinstance(body, (bytes, str, bytearray)):
            # streaming iterable of bytes/str chunks
            self._body_iter = body
            self.body = b""
            self.is_stream = True
        else:
            self.is_stream = False
            if isinstance(body, str):
                self.body = body.encode("utf-8")
            elif isinstance(body, (bytes, bytearray)):
                self.body = bytes(body)
            elif body is None:
                self.body = b""
            else:
                self.body = str(body).encode("utf-8")
        if "content-type" not in self.headers and mime_type:
            # preserve explicit mime, allow caller override via headers
            self.headers.set("content-type", mime_type)
        if not self.is_stream and "content-length" not in self.headers:
            self.headers.set("content-length", str(len(self.body)))

    def iter_bytes(self):
        if self.is_stream:
            for chunk in self._body_iter:
                if isinstance(chunk, str):
                    yield chunk.encode("utf-8")
                else:
                    yield bytes(chunk)
        else:
            yield self.body

    def buffered(self):
        """Return a buffered copy (joins streams)."""
        if self.is_stream:
            data = b"".join(self.iter_bytes())
            return Response(data, self.status, self.headers)
        return self

    @property
    def text(self):
        if self.is_stream:
            return b"".join(self.iter_bytes()).decode("utf-8", "replace")
        return self.body.decode("utf-8", "replace")

    # -- helpers at application layer --
    @staticmethod
    def json_body(data, status=200, headers=None):
        raw = json.dumps(data).encode("utf-8")
        h = headers if headers is not None else Headers()
        h.set("content-type", "application/json")
        h.set("content-length", str(len(raw)))
        r = Response(b"", status=status, headers=h, mime_type=None)
        r.body = raw
        r.is_stream = False
        return r

    @staticmethod
    def text_body(text, status=200, mime_type="text/html", headers=None):
        return Response(text, status=status, headers=headers, mime_type=mime_type)

    def __repr__(self):
        return "Response(status={})".format(self.status)


def error_response(status, message, mime_type="text/plain"):
    body = "{} {}".format(status, message).encode("utf-8")
    h = Headers()
    h.set("content-type", mime_type)
    h.set("content-length", str(len(body)))
    return Response(body, status=status, headers=h, mime_type=None)


def split_path_query(target):
    """Split origin-form request target into (path, query_bytes)."""
    if not target:
        return "/", b""
    # target may be absolute-form when behind a proxy; reduce to path+query.
    if "://" in target:
        try:
            parts = urlsplit(target)
            path = parts.path or "/"
            return path, parts.query.encode("latin-1")
        except Exception:
            pass
    if "?" in target:
        p, q = target.split("?", 1)
        return p or "/", q.encode("latin-1")
    return target or "/", b""
