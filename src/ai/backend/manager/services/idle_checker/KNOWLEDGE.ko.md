# 유휴 검사기 서비스: 배경

> 규칙: `../AGENTS.md`. 스펙 선택: `../../models/specs/KNOWLEDGE.md`.

유휴 검사기 정의는 시스템 전역 카탈로그 항목이다. session 을 제외하거나 포함하는 것은 그 정의를 session 하나에서 비활성화하는 수정이다. 후자는 전자 없이는 의미가 없고 서로 다른 엔티티가 응답하지만 하나의 패키지를 공유한다.

## processor 필드

`backend.ai mgr ops list --concern session` 는 연결된 목록을 출력한다. 그 출력이 엔티티 유형, shape, 연산, gate, backing 을 응답한다.

## 응답하는 엔티티가 둘이라 그룹도 둘이다

- 카탈로그 연산 넷은 `idle_checker` 그룹에서 나오고, 제외와 포함은 `session` 그룹에서 나온다.
- 그 둘은 검사기가 아니라 session 이 응답한다. session 의 유휴 검사를 비활성화할 권한은 그 session 에 대한 권한이다.
- 그래서 한 패키지가 `ProcessorGroup` 둘을 받는다. 하나로 합치면 한쪽의 감사 row 가 잘못된 엔티티를 지목하게 된다.

## 검사기 정의는 global 이다

- `idle_checkers` row 는 어느 스코프에도 속하지 않는다. domain 이나 project 에 붙는 것은 정의가 아니라 유휴 검사기 할당(`idle_checker_assignment`)이다.
- 정의 단위로 부여하는 것이 없으므로 표현할 엔티티별 권한도, 공유할 것도 없다.
- REST 와 GQL 진입점 넷 모두 직접 작성한 superadmin 검사를 실행하므로 global gate 가 그 진입점들과 일치한다.

## 생성과 수정만 서비스 메서드를 유지한다

- 둘 다 기록하기 전에 다른 엔티티를 읽는다. utilization 스펙이 지목한 prometheus query preset 을 가져오고, 그 preset 이 허용으로 선언하지 않은 filter 와 group label 을 거부한다.
- 다른 repository 를 읽는 검사는 action validator 가 감당하는 범위를 넘고, 스펙은 SQL 을 실행할 수 없다. 서비스 메서드를 유지하는 기준이 이것이다.
- 검사를 지나면 서비스는 action 의 스펙을 변경 없이 ops 에 전달한다. 그 밖의 일은 하지 않는다.

## API 는 하나를 지목하지만 purge 는 bulk 다

- 카탈로그의 delete 는 `global_partial_bulk_purge_ops` 로 연결되고, 이는 엔티티마다 응답한다.
- 현재 REST 와 GQL 진입점은 검사기 하나를 지목하므로 adapter 는 단일 id 목록으로 호출하고, 보고할 수 있는 실패 하나를 raise 한다. API 는 검사기 하나를 지목해 제거하거나 실패한다.
- 삭제된 정의를 참조하는 할당과 session row 는 `ON DELETE CASCADE` 로 함께 삭제된다. 삭제를 차단하는 전제 조건은 없다.

## 없는 row 는 도메인 에러가 아니다

- 없는 row 를 지목하는 수정이나 purge 는 `IdleCheckerNotFound` 가 아니라 `EntityNotFoundError` 를 raise 한다.
- ops 는 식별자에서 엔티티 유형을 읽으므로 코드의 도메인은 같은 `idle_checker` 다. 둘 다 404 이고 `error_type` 문자열만 다르다.
