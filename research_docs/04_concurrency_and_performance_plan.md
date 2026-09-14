# Concurrency and Performance Plan

## Objective

Make concurrency explicit and safe for both synchronous and asynchronous applications.

## Execution model

- WSGI applications execute synchronous handlers according to the hosting server's worker model.
- ASGI applications support native async handlers and awaitable middleware.
- Synchronous handlers invoked from ASGI run in a bounded executor so they cannot block the event loop indefinitely.
- Async handlers are rejected or adapted clearly when used through the synchronous WSGI path.
- Preserve the current threaded server as a development option, with documented limits.

## Lifecycle and resource management

- Define application startup, per-worker startup, request, shutdown, and drain hooks.
- Add timeout and cancellation propagation for request handling and downstream calls.
- Define bounded queues and backpressure behavior for streaming and executor work.
- Provide resource registration hooks for database pools, HTTP clients, caches, and other external services.
- Ensure resources close during graceful shutdown and that worker timeouts produce safe responses/logs.

## Performance work

- Use an efficient route structure such as a radix/tree router while keeping route behavior deterministic.
- Avoid repeated parsing, serialization, and filesystem-stat work within one request.
- Support conditional static responses and configurable cache headers.
- Add benchmarks for routing, middleware, parsing, serialization, static files, and concurrent workloads.
- Track latency percentiles, active requests, queue depth, error counts, and response sizes.

## Acceptance tests

- Concurrent requests do not corrupt request state or shared configuration.
- A blocking synchronous handler does not stall unrelated ASGI requests beyond executor capacity.
- Timeouts cancel or terminate work according to documented guarantees.
- Shutdown drains active requests and closes registered resources within the configured deadline.

