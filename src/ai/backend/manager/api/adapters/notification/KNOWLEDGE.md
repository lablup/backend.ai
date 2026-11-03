---
name: notification-adapter-scenarios
type: reference
description: what the notification adapter guarantees; channels and rules are global rows only the superadmin reaches, a rule names its channel by id with nothing holding the two together, and the two validations send through the channel or render the template
scope: src/ai/backend/manager/api/adapters/notification
keywords: [notification, channel, rule, scenario, adapter, superadmin, monitor, webhook, email, validate]
generated:
  by: claude-code/opus-5
  at: 2026-09-17
status: draft
---
# notification 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

이 어댑터는 `notification_channel`과 `notification_rule` 두 엔티티를 다룬다. 둘 다 어느 스코프에도
속하지 않게 만들어진다. 생성과 검색은 호출한 사용자가 슈퍼관리자인지 검사하고(검색은 모니터도
통과한다), id를 지정하는 조회·수정·삭제·검증은 그 행에 부여된 권한을 검사하지만 그 권한을 받을
방법이 없다. 그래서 어느 호출이든 슈퍼관리자만 통과하지만 거부 이유가 서로 다르다.

규칙은 채널을 `channel_id` 값으로만 가리킨다. 두 테이블을 잇는 외래 키가 없으므로, 없는 채널
id로 규칙을 만들 수 있고 규칙이 가리키는 채널을 지워도 규칙은 남는다.

호출자는 요청과 별도로 `created_by` 값을 준다. 생성된 행의 `created_by` 값은 그 값이다.

## 채널 생성

`spec`에 `webhook`과 `email`을 둘 다 주면 `webhook` 쪽을 쓴다. 어댑터가 `spec`을 먼저 읽고
`channel_type` 값은 따로 저장하므로, 둘이 어긋난 요청은 행을 쓴 뒤 그 행을 다시 읽어 답을
만드는 자리에서 명세 형식 검사에 걸려 거부된다. 같은 트랜잭션 안이라 쓴 행은 되돌려진다.

이름이 비어 있거나 길이 제한을 넘는 요청은 시나리오로 두지 않는다. 요청 타입이 이미 거부한다.

"모니터가 만든다"는 검색 절의 "모니터가 검색한다"와 짝이다. 같은 사용자가 검색은 할 수 있고
생성은 할 수 없다.

## 채널 조회

모니터는 검색은 통과하지만 id로 하나를 조회하지는 못한다. 검색은 슈퍼관리자 검사가 읽기에 한해
모니터를 통과시키는 반면, id 조회는 권한 검사이고 모니터에게도 부여된 권한이 없기 때문이다.

존재하지 않는 id는 슈퍼관리자와 그 밖의 사용자에게 서로 다른 이유로 거부된다. 권한 검사가 먼저
실행되는데 없는 행에는 부여된 권한도 없으므로, 그 검사를 통과하는 슈퍼관리자만 대상을 찾을 수
없어 거부된다. 아래 절들의 없는 id 시나리오도 모두 같다.

한 번에 여럿을 조회할 때 없는 id는 빈 항목으로, 권한이 없는 id는 거부가 담긴 항목으로 온다.
둘을 구분해 담으므로, 권한이 없는 사용자에게 행이 없다고 답하지 않는다.

## 채널 검색

## 채널 수정

`channel_type` 값은 수정할 수 없다. `spec`만 바꿀 수 있으므로 `webhook` 채널에 `email` `spec`을
주면 생성 절의 어긋난 요청과 같은 경로로 거부된다.

## 채널 삭제

삭제는 행을 지우는 purge다. soft delete는 없다. 규칙이 가리키는 채널을 지워도 막히지 않는 것은 두
테이블 사이에 외래 키가 없기 때문이다.

수정과 purge는 접두어 없는 이름(`updateNotificationChannel`, `purgeNotificationChannel`)이
기본이고 권한 검사만 거친다. 옛 이름(`adminUpdateNotificationChannel`,
`adminDeleteNotificationChannel`, `deleteNotificationChannel`)과 본문에 id를 받는 옛 REST 삭제 경로는
같은 호출로 잇는 deprecated 별칭이고, 슈퍼관리자 검사를 그대로 거친다. 규칙도 같다.

## 여럿 채널 수정

## 여럿 채널 purge

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 채널은 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다. 규칙의 여럿 연산도 같다.

## 채널 검증

검증은 시험 메시지를 그 채널로 실제로 보낸다. 시나리오는 보내는 쪽을 받아 적기만 하는 대역으로
바꿔 돌린다. 보내기가 실패했을 때의 거부는 대역이 만들 수 없으므로 시나리오로 두지 않는다.

## 규칙 생성

`message_template` 값은 만들 때 검사하지 않는다. 깨진 템플릿도 저장되고, 검증에서야 거부된다.

## 규칙 조회

## 규칙 검색

## 규칙 수정

`rule_type` 값과 `channel_id` 값은 수정할 수 없다. 요청 타입에 그 자리가 없다.

## 규칙 삭제

## 여럿 규칙 수정

## 여럿 규칙 purge

## 규칙 검증

검증은 규칙과 그 채널을 읽고, 시험 데이터를 `rule_type`의 형식으로 검사한 뒤, 템플릿을 그려
채널로 보낸다. 시나리오는 보내는 쪽만 대역으로 바꾼다. 형식에 맞지 않는 시험 데이터와 그릴 수
없는 템플릿의 거부는 시나리오로 두지 않는다. 어댑터와 데이터베이스가 결과를 바꾸지 않고, 서비스의
단위 테스트가 검사한다.
