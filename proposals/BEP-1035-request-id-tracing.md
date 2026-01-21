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

Request ID tracing is not systematically implemented:
- Manager has `request_id_middleware` for HTTP requests, but doesn't propagate to other services
- Agent RPC does not support request_id
- Background tasks do not have request_id
- App-Proxy does not have request_id support

This leads to:
- No way to correlate logs across components
- Cannot trace the full path of a request through the system

## Design Principles

1. **Context-based Propagation**: Use Python's `contextvars` to carry request ID through async call chains
2. **Automatic Generation**: Generate request IDs at system entry points if not provided
3. **Standard Headers**: Use consistent header names across HTTP and RPC protocols
4. **Extensible Structure**: Design for future additions (correlation_id, trace_id, span_id for OpenTelemetry)
5. **Minimal Overhead**: Request ID handling should have negligible performance impact
6. **Backward Compatibility**: Support gradual migration without breaking existing deployments

## Scope

### In Scope

| Component | Current | Proposed |
|-----------|---------|----------|
| Common Infrastructure | `request_id_middleware` exists | Add utilities, RPC headers model |
| Manager | HTTP middleware only | Propagate to Agent, Storage-Proxy, App-Proxy |
| Agent | No request_id support | Add RPC headers support |
| Storage-Proxy | HTTP middleware only | Add background task support |
| App-Proxy Coordinator | No request_id support | Add middleware and propagation |
| App-Proxy Worker | No request_id support | Add middleware and propagation |

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
| [agent.md](./BEP-1035/agent.md) | Agent component: RPC headers design |
| [storage-proxy.md](./BEP-1035/storage-proxy.md) | Storage-Proxy component |
| [app-proxy.md](./BEP-1035/app-proxy.md) | App-Proxy Coordinator and Worker |

### Key Design Decisions

#### 1. RPC Header Structure (Extensible)

For Agent RPC calls via Callosum (which doesn't support separate headers), we embed headers in the body:

```python
# Request Structure
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
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
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
    },
    "result": {...}  # or "error": {...}
}
```

See [agent.md](./BEP-1035/agent.md) for complete RPC headers specification.

#### 2. HTTP Header Standard

| Header Name | Direction | Description |
|-------------|-----------|-------------|
| `X-Backend-Request-ID` | Request/Response | Primary request identifier, echoed in response |

#### 3. Request ID Format

```
Format: "{uuid4}"
Example: "550e8400-e29b-41d4-a716-446655440000"
```

Generated using `uuid.uuid4()`.

## Implementation Status

| Component | Current State | Target State | Priority |
|-----------|--------------|--------------|----------|
| Common | `request_id_middleware` only | Add utilities, `RPCHeaders` model | High |
| Manager | HTTP middleware only | Propagate to all outbound calls | High |
| Agent | No request_id support | RPC headers support | High |
| Storage-Proxy | HTTP middleware only | Add background task decorator | Low |
| App-Proxy | No request_id support | Add middleware | Medium |

## Migration Plan

### Phase 1: Common Infrastructure

1. Add `RPCHeaders` Pydantic model to common
2. Add `@with_request_id_context` decorator
3. Add utilities (`bind_request_id`, `current_request_id`, etc.)

### Phase 2: Agent RPC Headers

1. Add RPC headers support to Agent
2. Update Manager to send headers in RPC calls
3. Maintain backward compatibility with legacy Agents

### Phase 3: App-Proxy Standardization

1. Add `request_id_middleware` to Coordinator and Worker
2. Ensure Worker ↔ Coordinator propagation

### Phase 4: Full Coverage

1. Add `@with_request_id_context` to all background tasks
2. Add request_id to event system metadata

## Backward Compatibility

### Manager → Agent Communication

During migration:
- Manager sends requests with `headers` field in body
- New Agents extract request_id from headers
- Legacy Agents ignore the `headers` field (no breaking change)

Version detection via Agent capability advertisement.

### HTTP Services

HTTP services can adopt `request_id_middleware` incrementally - no breaking changes.

## Open Questions

1. **Capability Advertisement**: How should Manager detect if Agent supports RPC headers?
   - Option A: Agent advertises capabilities during registration
   - Option B: Always send headers (legacy Agents ignore unknown fields)

2. **WebSocket Sessions**: How should long-lived WebSocket connections handle request IDs?
   - Option A: One request_id per connection
   - Option B: New request_id per message

3. **Event System**: Should event handlers maintain the original request_id or generate new ones?
   - Recommendation: Maintain original for causality tracking

## Ideation

Ideas under consideration for future iterations. These are not part of the current proposal.

### Source-Prefixed Request IDs

Currently, all request IDs are plain UUIDs (e.g., `550e8400-e29b-41d4-a716-446655440000`). Consider adding a source prefix to indicate where the request originated:

| Source | Format | Example |
|--------|--------|---------|
| Client SDK | `client-{uuid4}` | `client-550e8400-e29b-41d4-a716-446655440000` |
| Web UI | `webui-{uuid4}` | `webui-6ba7b810-9dad-11d1-80b4-00c04fd430c8` |
| Manager (internal) | `mgr-{uuid4}` | `mgr-f47ac10b-58cc-4372-a567-0e02b2c3d479` |
| Agent (internal) | `agent-{uuid4}` | `agent-7c9e6679-7425-40de-944b-e07fc1f90ae7` |
| Background task | `bgtask-{uuid4}` | `bgtask-a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` |

**Benefits:**
- Quickly identify request origin when debugging
- Filter logs by source type
- Understand request flow patterns

**Considerations:**
- Requires coordination across all entry points
- Client SDK would need to be updated to use the prefix
- Backward compatibility with existing plain UUID format

## References

- [OpenTelemetry Trace Context](https://www.w3.org/TR/trace-context/)
- [BEP-1002: Agent Architecture](./BEP-1002-agent-architecture.md)
