# Common Infrastructure

This document describes the common infrastructure for request ID tracing in Backend.AI.

## Context Propagation

Request ID is propagated through async call chains using Python's `contextvars.ContextVar`.

**Why ContextVar?**
- Async-safe: Properly propagates across `await` boundaries
- Task isolation: Each asyncio Task inherits but can override the context
- Zero overhead: Native Python mechanism

## Core Utilities

| Utility | Description |
|---------|-------------|
| `current_request_id()` | Returns the current request ID from context |
| `new_request_id()` | Generates a new UUID |
| `bind_request_id(id)` | Context manager to temporarily bind a request ID |
| `@with_request_id_context` | Decorator that auto-generates request ID if not present |

### `@with_request_id_context` Decorator

Used for non-HTTP entry points where request ID needs to be auto-generated:
- Background tasks
- Message queue event handlers
- Scheduled jobs

## HTTP Middleware

`request_id_middleware` for aiohttp:

1. Extract `X-Backend-Request-ID` from request header
2. Generate new UUID if not present
3. Bind to context for the request duration
4. Echo in response header

## RPC Headers Model

For RPC communication where headers cannot be sent separately (e.g., Callosum):

```python
class RPCHeaders(BaseModel):
    request_id: str | None = None
    # Extensible for future tracing needs
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
```

Headers are embedded in the request/response body:

```python
# Request
{"headers": {"request_id": "..."}, "args": [...], "kwargs": {...}}

# Response
{"headers": {"request_id": "..."}, "result": {...}}
```

## Message Queue Integration

Events include request ID in metadata for causality tracking:

```python
class MessageMetadata(BaseModel):
    request_id: str | None = None
    timestamp: datetime
    source: str
```
