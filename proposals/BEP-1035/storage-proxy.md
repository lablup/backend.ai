# Storage-Proxy Component

Storage-Proxy handles file storage operations for virtual folders (vfolders). It provides HTTP APIs for file upload, download, and management operations.

## Proposed Implementation

Storage-Proxy should use the standard `request_id_middleware` for HTTP requests:

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
   │  X-Backend-Request-ID: 550e8400...        │
   ├──────────────────────────────▶│
   │                               │
   │         middleware extracts   │
   │         550e8400... and binds     │
   │         to context            │
   │                               │
   │         All logs include      │
   │         request_id: 550e8400...   │
   │                               │
   │  200 OK                       │
   │  X-Backend-Request-ID:        │
   │    550e8400...                    │
   │◀──────────────────────────────┤
```

### Direct Client Requests

Clients may also call Storage-Proxy directly (for presigned URLs, etc.):

```
Client                        Storage-Proxy
   │                               │
   │  GET /download/...            │
   │  (no X-Backend-Request-ID)            │
   ├──────────────────────────────▶│
   │                               │
   │         middleware generates  │
   │         new request_id        │
   │                               │
   │  200 OK                       │
   │  X-Backend-Request-ID:        │
   │    {generated-uuid}            │
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
| HTTP middleware | Not implemented | Need to add `request_id_middleware` |
| Response header | Not implemented | Need to add `X-Backend-Request-ID` |
| Background tasks | Not implemented | Need `@with_request_id_context` |

## Implementation Checklist

- [ ] Apply `request_id_middleware` to main app
- [ ] Response includes `X-Backend-Request-ID`
- [ ] Add `@with_request_id_context` to cleanup tasks
- [ ] Add `@with_request_id_context` to sync operations
- [ ] Verify long-running operations preserve request_id

## Configuration

No special configuration required. Storage-Proxy inherits the standard request ID handling from common infrastructure.


