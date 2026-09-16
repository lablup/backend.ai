---
name: service-catalog-adapter-scenarios
type: reference
description: what the service catalog adapter guarantees, as scenarios; a single search behind the superadmin role that the monitor role also passes, rows laid through the registration spec and so always healthy, endpoints carried whole
scope: src/ai/backend/manager/api/adapters/service_catalog
keywords: [service catalog, scenario, adapter, superadmin, monitor, search, endpoints]
generated:
  by: claude-code/opus-5
  at: 2026-09-16
status: draft
---
# service_catalog 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

이 어댑터가 제공하는 호출은 검색(`admin_search`) 하나다. 카탈로그 행은 서비스가 스스로 등록하고
heartbeat를 보낼 때 이벤트 처리기가 기록하며, 관리자가 생성·수정·삭제하는 호출은 없다. 검색은
전역 역할이 있어야 하고, 읽기 연산이므로 모니터 역할의 사용자도 권한 검사를 통과한다.

행을 만드는 write spec은 등록 처리기가 쓰는 upsert spec 하나다. 그 spec은 상태를 언제나 정상으로
기록하므로, 시나리오가 만드는 서비스는 모두 정상 상태다. 등록 해제 처리와 heartbeat가 끊긴
서비스를 비정상으로 바꾸는 처리는 spec 없이 행을 직접 수정하므로, 시나리오는 그 상태의 서비스를
만들 수 없다.

## 검색

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 검색한다 | 서비스 둘, 그중 하나에 엔드포인트 하나, 전역 역할 있음 | 전체 조회 | 둘 다 반환되고, 엔드포인트도 함께 반환된다 |
| `service_group` 필터로 검색한다 | `service_group` 값이 다른 서비스 둘, 전역 역할 있음 | `service_group` 필터로 조회 | `service_group` 값이 일치하는 서비스만 반환된다 |
| 상태가 같은 것을 고른다 | 정상 서비스 둘, 전역 역할 있음 | `equals` 조건에 정상을 지정해 조회 | 둘 다 반환된다 |
| 상태가 다른 것을 고른다 | 정상 서비스 둘, 전역 역할 있음 | `not_equals` 조건에 정상을 지정해 조회 | 아무것도 반환되지 않는다 |
| 상태 목록에 든 것을 고른다 | 정상 서비스 둘, 전역 역할 있음 | `in` 조건에 비정상·등록 해제를 지정해 조회 | 아무것도 반환되지 않는다 |
| 상태 목록에 들지 않은 것을 고른다 | 정상 서비스 둘, 전역 역할 있음 | `not_in` 조건에 비정상·등록 해제를 지정해 조회 | 둘 다 반환된다 |
| 페이지 크기를 생략한다 | 서비스 11개, 전역 역할 있음 | `limit` 없이 조회 | 10건까지 반환되고 다음 페이지가 있다고 응답한다 |
| 모니터 역할이 검색한다 | 서비스 둘, 모니터 역할 | 전체 조회 | 슈퍼관리자와 같은 응답 |
| 슈퍼관리자가 아닌 사용자가 검색한다 | 전역 역할 없음 | 전체 조회 | 역할 부족으로 거부 |

상태 필터는 `equals`, `in`, `not_equals`, `not_in` 네 조건을 받고, 상태가 같은 것·다른 것·목록에
든 것·목록에 들지 않은 것을 검색하는 시나리오가 조건을 하나씩 확인한다. 시나리오가 만드는 서비스가
모두 정상 상태이므로, 각 조건마다 전부 반환되거나 아무것도 반환되지 않는 경우만 확인한다. 상태가
섞인 서비스 중 지정한 상태만 반환하는 시나리오는 "아직 적지 않은 것"에 있다.

요청 타입에는 `first`·`after`·`last`·`before` 필드가 있지만 이 검색은 페이지 크기(`limit`)와
`offset` 값만 읽는다. 커서 필드를 함께 지정하면 지금은 오류 없이 무시된다. 커서 시나리오는 이 필드를
무시할 것인지 사용할 것인지 정한 뒤에 적는다.

## 아직 적지 않은 것

| 시나리오 | 왜 |
|---|---|
| 상태가 섞인 서비스 중 지정한 상태의 서비스만 반환된다 | 정상이 아닌 상태를 기록하는 write spec이 없다. 등록 해제와 stale 정리가 행을 직접 수정하므로, 그 상태의 서비스를 만들 방법이 생기면 옮긴다 |

`batch_load_fields`는 모든 어댑터가 상속하는 공용 메서드이지 이 엔티티의 호출이 아니다. 리포트의
호출 집계에는 포함되지만 이 문서에 적을 시나리오는 없다.
