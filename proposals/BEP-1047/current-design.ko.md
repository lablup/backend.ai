# 현재 설계

> [BEP-1047](../BEP-1047-resource-slot-db-normalization.md) 의 상세 문서

## resource slot 저장

모든 resource slot 은 `ResourceSlotColumn` 을 통해 JSONB 로 저장한다.

```python
# models/base.py
class ResourceSlotColumn(TypeDecorator[ResourceSlot]):
    impl = JSONB
    cache_ok = True
```

`ResourceSlot` 타입은 `dict[SlotName, Decimal]` 이고, key 는 동적 slot 이름이다(예: `cpu`, `mem`, `cuda.device`).

## 영향받는 테이블

| 테이블 | JSONB column | 목적 |
|-------|--------------|---------|
| `kernels` | `occupied_slots`, `requested_slots` | kernel 별 자원 할당 |
| `agents` | `available_slots`, `occupied_slots` | Agent 용량과 현재 사용량 |
| `domain_usage_buckets` | `resource_usage`, `capacity_snapshot` | domain 별 과거 사용량 |
| `project_usage_buckets` | `resource_usage`, `capacity_snapshot` | project 별 과거 사용량 |
| `user_usage_buckets` | `resource_usage`, `capacity_snapshot` | user 별 과거 사용량 |
| `domain_fair_shares` | `total_decayed_usage`, `resource_weights` | fair share 우선순위 데이터 |
| `project_fair_shares` | `total_decayed_usage`, `resource_weights` | fair share 우선순위 데이터 |
| `user_fair_shares` | `total_decayed_usage`, `resource_weights` | fair share 우선순위 데이터 |

## slot 유형 registry (etcd)

slot 유형은 현재 다음을 조합해 정의한다.

- **etcd** (`config/resource_slots/{name}`): runtime slot 유형 registry
- **`INTRINSIC_SLOTS`** (manager/defs.py): hardcoded `cpu` → COUNT, `mem` → BYTES
- **`KNOWN_SLOT_METADATA`** (api/etcd.py): 알려진 slot 의 표시 메타데이터
- **`SlotTypes` enum** (common/types.py): `COUNT`, `BYTES`, `UNIQUE`, `UNIFIED`

```python
# manager/defs.py
INTRINSIC_SLOTS: Final = {
    SlotName("cpu"): SlotTypes("count"),
    SlotName("mem"): SlotTypes("bytes"),
}
```

## 집계 흐름 (스케줄러)

```
┌─────────────┐    SELECT *     ┌──────────────┐   Python loop   ┌────────────────┐
│  kernels    │ ──────────────→ │  App Server  │ ──────────────→ │ ResourceSlot   │
│ (JSONB)     │  full row scan  │  (memory)    │  deserialize    │ aggregation    │
└─────────────┘                 └──────────────┘  + accumulate   └────────────────┘
```

### 주요 집계 지점

**`_calculate_agent_occupied_slots()`** 는 모든 kernel 을 Python 으로 반복한다.

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

**`_fetch_kernel_occupancy()`** (db_source.py:417)는 전체 결과 집합을 반복하며 keypair, user, group, domain, agent 별 점유량을 Python 으로 누적해 `ResourceOccupancySnapshot` 을 생성한다.

**Validator** (`domain_resource_limit.py`, `group_resource_limit.py`, `keypair_resource_limit.py`, `user_resource_limit.py`)는 메모리에 누적한 `ResourceSlot` 객체를 정책 한도와 비교한다.

### Fair share decay 계산

decay 계산은 자원 × 엔티티 × bucket 일마다 `Decimal("2") ** exponent` 를 적용한다.

```python
# calculator.py:340-355
exponent = Decimal(str(-days_ago)) / Decimal(str(half_life_days))
decay_factor = Decimal("2") ** exponent
return ResourceSlot({key: value * decay_factor for key, value in usage.items()})
```
