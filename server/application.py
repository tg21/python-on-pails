"""Shared application dispatch layer (stdlib only).

All serving entry points (dev server, WSGI, ASGI) build a protocol-neutral
``server.http.Request`` and call :class:`PyopApplication` to get a
``server.http.Response``. Business-logic behaviour (views, controllers,
input models, custom responses) is preserved here in one place.
"""
import json
import os

from server.http import Headers, Request, Response, error_response
from server.misc import jsonify, parseJsonToClass
from server.responseHandler import (
    _processPyHtml,
    _read_bin,
    _run_python_file,
    subprocessPyFile,
)
from server.settings import config

STANDARD_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
# Methods the dev/WSGI/ASGI stack explicitly implements.
# Anything else (e.g. TRACE, CONNECT, custom verbs) -> 501 in production mode.
SUPPORTED_METHODS = set(STANDARD_METHODS)


def _is_production():
    return bool(getattr(config, "production", False))


def _limit(name, default):
    return getattr(config, name, default)


def apply_proxy_headers(request):
    """Rewrite client/scheme/host from trusted proxy headers (in place)."""
    trusted = getattr(config, "trust_proxy_headers", False)
    if not trusted:
        return request
    # allow list of trusted proxy IPs; True means trust all (documented for
    # use behind Nginx/Caddy/Cloudflare that strip spoofed headers).
    allow = getattr(config, "trusted_proxies", None)
    if isinstance(allow, (list, tuple, set)) and allow:
        client_ip = (request.client[0] if request.client else "")
        if client_ip not in allow and "*" not in allow:
            return request
    h = request.headers
    xff = h.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            port = request.client[1] if request.client else 0
            try:
                port = int(h.get("x-forwarded-port", port) or port)
            except Exception:
                pass
            request.client = (first, port)
    proto = h.get("x-forwarded-proto") or h.get("x-forwarded-scheme")
    if proto:
        request.scheme = proto.split(",")[0].strip().lower()
    host = h.get("x-forwarded-host") or h.get("forwarded-host")
    if host:
        request.host = host.split(",")[0].strip()
        request.url = "{}://{}{}".format(request.scheme, request.host, request.path)
    return request


class _LegacyReqShim:
    """Minimal PyopReq-compatible object for legacy controllers.

    Legacy ``req: PyopReq`` params expect ``client_address``,
    ``send_custom_response`` and ``close_connection``. Calls to
    ``send_custom_response`` are captured so dispatch can return them.
    """

    def __init__(self, request):
        self._request = request
        self.client_address = request.client
        self.close_connection = False
        self._custom = None

    def send_custom_response(self, content, responseCode=200, mimeType="text/html"):
        if isinstance(content, str):
            content = content.encode("utf-8")
        elif not isinstance(content, (bytes, bytearray)):
            content = str(content).encode("utf-8")
        self._custom = Response(bytes(content), status=responseCode, mime_type=mimeType)


def parse_data_to_object(data, model, types=None, args_count=0, shim=None):
    """Port of PyOPSever.ParseRequestDataInToObject (no handler dependency)."""
    if isinstance(data, str):
        if data == "":
            data = {}
        else:
            try:
                data = json.loads(data)
            except Exception:
                if getattr(config, "logging", False):
                    pass
                data = jsonify(data)
    elif not isinstance(data, dict):
        raise ValueError("unsupported request data format")
    if model is not None:
        if types is None:
            data = parseJsonToClass(data, model)
        else:
            output = []
            if args_count == 1:
                tp = types.get(model[0], None)
                output.append(parseJsonToClass(data, tp))
            else:
                for i in range(args_count):
                    tp = types.get(model[i], None)
                    if tp is None:
                        output.append(data[i] if isinstance(data, (list, tuple)) else data.get(model[i]) if isinstance(data, dict) else None)
                    elif getattr(tp, "__name__", "") == "PyopReq" or tp is _LegacyReqShim or "PyopReq" in str(tp):
                        output.append(shim)
                    else:
                        val = data[model[i]] if isinstance(data, dict) and model[i] in data else (data.get(model[i]) if isinstance(data, dict) else None)
                        output.append(parseJsonToClass(val, tp))
            return output
    else:
        from server.misc import dict2obj
        data = dict2obj(data) if isinstance(data, dict) else data
    return data


