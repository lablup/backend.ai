# 스코프 연동 지표 카탈로그와 대시보드

## 관련 이슈

- Epic **BA-6683**, 이 BEP **BA-6685**
- 관련: BA-6449 (legacy resource-usage/stats REST 제거), BA-6114 (resource_usage 를 Valkey 에서 이전),
  BA-126 (resource-usage API 리팩터링), BA-6446 (새 통합 자원 조회 API), BA-4051 (ValkeyStatClient 제거)
- 기반 BEP (참조만 하고 확장하지 않음): **[BEP-1045](BEP-1045-prometheus-client-extraction-and-querier-interface-abstraction.md)** (Prometheus client 추출),
  **[BEP-1050](BEP-1050-prometheus-query-preset-system.md)** (query preset 시스템),
  **[BEP-1026](BEP-1026-fair-share-scheduler.md)** (resource_usage_history bucket),
  virtual_scope RBAC (권한 모델)

## 1. 목표

`(scope_type, scope_id)` 를 받아 그 스코프의 **instant/range 지표**와 **전용 대시보드**를 반환하는
**스코프 지표 카탈로그** 계층을 정의한다.

핵심 원칙: 스코프와 지표의 연결을 **저장된 일반화 카탈로그**로 유지한다.

- **전용 테이블이** 스코프가 어떤 지표(질의 정의)를 가지는지 **저장**하며, 클라이언트는 **일반화된 디스크립터와 값**을 받는다. `live_stat` 이나 월별 사용량 같은 특정 질의를 **코드에 고정하지 않는다**.
- 실제 값은 여전히 Prometheus 질의(BEP-1050 preset)에서 가져오지만, **스코프와 질의의 연결이 데이터 기반**이므로 Prometheus label schema 를 확장할 필요가 없다.
- 읽기 권한은 **스코프 연산**으로 다룬다(virtual_scope RBAC).

지표 데이터 상당수는 이미 Prometheus 로 흐르지만(`backendai_container_utilization`, model-service `vllm:*`), **스코프별로 질의하고 시각화하는 진입점이 없다**. 이 BEP 가 그 진입점(저장 카탈로그, 스코프 REST, 대시보드)을 정의한다.

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다.

### 2.1 지표 원천 (Prometheus series)

| | 항목 |
|---|---|
| ✅ | `backendai_container_utilization{agent_id, kernel_id, session_id, user_id, project_id, container_metric_name, value_type}`, `backendai_device_utilization` (agent), `backendai_process_utilization` 세 지표는 `agent/metrics/metric.py` 에 있다 |
| ✅ | model-service scrape: 각 route 가 `ModelServiceMetadata{runtime_variant, endpoint_id, deployment_id, project}` 를 등록 → `/metrics/service_discovery` → Prometheus `http-sd` 가 `vllm:*` 를 수집한다 |
| ➕ | 스코프와 지표의 연결은 **저장 카탈로그**가 `scope_type` 별로 관리한다. **Prometheus label 추가와 전략은 이 BEP 범위 밖**이다(전용 테이블로 해결) |

### 2.2 카탈로그 저장 (스코프와 지표의 연결)

| | 항목 |
|---|---|
| ✅ | `prometheus_query_presets` 테이블과 CRUD/실행 REST, `MetricPreset({labels}/{window}/{group_by})`, `ContainerMetricQuerier`, `PrometheusClient.execute_preset` (BEP-1050) |
| ➕ | **스코프 타입별 지표 연결을 저장하는 카탈로그 테이블이 없다**. 호출부가 매번 label 과 질의를 알아야 한다. 이 BEP 가 저장 카탈로그를 도입한다 |

### 2.3 API

| | 항목 |
|---|---|
| ✅ | superadmin preset 실행 REST (`resource/prometheus-query-definitions`) |
| ➕ | `(scope_type, scope_id)` 의 instant/range 지표와 대시보드를 반환하는 **스코프 수준 REST v2 엔드포인트가 없다** |

### 2.4 대시보드

| | 항목 |
|---|---|
| ✅ | Web UI `StatisticsPage`/`DeploymentDetailPage` 묶음이 있다 |
| ➕ | **대시보드, panel(1:N), 스코프와 대시보드의 연결**을 저장하는 구조가 없다. 지표 카탈로그와 **분리**해 관리한다 |

## 3. 구현 설계

**핵심 흐름(지표):** `(scope_type, scope_id)` → 저장 카탈로그에서 `scope_type` 의 지표 연결을 조회 → 질의 시점에 받은 `scope_id` 를 `id` 로 preset 에 전달해 실행(instant/range). 권한은 스코프 연산으로 검사한다.

**대시보드는 별도 하위 시스템**이다(dashboard 1:N panel + scope link). 지표 카탈로그와 독립적으로 관리한다((c) 참조).

### (a) 스코프 정의와 저장 연결 (핵심)

`ScopeType = {session, kernel, agent, deployment, resource_group, domain, project, user}` (확장 가능).

스코프와 지표의 연결을 **저장 카탈로그**로 유지한다. 연결 하나의 계약(개념):

| 필드 | 의미 |
|-------|-----|
| `scope_type` | 이 연결이 적용되는 스코프 종류 |
| `preset_ref` | 실행할 PromQL preset 참조 (BEP-1050) |
| `mode` | instant \| range |
| `viz`, `unit` | panel 렌더 힌트(stat/timeseries/gauge/table, unit) |

