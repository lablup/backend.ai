---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2025-01-21
Created-Version: 26.2.0
Target-Version: 26.2.0
Implemented-Version:
---

# Distributed Request ID Propagation

## Abstract

This BEP defines a comprehensive request ID tracing system for Backend.AI's distributed architecture. It establishes standards for generating, propagating, and utilizing request IDs across all components (Manager, Agent, Storage-Proxy, App-Proxy, Web Server) to enable end-to-end request tracing, debugging, and observability.

## Motivation

Backend.AI is a distributed system where a single user request can traverse multiple components:
1. A user request enters via the Manager's HTTP API
2. The Manager may invoke RPCs on Agents, HTTP calls to Storage-Proxy, or communicate with App-Proxy
3. Background tasks and event handlers process work asynchronously
4. Each component generates logs independently

Without a unified request ID tracing system:
- **Debugging is difficult**: When an error occurs, correlating logs across components requires manual timestamp matching
- **Root cause analysis is slow**: Tracing the full path of a failed request requires examining logs from multiple services
- **Observability is limited**: Cannot build request flow visualizations or measure end-to-end latencies
- **Audit trails are incomplete**: Cannot definitively link related operations across service boundaries

### Current State

Several components have partial implementations:
- Manager uses `request_id_middleware` for HTTP requests
- Agent extracts `request_id` from RPC body but has multiple registry versions
- Some background tasks generate request IDs, but coverage is incomplete
- App-Proxy has custom (non-standard) request ID handling

This fragmented approach leads to:
- Inconsistent header names and extraction logic
- Missing propagation at some service boundaries
- Duplicate implementations across components

## Design Principles

1. **Context-based Propagation**: Use Python's `contextvars` to carry request ID through async call chains
2. **Automatic Generation**: Generate request IDs at system entry points if not provided
3. **Standard Headers**: Use consistent header names across HTTP and RPC protocols
4. **Extensible Structure**: Design for future additions (correlation_id, trace_id, span_id for OpenTelemetry)
5. **Minimal Overhead**: Request ID handling should have negligible performance impact
6. **Backward Compatibility**: Support gradual migration without breaking existing deployments

## Scope

### In Scope

| Component | Status | Description |
|-----------|--------|-------------|
| Common Infrastructure | Partial | `request_id_middleware`, utilities, ContextVar |
| Manager | Partial | Hub component, propagates to other services |
| Agent | Partial | RPCFunctionRegistryV3 needed for proper header handling |
| Storage-Proxy | ✓ | Uses standard middleware |
| App-Proxy Coordinator | ✗ | Custom implementation needs standardization |
| App-Proxy Worker | ✗ | Custom implementation needs standardization |

### Out of Scope (Future Work)

| Component | Notes |
|-----------|-------|
| Account Manager | Separate service, may follow later |
| Web Server | Frontend proxy, may add middleware |
| WSProxy | WebSocket proxy, pass-through behavior |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Request Flow                                    │
└─────────────────────────────────────────────────────────────────────────────┘

    External Request                 Background Task
          │                                │
          ▼                                ▼
    ┌─────────────┐                 ┌─────────────────┐
    │    HTTP     │                 │   Auto-generate │
    │ middleware  │                 │   request_id    │
    └──────┬──────┘                 └────────┬────────┘
           │                                 │
           ▼                                 ▼
    ┌─────────────────────────────────────────────────┐
    │              _request_id_var (ContextVar)        │
    │                                                  │
    │   current_request_id() → str | None             │
    │   bind_request_id(id) → context manager         │
    └──────────────────────────────────────────────────┘
           │
           ├──────────────────┬──────────────────┬────────────────────┐
           ▼                  ▼                  ▼                    ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │    Agent    │    │  Storage-   │    │  App-Proxy  │    │   Event     │
    │    (RPC)    │    │   Proxy     │    │    (HTTP)   │    │   System    │
    │             │    │   (HTTP)    │    │             │    │             │
    │ headers: {  │    │ X-Request-  │    │ X-Request-  │    │ metadata: { │
    │  request_id │    │    ID       │    │    ID       │    │  request_id │
    │ }           │    │             │    │             │    │ }           │
    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Detailed Design

