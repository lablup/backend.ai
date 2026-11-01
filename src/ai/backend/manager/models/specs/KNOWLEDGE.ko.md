# write spec: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 패키지가 있는 이유

write spec 은 "무엇을 쓰는가"(row, membership, 무결성 검사)를 schema 옆의 선언으로 변경하고, 실행은 ops
계층이 맡는다. write 의 RBAC 부수 효과, 곧 graph 에 node 를 마련하고 membership 을 등록하는 일을 실행
경로가 아니라 spec 의 type 이 정하게 하려는 패키지다.

## spec 선택에서 남은 질문은 "엔티티인가" 하나다

**모든 엔티티는 graph 에 node 를 가진다.** membership 을 가질 수 있고 공유될 수 있다.

| spec | 기준 | write 동작 |
|---|---|---|
| Entity | 일급 엔티티(vfolder/session/...) | create 가 node 를 마련하고(스스로를 own 하고 govern 한다) 각 `created_in()` 스코프가 이를 own 하고 govern 한다. purge 는 대칭으로 정리하고 upsert 는 idempotent 하게 남는다 |
| Global, role-managed | 프리셋 역할을 부여하는 엔티티이며 스코프 없이 생성되는 것(domain, resource group) | Global 동작 + 프리셋 역할 생성: `RoleManagedGlobalEntityCreator` |
| Entity, role-managed | 프리셋 역할을 부여하는 엔티티이며 스코프 안에서 생성되는 것(project, user) | Entity 동작 + 프리셋 역할 생성: `RoleManagedEntityCreator`, domain 을 `created_in()` 한다 |
| Global | 다른 엔티티 아래에 속하지 않는 엔티티 | `created_in` 을 뺀 Entity 동작. node 는 같은 방식으로 마련한다 |
| Field | 다른 엔티티가 소유하는 row(자체 get/delete API 가 있어도) | create 에 `owner_id` 가 필요하고 purge 는 일반 delete 다 |
| Sidecar | graph 밖의 row. 감사 기록, event log | create 는 insert 만 한다. 지정한 엔티티는 읽기 권한의 근거이지 소유자가 아니다 |

## relation 은 양쪽에 속하므로 어느 항목에도 속하지 않는다

- write spec 은 소유를 기준으로 나뉘고, 두 항목 모두 소유가 0 또는 1이라고 가정한다. 엔티티는 스스로를
  own 하고 필드는 엔티티 하나가 소유한다. 두 엔티티를 잇는 row 는 양쪽이 소유하므로 어느 항목도 그렇게
  말할 수 없다.
- 소유는 호출 지점이 아니라 schema 에서 읽는다. row 가 사라질 때 무엇이 삭제하는지가 소유자다.
  polymorphic 참조는 외래 키가 없으므로 그 소유는 제약에 대한 사실이 아니라 정리 코드에 대한 사실이다.
- 그래서 relation 루트는 pair 를 지정하고 row id 는 지정하지 않는다. row 를 쓴 계층 밖에서는 그 id 를
  가지지 않으며, 읽기는 두 엔티티 사이의 row 가 아니라 relation 이 접근하는 엔티티를 반환한다.
- 끄기는 접근이 아니라 상태다. 프로젝트에서 한동안 제외된 resource group 도 양쪽에서 읽혀야 제외가
  드러나고 되돌릴 수 있다(Kubernetes 의 cordon 과 GitLab 의 archive 가 택한 방식). 그래서 lifecycle 전이는
  row 만 쓰고 graph 는 create 와 purge 에서만 움직인다. create 에 꺼진 row 를 되살리는 upsert 가 없는
  이유이기도 하다. 되살리기는 restore 의 역할이다.
- 전체 근거: `proposals/BEP-1075-entity-relation-operations.md`.

## sidecar 는 어느 항목에도 속하지 않는다

