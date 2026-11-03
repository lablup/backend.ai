---
name: login-client-type-adapter-scenarios
type: reference
description: "what the login client type adapter guarantees: the reads open to every authenticated user, the superadmin role on create, the entity gate nobody but a superadmin passes on update and purge, single and partial bulk, the page size of fifty"
scope: src/ai/backend/manager/api/adapters/login_client_type
keywords: [login client type, scenario, adapter, superadmin, public read, page size]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# login_client_type 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

`login_client_type` 엔티티는 global 과 public 양쪽에 소속된다. 생성은 호출한 사용자가
슈퍼관리자인지 검사하고, 지정해 수정·purge 하는 호출은 그 `login_client_type` 행에 부여된
권한을 검사하는데 그 권한은 global 에서만 나온다. 생성과 수정·purge 모두 슈퍼관리자만 성공하지만
거부 이유가 서로 다르다. 조회와 검색은 public 에서 READ 를 검사한다. 모든 계정이 public 소속
역할을 자동으로 받으므로 로그인한 사용자는 모두 읽을 수 있다.

## 생성

이름이 비어 있거나 길이 제한을 넘는 요청은 시나리오로 두지 않는다. 요청 타입이 이미 막기
때문이다.

## 조회

조회는 public 에서 READ 를 검사한다. public 조회 권한만 받은 사용자가 성공하는 시나리오가 그것을
증명하고, 대응하는 거부 시나리오는 생성 절의 역할 부족으로 거부되는 시나리오다. 존재하지 않는 id와
닿을 수 없는 id는 같은 이유로 거부된다.

인증되지 않은 호출은 시나리오로 두지 않는다. 시나리오는 언제나 미리 만들어 둔 사용자로 호출한다.

## 검색

이름 필터가 무엇을 좁히는지와 페이지 방식 — 기본 크기 50, `first`만 지정한 요청을 커서로 읽는지
(BA-7927) — 는 시나리오로 두지 않는다. 필터를 조건으로 옮기고 페이지를 자르는 것은 단위 테스트의
자리다.

## 수정

수정은 대상 id를 요청 본문 밖에서 별도 인자로 받는다. 시나리오가 id를 인자와 본문에 거듭 적지
않도록 이 구조를 유지한다.

존재하지 않는 id는 슈퍼관리자와 그 밖의 사용자에게 서로 다른 이유로 거부된다. 권한 검사가 먼저
실행되는데 존재하지 않는 행에는 부여된 권한도 없으므로, 그 검사를 통과하는 슈퍼관리자만 대상을
찾을 수 없어 거부된다. purge 절의 같은 시나리오도 마찬가지다.

이름 중복은 생성할 때와 수정할 때 서로 다른 오류로 거부된다. 생성은 이 엔티티 전용 오류로
거부하고, 수정은 저장소의 제약 위반 오류를 그대로 전파한다. 시나리오를 적기 전에 하나로 맞출
것인지 정한다.

## purge

이 어댑터에는 soft delete가 없다.

## 여럿 수정하기

## 여럿 purge

여럿 연산은 호출 전체를 거부하지 않는다. 처리한 종류는 처리된 목록에, 처리하지 못한 것은 id 와
이유를 실패 목록에 싣는다.
