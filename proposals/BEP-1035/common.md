# Common Infrastructure

This document describes the common infrastructure for request ID tracing in Backend.AI.

## Context Variables

The request ID is propagated through async call chains using Python's `contextvars`:

```python
# ai/backend/common/logging_utils.py
from contextvars import ContextVar

_request_id_var: ContextVar[str | None] = ContextVar("_request_id_var", default=None)
```

### Why ContextVar?

- **Async-safe**: Properly propagates across `await` boundaries
- **Task isolation**: Each asyncio Task inherits but can override the context
- **Zero overhead**: Native Python mechanism, no external dependencies

## Core Utilities

### `current_request_id()`

Retrieves the current request ID from context:

```python
def current_request_id() -> str | None:
    """
    Returns the current request ID if set, otherwise None.
    """
    return _request_id_var.get()
```

### `new_request_id()`

Generates a new request ID:

```python
import uuid

def new_request_id() -> str:
    """
    Generates a new request ID in the standard format.
    Format: "req-{uuid4}"
    """
    return f"req-{uuid.uuid4()}"
```

### `bind_request_id()`

Context manager for temporarily binding a request ID:

```python
from contextlib import contextmanager

@contextmanager
def bind_request_id(request_id: str | None) -> Iterator[None]:
    """
    Binds a request ID to the current context.
    Use this when making outbound calls to propagate the request ID.
    
    Example:
        with bind_request_id(current_request_id()):
            await make_rpc_call(...)
    """
    token = _request_id_var.set(request_id)
    try:
        yield
    finally:
        _request_id_var.reset(token)
```

### `with_request_id()`

Async context manager variant:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def with_request_id(request_id: str | None) -> AsyncIterator[None]:
    """
    Async context manager for binding request ID.
    Useful when the binding scope includes async operations.
    """
    token = _request_id_var.set(request_id)
    try:
        yield
    finally:
        _request_id_var.reset(token)
```

### `receive_request_id()`

Extracts and binds request ID from incoming requests:

```python
def receive_request_id(headers: Mapping[str, Any]) -> str:
    """
    Extracts request_id from headers, generates new one if not present,
    and binds it to the current context.
    
    Returns the active request_id.
    """
    request_id = headers.get("request_id") or new_request_id()
    _request_id_var.set(request_id)
    return request_id
```

### `@with_request_id_context` Decorator

Ensures a request ID exists for non-HTTP entry points (background tasks, event handlers, etc.):

```python
from functools import wraps

