# App-Proxy Components

App-Proxy consists of two components:
- **Coordinator**: Manages circuit lifecycle, worker registration, and session mappings
- **Worker**: Handles actual proxying to application endpoints (kernel containers)

## Architecture Overview

```
Manager                   Coordinator                  Worker                    App
   │                           │                          │                       │
   │  POST /v2/proxy/auth      │                          │                       │
   │  (create circuit)         │                          │                       │
   ├──────────────────────────▶│                          │                       │
   │                           │                          │                       │
   │                           │  Redis Event             │                       │
   │                           │  (circuit created)       │                       │
   │                           ├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─▶│                       │
   │                           │                          │                       │
   │  ◀── redirect URL ────────┤                          │                       │
   │                           │                          │                       │
   │                           │                          │                       │
   │      Client (after redirect)                         │                       │
   │             │                                        │                       │
   │             │  HTTP Request (direct)                 │                       │
   │             ├───────────────────────────────────────▶│                       │
   │             │                                        │  Proxy to App         │
   │             │                                        ├──────────────────────▶│
   │             │                                        │                       │
   │             │                                        │◀──────────────────────┤
   │             │◀───────────────────────────────────────┤                       │
```

**Key Points:**
- Manager initiates circuit creation via Coordinator API
- Coordinator deploys circuits to Workers via Redis events
- Client traffic goes directly to Worker (not through Coordinator)

## Current State

App-Proxy (Coordinator and Worker) does not have request_id support:
- No HTTP middleware for request ID in Coordinator or Worker
- No request_id in circuit metadata (Redis events)
- No request_id in WebSocket/SSE connections

## Proposed Changes

### 1. Apply Standard Middleware

Apply HTTP middleware for request ID to both Coordinator and Worker aiohttp applications.

### 2. Circuit Creation Event Propagation

When Manager creates a circuit via Coordinator API:
- Coordinator extracts `X-Backend-Request-ID` from Manager's request
- Include `origin_request_id` in circuit metadata (Redis event)
- Worker receives and stores this for tracing the circuit's origin

### 3. Worker → App Propagation

Worker includes `X-Backend-Request-ID` header when proxying to applications (kernel containers).

### 4. WebSocket Session Context

For long-lived connections:
- Capture request_id at connection establishment
- Preserve the same request_id for all messages in the session
- Alternative: Generate per-message request_id with session prefix for high-cardinality tracing

## Request Flow

### Circuit Creation (via Manager)

```
Manager                   Coordinator                  Worker
   │                           │                          │
   │  POST /v2/proxy/auth      │                          │
   │  X-Backend-Request-ID     │                          │
   ├──────────────────────────▶│                          │
   │                           │                          │
   │             middleware extracts/generates request_id │
   │                           │                          │
   │                           │  Redis Event             │
   │                           │  (circuit metadata)      │
   │                           ├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─▶│
   │                           │                          │
   │  redirect URL + token     │                          │
   │  X-Backend-Request-ID     │                          │
   │◀──────────────────────────┤                          │
```

### HTTP Request (Client → Worker, direct)

```
Client                                    Worker                    App
   │                                         │                       │
   │  HTTP Request (to allocated port/domain)│                       │
   ├────────────────────────────────────────▶│                       │
   │                                         │                       │
   │               middleware generates request_id                   │
   │                                         │                       │
   │                                         │  Proxy to App         │
   │                                         │  X-Backend-Request-ID │
   │                                         ├──────────────────────▶│
   │                                         │                       │
   │                                         │◀──────────────────────┤
   │  X-Backend-Request-ID                   │                       │
   │◀────────────────────────────────────────┤                       │
```

### WebSocket Connection (Client → Worker, direct)

```
Client                                    Worker                    App
   │                                         │                       │
   │  WS Upgrade (to allocated port/domain)  │                       │
   ├────────────────────────────────────────▶│                       │
   │                                         │                       │
   │               middleware generates request_id                   │
   │                                         │                       │
   │  WS Established                         │  WS to App            │
   │  X-Backend-Request-ID                   ├──────────────────────▶│
   │◀────────────────────────────────────────┤                       │
   │                                         │                       │
   │  WS Message                             │                       │
   ├────────────────────────────────────────▶│  (same request_id)    │
   │                                         ├──────────────────────▶│
```

## Implementation Checklist

### Coordinator

- [ ] Apply HTTP middleware for request ID
- [ ] Include `origin_request_id` in circuit metadata (Redis events)
- [ ] Store origin_request_id in circuit database record

### Worker

- [ ] Apply HTTP middleware for request ID
- [ ] Propagate `X-Backend-Request-ID` to applications (kernel containers)
- [ ] Handle WebSocket connections with session-level request_id context
