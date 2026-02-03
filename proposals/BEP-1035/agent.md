# Agent Component

The Agent component handles compute kernel management and communicates with the Manager via Callosum RPC.

## Callosum Constraints

Callosum is the RPC library used for Manager ↔ Agent communication:

- **No separate header channel**: Unlike HTTP, no metadata mechanism separate from the message body
- **Binary protocol**: Messages are serialized (msgpack) as single payloads

**Implication**: Request metadata (including request_id) must be embedded within the message body.

## Current State

- Agent RPC does not support request_id propagation
- No structure for metadata in request/response

## Proposed Design

### Request/Response Structure

Embed headers in the message body:

**Request:**
```json
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "args": ["kernel-id-123"],
    "kwargs": {"timeout": 30}
}
```

**Response (success):**
```json
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "result": {"kernel_id": "kernel-abc", "status": "running"}
}
```

**Response (error):**
```json
{
    "headers": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "error": {"type": "KernelNotFoundError", "message": "..."}
}
```

### Headers Model (Example)

```python
# Pydantic model for RPC headers
class RPCHeadersModel(BaseModel):
    request_id: str | None = None
    # Extensible for future tracing
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    class Config:
        extra = "allow"
```

## Backward Compatibility

### Request Format Detection

| Request Format | Detection | Handling |
|----------------|-----------|----------|
| With `headers` | `"headers" in body` | Extract request_id |
| Without `headers` | Legacy format | Auto-generate request_id |

Legacy Agents ignore unknown `headers` field. New Agents use it for tracing.

## Migration Strategy

1. **Phase 1**: Agent accepts both formats (non-breaking)
2. **Phase 2**: Manager sends new format to capable Agents
3. **Phase 3**: Deprecation warnings for legacy format
4. **Phase 4**: Remove legacy support (breaking)

## Implementation Checklist

- [ ] Add RPC headers model to Agent
- [ ] Update Agent RPC dispatcher for new format
- [ ] Add legacy format fallback
- [ ] Update Manager to send headers
- [ ] Add capability advertisement

## References

- [Callosum](https://github.com/lablup/callosum) - RPC Transport Library for asyncio
