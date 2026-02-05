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

Coordinator does not store request_id from Manager's circuit creation request.

## Proposed Changes

### 1. No Request ID Generation in App-Proxy

App-Proxy does not generate request_id. All request_id values originate from Manager.
Coordinator only extracts `X-Backend-Request-ID` from Manager's request and stores it for tracing.

### 2. Circuit Creation Tracing

When Manager creates a circuit via Coordinator API:
- Coordinator extracts `X-Backend-Request-ID` from Manager's request
- Store as `origin_request_id` in circuit database record for audit/debugging purposes

## Request Flow

### Circuit Creation (via Manager)

```
Manager                   Coordinator
   │                           │
   │  POST /v2/proxy/auth      │
   │  X-Backend-Request-ID     │
   ├──────────────────────────▶│
   │                           │
   │     extract request_id    │
   │     store as origin_rid   │
   │                           │
   │  redirect URL + token     │
   │◀──────────────────────────┤
```

## Implementation Checklist

### Coordinator

- [ ] Extract `X-Backend-Request-ID` from Manager's request (no generation)
- [ ] Store origin_request_id in circuit database record

### Worker

No request_id handling required. Worker does not interact with Manager directly.
