# VFolder Storage Quota

Quota system for artifacts stored in a specific VFolder when the user provides a `vfolder_id`.

## Overview

When `vfolder_id` is provided in `import_revision()`, the artifact is stored in the specified VFolder.
VFolders already have an existing quota system via `quota_scope`, but there is **no pre-validation** during artifact import.

**Current Problems:**
- No quota check before import starts
- Large artifact imports can fail mid-way when storage proxy detects quota exceeded
- Failed imports may leave partial downloads

## Data Model

### VFolder Quota Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VFolder Quota Structure                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  quota_scope_id determination based on Ownership Type                    │
│                                                                          │
│  ┌─────────────────────┐          ┌─────────────────────┐               │
│  │ User-owned VFolder  │          │ Project-owned VFolder│              │
│  ├─────────────────────┤          ├─────────────────────┤               │
│  │ ownership_type:     │          │ ownership_type:     │               │
│  │   "user"            │          │   "group"           │               │
│  │                     │          │                     │               │
│  │ quota_scope_id:     │          │ quota_scope_id:     │               │
│  │   "user:{user_uuid}"│          │   "project:{group_id}"              │
│  └──────────┬──────────┘          └──────────┬──────────┘               │
│             │                                 │                          │
│             ▼                                 ▼                          │
│  ┌─────────────────────┐          ┌─────────────────────┐               │
│  │ users               │          │ groups              │               │
│  ├─────────────────────┤          ├─────────────────────┤               │
│  │ uuid                │          │ id                  │               │
│  │ resource_policy ────┼──┐       │ resource_policy ────┼──┐            │
│  └─────────────────────┘  │       └─────────────────────┘  │            │
│                           │                                 │            │
│                           ▼                                 ▼            │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐       │
│  │ user_resource_policies      │  │ project_resource_policies   │       │
│  ├─────────────────────────────┤  ├─────────────────────────────┤       │
│  │ name                        │  │ name                        │       │
│  │ max_vfolder_count           │  │ max_vfolder_count           │       │
│  │ max_quota_scope_size  ◄─────┼──┼── Quota limit (bytes)       │       │
│  │ ...                         │  │ max_network_count           │       │
│  └─────────────────────────────┘  └─────────────────────────────┘       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### VFolder Row Structure

```
┌─────────────────────────┐
│ vfolders                │
├─────────────────────────┤
│ id                      │
│ name                    │
│ host                    │  ─── storage proxy host (e.g., "local:volume1")
│ quota_scope_id          │  ─── "user:{uuid}" or "project:{uuid}"
│ usage_mode              │
│ permission              │
│ ownership_type          │  ─── "user" or "group"
│ user                    │  ─── owner user UUID (for user-owned)
│ group                   │  ─── owner group ID (for project-owned)
│ ...                     │
└─────────────────────────┘
```

## Import Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 VFolder Destination Import Flow                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  import_revision(action) where action.vfolder_id is provided             │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 1. Get VFolder info                                                │ │
│  │    vfolder = await vfolder_repository.get_by_id(action.vfolder_id) │ │
│  │                                                                    │ │
│  │    vfolder = {                                                     │ │
│  │        id: "...",                                                  │ │
│  │        host: "local:volume1",                                      │ │
│  │        quota_scope_id: "user:abc123...",                           │ │
│  │    }                                                               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 2. Build VFolderID                                                 │ │
│  │    vfolder_id = VFolderID(vfolder.quota_scope_id, vfolder.id)      │ │
│  │    volume_name = parse_host(vfolder.host)  # "volume1"             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 3. Quota Check (NEW)                                               │ │
│  │                                                                    │ │
│  │    ┌──────────────────────────────────────────────────────────┐   │ │
│  │    │ a. Get current usage from storage proxy                  │   │ │
│  │    │    usage = await storage_client.get_quota_scope_usage(   │   │ │
│  │    │        volume_name, quota_scope_id                       │   │ │
│  │    │    )                                                     │   │ │
│  │    │    # returns: { used_bytes: 5368709120 }                 │   │ │
│  │    └──────────────────────────────────────────────────────────┘   │ │
│  │                              │                                     │ │
│  │                              ▼                                     │ │
│  │    ┌──────────────────────────────────────────────────────────┐   │ │
│  │    │ b. Get quota limit from resource policy                  │   │ │
│  │    │    max_size = await get_quota_scope_limit(quota_scope_id)│   │ │
│  │    │    # Query user_resource_policies or                     │   │ │
│  │    │    # project_resource_policies based on scope type       │   │ │
│  │    │    # returns: 10737418240 (10GB) or -1 (unlimited)       │   │ │
│  │    └──────────────────────────────────────────────────────────┘   │ │
│  │                              │                                     │ │
│  │                              ▼                                     │ │
│  │    ┌──────────────────────────────────────────────────────────┐   │ │
│  │    │ c. Compare                                               │   │ │
│  │    │    if max_size > 0:  # -1 means unlimited                │   │ │
│  │    │        if usage.used_bytes + revision.size > max_size:   │   │ │
│  │    │            raise VFolderQuotaExceededError(...)          │   │ │
│  │    └──────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 4. Proceed with import                                             │ │
│  │    vfolder_target = VFolderStorageTarget(                          │ │
│  │        vfolder_id=vfolder_id,                                      │ │
│  │        volume_name=volume_name,                                    │ │
│  │    )                                                               │ │
│  │                                                                    │ │
│  │    await storage_proxy.import_huggingface_models(                  │ │
│  │        storage_step_target_mappings={                              │ │
│  │            step: vfolder_target for step in ArtifactStorageImportStep │
│  │        }                                                           │ │
│  │    )                                                               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 5. Storage Proxy writes to VFolder path                            │ │
│  │    /mnt/vfhost/quota_scope_id/vfolder_id/{artifact_files}          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quota Check Logic

