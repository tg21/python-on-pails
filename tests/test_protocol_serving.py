import asyncio
import io
import os
import unittest

from server.http import Headers, Request, Response
from server.application import PyopApplication
from server import wsgi as wsgi_mod
from server import asgi as asgi_mod
from server.settings import config


def req(method, path, body=b"", headers=None, client=("127.0.0.1", 5000)):
    if "?" in path:
        p, q = path.split("?", 1)
        qb = q.encode("latin-1")
    else:
        p, qb = path, b""
    h = Headers(headers or [])
    return Request(method, p, qb, h, body, client, "http", "test")


class TestContracts(unittest.TestCase):
    def test_headers_case_insensitive_and_repeated(self):
        h = Headers([("Set-Cookie", "a=1"), ("set-cookie", "b=2"), ("Content-Type", "text/html")])
        self.assertEqual(h.get("SET-COOKIE"), "a=1")
        self.assertEqual(h.get_all("set-cookie"), ["a=1", "b=2"])
        h.set("Content-Type", "application/json")
        self.assertEqual(h.get_all("content-type"), ["application/json"])

    def test_request_helpers(self):
        r = Request("get", "/sum", b"a=1&b=2", Headers([("Cookie", "s=abc")]), b'{"a":1}', ("1.2.3.4", 9), "http", "x")
        self.assertEqual(r.method, "GET")
        self.assertEqual(r.query, {"a": "1", "b": "2"})
        self.assertEqual(r.cookies, {"s": "abc"})
        self.assertIn("a", r.json())

    def test_response_content_length_and_stream(self):
        r = Response(b"hi")
        self.assertEqual(r.headers.get("content-length"), "2")
        s = Response((c for c in [b"a", b"b"]), mime_type="text/plain")
        self.assertTrue(s.is_stream)
        self.assertEqual(b"".join(s.iter_bytes()), b"ab")

    def test_no_third_party(self):
        for mod in ("server.http", "server.application", "server.wsgi", "server.asgi"):
            m = __import__(mod, fromlist=["x"])
            src = open(m.__file__).read()
            for pkg in ("gunicorn", "uvicorn", "hypercorn", "waitress", "flask", "django", "requests"):
                self.assertNotIn("import " + pkg, src)


