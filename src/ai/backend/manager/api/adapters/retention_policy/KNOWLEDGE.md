---
name: retention-policy-adapter-scenarios
type: reference
description: what the retention policy adapter guarantees; the one policy a category holds, the read that needs the entity gate unlike the other catalogs, the purge that the deprecated delete also calls, the partial bulk update and purge, the monitor role passing the search
scope: src/ai/backend/manager/api/adapters/retention_policy
keywords: [retention policy, scenario, adapter, superadmin, monitor, category, purge, partial bulk]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# retention_policy 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

`retention_policy` 정책은 카테고리마다 하나이고 어느 스코프에도 속하지 않게 만들어진다. 생성과
검색은 호출한 사용자가 슈퍼관리자인지 검사하고, id를 지정하는 조회·수정·완전 삭제는 그 정책에 부여된 권한을 검사하지만
그 권한을 받을 방법이 없다. 생성·검색과 조회·수정·완전 삭제 모두 슈퍼관리자만 통과하지만 거부
이유가 서로 다르다.

다른 전역 카탈로그와 달리 id로 하나를 조회하는 것도 권한 검사를 거친다. 인증만 확인하는
카탈로그의 조회 시나리오를 그대로 옮기면, 아무 권한도 없는 사용자의 조회가 통과가 아니라 권한
부족으로 거부된다.

## 생성

`last_swept_at` 값은 요청으로 정할 수 없다. 생성할 때 비어 있고 정리 루프가 나중에 채우며, 이
어댑터의 어느 호출도 그 값을 갱신하지 않는다.

보존 일수가 하루보다 짧은 요청은 시나리오로 두지 않는다. 요청 타입이 이미 거부하기 때문이다.

"모니터 역할이 생성한다"는 검색 절의 "모니터 역할이 검색한다"와 짝이다. 같은 사용자가 검색은 할
수 있고 생성은 할 수 없다.

## 조회

존재하지 않는 id는 슈퍼관리자와 그 밖의 사용자에게 서로 다른 이유로 거부된다. 권한 검사가 먼저
실행되는데 없는 행에는 부여된 권한도 없으므로, 그 검사를 통과하는 슈퍼관리자만 대상을 찾을 수
없어 거부된다. 아래 절들의 없는 id 시나리오도 모두 같다.

## 검색

카테고리가 생성 절에 나열한 8개뿐이라 정책도 8개를 넘지 못한다. 10건을 초과해 다음 페이지를
확인하는 시나리오는 만들 수 없으므로 두지 않는다.

모니터 역할은 슈퍼관리자 검사에서 읽기만 통과한다. 이 엔티티에서 그 차이를 보여 주는 짝은 "모니터
역할이 검색한다"와 "모니터 역할이 생성한다"다.

## 수정

카테고리 중복은 생성할 때와 수정할 때 서로 다른 오류로 거부된다. 생성은 이 엔티티의 오류로
거부하고, 수정은 저장소의 제약 위반을 그대로 전파한다. 시나리오를 적기 전에 하나로 맞출 것인지
정한다.

## 완전 삭제

soft delete 는 없다. deprecated 된 삭제 GQL mutation 과 SDK 메서드는 완전 삭제를 부른다.

## 여럿 수정하기

## 여럿 완전 삭제

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 정책은 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다.
