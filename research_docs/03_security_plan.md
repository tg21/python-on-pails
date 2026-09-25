# Security Plan

## Objective

Provide a secure web baseline in the framework core while keeping external stores and infrastructure integrations optional.

## Secure defaults

- Add configurable `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options`, frame protection, `Referrer-Policy`, and `Permissions-Policy` headers.
- Make production error responses generic and keep tracebacks in logs only.
- Add correlation/request IDs and redact authorization headers, cookies, passwords, tokens, and configurable sensitive fields.
- Set secure, HttpOnly, SameSite, and path/domain cookie attributes through configuration.

## Sessions and CSRF

- Define a `SessionStore` interface with load, save, rotate, and invalidate operations.
- Provide signed, tamper-evident cookie sessions using standard-library cryptography primitives and key rotation.
- Define optional adapters for Redis, Memcached, and database-backed sessions.
- Add CSRF token generation and validation for state-changing methods, with configurable exemptions for APIs and webhooks.
- Ensure session and CSRF secrets are required or clearly unsafe in development mode.

## Input and abuse controls

- Add configurable maximum body size, header size, URL length, upload size, and parsing depth.
- Validate and normalize headers and reject request smuggling or ambiguous framing conditions.
- Add a `RateLimiter` interface keyed by client IP, authenticated identity, API key, route, or combinations thereof.
- Provide an in-memory limiter for single-process deployments and document distributed adapters for multi-worker deployments.
- Use parameterized database operations through repository adapters; do not claim that HTTP validation alone prevents SQL injection.

## Output and templates

- HTML templates must escape interpolated values by default.
- Raw HTML must require an explicit safe-output operation.
- JSON serialization must reject or safely encode unsupported values rather than leaking object internals.
- Static files must be confined to configured roots and must not follow unsafe path escapes.

## Acceptance tests

- Security headers appear only according to configured policy and do not duplicate existing values incorrectly.
- Tampered sessions fail validation and rotated keys continue accepting configured previous keys.
- CSRF-protected requests reject missing or invalid tokens.
- Rate limits return 429 with useful retry metadata.
- Production errors contain no traceback, filesystem path, secret, or request payload leakage.

