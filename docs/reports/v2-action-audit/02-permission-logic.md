# 2. 권한 검사 로직 확인

`backend.ai mgr ops list`와 `backend.ai mgr ops entities`의 출력을 RBAC 코드와 대조해, 카탈로그가
광고하는 것과 실제로 검사되는 것이 같은지 그리고 그 검사가 옳은지를 본다. 1부가 배선이 규칙에
맞는지 봤다면, 여기서는 그 배선이 만들어내는 **검사 자체**를 본다.

| | |
|---|---|
| Jira | BA-7494 |
| 기준 커밋 | `b2b200c0da` |
| 입력 | `mgr ops list -o json` 652행, `mgr ops entities -o json`, `ai.backend.manager` 코드 |
| 상태 | 진행 중 — A 완료, B 일부, C 미착수 |

## 대조가 성립하는 이유

권한 검사에 들어가는 입력은 셋뿐이고, 셋 다 카탈로그 컬럼에 대응한다.

| 검사 입력 | 코드에서 오는 곳 | 대응 컬럼 |
|---|---|---|
| 어떤 validator가 도는가 | 프로세서 클래스가 고정하는 것 + `deps.validators.<shape>` | `kind` + `gate` |
| 어떤 permission 비트를 요구하는가 | `action.operation_type().to_permission()` | `operation` |
| 무엇에 대해 묻는가 | single·bulk·field는 `meta.entity`, scope는 `scope_targets()` × `action.entity_type()` | `entity_type` / `field_type` |

`VirtualScopeSingleEntityActionRBACValidator`와 `VirtualScopeScopeActionRBACValidator`가 저 세
값만 조합해 `check_*_via_virtual_scope`를 부른다. 그래서 카탈로그 행은 검사 입력의 예고이고,
예고와 실제를 diff할 수 있다.

## A. 검사 사슬 — 어떤 shape에 무엇이 붙는가

게이트는 `deps.validators`가 아니라 **프로세서 생성자가 고정**한다. RBAC validator만 주입된다.

| kind / gate | 프로세서 | 생성자가 고정 | 주입되는 것 | 행 수 |
|---|---|---|---|---:|
| `global` / `permission` | `GlobalActionProcessor` | `SuperAdminActionValidator` | `global_scope` (비어 있음) | 191 |
| `global` / `public` | `PublicActionProcessor` | `AuthenticatedActionValidator` | `global_scope` (비어 있음) | 23 |
| `global` / `anonymous` | `AnonymousGlobalActionProcessor` | 없음 | 없음 | 4 |
| `single_entity` / `permission` | `SingleEntityActionProcessor` | 없음 | `single_entity` | 278 |
| `single_entity` / `public` | `SingleEntityActionProcessor` | `AuthenticatedActionValidator` | — | 7 |
| `scope` / `permission` | `ScopeActionProcessor` | 없음 | `scope` | 81 |
| `scope` / `anonymous` | `ScopeActionProcessor` | 없음 | 없음 | 1 |
| `bulk` / `permission` | `PartialBulk…` / `BulkActionProcessor` | 없음 | `atomic_bulk`·`partial_bulk` | 20 |
| `bulk` / `public` | `PublicPartialBulkActionProcessor` | `AuthenticatedAtomicBulkActionValidator` | — | 2 |
| `lookup` / `permission` | `LookupActionProcessor` | `AuthenticatedActionValidator` | post: `single_entity` | 35 |
| `lookup` / `public` | `LookupActionProcessor` | `AuthenticatedActionValidator` | post 없음 | 10 |

프로덕션 조립(`dependencies/processing/composer.py:418`)은 `single_entity`, `partial_bulk`,
`atomic_bulk`, `scope` 넷만 채운다. `global_scope`와 `lookup`은 빈 리스트로 남지만 게이트가
프로세서에 고정돼 있으므로 구멍이 아니다.

### A-1. 검사되는 값이 카탈로그와 다른 3건

1부에서 "entity type 불일치 6건"으로 묶은 것 중 셋은 감사 기록만의 문제가 아니다. `scope` kind는
`ScopePermissionCheckKey(entity_type=action.entity_type())`로 **어떤 permission 행이 매칭될지**를
정한다.

| action | kind | 카탈로그가 광고 | 검사에 실제로 쓰임 |
|---|---|---|---|
| `search_domain_usage_buckets` | `scope` | `global` | `domain` |
| `search_project_usage_buckets` | `scope` | `global` | `project` |
| `search_user_usage_buckets` | `scope` | `global` | `user` |

나머지 셋(`search_artifact_revisions`, `delegate_import_artifact_revision_batch`,
`global_search_replica_group_history`)은 `global` kind라 SUPERADMIN 게이트에 걸리고, entity type은
감사 행에만 남는다. 1부의 한 덩어리가 여기서 둘로 갈린다.

## B. 검사 대상이 RBAC 모델과 맞는가

`mgr ops entities`가 주는 entity/field 트리를 permission 저장소의 타입과 맞춰본다.

### B-1. 저장소 타입 이전 — 여기서 다루지 않음

`permissions` 테이블이 레거시 enum 타입에 남아 있어 일부 entity type이 권한 행과 매칭되지 않는
문제가 있다. 액션 정의가 아니라 저장소 스키마의 문제이므로 BA-7498에서 처리한다.

### B-2. 남은 항목

- field row는 소유 엔티티로 검사하므로 `field_type`이 `ScopePermissionCheckKey`로 새지 않아야
  한다. 실제로 새지 않는지 확인.
- `GLOBAL_ENTITY_TYPE`은 AGENTS.md상 배선 전용인데, 그것을 검사 대상으로 넘기는 행이 4개 있다
  (`purge_entity_label`, `search_entity_labels` 등). 배선이 잘못된 쪽으로 보인다.
- 액션이 선언하는 `scope_targets()`가 연산의 실제 범위와 맞는지 — 한 사용자의 읽기가 도메인
  스코프를 대상으로 선언하면 검사가 잘못된 층에서 이뤄진다.

## C. 검사 로직 자체 — 미착수

- `to_permission()`은 마스크를 반환하고 `covers()`가 모든 비트를 요구하는 것으로 보인다
  (`db_source.py:1238`). UPSERT = `CREATE|UPDATE`가 한 비트만으로 통과하지 않는지 확인.
- `to_permission()`(마스크)과 `to_permission_operation()`(단일 값, UPSERT를 CREATE로 좁힘)이
  공존한다. 후자는 레거시 validator 4곳(`actions/validators/rbac/`)이 읽는다. 같은 액션이 두 경로를
  타면 더 약한 쪽이 통과시킬 수 있다.
- 모든 validator 앞머리의 `if user.is_superadmin: return` — is_superadmin이 신뢰할 수 있는
  출처에서만 오는지.
- `enforcement_enabled`(기본값 `true`)가 꺼지면 v2 validator가 `current_user()` 확인 전에 반환한다.
  설정 설명은 "레거시 권한 경로만 적용된다"고 하지만, v2 전용 액션에는 레거시 경로가 없다. 이때
  무엇이 남는지 — 라우트의 auth 미들웨어뿐인지 — 확인.
- 체인의 per-hop cap clipping이 `granted & scope_cap & entity_cap`으로 좁히는 방향이 맞는지.
