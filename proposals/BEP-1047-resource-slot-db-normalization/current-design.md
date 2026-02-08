# Current Design

> Detail document for [BEP-1047](../BEP-1047-resource-slot-db-normalization.md)

## Resource Slot Storage

All resource slots are stored as JSONB via `ResourceSlotColumn`:

```python
# models/base.py
class ResourceSlotColumn(TypeDecorator[ResourceSlot]):
    impl = JSONB
    cache_ok = True
```

The `ResourceSlot` type is a `dict[SlotName, Decimal]` where keys are dynamic slot names (e.g., `cpu`, `mem`, `cuda.device`).

## Affected Tables

| Table | JSONB Columns | Purpose |
|-------|--------------|---------|
| `kernels` | `occupied_slots`, `requested_slots` | Per-kernel resource allocation |
| `agents` | `available_slots`, `occupied_slots` | Agent capacity and current usage |
| `domain_usage_buckets` | `resource_usage`, `capacity_snapshot` | Historical usage per domain |
| `project_usage_buckets` | `resource_usage`, `capacity_snapshot` | Historical usage per project |
| `user_usage_buckets` | `resource_usage`, `capacity_snapshot` | Historical usage per user |
| `domain_fair_shares` | `total_decayed_usage`, `resource_weights` | Fair share priority data |
| `project_fair_shares` | `total_decayed_usage`, `resource_weights` | Fair share priority data |
| `user_fair_shares` | `total_decayed_usage`, `resource_weights` | Fair share priority data |

## Slot Type Registry (etcd)

Slot types are currently defined via a combination of:

- **etcd** (`config/resource_slots/{name}`): Runtime slot type registry
- **`INTRINSIC_SLOTS`** (manager/defs.py): Hardcoded `cpu` → COUNT, `mem` → BYTES
- **`KNOWN_SLOT_METADATA`** (api/etcd.py): Display metadata for known slots
- **`SlotTypes` enum** (common/types.py): `COUNT`, `BYTES`, `UNIQUE`, `UNIFIED`

```python
# manager/defs.py
INTRINSIC_SLOTS: Final = {
    SlotName("cpu"): SlotTypes("count"),
    SlotName("mem"): SlotTypes("bytes"),
}
```

## Aggregation Flow (Scheduler)

```
┌─────────────┐    SELECT *     ┌──────────────┐   Python loop   ┌────────────────┐
│  kernels    │ ──────────────→ │  App Server  │ ──────────────→ │ ResourceSlot   │
│ (JSONB)     │  full row scan  │  (memory)    │  deserialize    │ aggregation    │
└─────────────┘                 └──────────────┘  + accumulate   └────────────────┘
```

### Key Aggregation Sites

**`_calculate_agent_occupied_slots()`** — Python loop over all kernels:

```python
# db_source.py — _calculate_agent_occupied_slots()
# "Aggregates occupied_slots in Python since it's a custom ResourceSlot type."
for row in result:
    if row.agent:
        if kernel_status in KernelStatus.resource_occupied_statuses():
            slots_to_use = row.occupied_slots
        else:
            slots_to_use = row.requested_slots
        if slots_to_use:
            agent_slots[row.agent] += slots_to_use
```

**`_fetch_kernel_occupancy()`** (db_source.py:417) — builds `ResourceOccupancySnapshot` by iterating the full result set and accumulating occupancy per keypair, user, group, domain, and agent in Python.

**Validators** (`domain_resource_limit.py`, `group_resource_limit.py`, `keypair_resource_limit.py`, `user_resource_limit.py`) — compare accumulated in-memory `ResourceSlot` objects against policy limits.

### Fair Share Decay Calculation

The decay calculation applies `Decimal("2") ** exponent` per resource × per entity × per bucket day:

```python
# calculator.py:340-355
exponent = Decimal(str(-days_ago)) / Decimal(str(half_life_days))
decay_factor = Decimal("2") ** exponent
return ResourceSlot({key: value * decay_factor for key, value in usage.items()})
```