- 엔티티는 스스로 설 수 있고 virtual entity 를 통해 다른 엔티티와 엮인다. 필드는 스스로 설 수 없고
  소유자의 값에 덧붙는 확장이며 소유자의 권한으로 처리된다.
- sidecar 는 대각선을 택한다. 스스로 서지만 node 를 가지지 않고, 필드처럼 엔티티의 권한으로 읽힌다. 감사
  기록은 대상 엔티티보다 오래 남고, 어떤 기록은 엔티티를 지정하지 않는다.
- 그래서 create 가 정하는 것이 없다. node 도 소유자도 없다. 지정한 엔티티는 읽는 쪽을 권한 부여하는
  값이므로, row 가 누구의 것도 아닌데도 읽기는 그 엔티티에 대한 스코프 모양이 된다.

## 공통 ABC 가 없는 것이 강제 수단이다

- 공통 상위 type 이 있으면 node 를 마련하지 않는 실행 경로에 전달된 엔티티 spec 이 type 검사를 통과하고
  조용히 건너뛴다. 이 계보가 막으려는 결함이 정확히 그것이다.
- 루트마다 메서드 선언을 중복하는 것이 그 경로를 표현 불가능하게 만드는 대가다.
- 실행 로직 재사용은 일반 값을 받는 ops helper 로 한다.

## role-managed 루트가 subtype 이 아닌 것도 같은 수단이다

- `RoleManagedEntityCreator` 가 `EntityCreator` 의 subtype 이면 일반 `create_entity` 경로의 type 검사를
  통과하고 프리셋 역할을 조용히 건너뛴다.
- 엔티티 훅을 결합 루트에 중복해 두어 role-managed 경로만 이를 받는다.
- `RoleTemplateSource` 만 공유 base 로 남는다. 어떤 write 경로도 그 type 을 단독으로 받지 않는다.

## guard 는 루트에 두어 어떤 경로도 건너뛸 수 없게 한다

- creator, updater, 단일 row purger 는 각각 guard 를 abstract 로 선언한 루트와 `@final` 아래 빈 목록을
  반환하는 subtype 을 둔다. 하나의 ops 경로가 둘을 처리하므로 guard 가 있는 spec 을 guard 없이 쓰는
  경로에 전달할 수 없다. 공통 ABC 가 없는 것이 다른 곳에서 강제하는 것과 같은 방식이다.
- 대신 서로 무관한 루트 둘을 두던 때(`DataUpdater` 와 `GuardedDataUpdater`)에는 ops, service, action,
  group 표면이 두 배가 되고 거부가 일반화되지 않았다. write 가 `None` 을 반환하고 호출자가 row 를 다시
  읽어 없음과 거부를 구분했으며, 호출자마다 오류를 새로 만들었다.
- 검사에 오류를 두면 진단이 ops 로 옮겨 간다. statement 가 아무것도 건드리지 않으면 지정한 row 를 한 번
  SELECT 해 옆의 모든 guard 조건을 평가한다. row 가 없으면 사라진 것이고, 처음 나온 `false` 가 오류를
  지정한다. 두 statement 사이에 바뀌어 모든 guard 를 통과하는 row 는 첫 guard 가 그 이유를 반환한다.
  write 는 거부했고 다시 실행하면 호출자가 요청하지 않은 두 번째 write 가 되기 때문이다.
- 실패는 한 번의 왕복으로 끝난다. 예전에 `row_exists` 가 치르던 비용이다. `guard_checks()` 가 비어 있는
  spec 은 비용을 내지 않는다. 진단은 탓할 guard 가 있을 때만 실행한다.
- `RolePurger` 는 SYSTEM 거부를 충돌 검사가 아니라 guard 로 선언한다. 조건이 남길 row 가 아니라 삭제되는
  row 에 있기 때문이다.

## global 엔티티도 node 를 마련하는 이유

