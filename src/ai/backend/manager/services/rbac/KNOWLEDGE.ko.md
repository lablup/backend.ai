# RBAC 그래프 쓰기: 배경

> 규칙: `../AGENTS.md`. 설계: `proposals/BEP-1075-entity-relation-operations.md`,
> `proposals/BEP-1076-project-membership.md`, `proposals/BEP-1077-project-scoped-ownership.md`.

권한 그래프를 구성하는 연산은 그 대상 도메인이 아니라 여기에 연결한다. container registry 의
허용된 프로젝트와 자원 그룹의 도메인은 서로 다른 두 짝에 대한 같은 연산인데, 각각 자기
도메인에 있던 동안에는 요구하는 권한이 그 도메인의 권한뿐이었다.

## processor field

`backend.ai mgr ops list --concern rbac` 는 연결된 목록을 출력한다. 그 출력이 엔티티
타입, 모양, 연산, gate, backing 을 나타낸다.

## relation 이 소유 도메인의 연산이 아닌 이유

- registry 의 허용된 프로젝트는 updater field 로 전달되곤 했다. 그래서 registry 의 UPDATE
  권한만으로 호출자가 row 를 기록할 수 있었고 프로젝트에는 권한을 요구하지 않았다.
- relation 은 스코프 둘을 지정하고 엔티티 타입은 지정하지 않으므로, 양쪽에 권한을 요구하고
  어느 쪽도 다른 쪽을 대신하지 않는다.
- 자원 그룹의 association 연산 네 개에는 mapping row 옆에 두 번째 row 를 기록하는 binder 가
  있었다. relation ops 는 대신 그래프를 기록한다. 스코프가 READ 로 대상을 govern 하고,
  대상이 READ share 로 스코프를 보유한다.

## action 네 개가 모든 relation 을 처리한다

- `CreateRelationAction`, `PurgeRelationAction`, `DeleteRelationAction`,
  `RestoreRelationAction` 은 짝과 어떤 relation 인지 나타내는 spec 을 갖는다. 그래서
  방향마다 연결 하나가 registry, 자원 그룹, 유휴 검사기 할당, 그리고 앞으로 추가될 relation
  을 처리한다.
- lifecycle 방향 둘은 lifecycle column 을 가진 relation 을 위해 있다. 하나를 끄면 row 와
  양쪽이 서로 읽는 내용이 남으므로, 꺼진 relation 도 양쪽 목록에 남고 다시 켤 수 있다.
- spec 은 요청을 읽는 곳에서 고른다. adapter 는 registry 의 프로젝트나 자원 그룹의 허용
  목록을 가지고 어떤 relation 을 보는지 알지만, service 와 repository 는 알지 못한다.
- 한 실행은 요청이 지정한 모든 짝을 담으므로 호출자가 service 를 반복 호출하지 않는다.
  엔티티는 몇 개의 짝이 지정하든 한 번만 권한을 요구하고, 응답은 짝 단위다.
- 이미 연결된 짝은 ops 에서 건너뛰고 `False` 로 응답한다. 같은 짝을 두 번 지정하는 것을
  호출자가 피할 필요가 없으므로, 어느 호출부도 중복을 잡지 않는다.
- 이미 연결된 짝도 그래프 읽기(govern 과 share)를 다시 등록한다. 등록은 idempotent
  하므로, 그래프 row 없이 row 만 남은 짝은 다시 생성할 때 채워진다.
- 감사 로그 row 는 방향(`create_relation`, `purge_relation`, `delete_relation`,
  `restore_relation`)과 지정한 스코프를 기록한다. relation 을 구분하는 것은 이름이 아니라
  짝이다.
- 여러 짝에 대한 실행이 무엇을 *의미*하는지는 여전히 호출자가 정한다. registry 의 "연결된
  것이 없는데 제거하면 에러가 난다"는 반환된 응답을 센다.

## roster 는 스코프 안에 담기는 경우다

- 프로젝트 안의 사용자는 스코프 하나이지 둘이 아니다. `scope_targets` 는 프로젝트이고
  `entity_type` 은 `user` 다(BEP-1076). relation 이 아니라 scope action 이다.
- 등록과 역할 부여는 하나의 ops primitive 에서 처리한다. 호출자가 지정한 역할 없이 roster
  에 있는 사용자는 그 연산이 남겨도 되는 상태가 아니다.
- `join_member` 와 `join_members` 는 같은 검사로 받을 사용자를 고른다. 프로젝트 도메인의
  사용자만 받고, 이미 roster 에 있는 사용자는 그대로 둔다. membership row 와 cap 은 다시
  기록하지 않는다.
- 받지 않은 사용자는 `join_members` 에서 결과에서 빠지고, `join_member` 에서는
  `ProjectMemberNotJoinableError` 로 거부된다.

## 개인 프로젝트 거부는 ops 불변 조건이다

- 개인 프로젝트는 함께 생성된 사용자 외에 멤버를 받지 않는다. 거부는 `V2RosterWriteOps` 에
  있으므로 어느 경로도 이를 우회하지 못한다.
- 사용자 provisioning 경로는 대신 기반 primitive 로 멤버를 추가한다. 소유자가 이런
  프로젝트가 받는 유일한 멤버이기 때문이다.
- 사용자가 등록된 프로젝트는 여러 호출자가 좁히는데, 각자 적용하는 필터는 각자 빠뜨릴 수
  있는 필터다.
- 없는 프로젝트에 대한 roster 쓰기도 같은 이유로 거부한다. 대상이 없는 간선은 어느
  호출자도 요청하지 않은 상태다.

## roster 는 그래프 그 자체다

- roster 항목은 그래프 간선과 그 cap 이다. roster 읽기는 그래프에서 응답하며, BA-7796
  이후로는 다른 곳에서 응답할 수 없다.

## 역할 부여도 roster 항목이다

- 프로젝트 스코프 역할을 부여하면 그 사용자를 프로젝트 멤버 목록에 추가하고, 그곳의 마지막
  역할을 회수하면 목록에서 제거한다. 두 쓰기는 하나의 연산이므로 역할 카탈로그가 아니라
  roster 옆인 여기에 있다.
- bulk 역할 부여는 사용자 단위로 실패한다. roster 에 참여할 수 없는 사용자와 부여가 실패한
  사용자는 실패 목록으로 보고되고 나머지 사용자는 통과한다.
- 역할 카탈로그에 남는 것은 역할 자체와 그 권한이다. 역할 생성, 수정, 조회는 그래프 쓰기가
  아니다.
- 이 네 연산은 아직 legacy action 기반에 있다. 역할 도메인의 v2 계보 이전이 진행 중이며,
  이 연산들도 그곳으로 따라간다.
