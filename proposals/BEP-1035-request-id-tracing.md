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
  External Request              Background Task / Event Handler
        │                                  │
        ▼                                  ▼
  ┌───────────┐                    ┌─────────────────────────┐
  │   HTTP    │                    │ 1. Use propagated rid   │
  │ Middleware│                    │    (from event/context) │
  └─────┬─────┘                    │ 2. Auto-generate        │
        │                          │    (fallback only)      │
        │                          └───────────┬─────────────┘
        │                                      │
        └────────────────┬─────────────────────┘
                         ▼
         ┌───────────────────────────────────────┐
         │     _request_id_var (ContextVar)      │
         │                                       │
         │  current_request_id() → str | None    │
         │  bind_request_id(id) → context manager│
         └───────────────────┬───────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │    Agent    │   │   Storage   │   │  App-Proxy  │
    │    (RPC)    │   │    Proxy    │   │   (HTTP)    │
    │             │   │   (HTTP)    │   │             │
    │ headers: {  │   │ X-Backend-  │   │ X-Backend-  │
    │  request_id │   │ Request-ID  │   │ Request-ID  │
    │ }           │   │             │   │             │
    └─────────────┘   └─────────────┘   └─────────────┘
```

## Detailed Design

Detailed specifications are organized into component-specific documents:

| Document | Description |
|----------|-------------|
| [manager.md](./BEP-1035/manager.md) | Manager component: entry points, outbound propagation |
| [agent.md](./BEP-1035/agent.md) | Agent component: RPC headers design |
| [storage-proxy.md](./BEP-1035/storage-proxy.md) | Storage-Proxy component |
| [app-proxy.md](./BEP-1035/app-proxy.md) | App-Proxy Coordinator and Worker |

## Implementation Status

| Component | Current State | Target State | Priority |
|-----------|--------------|--------------|----------|
| Common | HTTP middleware only | Add utilities, RPC headers model | High |
| Manager | HTTP middleware only | Propagate to all outbound calls | High |
| Agent | No request_id support | RPC headers support | High |
| Storage-Proxy | HTTP middleware only | Add context binding for background tasks | Low |
| App-Proxy | No request_id support | Add middleware | Medium |

## Migration Plan

### Phase 1: Common Infrastructure

1. Add decorator for background task/event handler context binding
2. Enhance context utilities for request ID propagation

### Phase 2: Agent RPC Headers

1. Add RPC headers model to Agent
2. Add RPC headers support to Agent RPC dispatcher
3. Update Manager to send headers in RPC calls
4. Maintain backward compatibility with legacy Agents

### Phase 3: App-Proxy Standardization

1. Add HTTP middleware for request ID to Coordinator and Worker
2. Ensure Worker ↔ Coordinator propagation

### Phase 4: Full Coverage

1. Apply context binding decorator to all background tasks and event handlers
2. Add request_id to event system metadata

## Backward Compatibility

### Manager → Agent Communication

During migration:
- Manager sends requests with `headers` field in body
- New Agents extract request_id from headers
- Legacy Agents ignore the `headers` field (no breaking change)

Version detection via Agent capability advertisement.

### HTTP Services

HTTP services can adopt request ID middleware incrementally - no breaking changes.

## Open Questions

1. **Capability Advertisement**: How should Manager detect if Agent supports RPC headers?
   - Option A: Agent advertises capabilities during registration
   - Option B: Always send headers (legacy Agents ignore unknown fields)

2. **Event System**: Should event handlers maintain the original request_id or generate new ones?
   - Recommendation: Maintain original for causality tracking

## Ideation

Ideas under consideration for future iterations. These are not part of the current proposal.

### Structured Request ID Data

Instead of plain UUID strings, use a structured type to carry origin metadata:

```python
@dataclass
class RequestIdData:
    request_id: str                    # UUID string
    component_source: str              # Where generated: "manager", "agent", "storage-proxy"
    source_detail: str | None = None   # Optional detail: "event_handler", "background_task", "rpc_handler"
```

| component_source | source_detail (examples) | Description |
|------------------|--------------------------|-------------|
| `manager` | `None` | HTTP API request |
| `manager` | `event_handler` | Event handler processing |
| `manager` | `background_task` | Background task execution |
| `agent` | `rpc_handler` | Agent RPC handler |
| `storage-proxy` | `background_task` | Storage background task |

**Benefits:**
- Quickly identify request origin when debugging
- Filter logs by component and detail
- Structured data enables better querying
- No string parsing required (unlike prefix approach)

**Considerations:**
- Requires updating context utilities to handle structured data
- Serialization format for RPC/HTTP headers (JSON or separate headers)

## References

- [OpenTelemetry Trace Context](https://www.w3.org/TR/trace-context/)
- [BEP-1002: Agent Architecture](./BEP-1002-agent-architecture.md)
