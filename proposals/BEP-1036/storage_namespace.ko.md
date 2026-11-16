# StorageNamespace quota

기본 아티팩트 저장소(Reservoir archive storage)의 quota 시스템이다.

## 개요

`vfolder_id` 를 제공하지 않으면 아티팩트는 설정된 Reservoir archive storage 에 저장된다.
이 저장소는 `StorageNamespaceRow` 가 관리하며 두 backend 타입을 지원한다.

- **Object Storage** (MinIO, S3 등)
- **VFS Storage** (로컬/네트워크 filesystem)

두 타입은 `StorageNamespaceRow.max_size` 를 통해 같은 quota 방식을 공유한다.

## 데이터 모델

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

## backend 타입 차이

| 항목 | Object Storage | VFS Storage |
|--------|---------------|-------------|
| 스토리지 네임스페이스 설정 키 | `bucket_name` | `subpath` |
| 참조 테이블 | `object_storage` | `vfs_storage` |
| 물리 저장소 | S3 bucket (예: `s3://artifacts/`) | filesystem 경로 (예: `/mnt/nfs/artifacts/`) |

quota 관리와 사용량 집계는 두 타입이 같다.

## quota 검사 로직

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

### 사용량 집계 질의

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

또는 무제한으로 설정한다.

```json
{ "max_size": null }
```
