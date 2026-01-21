# Storage-Proxy Component

Storage-Proxy handles file storage operations for virtual folders (vfolders). It provides HTTP APIs for file upload, download, and management operations.

## Current Implementation

Storage-Proxy already uses the standard `request_id_middleware` for HTTP requests:

```python
# ai/backend/storage/server.py
from ai.backend.common.logging_utils import request_id_middleware

app = web.Application(middlewares=[
    request_id_middleware,
    # ... other middlewares
])
```

## Request Flow

### Incoming Requests from Manager

```
Manager                       Storage-Proxy
   │                               │
   │  POST /folders/upload         │
   │  X-Request-ID: req-123        │
   ├──────────────────────────────▶│
   │                               │
   │         middleware extracts   │
   │         req-123 and binds     │
   │         to context            │
   │                               │
   │         All logs include      │
   │         request_id: req-123   │
   │                               │
   │  200 OK                       │
   │  X-Backend-Request-ID:        │
   │    req-123                    │
   │◀──────────────────────────────┤
```

### Direct Client Requests

Clients may also call Storage-Proxy directly (for presigned URLs, etc.):

```
Client                        Storage-Proxy
   │                               │
   │  GET /download/...            │
   │  (no X-Request-ID)            │
   ├──────────────────────────────▶│
   │                               │
   │         middleware generates  │
   │         new request_id        │
   │                               │
   │  200 OK                       │
   │  X-Backend-Request-ID:        │
   │    req-{generated}            │
   │◀──────────────────────────────┤
```

## Background Operations

Storage-Proxy performs background operations that need their own request IDs.
The `@with_request_id_context` decorator automatically generates one if not present:

### File Cleanup Tasks

```python
from ai.backend.common.logging_utils import with_request_id_context

@with_request_id_context
async def cleanup_expired_uploads() -> None:
    """
    Periodically clean up incomplete/expired uploads.
    """
    log.info("Starting upload cleanup")
    # request_id is bound for log correlation
    
    for upload in await find_expired_uploads():
        await delete_upload(upload.id)
        log.info("Deleted expired upload", upload_id=upload.id)
```

### Storage Sync Operations

```python
@with_request_id_context
async def sync_vfolder_quota() -> None:
    """
    Sync vfolder quota with actual disk usage.
    """
    log.info("Starting quota sync")
    
    for vfolder in await list_vfolders():
        actual_size = await calculate_vfolder_size(vfolder)
        await update_quota(vfolder.id, actual_size)
```

### Clone/Copy Operations

Long-running operations that span multiple async boundaries:

```python
async def clone_vfolder(
    source_id: VFolderID,
    dest_id: VFolderID,
) -> None:
    # Request ID should be preserved from the initiating request
    request_id = current_request_id()
    log.info(
        "Starting vfolder clone",
        source=source_id,
        dest=dest_id,
    )
    
    async for file in list_files(source_id):
        await copy_file(source_id, dest_id, file)
        log.debug("Copied file", file=file.name)
```

## Internal Operations

### Storage Backend Calls

When Storage-Proxy communicates with storage backends (S3, NFS, etc.), request ID can be included in client-side logging:

```python
async def upload_to_s3(
    bucket: str,
    key: str,
    data: bytes,
) -> None:
    request_id = current_request_id()
    
    log.info(
        "Uploading to S3",
        bucket=bucket,
        key=key,
        size=len(data),
    )
    
    await s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
    )
    
    log.info("Upload complete", bucket=bucket, key=key)
```

Note: S3/cloud storage APIs typically don't support custom trace headers in the same way, but local logging with request_id enables correlation.

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| HTTP middleware | ✓ Implemented | Standard `request_id_middleware` |
| Response header | ✓ Implemented | `X-Backend-Request-ID` in responses |
| Background tasks | △ Partial | Some tasks may need `@with_request_id_context` |
| Internal logging | ✓ Implemented | Uses `current_request_id()` |

## Implementation Checklist

- [x] `request_id_middleware` applied to main app
- [x] Response includes `X-Backend-Request-ID`
- [ ] Audit background tasks for `@with_request_id_context`
- [ ] Add `@with_request_id_context` to cleanup tasks
- [ ] Add `@with_request_id_context` to sync operations
- [ ] Verify long-running operations preserve request_id

## Configuration

No special configuration required. Storage-Proxy inherits the standard request ID handling from common infrastructure.

## Testing

### Unit Tests

```python
async def test_request_id_propagation():
    """Verify request ID is extracted from header."""
    async with create_test_client(app) as client:
        response = await client.get(
            "/health",
            headers={"X-Request-ID": "test-req-123"},
        )
        assert response.headers["X-Backend-Request-ID"] == "test-req-123"

async def test_request_id_generation():
    """Verify request ID is generated if not provided."""
    async with create_test_client(app) as client:
        response = await client.get("/health")
        assert "X-Backend-Request-ID" in response.headers
        assert response.headers["X-Backend-Request-ID"].startswith("req-")
```

### Integration Tests

```python
async def test_manager_storage_tracing():
    """Verify request ID flows from Manager to Storage-Proxy."""
    request_id = "req-integration-test"
    
    # Manager makes call to Storage-Proxy
    async with manager_client.session() as session:
        with bind_request_id(request_id):
            response = await call_storage_proxy(session, "/folders/list", {})
    
    # Verify Storage-Proxy received and echoed request ID
    assert response.headers["X-Backend-Request-ID"] == request_id
    
    # Verify logs contain request_id (check log output)
```