def _raw_text(request):
    body = request.body
    if isinstance(body, (bytes, bytearray)):
        try:
            return bytes(body).decode("utf-8")
        except Exception:
            return bytes(body).decode("latin-1")
    return ""


def format_request_data(request, model, types=None, args_count=0, shim=None):
    if request.method == "GET":
        data = request.query_string.decode("latin-1") if request.query_string else ""
    else:
        data = _raw_text(request)
    return parse_data_to_object(data, model, types, args_count, shim=shim)


def _to_response_body(result):
    if isinstance(result, (bytes, bytearray)):
        return bytes(result), None
    if isinstance(result, str):
        return result.encode("utf-8"), None
    if hasattr(result, "__iter__") and not isinstance(result, dict):
        # allow generator streaming; adapters buffer when protocol forbids it
        return result, None
    return result, None


class PyopApplication:
    """Callable dispatch: Request -> Response."""

    def __init__(self, views=None, get_routes=None, post_routes=None, static_dir=None, views_dir=None):
        # Lazy import so tests can inject fakes and app reload picks up edits.
        if views is None or get_routes is None or post_routes is None:
            from mvc.views.views import views as _views
            from mvc.controllers.routes import getRoutes as _get, postRoutes as _post
            views = _views if views is None else views
            get_routes = _get if get_routes is None else get_routes
            post_routes = _post if post_routes is None else post_routes
        self.views = views
        self.get_routes = get_routes
        self.post_routes = post_routes
        base = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/"
        self.static_dir = static_dir or (base + config.static)
        self.views_dir = views_dir or (base + getattr(config, "views", "mvc/views/"))
        self._startup_hooks = list(getattr(config, "on_startup", []) or [])
        self._shutdown_hooks = list(getattr(config, "on_shutdown", []) or [])
        self._ready = False
        self._draining = False

    # -- lifecycle / operations --
    def add_startup_hook(self, fn):
        self._startup_hooks.append(fn)

    def add_shutdown_hook(self, fn):
        self._shutdown_hooks.append(fn)

    def startup(self):
        for fn in self._startup_hooks:
            fn()
        self._ready = True

    def shutdown(self):
        self._draining = True
        for fn in self._shutdown_hooks:
            try:
                fn()
            except Exception:
                if getattr(config, "logging", False):
                    raise
        self._ready = False

    @property
    def ready(self):
        return self._ready and not self._draining

    # -- dispatch --
    def __call__(self, request):
        try:
            apply_proxy_headers(request)
            if self._draining:
                return error_response(503, "Service Unavailable: draining")
            # limits -> standards-based codes (production) or legacy fallback
            max_url = _limit("max_url_length", 8192)
            if len(request.path or "") + len(request.query_string or b"") > max_url:
                return error_response(414, "URI Too Long")
            max_hdr = _limit("max_header_size", 16384)
            total_hdr = sum(len(k) + len(v) for (k, v) in request.headers.items())
            if total_hdr > max_hdr:
                return error_response(431, "Request Header Fields Too Large")
            body_len = len(request.body) if isinstance(request.body, (bytes, bytearray)) else 0
            if not isinstance(request.body, (bytes, bytearray)):
                return error_response(400, "Bad Request")
            max_body = _limit("max_body_size", 1024 * 1024)
            if body_len > max_body:
                return error_response(413, "Payload Too Large")
            method = (request.method or "").upper()
            if method not in SUPPORTED_METHODS:
                if _is_production() or not getattr(config, "fool_nmap", False):
                    return error_response(501, "Not Implemented")
                return Response(getattr(config, "fool_nmap_content", ""), status=200, mime_type="application/json")
            if method == "OPTIONS":
                allow = self._allow_for(request.path)
                h = Headers()
                h.set("allow", allow)
                h.set("content-length", "0")
                return Response(b"", status=204 if allow else 404, headers=h, mime_type=None)

            route_kind, route = self._find_route(method, request.path)
            if route_kind is None:
                return self._serve_static_fallback(request)
            if route_kind == "view":
                resp = self._handle_view(route)
            elif route_kind == "method_mismatch":
                return self._method_not_allowed(request.path)
            else:
                resp = self._handle_controller(request, route)
            if method == "HEAD" and not resp.is_stream:
                # HEAD: same headers, empty body, keep content-length
                h = Headers(resp.headers.items())
                empty = Response(b"", status=resp.status, headers=h, mime_type=None)
                return empty
            return resp
        except ValueError:
            return error_response(400, "Bad Request")
        except Exception as exc:
            if getattr(config, "logging", False):
                print(exc)
            return error_response(500, "Internal Server Error")

    def _allow_for(self, path):
        allowed = []
        if path in (self.views or {}):
            allowed.append("GET")
        if path in (self.get_routes or {}):
            allowed.append("GET")
        if path in (self.post_routes or {}):
            allowed.extend(["POST", "PUT", "PATCH", "DELETE"])
        # static file exists -> GET/HEAD
        if not allowed:
            full = os.path.join(self.static_dir, path.lstrip("/"))
            views_full = os.path.join(getattr(self, "views_dir", self.static_dir), path.lstrip("/"))
            if os.path.isfile(full) or os.path.isfile(views_full):
                allowed.extend(["GET", "HEAD"])
        # OPTIONS always allowed on known paths
        if allowed and "OPTIONS" not in allowed:
            allowed.append("OPTIONS")
        return ", ".join(sorted(set(allowed)))

    def _find_route(self, method, path):
        if path in (self.views or {}):
            return "view", self.views[path]
        if method in ("GET", "HEAD"):
            if path in (self.get_routes or {}):
                return "controller", self.get_routes[path]
            if path in (self.post_routes or {}):
                # path exists but wrong method
                return "method_mismatch", self.post_routes[path]
        elif method in ("POST", "PUT", "PATCH", "DELETE"):
            if path in (self.post_routes or {}):
                return "controller", self.post_routes[path]
            if path in (self.get_routes or {}):
                return "method_mismatch", self.get_routes[path]
        else:
            return None, None
        return None, None

    def _handle_view(self, route):
        if callable(route):
            result = route()
            body, _ = _to_response_body(result)
            if isinstance(body, (bytes, bytearray)):
                return Response(bytes(body), status=200, mime_type="text/html")
            if hasattr(body, "__iter__"):
                return Response(body, status=200, mime_type="text/html")
            return Response(body, status=200, mime_type="text/html")
        if isinstance(route, str):
            full = os.path.join(self.static_dir, route)
            return self._serve_file(full, default_mime="text/html")
        raise ValueError("bad view route")

    def _handle_controller(self, request, route):
        if isinstance(route, tuple) and route and route[0] == "method_mismatch":
            route = route[1]
        # route may be the sentinel string from _find_route
        if isinstance(route, str) and route == "method_mismatch":
            pass
        input_model = None
        custom = None
        action = route
        if isinstance(route, dict):
            action = route.get("action")
            input_model = route.get("input", None)
            custom = route.get("customResponse", None)
        if isinstance(action, str) and action == "method_mismatch":
            return self._method_not_allowed(request.path)
        shim = _LegacyReqShim(request)
        if callable(action):
            if input_model is None:
                params = action.__code__.co_varnames
                types = action.__annotations__
                argc = action.__code__.co_argcount
                # Detect PyopReq-annotated params by name (robust to import identity)
                adapted_types = dict(types)
                for pname, t in types.items():
                    if getattr(t, "__name__", "") == "PyopReq":
                        adapted_types[pname] = _LegacyReqShim
                # need raw param names tuple for parse_data_to_object
                req_data = format_request_data(request, params, adapted_types, argc, shim=shim)
                if not isinstance(req_data, list):
                    req_data = [req_data]
                # replace shim placeholder identity: parse uses type-name check already
                result = action(*req_data)
                if shim._custom is not None:
                    return shim._custom
                return self._wrap_result(result, custom, default_mime="application/json")
            else:
                req_data = format_request_data(request, input_model, shim=shim)
                result = action(req_data)
                if shim._custom is not None:
                    return shim._custom
                return self._wrap_result(result, custom, default_mime="application/json")
        if isinstance(action, str) and action.endswith(".py"):
            base = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/"
            full = base + config.controllers + action
            req_data = format_request_data(request, input_model, shim=shim)
            res = subprocessPyFile(full, req_data)
            return self._wrap_result(res, custom, default_mime="application/json")
        # method mismatch sentinel
        if route == "method_mismatch" or action == "method_mismatch":
            return self._method_not_allowed(request.path)
        raise ValueError("bad controller route")

    def _method_not_allowed(self, path):
        if _is_production():
            h = Headers()
            h.set("allow", self._allow_for(path))
            h.set("content-type", "text/plain")
            body = b"405 Method Not Allowed"
            h.set("content-length", str(len(body)))
            return Response(body, status=405, headers=h, mime_type=None)
        # legacy compat: fall through to static fallback (may 500/200)
        return self._serve_static_fallback(Request("GET", path))

    def _wrap_result(self, result, custom, default_mime="application/json"):
        if isinstance(result, Response):
            return result
        if custom is None:
            body, _ = _to_response_body(result)
            if isinstance(body, (bytes, bytearray)):
                return Response(body, status=200, mime_type=default_mime)
            if hasattr(body, "__iter__"):
                return Response(body, status=200, mime_type=default_mime)
            if isinstance(body, dict):
                return Response.json_body(body, status=200)
            return Response(body, status=200, mime_type=default_mime)
        if custom is True:
            if not isinstance(result, dict):
                raise ValueError("customResponse=True requires dict result")
            content = result.get("content", b"")
            code = result.get("code", 200)
            mime = result.get("mimeType", default_mime)
            if isinstance(content, str):
                content = content.encode("utf-8")
            elif not isinstance(content, (bytes, bytearray)):
                content = str(content).encode("utf-8")
            return Response(bytes(content), status=code, mime_type=mime)
        if isinstance(custom, dict):
            code = custom.get("code", 200)
            mime = custom.get("mimeType", default_mime)
            if isinstance(result, (bytes, bytearray)):
                return Response(bytes(result), status=code, mime_type=mime)
            if isinstance(result, str):
                return Response(result.encode("utf-8"), status=code, mime_type=mime)
            if isinstance(result, dict):
                raw = json.dumps(result).encode("utf-8")
                h = Headers()
                h.set("content-type", mime)
                h.set("content-length", str(len(raw)))
                return Response(raw, status=code, headers=h, mime_type=None)
            return Response(result, status=code, mime_type=mime)
        raise ValueError("bad customResponse")

    def _serve_file(self, full_path, default_mime="text/html"):
        from server.mimeTypes import mimeTypes  # local import: big file
        norm = os.path.normpath(full_path)
        static_root = os.path.normpath(self.static_dir)
        views_root = os.path.normpath(getattr(self, "views_dir", static_root))
        if not (norm.startswith(static_root) or norm.startswith(views_root)):
            return error_response(403, "Forbidden")
        try:
            if norm.endswith(".py"):
                return Response(_run_python_file(norm), status=200, mime_type="text/html")
            if norm.endswith(".pyhtml"):
                return Response(_processPyHtml(norm), status=200, mime_type="text/html")
            if norm.endswith(".html"):
                return Response(_read_bin(norm), status=200, mime_type="text/html")
            ext = "." + norm.split(".")[-1] if "." in norm else ""
            return Response(_read_bin(norm), status=200, mime_type=mimeTypes.get(ext, "application/octet-stream"))
        except FileNotFoundError:
            if _is_production() or not getattr(config, "wildcard_response", False):
                return error_response(404, "Not Found")
            # legacy wildcard: missing files bubble as 500 FileNotFoundError name
            return Response("FileNotFoundError", status=500, mime_type="text/html")
        except Exception as exc:
            if getattr(config, "logging", False):
                print(exc)
            return error_response(500, "Internal Server Error")

    def _serve_static_fallback(self, request):
        # _find_route returned None; check method-mismatch first
        if request.path in (self.get_routes or {}) or request.path in (self.post_routes or {}):
            if _is_production():
                h = Headers()
                h.set("allow", self._allow_for(request.path))
                body = b"405 Method Not Allowed"
                h.set("content-type", "text/plain")
                h.set("content-length", str(len(body)))
                return Response(body, status=405, headers=h, mime_type=None)
        rel = request.path.lstrip("/")
        # 1) documented location: files under config.static (mvc/views/static/).
        full = os.path.join(self.static_dir, rel)
        if os.path.isfile(full):
            return self._serve_file(full)
        # 2) convenience: a bare file dropped directly in the views folder
        # (config.views, e.g. mvc/views/index.py requested as /index.py).
        # Static takes precedence so existing apps are unaffected.
        views_full = os.path.join(getattr(self, "views_dir", self.static_dir), rel)
        if os.path.isfile(views_full):
            return self._serve_file(views_full)
        if _is_production() or not getattr(config, "wildcard_response", False):
            return error_response(404, "Not Found")
        return Response("FileNotFoundError", status=500, mime_type="text/html")


# Default application instance (importable without third-party packages).
application = PyopApplication()
