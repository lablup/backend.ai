---
name: service-catalog-adapter-scenarios
type: reference
description: what the service catalog adapter guarantees, as scenarios; a single search behind the superadmin role that the monitor role also passes, rows written only by the registration event handler, endpoints carried whole
scope: src/ai/backend/manager/api/adapters/service_catalog
keywords: [service catalog, scenario, adapter, superadmin, monitor, search, endpoints]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# 서비스 카탈로그 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

이 어댑터가 제공하는 호출은 검색(`admin_search`) 하나다. 카탈로그 행은 서비스가 자기를 등록하고
heartbeat를 보낼 때 이벤트 처리기가 직접 쓰며, 관리자가 생성·수정·삭제하는 호출은 없다. 검색은
전역 역할이 있어야 하고, 읽기 연산이므로 모니터 역할도 통과한다.

행을 만드는 write spec이 없다. 시나리오의 상황을 준비하려면 등록 이벤트 처리기가 쓰는 경로를
그대로 사용해야 한다.

## 검색

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 검색한다 | 서비스 둘, 그중 하나에 엔드포인트 하나, 전역 역할 있음 | 전체 조회 | 둘 다 집계되고, 엔드포인트가 함께 담긴다 |
| 서비스 그룹 필터로 검색한다 | 그룹이 다른 서비스 둘, 전역 역할 있음 | 그룹 필터 조회 | 그 그룹의 서비스만 남는다 |
| 상태 필터로 검색한다 | `healthy`인 서비스와 `deregistered`인 서비스가 섞여 있음, 전역 역할 있음 | 상태 필터 조회 | 지정한 상태의 서비스만 남는다 |
| 페이지 크기를 생략한다 | 서비스 11개, 전역 역할 있음 | 크기 없이 조회 | 10건까지 반환되고 다음 페이지가 있다고 응답한다 |
| 모니터 역할이 검색한다 | 서비스 둘, 모니터 역할 | 전체 조회 | 슈퍼관리자와 같은 응답 |
| 슈퍼관리자가 아닌 사용자가 검색한다 | 전역 역할 없음 | 전체 조회 | 역할 부족으로 거부 |

상태 필터는 `equals`, `in`, `not_equals`, `not_in` 조건을 받는다. "상태 필터로 검색한다"
시나리오는 이 조건들을 모두 확인한다.

요청 타입이 커서를 받지만 이 검색은 크기와 건너뛸 수만 읽는다. 커서를 함께 주면 지금은 조용히
무시된다. 시나리오를 적기 전에 무시할 것인지 사용할 것인지 정한다.

## 아직 적지 않은 것

없다. 어댑터가 제공하는 검색 호출이 위에 있다.

`batch_load_fields`는 모든 어댑터가 물려받는 공용 도우미이지 이 엔티티의 호출이 아니다. 레포트가
함께 세지만 적을 것이 없다.
