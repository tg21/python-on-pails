# Protocol and Serving Plan

## Objective

Introduce production-server contracts without abandoning the dependency-free development server or existing MVC applications.

## Design

- Define protocol-neutral `Request` and `Response` objects containing method, URL, path, query, headers, cookies, body, client metadata, status, response headers, and body/iterator data.
- Add a WSGI adapter conforming to PEP 3333 for Gunicorn, uWSGI, Waitress, and similar servers.
- Add an ASGI HTTP adapter conforming to the ASGI specification for Uvicorn, Hypercorn, and similar servers.
- Keep `python3 main.py` as a development/compatibility server implemented over the same application dispatch layer.
- Adapt existing callable routes, controller files, views, input models, and custom response dictionaries into the new contract.

## HTTP behavior

- Handle all standard HTTP methods explicitly and return correct 404, 405, 400, 413, 414, 431, 500, and 501 responses.
- Normalize headers case-insensitively while preserving repeated headers such as `Set-Cookie`.
- Support request and response bodies as bytes; expose text and JSON helpers at the application layer.
- Set accurate content length when buffering is possible and support streaming iterables where the serving protocol permits it.
- Delegate HTTP/2, TLS, connection pooling, and certificate management to the production server or reverse proxy.
- Define trusted-proxy configuration for forwarded host, scheme, client IP, and port headers.

## Lifecycle and operations

- Add startup, readiness, shutdown, and drain hooks.
- Add configurable request, header, body, and idle timeouts.
- Ensure shutdown stops accepting new work, drains active requests, and exits after a deadline.
- Document Nginx, Caddy, Cloudflare, Gunicorn, Uvicorn, and Hypercorn deployment patterns without requiring them as runtime dependencies.

## Compatibility and acceptance

- Existing sample routes and views produce equivalent responses through the legacy server, WSGI, and ASGI entry points.
- A minimal WSGI and ASGI application can be imported without third-party packages.
- Malformed requests and unsupported methods receive standards-based responses instead of the current nmap-specific success response when production mode is enabled.
- Legacy behavior remains available behind an explicit compatibility setting.

