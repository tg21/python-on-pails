## Architecture (entry: `main.py`)
- `main.py:run()` → `ThreadedPyOPServer` + `PyOPSever(BaseHTTPRequestHandler)`. Only `GET`/`POST` via `do_GET`/`do_POST` → `GETPOST()`. Other methods return `config.fool_nmap_content` (200) when `config.fool_nmap=True`.
- Route precedence in `GETPOST()`: `mvc/views/views.py:views` first → `getRoutes`/`postRoutes` in `mvc/controllers/routes.py` → static-file fallback under `config.static` (`mvc/views/static/`). All paths in `settings.py` are relative dir names with trailing slash.
- Behaviour flags live in `server/settings.py:config` (`wildcard_response`, `fool_nmap`, `enableTLS`, `logging=False` — errors print only if logging on).
