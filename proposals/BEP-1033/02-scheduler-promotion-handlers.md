# Scheduler Promotion Spec Test Scenarios

## Overview

Promotion operations are handled using declarative `PromotionSpec`. The previous handler-based
implementation was integrated into the Coordinator by removing unnecessary abstraction for simple
transformation logic.

The Coordinator queries sessions by the spec's kernel matching conditions and directly converts
matched sessions into `SessionTransitionInfo`.

**Source Files:**
- `sokovan/scheduler/types.py` - PromotionSpec definition
- `sokovan/scheduler/factory.py` - spec definitions and mapping
- `sokovan/scheduler/coordinator.py` - promotion processing logic
- `data/kernel/types.py` - KernelStatus state group definitions

---

## PromotionSpec Structure

```python
@dataclass(frozen=True)
class PromotionSpec:
    name: str                                    # Operation identifier
    target_statuses: list[SessionStatus]         # Target session statuses
    target_kernel_statuses: list[KernelStatus]   # Kernel matching conditions
    kernel_match_type: KernelMatchType           # ALL/ANY/NOT_ANY
    success_status: SessionStatus                # Status to transition to on success
    reason: str                                  # Transition reason
```

---

## KernelStatus State Groups

```python
class KernelStatus(CIStrEnum):
    @classmethod
    def pre_prepared_statuses(cls) -> frozenset[KernelStatus]:
        """Statuses before image pulling completion"""
        return frozenset((PENDING, SCHEDULED, PREPARING, BUILDING, PULLING))

    @classmethod
    def pre_running_statuses(cls) -> frozenset[KernelStatus]:
        """Statuses before kernel execution"""
        return frozenset((PENDING, SCHEDULED, PREPARING, BUILDING, PULLING, PREPARED, CREATING))
```

---

## Promotion Spec Definitions (4)

| ScheduleType | name | target_statuses | kernel_match | success_status | reason |
|--------------|------|-----------------|--------------|----------------|--------|
| CHECK_PULLING_PROGRESS | promote-to-prepared | PREPARING, PULLING | NOT_ANY(pre_prepared) | PREPARED | triggered-by-scheduler |
| CHECK_CREATING_PROGRESS | promote-to-running | CREATING | NOT_ANY(pre_running) | RUNNING | triggered-by-scheduler |
| CHECK_TERMINATING_PROGRESS | promote-to-terminated | TERMINATING | ALL(TERMINATED) | TERMINATED | triggered-by-scheduler |
| DETECT_KERNEL_TERMINATION | detect-termination | PENDING~RUNNING, DEPRIORITIZING | ANY(TERMINATED, CANCELLED) | TERMINATING | ABNORMAL_TERMINATION |

### Kernel Matching Semantics

- **NOT_ANY**: No kernels should be in the specified statuses (detecting exit from pre-X states)
- **ANY**: At least one kernel should be in the specified status (anomaly detection)
- **ALL**: All kernels must be in the specified status (completion verification)

---

## Coordinator Promotion Processing Flow

```
_process_promotion_schedule(spec)
    └── per scaling_group (parallel):
            _process_promotion_scaling_group(spec, schedule_type, scaling_group)
                ├── Build BatchQuerier with kernel match conditions
                ├── repository.search_sessions_for_handler(querier)
                ├── [Phase: {spec.name}]  # e.g., "promote-to-prepared"
                │   └── [Step: check_kernel_status]
                │       └── Build SessionTransitionInfo from session_infos
                ├── _handle_promotion_status_transitions(spec, result, records)
                │   ├── Get hook for target status
                │   ├── Execute hooks (fetch full data if needed)
                │   └── Batch update sessions with history
                └── Run post-processors
```

---

## Coordinator Promotion Processing Scenarios

### SC-PS-001: NOT_ANY Query Condition Verification (CHECK_PULLING_PROGRESS)

