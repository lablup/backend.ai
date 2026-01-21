# App-Proxy Components

App-Proxy consists of two components:
- **Coordinator**: Routes requests and manages session mappings
- **Worker**: Handles actual proxying to application endpoints

## Architecture Overview

```
Client                    Coordinator                   Worker                    App
   │                           │                           │                       │
   │  HTTP Request             │                           │                       │
   │  X-Backend-Request-ID     │                           │                       │
   ├──────────────────────────▶│                           │                       │
   │                           │                           │                       │
   │                           │  Route to Worker          │                       │
   │                           │  X-Backend-Request-ID     │                       │
   │                           ├──────────────────────────▶│                       │
   │                           │                           │                       │
   │                           │                           │  Proxy to App         │
   │                           │                           │  X-Backend-Request-ID │
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

Apply `request_id_middleware` to both Coordinator and Worker aiohttp applications.

### 2. Coordinator → Worker Propagation

Coordinator includes `X-Backend-Request-ID` header when forwarding requests to Worker.

### 3. Worker → App Propagation

Worker includes `X-Backend-Request-ID` header when proxying to applications.

### 4. WebSocket Session Context

For long-lived connections:
- Capture request_id at connection establishment
- Preserve the same request_id for all messages in the session
- Alternative: Generate per-message request_id with session prefix for high-cardinality tracing

## Request Flow

### HTTP Request

```
Client                    Coordinator                   Worker                    App
   │                           │                           │                       │
   │  POST /apps/jupyter       │                           │                       │
   │  X-Backend-Request-ID     │                           │                       │
   ├──────────────────────────▶│                           │                       │
   │                           │                           │                       │
   │                           │  POST /proxy              │                       │
   │                           │  X-Backend-Request-ID     │                       │
   │                           ├──────────────────────────▶│                       │
   │                           │                           │                       │
   │                           │                           │  GET /api             │
   │                           │                           │  X-Backend-Request-ID │
   │                           │                           ├──────────────────────▶│
   │                           │                           │                       │
   │                           │                           │◀──────────────────────┤
   │                           │◀──────────────────────────┤                       │
   │◀──────────────────────────┤                           │                       │
```

### WebSocket Connection

```
Client                    Coordinator                   Worker
   │                           │                           │
   │  WS Upgrade               │                           │
   │  X-Backend-Request-ID     │                           │
   ├──────────────────────────▶│                           │
   │                           │                           │
   │  WS Established           │                           │
   │◀──────────────────────────┤                           │
   │                           │                           │
   │  WS Message               │                           │
   ├──────────────────────────▶│                           │
   │                           │  (same request_id)        │
   │                           ├──────────────────────────▶│
```

## Implementation Checklist

### Coordinator

- [ ] Apply `request_id_middleware`
- [ ] Propagate `X-Backend-Request-ID` to Worker
- [ ] Store origin_request_id in session info
- [ ] Handle WebSocket connections with session context

### Worker

- [ ] Apply `request_id_middleware`
- [ ] Propagate `X-Backend-Request-ID` to applications
- [ ] Handle streaming responses with proper context
