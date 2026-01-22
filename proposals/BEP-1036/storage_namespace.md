# StorageNamespace Quota

Quota system for default artifact storage (Reservoir archive storage).

## Overview

When `vfolder_id` is not provided, artifacts are stored in the configured Reservoir archive storage.
This storage is managed by `StorageNamespaceRow` and supports two backend types:

- **Object Storage** (MinIO, S3, etc.)
- **VFS Storage** (local/network filesystem)

## Data Model

### Current Structure

```
┌─────────────────────────┐
│ object_storage          │
├─────────────────────────┤
│ id                      │◄─────┐
│ name                    │      │
│ host                    │      │
│ endpoint                │      │
│ access_key              │      │
│ secret_key              │      │
└─────────────────────────┘      │
                                  │ storage_id (object_storage)
┌─────────────────────────┐      │
│ storage_namespace       │──────┘
├─────────────────────────┤
│ id                      │◄─────────────────────────────────────┐
│ storage_id              │                                      │
│ namespace (bucket name) │                                      │
└─────────────────────────┘                                      │
                                                                  │
┌─────────────────────────┐      ┌─────────────────────────┐     │
│ vfs_storage             │      │ association_artifacts_  │     │
├─────────────────────────┤      │ storages                │     │
│ id                      │◄──┐  ├─────────────────────────┤     │
│ name                    │   │  │ id                      │     │
│ host                    │   │  │ artifact_revision_id ───┼──┐  │
│ base_path               │   │  │ storage_namespace_id ───┼──┼──┘
└─────────────────────────┘   │  │ storage_type            │  │
                              │  └─────────────────────────┘  │
                              │         │                     │
                              │         │ "object_storage"    │
                              │         │ or "vfs_storage"    │
                              │         │                     │
                              └─────────┘                     │
                                storage_id (vfs)              │
                                                              │
┌─────────────────────────┐                                   │
│ artifact_revisions      │                                   │
├─────────────────────────┤                                   │
│ id ◄────────────────────┼───────────────────────────────────┘
│ artifact_id             │
│ version                 │
│ size                    │  ◄── Individual revision size
│ status                  │
└─────────────────────────┘
```

### Proposed: Add max_size

```
┌─────────────────────────┐
│ storage_namespace       │
├─────────────────────────┤
│ id                      │
│ storage_id              │
│ namespace               │
│ max_size (NEW)          │  ◄── NULL = unlimited, in bytes
└─────────────────────────┘
```

## Scenarios by Storage Type

