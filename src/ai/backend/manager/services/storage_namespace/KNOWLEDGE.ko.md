# 스토리지 네임스페이스 service: 배경

> 규칙은 `../AGENTS.md`, spec 선택은 `../../models/specs/KNOWLEDGE.md` 에 있다.

스토리지 네임스페이스는 object storage 가 노출하는 bucket 이거나 VFS storage 가 노출하는 subpath 다. artifact 가 이 row 중 하나를 참조해 저장 위치를 기록한다. 스토리지 네임스페이스가 storage 의 column 으로 있는 대신 자체 식별자를 가져야 하므로 이 패키지가 존재한다.

## processor fields

`backend.ai mgr ops list --concern artifact_registry --entity storage_namespace` 를 실행하면 연결 및 호출 경로로 처리되는 목록이 출력된다. 그 출력이 엔티티 종류, shape, operation, gate, backing 을 알려 준다.

이 domain 의 모든 REST route 는 `superadmin_required` 를 선언하므로 global gate 가 surface 의 약속과 일치한다. 이 패키지가 의존하는 object storage 와 VFS storage 패키지도 같다. 두 패키지의 surface 는 v1 을 포함해 모두 super-admin operation 이므로 여기서 일반 사용자에게 열린 조회는 없다.

## 등록 해제는 id 를 받고, 호출자는 lookup 으로 짝을 id 로 변환한다

- 등록은 `(storage_id, namespace)` 를 노출하는데, 이것은 테이블의 unique 제약이지 primary key 가 아니다. purge spec 은 primary 값 하나를 key 로 사용한다.
- purge 에 두 번째 주소 지정 방식을 추가하는 대신, 호출자가 `lookup` 으로 그 짝을 찾아 id 를 전달한다. lookup 은 이미 일치하는 row 가 둘이면 임의의 row 로 응답하지 않고 거부한다.
- 이 변환은 adapter 에 있으므로 API 는 등록했을 때와 같은 방식으로 스토리지 네임스페이스를 계속 지정한다.

## own 하는 storage 는 polymorphic 이고 schema 는 그것을 말하지 않는다

- `storage_id` 는 `object_storages` 나 `vfs_storages` 를 참조하고, row 는 어느 쪽인지 알려 주는 discriminator 를 갖지 않는다.
- 그래서 `artifact_revision/service.py` 는 object storage 를 먼저 조회하고 예외가 나면 VFS storage 로 대체한다. 실패를 분기로 사용한다.
- ORM 은 절반만 모델링한다. `StorageNamespaceRow.object_storage_row` 가 `ObjectStorageRow` 만 조인하므로 VFS 가 own 하는 namespace 는 조회 결과가 없다.

## 이 참조 경로에 foreign key 는 없다

| 연결 | 제약 |
|---|---|
| `storage_namespace.storage_id` → `object_storages` 또는 `vfs_storages` | 없음 |
| `association_artifacts_storages.storage_namespace_id` → `storage_namespace.id` | 없음 |
| `association_artifacts_storages.artifact_revision_id` → `artifact_revisions.id` | 없음 |

- artifact 가 아직 참조하는 namespace 를 등록 해제하면 artifact 가 더 이상 없는 위치를 지정하게 된다. `conflict_checks()` 도 이 상황을 선언하지 않는다.
- association 은 `artifact_revision_id` 에 unique 이고 항상 revision 쪽에서만 조회하므로, 모양과 달리 일대일이고 단방향이다.
