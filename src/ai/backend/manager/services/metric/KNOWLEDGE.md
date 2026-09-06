---
name: manager-services-metric
type: design-rationale
description: 컨테이너 사용량 조회 도메인의 액션 모양 선택, public 게이트 근거, 실시간 통계가 세션에 답하는 이유, 프로세서 필드 이름
scope: src/ai/backend/manager/services/metric
keywords:
  - MetricProcessors
  - PublicSearchContainerMetricsAction
  - PublicSearchContainerMetricMetadataAction
  - BatchGetKernelLiveStatsAction
  - LookupBulkKernelOwnerAction
  - PROMETHEUS_QUERY_PRESET_ENTITY_TYPE
  - PublicActionProcessor
  - Concern.METRIC
sources:
  - src/ai/backend/manager/services/metric
  - src/ai/backend/manager/services/prometheus_query_preset
generated:
  by: claude-code/opus-5
  at: 2026-08-23
status: draft
---

# 컨테이너 사용량 조회 (`services/metric`)

이 도메인은 테이블이 아니라 Prometheus가 답하는 시계열을 읽는다. 저장소 계층은
`repositories/metric` 이고, 그 아래는 DB가 아니라 메트릭 스토어다.

## 모양은 지목하는 대상이 정한다

- 지표 시계열과 이름 목록은 아무 행도 지목하지 않는다. 라벨로 스토어를 좁힐 뿐이므로
  global 모양이다.
- 실시간 통계는 호출부가 커널을 지목해 넘긴다. 커널은 행이지 엔티티가 아니므로 bulk field
  모양이며, 그 커널들을 품은 세션을 먼저 읽어 그 세션들에 대해 검사한다.
- 세 연산 다 `operation_type()` 은 `SEARCH` 다. 라벨을 얼마나 좁히든 필터링된 질의다.

## 앞의 두 연산은 SUPERADMIN이 아니라 public이다

- 사용량 패널은 일반 사용자가 자기 자원을 보는 화면이므로 superadmin 게이트를 두면
  기능이 사라진다.
- 레거시 배선에는 게이트가 아예 없었다. public 으로 옮기면서 인증 확인이 처음 붙는다.
- 어느 사용자·프로젝트의 컨테이너까지 보이는지는 게이트가 아니라 호출부가 채우는
  라벨이 정한다.

## 엔티티는 읽는 대상에 따라 둘로 갈린다

| 연산 | 답하는 엔티티 | 이유 |
|---|---|---|
| 지표 시계열 · 이름 목록 | prometheus query preset | 코드에 박힌 질의다. 저장된 preset 행과 다른 점은 행이 아니라 붙박이라는 것뿐이다 |
| 커널 실시간 통계 | session | 커널은 세션의 행이므로 `LookupBulkKernelOwnerAction` 으로 세션을 읽어 그 세션이 답한다 |

- 앞의 둘은 `Concern.METRIC` 아래 preset 도메인과 같은 그룹을 쓰고 public 게이트다.
- 실시간 통계는 `ProcessorGroup.bulk_field` 로 배선한다. 같은 모양을 쓰는 것이
  `BatchGetKernelResourceAllocationAction` 이다.
- 프로세서 필드는 `public_search`(지표) / `metadata_public_search`(이름 목록) /
  `batch_get_kernel_live_stats`(실시간 통계) 셋이다.

## 서비스는 남는다

- 세 메서드 모두 외부 시스템(Prometheus)을 부르므로 ops 제네릭 서비스로 내려갈 수
  없다. 리포지토리 spec 을 그대로 넘기는 통과 연산이 아니다.