- **일반화**: 클라이언트는 특정 질의가 아니라 **연결 디스크립터와 실행 값**을 받는다. 새 지표나 스코프를 추가하는 일은 코드 변경이 아니라 **카탈로그 데이터 추가**다.
- **연결은 `scope_type` 단위**: 카탈로그는 지표를 `scope_type` 에만 연결한다. **`scope_id` 는 저장하지 않는다**. 질의 시점에 `id` 로 받아 preset 실행에 전달한다. 저장 schema(연결 테이블 하나 대 스코프별 테이블)는 구현 선택이다.
- **관리**: 카탈로그는 **고정 seed 기본값**으로 채우고 **admin CRUD** 로 편집한다.

### (b) 스코프별 MetricSet

스코프의 MetricSet 은 **그 `scope_type` 에 저장된 연결의 집합**이다. 유일한 선택 축은 **스코프**다.

> 지표 집합은 runtime variant(vLLM/custom 등)로 나뉘지 않는다. deployment 는 자기 스코프에 저장된 MetricSet 을 그대로 받는다. runtime 별로 다른 지표가 필요하면 그것은 **데이터 문제(카탈로그에 연결을 더 추가)** 이지 설계 축이 아니다.

### (c) 대시보드: 별도 하위 시스템 (dashboard 1:N panel + scope link)

대시보드는 (a)의 지표 카탈로그와 **분리된 저장 구조**로 관리한다. 세 부분이다.

| 부분 | 의미 |
|------|-----|
| `dashboard` | 대시보드 하나(제목과 그 밖의 메타데이터) |
| `panel` | 대시보드에 속한 panel `{title, preset_ref, mode, viz, unit, order}`. **dashboard 1 : N panel** |
| 스코프와 대시보드의 연결 | entity(스코프)와 대시보드를 잇는 매핑. 스코프별 대시보드 연결을 제공한다 |

조회 시 **스코프에 연결된 대시보드와 그 panel** 을 반환하고, 각 panel 의 preset 은 `scope_id` 를 `id` 로 받아 실행한다. **이 API 를 사용하는 쪽은 Web UI** 이고 panel 을 자체 렌더링한다(Grafana provisioning/deeplink 는 범위 밖). dashboard/panel/link 는 고정 seed 와 admin CRUD 로 관리한다.

### (d) API 구성

```
GET /resource/scopes/{scope_type}/{scope_id}/metrics?range=<window>&step=<step>
    → { "<preset>": {"instant": <scalar>, "series": [[ts,val],...]}, ... }   # instant only when range omitted
GET /resource/scopes/{scope_type}/{scope_id}/dashboard
    → linked dashboard + panels (each panel preset executes with scope_id)   # rendered natively by Web UI
```

REST v2 트리이다. 지표 카탈로그와 dashboard/panel/link 는 각각 admin CRUD API 를 가진다.

### (e) 권한: 스코프 연산

읽기 권한은 **virtual_scope RBAC 아래의 스코프 연산으로 다룬다**. `(scope_type, scope_id)` 자체가 권한 스코프이므로 지표 질의는 그 스코프의 읽기 권한 검사로 줄어든다(session/deployment = owner/project, resource_group/domain = admin 등은 RBAC 정책이 정한다). 지표를 위한 별도 권한 축은 두지 않는다.

### (f) 적용 (최소한)

일반 메커니즘의 최소한의 적용만 다룬다. 별도 query builder 나 단일 기준값 설계는 두지 않는다.

- **세션 instant 집합 ≈ 기존 `live_stat`**: 세션 스코프의 instant MetricSet 으로 제공한다. 하드코딩된 `live_stat` 질의를 카탈로그 연결로 교체한다(BA-6114 와 연결, `ValkeyStatClient` 제거).
- **월별 사용량**: live/range 는 이 API 로 제공하고, 과금 수준의 월별 집계는 계속 `resource_usage_history` bucket 을 기준으로 노출한다. **코드에 고정하는 질의는 없다**. legacy 엔드포인트 네 개의 제거는 BA-6449 가 맡는다.

## 결정 요약

| 결정 | 내용 |
|----------|---------|
| 카탈로그 | 스코프와 지표의 연결을 **저장 테이블(일반화)** 에 둔다. 지표나 스코프 추가는 데이터 추가다. 하드코딩 질의는 없다 |
| Label | scope→series 는 질의 시점에 `scope_id` 를 `id` 로 전달해 해석한다. **Prometheus label 확장은 없다** |
| 선택 축 | **스코프 하나**다. runtime variant 축은 제외한다 |
| 권한 | **스코프 연산**(virtual_scope RBAC)이다. 별도 권한 축은 없다 |
| SLA | scope_type 에 매핑된 **저장 지표 항목**일 뿐이다(설계 문제가 아니다) |
| 적용 (live_stat/월별) | 일반 메커니즘의 최소한의 적용이다. 별도 query builder 나 단일 기준값 논의는 없다 |
| 대시보드 | 지표 카탈로그와 **분리된 구조**다: `dashboard` 1:N `panel` + 스코프와 대시보드의 연결. Web UI 가 자체 렌더링한다(Grafana provisioning 은 범위 밖) |
| 관리 | 지표 카탈로그와 대시보드 모두 **고정 seed + admin CRUD** 를 사용한다 |

## 범위 밖

- 장기 보존 TSDB(Thanos/Mimir)와 그 밖의 인프라 계층.
- Prometheus label 전략과 cardinality 조정(저장 카탈로그가 대체한다).

## 참고

- [BEP-1045](BEP-1045-prometheus-client-extraction-and-querier-interface-abstraction.md), [BEP-1050](BEP-1050-prometheus-query-preset-system.md), [BEP-1026](BEP-1026-fair-share-scheduler.md), [BEP-1025](BEP-1025-server-side-csv-export.md)
- 코드: `agent/metrics/metric.py`, `manager/clients/prometheus/*`, `sokovan/deployment/route/executor.py`, `repositories/resource_usage_history/`, `example-prometheus-query-presets.json`
