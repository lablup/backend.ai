# Phase 1: Foundation Tables

> Detail document for [BEP-1047](../BEP-1047-resource-slot-db-normalization.md)

Add new normalized tables alongside existing JSONB columns. No existing behavior changes.

## 1.1 `resource_slot_types` — Slot Type Registry

Migrate slot type definitions from etcd to a database table:

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

### Design Decisions

- `slot_name` as natural PK (matches existing `SlotName` string keys)
- `rank` for display ordering (replaces `agent_selection_resource_priority` config)
- Absorbs `KNOWN_SLOT_METADATA` and `INTRINSIC_SLOTS` into a single source of truth

### Seed Data

From `INTRINSIC_SLOTS` + `KNOWN_SLOT_METADATA`:

| slot_name | slot_type | display_name | rank |
|-----------|-----------|-------------|------|
| cpu | count | CPU | 40 |
| mem | bytes | Memory | 50 |
| cuda.device | count | GPU (CUDA) | 10 |
| cuda.shares | count | GPU (fGPU) | 20 |
| rocm.device | count | GPU (ROCm) | 30 |
| tpu.device | count | TPU | 35 |

## 1.2 `agent_resources` — Agent Resource Inventory

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

### Design Decisions

- **Composite PK** `(agent_id, slot_name)` — no UUID needed since no FK references this table
- **`NUMERIC(24,6)`** — supports `mem` byte values up to 10^18 (exabyte) with 6 decimal places for fractional CPU/GPU
- **`used` nullable** — `NULL` semantics differ from `0` (uninitialized vs zero usage)
- **`ON DELETE CASCADE`** — agent deletion automatically cleans up capacity rows

## 1.3 `resource_allocations` — Kernel-Level Allocations

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

### Design Decisions

- **`requested` vs `used`** — maps to existing `requested_slots` / `occupied_slots` JSONB split
- **`used` nullable** — `NULL` = pending assignment, non-NULL = scheduler has assigned resources
- **`used_at` timestamp** — enables time-based queries (e.g., allocation latency metrics)

## 1.4 SQL Aggregation Examples

With normalized tables, the scheduler's Python aggregation loops become SQL:

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

## NUMERIC(24,6) Range Verification

| Resource | Max Per-Entity Value | Digits | Verdict |
|----------|---------------------|--------|---------|
| `mem` (bytes) | ~10^13 (12 TiB) | 14 | Safe |
| `cpu` (cores) | ~10,000 | 5 | Safe |
| `cuda.shares` (fractional) | ~8.0 | 1 | Safe |
| `cuda.device` (count) | ~8 | 1 | Safe |
| Agent sum (1,000 agents × 12 TiB) | ~10^16 | 17 | Safe |
| NUMERIC(24,6) max | 10^18 | 18 | - |
