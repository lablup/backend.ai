# VFolder storage quota

사용자가 `vfolder_id` 를 제공하면 특정 vfolder 에 저장되는 아티팩트의 quota 시스템이다.

## 개요

`import_revision()` 에 `vfolder_id` 를 제공하면 아티팩트는 지정한 vfolder 에 저장된다.
vfolder 에는 `quota_scope` 를 통한 기존 quota 시스템이 이미 있지만, 아티팩트 import 중에는 quota 검사가 **없다**.

**현재 문제:**
- import 시작 전 quota 검사가 없다
- storage proxy 가 quota 초과를 감지하면 큰 아티팩트 import 가 중간에 실패할 수 있다
- 실패한 import 는 부분 다운로드를 남길 수 있다

## 데이터 모델

### VFolder quota 구조

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

### VFolder row 구조

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

## import 흐름

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

## quota 검사 로직

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

vfolder 가 사용하는 quota scope 의 현재 사용량을 반환한다.

**요청:**
```
GET /volumes/volume1/quota-scopes/user:abc123...
```

**응답:**
```json
{
  "used_bytes": 5368709120,
  "limit_bytes": 10737418240
}
```

> 참고: `limit_bytes` 는 storage proxy 계층에서 설정한 한도이고, manager 의 자원 정책과 별도로 관리될 수 있다. 이 BEP 는 manager 의 자원 정책 값을 우선한다.

## 사용자 vfolder 와 프로젝트 vfolder 비교

| 항목 | 사용자 vfolder | 프로젝트 vfolder |
|--------|-------------|-----------------|
| `ownership_type` | `"user"` | `"group"` |
| `quota_scope_id` 형식 | `"user:{user_uuid}"` | `"project:{group_id}"` |
| 자원 정책 테이블 | `user_resource_policies` | `project_resource_policies` |
| quota 필드 | `max_quota_scope_size` | `max_quota_scope_size` |
| 소유자 참조 | `vfolders.user` | `vfolders.group` |

## 현재 동작과 제안 동작

### 현재 동작

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

### 제안 동작

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

## 에러 응답 예시

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
