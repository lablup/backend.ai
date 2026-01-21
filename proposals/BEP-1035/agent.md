# Agent Component

The Agent component handles compute kernel management and communicates with the Manager via Callosum RPC. This document describes the request ID tracing implementation for the Agent.

## Callosum Constraints

Callosum is the RPC library used for Manager ↔ Agent communication. Key constraints:

1. **No separate header channel**: Unlike HTTP, Callosum doesn't have a metadata/header mechanism separate from the message body
2. **Binary protocol**: Messages are serialized (msgpack) and sent as single payloads
3. **Request-response pattern**: Each RPC call has a request and response

**Implication**: Request metadata (including request_id) must be embedded within the message body structure.

## Current State

- Agent RPC does not support request_id propagation
- No way to trace the origin of Manager → Agent RPC calls
- No structure for metadata in request/response

## Proposed Design

### Design Goals

1. **Separate concerns**: Headers (metadata) separated from args/kwargs (business data)
2. **Extensibility**: Header structure supports future additions (correlation_id, trace_id)
3. **Type safety**: Pydantic models for validation
4. **Backward compatibility**: Graceful handling of legacy requests without headers

### Request Structure

```python
from pydantic import BaseModel

class RPCHeaders(BaseModel):
    """
    Headers for RPC requests.
    Designed for extensibility with extra="allow".
    """
    request_id: str | None = None
    correlation_id: str | None = None  # Future: group related requests
    trace_id: str | None = None        # Future: OpenTelemetry
    span_id: str | None = None         # Future: OpenTelemetry
    
    class Config:
        extra = "allow"

class RPCRequest(BaseModel):
    """
    V3 RPC request structure.
    """
    headers: RPCHeaders = RPCHeaders()
    args: list[Any] = []
    kwargs: dict[str, Any] = {}
```

Wire format:

```json
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "correlation_id": null,
        "trace_id": null,
        "span_id": null
    },
    "args": ["kernel-id-123"],
    "kwargs": {"timeout": 30}
}
```

### Response Structure

```python
class RPCResponse(BaseModel):
    """
    V3 RPC response structure.
    """
    headers: RPCHeaders = RPCHeaders()
    result: Any | None = None
    error: dict[str, Any] | None = None
```

Success response:

```json
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "result": {
        "kernel_id": "kernel-abc",
        "status": "running"
    }
}
```

Error response:

```json
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "error": {
        "type": "KernelNotFoundError",
        "message": "Kernel kernel-xyz not found",
        "details": {}
    }
}
```

### Implementation

```python
class RPCDispatcher:
    """
    RPC dispatcher with structured headers and extensible tracing.
    """
    
    _functions: dict[str, Callable[..., Awaitable[AbstractAgentResp]]]
    
    def register(self, name: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._functions[name] = func
            return func
        return decorator
    
    async def dispatch(self, method: str, raw_body: dict) -> dict:
        """
        Dispatch RPC call.
        Automatically detects and handles both new and legacy formats.
        """
        # Parse request
        request = self._parse_request(raw_body)
        
        # Bind request_id to context
        request_id = request.headers.request_id or new_request_id()
        _request_id_var.set(request_id)
        
        try:
            func = self._functions.get(method)
            if func is None:
                return self._error_response(
                    request_id,
                    "MethodNotFoundError",
                    f"Method {method} not found",
                )
            
            result = await func(*request.args, **request.kwargs)
            return self._success_response(request_id, result)
            
        except Exception as e:
            log.exception("RPC call failed", method=method)
            return self._error_response(
                request_id,
                type(e).__name__,
                str(e),
            )
    
    def _parse_request(self, raw_body: dict) -> RPCRequest:
        """
        Parse request with automatic format detection.
        """
        if "headers" in raw_body:
            # New format with headers
            return RPCRequest.model_validate(raw_body)
        else:
            # Legacy format: no request_id, will be auto-generated
            return RPCRequest(
                headers=RPCHeaders(),
                args=raw_body.get("args", []),
                kwargs=raw_body.get("kwargs", {}),
            )
    
    def _success_response(
        self,
        request_id: str,
        result: AbstractAgentResp,
    ) -> dict:
        return {
            "headers": {"request_id": request_id},
            "result": result.to_response(),
        }
    
    def _error_response(
        self,
        request_id: str,
        error_type: str,
        message: str,
    ) -> dict:
        return {
            "headers": {"request_id": request_id},
            "error": {
                "type": error_type,
                "message": message,
            },
        }
```

### Usage Example

```python
dispatcher = RPCDispatcher()

@dispatcher.register("create_kernel")
async def create_kernel(
    kernel_id: str,
    config: KernelConfig,
) -> CreateKernelResponse:
    log.info("Creating kernel", kernel_id=kernel_id)
    # request_id is already in context from dispatch()
    
    kernel = await kernel_manager.create(kernel_id, config)
    
    return CreateKernelResponse(
        kernel_id=kernel.id,
        status=kernel.status,
    )
```

## Version Negotiation

Manager needs to know which protocol version the Agent supports.

### Option A: Capability Advertisement (Recommended)

Agent advertises capabilities during heartbeat/registration:

```python
# Agent side
heartbeat_data = {
    "agent_id": agent_id,
    "capabilities": {
        "rpc_headers": True,  # Supports headers in RPC
    },
}

# Manager side
if agent.capabilities.get("rpc_headers", False):
    request_body = {
        "headers": {"request_id": current_request_id()},
        "args": args,
        "kwargs": kwargs,
    }
else:
    # Legacy format (no request_id support)
    request_body = {
        "args": args,
        "kwargs": kwargs,
    }
```

### Option B: Always Send Headers

Manager always includes headers (simpler approach):

```python
request_body = {
    "headers": {"request_id": current_request_id()},
    "args": args,
    "kwargs": kwargs,
}
```

Legacy Agents ignore unknown `headers` field, new Agents use it for tracing.

## Backward Compatibility

### Request Format Detection

Agent automatically detects request format:

| Request Format | Detection | Handling |
|----------------|-----------|----------|
| With `headers` | `"headers" in body` | Extract request_id from headers |
| Without `headers` | Legacy format | Auto-generate request_id |

### Response Format

Manager detects response format by presence of `headers` field:

| Response Format | Detection | Handling |
|-----------------|-----------|----------|
| With `headers` | `"headers" in response` | Process as new format |
| Without `headers` | Legacy format | Process as legacy |

## Migration Strategy

### Phase 1: Agent Update (Non-breaking)

1. Agent accepts both new format (with `headers`) and legacy format
2. Can be deployed without Manager changes

### Phase 2: Manager Update

1. Manager detects Agent capabilities
2. Send new format to Agents that support it
3. Continue legacy format for older Agents

### Phase 3: Deprecation

1. Log warnings when legacy format is used
2. Announce removal timeline

### Phase 4: Cleanup (Breaking)

1. Remove legacy format support code
2. Require new format only

## Implementation Checklist

- [ ] Add `RPCHeaders` model to `ai.backend.common`
- [ ] Add `RPCRequest` and `RPCResponse` models
- [ ] Update Agent RPC dispatcher to support new format
- [ ] Add legacy format fallback detection
- [ ] Add capability advertisement for rpc protocol version
- [ ] Update Manager `PeerInvoker` to send new format
- [ ] Add version detection in Manager
- [ ] Add integration tests for format compatibility
- [ ] Add metrics for protocol version usage

## References

- [Callosum](https://github.com/lablup/callosum) - An RPC Transport Library for asyncio
