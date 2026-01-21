# KernelV2 GQL - Types to Skip

These types are **not to be implemented** in the new PR. They have been decided to be replaced by other designs.

Since we're creating a fresh PR, these types simply won't be included rather than being removed.

---

## Summary

| Type | Location | Reason |
|------|----------|--------|
| `SchedulerPredicateGQL` | `common/types.py` | Replaced by new scheduler design |
| `SchedulerInfoGQL` | `common/types.py` | Replaced by new scheduler design |
| `KernelStatusHistoryEntryGQL` | `kernel/types.py` | Replaced by new status tracking design |
| `KernelStatusHistoryGQL` | `kernel/types.py` | Replaced by new status tracking design |

---

## Scheduler Types (Do Not Implement)

### SchedulerPredicateGQL

**Original Definition** (from PR #8079):

```python
@strawberry.type(
    name="SchedulerPredicate",
    description=(
        "Added in 26.1.0. A scheduler predicate result from scheduling attempts. "
        "Predicates are conditions checked during session scheduling."
    ),
)
class SchedulerPredicateGQL:
    name: str = strawberry.field(
        description="Name of the predicate (e.g., 'concurrency', 'reserved_time')."
    )
    msg: str | None = strawberry.field(
        description="Message explaining why the predicate failed. Null for passed predicates."
    )
```

**Action**: Do not implement. Will be replaced by new scheduler design.

### SchedulerInfoGQL

**Original Definition** (from PR #8079):

```python
@strawberry.type(
    name="SchedulerInfo",
    description=(
        "Added in 26.1.0. Scheduler information including retry attempts and predicate results. "
        "Contains details about scheduling attempts when a session is pending."
    ),
)
class SchedulerInfoGQL:
    retries: int | None = strawberry.field(
        description="Number of scheduling attempts made for this session."
    )
    last_try: str | None = strawberry.field(
        description="ISO 8601 timestamp of the last scheduling attempt."
    )
    msg: str | None = strawberry.field(
        description="Message from the last scheduling attempt."
    )
    failed_predicates: list[SchedulerPredicateGQL] | None = strawberry.field(
        description="List of predicates that failed during scheduling."
    )
    passed_predicates: list[SchedulerPredicateGQL] | None = strawberry.field(
        description="List of predicates that passed during scheduling."
    )
```

**Action**: Do not implement. Will be replaced by new scheduler design.

---

## Status History Types (Do Not Implement)

### KernelStatusHistoryEntryGQL

**Original Definition** (from PR #8079):

```python
@strawberry.type(
    name="KernelStatusHistoryEntry",
    description=(
        "Added in 26.1.0. A single status history entry recording a status transition. "
        "Contains the status name and the timestamp when the kernel entered that status."
    ),
)
class KernelStatusHistoryEntryGQL:
    status: str = strawberry.field(
        description="The kernel status name (e.g., 'PENDING', 'RUNNING', 'TERMINATED')."
    )
    timestamp: datetime = strawberry.field(
        description="Timestamp when the kernel entered this status."
    )
```

**Action**: Do not implement. Status history design will be revisited.

### KernelStatusHistoryGQL

**Original Definition** (from PR #8079):

```python
@strawberry.type(
    name="KernelStatusHistory",
    description=(
        "Added in 26.1.0. A collection of status history entries for a kernel. "
        "Records the progression of status changes throughout the kernel's lifecycle."
    ),
)
class KernelStatusHistoryGQL:
    entries: list[KernelStatusHistoryEntryGQL] = strawberry.field(
        description="List of status history entries in chronological order."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> KernelStatusHistoryGQL:
        entries = []
        for status, timestamp in data.items():
            if timestamp is None:
                continue
            if isinstance(timestamp, datetime):
                entries.append(KernelStatusHistoryEntryGQL(status=status, timestamp=timestamp))
            elif isinstance(timestamp, str):
                entries.append(
                    KernelStatusHistoryEntryGQL(
                        status=status,
                        timestamp=datetime.fromisoformat(timestamp),
                    )
                )
            else:
                raise InvalidKernelData(
                    f"Invalid timestamp type for status '{status}': "
                    f"expected datetime or str, got {type(timestamp).__name__}"
                )
        return cls(entries=entries)
```

**Action**: Do not implement. Status history design will be revisited.

---

## Affected Parent Types

The following types need modification to remove references to skipped types:

### KernelStatusDataContainerGQL

Remove `scheduler` field:

```python
# BEFORE (PR #8079)
class KernelStatusDataContainerGQL:
    error: KernelStatusErrorInfoGQL | None
    scheduler: SchedulerInfoGQL | None  # ← REMOVE
    kernel: KernelStatusDataGQL | None
    session: KernelSessionStatusDataGQL | None

# AFTER
class KernelStatusDataContainerGQL:
    error: KernelStatusErrorInfoGQL | None
    kernel: KernelStatusDataGQL | None
    session: KernelSessionStatusDataGQL | None
```

### KernelLifecycleInfoGQL

Remove `status_history` field:

```python
# BEFORE (PR #8079)
class KernelLifecycleInfoGQL:
    status: KernelStatusGQL
    result: SessionResultGQL
    status_changed: datetime | None
    status_info: str | None
    status_data: KernelStatusDataContainerGQL | None
    status_history: KernelStatusHistoryGQL | None  # ← REMOVE
    created_at: datetime | None
    terminated_at: datetime | None
    starts_at: datetime | None
    last_seen: datetime | None

# AFTER
class KernelLifecycleInfoGQL:
    status: KernelStatusGQL
    result: SessionResultGQL
    status_changed: datetime | None
    status_info: str | None
    status_data: KernelStatusDataContainerGQL | None
    created_at: datetime | None
    terminated_at: datetime | None
    starts_at: datetime | None
    last_seen: datetime | None
```

---

## from_kernel_info() Updates

The `from_kernel_info()` method needs to be updated to remove references:

```python
# REMOVE these lines:
status_history = KernelStatusHistoryGQL.from_mapping(
    kernel_info.lifecycle.status_history or {}
)

# REMOVE from KernelStatusDataContainerGQL.from_mapping():
# - All scheduler-related parsing code
# - References to SchedulerPredicateGQL
# - References to SchedulerInfoGQL

# REMOVE from KernelLifecycleInfoGQL instantiation:
# status_history=status_history,
```
