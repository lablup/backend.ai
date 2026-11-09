# 유휴 검사기 할당 service: 배경

> 규칙: `../AGENTS.md`. Spec 선택: `../../models/specs/KNOWLEDGE.md`. Relation
> 근거: `proposals/BEP-1075-entity-relation-operations.md`. Definition
> 카탈로그: `../idle_checker/KNOWLEDGE.md`.

## 할당은 relation 이다

- `idle_checker_bindings` 는 스코프와 유휴 검사기를 연결한다. 스코프는 도메인, 프로젝트,
  자원 그룹, 사용자 중 하나다. BEP-1075 는 이 테이블을 relation 테이블로 분류한다. 양쪽이
  own 하므로 엔티티도 field 도 아니고, 가상 엔티티 노드도 받지 않는다.
- 스코프는 relation 의 스코프이고 검사기는 그 대상이다. container registry relation 에서
  프로젝트가 스코프인 것과 같다. 연결하면 스코프가 READ 로 검사기를 govern 하고 검사기가
  스코프를 읽는다.
- `enabled` 는 row 의 lifecycle column 이다. 이 값을 전환하는 동작은
  `DeleteRelationAction` 과 `RestoreRelationAction` 이다. row 만 변경되고 양쪽 읽기는
  그대로라서, 비활성화된 할당도 목록에 남고 다시 활성화할 수 있다. 비활성화된 상태를 반영하는 것은
  reconciler 의 역할이다.

## 모양

| Action | 모양 | 연결 경로 | 권한을 판정하는 엔티티 |
|--------|-------|--------|-----------------|
| 연결, 비활성화, 다시 활성화, 연결 해제 | relation | `services/rbac` | 스코프와 검사기 각각 자기 자신 |
| lookup, 짝으로 lookup | lookup | `group.lookup` | 확인된 검사기에 대한 READ |
| admin_search | global | `group.global_scope` | SUPERADMIN gate |
| scoped_search | scope | `group.scope` | 지정한 모든 스코프의 `idle_checker` 에 대한 READ |

- 네 쓰기는 rbac 경계의 relation action 네 개이며, 이 도메인의 creator, lifecycle
  updater, purger 를 값으로 갖는다. 이 도메인은 자체 relation action 을 선언하지 않는다.
  한 실행이 어떤 relation 에 대한 것인지는 spec 이 담으므로, 방향마다 연결 경로 하나가 이 시스템이 사용하는
  모든 relation 을 처리한다.
- relation 쓰기는 짝만 반환하므로, adapter 는 payload 를 구성하려고 `lookup_by_pair` 로
  할당을 다시 읽는다.
- 읽기와 lookup 은 relation 이 연결하는 대상, 곧 검사기를 읽는다. 그래서 `idle_checker`
  그룹을 사용하고 그 타입을 선언한다. 스코프 읽기 권한자는 연결이 부여한 READ govern 을
  통해 할당의 검사기를 본다.
- 스코프 row 는 creator 의 전제 조건이다. 짝에서 스코프 쪽은 foreign key 를 갖지 않으므로,
  spec 이 있어야 하는 row 를 선언하고 relation 쓰기는 노드를 찾기 전에
  `IdleCheckerAssignmentScopeNotFound` 로 거부한다.
- 할당은 legacy source 에 접근하지 않는다. 쓰기는 relation 쓰기 ops 로, 읽기는 같은
  provider 의 읽기 ops 로 가며, 늘 searcher 로 처리한다. row id 는 엔티티 id 가 아니므로
  querier 가 그것을 지정하지 않는다. reconciler 의 읽기는 다른 읽기와 같은 legacy source 에 남는다.

## API 가 지정하는 id 를 먼저 조회로 확인한다

- REST 와 GQL API 는 할당 id 로 변경과 purge 를 하지만, relation 은 짝으로 지정한다.
  adapter 는 lookup 을 실행해 id 를 짝으로 변환한 뒤 relation action 을 실행한다.
- lookup 이 확인하는 엔티티는 검사기이므로 확인에는 검사기에 대한 READ 가 필요하고, 스코프
  읽기 권한자는 스코프의 govern 으로 그 권한을 갖는다. 검사기를 어디에서도 읽지 못하는
  호출자는 lookup 모양의 단일 응답을 받는다. id 존재 여부를 감추는 400 이다. 다른
  스코프로 검사기를 읽는 호출자는 짝을 확인한 뒤 relation 검사에서 403 으로 거부된다.
- BEP-1075 에서 relation 의 row id 는 API 밖으로 나가지 않는다. 이 방식은 API 모양을
  그대로 두면서 그 규칙을 따른다. API 에서 짝을 지정하는 후속 작업이 lookup 을 제거한다.

## 할당에 대한 권한이 지정해야 하는 것

- relation 은 양쪽이 권한을 판정한다. 프로젝트 할당을 비활성화하려면 프로젝트와 검사기 모두에
  SOFT_DELETE 가 필요하고, 연결을 해제하려면 양쪽에 HARD_DELETE 가 필요하다. 스코프
  부여만으로는 충분하지 않다.
- 검사기는 global 엔티티이므로 superadmin 이 아닌 사용자는 검사기를 지정한 부여가 필요하다.
  실제로 그러한 부여가 없는 스코프 관리자는 그 스코프의 할당을 활성화하고 비활성화할 수 없다.
- 사용자 자신의 스코프에 있는 할당은 그 사용자를 지정한다. 사용자가 속한 프로젝트의 권한은
  그 할당에 적용되지 않는다.

## 두 검색, 두 gate

- `scoped_search` 는 모든 스코프를 미리 지정하고, 하나라도 접근할 수 없으면 요청 전체를
  거부한다. 그다음 row 를 스코프에 걸쳐 OR 로 묶는다. relation 읽기는 relation 이 연결하는
  대상을 반환하므로, 결과는 페이지가 접근한 검사기를 보고한다.
- `admin_search` 는 SUPERADMIN gate 뒤에서 테이블 전체를 읽는다.
