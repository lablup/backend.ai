# App-Proxy Components

App-Proxy consists of two components:
- **Coordinator**: Routes requests and manages session mappings
- **Worker**: Handles actual proxying to application endpoints

This document describes the current state and proposed standardization of request ID tracing for both components.

## Architecture Overview

```
Client                    Coordinator                   Worker                    App
   │                           │                           │                       │
   │  HTTP Request             │                           │                       │
   │  X-Backend-Request-ID: 550e8400...    │                           │                       │
   ├──────────────────────────▶│                           │                       │
   │                           │                           │                       │
   │                           │  Route to Worker          │                       │
   │                           │  (with request context)   │                       │
   │                           ├──────────────────────────▶│                       │
   │                           │                           │                       │
   │                           │                           │  Proxy to App         │
   │                           │                           ├──────────────────────▶│
   │                           │                           │                       │
   │                           │                           │◀──────────────────────┤
   │                           │◀──────────────────────────┤                       │
   │◀──────────────────────────┤                           │                       │
```

## Current State

App-Proxy (Coordinator and Worker) does not have request_id support:
- No `request_id_middleware`
- No request_id propagation between Coordinator and Worker
- No request_id in WebSocket/SSE connections

## Proposed Changes

### 1. Apply Standard Middleware

Replace custom implementations with `request_id_middleware`:

```python
# ai/backend/appproxy/coordinator/server.py
from ai.backend.common.logging_utils import request_id_middleware

app = web.Application(middlewares=[
    request_id_middleware,
    # ... other middlewares
])
```

```python
# ai/backend/appproxy/worker/server.py
from ai.backend.common.logging_utils import request_id_middleware

app = web.Application(middlewares=[
    request_id_middleware,
    # ... other middlewares
])
```

### 2. Explicit Propagation in Coordinator → Worker

Coordinator explicitly includes request ID when forwarding:

```python
async def forward_to_worker(
    worker_url: str,
    request: web.Request,
) -> web.Response:
    request_id = current_request_id()
    
    # Build headers with explicit request_id
    headers = dict(request.headers)
    if request_id:
        headers["X-Backend-Request-ID"] = request_id
    
    async with session.request(
        request.method,
        worker_url,
        headers=headers,
        data=await request.read(),
    ) as response:
        # Echo request_id in response
        resp_headers = dict(response.headers)
        resp_headers["X-Backend-Request-ID"] = request_id or ""
        
        return web.Response(
            status=response.status,
            headers=resp_headers,
            body=await response.read(),
        )
```

### 3. Session Context Preservation

For long-lived connections, preserve the initial request_id:

```python
async def websocket_handler(request: web.Request, ws: web.WebSocketResponse) -> None:
    # Capture request_id at connection establishment
    session_request_id = current_request_id()
    
    log.info("WebSocket connection established", session_id=request["session_id"])
    
    async for msg in ws:
        # Each message processing uses the session's request_id
        with bind_request_id(session_request_id):
            await process_message(msg)
            log.debug("Processed message", msg_type=msg.type)
```

Alternative: Per-message request IDs for high-cardinality tracing:

```python
async def websocket_handler(request: web.Request, ws: web.WebSocketResponse) -> None:
    session_request_id = current_request_id()
    
    async for msg in ws:
        # Generate per-message request_id linked to session
        msg_request_id = f"{session_request_id}-msg-{uuid.uuid4().hex[:8]}"
        
        with bind_request_id(msg_request_id):
            await process_message(msg)
```

## Coordinator-Specific Changes

### Entry Points

```python
# All HTTP handlers automatically get request_id via middleware

@routes.post("/api/v1/route")
async def route_request(request: web.Request) -> web.Response:
    # request_id already bound by middleware
    log.info("Routing request", path=request.path)
    
    worker = await select_worker(request)
    return await forward_to_worker(worker.url, request)
```

### Internal State Management

Session registry should track originating request_id:

```python
@dataclass
class SessionInfo:
    session_id: str
    worker_id: str
    created_at: datetime
    origin_request_id: str | None  # Track original request for debugging
```

## Worker-Specific Changes

