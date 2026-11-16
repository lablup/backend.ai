# Phase 3: usage bucket 집계 최적화

> [BEP-1047](../BEP-1047-resource-slot-db-normalization.md) 의 상세 문서

Fair Share usage bucket 집계를 최적화한다. 두 가지 접근 방식을 검토한다(열린 질문 참고).

## Option A: JSONB SQL 집계 함수

기존 `ResourceSlotColumn` JSONB 를 유지하고 집계용 PostgreSQL 함수를 추가한다.

```sql
-- Custom aggregate function for ResourceSlot JSONB
CREATE FUNCTION jsonb_resource_slot_sum(state JSONB, val JSONB)
RETURNS JSONB AS $$
    SELECT jsonb_object_agg(
        key,
        (COALESCE((state->>key)::numeric, 0) + (val->>key)::numeric)::text
    )
    FROM jsonb_each_text(val)
$$ LANGUAGE SQL IMMUTABLE;

CREATE AGGREGATE resource_slot_sum(JSONB) (
    SFUNC = jsonb_resource_slot_sum,
    STYPE = JSONB,
    INITCOND = '{}'
);
```

장점: schema migration 이 필요 없다. 단점: native numeric 보다 효율이 낮고 유지보수가 어렵다.

## Option B: 정규화 usage 테이블 (amount 와 duration 분리)

현재 usage bucket 은 미리 곱한 resource-seconds(예: byte-seconds)를 `resource_usage` 에 저장한다.
큰 cluster 에서는 `mem_bytes × seconds` 가 10^18 을 넘어 NUMERIC(24,6) 범위를 넘어 오버플로가 발생할 수 있다.

**핵심**: 곱한 값을 저장하지 않는다. **amount 와 duration 을 따로** 저장한다.
곱셈은 SQL 질의 시점에 수행하고, PostgreSQL 이 중간 산술 결과의 NUMERIC 정밀도를 자동으로 늘리므로 overflow 위험이 없다.

```sql
CREATE TABLE usage_bucket_entries (
    bucket_id        UUID           NOT NULL,  -- FK to *_usage_buckets.id
    bucket_type      VARCHAR(16)    NOT NULL,  -- 'domain', 'project', 'user'
    slot_name        VARCHAR(64)    NOT NULL REFERENCES resource_slot_types(slot_name),
    amount           NUMERIC(24,6)  NOT NULL,  -- resource amount (bytes, cores, etc.)
    duration_seconds INTEGER        NOT NULL,  -- actual usage duration within bucket period
    capacity         NUMERIC(24,6)  NOT NULL,  -- scaling group capacity for this slot
    PRIMARY KEY (bucket_id, slot_name)
);
```

### 값 범위 안전성

개별 column 값은 NUMERIC(24,6) 범위 안에 충분히 들어온다.

| column | 최대값 | 자릿수 | 판정 |
|--------|----------|--------|---------|
| `amount` (mem bytes) | ~10^13 (12 TiB) | 14 | 안전 |
| `duration_seconds` (1 day) | 86,400 | 5 | 안전 |
| `capacity` (agent sum) | ~10^16 | 17 | 안전 |

`amount × duration_seconds` 곱은 SQL 중간 값으로만 존재하고 저장하지 않으며, PostgreSQL 이 정밀도를 자동으로 늘린다.

### Decay 가 적용된 사용량 질의

```sql
-- Decayed usage sum (replaces Python calculator.py loop)
-- amount × duration_seconds is computed at query time, never stored
SELECT
    ube.slot_name,
    SUM(
        ube.amount * ube.duration_seconds
        * POWER(2, -EXTRACT(DAY FROM now() - b.period_start) / :half_life_days)
    ) AS decayed_usage
FROM usage_bucket_entries ube
JOIN user_usage_buckets b ON b.id = ube.bucket_id
WHERE b.user_uuid = :user_uuid
  AND b.period_start >= :lookback_start
GROUP BY ube.slot_name;
```

### 비교

| 항목 | Option A (JSONB 함수) | Option B (정규화 + 분리) |
|--------|---------------------------|-------------------------------------|
| schema migration | 없음 | 새 테이블 + 데이터 migration |
| overflow 위험 | 현재와 같음(resource-seconds) | 제거됨(amount/duration 분리) |
| 질의 성능 | JSONB 파싱 부담 | native NUMERIC 집계 |
| 일관성 | Phase 1/2 와 다름 | Phase 1/2 와 같은 패턴 |
| 유지보수성 | 사용자 정의 PL/pgSQL 함수 | 표준 SQL |

장점: overflow 위험을 없애고 SQL 집계를 가능하게 하며 Phase 1/2 패턴과 일관된다.
단점: migration 때 기존 resource-seconds 데이터를 분해해야 한다.
