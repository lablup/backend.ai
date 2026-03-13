# StorageNamespace Quota

Quota system for default artifact storage (Reservoir archive storage).

## Overview

When `vfolder_id` is not provided, artifacts are stored in the configured Reservoir archive storage.
This storage is managed by `StorageNamespaceRow` and supports two backend types:

- **Object Storage** (MinIO, S3, etc.)
- **VFS Storage** (local/network filesystem)

Both types share the same quota mechanism via `StorageNamespaceRow.max_size`.

## Data Model

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
│ namespace               │                                      │
│ max_size (NEW)          │  ◄── NULL = unlimited, in bytes      │
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

## Backend Type Differences

| Aspect | Object Storage | VFS Storage |
|--------|---------------|-------------|
| Config key for namespace | `bucket_name` | `subpath` |
| Reference table | `object_storage` | `vfs_storage` |
| Physical storage | S3 bucket (e.g., `s3://artifacts/`) | Filesystem path (e.g., `/mnt/nfs/artifacts/`) |

Quota management and usage aggregation are identical for both types.

## Quota Check Logic

```python
async def check_storage_namespace_quota(
    self,
    namespace_id: uuid.UUID,
    additional_size: int,
) -> None:
    """
    Check the quota for a StorageNamespace.
    Same logic applies regardless of storage_type.
    """
    namespace = await self._storage_namespace_repo.get_by_id(namespace_id)

    # NULL means unlimited
    if namespace.max_size is None:
        return

    # Aggregate current usage via association table
    usage = await self._storage_namespace_repo.get_usage(namespace_id)

    if usage.total_size + additional_size > namespace.max_size:
        raise StorageNamespaceQuotaExceededError(...)
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
