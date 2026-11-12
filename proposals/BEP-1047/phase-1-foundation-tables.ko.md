# Phase 1: 기반 테이블

> [BEP-1047](../BEP-1047-resource-slot-db-normalization.md) 의 상세 문서

기존 JSONB column 옆에 새 정규화 테이블을 추가한다. 기존 동작은 변경되지 않는다.

## 1.1 `resource_slot_types`: slot 유형 레지스트리

slot 유형 정의를 etcd 에서 데이터베이스 테이블로 이전한다.

```sql
CREATE TABLE resource_slot_types (
    slot_name     VARCHAR(64)  PRIMARY KEY,
    slot_type     VARCHAR(16)  NOT NULL,  -- count, bytes, unique, unified
    display_name  VARCHAR(128),
    rank          INTEGER      NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

### 설계 결정

- `slot_name` 을 자연 PK 로 사용한다(기존 `SlotName` 문자열 key 와 일치)
- `rank` 는 표시 순서용이다(`agent_selection_resource_priority` config 를 대체)
- `KNOWN_SLOT_METADATA` 와 `INTRINSIC_SLOTS` 를 하나의 기준 출처로 흡수한다

### Seed 데이터

`INTRINSIC_SLOTS` + `KNOWN_SLOT_METADATA` 에서 가져온다.

| slot_name | slot_type | display_name | rank |
|-----------|-----------|-------------|------|
| cpu | count | CPU | 40 |
| mem | bytes | Memory | 50 |
| cuda.device | count | GPU (CUDA) | 10 |
| cuda.shares | count | GPU (fGPU) | 20 |
| rocm.device | count | GPU (ROCm) | 30 |
| tpu.device | count | TPU | 35 |

## 1.2 `agent_resources`: Agent 자원 목록

```sql
CREATE TABLE agent_resources (
    agent_id       VARCHAR(64)    NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    slot_name      VARCHAR(64)    NOT NULL REFERENCES resource_slot_types(slot_name),
    capacity       NUMERIC(24,6)  NOT NULL,
    used           NUMERIC(24,6),  -- NULL = not yet assigned, 0 = assigned but idle
    created_at     TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ    NOT NULL DEFAULT now(),
    PRIMARY KEY (agent_id, slot_name)
);

CREATE INDEX ix_agent_resources_slot_name ON agent_resources (slot_name);
CREATE INDEX ix_agent_resources_agent_avail ON agent_resources (agent_id, slot_name, capacity, used);
```

### 설계 결정

- **복합 PK** `(agent_id, slot_name)`: 이 테이블을 참조하는 FK 가 없어 UUID 가 필요 없다
- **`NUMERIC(24,6)`**: `mem` byte 값을 10^18(exabyte)까지 담고, 소수 CPU/GPU 를 위해 소수점 6자리를 둔다
- **`used` nullable**: `NULL` 은 `0` 과 다른 의미다(초기화되지 않음과 사용량 0)
- **`ON DELETE CASCADE`**: Agent 를 삭제하면 용량 row 를 자동으로 정리한다

## 1.3 `resource_allocations`: kernel 단위 할당

```sql
CREATE TABLE resource_allocations (
    kernel_id      UUID           NOT NULL REFERENCES kernels(id) ON DELETE CASCADE,
    slot_name      VARCHAR(64)    NOT NULL REFERENCES resource_slot_types(slot_name),
    requested      NUMERIC(24,6)  NOT NULL,
    used           NUMERIC(24,6),  -- NULL until actually assigned by scheduler
    created_at     TIMESTAMPTZ    NOT NULL DEFAULT now(),
    used_at        TIMESTAMPTZ,    -- set when scheduler assigns resources
    PRIMARY KEY (kernel_id, slot_name)
);

-- Aggregation indexes
CREATE INDEX ix_ra_slot_name ON resource_allocations (slot_name);
CREATE INDEX ix_ra_kernel_slot ON resource_allocations (kernel_id, slot_name);
```

### 설계 결정

- **`requested` 와 `used`**: 기존 `requested_slots` / `occupied_slots` JSONB 분리와 대응한다
- **`used` nullable**: `NULL` 은 할당 대기, NULL 이 아니면 스케줄러가 자원을 할당한 상태다
- **`used_at` 시각**: 시각 기반 조회(예: 할당 지연 지표)를 가능하게 한다

## 1.4 SQL 집계 예시

정규화 테이블이 있으면 스케줄러의 Python 집계 반복문을 SQL 로 처리한다.

```sql
-- Total occupied slots per agent (replaces _calculate_agent_occupied_slots)
SELECT
    k.agent,
    ra.slot_name,
    SUM(CASE
        WHEN k.status IN ('RUNNING', 'TERMINATING') THEN ra.used
        ELSE ra.requested
    END) AS total_amount
FROM resource_allocations ra
JOIN kernels k ON k.id = ra.kernel_id
WHERE k.agent = ANY(:agent_ids)
  AND k.status = ANY(:resource_statuses)
GROUP BY k.agent, ra.slot_name;

-- Total GPU usage per project (currently requires full Python scan)
SELECT ra.slot_name, SUM(ra.used) AS total
FROM resource_allocations ra
JOIN kernels k ON k.id = ra.kernel_id
WHERE k.group_id = :project_id
  AND k.status IN ('RUNNING', 'TERMINATING')
  AND ra.slot_name = 'cuda.device'
GROUP BY ra.slot_name;
```

## NUMERIC(24,6) 범위 검증

| 자원 | 엔티티별 최댓값 | 자릿수 | 판정 |
|----------|---------------------|--------|---------|
| `mem` (bytes) | ~10^13 (12 TiB) | 14 | 안전 |
| `cpu` (cores) | ~10,000 | 5 | 안전 |
| `cuda.shares` (fractional) | ~8.0 | 1 | 안전 |
| `cuda.device` (count) | ~8 | 1 | 안전 |
| Agent 합계 (1,000 agents × 12 TiB) | ~10^16 | 17 | 안전 |
| NUMERIC(24,6) 최대 | 10^18 | 18 | - |
