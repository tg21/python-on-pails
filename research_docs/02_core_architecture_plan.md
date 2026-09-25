# Core Architecture Plan

## Objective

Replace dictionary-only dispatch with a maintainable application core while preserving the current MVC conventions.

## Routing

- Introduce a `Router` with method-aware route registration and matching.
- Support static segments, typed parameters, optional query values, and route parameter conversion.
- Use deterministic precedence: static segments before typed parameters, typed parameters before unconstrained parameters, then registration order.
- Return explicit 404 and 405 results, including an `Allow` header for known methods.
- Keep legacy `getRoutes` and `postRoutes` dictionaries usable through a compatibility registration path.
- Prevent duplicate and ambiguous routes at registration time with useful configuration errors.

## Middleware

- Add an onion-style middleware pipeline with request entry, downstream invocation, response exit, and exception handling.
- Middleware must be able to short-circuit requests, mutate responses, attach request state, and observe timing/status data.
- Provide built-in extension points for authentication, CORS, security headers, request IDs, access logging, sessions, rate limiting, and exception handling.
- Ensure middleware ordering is explicit and tested.

## Request and response behavior

- Define one response normalization path for bytes, strings, JSON-compatible values, HTML, custom response dictionaries, and streaming iterables.
- Preserve current default MIME behavior for legacy controllers and views.
- Separate route matching, request parsing, controller invocation, serialization, and error handling into independent components.
- Keep failed legacy type casts returning `None`; offer strict validation as an opt-in API.
- Make static file lookup root-confined and resistant to path traversal.

## Compatibility

- Preserve bare view callables with no arguments.
- Preserve controller callables, controller-file subprocess execution, `PyopReq`, input model classes, and `customResponse` behavior.
- Introduce deprecation warnings only for behavior that cannot safely coexist with the new application API.

## Acceptance tests

- Static, typed, overlapping, query-bearing, and method-specific routes match predictably.
- Middleware can add headers, replace responses, short-circuit requests, and handle exceptions.
- Legacy route tables dispatch through the new router without changing existing test expectations.
- Static-file traversal attempts fail safely.

