---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2026-01-06
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# VFolder Destination Support for Artifact Import

## Motivation

Currently, when users import artifacts via the `import_artifacts` API, the download destination is determined by the pre-configured `artifact_storage` in the system settings. This limits flexibility as users cannot choose where to store their imported models.

### Current Structure

The current artifact import flow works as follows:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client (WebUI)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ import_artifacts(artifactRevisionIds)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 Manager                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  ArtifactRevisionService.import_revision()                            │  │
│  │    1. Load artifact & revision data from DB                           │  │
│  │    2. Read reservoir_config from settings                             │  │
│  │    3. Resolve storage_host from artifact_storage config               │  │
│  │    4. Build storage_step_mappings (DOWNLOAD, VERIFY, ARCHIVE)         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ POST /import (with storage_step_mappings)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Storage Proxy                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Import Pipeline                                                      │  │
│  │    1. DOWNLOAD: Fetch model from external registry (HuggingFace/etc)  │  │
│  │    2. VERIFY: Run verification (malware scan, etc.)                   │  │
│  │    3. ARCHIVE: Store to final destination                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  StoragePool                                                          │  │
│  │    ├── VFSStorage (pre-configured from config file)                   │  │
│  │    └── ObjectStorage (pre-configured from config file)                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         artifact_storage (destination)                      │
│                                                                             │
│   Pre-configured in storage-proxy.toml:                                     │
│   ┌─────────────────────┐    or    ┌─────────────────────┐                  │
│   │  VFS Storage        │          │  Object Storage     │                  │
│   │  /path/to/artifacts │          │  s3://bucket/...    │                  │
│   └─────────────────────┘          └─────────────────────┘                  │
│                                                                             │
│   ⚠️  Cannot download directly to user's VFolder                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Limitation**: Models cannot be downloaded directly to user VFolders, which limits direct integration with Backend.AI's compute sessions and model serving features.

### Use Case: Model Store Integration

On the Model Store page, users need the ability to download models directly to their own vfolders:

1. User clicks the "Import Model to My VFolder" button on the Model Store page.
2. A vfolder selection page is displayed, where the user can create a model-type vfolder or select an existing one.
3. The selected vfolder ID is passed to the `import_artifacts` mutation, and the model is downloaded to that vfolder instead of the preconfigured storage.

This enhancement allows users to download models to:
- Their own VFS (Virtual File System)
- Object storage
- The model store

## Proposed Changes

### API Changes

Add an optional `vfolderId` parameter to the `import_artifacts` API.

### Architecture Changes

#### 1. VolumeStorageAdapter Class

To support vfolder destinations, we need a way to use `AbstractVolume` (the volume backend interface) as an artifact storage target. The existing import pipeline expects `AbstractStorage` interface, so we introduce `VolumeStorageAdapter` that bridges these two interfaces:

```python
class VolumeStorageAdapter(AbstractStorage):
    """
    Adapter that wraps AbstractVolume to implement AbstractStorage interface.

    This enables using any volume backend (VFS, XFS, NetApp, GPFS, Weka, VAST, CephFS, etc.)
    as an artifact storage target without registering to StoragePool.
    """

    def __init__(
        self,
        name: str,
        volume: AbstractVolume,
        vfid: VFolderID,
    ) -> None:
        self._name = name
        self._volume = volume
        self._vfid = vfid

    async def stream_upload(self, filepath: str, data_stream: StreamReader) -> None:
        # Delegates to volume.add_file()
        ...

    async def stream_download(self, filepath: str) -> StreamReader:
        # Delegates to volume.read_file()
        ...

    async def delete_file(self, filepath: str) -> None:
        # Delegates to volume.delete_files()
        ...

    async def get_file_info(self, filepath: str) -> VFSFileMetaResponse:
        # Uses volume.sanitize_vfpath() + aiofiles.os.stat()
        ...
```

**Key advantages of VolumeStorageAdapter:**
- Uses volume's native file operations (add_file, read_file, delete_files, mkdir)
- Supports all vfolder backends uniformly (VFS, XFS, NetApp, GPFS, Weka, VAST, CephFS, etc.)
- No StoragePool registration overhead
- Works with backend-specific quota management
- Delegates all operations to the volume, enabling backend-specific optimizations

#### 2. StorageTarget Class

With `VolumeStorageAdapter`, we can now use volumes as artifact storage. However, the existing import pipeline uses storage names (strings) to look up storages from `StoragePool`. We need a way to pass either:
- A storage name (`str`) for pre-configured storages (existing behavior)
- A `VolumeStorageAdapter` instance for vfolder destinations (new behavior)

The `StorageTarget` class provides this unified interface:

```python
class StorageTarget:
    """
    Wrapper for storage step mapping that can be either a storage name (str)
    or a storage instance (AbstractStorage).

    When str: resolved via storage_pool.get_storage(name)
    When AbstractStorage: used directly (e.g., VolumeStorageAdapter for VFolder imports)
    """

    _value: str | AbstractStorage

    def __init__(self, value: str | AbstractStorage) -> None:
        self._value = value

    def resolve(self, storage_pool: AbstractStoragePool) -> AbstractStorage:
        """Resolve this mapping to an AbstractStorage instance."""
        if isinstance(self._value, AbstractStorage):
            return self._value
        return storage_pool.get_storage(self._value)
```

#### 3. Updated Import Step Context

The `ImportStepContext` is updated to use `StorageTarget` instead of string-only mappings:

```python
@dataclass
class ImportStepContext:
    """Context shared across import steps"""

    model: ModelTarget
    registry_name: str
    storage_pool: AbstractStoragePool
    storage_step_mappings: dict[ArtifactStorageImportStep, StorageTarget]
    step_metadata: dict[str, Any]
```

Import steps now use `StorageTarget.resolve()` to get the storage instance:

```python
# In import step
storage = context.storage_step_mappings[self.step_type].resolve(context.storage_pool)
await storage.stream_upload(filepath, data_stream)
```

### Request Flow

```
API Request with vfolderId
    │
    ▼
Parse vfid from request body
    │
    ▼
Get volume from VolumePool by volume_name
    │
    ▼
Create VolumeStorageAdapter (name: vfolder_storage_{request_id})
    │
    ▼
Create StorageTarget wrapping VolumeStorageAdapter
    │
    ▼
Build storage_step_mappings with StorageTarget instances
    │
    ▼
Start background import task ──► Return response to client
    │
    ▼
[Background task runs...]
    │
    │  Each step resolves storage via:
    │  storage = mapping.resolve(storage_pool)
    │  → Returns VolumeStorageAdapter directly
    │
    ▼
Task completes (success or failure)
```

Using `request_id` in the adapter name ensures uniqueness and traceability.