class TestDispatch(unittest.TestCase):
    def setUp(self):
        self._prod = config.production
        self._wild = config.wildcard_response
        self._fool = config.fool_nmap
        config.production = True
        config.wildcard_response = False
        config.fool_nmap = False
        self.app = PyopApplication()

    def tearDown(self):
        config.production = self._prod
        config.wildcard_response = self._wild
        config.fool_nmap = self._fool
        config.trust_proxy_headers = False

    def test_view_function(self):
        self.assertEqual(self.app(req("GET", "/helloThere")).text, "General Kenobi !")

    def test_view_static_file(self):
        r = self.app(req("GET", "/hello"))
        self.assertEqual(r.status, 200)
        self.assertIn("Hello There", r.text)

    def test_get_controller_introspection(self):
        r = self.app(req("GET", "/sum?a=3&b=4"))
        self.assertEqual(r.status, 200)
        self.assertIn("7", r.text)

    def test_post_custom_response(self):
        r = self.app(req("POST", "/sumCustom", b'{"a":1,"b":2,"c":3,"d":[4]}'))
        self.assertEqual(r.status, 200)
        self.assertIn("text/html", r.headers.get("content-type"))

    def test_404(self):
        self.assertEqual(self.app(req("GET", "/nope-xyz")).status, 404)

    def test_405_post_only_as_get(self):
        app = PyopApplication(views={}, get_routes={}, post_routes={"/only-post": lambda req: "x"})
        self.assertEqual(app(req("GET", "/only-post")).status, 405)

    def test_405_get_route_posted(self):
        app = PyopApplication(views={}, get_routes={"/only-get": lambda: "x"}, post_routes={})
        self.assertEqual(app(req("POST", "/only-get", b"")).status, 405)

    def test_501_unknown_method(self):
        self.assertEqual(self.app(req("TRACE", "/hello")).status, 501)

    def test_413_body_limit(self):
        old = config.max_body_size
        config.max_body_size = 4
        try:
            self.assertEqual(self.app(req("POST", "/sum", b"12345")).status, 413)
        finally:
            config.max_body_size = old

    def test_414_url(self):
        old = config.max_url_length
        config.max_url_length = 8
        try:
            self.assertEqual(self.app(req("GET", "/123456789")).status, 414)
        finally:
            config.max_url_length = old

    def test_431_headers(self):
        old = config.max_header_size
        config.max_header_size = 4
        try:
            self.assertEqual(self.app(req("GET", "/helloThere", headers=[("X-Big", "x" * 100)])).status, 431)
        finally:
            config.max_header_size = old

    def test_400_malformed(self):
        app = PyopApplication()
        bad = Request("POST", "/sum", b"", Headers(), object(), ("h", 0), "http", "x")
        self.assertEqual(app(bad).status, 400)

    def test_head_empty_body(self):
        r = self.app(req("HEAD", "/helloThere"))
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body, b"")

    def test_options_allow(self):
        r = self.app(req("OPTIONS", "/sum"))
        self.assertIn(r.status, (200, 204))
        self.assertTrue(r.headers.get("allow"))

    def test_trusted_proxy(self):
        config.trust_proxy_headers = True
        config.trusted_proxies = ["*"]
        r = req("GET", "/helloThere", headers=[("X-Forwarded-For", "9.9.9.9"), ("X-Forwarded-Proto", "https"), ("X-Forwarded-Host", "ex.com")])
        r.client = ("10.0.0.1", 80)
        self.app(r)
        self.assertEqual(r.client[0], "9.9.9.9")
        self.assertEqual(r.scheme, "https")
        self.assertEqual(r.host, "ex.com")

    def test_lifecycle_hooks_and_drain(self):
        calls = []
        self.app.add_startup_hook(lambda: calls.append("up"))
        self.app.add_shutdown_hook(lambda: calls.append("down"))
        self.app.startup()
        self.assertTrue(self.app.ready)
        self.app.shutdown()
        self.assertEqual(calls, ["up", "down"])
        self.assertEqual(self.app(req("GET", "/helloThere")).status, 503)

    def test_legacy_compat_flag(self):
        config.production = False
        config.fool_nmap = True
        app = PyopApplication()
        self.assertEqual(app(req("TRACE", "/hello")).status, 200)


class TestAdapters(unittest.TestCase):
    def setUp(self):
        self._prod = config.production
        config.production = True
        config.wildcard_response = False
        config.fool_nmap = False
        self.app = PyopApplication()

    def tearDown(self):
        config.production = self._prod

    def _environ(self, path="/helloThere", method="GET", body=b""):
        return {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "",
                "CONTENT_LENGTH": str(len(body)), "CONTENT_TYPE": "",
                "SERVER_NAME": "t", "SERVER_PORT": "80", "REMOTE_ADDR": "127.0.0.1",
                "REMOTE_PORT": "9", "wsgi.url_scheme": "http", "wsgi.input": io.BytesIO(body)}

    def test_wsgi_equivalence(self):
        captured = {}
        w = wsgi_mod.wsgi_app_factory(self.app)
        body = w(self._environ(), lambda s, h: captured.update(status=s, headers=h))
        self.assertIn("200", captured["status"])
        self.assertEqual(b"".join(body), b"General Kenobi !")

    def test_wsgi_404(self):
        captured = {}
        w = wsgi_mod.wsgi_app_factory(self.app)
        w(self._environ("/missing-xyz"), lambda s, h: captured.update(status=s))
        self.assertIn("404", captured["status"])

    def test_asgi_equivalence(self):
        a = asgi_mod.asgi_app_factory(self.app)
        scope = {"type": "http", "method": "GET", "path": "/helloThere", "query_string": b"",
                 "headers": [(b"host", b"t")], "scheme": "http", "client": ("127.0.0.1", 9)}
        msgs = [{"type": "http.request", "body": b"", "more_body": False}]
        sent = []

        async def receive():
            return msgs.pop(0) if msgs else {"type": "http.disconnect"}

        async def send(m):
            sent.append(m)

        asyncio.run(a(scope, receive, send))
        start = [m for m in sent if m["type"] == "http.response.start"][0]
        body = [m for m in sent if m["type"] == "http.response.body"][0]
        self.assertEqual(start["status"], 200)
        self.assertEqual(body["body"], b"General Kenobi !")

    def test_asgi_lifespan(self):
        a = asgi_mod.asgi_app_factory(self.app)
        seq = [{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}]
        sent = []

        async def receive():
            return seq.pop(0)

        async def send(m):
            sent.append(m)
            if len(sent) >= 2:
                raise StopAsyncIteration

        async def run():
            try:
                await a({"type": "lifespan"}, receive, send)
            except StopAsyncIteration:
                pass

        asyncio.run(run())
        self.assertEqual(sent[0]["type"], "lifespan.startup.complete")
        self.assertEqual(sent[1]["type"], "lifespan.shutdown.complete")


