# Storage Component-Internal DTOs

This module contains Data Transfer Objects (DTOs) that are used exclusively within the Storage component.

## Purpose

DTOs in `ai.backend.storage.dto` are internal data structures for:
- Storage backend operations
- Volume management internal logic
- Storage quota calculations
- File operation contexts
- Internal storage service coordination

These DTOs are **NOT** exposed to other components through RPC. For RPC interfaces with Manager or other components, use `ai.backend.common.dto/storage/`.

## Organization

DTOs are organized by functional area within the storage component:

```
dto/
├── volume/            # Volume-specific DTOs
├── file/              # File operation DTOs
├── quota/             # Quota management DTOs
└── ...                # Other storage domains
```

## When to Add DTOs Here

**✅ Add to `storage/dto/` when:**
- The DTO is used only within Storage's internal services
- The DTO represents internal storage backend operations
- The DTO is used for storage driver coordination
- The DTO aggregates data from multiple storage backends
- No other component needs to reference it
- Changes affect only the Storage component

**❌ Do NOT add to `storage/dto/` when:**
- The DTO is used in RPC calls from Manager or Agent
- The DTO is part of the Storage RPC API
- Other components need the same data structure
- The DTO represents a public storage contract

For shared DTOs, use `ai.backend.common.dto/storage/` instead.

## Guidelines

### 1. Use Dataclasses for Internal DTOs

Prefer dataclasses for simplicity in internal storage DTOs:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class VolumeOperationContext:
    """Internal context for volume operations.

    Used by storage services to coordinate operations
    across different storage backends.
    """

    volume_id: str
    mount_path: Path
    backend_type: str
    owner_id: str
    quota_bytes: int | None = None
```

### 2. Immutability

DTOs should be immutable to prevent race conditions in async operations:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class FileTransferMetadata:
    """Metadata for file transfer operations (internal)."""

    source_path: str
    destination_path: str
    file_size: int
    checksum: str
    transfer_id: str
```

### 3. Path Handling

Use `pathlib.Path` for filesystem paths in internal DTOs:

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class StorageLocation:
    """Internal representation of a storage location."""

    backend_id: str
    mount_point: Path
    relative_path: Path

    @property
    def absolute_path(self) -> Path:
        """Calculate absolute path."""
        return self.mount_point / self.relative_path
```

### 4. Storage Backend Abstraction

DTOs should abstract storage backend details:

```python
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class StorageQuotaInfo:
    """Internal quota information from storage backend.

    Abstracts quota details regardless of backend type
    (POSIX, S3, Ceph, etc.).
    """

    volume_id: str
    used_bytes: int
    quota_bytes: int | None  # None = unlimited
    file_count: int
    backend_type: Literal["posix", "s3", "ceph", "hammerspace"]
```

### 5. Async Operation Context

For async storage operations, include operation context:

```python
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai.backend.storage.storages.base import BaseStorageBackend

@dataclass(frozen=True)
class AsyncCopyContext:
    """Context for async file copy operations.

    Used internally to track long-running copy operations
    across storage backends.
    """

    operation_id: str
    source_backend: BaseStorageBackend
    destination_backend: BaseStorageBackend
    source_path: str
    destination_path: str
    total_bytes: int
    started_at: float
```

### 6. Error Context

Include context for error reporting:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class StorageOperationError:
    """Internal error context for storage operations.

    Provides detailed context for debugging storage failures.
    """

    operation: str
    volume_id: str
    path: str
    backend_type: str
    error_message: str
    error_code: str | None = None
```

## Relationship with RPC Layer

```
┌─────────────────────────────────────────────────────────────┐
│ Manager Component                                            │
│   - Calls Storage via RPC                                    │
│   - Uses common/dto/storage DTOs                            │
└─────────────────────┬───────────────────────────────────────┘
                      │ RPC (uses common/dto/storage)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Storage RPC Handler (api/*)                                  │
│   - Converts between RPC DTOs and Internal DTOs             │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Storage Service Layer (services/*)                           │
│   - Uses storage/dto DTOs internally                         │
│   - Coordinates storage backend operations                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Storage Backends (storages/*)                                │
│   - Implements storage operations                            │
│   - Returns internal DTOs                                    │
└─────────────────────────────────────────────────────────────┘
```

## Examples

### Good Example: Internal DTO

```python
# src/ai/backend/storage/dto/volume/operation.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class VolumeSnapshotContext:
    """Internal context for volume snapshot operations.

    Used by storage backends to coordinate snapshot creation
    and restoration.
    """

    volume_id: str
    snapshot_id: str
    snapshot_path: Path
    created_at: float
    metadata: dict[str, str]
```

### Bad Example: Should be in common/dto

```python
# ❌ WRONG: This is used in RPC from Manager
# Should be in ai.backend.common.dto/storage/request.py

from pydantic import BaseModel

class CreateVolumeRequest(BaseModel):
    """RPC request to create a volume."""  # This is external!

    volume_id: str
    owner_id: str
    quota_bytes: int
```

### Converting Between RPC and Internal DTOs

```python
# In storage RPC handler
from ai.backend.common.dto.storage.request import CreateVolumeRequest
from ai.backend.storage.dto.volume.operation import VolumeOperationContext

async def create_volume_rpc_handler(
    request: CreateVolumeRequest  # External RPC DTO
) -> None:
    # Convert to internal DTO
    context = VolumeOperationContext(
        volume_id=request.volume_id,
        mount_path=Path(f"/volumes/{request.volume_id}"),
        backend_type="posix",  # Determined internally
        owner_id=request.owner_id,
        quota_bytes=request.quota_bytes,
    )

    # Use internal DTO in service layer
    await storage_service.create_volume(context)
```

## Storage Backend Implementations

When implementing storage backends, use internal DTOs for consistency:

```python
from abc import ABC, abstractmethod
from ai.backend.storage.dto.volume.operation import VolumeOperationContext

class BaseStorageBackend(ABC):
    """Base class for storage backends."""

    @abstractmethod
    async def create_volume(
        self,
        context: VolumeOperationContext,  # Internal DTO
    ) -> None:
        """Create a volume in this storage backend."""
        ...
```

## Testing

Internal DTOs should be tested for:
- Immutability (frozen=True works correctly)
- Type validation
- Conversion logic to/from RPC DTOs

```python
import pytest
from ai.backend.storage.dto.volume.operation import VolumeOperationContext

def test_volume_operation_context_immutable() -> None:
    """Test that VolumeOperationContext is immutable."""
    context = VolumeOperationContext(
        volume_id="vol-123",
        mount_path=Path("/volumes/vol-123"),
        backend_type="posix",
        owner_id="user-456",
        quota_bytes=1000000,
    )

    # Should raise error when trying to modify
    with pytest.raises(AttributeError):
        context.volume_id = "vol-456"  # type: ignore
```

## See Also

- [Shared DTOs README](../../common/dto/README.md) - Inter-component DTOs
- [Storage README](../README.md) - Storage component overview
