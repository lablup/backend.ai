# Manager Actions: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 계층이 존재하는 이유

모든 service 동작을 하나의 균일한 envelope 로 감싸 authorization, auditing, metrics 를 handler 마다 다시 구현하지 않고 구조적으로 적용한다. 이 계층을 우회하는 동작은 셋 다 받지 못한다. handler 가 service 가 아니라 processor 를 호출하는 이유다.

## 권한은 유도되고 action 이 선언하지 않는다

- v2 base 는 대상의 모양으로 action 을 분류한다. 모양 목록은 `AGENTS.md` 에 있다.
- 필요한 권한은 `operation_type()` 에서 유도한다. action 이 권한을 선언하지 않으므로 둘이 어긋날 수 없다.
- `RESTORE` 만 의도적으로 나뉜다. 동작과 감사 레이블은 restore 이고 검사하는 권한은 soft-delete 다. 새 permission bit 는 없다.

## 자기 scope 이 없는 엔티티도 id 로 지정된다

- super admin 은 entity gate 를 통과하므로 동작이 `single_entity` 든 `bulk` 든 admin 경로는 열려 있다.
- 아직 어느 흐름도 한 엔티티에 권한을 부여하지 않지만 super admin 은 여전히 부여할 수 있다. 동작을 `global` 로 올리면 그 경로가 사라진다.
- `global` 은 아무것도 지정하지 않으므로 `entity_id()` 를 가지지 않는다. 감사 추적을 위해 하나 추가하면 그것을 authorization 입력으로 읽게 된다.

## backing 은 모양과 직교한다

- `OpsBackendAction` mixin(`actions/v2/ops/`)은 두 번째 독립 축이다. 실행 방식에 대한 축이다.
- pass-through action 은 repository spec(`to_creator()`, `to_searcher()` 등)을 가지며 generic service 에서 실행된다. RBAC 과 감사는 shape 축이 계속 맡는다.
- 동작에 분기가 생기는 순간 service 메서드로 승격한다. generic 경로에는 분기를 숨길 hook 이 없다.

## soft delete 는 action 이 재분류하는 update 다

- DB 동작은 UPDATE 이므로 ops 에 일반화할 delete 가 없다. update 경로 하나가 둘 다 처리한다. 분리는 한 계층 위에 있다. action 이 `operation_type() == DELETE` 를 선언하고 RBAC 검사와 audit row 의 `operation` column 이 그것을 읽는다.
- 따라서 guard 는 ops 가 아니라 spec 에 있다. 일반 updater 가 lifecycle column 을 노출하지 않으므로 일반 편집 경로에는 그 전이를 수행할 field 가 없다. update 모양 action 으로 전이에 도달하면 삭제가 `UPDATE` 로 기록되어 추적에서 사라진다.
- generic delete service 는 의도적으로 update 형제와 byte 단위로 같다. delete 형 action class 를 배선 지점에 묶기 위해 존재하고, 다른 것을 실행하려는 것이 아니다.

## field row 의 동작은 소유 엔티티가 처리한다

- 검증과 감사 추적 모두 어느 엔티티에 대한 것인지 질문한다. field row 는 자기 membership 을 갖지 않으므로 그것을 지정하는 동작은 소유 엔티티를 먼저 읽어야 응답할 대상이 생긴다.
- 그 읽기는 lookup action 으로 실행된다. 사라진 row 를 지정하는 요청은 `lookup_kind` / `lookup_key` 에 key 가 있는 lookup 실패를 남긴다. field id 가 추적에 들어가는 곳은 여기뿐이다.
- 소유 엔티티의 id 는 요청에서 가져오지 않는다. 둘이 그 관계에 있다는 확인에 같은 질의가 필요하고, 확인 없이 신뢰하면 호출자가 다른 사람의 row 옆에 자기 owner 를 전달할 수 있다.
- 모든 field write 는 `UPDATE` 다. row 를 추가하거나 제거하는 것은 그 엔티티의 변경이고 그 엔티티의 권한이 처리한다. 별도 permission bit 는 그것과 어긋난다.

## relation 은 scope 둘을 지정하고 kind 를 지정하지 않는다