global 엔티티 아래에도 row 가 생성된다. container registry 아래의 image 가 그렇다. node 가 없으면 그
row 들이 membership 이 향할 대상이 없고, global 엔티티 자체는 super-admin 외에는 접근할 수 없다.

삭제 쪽은 항상 node 를 정리했다(`purge_entity` 가 `_teardown_entity` 를 호출한다). 생성 쪽은 생성한 적
없는 것을 정리하던 비대칭을 없앴다.

## field row 는 자체 id 를 가진다

- 소유 엔티티가 정확히 하나인 row 가 field row 다. 소유자를 참조하는 방식(연쇄 FK 또는 polymorphic
  `(entity_type, entity_id)` pair)은 기준이 아니고, API 가 지금 개별 row 를 지정하는지도 기준이 아니다.
- 그런 테이블에는 `id` uuid 를 둔다. 기본 키가 복합이면 그대로 두고 `id` 를 유일 column 으로 추가한다.
  기존 질의와 인덱스가 모두 살아남고 `FieldIdentifier` 를 표현할 수 있다.
- 소유자마다 slot 하나의 양을 기록하는 다섯 테이블(agent / session / model card / deployment preset /
  deployment revision)이 이 모양이다.

## 연산이 어느 끝에서 시작하는지가 검사를 정한다

| 시작점 | 소유자 | 모양 | 검사 대상 |
|---|---|---|---|
| field row 의 id | 모름 | field | 먼저 읽은 소유 엔티티 |
| 엔티티의 id | 앎 | scope | 그 엔티티를 스코프로 |

- 그 엔티티의 field row 여럿을 반환하는 읽기는 엔티티에서 시작했으므로 무엇을 건드리는 대상이 아니라 어디를
  살펴볼 대상을 지정한다. 소유자를 스코프로 둔 scope 모양이다.
- field row 생성이 소유 엔티티의 id 를 받는 이유도 같다.
- 규칙은 `../../actions/AGENTS.md` 에 있다.

## field row 의 membership 은 소유자를 통해서만 알 수 있다

- field row 는 자체 membership 을 갖지 않으므로 이를 지정한 연산은 검증할 것도 기록할 것도 없다.
  `FieldOwnerLookup` 이 그 역할을 채운다. field row 의 id 에서 소유 엔티티의 id 로 잇는다.
- 조건이 아니라 질의를 선언하는 이유는 둘이다. 소유자가 join 을 통해서만 접근할 수 있고, (row id, 소유자
  id) pair 를 선택하는 것이 batch 에서 각 row 의 소유자를 잃지 않게 한다.
- `Select` 의 type parameter 가 invariant 라 일반적이다. 구체 column type 은 느슨하게 선언한 type 과
  맞지 않으므로 구현이 자기 type 둘을 모두 밝힌다. `DataBatchPurger` 가 row type 에 대해 일반적인
  이유도 같다.

## soft delete 는 field 의 부재로 guard 된다

spec 루트와 같은 방식이다. write 를 차단하는 것은 실행 시점의 검사가 아니라 선언의 모양이다.

soft delete 는 DB 에서 UPDATE 이므로 ops 가 편집과 구분할 수 없다. 일반화할 delete 연산도 없고 거기서
강제할 자리도 없다. 이를 삭제로 기록하는 것은 action 의 `operation_type()` 이며, RBAC 권한과 감사 row 의
`operation` 을 정한다.

구멍이 하나 남는다. lifecycle column 을 쓰는 일반 편집은 `UPDATE` 로 기록되므로 삭제가 기록에 나타나지
않는다. 일반 updater 에서 그 field 를 제거하면 그 구멍이 닫힌다. 편집 경로에는 전이를 만들 수단이 없다.
delete 와 restore 를 상수 `build_values()` 를 가진 별도 updater 로 나누면 나머지가 닫힌다. 인자로 받은
전이 값은 잘못 전달될 수 있는 값이다.

