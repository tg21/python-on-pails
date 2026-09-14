# Testing, CI, and Deployment Plan

## Objective

Establish confidence in protocol compatibility, security, performance, and upgrade safety.

## Test layers

- Preserve and extend current request-parsing unit tests, including silent failed-cast compatibility cases.
- Add unit tests for routing, precedence, conversion, middleware, serialization, configuration, cookies, sessions, CSRF, rate limiting, security headers, and error handling.
- Add WSGI and ASGI integration tests using dependency-free harnesses.
- Add live development-server tests for supported methods, malformed requests, limits, keep-alive behavior, and shutdown.
- Add regression tests for legacy views, controller files, subprocess execution, custom responses, and static-file behavior.
- Add concurrency and timeout tests with deterministic synchronization rather than sleep-based timing where possible.
- Add security tests for traversal, header injection, request smuggling conditions, session tampering, CSRF failures, and information leakage.

## Quality gates

- Target more than 90% coverage for framework code, with documented exclusions.
- Run tests on all supported Python versions.
- Add reproducible benchmark commands and track regressions separately from correctness tests.
- Add static checks that use only approved development dependencies.
- Fail CI on broken compatibility tests, security regressions, or invalid packaging/deployment examples.

## Deployment artifacts

- Document WSGI and ASGI server commands.
- Add optional Docker and reverse-proxy examples with non-root execution, health checks, signal forwarding, and configurable ports.
- Document TLS termination, forwarded headers, body limits, worker counts, timeouts, logging, and secret injection.
- Add release notes, deprecation policy, migration guides, and rollback guidance.

## Acceptance criteria

- Existing tests pass unchanged.
- New protocol, security, and compatibility tests pass in CI.
- A sample application can be deployed behind a reverse proxy using either WSGI or ASGI.
- Deployment documentation does not imply that the built-in development server is suitable for internet-facing production traffic.

