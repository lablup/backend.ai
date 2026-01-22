---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2026-01-22
Created-Version: 26.2.0
Target-Version:
Implemented-Version:
---

# Artifact Storage Usage Tracking and Quota Enforcement

## Related Issues

- JIRA: BA-3989 (Epic), BA-3990, BA-3991, BA-3992, BA-3994
- GitHub: #8194

## Motivation

Currently, artifact storage has no usage tracking or capacity limits. When artifacts are imported, they are stored without any visibility into how much space is being consumed or any mechanism to prevent storage exhaustion.

This creates operational risks:

- Storage can be exhausted without warning
- No visibility into storage utilization
- No way to enforce capacity planning or cost control

The artifact import flow supports two storage destinations, and both need quota enforcement:

1. **Default (StorageNamespace)**: No quota system exists
2. **VFolder destination**: Quota system exists (`max_quota_scope_size`) but not integrated into artifact import pre-check

## Current Design

### Existing Data Model

- **`StorageNamespaceRow`**: Tracks basic namespace information (`id`, `storage_id`, `namespace`). No quota-related fields.
- **`ArtifactRevisionRow`**: Already tracks `size` for individual revisions.
- **`AssociationArtifactsStorageRow`**: Links artifact revisions to storage namespaces.

### Dual Storage Destination

The artifact import flow (`import_revision()`) supports two destinations:

| Destination | When | Current Quota |
|-------------|------|---------------|
| StorageNamespace | `vfolder_id` is None | **None** |
| VFolder | `vfolder_id` is provided | `max_quota_scope_size` in resource policy (enforced by storage proxy at write time) |

### VFolder Quota System

VFolders have an existing quota system:

- `VFolderRow.quota_scope_id` → Links to user or project
- Resource policies define `max_quota_scope_size`
- Storage proxy enforces quota at filesystem write time

**Problem**: The artifact import does not pre-check VFolder quota before starting the import. Large imports can fail mid-way when the storage proxy rejects writes due to quota limits.

## Proposed Design

### Overview

Create a unified quota enforcement layer that performs pre-validation before artifact import begins, regardless of storage destination.

### Unified Quota Service

Create `ArtifactStorageQuotaService` that handles both storage destinations with a single entry point:

```python
class ArtifactStorageQuotaService:
    """Unified quota service for artifact storage."""

    async def check_quota(
        self,
        storage_destination: StorageDestination,
        additional_size: int,
    ) -> None:
        match storage_destination:
            case StorageNamespaceDestination(namespace_id):
                await self._check_storage_namespace_quota(namespace_id, additional_size)
            case VFolderDestination(vfolder_id, quota_scope_id):
                await self._check_vfolder_quota(vfolder_id, quota_scope_id, additional_size)
```

### Storage Destination Details

Each storage destination has different quota mechanisms:

| Destination | Quota Source | Usage Source | Details |
|-------------|-------------|--------------|---------|
| StorageNamespace | `StorageNamespaceRow.max_size` (NEW) | Aggregated from `artifact_revisions` via association table | [storage_namespace.md](BEP-1036/storage_namespace.md) |
| VFolder | `max_quota_scope_size` from resource policy | Storage proxy API | [vfolder_storage.md](BEP-1036/vfolder_storage.md) |

### Import Flow Integration

The quota check is integrated into the import flow before any file transfer begins:

```python
async def import_revision(self, action: ImportArtifactRevisionAction) -> ...:
    revision_data = await self._artifact_repository.get_artifact_revision_by_id(...)

    # Determine storage destination and check quota
    if action.vfolder_id:
        destination = VFolderDestination(...)
    else:
        destination = StorageNamespaceDestination(namespace_id=namespace_id)

    if revision_data.size:
        await self._quota_service.check_quota(destination, revision_data.size)

    # Proceed with import only if quota check passes
    ...
```

See [quota-flow.md](BEP-1036/quota-flow.md) for the complete flow diagram.

### Error Types

```python
class StorageQuotaExceededError(BackendError):
    """Base class for quota exceeded errors."""
    pass

class StorageNamespaceQuotaExceededError(StorageQuotaExceededError):
    """Raised when StorageNamespace quota would be exceeded."""
    namespace_id: uuid.UUID
    current_size: int
    max_size: int
    requested_size: int

class VFolderQuotaExceededError(StorageQuotaExceededError):
    """Raised when VFolder quota scope limit would be exceeded."""
    vfolder_id: VFolderID
    quota_scope_id: QuotaScopeID
    current_size: int
    max_size: int
    requested_size: int
```

### REST API Endpoints

#### GET /storage-namespaces/{id}/usage

Returns storage namespace usage statistics.

```json
{
  "namespace_id": "...",
  "total_size": 10737418240,
  "max_size": 107374182400,
  "revision_count": 42,
  "utilization_percent": 10.0
}
```

#### PATCH /storage-namespaces/{id}/quota

Updates quota for a storage namespace. Admin-only.

```json
{ "max_size": 107374182400 }  // or null for unlimited
```

## Migration / Compatibility

### Backward Compatibility

- Existing storage namespaces will have `max_size = NULL` (unlimited)
- No changes to existing import behavior unless quota is explicitly set
- VFolder quota integration uses existing `max_quota_scope_size` from resource policies

### Breaking Changes

None. This is an additive feature.

## Testing Scenarios

### StorageNamespace Quota Tests
- Quota check passes when under limit
- Quota check passes when `max_size` is NULL (unlimited)
- Quota check raises error when limit would be exceeded
- Import flow rejects artifact when quota exceeded

### VFolder Quota Tests
- Pre-check queries storage proxy for current usage
- Quota check uses `max_quota_scope_size` from resource policy
- Import is rejected before starting if quota would be exceeded
- Handles case when resource policy limit is unlimited (-1)

### Unified Flow Tests
- Correct quota system is selected based on `vfolder_id` presence
- Error messages clearly indicate which quota was exceeded

## Future Ideas

### Quota Threshold Notifications

When storage usage approaches the configured limit, the system could notify administrators:

- Threshold levels: 80%, 90%, 95% utilization
- Integration with existing notification system

## References

- [BEP-1019: MinIO Artifact Registry Storage](BEP-1019-minio-artifact-registry-storage.md)
- [StorageNamespace Quota Details](BEP-1036/storage_namespace.md)
- [VFolder Storage Quota Details](BEP-1036/vfolder_storage.md)
- [Quota Flow Diagram](BEP-1036/quota-flow.md)