- link 의 모양은 포함 관계를 따른다. user 는 project 안에 있으므로 scope 모양이다. scope 하나와 그 안에 포함된 type 이다. resource group 은 여러 domain 이 공유하는 cluster 자원이라 어느 쪽도 다른 쪽 안에 있지 않고 둘 다 지정한다.
- 둘 다 지정하면 둘 다 질문한다. entity type 이 없으면 scope 에서 읽을 것이 없으므로 질문은 scope 자체의 권한으로 줄어든다. bulk validator 가 이미 질문하는 entity 질문이다. 거부된 scope 하나가 실행 전체를 거부한다. row 가 둘 모두에 대한 것이므로 남은 부분집합이 없다.
- bulk 모양이 아니다. bulk 는 엔티티마다 한 번 실행하고 엔티티마다 응답한다. link 는 한 번 실행하고 한 번 응답한다.
- audit row 는 entity 도 kind 도 지정하지 않는다. 기록된 것은 두 엔티티 사이에 있고 어느 쪽도 아니다. scope 는 `audit_log_scopes` 로 가고 `audit_logs.entity_type` 이 NULL 을 허용하는 이유다. reporter 는 scope 마다 메시지 하나를 계속 내보낸다. 모든 scope 가 엔티티이고 각각 자기가 무엇인지로 보고되기 때문이다.
- relation 에서 권한을 유도하는 방식은 기각했다. 여러 relation 을 거쳐 같은 엔티티에 도달하면 해지가 참조 계수가 되고, business 동작의 부수 효과로 기록된 권한은 role 과 grant 로 설명할 수 없다.
- 근거: `proposals/BEP-1075-entity-relation-operations.md`.

## field bulk 는 row 마다 응답하고 엔티티마다 기록한다

- 응답은 호출자가 지정한 row 마다다. owner 로 합치면 한 owner 안에서 어느 항목이 실패했는지 잃는다.
- 기록은 소유 엔티티마다다. field id 는 entity column 에 들어갈 수 없다. 어느 row 였는지는 description 에 들어간다.
- 끝이 다른 한 owner 의 row 도 합치지 않는다. 실패는 서로 다른 description 을 가지므로 어차피 합쳐지지 않고, volume 은 retention 문제다.
- batch owner 읽기도 lookup action 이다. repository 로 바로 가면 그 읽기가 기록되지 않고 없는 row 도 언급되지 않는다. bulk lookup processor(`field_group` 은 owner 용으로, `bulk_lookup_ops` / `public_bulk_lookup_ops` 는 entity key 용으로 생성한다)는 key 마다 응답하고 아무것도 지정하지 않은 key 는 실패한 실행이 아니라 실패한 key 다.

## many-row write: 실패 모드는 이름으로 정하고 인자로 두지 않는다

- `atomic_*` 는 모든 row 를 함께 플러시하고 첫 실패에서 예외를 발생시킨다. 실행은 엔티티를 지정하지 않은 실패 하나를 기록한다. 아무것도 기록되지 않았고 어느 row 도 탓할 수 없기 때문이다.
- `partial_*` 는 항목마다 savepoint 로 격리하고 항목마다 응답한다. 실행 자체는 성공하고 판정을 담는다.
- flag 로 고를 수 없다. 반환 type 이 다르고(`list` 대 `BulkResultWithFailures`) 그 type 이 generic service, action result, processor 를 거쳐 전파된다. 값 하나가 네 계층의 type 을 결정할 수 없다.
- `Bulk` 는 `BaseBulkAction` 모양을 의미한다. 호출자가 엔티티를 지정했으므로 각각 응답한다. 대상이 scope 하나, owner 하나, system 인 many-row write 는 bulk 모양이 아니므로 atomic create 는 scope, single-entity, global 모양이다.

## 감사 원칙: write 는 항상, 읽기는 구독 시, 실패는 항상

- write 기록은 설정으로 비활성화할 수 없고, 성공한 읽기는 구독할 때만 기록하며, 실패는 권한 거부(`DENIED`)를 포함해 항상 기록한다(`audit_policy.py`).
- 검증은 monitor lifecycle 안에서 실행되어 거부도 row 를 남긴다.
- 참조 구조는 GCP audit 설정이다. admin activity 는 항상 활성, data access 는 선택, policy denial 은 항상 활성이다.
- bulk 는 대상마다 row 하나를 자기 상태와 함께 기록한다. 단일 row 대안(JSON 배열, 자식 테이블)은 대상별 조회를 volume 과 맞바꾸고, volume 은 schema 문제가 아니라 retention 문제다.

## lookup 은 존재를 누설하면 안 된다

- lookup 은 권한 검사 전에 key 를 해석하므로 구분 가능한 "not found" 는 권한 없는 호출자에게 존재를 누설한다. lookup miss 와 권한 거부가 같은 응답 모양을 가져야 하는 이유다.
- lookup metric 은 key 의 모양으로만 레이블을 붙인다. 값 레이블은 cardinality 폭증이다.
- 이 metric 은 legacy 정리 지표를 겸한다. counter 가 0 에 머무는 lookup 은 삭제할 수 있다.