```python
async def check_vfolder_quota(
    self,
    vfolder_data: VFolderData,
    additional_size: int,
) -> None:
    """
    Check the quota scope limit for a VFolder.
    """
    quota_scope_id = vfolder_data.quota_scope_id
    _, volume_name = self._storage_manager.get_proxy_and_volume(vfolder_data.host)

    # 1. Get current quota scope usage from storage proxy
    storage_client = self._storage_manager.get_manager_facing_client(vfolder_data.host)
    usage = await storage_client.get_quota_scope_usage(volume_name, str(quota_scope_id))

    # 2. Get limit from resource policy
    max_size = await self._get_quota_scope_limit(quota_scope_id)

    # -1 means unlimited
    if max_size < 0:
        return

    # 3. Check if limit would be exceeded
    if usage.used_bytes + additional_size > max_size:
        raise VFolderQuotaExceededError(
            vfolder_id=VFolderID(quota_scope_id, vfolder_data.id),
            quota_scope_id=quota_scope_id,
            current_size=usage.used_bytes,
            max_size=max_size,
            requested_size=additional_size,
        )


async def _get_quota_scope_limit(self, quota_scope_id: QuotaScopeID) -> int:
    """
    Parse scope type from QuotaScopeID and query the appropriate resource policy.
    """
    scope_type, scope_uuid = quota_scope_id.split(":", 1)

    match scope_type:
        case "user":
            user = await self._user_repo.get_by_uuid(UUID(scope_uuid))
            policy = await self._user_policy_repo.get_by_name(user.resource_policy)
            return policy.max_quota_scope_size

        case "project":
            group = await self._group_repo.get_by_id(UUID(scope_uuid))
            policy = await self._project_policy_repo.get_by_name(group.resource_policy)
            return policy.max_quota_scope_size
```

## Storage Proxy API

### GET /volumes/{volume}/quota-scopes/{quota_scope_id}

Returns current usage of the quota scope used by the VFolder.

**Request:**
```
GET /volumes/volume1/quota-scopes/user:abc123...
```

**Response:**
```json
{
  "used_bytes": 5368709120,
  "limit_bytes": 10737418240
}
```

> Note: `limit_bytes` is the limit set at the storage proxy level and may be managed
> separately from the manager's resource policy. This BEP prioritizes the manager's
> resource policy value.

## User vs Project VFolder Comparison

| Aspect | User VFolder | Project VFolder |
|--------|-------------|-----------------|
| `ownership_type` | `"user"` | `"group"` |
| `quota_scope_id` format | `"user:{user_uuid}"` | `"project:{group_id}"` |
| Resource Policy table | `user_resource_policies` | `project_resource_policies` |
| Quota field | `max_quota_scope_size` | `max_quota_scope_size` |
| Owner reference | `vfolders.user` | `vfolders.group` |

## Current vs Proposed Behavior

### Current Behavior

```
import_revision(vfolder_id=...)
    │
    ▼
storage_proxy.import_models(vfolder_target=...)
    │
    ▼
Storage Proxy detects quota exceeded during file write
    │
    ▼
Error returned (import fails mid-way)
    │
    ▼
May leave partial download state
```

### Proposed Behavior

```
import_revision(vfolder_id=...)
    │
    ▼
quota_service.check_vfolder_quota(...)  ◄── NEW: Pre-validation
    │
    ├── If exceeded: Return VFolderQuotaExceededError immediately
    │
    ▼ (if passed)
storage_proxy.import_models(vfolder_target=...)
    │
    ▼
Complete successfully
```

## Error Response Example

```json
{
  "error": "VFolderQuotaExceededError",
  "message": "VFolder quota scope limit would be exceeded",
  "details": {
    "vfolder_id": "user:abc123.../vf-123...",
    "quota_scope_id": "user:abc123...",
    "current_size_bytes": 5368709120,
    "max_size_bytes": 10737418240,
    "requested_size_bytes": 8589934592,
    "available_bytes": 5368709120
  }
}
```