상태를 담는 column 은 아직 다르다(role preset 은 `deleted`, vfolder 나 user 는 `status`). BEP-1069 는
이를 soft delete mixin 의 `deleted_at` 으로 옮긴다. business 상태와 삭제가 동시에 성립하므로(비활성
상태에서 삭제된 user) 하나의 enum 으로 합치면 restore 가 앞선 business 상태를 잃는다. user 와 role 의
restore 는 지금 항상 `active` 를 쓴다.

## own 과 govern 은 다른 relation 이고 생성이 둘을 조합한다

- own: virtual entity 가 엔티티를 보유한다. 엔티티는 그 virtual entity 의 목록에 있고("목록 = 등재")
  한 홉 떨어져 있다.
- govern: 스코프가 virtual entity 를 govern 한다. 스코프의 역할이 그 virtual entity 가 own 하는 모든 것에
  접근한다. 둘 중 넓은 relation 이다.
- resolver 는 한 홉을 걷는다: `entity → 이를 own 하는 virtual entity → 그것을 govern 하는 스코프 →
  role`. 검사는 ops 에도 있다(`PermissionReadOps`, `PermissionOpsProvider` 의 읽기 쪽).
  `PermissionDBSource` 는 위임하므로 graph 는 ops 로만 쓰고 읽는다.
- 검사는 relation 이름을 딴 둘이다. repository 는 key 마다 mask 를 반환하고, 검사(`mask.covers(bits)`)는
  validator 가 한다.

| 검사 | 질문 | repository 가 반환하는 mask |
|---|---|---|
| own 검사 | 내 역할이 있는 스코프가 govern 하는 virtual entity 가 이 엔티티를 own 하는가(cap 포함): "이 bit 들로 이 엔티티를 own 하는가" | `owned_permissions(keys)`: key 마다 경로 전체의 `permission & govern cap & share cap` 의 OR |
| govern 검사 | 내 역할이 있는 스코프가 이 스코프의 virtual entity 를 govern 하는가(자기 govern 포함), 그 안에서 이 엔티티 type 에 이 bit 를 주는가: "이 type 과 이 bit 로 이 스코프를 govern 하는가" | `governed_permissions(keys)` |

- entity create 와 search 는 govern 검사(생성되는 것이 스코프 소유가 된다), 단일 엔티티, bulk, relation
  action 은 own 검사를 쓴다. global 은 graph 밖이다(superadmin). field 검사와 목록 필터(BEP-1077 의 field 검사와 목록 필터 절)는 후속 작업이다.
- own 검사는 홉마다 인덱스 조회 하나이고 엔티티마다 row 하나를 반환한다.

| 측정 | 방법 |
|---|---|
| 동등성 | `tests/unit/manager/repositories/permission_controller/test_own_check_query.py`: 옛 질의(경로와 bit 마다 row 하나를 Python 에서 OR)를 함수로 남겨 두고 CI 마다 새 질의와 같은 답을 내는지 세 모양(own 사슬, share, 역할 여럿)으로 검사한다 |
| benchmark | 같은 파일. `BAI_BENCHMARK=1 … -s` 는 엔티티 1,000개를 실행하고, `BAI_BENCHMARK_SCALE=1 … -s` 는 COPY 로 seed 한 규모(domain 10, project 1,000, user 10,000, session 1M, vfolder 1M, share 300k, role 10,000, permission 100k, user role 100k, relation row 약 13M, seed 약 4분, pants 에 `--test-timeout-default=3600 --test-attempts-default=1` 필요)를 실행한다. warm-up 뒤 두 질의를 번갈아 실행하고 min / median / p95 와 `EXPLAIN (ANALYZE, BUFFERS)` 를 출력한다 |

