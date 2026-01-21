# Agent Component

The Agent component handles compute kernel management and communicates with the Manager via Callosum RPC. This document describes the request ID tracing implementation for the Agent, including the proposed RPCFunctionRegistryV3.

## Callosum Constraints

Callosum is the RPC library used for Manager ↔ Agent communication. Key constraints:

1. **No separate header channel**: Unlike HTTP, Callosum doesn't have a metadata/header mechanism separate from the message body
2. **Binary protocol**: Messages are serialized (msgpack) and sent as single payloads
3. **Request-response pattern**: Each RPC call has a request and response

**Implication**: Request metadata (including request_id) must be embedded within the message body structure.

## Current Implementation

### RPCFunctionRegistry (V1)

The original registry returns dict-based responses:

```python
class RPCFunctionRegistry:
    """Legacy registry with dict responses."""
    
    _functions: dict[str, Callable]
    
    async def dispatch(self, method: str, body: dict) -> dict:
        # Extract request_id if present
        request_id = body.get("request_id")
        if request_id:
            _request_id_var.set(request_id)
        
        func = self._functions[method]
        result = await func(*body.get("args", []), **body.get("kwargs", {}))
        return result  # Returns arbitrary dict
```

**Issues**:
- No structured response format
- request_id extraction is ad-hoc
- No type safety

### RPCFunctionRegistryV2

Introduced DTO-based responses:

```python
class RPCFunctionRegistryV2:
    """Registry with structured DTO responses."""
    
    _functions: dict[str, Callable[..., AbstractAgentResp]]
    
    async def dispatch(self, method: str, body: dict) -> dict:
        request_id = body.get("request_id")
        if request_id:
            _request_id_var.set(request_id)
        
        func = self._functions[method]
        response: AbstractAgentResp = await func(
            *body.get("args", []),
            **body.get("kwargs", {}),
        )
        return response.to_response()
```

**Improvements over V1**:
- Structured response via `AbstractAgentResp`
- Still extracts request_id from body root

**Remaining Issues**:
- request_id mixed with business data
- No extensible header structure for future tracing needs

## Proposed: RPCFunctionRegistryV3

### Design Goals

1. **Separate concerns**: Headers (metadata) separated from args/kwargs (business data)
2. **Extensibility**: Header structure supports future additions (correlation_id, trace_id)
3. **Type safety**: Pydantic models for validation
4. **Backward compatibility**: Graceful handling of V2 requests

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
        "request_id": "req-550e8400-e29b-41d4-a716-446655440000",
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
        "request_id": "req-550e8400-e29b-41d4-a716-446655440000"
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
        "request_id": "req-550e8400-e29b-41d4-a716-446655440000"
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
class RPCFunctionRegistryV3:
    """
    V3 registry with structured headers and extensible tracing.
    """
    
    _functions: dict[str, Callable[..., Awaitable[AbstractAgentResp]]]
    
    def register(self, name: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            self._functions[name] = func
            return func
        return decorator
    
    async def dispatch(self, method: str, raw_body: dict) -> dict:
        """
        Dispatch RPC call with V3 protocol.
        Falls back to V2 format detection for compatibility.
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
        Parse request with V3/V2 format detection.
        """
        if "headers" in raw_body:
            # V3 format
            return RPCRequest.model_validate(raw_body)
        else:
            # V2 fallback: extract request_id from body root
            return RPCRequest(
                headers=RPCHeaders(request_id=raw_body.get("request_id")),
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
registry = RPCFunctionRegistryV3()

@registry.register("create_kernel")
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
        "rpc_version": 3,  # Supports V3 protocol
        "features": ["request_tracing", "structured_errors"],
    },
}

# Manager side
if agent.capabilities.get("rpc_version", 1) >= 3:
    # Use V3 format
    request_body = RPCRequest(
        headers=RPCHeaders(request_id=current_request_id()),
        args=args,
        kwargs=kwargs,
    ).model_dump()
else:
    # Use V2 format
    request_body = {
        "request_id": current_request_id(),
        "args": args,
        "kwargs": kwargs,
    }
```

### Option B: Dual Format (Transition Period)

Manager sends both formats during migration:

```python
request_body = {
    "headers": {"request_id": current_request_id()},  # V3
    "request_id": current_request_id(),                # V2 fallback
    "args": args,
    "kwargs": kwargs,
}
```

V3 Agents use `headers`, V2 Agents use root `request_id`.

## Backward Compatibility

### Agent Receiving Requests

| Manager Version | Request Format | Agent V2 | Agent V3 |
|-----------------|----------------|----------|----------|
| Pre-V3 | V2 (root request_id) | ✓ Works | ✓ Falls back |
| V3+ | V3 (headers) | ✓ Ignores headers | ✓ Works |
| V3+ (dual) | Both formats | ✓ Uses root | ✓ Uses headers |

### Manager Processing Responses

| Agent Version | Response Format | Manager V2 | Manager V3 |
|---------------|-----------------|------------|------------|
| V2 | Dict (no headers) | ✓ Works | ✓ Falls back |
| V3 | With headers | Ignores | ✓ Works |

## Migration Strategy

### Phase 1: Add V3 to Agent (Non-breaking)

1. Implement `RPCFunctionRegistryV3` with V2 fallback
2. Agent accepts both formats
3. No Manager changes required

### Phase 2: Update Manager to Send V3

1. Manager detects Agent version via capabilities
2. Send V3 format to V3 Agents
3. Continue V2 format for older Agents

### Phase 3: Deprecate V2

1. Log warnings when V2 fallback is used
2. Set timeline for V2 removal

### Phase 4: Remove V2 (Breaking)

1. Remove V2 compatibility code
2. Require V3 protocol

## Implementation Checklist

- [ ] Add `RPCHeaders` model to `ai.backend.common`
- [ ] Add `RPCRequest` and `RPCResponse` models
- [ ] Implement `RPCFunctionRegistryV3`
- [ ] Add V2 fallback detection in V3 registry
- [ ] Update Agent server to use V3 registry
- [ ] Add capability advertisement for rpc_version
- [ ] Update Manager `PeerInvoker` for V3 format
- [ ] Add version detection in Manager
- [ ] Add integration tests for V2 ↔ V3 compatibility
- [ ] Add metrics for protocol version usage
