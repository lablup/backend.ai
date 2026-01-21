# Manager Component

The Manager serves as the central hub in Backend.AI's architecture. It receives requests from clients and orchestrates operations across Agents, Storage-Proxy, and App-Proxy services.

## Entry Points

### HTTP API

Apply `request_id_middleware` to the aiohttp application. The middleware:
1. Extracts `X-Backend-Request-ID` header if present
2. Generates new request ID if not present
3. Binds request ID to context
4. Adds `X-Backend-Request-ID` to response headers

### Background Tasks

Apply `@with_request_id_context` decorator to background tasks that don't originate from HTTP requests.

### Message Queue Event Handlers

Restore request ID from event metadata for causality tracking.

## Outbound Propagation

### Agent RPC Calls

Manager communicates with Agents via Callosum RPC. Include request ID in the request body:

```python
request_body = {
    "headers": {"request_id": current_request_id()},
    "args": args,
    "kwargs": kwargs,
}
```

Legacy Agents without headers support will ignore the `headers` field.

### HTTP Calls (Storage-Proxy, App-Proxy, WSProxy)

Include `X-Backend-Request-ID` header in all outbound HTTP requests.

## Event System Integration

- **EventProducer**: Include request_id in event metadata
- **EventDispatcher**: Restore request_id from metadata when handling events

## Request Flow

### Session Creation

```
Client                    Manager                    Agent
   │                         │                         │
   │  POST /sessions         │                         │
   ├────────────────────────▶│                         │
   │                         │                         │
   │               middleware generates request_id     │
   │                         │                         │
   │                         │  RPC: create_kernel     │
   │                         │  headers.request_id     │
   │                         ├────────────────────────▶│
   │                         │                         │
   │                         │◀────────────────────────┤
   │                         │                         │
   │  X-Backend-Request-ID   │                         │
   │◀────────────────────────┤                         │
```

### VFolder Upload

```
Client                    Manager               Storage-Proxy
   │                         │                         │
   │  POST /folders/upload   │                         │
   ├────────────────────────▶│                         │
   │                         │                         │
   │               middleware generates request_id     │
   │                         │                         │
   │                         │  POST /upload           │
   │                         │  X-Backend-Request-ID   │
   │                         ├────────────────────────▶│
   │                         │                         │
   │                         │◀────────────────────────┤
   │                         │                         │
   │  X-Backend-Request-ID   │                         │
   │◀────────────────────────┤                         │
```

## Implementation Checklist

- [ ] `request_id_middleware` applied to main app and sub-apps
- [ ] `@with_request_id_context` on background tasks
- [ ] Agent RPC calls include headers
- [ ] Storage-Proxy/App-Proxy HTTP calls include header
- [ ] Event system propagates request_id
