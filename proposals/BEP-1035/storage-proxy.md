# Storage-Proxy Component

Storage-Proxy handles file storage operations for virtual folders (vfolders). It provides HTTP APIs for file upload, download, and management operations.

## Current State

Storage-Proxy does not have standardized request_id support:
- No HTTP middleware for request ID
- No `X-Backend-Request-ID` in responses
- Background tasks have no request_id

## Proposed Changes

### HTTP Middleware

Apply HTTP middleware for request ID handling:
- Incoming requests from Manager (with `X-Backend-Request-ID`)
- Direct client requests (generate new request_id)

### Background Operations

Apply context binding decorator to background tasks:
- File cleanup tasks
- Storage sync operations
- Clone/copy operations

### Request Flow

**Via Manager:**
```
Manager                       Storage-Proxy
   │                               │
   │  POST /folders/upload         │
   │  X-Backend-Request-ID         │
   ├──────────────────────────────▶│
   │                               │
   │         extract request_id    │
   │         from header           │
   │                               │
   │  200 OK                       │
   │  X-Backend-Request-ID         │
   │◀──────────────────────────────┤
```

**Direct Client Access (via StorageProxyClientFacingInfo):**
```
Client                        Storage-Proxy
   │                               │
   │  GET /download/...            │
   │  (no X-Backend-Request-ID)    │
   ├──────────────────────────────▶│
   │                               │
   │         generate new          │
   │         request_id            │
   │                               │
   │  200 OK                       │
   │  X-Backend-Request-ID         │
   │◀──────────────────────────────┤
```

When clients access Storage-Proxy directly (e.g., presigned URLs), Storage-Proxy generates its own request_id.

## Implementation Checklist

- [ ] Apply HTTP middleware to main app
- [ ] Response includes `X-Backend-Request-ID`
- [ ] Context binding decorator on background tasks
