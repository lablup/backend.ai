---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-02-08
Created-Version: 26.3.0
Target-Version:
Implemented-Version:
---

# Resource Slot DB Normalization

## Related Issues

- JIRA Epic: [BA-4302](https://lablup.atlassian.net/browse/BA-4302) — Resource Slot DB Normalization
- JIRA Stories:
  - [BA-4303](https://lablup.atlassian.net/browse/BA-4303) — Phase 1: Foundation tables and migration
- Related BEPs:
  - [BEP-1026](BEP-1026-fair-share-scheduler.md) — Fair Share Scheduler (usage bucket / fair share tables)
  - [BEP-1000](BEP-1000-redefining-accelerator-metadata.md) — Redefining Accelerator Metadata (slot metadata)

## Motivation

All resource slot data in Backend.AI is stored as **JSONB columns** via `ResourceSlotColumn`.
This creates three critical problems at scale:

1. **SQL Aggregation Is Impossible** — Every aggregation must load all rows into Python memory and iterate manually (e.g., `_calculate_agent_occupied_slots()`, `_fetch_kernel_occupancy()`)
2. **Atomic Operations Are Impossible** — Updating a single resource requires read-modify-write of the entire JSONB object, creating race conditions under concurrent scheduling
3. **Cross-Entity Queries Are Inefficient** — Questions like "total GPU usage per project" require full Python scans instead of `SELECT SUM(...) GROUP BY`

The Fair Share scheduler (BEP-1026) compounds these problems by applying Python `Decimal` exponent calculations per resource × per entity × per bucket day, which could be a single SQL window function with normalized columns.

## Current Design

> Details: [current-design.md](BEP-1047/current-design.md)

8 tables store resource slots as JSONB (`kernels`, `agents`, `*_usage_buckets`, `*_fair_shares`). Slot type definitions are scattered across etcd, `INTRINSIC_SLOTS`, `KNOWN_SLOT_METADATA`, and the `SlotTypes` enum.

All scheduler aggregation happens via Python loops over full result sets.

## Proposed Design

Normalize JSONB resource slots into relational tables with `(entity_id, slot_name, amount)` rows, enabling SQL-native aggregation while maintaining backward compatibility through phased migration.

### Phase 1: Foundation Tables (Non-Destructive)

> Details: [phase-1-foundation-tables.md](BEP-1047/phase-1-foundation-tables.md)

Add new normalized tables alongside existing JSONB columns. No existing behavior changes.

| Table | Purpose | PK |
|-------|---------|-----|
| `resource_slot_types` | Slot type registry (replaces etcd + hardcoded defs) | `slot_name` |
| `agent_resource_capacity` | Agent resource inventory | `(agent_id, slot_name)` |
| `resource_allocations` | Per-kernel resource allocations | `(kernel_id, slot_name)` |

Key design decisions: composite PKs (no UUID), `NUMERIC(24,6)` for all amounts, `used` nullable (NULL vs 0 semantics), `ON DELETE CASCADE`.

### Phase 2: Scheduler Integration

> Details: [phase-2-scheduler-integration.md](BEP-1047/phase-2-scheduler-integration.md)

Connect the new tables to the kernel lifecycle (create → running → terminate) with dual-write. Replace Python aggregation loops with SQL `GROUP BY` queries. Validate JSONB vs normalized data via background task, then cut over.

### Phase 3: Usage Bucket Optimization

> Details: [phase-3-usage-bucket-optimization.md](BEP-1047/phase-3-usage-bucket-optimization.md)

Two options under consideration:
- **Option A**: JSONB SQL aggregation functions (no schema change, less efficient)
- **Option B**: Normalized tables with amount + duration separation (eliminates overflow risk, consistent with Phase 1/2)

Option B stores amount and duration separately instead of pre-multiplied resource-seconds, keeping all stored values within NUMERIC(24,6) range and deferring multiplication to SQL query time.

## Migration / Compatibility

> Details: [migration-compatibility.md](BEP-1047/migration-compatibility.md)

| Phase | Strategy | Risk |
|-------|----------|------|
| Phase 1 | `CREATE TABLE` only, backfill from JSONB | Zero — non-destructive |
| Phase 2 | Dual-write → validate → cutover | Low — rollback by disabling dual-write |
| Phase 3 | JSONB deprecation → removal | Medium — requires coordinated migration |

etcd slot type definitions migrate incrementally: DB takes precedence (Phase 1) → CLI import (Phase 2) → etcd dependency removed (Phase 3).

## Implementation Plan

### Phase 1: Foundation (Target: BA-4303)

1. Alembic migration: create 3 new tables
2. Seed `resource_slot_types` from `INTRINSIC_SLOTS` + `KNOWN_SLOT_METADATA`
3. Backfill `agent_resource_capacity` and `resource_allocations` from existing JSONB
4. Row models and repository layer
5. Tests: schema validation, backfill correctness, SQL aggregation

### Phase 2: Scheduler Integration

1. Dual-write hooks at lifecycle stages
2. SQL aggregation service (replaces `_fetch_kernel_occupancy()`, `_calculate_agent_occupied_slots()`)
3. Background validation task
4. Cutover to SQL read path
5. Tests: dual-write consistency, SQL vs Python equivalence

### Phase 3: Usage Bucket Optimization

1. Decide approach (Option A vs B)
2. Implement and replace Python decay calculation with SQL
3. Performance benchmarking
4. Tests: decay precision validation

## Open Questions

1. **Phase 3 approach**: JSONB SQL functions (Option A) vs normalized tables with amount/duration separation (Option B)?
2. **Fair Share decay precision**: PostgreSQL `POWER()` uses float64. Is this sufficient vs current Python `Decimal`?
3. **AcceleratorMetadata integration**: Should `resource_slot_types` absorb BEP-1000's full schema, or remain separate with FK?
4. **etcd → DB migration CLI**: One-time CLI command or automatic alembic migration?
5. **Index strategy**: Should we add partial indexes (e.g., `WHERE status IN ('RUNNING', 'TERMINATING')`)?

## References

- [BEP-1026: Fair Share Scheduler](BEP-1026-fair-share-scheduler.md) — usage buckets and fair share tables
- [BEP-1000: Redefining Accelerator Metadata](BEP-1000-redefining-accelerator-metadata.md) — slot metadata design
- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/16/datatype-json.html)
- [PostgreSQL Numeric Types](https://www.postgresql.org/docs/16/datatype-numeric.html)