Detailed specifications are organized into component-specific documents:

| Document | Description |
|----------|-------------|
| [common.md](./BEP-1035/common.md) | Common infrastructure: ContextVar, middleware, utilities |
| [manager.md](./BEP-1035/manager.md) | Manager component: entry points, outbound propagation |
| [agent.md](./BEP-1035/agent.md) | Agent component: RPCFunctionRegistryV3 design |
| [storage-proxy.md](./BEP-1035/storage-proxy.md) | Storage-Proxy component |
| [app-proxy.md](./BEP-1035/app-proxy.md) | App-Proxy Coordinator and Worker |

### Key Design Decisions

#### 1. RPC Header Structure (Extensible)

For Agent RPC calls via Callosum (which doesn't support separate headers), we embed headers in the body:

```python
# Request Structure
{
    "headers": {
        "request_id": "req-abc123",
        "correlation_id": "...",    # Optional, future
        "trace_id": "...",          # Optional, OpenTelemetry
        "span_id": "...",           # Optional, OpenTelemetry
    },
    "args": [...],
    "kwargs": {...}
}

# Response Structure
{
    "headers": {
        "request_id": "req-abc123",
    },
    "result": {...}  # or "error": {...}
}
```

See [agent.md](./BEP-1035/agent.md) for complete RPCFunctionRegistryV3 specification.

#### 2. HTTP Header Standard

| Header Name | Direction | Description |
|-------------|-----------|-------------|
| `X-Request-ID` | Request/Response | Primary request identifier |
| `X-Backend-Request-ID` | Response | Echo back for debugging |

#### 3. Request ID Format

```
Format: "req-{uuid4}"
Example: "req-550e8400-e29b-41d4-a716-446655440000"
```

Generated using `ai.backend.common.logging.new_request_id()`.

## Implementation Status

| Component | Current State | Target State | Priority |
|-----------|--------------|--------------|----------|
| Common | `request_id_middleware` exists | Add `RPCHeaders` model | High |
| Manager | Middleware active, partial propagation | Full propagation to all services | High |
| Agent | v1/v2 registries | RPCFunctionRegistryV3 | High |
| Storage-Proxy | Middleware active | Complete | Low |
| App-Proxy | Custom implementation | Standardize to common | Medium |

## Migration Plan

### Phase 1: Common Infrastructure (26.1.x)

1. Add `RPCHeaders` Pydantic model to common
2. Add `receive_request_id()` utility for RPC handlers
3. Ensure `bind_request_id()` is used in all outbound calls

### Phase 2: Agent RPCFunctionRegistryV3 (26.2.0)

1. Implement V3 registry with header support
2. Add version negotiation between Manager and Agent
3. Maintain V2 compatibility during transition

### Phase 3: App-Proxy Standardization (26.2.x)

1. Replace custom request ID handling with standard middleware
2. Ensure Worker ↔ Coordinator propagation

### Phase 4: Cleanup (26.3.0)

1. Remove deprecated V1/V2 registries
2. Remove compatibility shims

## Backward Compatibility

### Manager → Agent Communication

During migration:
- Manager sends requests with headers in body
- V3 Agents extract from headers
- V2 Agents continue to work (fallback to body.request_id)

Version detection via Agent capability advertisement or protocol negotiation.

### HTTP Services

Existing services already use `X-Request-ID` header - no breaking changes.

## Open Questions

1. **Version Negotiation**: How should Manager detect Agent RPC version?
   - Option A: Agent advertises capabilities during registration
   - Option B: Try V3 format, fallback to V2 on error
   - Option C: Configuration-based version selection

2. **WebSocket Sessions**: How should long-lived WebSocket connections handle request IDs?
   - Option A: One request_id per connection
   - Option B: New request_id per message
   - Option C: Client-provided request_id in each message

3. **Event System**: Should event handlers maintain the original request_id or generate new ones?
   - Recommendation: Maintain original for causality tracking

## References

- [OpenTelemetry Trace Context](https://www.w3.org/TR/trace-context/)
- [BEP-1002: Agent Architecture](./BEP-1002-agent-architecture.md)
