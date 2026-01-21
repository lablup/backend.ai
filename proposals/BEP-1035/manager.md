# Manager Component

The Manager serves as the central hub in Backend.AI's architecture. It receives requests from clients and orchestrates operations across Agents, Storage-Proxy, and App-Proxy services.

## Entry Points

### HTTP API

All HTTP requests enter through the aiohttp application with `request_id_middleware`:

```python
# ai/backend/manager/server.py
from ai.backend.common.logging_utils import request_id_middleware

app = web.Application(middlewares=[
    request_id_middleware,
    # ... other middlewares
])
```

The middleware automatically:
1. Extracts `X-Request-ID` header if present
2. Generates new request ID if not present
3. Binds request ID to context
4. Adds `X-Backend-Request-ID` to response headers

### Background Tasks

Background tasks use the `@ensure_request_id` decorator:

```python
from ai.backend.common.logging_utils import ensure_request_id

@ensure_request_id
async def cleanup_stale_sessions() -> None:
    """Periodic background task."""
    log.info("Running cleanup")  # Has request_id for tracing
    # ...

@ensure_request_id
async def process_pending_operations() -> None:
    """Background worker processing queue."""
    # ...
```

### Message Queue Event Handlers

Event handlers preserve request ID from event metadata:

```python
async def handle_event(event: Event, metadata: MessageMetadata) -> None:
    # Restore original request_id for causality tracking
    if metadata.request_id:
        _request_id_var.set(metadata.request_id)
    else:
        _request_id_var.set(new_request_id())
    
    await process_event(event)
```

## Outbound Propagation

### Agent RPC Calls

Manager communicates with Agents via Callosum RPC. Request ID is propagated in the request body:

```python
# ai/backend/manager/agent/invoker.py

class PeerInvoker:
    async def invoke(
        self,
        method: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        request_id = current_request_id()
        
        # Build request with headers
        request_body = {
            "headers": {
                "request_id": request_id,
            },
            "args": args,
            "kwargs": kwargs,
        }
        
        # Send via Callosum
        response = await self._peer.invoke(method, request_body)
        return response.get("result")
```

#### Legacy Compatibility

For Agents running older versions (V2 registry), the request_id is also placed at the top level:

```python
# Compatibility mode
request_body = {
    "headers": {"request_id": request_id},  # V3 format
    "request_id": request_id,                # V2 fallback
    "args": args,
    "kwargs": kwargs,
}
```

### Storage-Proxy HTTP Calls

Storage-Proxy communication uses standard HTTP headers:

```python
# ai/backend/manager/api/vfolder.py

async def call_storage_proxy(
    session: aiohttp.ClientSession,
    endpoint: str,
    params: dict,
) -> dict:
    request_id = current_request_id()
    headers = {}
    if request_id:
        headers["X-Request-ID"] = request_id
    
    async with session.post(
        endpoint,
        headers=headers,
        json=params,
    ) as response:
        return await response.json()
```

### App-Proxy HTTP Calls

App-Proxy communication follows the same pattern:

```python
async def call_app_proxy(
    session: aiohttp.ClientSession,
    coordinator_url: str,
    operation: str,
    data: dict,
) -> dict:
    request_id = current_request_id()
    headers = {"X-Request-ID": request_id} if request_id else {}
    
    async with session.post(
        f"{coordinator_url}/{operation}",
        headers=headers,
        json=data,
    ) as response:
        return await response.json()
```

### WSProxy Calls

WebSocket proxy calls include request ID:

```python
async def establish_wsproxy_session(
    session_info: SessionInfo,
) -> WSProxySession:
    request_id = current_request_id()
    headers = {"X-Request-ID": request_id} if request_id else {}
    
    # Initial HTTP upgrade request carries request_id
    ws = await connect_wsproxy(
        session_info.wsproxy_url,
        headers=headers,
    )
    return ws
```

## Event System Integration

### EventProducer

When producing events, include request ID in metadata:

```python
from ai.backend.common.events import EventProducer

class ManagerEventProducer:
    async def produce(self, event: Event) -> None:
        metadata = EventMetadata(
            request_id=current_request_id(),
            timestamp=datetime.now(UTC),
            source="manager",
        )
        await self._producer.send(event, metadata=metadata)
```

### EventDispatcher

When dispatching events to handlers:

```python
class EventDispatcher:
    async def dispatch(self, event: Event, metadata: EventMetadata) -> None:
        # Bind request_id from event metadata
        token = _request_id_var.set(metadata.request_id or new_request_id())
        try:
            await self._handlers[event.type](event)
        finally:
            _request_id_var.reset(token)
```

## Request Flow Examples

### Session Creation

```
Client                    Manager                    Agent
   │                         │                         │
   │  POST /sessions         │                         │
   │  X-Request-ID: req-123  │                         │
   ├────────────────────────▶│                         │
   │                         │                         │
   │           middleware binds req-123                │
   │                         │                         │
   │                         │  RPC: create_kernel     │
   │                         │  headers.request_id:    │
   │                         │    req-123              │
   │                         ├────────────────────────▶│
   │                         │                         │
   │                         │    Agent logs with      │
   │                         │    request_id: req-123  │
   │                         │                         │
   │                         │◀────────────────────────┤
   │                         │                         │
   │  201 Created            │                         │
   │  X-Backend-Request-ID:  │                         │
   │    req-123              │                         │
   │◀────────────────────────┤                         │
```

### VFolder Upload to Storage-Proxy

```
Client                    Manager               Storage-Proxy
   │                         │                         │
   │  POST /folders/upload   │                         │
   │  X-Request-ID: req-456  │                         │
   ├────────────────────────▶│                         │
   │                         │                         │
   │                         │  POST /upload           │
   │                         │  X-Request-ID: req-456  │
   │                         ├────────────────────────▶│
   │                         │                         │
   │                         │    Storage-Proxy logs   │
   │                         │    with req-456         │
   │                         │                         │
   │                         │◀────────────────────────┤
   │                         │                         │
   │◀────────────────────────┤                         │
```

## Implementation Checklist

### HTTP Entry Points
- [x] `request_id_middleware` applied to main app
- [ ] Verify all sub-apps have middleware

### Background Tasks
- [x] `@ensure_request_id` on cleanup tasks (PR #8160)
- [x] `@ensure_request_id` on background workers (PR #8160)
- [ ] Audit all background entry points

### Outbound Calls
- [ ] Agent RPC via PeerInvoker
- [ ] Storage-Proxy HTTP calls
- [ ] App-Proxy HTTP calls
- [ ] WSProxy establishment

### Event System
- [ ] EventProducer includes request_id in metadata
- [ ] EventDispatcher restores request_id from metadata

## Migration Notes

### Current State

1. `request_id_middleware` is applied to Manager HTTP app
2. PR #8160 added `@ensure_request_id` to background tasks
3. Agent RPC calls partially propagate request_id (depends on Agent version)

### Required Changes

1. **PeerInvoker update**: Ensure all RPC calls include `headers.request_id`
2. **Storage-Proxy calls**: Add `X-Request-ID` header to all HTTP calls
3. **App-Proxy calls**: Add `X-Request-ID` header to all HTTP calls
4. **Event system**: Include request_id in event metadata

### Testing Strategy

1. **Unit tests**: Verify request_id propagation in each call site
2. **Integration tests**: Trace request_id across Manager → Agent flow
3. **Log correlation tests**: Verify logs from all components share request_id
