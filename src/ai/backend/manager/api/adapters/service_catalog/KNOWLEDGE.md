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

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 것과 실행 결과가 어긋나면 문장을 먼저
의심한다.

이 어댑터는 읽기 하나뿐이다. 카탈로그의 행은 서비스가 자기를 등록하고 심장 박동을 보낼 때
이벤트 처리기가 직접 쓰고, 관리자가 손으로 만들거나 고치는 자리는 없다. 그 하나의 훑기는
전역 역할이 지키고, 읽기이므로 모니터 역할도 지난다.

행을 만드는 write spec이 없다. 상황을 세우려면 등록 이벤트 처리기가 쓰는 길을 그대로 써야
한다.

## 훑기

| 시나리오 | 상황 | 요청 | 결과 |
|---|---|---|---|
| 슈퍼관리자가 훑는다 | 서비스 둘, 그중 하나는 엔드포인트 하나를 가짐, 전역 역할 있음 | 전체 조회 | 둘을 모두 세고, 엔드포인트가 함께 실린다 |
| 서비스 그룹으로 걸러 훑는다 | 그룹이 다른 서비스 둘, 전역 역할 있음 | 그룹 필터 조회 | 그 그룹의 것만 남는다 |
| 상태로 걸러 훑는다 | 건강한 것과 등록 해제된 것이 섞여 있음, 전역 역할 있음 | 상태 필터 조회 | 고른 상태의 것만 남는다 |
| 페이지 크기를 생략한다 | 서비스 열하나, 전역 역할 있음 | 크기 없이 조회 | 열 건까지 오고 다음 쪽이 있다고 답한다 |
| 모니터 역할이 훑는다 | 서비스 둘, 모니터 역할 | 전체 조회 | 슈퍼관리자와 같은 답 |
| 슈퍼관리자가 아닌 사용자가 훑는다 | 전역 역할 없음 | 전체 조회 | 역할로 거부 |

상태 필터는 같음·목록 안·다름·목록 밖 네 갈래를 받는다. 셋째 줄은 네 갈래를 함께 본다.

요청 타입이 커서를 받지만 이 훑기는 크기와 건너뛸 수만 읽는다. 커서를 함께 주면 지금은 조용히
버려진다. 줄을 적기 전에 버릴 것인지 쓸 것인지 정한다.

## 아직 적지 않은 것

없다. 어댑터가 내놓는 호출 하나가 위에 있다.

`batch_load_fields`는 모든 어댑터가 물려받는 공용 도우미이지 이 엔티티의 호출이 아니다. 레포트가
함께 세지만 적을 것이 없다.