| 규모 실행(로컬 container, 정상 실행 셋 중 둘의 범위) | 옛 질의 중앙값 | 새 질의 중앙값 | DB 내부 실행 |
|---|---|---|---|
| session 2,000개(내 것 1,000 + 남의 것 1,000, 모두 접근) | 71 ~ 74 ms | 56 ~ 59 ms | 41 ms 대 42 ms |
| vfolder 500개(261개 접근) | 13 ms | 13 ms | 6.7 ms 대 7.2 ms |

- 계획은 둘이 같다: entity unique index → own index → govern index-only → governor PK → user 권한과의
  hash join(수십 row). 모든 홉이 인덱스 조회이고 seq scan 은 없다. 41 ms 중 31 ms 는 엔티티 2,000개 ×
  경로 약 7개의 nested loop 다.
- 실제 시간 차이는 반환 row 수(5,260 → 2,000)와 Python OR loop 제거에서 나온다. `bit_or … GROUP BY` 가
  그 대가로 Sort + GroupAggregate 약 1 ms 를 더한다. user 권한을 CTE 로 앞세우는 것은 얻는 것이 없었고
  (planner 가 이미 한다) 넣지 않았다.
- 한 실행에서는 같은 data 에서 두 질의의 중앙값이 29초였다(COPY 직후의 container DB 로 보인다). 재현되지
  않았고, 운영 규모의 호출은 운영 통계 아래에서 계획을 다시 읽어야 한다.
- 모든 엔티티의 own virtual entity 가 그 엔티티를 own 하고 자기 스코프가 이를 govern 한다(`_provision`).
- `created_in`(session → project, user): 생성된 곳이 이를 own 하고 govern 한다. own 을 통해 프로젝트의
  역할이 session 에 접근해 목록에 올리고, govern 을 통해 session 이 own 하는 것(invitation)에 접근한다.
  domain 은 user 의 virtual entity 를 govern 하므로 user 가 own 하는 session 에 접근한다.
- project 와 user 도 domain 을 `created_in` 한다. domain 이 이들을 own 하고 govern 한다. own 은 해석에
  추가하는 것이 없지만(자기 own 과 govern 이 이미 접근한다) 해가 없고 스코프와 resource 엔티티를 하나의
  규칙 아래 둔다. user 의 virtual entity 는 domain 만 govern 한다. project 가 govern 하면 user 가 own 하는
  것이 프로젝트로 새어 나간다(BEP-1077).
- 예전 `member_of` 도 둘을 모두 썼다. 이름이 own 만 말해서 govern 이 가려졌다.
- share(`replace_share` / `replace_share_fields`)는 받는 스코프에 빌려준 cap 있는 own 이다. own 은
  virtual entity 에 붙으므로 이를 govern 하는 모든 스코프에 속하고, share 는 그 virtual entity 의 스코프
  하나에 주어지므로 그 스코프의 자기 govern 으로만 반환한다. 그래서 resolver 는 (1) 공유 엔티티의 type
  에만, (2) 자기 govern 을 통해서만 share 를 지나간다. 스코프로 취한 공유 vfolder 는 그 아래 invitation 을
  읽지 않고, resource group 에 공유된 project 는 그 resource group 을 govern 하는 다른 project 가 읽지
  않는다.
- relation(`create_relation(scope, target)`): 스코프가 cap READ 로 target 을 govern 하고 target 은 READ
  share 로 스코프를 보유한다. project 는 resource group 과 그 agent 를 읽고, resource group 은 project
  자체만 읽는다. project 가 own 하는 user, session, vfolder 는 보이지 않는다. govern 쪽 cap
  (`scope_bindings.permission_cap`)은 relation 만 쓴다. 자기 govern 과 `created_in` govern 은 cap 을
  갖지 않는다.
- relation 테이블은 양쪽에 cascade 외래 키를 가진다(`association_container_registries_groups`,
  `sgroups_for_groups`). 엔티티가 사라지면 그 row 도 함께 사라지고 어느 ops 메서드도 한쪽 전체를 지정하지
  않는다. relation spec 은 pair 의 id type 으로 typed 되므로 spec 이 각 id 를 제 type 으로 읽는다.
