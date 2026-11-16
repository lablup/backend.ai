# 아티팩트 저장소 사용량 추적과 quota 강제

## 동기

지금 아티팩트 저장소에는 사용량 추적도 용량 한도도 없다. 아티팩트를 가져오면 얼마나 공간을 차지하는지 알 수 없고, 저장 공간 고갈을 방지할 장치도 없이 그대로 저장된다.

그래서 운영 위험이 생긴다.

- 경고 없이 저장 공간이 고갈될 수 있다
- 저장소 사용률을 볼 수 없다
- 용량 계획이나 비용 관리를 강제할 방법이 없다

아티팩트 import 흐름은 두 저장 목적지를 지원하고, 둘 다 quota 강제가 필요하다.

1. **기본(StorageNamespace)**: quota 시스템이 없다
2. **vfolder 목적지**: quota 시스템이 있지만(`max_quota_scope_size`) 아티팩트 import 사전 검사에 통합되지 않았다

## 현재 설계

### 기존 데이터 모델

- **`StorageNamespaceRow`**: 기본 스토리지 네임스페이스 정보(`id`, `storage_id`, `namespace`)를 추적한다. quota 관련 필드는 없다.
- **`ArtifactRevisionRow`**: revision 별 `size` 를 이미 추적한다.
- **`AssociationArtifactsStorageRow`**: 아티팩트 revision 을 스토리지 네임스페이스에 연결한다.

### 두 저장 목적지

아티팩트 import 흐름(`import_revision()`)은 두 목적지를 지원한다.

| 목적지 | 조건 | 현재 quota |
|-------------|------|---------------|
| StorageNamespace | `vfolder_id` 가 None | **없음** |
| vfolder | `vfolder_id` 를 제공 | 자원 정책의 `max_quota_scope_size` (storage proxy 가 write 시점에 강제) |

### vfolder quota 시스템

vfolder 에는 기존 quota 시스템이 있다.

- `VFolderRow.quota_scope_id` 가 사용자나 프로젝트를 참조한다
- 자원 정책이 `max_quota_scope_size` 를 정한다
- storage proxy 가 filesystem write 시점에 quota 를 강제한다

**문제**: 아티팩트 import 는 시작 전에 vfolder quota 를 사전 검사하지 않는다. 큰 import 는 storage proxy 가 quota 한도 때문에 쓰기를 거부하면 중간에 실패할 수 있다.

## 제안 설계

### 개요

저장 목적지와 상관없이 아티팩트 import 시작 전에 사전 검증을 실행하는 통합 quota 강제 계층을 생성한다.

### 통합 quota service

두 저장 목적지를 하나의 진입점으로 처리하는 `ArtifactStorageQuotaService` 를 생성한다.

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

### 저장 목적지별 세부 사항

저장 목적지마다 quota 방식이 다르다.

| 목적지 | quota 원천 | 사용량 원천 | 세부 사항 |
|-------------|-------------|--------------|---------|
| StorageNamespace | `StorageNamespaceRow.max_size` (NEW) | association 테이블을 거쳐 `artifact_revisions` 에서 집계 | [storage_namespace.md](BEP-1036/storage_namespace.md) |
| vfolder | 자원 정책의 `max_quota_scope_size` | storage proxy API | [vfolder_storage.md](BEP-1036/vfolder_storage.md) |

### quota 검사를 포함한 import 흐름

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         import_revision(action)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Get revision_data (includes size)                                        │
│                                                                              │
│  2. Determine storage destination                                            │
│     ┌─────────────────────────────┬────────────────────────────────────┐    │
│     │    vfolder_id provided?     │                                    │    │
│     └──────────┬──────────────────┴────────────────────┬───────────────┘    │
│                │ YES                                   │ NO                  │
│                ▼                                       ▼                     │
│     ┌─────────────────────────┐          ┌─────────────────────────────┐    │
│     │  VFolderDestination     │          │  StorageNamespaceDestination│    │
│     │  - vfolder_id           │          │  - namespace_id             │    │
│     │  - quota_scope_id       │          │                             │    │
│     └───────────┬─────────────┘          └───────────────┬─────────────┘    │
│                 │                                         │                  │
│                 └──────────────┬──────────────────────────┘                  │
│                                ▼                                             │
│  3. ┌──────────────────────────────────────────────────────────────────┐    │
│     │            ArtifactStorageQuotaService.check_quota()             │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                │                                             │
│                 ┌──────────────┴──────────────┐                              │
│                 ▼                              ▼                             │
│     ┌─────────────────────────┐    ┌─────────────────────────────────┐      │
│     │ _check_vfolder_quota()  │    │ _check_storage_namespace_quota()│      │
│     └───────────┬─────────────┘    └───────────────┬─────────────────┘      │
│                 │                                   │                        │
│                 └──────────────┬────────────────────┘                        │
│                                ▼                                             │
│                 ┌──────────────────────────────┐                             │
│                 │     Quota Exceeded?          │                             │
│                 └──────────────┬───────────────┘                             │
│                    YES │              │ NO                                   │
│                        ▼              ▼                                      │
│     ┌─────────────────────────┐    ┌─────────────────────────────────┐      │
│     │ Raise appropriate error │    │ 4. Proceed with import          │      │
│     │ - VFolderQuotaExceeded  │    │    - Call storage proxy         │      │
│     │ - StorageNamespace      │    │    - Update status              │      │
│     │   QuotaExceeded         │    │    - Associate with storage     │      │
│     └─────────────────────────┘    └─────────────────────────────────┘      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### quota 검사의 데이터 원천