class TestViewsDirFallback(unittest.TestCase):
    """Regression: a bare file in config.views (e.g. mvc/views/index.py)
    requested as /index.py must materialize; static/ takes precedence."""

    def setUp(self):
        import tempfile
        self._prod = config.production
        self._wild = config.wildcard_response
        config.production = True
        config.wildcard_response = False
        self.tmp = tempfile.mkdtemp()
        self.sdir = self.tmp + "/static"
        self.vdir = self.tmp + "/views"
        os.makedirs(self.sdir)
        os.makedirs(self.vdir)

    def tearDown(self):
        config.production = self._prod
        config.wildcard_response = self._wild

    def _get(self, app, path):
        return app(req("GET", path))

    def test_views_index_py_served(self):
        with open(os.path.join(self.vdir, "index.py"), "w") as f:
            f.write("def main():\n    return 'views-index-ok'\n")
        app = PyopApplication(views={}, get_routes={}, post_routes={},
                              static_dir=self.sdir, views_dir=self.vdir)
        r = self._get(app, "/index.py")
        self.assertEqual(r.status, 200)
        self.assertIn("views-index-ok", r.text)

    def test_static_takes_precedence_over_views(self):
        with open(os.path.join(self.vdir, "index.py"), "w") as f:
            f.write("def main():\n    return 'views'\n")
        with open(os.path.join(self.sdir, "index.py"), "w") as f:
            f.write("def main():\n    return 'static'\n")
        app = PyopApplication(views={}, get_routes={}, post_routes={},
                              static_dir=self.sdir, views_dir=self.vdir)
        r = self._get(app, "/index.py")
        self.assertEqual(r.status, 200)
        self.assertIn("static", r.text)

    def test_view_py_using_dunder_file_renders(self):
        # Regression: exec sandbox must provide __file__; the sample
        # static/index.py uses it and previously came back 500.
        with open(os.path.join(self.sdir, "whoami.py"), "w") as f:
            f.write("def main():\n    return 'path=' + __file__\n")
        app = PyopApplication(views={}, get_routes={}, post_routes={},
                              static_dir=self.sdir, views_dir=self.vdir)
        r = self._get(app, "/whoami.py")
        self.assertEqual(r.status, 200)
        self.assertIn("whoami.py", r.text)

    def test_pyhtml_using_dunder_file_renders(self):
        with open(os.path.join(self.sdir, "whoami.pyhtml"), "w") as f:
            f.write("<html><body><py>\nreturn 'path=' + __file__\n</py></body></html>")
        app = PyopApplication(views={}, get_routes={}, post_routes={},
                              static_dir=self.sdir, views_dir=self.vdir)
        r = self._get(app, "/whoami.pyhtml")
        self.assertEqual(r.status, 200)
        self.assertIn("whoami.pyhtml", r.text)


class TestDevServerLifecycle(unittest.TestCase):
    """Regression: Ctrl+C must stop the server. shutdown() blocks until the
    serve_forever() loop exits, so it must run in a different thread than
    serve_forever() itself (the old handler called it inline and hung)."""

    def test_threaded_shutdown_returns(self):
        import threading
        import time
        import urllib.request
        from main import ThreadedPyOPServer, PyOPSever
        srv = ThreadedPyOPServer(("127.0.0.1", 0), PyOPSever)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            time.sleep(0.2)
            port = srv.server_address[1]
            with urllib.request.urlopen("http://127.0.0.1:%d/helloThere" % port, timeout=5) as r:
                self.assertEqual(r.status, 200)
            stopper = threading.Thread(target=srv.shutdown, daemon=True)
            stopper.start()
            stopper.join(timeout=5)
            t.join(timeout=5)
            self.assertFalse(t.is_alive(), "serve_forever did not exit after shutdown()")
        finally:
            try:
                srv.server_close()
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