## public 은 anonymous 가 아니라 인증된 모든 사용자다

- `PublicActionProcessor` 는 global gate 를 인증 검사로 교체하고 다른 것은 하지 않는다.
- action class 와 함께 생성되는 유일한 processor 이므로 요청 시점이 아니라 구성 시점에 write 동작을 거부한다.
- 아무도 로그인하기 전에 실행되는 읽기는 따라서 자기 processor 가 없다. `ScopeActionProcessor` 는 gate 를 고정하지 않으므로 `ProcessorGroup.anonymous_scope` 가 class 추가 없이 하나를 배선한다. 읽기 동작만 받고 구성 시점에 검사한다.
- 어떤 principal 도 도달할 수 없는 write(엔티티가 저장한 secret 으로 인증되는 외부 system 의 webhook 게시)는 달리 갈 곳이 없으므로 `AnonymousGlobalActionProcessor` 가 validator 없이 실행한다. 배선을 anonymous gate 로 기록하는 것이 그 집합을 셀 수 있게 유지한다.

## global action 은 global singleton 이 처리한다

- global action 은 scope 를 지정하지 않는다. 어디에도 속하지 않는 것과 같지 않다. `global` singleton 이 그 scope 이고 action 의 entity type 에 부여하는 bit 가 gate 다.
- 검사는 type 으로 한다. 질의에 scope 조건을 두지 않으므로 global 권한을 위임받은 user 는 그 type 의 모든 row 를 읽는다. project 나 user 에 속한 자원에 대한 global search 도 다르지 않다.
- super admin 과 읽기의 monitor 는 user role 에서 바로 통과한다. role row 없이 동작하던 것이 계속 동작하고 둘 다 권한 읽기를 소비하지 않는다.
- 강제 적용 switch(`manager.rbac.enforcement_enabled`)가 꺼져 있으면 그 두 우회만 남고 나머지는 모두 거부된다. 꺼져 있는 동안 permission row 가 유지된다는 보장이 없으므로 fall-back 은 호출자를 통과시키는 것이 아니라 이전 동작인 super admin 전용이다.
- role 편집기가 제공하는 목록(`role_grantable_wirings`)은 global 배선을 포함하지 않는다. `role_scope_types` 가 `global` 을 지정하지 않고 matrix 에 그 축이 없기 때문이다. gate 는 동작하지만 그 목록으로 위임할 role 은 아직 생성할 수 없다.

## registry 가 catalog 다

- `ProcessorRegistry.wired_actions()` 는 등록된 action class 를 모두 누적한다. 실제로 사용 중인 것의 권위 있는 catalog 다.
- sweep test 는 v2 base 의 `__subclasses__()` 를 배선과 비교한다. 존재하지만 등록되지 않은 action 은 dead code 가 아니라 test 실패다.
- 같은 sweep 이 `action_name()` 의 유일성을 검사한다. entity type 은 더 이상 class 에서 읽을 수 없다. single-entity action 은 id 에서 유도하고 field action 은 owner 를 읽기 전까지 가지지 않으므로 이름만으로 두 실행을 구분해야 한다.

## catalog 를 읽는 명령

- `backend.ai mgr ops list` 는 모든 배선 기록을 출력한다. `--concern`, `--entity`, `--field`, `--operation`, `--gate`, `--backing` 으로 필터하고 `--output json|tsv` 로 형식을 변경한다. `backend.ai mgr ops entities` 는 entity type 과 그 아래 field type 을 출력하고, `backend.ai mgr ops describe <entity_type> <action_name>` 은 한 동작의 입력 field 와 정의 위치를 추가한다.
- 배선이 concern, entity_type, field_type, kind, gate, backing 을 결정하므로 action class 는 어느 것도 가지지 않는다. class 는 operation 과 action_name 을 선언한다.
- 영역은 `Concern` member 로 선언하고 각각 무엇을 담는지 한 항목을 둔다. 새 domain 은 새 이름을 두지 않고 그중 하나를 고른다.
- 어느 의존성 stage 도 시작하지 않는다. 조립은 handler 를 호출하지 않고 저장하므로 runtime 대신 stand-in 이면 충분하다. database, leader election, event consumer 가 없고 실행 중인 Manager 와 충돌하는 것도 없다.
- registry 가 기록한 것만 나타난다. legacy base 에 남은 processor 는 `ProcessorGroup` 밖에서 배선되어 목록에 없다.
