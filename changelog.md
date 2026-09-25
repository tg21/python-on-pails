## 2026-09-14

- Added detailed production-readiness plans covering protocol adapters, core architecture, security, concurrency, observability/configuration/data integrations, and testing/deployment.

## 2026-09-15 - Protocol and serving plan (research_docs/01)
- Added protocol-neutral Request/Response/Headers (server/http.py) with case-insensitive multi-value headers, cookies, bytes bodies, text/JSON helpers, streaming iterables, accurate content-length.
- Added shared dispatch PyopApplication (server/application.py) adapting views, callable/file controllers, input models, customResponse; explicit GET/HEAD/POST/PUT/PATCH/DELETE/OPTIONS with 404/405+Allow/400/413/414/431/500/501 in production mode, legacy fool_nmap/wildcard behind production=False.
- Added WSGI PEP 3333 (server/wsgi.py) and ASGI HTTP+lifespan (server/asgi.py) adapters, stdlib-only importable.
- Rewired main.py dev server onto the same dispatch layer; added HEAD/PUT/PATCH/DELETE/OPTIONS, 414 guard, graceful SIGTERM/SIGINT drain with shutdown_drain_seconds.
- Extended server/settings.py: production, legacy_compat, body/url/header limits, request/header/body/idle timeouts, trust_proxy_headers/trusted_proxies, on_startup/on_shutdown hooks.
- Tests: tests/test_protocol_serving.py (26 tests incl. legacy test) covers contracts, routing equivalence, error codes, proxy, lifecycle/drain, WSGI/ASGI incl. lifespan.
- Docs: docs/serving.md + architecture note; AGENTS.md docs index updated.

## 2026-09-16 - Ctrl+C hang + views/index.py 404 fix
- Fixed dev-server shutdown hang: signal handler called httpd.shutdown() in the same thread running serve_forever(), which deadlocks per BaseServer docs. Handler now only flips state, runs app.shutdown(), and calls httpd.shutdown() from a daemon thread; drain deadline forces server_close(), second Ctrl+C force-exits, KeyboardInterrupt fallback added, server_close() + "Server stopped." on exit.
- Fixed /index.py 404: static fallback only searched config.static (mvc/views/static/), so a bare mvc/views/index.py never materialized. Fallback now tries static/ first, then config.views (mvc/views/index.py); static wins, traversal outside both roots is 403; _allow_for and _serve_file guard updated the same way.
- Tests: TestViewsDirFallback (views-only serve, static precedence) and TestDevServerLifecycle (ephemeral live GET + threaded shutdown returns) added; 29 tests pass.
- Docs: docs/serving.md static/views resolution section.

## 2026-09-16 - static/index.py 500 fix (__file__ missing in exec sandbox)
- Root cause of /index.py not rendering: file was correctly resolved in mvc/views/static/, but _run_python_file() exec'd it with an empty globals dict, so the sample's f-string using __file__ raised NameError -> 500 Internal Server Error.
- Fixed server/responseHandler.py: _run_python_file() now execs with {'__file__': path, '__name__': '__main__'} globals; same for <py> blocks in _processPyHtml()/MyHTMLParser (parser now carries the source path, default '<pyhtml>').
- Tests: view .py and .pyhtml referencing __file__ render 200; 31 tests pass.
- Docs: docs/serving.md notes __file__/__name__ availability in view execution.