**StorageNamespace**: 사용량은 association 테이블로 연결된 아티팩트 revision 에서 집계한다.

```
┌─────────────────────┐     ┌─────────────────────────────────┐
│ storage_namespace   │     │ association_artifacts_storages  │
├─────────────────────┤     ├─────────────────────────────────┤
│ id                  │◄────│ storage_namespace_id            │
│ max_size (NEW)      │     │ artifact_revision_id ───────────┼──┐
└─────────────────────┘     └─────────────────────────────────┘  │
                                                                  │
                            ┌─────────────────────────────────┐  │
                            │ artifact_revisions              │  │
                            ├─────────────────────────────────┤  │
                            │ id ◄────────────────────────────┼──┘
                            │ size                            │
                            └─────────────────────────────────┘
```

**vfolder**: 사용량은 storage proxy 에서 조회하고, 한도는 자원 정책에서 가져온다.

```
┌─────────────────────┐     ┌─────────────────────────────────┐
│ vfolders            │     │ user_resource_policies /        │
├─────────────────────┤     │ project_resource_policies       │
│ id                  │     ├─────────────────────────────────┤
│ quota_scope_id ─────┼────►│ max_quota_scope_size            │
└─────────────────────┘     └─────────────────────────────────┘
         │
         │ VFolderID
         ▼
┌─────────────────────┐
│ Storage Proxy       │
├─────────────────────┤
│ get_quota_scope_    │
│ usage(quota_scope)  │──► Current usage in bytes
└─────────────────────┘
```

### quota 검사 비교

| 항목 | StorageNamespace | vfolder |
|--------|------------------|---------|
| 한도 원천 | `storage_namespace.max_size` | `resource_policy.max_quota_scope_size` |
| 사용량 원천 | association 테이블을 통한 DB 집계 | storage proxy API |
| 무제한 값 | `NULL` | `-1` |
| 범위 | 스토리지 네임스페이스 단위 | quota scope 단위(사용자/프로젝트) |

### 에러 타입

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

### REST API 엔드포인트

#### GET /storage-namespaces/{id}/usage

스토리지 네임스페이스 사용량 통계를 반환한다.

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

스토리지 네임스페이스의 quota 를 변경한다. admin 전용이다.

```json
{ "max_size": 107374182400 }  // or null for unlimited
```

## 테스트 시나리오

### StorageNamespace quota 테스트
- 한도 미만이면 quota 검사를 통과한다
- `max_size` 가 NULL(무제한)이면 quota 검사를 통과한다
- 한도를 넘으면 quota 검사가 에러를 발생시킨다
- quota 를 넘으면 import 흐름이 아티팩트를 거부한다

### vfolder quota 테스트
- 사전 검사가 storage proxy 에서 현재 사용량을 조회한다
- quota 검사는 자원 정책의 `max_quota_scope_size` 를 사용한다
- quota 를 넘으면 시작 전에 import 를 거부한다
- 자원 정책 한도가 무제한(-1)인 경우를 처리한다

### 통합 흐름 테스트
- `vfolder_id` 존재 여부로 올바른 quota 시스템을 선택한다
- 에러 메시지가 어느 quota 를 넘었는지 분명히 나타낸다

## 향후 아이디어

### quota 임계값 알림

저장소 사용량이 설정한 한도에 가까워지면 시스템이 관리자에게 알릴 수 있다.

- 임계값 수준: 80%, 90%, 95% 사용률
- 기존 알림 시스템과의 통합

## 참고

- [BEP-1019: MinIO Artifact Registry Storage](BEP-1019-minio-artifact-registry-storage.md)
