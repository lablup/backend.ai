# Phase 2: Scheduler Integration

> Detail document for [BEP-1047](../BEP-1047-resource-slot-db-normalization.md)

Connect the new tables to the scheduler lifecycle, enabling SQL-native occupancy calculations.

## 2.1 Kernel Lifecycle Integration

Update resource writes at each lifecycle stage:

| Stage | Current Code | Change |
|-------|-------------|--------|
| Session creation | `_allocate_single_session()` writes `requested_slots` JSONB | Additionally INSERT into `resource_allocations` |
| Running transition | `_update_occupied_slots()` writes `occupied_slots` JSONB | Additionally UPDATE `resource_allocations.used` |
| Termination | Status transition clears slots | DELETE from `resource_allocations` |

During Phase 2, **dual-write** to both JSONB and normalized tables to enable validation.

## 2.2 Occupancy Calculation (SQL)

Replace `_fetch_kernel_occupancy()` Python aggregation with SQL:

```sql
-- Build ResourceOccupancySnapshot via SQL
SELECT
    k.access_key,
    k.user_uuid,
    k.group_id,
    k.domain_name,
    k.agent,
    ra.slot_name,
    SUM(CASE
        WHEN k.status IN ('RUNNING', 'TERMINATING') THEN ra.used
        ELSE ra.requested
    END) AS amount
FROM resource_allocations ra
JOIN kernels k ON k.id = ra.kernel_id
WHERE k.scaling_group = :scaling_group
  AND k.status = ANY(:resource_statuses)
GROUP BY k.access_key, k.user_uuid, k.group_id, k.domain_name, k.agent, ra.slot_name;
```

This eliminates the per-row Python deserialization and accumulation loop.

## 2.3 Validator Optimization

Resource limit validators currently compare in-memory `ResourceSlot` objects.
With normalized tables, validators can push limit checks into SQL:

```sql
-- Check if adding a workload exceeds domain limit
SELECT ra.slot_name,
       SUM(ra.used) AS current_usage
FROM resource_allocations ra
JOIN kernels k ON k.id = ra.kernel_id
WHERE k.domain_name = :domain_name
  AND k.status = ANY(:resource_statuses)
GROUP BY ra.slot_name;
```

The comparison against policy limits remains in Python, but the aggregation moves to SQL.

## 2.4 Affected Code Paths

| Code Path | File | Current Behavior | After Phase 2 |
|-----------|------|-----------------|---------------|
| `_allocate_single_session()` | db_source.py | INSERT `requested_slots` JSONB | + INSERT `resource_allocations` rows |
| `_update_occupied_slots()` | hooks/status.py | UPDATE `occupied_slots` JSONB | + UPDATE `resource_allocations.used` |
| `_fetch_kernel_occupancy()` | db_source.py | Python loop aggregation | SQL GROUP BY query |
| `_calculate_agent_occupied_slots()` | db_source.py | Python loop aggregation | SQL GROUP BY query |
| Domain/Group/Keypair/User validators | provisioner/validators/ | In-memory ResourceSlot compare | SQL aggregation + Python compare |
