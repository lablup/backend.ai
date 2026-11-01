# 알림 service: 배경

> 규칙: `../AGENTS.md`. Spec 선택: `../../models/specs/KNOWLEDGE.md`.

알림 채널은 메시지를 보낼 수 있는 대상이고, 알림 규칙은 어떤 event 가 어느 채널로 가는지
정한다. 규칙은 지정한 채널 없이는 의미가 없고, 둘 다 사용자가 own 하는 것이 아니라 시스템
전체 설정이므로 한 패키지에 둔다.

## processor fields

`backend.ai mgr ops list --concern notification_center` 는 연결 및 호출 경로로 처리되는 목록을 출력한다. 그
출력이 엔티티 타입, 모양, 연산, gate, backing 을 나타낸다.

`ProcessorGroup` 두 개가 연결 및 호출 경로로 처리되며, 엔티티 타입마다 하나다. REST route 열셋이 모두
`superadmin_required` 를 선언하므로 global gate 가 API 와 일치한다.

## 여기서는 global 이 적합한 형태다

- 두 테이블 모두 스코프와 연결되지 않는다. 채널은 시스템이 own 하는 endpoint 이고, 규칙은
  그 endpoint 를 향하는 라우팅 항목이다.
- 채널이나 규칙 단위로 부여되는 것이 없으므로 표현할 엔티티별 권한도, 공유할 것도 없다.

## 세 연산은 데이터베이스 밖의 동작을 포함하므로 service 를 유지한다

- `validate_channel` 은 채널로 실제 시험 메시지를 발송한다.
- `validate_rule` 은 시험 데이터로 규칙의 template 을 렌더링한다.
- `process_notification` 은 event 를 규칙과 대조해 메시지를 준비한다.
- 셋 중 어느 것도 ops 계층이 spec 으로 실행할 수 있는 쓰기가 아니다. service 메서드를
  유지하는 기준이 이것이다.

## 규칙 조회는 채널을 함께 반환한다

- 대상 규칙을 찾는 조회는 `MatchingNotificationRuleData` 를 반환하며, 규칙마다 지정한
  채널을 짝지어 반환한다. 규칙만 받은 호출자는 채널을 하나씩 다시 조회해야 하기 때문이다.
- 규칙을 가지고 그 채널을 따로 원하는 호출자는 id 로 채널을 조회한다. 짝은 발송 경로에서
  사용한다.