def with_request_id_context(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """
    Decorator that ensures a request ID is present in the context.
    If no request ID exists, generates a new one automatically.
    
    Use this for:
    - Background task handlers
    - Message queue event handlers
    - Scheduled jobs
    - Any async entry point that doesn't go through HTTP middleware
    
    Example:
        @with_request_id_context
        async def handle_background_task():
            # request_id is guaranteed to be set
            log.info("Processing task")
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        if current_request_id() is None:
            _request_id_var.set(new_request_id())
        return await func(*args, **kwargs)
    return wrapper
```

## HTTP Middleware

### `request_id_middleware`

Standard aiohttp middleware for HTTP servers:

```python
from aiohttp import web

@web.middleware
async def request_id_middleware(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    """
    Middleware that extracts or generates request ID for incoming HTTP requests.
    
    Behavior:
    1. Check for X-Backend-Request-ID header in incoming request
    2. If not present, generate a new request ID
    3. Bind the request ID to the context
    4. Add X-Backend-Request-ID header to response
    """
    # Extract from header or generate new
    request_id = request.headers.get("X-Backend-Request-ID") or new_request_id()
    
    # Bind to context
    _request_id_var.set(request_id)
    
    # Store in request for handler access
    request["request_id"] = request_id
    
    try:
        response = await handler(request)
        # Echo request ID in response
        response.headers["X-Backend-Request-ID"] = request_id
        return response
    except Exception:
        raise
```

### Usage in aiohttp Application

```python
from aiohttp import web
from ai.backend.common.logging_utils import request_id_middleware

app = web.Application(middlewares=[
    request_id_middleware,
    # ... other middlewares
])
```

## RPC Headers Model

For RPC communication (used by Agent), headers are embedded in the request body:

```python
from pydantic import BaseModel

class RPCHeaders(BaseModel):
    """
    Headers for RPC requests and responses.
    
    Designed for extensibility - additional fields can be added
    for future tracing needs (correlation_id, trace_id, span_id).
    """
    request_id: str | None = None
    correlation_id: str | None = None  # Future: for grouping related requests
    trace_id: str | None = None        # Future: OpenTelemetry trace ID
    span_id: str | None = None         # Future: OpenTelemetry span ID
    
    class Config:
        extra = "allow"  # Allow additional fields for forward compatibility
```

### Serialization

```python
# Sender side
headers = RPCHeaders(request_id=current_request_id())
request_body = {
    "headers": headers.model_dump(exclude_none=True),
    "args": args,
    "kwargs": kwargs,
}

# Receiver side
headers = RPCHeaders.model_validate(request_body.get("headers", {}))
receive_request_id({"request_id": headers.request_id})
```

## Message Queue Integration

For event-driven communication via message queues:

```python
from ai.backend.common.events import EventProducer

class MessageMetadata(BaseModel):
    """
    Metadata attached to message queue events.
    """
    request_id: str | None = None
    timestamp: datetime
    source: str

# When producing events
async def produce_event(event: Event) -> None:
    metadata = MessageMetadata(
        request_id=current_request_id(),
        timestamp=datetime.now(UTC),
        source="manager",
    )
    await producer.send(event, metadata=metadata)

# When consuming events
@with_request_id_context
async def handle_event(event: Event, metadata: MessageMetadata) -> None:
    if metadata.request_id:
        _request_id_var.set(metadata.request_id)
    # Process event with request_id in context
```

## Logging Integration

### `with_log_context_fields`

Request ID is automatically included in structured logs:

```python
from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

# Request ID is automatically included via the logging context
# when using BraceStyleAdapter with proper configuration

@with_log_context_fields(request_id=current_request_id)
async def process_request():
    log.info("Processing request")  # Includes request_id in log record
```

### Log Output Format

With request ID tracing, log entries include the request ID:

```json
{
    "timestamp": "2025-01-21T10:30:00Z",
    "level": "INFO",
    "logger": "ai.backend.manager.api.session",
    "message": "Session created",
    "request_id": "req-550e8400-e29b-41d4-a716-446655440000",
    "session_id": "sess-abc123"
}
```

## Usage Patterns

### Pattern 1: HTTP Handler

```python
async def create_session(request: web.Request) -> web.Response:
    # request_id already bound by middleware
    log.info("Creating session")
    
    # Propagate to Agent RPC
    async with bind_request_id(current_request_id()):
        await agent_rpc.create_kernel(...)
    
    return web.json_response({"status": "ok"})
```

### Pattern 2: Background Task

```python
@with_request_id_context
async def cleanup_expired_sessions() -> None:
    """Background task that runs periodically."""
    log.info("Starting cleanup")  # Has request_id for tracing
    
    for session in expired_sessions:
        await terminate_session(session)
```

### Pattern 3: Event Handler

```python
async def handle_kernel_terminated(event: KernelTerminatedEvent) -> None:
    # Restore request_id from event metadata
    if event.metadata.request_id:
        with bind_request_id(event.metadata.request_id):
            await cleanup_kernel_resources(event.kernel_id)
```

### Pattern 4: Cross-Service HTTP Call

```python
async def call_storage_proxy(operation: str, params: dict) -> dict:
    request_id = current_request_id()
    headers = {"X-Backend-Request-ID": request_id} if request_id else {}
    
    async with session.post(
        f"{storage_url}/{operation}",
        headers=headers,
        json=params,
    ) as response:
        return await response.json()
```

## Implementation Checklist

- [ ] `_request_id_var` ContextVar
- [ ] `current_request_id()` function
- [ ] `new_request_id()` function  
- [ ] `bind_request_id()` context manager
- [ ] `@with_request_id_context` decorator
- [ ] `request_id_middleware` for aiohttp
- [ ] `RPCHeaders` Pydantic model
- [ ] `receive_request_id()` utility
- [ ] `with_request_id()` async context manager
