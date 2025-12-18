# Storage Inter-Component DTOs (Legacy)

**This is a legacy module for inter-component communication. New DTOs should be added to `ai.backend.common.dto/storage/` instead.**

This module contains Data Transfer Objects (DTOs) that are used for communication between the Storage component and other Backend.AI components (primarily Manager).

## Purpose

DTOs in `ai.backend.storage.dto` were originally created for:
- RPC communication between Storage and Manager components
- Storage API request/response schemas
- Inter-component data exchange

**Migration Status:**
- **Legacy Location**: This module exists for backward compatibility
- **Current Practice**: Use `ai.backend.common.dto/storage/` for new inter-component DTOs
- **Recommendation**: Use Pydantic models for better validation and type safety
- **Future**: Gradually migrate existing DTOs to `common/dto/storage/`

For storage-internal operations (not exposed to other components), create DTOs in storage service modules directly or use inline dataclasses.

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

**⚠️ DEPRECATED: Do NOT add new DTOs to `storage/dto/`**

This module is in maintenance mode. For new DTOs:

**✅ Add to `ai.backend.common.dto/storage/` when:**
- The DTO is used in RPC calls between Storage and Manager/Agent
- The DTO is part of the Storage RPC API
- Other components need to reference the data structure
- The DTO represents a storage API contract

**✅ Use inline dataclasses or service-specific modules when:**
- The DTO is used only within Storage's internal services
- The DTO represents internal storage backend operations
- The DTO is used for storage driver coordination
- No other component needs to reference it

**Existing DTOs in this module:**
- Maintain for backward compatibility
- Use Pydantic when adding fields or modifying existing DTOs
- Plan migration to `common/dto/storage/` for frequently used DTOs

## Guidelines

### 1. Use Pydantic for Inter-Component DTOs (Recommended)

For inter-component communication, use Pydantic models for validation and type safety:

```python
from __future__ import annotations

from pydantic import BaseModel, Field

class VolumeCreateRequest(BaseModel):
    """Request to create a volume (inter-component RPC).

    Used by Manager to request volume creation from Storage.
    """

    volume_id: str = Field(..., description="Unique volume identifier")
    owner_id: str = Field(..., description="Owner user ID")
    backend_type: str = Field(..., description="Storage backend type")
    quota_bytes: int | None = Field(None, description="Quota in bytes")

# For storage-internal operations, use dataclasses in service modules
```

### 2. Immutability

Inter-component DTOs should be immutable when possible:

```python
from pydantic import BaseModel, ConfigDict

class FileTransferRequest(BaseModel):
    """Request for file transfer between volumes (inter-component RPC)."""

    model_config = ConfigDict(frozen=True)

    source_volume_id: str
    source_path: str
    destination_volume_id: str
    destination_path: str
```

### 3. Path Handling

Use string paths in inter-component DTOs for serialization compatibility:

```python
from pydantic import BaseModel, Field

class VolumePathRequest(BaseModel):
    """Request for volume path operations (inter-component RPC)."""

    volume_id: str = Field(..., description="Volume identifier")
    path: str = Field(..., description="Relative path within volume")
    # Use strings for RPC serialization, convert to Path internally
```

### 4. Backend-Agnostic Design

Inter-component DTOs should abstract storage backend details:

```python
from typing import Literal
from pydantic import BaseModel, Field

class VolumeQuotaResponse(BaseModel):
    """Volume quota information (inter-component RPC response).

    Abstracts quota details regardless of backend type.
    """

    volume_id: str = Field(..., description="Volume identifier")
    used_bytes: int = Field(..., description="Used space in bytes")
    quota_bytes: int | None = Field(None, description="Quota in bytes (None = unlimited)")
    file_count: int = Field(..., description="Number of files")
```

### 5. Documentation

All inter-component DTOs must have comprehensive documentation:

```python
from pydantic import BaseModel, Field

class VolumeCreateRequest(BaseModel):
    """Request to create a new volume.

    This DTO is sent from Manager to Storage via RPC
    to initiate volume creation.

    Used by:
    - Manager: Session creation flow
    - Manager: Admin volume management API
    """

    volume_id: str = Field(..., description="Unique volume identifier")
    owner_id: str = Field(..., description="User ID of the volume owner")
    quota_bytes: int | None = Field(
        None,
        description="Maximum size in bytes (None for unlimited)",
    )
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Manager Component                                            │
│   - Calls Storage via RPC                                    │
│   - SHOULD use: common/dto/storage DTOs (new)               │
│   - MAY use: storage/dto DTOs (legacy, backward compat)     │
└─────────────────────┬───────────────────────────────────────┘
                      │ RPC Communication
                      │ (Pydantic models for validation)
┌─────────────────────▼───────────────────────────────────────┐
│ Storage RPC Handler (api/*)                                  │
│   - Receives DTOs from storage/dto (legacy) or               │
│     common/dto/storage (new)                                 │
│   - Converts to internal dataclasses if needed              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Storage Service Layer (services/*)                           │
│   - Uses internal dataclasses for business logic            │
│   - No dependency on RPC DTOs                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Storage Backends (storages/*)                                │
│   - Backend-specific implementations                         │
│   - Returns internal dataclasses                             │
└─────────────────────────────────────────────────────────────┘
```

## Examples

### Good Example: Legacy Inter-Component DTO (Pydantic)

```python
# src/ai/backend/storage/dto/volume.py
from __future__ import annotations

from pydantic import BaseModel, Field

class CreateVolumeRequest(BaseModel):
    """RPC request to create a volume (legacy location).

    TODO: Migrate to ai.backend.common.dto/storage/request.py
    """

    volume_id: str = Field(..., description="Unique volume identifier")
    owner_id: str = Field(..., description="Owner user ID")
    quota_bytes: int | None = Field(None, description="Quota in bytes")
```

### Better Example: Migrated to common/dto

```python
# ✅ BETTER: In ai.backend.common.dto/storage/request.py
# Other components can import this more easily

from pydantic import BaseModel, Field

class CreateVolumeRequest(BaseModel):
    """RPC request to create a volume.

    Used by Manager to request volume creation from Storage.
    """

    volume_id: str = Field(..., description="Unique volume identifier")
    owner_id: str = Field(..., description="Owner user ID")
    quota_bytes: int | None = Field(None, description="Quota in bytes")
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

## Migration Strategy

When migrating DTOs from `storage/dto/` to `common/dto/storage/`:

1. **Identify high-traffic DTOs** used in RPC calls
2. **Copy to `common/dto/storage/`** with proper documentation
3. **Add backward compatibility** in legacy location:
   ```python
   # In ai.backend.storage.dto/volume.py
   # TODO: Deprecated - use ai.backend.common.dto.storage.volume instead
   from ai.backend.common.dto.storage.volume import CreateVolumeRequest

   __all__ = ["CreateVolumeRequest"]
   ```
4. **Update imports** in Manager and other components
5. **Document migration** in changelog
6. **Remove legacy module** after deprecation period

## See Also

- [Shared DTOs README](../../common/dto/README.md) - Inter-component DTOs
- [Storage README](../README.md) - Storage component overview
