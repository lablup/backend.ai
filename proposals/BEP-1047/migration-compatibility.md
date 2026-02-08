# Migration / Compatibility

> Detail document for [BEP-1047](../BEP-1047-resource-slot-db-normalization.md)

## Phase 1: Non-Destructive Addition

- **Schema**: `CREATE TABLE` only — no existing tables are modified
- **Data**: Seed `resource_slot_types` from `INTRINSIC_SLOTS` + `KNOWN_SLOT_METADATA`
- **Backfill**: Populate `agent_resources` from `agents.available_slots` / `agents.occupied_slots`
- **Backfill**: Populate `resource_allocations` from `kernels.requested_slots` / `kernels.occupied_slots`
- **Risk**: Zero — existing code paths are unaffected

## Phase 2: Dual-Write with Validation

- **Write path**: Write to both JSONB columns and normalized tables
- **Read path**: Continue reading from JSONB (primary), validate against normalized tables
- **Validation**: Background task compares JSONB vs normalized data, logs discrepancies
- **Cutover**: Once validation passes consistently, switch read path to normalized tables
- **Rollback**: Remove dual-write, normalized tables become stale but can be re-backfilled

## Phase 3: JSONB Column Deprecation (Future)

- **After Phase 2 stabilizes**: Stop writing to JSONB columns
- **Migration**: Mark JSONB columns as deprecated
- **Removal**: Drop JSONB columns in a subsequent major version (with alembic migration)

## Breaking Changes

- **Phase 1**: None
- **Phase 2**: Internal API changes in scheduler data source (no external API impact)
- **Phase 3**: JSONB columns removed — any direct JSONB queries must migrate

## etcd Migration

Resource slot type definitions currently in etcd (`config/resource_slots/{name}`) will need a migration path:

1. **Phase 1**: Read from both etcd and `resource_slot_types` table, DB takes precedence
2. **Phase 2**: CLI command to import etcd slot definitions into DB
3. **Phase 3**: Remove etcd dependency for slot type registry