### Object Storage (MinIO/S3)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Object Storage Scenario                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Reservoir Config                                                        │
│  ┌────────────────────────────────────────┐                             │
│  │ storage_type: "object_storage"         │                             │
│  │ archive_storage: "minio-main"          │                             │
│  │ bucket_name: "artifacts"               │ ─── namespace               │
│  └────────────────────────────────────────┘                             │
│                                                                          │
│  import_revision() flow                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 1. namespace = reservoir_config.bucket_name                      │   │
│  │                                                                  │   │
│  │ 2. object_storage = get_by_name("minio-main")                    │   │
│  │    → ObjectStorageRow { id, host, endpoint, ... }                │   │
│  │                                                                  │   │
│  │ 3. storage_namespace = get_by_storage_and_namespace(             │   │
│  │        storage_id=object_storage.id,                             │   │
│  │        namespace="artifacts"                                     │   │
│  │    )                                                             │   │
│  │    → StorageNamespaceRow { id, max_size, ... }                   │   │
│  │                                                                  │   │
│  │ 4. quota_check(storage_namespace.id, revision.size)              │   │
│  │                                                                  │   │
│  │ 5. storage_proxy.import_huggingface_models(...)                  │   │
│  │    → Files stored in MinIO bucket                                │   │
│  │                                                                  │   │
│  │ 6. associate_artifact_with_storage(                              │   │
│  │        revision_id, namespace_id, "object_storage"               │   │
│  │    )                                                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Physical storage location                                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ MinIO: s3://artifacts/{revision_id}/model.safetensors            │   │
│  │                ▲                                                 │   │
│  │                │                                                 │   │
│  │        bucket_name (namespace)                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### VFS Storage (Filesystem)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          VFS Storage Scenario                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Reservoir Config                                                        │
│  ┌────────────────────────────────────────┐                             │
│  │ storage_type: "vfs_storage"            │                             │
│  │ archive_storage: "nfs-models"          │                             │
│  │ subpath: "reservoir/artifacts"         │ ─── namespace               │
│  └────────────────────────────────────────┘                             │
│                                                                          │
│  import_revision() flow                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 1. namespace = reservoir_config.subpath                          │   │
│  │                                                                  │   │
│  │ 2. vfs_storage = get_by_name("nfs-models")                       │   │
│  │    → VFSStorageRow { id, host, base_path, ... }                  │   │
│  │                                                                  │   │
│  │ 3. storage_namespace = get_by_storage_and_namespace(             │   │
│  │        storage_id=vfs_storage.id,                                │   │
│  │        namespace="reservoir/artifacts"                           │   │
│  │    )                                                             │   │
│  │    → StorageNamespaceRow { id, max_size, ... }                   │   │
│  │                                                                  │   │
│  │ 4. quota_check(storage_namespace.id, revision.size)              │   │
│  │                                                                  │   │
│  │ 5. storage_proxy.import_huggingface_models(...)                  │   │
│  │    → Files stored on NFS                                         │   │
│  │                                                                  │   │
│  │ 6. associate_artifact_with_storage(                              │   │
│  │        revision_id, namespace_id, "vfs_storage"                  │   │
│  │    )                                                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Physical storage location                                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ NFS: /mnt/nfs/reservoir/artifacts/{revision_id}/model.safetensors│   │
│  │              ▲                                                   │   │
│  │              │                                                   │   │
│  │        base_path + subpath (namespace)                           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quota Check Logic

```python
async def check_storage_namespace_quota(
    self,
    namespace_id: uuid.UUID,
    additional_size: int,
) -> None:
    """
    Check the quota for a StorageNamespace.

    Same logic applies regardless of storage_type (object_storage/vfs_storage).
    """
    # 1. Get max_size from namespace
    namespace = await self._storage_namespace_repo.get_by_id(namespace_id)

    # NULL means unlimited
    if namespace.max_size is None:
        return

    # 2. Aggregate current usage (sum of revision sizes linked via association table)
    usage = await self._storage_namespace_repo.get_usage(namespace_id)

    # 3. Check if limit would be exceeded
    if usage.total_size + additional_size > namespace.max_size:
        raise StorageNamespaceQuotaExceededError(
            namespace_id=namespace_id,
            current_size=usage.total_size,
            max_size=namespace.max_size,
            requested_size=additional_size,
        )
```

### Usage Aggregation Query

```sql
SELECT
    COALESCE(SUM(ar.size), 0) as total_size,
    COUNT(ar.id) as revision_count
FROM association_artifacts_storages aas
JOIN artifact_revisions ar ON aas.artifact_revision_id = ar.id
WHERE aas.storage_namespace_id = :namespace_id
```

## Object Storage vs VFS Storage Comparison

| Aspect | Object Storage | VFS Storage |
|--------|---------------|-------------|
| Config key | `bucket_name` | `subpath` |
| Reference table | `object_storage` | `vfs_storage` |
| `storage_type` value | `"object_storage"` | `"vfs_storage"` |
| Physical storage | S3 bucket | Filesystem path |
| Quota management | **Same** (StorageNamespaceRow.max_size) |
| Usage aggregation | **Same** (association table based) |

## API

### GET /storage-namespaces/{id}/usage

```json
{
  "namespace_id": "550e8400-e29b-41d4-a716-446655440000",
  "storage_type": "object_storage",
  "namespace": "artifacts",
  "total_size": 10737418240,
  "max_size": 107374182400,
  "revision_count": 42,
  "utilization_percent": 10.0
}
```

### PATCH /storage-namespaces/{id}/quota

```json
{ "max_size": 107374182400 }
```

Or set to unlimited:

```json
{ "max_size": null }
```
