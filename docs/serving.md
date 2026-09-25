# Serving: dev server, WSGI, ASGI

All entry points share `server/application.py:PyopApplication`, which maps
protocol-neutral `server/http.py:Request` -> `Response`. Business logic
(views, controllers, input models, `customResponse`) lives only in that layer.

## Entry points (no third-party runtime deps)

- Dev/compat: `python3 main.py` (`main.py:get_application()` + `ThreadedPyOPServer`).
- WSGI (PEP 3333): `server.wsgi:application` / `server.wsgi:wsgi_app_factory(app)`.
- ASGI (HTTP + lifespan): `server.asgi:application` / `server.asgi:asgi_app_factory(app)`.

## Production vs legacy

`server/settings.py:config`:

- `production = False` (default) preserves legacy dev behaviour: unknown methods
  return `fool_nmap_content` (200) when `fool_nmap=True`; missing files return
  `500 FileNotFoundError` when `wildcard_response=True`.
- `production = True` (+ `wildcard_response=False`, `fool_nmap=False`) returns
  standards-based `400/404/405/413/414/431/500/501`. `legacy_compat=True` marks
  the explicit opt-out back to legacy.

## HTTP behaviour

- Methods `GET/HEAD/POST/PUT/PATCH/DELETE/OPTIONS` are explicit. Unknown verbs
  -> `501` (production) or `fool_nmap` 200 (legacy). `OPTIONS` returns `Allow`;
  `HEAD` returns headers with empty body. Wrong-method known paths -> `405+Allow`.
- `server/http.py:Headers` is case-insensitive and preserves repeats
  (`Set-Cookie`, `get_all`). Bodies are `bytes`; `Request.text/.json()` and
  `Response.json_body/text_body` are app-layer helpers. Bufferable responses get
  accurate `Content-Length`; generator bodies stream (buffered by WSGI/dev).
- Limits: `max_body_size` -> 413, `max_url_length` -> 414,
  `max_header_size` -> 431. Malformed bodies -> 400.
- TLS/HTTP-2/pooling/certs are delegated to the production server or proxy.

## Static / views files

- Explicit `views` dict entries that are strings resolve under `config.static`
  (`mvc/views/static/`), e.g. `'/hello': 'welcome.html'` -> `static/welcome.html`.
- Any other path falls back to a file lookup: `config.static` first, then
  `config.views` (`mvc/views/`). So `/index.py` materializes
  `mvc/views/static/index.py` if present, else `mvc/views/index.py`. Static
  takes precedence; directory traversal outside both roots -> `403`.
  `.py` runs file-level `main()` with no args, `.pyhtml` executes `<py>` blocks.
  Both execute with `__file__` set to the source path (and `__name__ ==
  '__main__'`), so view code may reference its own location.

## Trusted proxy

Behind Nginx/Caddy/Cloudflare set:

```
config.trust_proxy_headers = True
config.trusted_proxies = ["10.0.0.1"]  # or ["*"] to trust the immediate hop
```

Honours `X-Forwarded-For` (client IP), `X-Forwarded-Proto/Scheme`,
`X-Forwarded-Host`, `X-Forwarded-Port`. Keep `False` (default) when directly
exposed so clients cannot spoof.

## Lifecycle / timeouts

- `PyopApplication.startup()/shutdown()`, `add_startup_hook(fn)`,
  `add_shutdown_hook(fn)`, `ready` flag; `config.on_startup/on_shutdown` lists.
  ASGI lifespan drives the same hooks; `main.py:run()` drains on
  SIGTERM/SIGINT and exits after `shutdown_drain_seconds`.
- `request_timeout/header_timeout/body_timeout/idle_timeout` are configurable;
  the dev server applies `request_timeout`; production servers own socket
  timeouts (documented, not reimplemented).

## Deployment patterns (servers not required as deps)

- Gunicorn: `gunicorn server.wsgi:application --workers 3 --timeout 30`
- uWSGI: `uwsgi --http :8000 --wsgi-file server/wsgi.py --callable application`
- Waitress: `waitress-serve --listen=0.0.0.0:8000 server.wsgi:application`
- Uvicorn: `uvicorn server.asgi:application --workers 3`
- Hypercorn: `hypercorn server.asgi:application`
- Nginx/Caddy/Cloudflare terminate TLS and forward `X-Forwarded-*`; set
  `trust_proxy_headers=True` + worker/timeout/body-limit values to match proxy.