### Entry Points

```python
# All HTTP handlers automatically get request_id via middleware

@routes.get("/{path:.*}")
async def proxy_request(request: web.Request) -> web.Response:
    # request_id already bound by middleware
    session = await get_session(request)
    
    log.info("Proxying request", session_id=session.id, path=request.path)
    
    return await proxy_to_app(session, request)
```

### Proxy to Application

When proxying to the actual application:

```python
async def proxy_to_app(
    session: Session,
    request: web.Request,
) -> web.Response:
    request_id = current_request_id()
    
    # Include request_id in proxied request (if app supports it)
    headers = dict(request.headers)
    headers["X-Backend-Request-ID"] = request_id or ""
    
    async with session.http.request(
        request.method,
        session.app_endpoint + request.path,
        headers=headers,
        data=await request.read(),
    ) as response:
        return web.Response(
            status=response.status,
            body=await response.read(),
        )
```

## Request Flow with Standardization

### HTTP Request

```
Client                    Coordinator                   Worker                    App
   │                           │                           │                       │
   │  POST /apps/jupyter       │                           │                       │
   │  X-Backend-Request-ID: 550e8400...    │                           │                       │
   ├──────────────────────────▶│                           │                       │
   │                           │                           │                       │
   │     middleware binds      │                           │                       │
   │     550e8400...               │                           │                       │
   │                           │                           │                       │
   │                           │  POST /proxy              │                       │
   │                           │  X-Backend-Request-ID: 550e8400...    │                       │
   │                           ├──────────────────────────▶│                       │
   │                           │                           │                       │
   │                           │     middleware binds      │                       │
   │                           │     550e8400...               │                       │
   │                           │                           │                       │
   │                           │                           │  GET /api             │
   │                           │                           │  X-Backend-Request-ID:        │
   │                           │                           │    550e8400...            │
   │                           │                           ├──────────────────────▶│
   │                           │                           │                       │
   │                           │                           │◀──────────────────────┤
   │                           │                           │                       │
   │                           │  X-Backend-Request-ID:    │                       │
   │                           │    550e8400...                │                       │
   │                           │◀──────────────────────────┤                       │
   │                           │                           │                       │
   │  X-Backend-Request-ID:    │                           │                       │
   │    550e8400...                │                           │                       │
   │◀──────────────────────────┤                           │                       │
```

### WebSocket Connection

```
Client                    Coordinator                   Worker
   │                           │                           │
   │  WS Upgrade               │                           │
   │  X-Backend-Request-ID: 6ba7b810...    │                           │
   ├──────────────────────────▶│                           │
   │                           │                           │
   │     binds 6ba7b810...         │                           │
   │     stores in session     │                           │
   │                           │                           │
   │  WS Established           │                           │
   │◀──────────────────────────┤                           │
   │                           │                           │
   │  WS Message 1             │                           │
   ├──────────────────────────▶│                           │
   │                           │                           │
   │     binds 6ba7b810...         │                           │
   │     (from session)        │                           │
   │                           ├──────────────────────────▶│
   │                           │                           │
```

## Implementation Checklist

### Coordinator

- [ ] Apply `request_id_middleware` to main app
- [ ] Remove custom request ID extraction code
- [ ] Add explicit `X-Backend-Request-ID` to Worker-bound requests
- [ ] Add `X-Backend-Request-ID` to responses
- [ ] Store origin_request_id in session info
- [ ] Handle WebSocket connections with session context

### Worker

- [ ] Apply `request_id_middleware` to main app
- [ ] Remove custom request ID extraction code
- [ ] Add `X-Backend-Request-ID` to application-bound requests
- [ ] Add `X-Backend-Request-ID` to responses
- [ ] Handle streaming responses with proper context

## Migration Notes

### Breaking Changes

None expected. Changes are internal implementation details.

### Testing Strategy

1. **Unit tests**: Verify middleware application
2. **Integration tests**: Trace request_id through Coordinator → Worker → App
3. **WebSocket tests**: Verify session-based request_id preservation

## Configuration

No special configuration required. Components will use standard middleware from common infrastructure.