- resource group 이 session 과 deployment 를 보는 것은 relation 이 아니다. scheduling 때 session 을
  resource group 에 READ 로 공유해 응답한다(후속). 그 resource group 을 govern 하는 다른 project 는
  share 로 응답을 받지 않으므로 새지 않는다.
- 두 축으로 네 루트다. `created_in` 유무(Entity / Global) × 프리셋 역할 유무(plain / RoleManaged).
  role-managed 는 plain 과 같은 relation 에 프리셋을 더한다.
- every-field share 와 field-path share 는 의미가 다르고 메서드도 다르다. 저장은 하나의 cap row tree(bit
  마다 row, path row)이지만 선언이 둘을 섞지 않는다. replace 는 앞의 것을 모두 버리고(delete 와 insert,
  읽지 않는다), widen 은 있는 것을 읽어 추가만 하고, narrow 는 제거만 한다. 섞인 share 는 replace 후
  widen 으로 쓴다.
- relation ops 의 위치. private 기본 연산은 `V2GraphWriteOpsBase` 에만 있고 어떤 provider 도 이를
  제공하지 않는다. 공개 표면은 provider / ops 세 쌍이다.

| relation | write | reverse | 쓰는 쪽 |
|---|---|---|---|
| node | `_provision(entities)`: node, 자기 own, 자기 govern | `_teardown(entity)`: 나머지는 FK cascade | create / purge |
| own | `_created_in` 의 일부로만 쓴다 | `_disown(owners, entity)` | project 를 떠나는 user |
| govern | `_govern(scopes, entity, cap)` | `_ungovern(scopes, entity)` | relation(cap READ) |
| own + govern | `_created_in(scopes, entity)`: node 조회 하나 | `_removed_from(scopes, entity)` | create(프리셋 역할 포함), transfer |
| share(cap 있는 own) | `_reset_share(scope, entity)` / `_widen_share(scope, entity, {bit: paths})` / `_narrow_share` | `_unshare(scope, entities)` | relation, share write |

| pair | provider / ops | 메서드 |
|---|---|---|
| entity write | `V2DBOpsProvider` / `V2WriteOps` | create / upsert / purge / update / field / batch. create 에 `_created_in`, purge 에 `_teardown` |
| relation write | `RelationOpsProvider` / `V2RelationWriteOps` | `create_relation(creator, scope, target)` / `delete_relation` / `restore_relation` / `purge_relation`: `_govern(cap READ)` + `_widen_share(READ)` |
| share write | `ShareOpsProvider` / `V2ShareWriteOps` | `replace_share` / `replace_share_fields` / `widen_*` / `narrow_*` / `unshare` / `transfer` / `accept_invitation` |

  뒤의 두 ops 는 `V2WriteOps` 를 확장하므로 row write 와 relation write 가 하나의 transaction 을 공유한다
  (vfolder 의 permission row + share, invitation row 의 update + share). "grant" 는 role 에 권한을
  부여하는 것과 겹쳐 쓰지 않는다.
- 한계: govern 은 한 홉이므로 domain → user → session → invitation 세 단계에서 domain 은 invitation 에
  접근하지 못한다. 필요하면 govern 을 쓸 때 상위 스코프의 govern 을 함께 복사해 닫는다.

## 엔티티 type 은 열린 문자열이다

- 권한 계층이 알기 전에 새 type 이 member 를 등록할 수 있게 하려는 규칙이다. 권한을 나르는 경로만 지연
  변환하고 거기서 거부한다.
- 등록 시점 무결성 보장은 "node 가 없는 target 에 대한 write 는 실패한다" 이다.
- 스코프 type 과 엔티티 type 을 나누던 축은 spec hook 에서 사라졌다. 모든 엔티티가 node 를 가지므로
  나눌 것이 남지 않았다.
