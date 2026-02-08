# Phase 3: Usage Bucket Aggregation Optimization

> Detail document for [BEP-1047](../BEP-1047-resource-slot-db-normalization.md)

Optimize Fair Share usage bucket aggregation. Two approaches are considered (see Open Questions).

## Option A: JSONB SQL Aggregation Functions

Keep existing `ResourceSlotColumn` JSONB but add PostgreSQL functions for aggregation:

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

Pros: No schema migration needed. Cons: Less efficient than native numeric, harder to maintain.

## Option B: Normalized Usage Tables (Amount + Duration Separation)

The current usage buckets store pre-multiplied resource-seconds (e.g., byte-seconds) in `resource_usage`.
For large clusters, `mem_bytes × seconds` can exceed 10^18 and overflow NUMERIC(24,6).

**Key insight**: Do not store the product. Store **amount and duration separately**.
The multiplication is performed at SQL query time, where PostgreSQL automatically extends
NUMERIC precision for intermediate arithmetic results — no overflow risk.

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

### Value Range Safety

Individual column values stay well within NUMERIC(24,6):

| Column | Max Value | Digits | Verdict |
|--------|----------|--------|---------|
| `amount` (mem bytes) | ~10^13 (12 TiB) | 14 | Safe |
| `duration_seconds` (1 day) | 86,400 | 5 | Safe |
| `capacity` (agent sum) | ~10^16 | 17 | Safe |

The multiplication `amount × duration_seconds` only exists as a SQL intermediate value
(never stored), and PostgreSQL auto-extends precision.

### Decayed Usage Query

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

### Comparison

| Aspect | Option A (JSONB Functions) | Option B (Normalized + Separation) |
|--------|---------------------------|-------------------------------------|
| Schema migration | None | New table + data migration |
| Overflow risk | Same as current (resource-seconds) | Eliminated (amount/duration split) |
| Query performance | JSONB parsing overhead | Native NUMERIC aggregation |
| Consistency | Different from Phase 1/2 | Same pattern as Phase 1/2 |
| Maintainability | Custom PL/pgSQL functions | Standard SQL |

Pros: Eliminates overflow risk, enables SQL aggregation, consistent with Phase 1/2 pattern.
Cons: Requires decomposition of existing resource-seconds data during migration.