- **Purpose**: Verify NOT_ANY semantic is correctly applied to BatchQuerier
- **Dependencies (Mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - Returns: `[SessionInfo(s1, PREPARING), SessionInfo(s2, PULLING)]`
- **Input:**
  - `spec`: PromotionSpec for CHECK_PULLING_PROGRESS
  - `scaling_group`: `"default"`
- **Execution:** `await coordinator._process_promotion_scaling_group(spec, schedule_type, "default")`
- **Verification:**
  - **Mock Calls:**
    - Verify querier in `search_sessions_for_handler` call:
      - Contains `SessionConditions.by_scaling_group("default")`
      - Contains `SessionConditions.by_statuses([PREPARING, PULLING])`
      - Contains `SessionConditions.by_kernel_match(KernelStatus.pre_prepared_statuses(), NOT_ANY)`
- **Classification**: `happy-path`

---

### SC-PS-002: ANY Query Condition Verification (DETECT_KERNEL_TERMINATION)

- **Purpose**: Verify ANY semantic is correctly applied to BatchQuerier
- **Dependencies (Mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - Returns: `[SessionInfo(s1, RUNNING)]` (some kernels TERMINATED)
- **Input:**
  - `spec`: PromotionSpec for DETECT_KERNEL_TERMINATION
  - `scaling_group`: `"default"`
- **Verification:**
  - **Mock Calls:**
    - Contains `SessionConditions.by_kernel_match([TERMINATED], ANY)`
- **Classification**: `happy-path`

---

### SC-PS-003: SessionTransitionInfo Creation Verification

- **Purpose**: Verify correct conversion from SessionInfo to SessionTransitionInfo
- **Dependencies (Mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - Returns: `[SessionInfo(s1, status=PREPARING, access_key="ak1", creation_id="c1")]`
  - `repository.update_sessions_status_with_history()`: success
- **Input:**
  - `spec`: promote-to-prepared (reason="triggered-by-scheduler")
  - `scaling_group`: `"default"`
- **Verification:**
  - **Status Update Call:**
    - `session_id` == `s1`
    - `from_status` == `SessionStatus.PREPARING`
    - `to_status` == `SessionStatus.PREPARED`
    - `reason` == `"triggered-by-scheduler"`
- **Classification**: `happy-path`

---

### SC-PS-004: Empty Session List Handling

- **Purpose**: Verify early return when no sessions match
- **Dependencies (Mock):**
  - `repository.search_sessions_for_handler(querier)`: Returns `[]`
  - `repository.update_sessions_status_with_history()`: should not be called
- **Verification:**
  - `update_sessions_status_with_history` not called
- **Classification**: `edge-case`

---

### SC-PS-005: Multiple Sessions Batch Processing

- **Purpose**: Verify multiple sessions are processed at once
- **Dependencies (Mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - Returns: `[SessionInfo(s1, CREATING), SessionInfo(s2, CREATING), SessionInfo(s3, CREATING)]`
- **Input:**
  - `spec`: promote-to-running
- **Verification:**
  - All 3 sessions transitioned to RUNNING
- **Classification**: `happy-path`

---

### SC-PS-006: Parallel Scaling Group Processing

- **Purpose**: Verify multiple scaling groups are processed in parallel
- **Dependencies (Mock):**
  - `repository.get_scaling_groups()`: Returns `["sg1", "sg2", "sg3"]`
- **Verification:**
  - `search_sessions_for_handler` called 3 times
- **Classification**: `happy-path`

---

## Kernel Matching Scenarios (Repository Integration)

### SC-KM-001: NOT_ANY Matching - No Pre-prepared Status Verification

- **Purpose**: Verify NOT_ANY(pre_prepared) filters correctly
- **Input:**
  - `spec`: promote-to-prepared
  - DB sessions:
    - `s1`: 2 kernels - PREPARED, RUNNING → included (no pre-prepared)
    - `s2`: 2 kernels - PREPARED, PULLING → excluded (PULLING is pre-prepared)
    - `s3`: 2 kernels - RUNNING, TERMINATED → included (no pre-prepared)
- **Verification:**
  - Query result: `[s1, s3]`
  - `s2` excluded due to PULLING kernel
- **Classification**: `happy-path`
- **Note**: Repository unit test

---

### SC-KM-002: NOT_ANY Matching - Terminal Status Allowed

- **Purpose**: Verify NOT_ANY allows terminal statuses
- **Input:**
  - `spec`: promote-to-running
  - DB sessions:
    - `s1`: 2 kernels - RUNNING, RUNNING → included
    - `s2`: 2 kernels - RUNNING, TERMINATED → included (partial failure allowed)
    - `s3`: 2 kernels - RUNNING, CREATING → excluded (CREATING is pre-running)
- **Verification:**
  - Query result: `[s1, s2]`
  - `s2` included despite some kernels being TERMINATED (partial failure allowed)
- **Classification**: `happy-path`

---

### SC-KM-003: ANY Matching - Detect if Any TERMINATED

- **Purpose**: Verify ANY(TERMINATED) detects partial kernel termination
- **Input:**
  - `spec`: detect-termination
  - DB sessions:
    - `s1`: 3 kernels - RUNNING, RUNNING, TERMINATED → included (1 TERMINATED)
    - `s2`: 2 kernels - RUNNING, RUNNING → excluded (no TERMINATED)
    - `s3`: 2 kernels - TERMINATED, TERMINATED → included (2 TERMINATED)
- **Verification:**
  - Query result: `[s1, s3]`
  - `s2` excluded due to no TERMINATED kernel
- **Classification**: `happy-path`

---

### SC-KM-004: ALL Matching - All Kernels Must Be TERMINATED

- **Purpose**: Verify ALL(TERMINATED) only matches complete termination
- **Input:**
  - `spec`: promote-to-terminated
  - DB sessions:
    - `s1`: 2 kernels - TERMINATED, TERMINATED → included
    - `s2`: 2 kernels - TERMINATED, TERMINATING → excluded (one still TERMINATING)
- **Verification:**
  - Query result: `[s1]`
- **Classification**: `happy-path`

---

## Hook Execution Scenarios

### SC-PH-001: RUNNING Status Hook Execution

- **Purpose**: Verify hook is executed on RUNNING transition
- **Dependencies (Mock):**
  - `hook_registry.get_hook(SessionStatus.RUNNING)`: Returns Hook
  - `hook.execute()`: Returns `HookResult(successes=[s1])`
- **Verification:**
  - `get_hook(RUNNING)` called
  - `hook.execute()` called
- **Classification**: `happy-path`

---

### SC-PH-002: Hook Failure Filters Sessions

- **Purpose**: Verify hook failure sessions are excluded from state transition
- **Dependencies (Mock):**
  - `hook.execute()`: Returns `HookResult(successes=[s1], failures=[s2])`
- **Verification:**
  - Only `s1` transitioned to RUNNING
  - `s2` not transitioned
- **Classification**: `error-case`

---

### SC-PH-003: No Hook Registered - Sessions Pass Through

- **Purpose**: Verify sessions pass through when no hook is registered
- **Dependencies (Mock):**
  - `hook_registry.get_hook(SessionStatus.PREPARED)`: Returns `None`
- **Verification:**
  - Only hook lookup performed, state transition proceeds without execution
- **Classification**: `happy-path`

---

## History Recording Scenarios

### SC-HR-001: Phase/Step Recording Verification

- **Purpose**: Verify Phase and Step are recorded during promotion processing
- **Dependencies (Mock):**
  - `repository.search_sessions_for_handler()`: Returns `[SessionInfo(s1)]`
- **Verification:**
  - `pool.build_all_records()` call result:
    - Phase: `spec.name` (e.g., "promote-to-prepared")
    - Phase detail: "Promoting to {success_status}"
    - Step: `"check_kernel_status"`
    - Step detail: "All kernels ready for {success_status}"
- **Classification**: `happy-path`

---

## Post-Processor Execution Scenarios

### SC-PP-001: Post-Processor Execution After Status Transition

- **Purpose**: Verify post-processor executes after successful status transition
- **Dependencies (Mock):**
  - `scheduling_controller.mark_next_schedule_needed()`: verify called
  - `valkey_schedule.invalidate_schedule_result_cache()`: verify called
- **Verification:**
  - Next schedule type marked
  - Schedule result cache invalidated
- **Classification**: `happy-path`

---

### SC-PP-002: Post-Processor Skip When No Transition

- **Purpose**: Verify post-processor is not executed when no state transition
- **Verification:**
  - `mark_next_schedule_needed` not called
- **Classification**: `edge-case`

---

## Spec Definition Verification Scenarios

### SC-SD-001: Factory PromotionSpec Definition Verification

- **Purpose**: Verify `_create_promotion_specs()` returns correct specs
- **Execution:** `specs = _create_promotion_specs()`
- **Verification:**
  - Specs defined for 4 ScheduleTypes
  - Verify field values for each spec:
    - CHECK_PULLING_PROGRESS:
      - `target_kernel_statuses` == `list(KernelStatus.pre_prepared_statuses())`
      - `kernel_match_type` == `NOT_ANY`
    - CHECK_CREATING_PROGRESS:
      - `target_kernel_statuses` == `list(KernelStatus.pre_running_statuses())`
      - `kernel_match_type` == `NOT_ANY`
    - CHECK_TERMINATING_PROGRESS:
      - `target_kernel_statuses` == `[TERMINATED]`
      - `kernel_match_type` == `ALL`
    - DETECT_KERNEL_TERMINATION:
      - `target_kernel_statuses` == `[TERMINATED]`
      - `kernel_match_type` == `ANY`
- **Classification**: `happy-path`

---

## Test Coverage Summary

| Category | happy-path | edge-case | error-case | Total |
|----------|------------|-----------|------------|-------|
| Coordinator Processing | SC-PS-001~006 | SC-PS-004 | - | 6 |
| Kernel Matching | SC-KM-001~004 | - | - | 4 |
| Hook Execution | SC-PH-001, SC-PH-003 | - | SC-PH-002 | 3 |
| History Recording | SC-HR-001 | - | - | 1 |
| Post-Processor | SC-PP-001 | SC-PP-002 | - | 2 |
| Spec Definition | SC-SD-001 | - | - | 1 |
| **Total** | **13** | **2** | **1** | **17** |

### Key Verification Points

1. **Kernel Matching Semantics**: Verify NOT_ANY/ANY/ALL work correctly
2. **Terminal Status Handling**: Allow partial failure (some kernels TERMINATED)
3. **Early Detection**: ANY detects immediately if any kernel is TERMINATED
4. **History Recording**: Verify Phase/Step are correctly recorded
5. **Hook Execution**: Verify status-specific hook calls and failure handling

### PromotionSpec Approach Advantages

- **Declarative Definition**: State transition logic clearly defined in specs
- **Duplication Removal**: Removed identical transformation logic from 4 handlers
- **Test Simplicity**: Coordinator-level integration tests suffice instead of individual handler tests
- **Maintainability**: Modify behavior by changing spec definitions only
- **Centralized State Groups**: Manage state groups via KernelStatus class methods
