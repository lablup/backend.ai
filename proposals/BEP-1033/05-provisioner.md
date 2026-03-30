# Provisioner Test Scenarios

## Overview

Test scenarios for Provisioner components based on actual code behavior.

The Provisioner orchestrates the PENDING -> SCHEDULED transition pipeline:
1. **Sequencing**: Orders workloads using configured sequencer (FIFO/LIFO/DRF)
2. **Validation**: Checks quota and constraints per workload
3. **Agent Selection**: Selects agents using configured strategy
4. **Allocation**: Persists allocation information to database

**Test Structure:**
- **SessionProvisioner**: Tests orchestration by mocking Validator, Sequencer, Selector, Allocator
- **Validator**: Tests individual validation rules
- **Sequencer**: Tests sequencing strategies (FIFO, LIFO, DRF)
- **Selector**: Tests agent selection strategies (RoundRobin, Concentrated, Dispersed)
- **Allocator**: Tests allocation logic

**Source Files:**
- `sokovan/scheduler/provisioner/provisioner.py`
- `sokovan/scheduler/provisioner/validators/`
- `sokovan/scheduler/provisioner/sequencers/`
- `sokovan/scheduler/provisioner/selectors/`
- `sokovan/scheduler/provisioner/allocators/`

---

# Part 1: SessionProvisioner Tests

---

## schedule_scaling_group Flow

```python
async def schedule_scaling_group(scaling_group, scheduling_data) -> ScheduleResult:
    # 1. Convert to SessionWorkload
    workloads = [session.to_session_workload() for session in scheduling_data.pending_sessions.sessions]

    # 2. Convert to SystemSnapshot
    system_snapshot = scheduling_data.snapshot_data.to_system_snapshot(...)

    # 3. Sequencing (shared step)
    sequenced_workloads = sequencer.sequence(system_snapshot, workloads)

    # 4. Per-workload processing
    for workload in sequenced_workloads:
        try:
            allocation = await _schedule_workload(workload, ...)
            session_allocations.append(allocation)
        except Exception:
            scheduling_failures.append(SchedulingFailure(...))

    # 5. Batch allocation
    scheduled_sessions = await allocator.allocate(batch)

    # 6. Update Valkey queue with failed sessions
    await valkey_schedule.set_pending_queue(scaling_group, failure_ids)

    return ScheduleResult(scheduled_sessions=scheduled_sessions)
```

---

## Dependencies (Mock Targets)

- `validator: SchedulingValidator`
  - `validate(snapshot, workload)` -> Raises exception on failure
- `sequencer: SchedulingSequencer`
  - `sequence(snapshot, workloads)` -> `list[SessionWorkload]`
- `agent_selector: AgentSelector`
  - `select_agents_for_batch_requirements(...)` -> `list[AgentSelection]`
- `allocator: SchedulingAllocator`
  - `allocate(batch)` -> `list[ScheduledSessionData]`
- `repository: SchedulerRepository`
  - Various query methods
- `valkey_schedule: ValkeyScheduleClient`
  - `set_pending_queue(scaling_group, session_ids)` -> `None`

---

## Happy Path Scenarios

### SC-PR-001: All Sessions Scheduled Successfully

- **Purpose**: Verify all workloads pass through pipeline and get allocated
- **Dependencies (Mock):**
  - `sequencer.sequence(snapshot, [w1, w2])`:
    - Returns: `[w1, w2]` (FIFO order)
  - `validator.validate(snapshot, w1)`:
    - Returns: `None` (pass)
  - `validator.validate(snapshot, w2)`:
    - Returns: `None` (pass)
  - `agent_selector.select_agents_for_batch_requirements(...)`:
    - Returns: `[AgentSelection(agent_id=a1, ...)]` for each call
  - `allocator.allocate(batch)`:
    - Returns: `[ScheduledSessionData(s1), ScheduledSessionData(s2)]`
- **Input:**
  - `scheduling_data` with 2 pending sessions
- **Execution:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **Verification:**
  - `len(result.scheduled_sessions)` == 2
  - `valkey_schedule.set_pending_queue.assert_called_with("default", [])` (no failures)
- **Classification**: `happy-path`

---

### SC-PR-002: No Snapshot Returns Empty Result

- **Purpose**: Verify early return when snapshot data is missing
- **Dependencies (Mock):**
  - (No calls expected after early return)
- **Input:**
  - `scheduling_data.snapshot_data = None`
- **Execution:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **Verification:**
  - `result` is empty ScheduleResult
  - Warning logged for missing snapshot
- **Classification**: `edge-case`

---

### SC-PR-003: Sequencer Orders Workloads with DRF

- **Purpose**: Verify DRF sequencer is selected based on scheduler configuration
- **Dependencies (Mock):**
  - `scheduling_data.scaling_group.scheduler = "drf"`
- **Input:**
  - 3 workloads with different resource requirements
- **Execution:** Via `_get_sequencer("drf")`
- **Verification:**
  - DRF sequencer used (ordered by fair share)
- **Classification**: `happy-path`

---

## Validation Failure Scenarios

### SC-PR-004: Validation Failure Creates SchedulingFailure

- **Purpose**: Verify validation exceptions are caught and recorded
- **Dependencies (Mock):**
  - `validator.validate(snapshot, w1)`:
    - Raises: `QuotaExceeded("User quota exceeded")`
- **Input:**
  - Single workload `w1`
- **Execution:** Via `_schedule_workload()` in `schedule_scaling_group()`
- **Verification:**
  - `scheduling_failures` contains failure for `w1`
  - `failure.msg` contains "User quota exceeded"
  - Workload not passed to agent selector
- **Classification**: `error-case`

---

### SC-PR-005: Partial Validation Failure

- **Purpose**: Verify valid sessions proceed when some fail validation
- **Dependencies (Mock):**
  - `validator.validate(snapshot, w1)`:
    - Raises: `QuotaExceeded("...")`
  - `validator.validate(snapshot, w2)`:
    - Returns: `None` (pass)
  - `allocator.allocate(batch)`:
    - Returns: `[ScheduledSessionData(s2)]`
- **Input:**
  - 2 workloads: `w1` (fails), `w2` (passes)
- **Execution:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **Verification:**
  - `len(result.scheduled_sessions)` == 1 (w2 only)
  - `valkey_schedule.set_pending_queue.assert_called_with("default", [s1])`
- **Classification**: `error-case`

---

## Agent Selection Scenarios

### SC-PR-006: Agent Selection Uses Configured Strategy

- **Purpose**: Verify correct agent selector is used based on configuration
- **Dependencies (Mock):**
  - `scheduling_data.scaling_group.scheduler_opts.agent_selection_strategy = CONCENTRATED`
  - `agent_selector_pool[CONCENTRATED].select_agents_for_batch_requirements(...)`:
    - Returns: `[AgentSelection(...)]`
- **Execution:** Via `_schedule_workload()`
- **Verification:**
  - Concentrated selector used (not dispersed)
- **Classification**: `happy-path`

---

### SC-PR-007: Agent Selection Failure Creates SchedulingFailure

- **Purpose**: Verify agent selection exceptions are caught
- **Dependencies (Mock):**
  - `agent_selector.select_agents_for_batch_requirements(...)`:
    - Raises: `AgentSelectionError("No agents available")`
- **Input:**
  - Workload requiring 8 GPUs, no sufficient agents
- **Execution:** Via `_schedule_workload()` in `schedule_scaling_group()`
- **Verification:**
  - `scheduling_failures` contains failure
  - `failure.msg` contains "No agents available"
- **Classification**: `error-case`

---

### SC-PR-008: Designated Agent Selection

- **Purpose**: Verify designated agents are passed to selector
- **Dependencies (Mock):**
  - `workload.designated_agent_ids = [a1]`
  - `agent_selector.select_agents_for_batch_requirements(..., designated_agent_ids=[a1])`:
    - Returns: `[AgentSelection(agent_id=a1)]`
- **Execution:** Via `_allocate_workload()`
- **Verification:**
  - Selector called with designated_agent_ids
- **Classification**: `happy-path`

---

## Snapshot Update Scenarios

### SC-PR-009: Snapshot Updated After Allocation

- **Purpose**: Verify in-memory snapshot is updated for next workload
- **Setup:**
  - Initial keypair occupancy: `{ak1: {occupied_slots: 0, session_count: 0}}`
  - Workload allocates 4 CPU
- **Dependencies (Mock):**
  - `w1` allocation succeeds
- **Execution:** Via `_update_system_snapshot()` after allocation
- **Verification:**
  - `snapshot.resource_occupancy.by_keypair[ak1].occupied_slots` increased
  - `snapshot.resource_occupancy.by_keypair[ak1].session_count` increased
  - `snapshot.resource_occupancy.by_user[user_uuid]` increased
  - `snapshot.resource_occupancy.by_group[group_id]` increased
  - `snapshot.resource_occupancy.by_domain[domain_name]` increased
- **Classification**: `happy-path`

---

### SC-PR-010: SFTP Session Updates sftp_session_count

- **Purpose**: Verify private (SFTP) sessions update correct counter
- **Setup:**
  - `workload.is_private = True`
- **Execution:** Via `_update_system_snapshot()`
- **Verification:**
  - `snapshot.resource_occupancy.by_keypair[ak].sftp_session_count` increased
  - `snapshot.concurrency.sftp_sessions_by_keypair[ak]` increased
  - Regular `session_count` not increased
- **Classification**: `edge-case`

---

## Execution Recording Scenarios

### SC-PR-011: Execution Records Capture Steps

- **Purpose**: Verify recorder context captures all steps
- **Dependencies (Mock):**
  - All steps succeed
- **Execution:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **Verification:**
  - Records contain steps: `["sequencing", "validation", "agent_selection", "allocation"]`
  - Each step contains sub-steps
  - Passed predicates populated in allocation
- **Classification**: `happy-path`

---

### SC-PR-012: Failed Step Recorded in Predicates

- **Purpose**: Verify failed steps appear in failed_phases
- **Dependencies (Mock):**
  - `validator.validate()` raises exception
- **Input:**
  - Workload that fails validation
- **Execution:** Via `schedule_scaling_group()`
- **Verification:**
  - `scheduling_failure.failed_phases` contains validation predicate
  - `scheduling_failure.passed_phases` contains sequencing predicate
- **Classification**: `error-case`

---

## Valkey Queue Update Scenarios

### SC-PR-013: Failed IDs Recorded in Valkey Queue

- **Purpose**: Verify failed session IDs are stored for retry
- **Dependencies (Mock):**
  - 2 of 3 workloads fail
  - `valkey_schedule.set_pending_queue(scaling_group, failure_ids)`:
    - Returns: `None`
- **Input:**
  - 3 workloads, 2 fail
- **Execution:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **Verification:**
  - `valkey_schedule.set_pending_queue.assert_called_with("default", [s1, s2])`
- **Classification**: `happy-path`

---

## Concurrency and Batch Scenarios

### SC-PR-014: Agent State Updated Across Workloads

- **Purpose**: Verify mutable agent reflects allocations
- **Setup:**
  - Agent `a1` with 10 CPU capacity
  - Workload `w1` needs 4 CPU
  - Workload `w2` needs 4 CPU
- **Execution:** Both workloads allocated to same agent
- **Verification:**
  - After both allocations, agent `a1` has 8 CPU used
  - Third workload needing 4 CPU would fail (insufficient)
- **Classification**: `happy-path`

---

### SC-PR-015: Batch Allocation Atomicity

- **Purpose**: Verify allocations are processed as a batch for efficiency
- **Dependencies (Mock):**
  - `allocator.allocate(batch)`:
    - Receives batch with multiple allocations
    - Returns: `list[ScheduledSessionData]`
- **Input:**
  - 3 workloads all passing validation
- **Execution:** `await provisioner.schedule_scaling_group("default", scheduling_data)`
- **Verification:**
  - `allocator.allocate.assert_called_once()` (single batch call)
  - Batch contains all 3 allocations
- **Classification**: `happy-path`

---

# Part 2: Validator Tests

## Overview

`SchedulingValidator` applies multiple `ValidatorRule`s sequentially.
Each rule validates `SystemSnapshot` and `SessionWorkload`, raising exceptions on failure.

**Source Files:** `sokovan/scheduler/provisioner/validators/`

**Validation Rules:**
| Rule | Exception | Purpose |
|------|-----------|---------|
| `ConcurrencyValidator` | `ConcurrencyLimitExceeded` | Concurrent session limit per keypair |
| `DependenciesValidator` | `DependenciesNotSatisfied` | Session dependency satisfaction |
| `KeypairResourceLimitValidator` | `KeypairResourceQuotaExceeded` | Keypair resource quota |
| `UserResourceLimitValidator` | `UserResourceQuotaExceeded` | User resource quota |
| `GroupResourceLimitValidator` | `GroupResourceQuotaExceeded` | Group resource quota |
| `DomainResourceLimitValidator` | `DomainResourceQuotaExceeded` | Domain resource quota |
| `PendingSessionCountLimitValidator` | `PendingSessionCountLimitExceeded` | Pending session count limit |
| `PendingSessionResourceLimitValidator` | `PendingSessionResourceLimitExceeded` | Pending session resource limit |

---

## SchedulingValidator Integration Tests

### SC-VD-001: All Rules Pass

- **Purpose**: Verify no exception when all validation rules pass
- **Dependencies (Mock):**
  - `rule1.validate(snapshot, workload)`: Returns `None`
  - `rule2.validate(snapshot, workload)`: Returns `None`
- **Input:**
  - `snapshot`: Sufficient quota and resources
  - `workload`: Valid session workload
- **Execution:** `validator.validate(snapshot, workload)`
- **Verification:**
  - No exception raised
  - All rules' `validate()` called
- **Classification**: `happy-path`

---

### SC-VD-002: Single Rule Failure Raises Exception

- **Purpose**: Verify single rule failure raises that exception directly
- **Dependencies (Mock):**
  - `rule1.validate(snapshot, workload)`: Raises `QuotaExceeded`
  - `rule2.validate(snapshot, workload)`: Returns `None` (pass)
- **Execution:** `validator.validate(snapshot, workload)`
- **Verification:**
  - `QuotaExceeded` exception raised (single error is raised directly)
  - `rule2.validate.assert_called_once()` (all rules executed)
- **Classification**: `error-case`

---

### SC-VD-002-1: Multiple Rule Failures Raise MultipleValidationErrors

- **Purpose**: Verify multiple rule failures collect all errors
- **Dependencies (Mock):**
  - `rule1.validate(snapshot, workload)`: Raises `QuotaExceeded`
  - `rule2.validate(snapshot, workload)`: Raises `ConcurrencyLimitExceeded`
  - `rule3.validate(snapshot, workload)`: Returns `None` (pass)
- **Execution:** `validator.validate(snapshot, workload)`
- **Verification:**
  - `MultipleValidationErrors` exception raised
  - `len(exception.errors)` == 2
  - All rules' `validate()` called
- **Classification**: `error-case`

---

## ConcurrencyValidator Tests

### SC-VD-003: Concurrent Session Limit Within - Pass

- **Purpose**: Verify pass when concurrent session count is within limit
- **Input:**
  - `snapshot.resource_policy.keypair_policies[ak1].max_concurrent_sessions` = 5
  - `snapshot.concurrency.sessions_by_keypair[ak1]` = 3
  - `workload.access_key` = `ak1`
  - `workload.is_private` = `False`
- **Execution:** `concurrency_validator.validate(snapshot, workload)`
- **Verification:**
  - No exception raised
- **Classification**: `happy-path`

---

### SC-VD-004: Concurrent Session Limit Exceeded - Fail

- **Purpose**: Verify failure when concurrent session count exceeds limit
- **Input:**
  - `snapshot.resource_policy.keypair_policies[ak1].max_concurrent_sessions` = 5
  - `snapshot.concurrency.sessions_by_keypair[ak1]` = 5
  - `workload.access_key` = `ak1`
  - `workload.is_private` = `False`
- **Execution:** `concurrency_validator.validate(snapshot, workload)`
- **Verification:**
  - `ConcurrencyLimitExceeded` exception raised
- **Classification**: `error-case`

---

## DependenciesValidator Tests

### SC-VD-005: No Dependencies - Pass

- **Purpose**: Verify sessions without dependencies always pass
- **Input:**
  - `workload.depends_on` = `[]`
- **Execution:** `dependencies_validator.validate(snapshot, workload)`
- **Verification:**
  - No exception raised
- **Classification**: `happy-path`

---

### SC-VD-006: All Dependencies Satisfied - Pass

- **Purpose**: Verify pass when all dependent sessions are TERMINATED + SUCCESS
- **Input:**
  - `snapshot.session_dependencies.by_session[workload.session_id]` = `[
      DependencyInfo(depends_on=s1, dependency_status=TERMINATED, dependency_result=SUCCESS),
      DependencyInfo(depends_on=s2, dependency_status=TERMINATED, dependency_result=SUCCESS)
    ]`
- **Execution:** `dependencies_validator.validate(snapshot, workload)`
- **Verification:**
  - No exception raised
- **Classification**: `happy-path`

---

### SC-VD-007: Dependencies Not Satisfied - Fail

- **Purpose**: Verify failure when dependent session is not TERMINATED + SUCCESS
- **Input:**
  - `snapshot.session_dependencies.by_session[workload.session_id]` = `[
      DependencyInfo(depends_on=s1, dependency_status=TERMINATED, dependency_result=SUCCESS),
      DependencyInfo(depends_on=s2, dependency_status=RUNNING, dependency_result=UNDEFINED)
    ]`
- **Execution:** `dependencies_validator.validate(snapshot, workload)`
- **Verification:**
  - `DependenciesNotSatisfied` exception raised
  - Exception message contains `s2`
- **Classification**: `error-case`

---

## KeypairResourceLimitValidator Tests

### SC-VD-008: Keypair Resource Quota Within - Pass

- **Purpose**: Verify pass when requested resources are within keypair quota
- **Input:**
  - `snapshot.resource_policy.by_keypair[ak1].total_resource_slots` = `{cpu: 100}`
  - `snapshot.resource_occupancy.by_keypair[ak1].occupied_slots` = `{cpu: 50}`
  - `workload.requested_slots` = `{cpu: 10}`
- **Execution:** `keypair_resource_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - No exception raised
- **Classification**: `happy-path`

---

### SC-VD-009: Keypair Resource Quota Exceeded - Fail

- **Purpose**: Verify failure when requested resources exceed keypair quota
- **Input:**
  - `snapshot.resource_policy.by_keypair[ak1].total_resource_slots` = `{cpu: 100}`
  - `snapshot.resource_occupancy.by_keypair[ak1].occupied_slots` = `{cpu: 95}`
  - `workload.requested_slots` = `{cpu: 10}`
- **Execution:** `keypair_resource_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - `KeypairResourceQuotaExceeded` exception raised
- **Classification**: `error-case`

---

## UserResourceLimitValidator Tests

### SC-VD-010: User Resource Quota Within - Pass

- **Purpose**: Verify pass when requested resources are within user quota
- **Input:**
  - `snapshot.resource_policy.by_user[user1].total_resource_slots` = `{cpu: 200}`
  - `snapshot.resource_occupancy.by_user[user1].occupied_slots` = `{cpu: 50}`
  - `workload.requested_slots` = `{cpu: 10}`
- **Execution:** `user_resource_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - No exception raised
- **Classification**: `happy-path`

---

### SC-VD-011: User Resource Quota Exceeded - Fail

- **Purpose**: Verify failure when requested resources exceed user quota
- **Input:**
  - `snapshot.resource_policy.by_user[user1].total_resource_slots` = `{cpu: 200}`
  - `snapshot.resource_occupancy.by_user[user1].occupied_slots` = `{cpu: 195}`
  - `workload.requested_slots` = `{cpu: 10}`
- **Execution:** `user_resource_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - `UserResourceQuotaExceeded` exception raised
- **Classification**: `error-case`

---

## GroupResourceLimitValidator Tests

### SC-VD-012: Group Resource Quota Within - Pass

- **Purpose**: Verify pass when requested resources are within group quota
- **Input:**
  - `snapshot.resource_policy.by_group[g1].total_resource_slots` = `{cpu: 500}`
  - `snapshot.resource_occupancy.by_group[g1].occupied_slots` = `{cpu: 100}`
  - `workload.requested_slots` = `{cpu: 10}`
- **Execution:** `group_resource_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - No exception raised
- **Classification**: `happy-path`

---

### SC-VD-013: Group Resource Quota Exceeded - Fail

- **Purpose**: Verify failure when requested resources exceed group quota
- **Input:**
  - `snapshot.resource_policy.by_group[g1].total_resource_slots` = `{cpu: 500}`
  - `snapshot.resource_occupancy.by_group[g1].occupied_slots` = `{cpu: 495}`
  - `workload.requested_slots` = `{cpu: 10}`
- **Execution:** `group_resource_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - `GroupResourceQuotaExceeded` exception raised
- **Classification**: `error-case`

---

## DomainResourceLimitValidator Tests

### SC-VD-014: Domain Resource Quota Within - Pass

- **Purpose**: Verify pass when requested resources are within domain quota
- **Input:**
  - `snapshot.resource_policy.by_domain[d1].total_resource_slots` = `{cpu: 1000}`
  - `snapshot.resource_occupancy.by_domain[d1].occupied_slots` = `{cpu: 500}`
  - `workload.requested_slots` = `{cpu: 10}`
- **Execution:** `domain_resource_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - No exception raised
- **Classification**: `happy-path`

---

### SC-VD-015: Domain Resource Quota Exceeded - Fail

- **Purpose**: Verify failure when requested resources exceed domain quota
- **Input:**
  - `snapshot.resource_policy.by_domain[d1].total_resource_slots` = `{cpu: 1000}`
  - `snapshot.resource_occupancy.by_domain[d1].occupied_slots` = `{cpu: 995}`
  - `workload.requested_slots` = `{cpu: 10}`
- **Execution:** `domain_resource_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - `DomainResourceQuotaExceeded` exception raised
- **Classification**: `error-case`

---

## PendingSessionCountLimitValidator Tests

### SC-VD-016: Pending Session Count Within - Pass

- **Purpose**: Verify pass when pending session count is within limit
- **Input:**
  - `snapshot.resource_policy.by_keypair[ak1].max_pending_session_count` = 10
  - `snapshot.concurrency.pending_sessions_by_keypair[ak1]` = 5
- **Execution:** `pending_session_count_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - No exception raised
- **Classification**: `happy-path`

---

### SC-VD-017: Pending Session Count Exceeded - Fail

- **Purpose**: Verify failure when pending session count exceeds limit
- **Input:**
  - `snapshot.resource_policy.by_keypair[ak1].max_pending_session_count` = 10
  - `snapshot.concurrency.pending_sessions_by_keypair[ak1]` = 10
- **Execution:** `pending_session_count_limit_validator.validate(snapshot, workload)`
- **Verification:**
  - `PendingSessionCountLimitExceeded` exception raised
- **Classification**: `error-case`

---

# Part 3: Sequencer Tests

## Overview

`SchedulingSequencer` filters workloads by priority then orders by strategy.

**Source Files:** `sokovan/scheduler/provisioner/sequencers/`

**Sequencer Strategies:**
| Strategy | Algorithm |
|----------|-----------|
| `FIFOSequencer` | First in, first out (original order) |
| `LIFOSequencer` | Last in, first out (reverse order) |
| `DRFSequencer` | Dominant Resource Fairness (fair share) |

---

## SchedulingSequencer Integration Tests

### SC-SQ-001: Only Highest Priority Selected

- **Purpose**: Verify only highest priority workloads included in sequencing
- **Input:**
  - `workloads`: `[w1(priority=10), w2(priority=5), w3(priority=10)]`
- **Execution:** `sequencer.sequence(snapshot, workloads)`
- **Verification:**
  - Result contains only `w1`, `w3` (priority=10)
  - `w2` excluded (priority=5)
- **Classification**: `happy-path`

---

### SC-SQ-002: Empty Workload List - WorkloadSequencer Level

- **Purpose**: Verify empty list returns empty list (direct WorkloadSequencer call)
- **Input:**
  - `workloads`: `[]`
- **Execution:** `workload_sequencer.sequence(snapshot, [])` (e.g., DRFSequencer)
- **Verification:**
  - Result is empty list (DRFSequencer early returns)
- **Note:** `SchedulingSequencer.sequence()` may error on `max()` for empty list - caller should validate
- **Classification**: `edge-case`

---

## FIFOSequencer Tests

### SC-SQ-003: FIFO Preserves Original Order

- **Purpose**: Verify original order is preserved
- **Input:**
  - `workloads`: `[w1, w2, w3]` (all same priority)
- **Execution:** `fifo_sequencer.sequence(snapshot, workloads)`
- **Verification:**
  - Result order: `[w1, w2, w3]`
- **Classification**: `happy-path`

---

## LIFOSequencer Tests

### SC-SQ-004: LIFO Reverses Order

- **Purpose**: Verify reverse order
- **Input:**
  - `workloads`: `[w1, w2, w3]` (all same priority)
- **Execution:** `lifo_sequencer.sequence(snapshot, workloads)`
- **Verification:**
  - Result order: `[w3, w2, w1]`
- **Classification**: `happy-path`

---

## DRFSequencer Tests

### SC-SQ-005: DRF - Lower Occupancy First

- **Purpose**: Verify workloads with lower dominant share scheduled first
- **Input:**
  - `snapshot.total_capacity` = `{cpu: 100, mem: 1000}`
  - `snapshot.resource_occupancy.by_keypair`:
    - `ak1`: `{cpu: 50}` (dominant share = 50%)
    - `ak2`: `{cpu: 10}` (dominant share = 10%)
  - `workloads`: `[w1(ak1), w2(ak2)]`
- **Execution:** `drf_sequencer.sequence(snapshot, workloads)`
- **Verification:**
  - Result order: `[w2, w1]` (ak2 first, lower occupancy)
- **Classification**: `happy-path`

---

### SC-SQ-006: DRF - Equal Occupancy Stable Sort

- **Purpose**: Verify original order preserved when dominant share is equal
- **Input:**
  - Two workloads with equal dominant share
- **Execution:** `drf_sequencer.sequence(snapshot, workloads)`
- **Verification:**
  - Original order preserved (stable sort)
- **Classification**: `edge-case`

---

### SC-SQ-007: DRF - Multi Resource Type

- **Purpose**: Verify highest occupancy among resource types is dominant share
- **Input:**
  - `snapshot.total_capacity` = `{cpu: 100, gpu: 10}`
  - `snapshot.resource_occupancy.by_keypair[ak1]` = `{cpu: 10, gpu: 5}`
  - dominant share = max(10/100, 5/10) = 50% (GPU)
- **Execution:** `drf_sequencer.sequence(snapshot, workloads)`
- **Verification:**
  - GPU occupancy used as dominant share
- **Classification**: `happy-path`

---

# Part 4: Selector Tests

## Overview

`AgentSelector` checks architecture compatibility, resource availability, then selects by strategy.

**Source Files:** `sokovan/scheduler/provisioner/selectors/`

**Selection Strategies:**
| Strategy | Algorithm |
|----------|-----------|
| `RoundRobinAgentSelector` | Cyclic selection |
| `ConcentratedAgentSelector` | Minimize resources (pack tightly) |
| `DispersedAgentSelector` | Maximize resources (spread out) |

**Selection Process:**
1. Filter by architecture compatibility
2. Filter by resource availability (slots + container count)
3. Check designated agents (use if available)
4. Select by strategy
5. Track state during batch selection

---

## AgentSelector Common Tests

### SC-SL-001: Architecture Mismatch - Fail

- **Purpose**: Verify failure when no agents match architecture
- **Input:**
  - `agents`: `[AgentInfo(arch="x86_64"), AgentInfo(arch="x86_64")]`
  - `requirements.architecture` = `"aarch64"`
- **Execution:** `selector.select_agents_for_batch_requirements(agents, criteria, config)`
- **Verification:**
  - `NoCompatibleAgentError` exception raised
- **Classification**: `error-case`

---

### SC-SL-002: Insufficient Resources - Fail

- **Purpose**: Verify failure when no agents have sufficient resources
- **Input:**
  - `agents`: `[AgentInfo(available_slots={cpu: 2})]`
  - `requirements.requested_slots` = `{cpu: 8}`
- **Execution:** `selector.select_agents_for_batch_requirements(agents, criteria, config)`
- **Verification:**
  - `InsufficientResourcesError` exception raised
- **Classification**: `error-case`

---

### SC-SL-003: Container Limit Exceeded - Fail

- **Purpose**: Verify failure when container count limit exceeded
- **Input:**
  - `agents`: `[AgentInfo(container_count=10)]`
  - `config.max_container_count` = 10
- **Execution:** `selector.select_agents_for_batch_requirements(agents, criteria, config)`
- **Verification:**
  - `ContainerLimitExceededError` exception raised
- **Classification**: `error-case`

---

### SC-SL-004: Designated Agent Used

- **Purpose**: Verify designated agent is used when compatible
- **Input:**
  - `agents`: `[AgentInfo(id=a1), AgentInfo(id=a2)]`
  - `designated_agent_ids` = `[a1]`
- **Execution:** `selector.select_agents_for_batch_requirements(agents, criteria, config, designated_agent_ids=[a1])`
- **Verification:**
  - Result selects `a1`
- **Classification**: `happy-path`

---

### SC-SL-005: Designated Agent Unavailable - Error

- **Purpose**: Verify error when designated agent is not compatible (no fallback)
- **Input:**
  - `agents`: `[AgentInfo(id=a1, arch="x86_64"), AgentInfo(id=a2, arch="aarch64")]`
  - `designated_agent_ids` = `[a1]`
  - `requirements.architecture` = `"aarch64"`
- **Execution:** `selector.select_agents_for_batch_requirements(..., designated_agent_ids=[a1])`
- **Verification:**
  - `NoAvailableAgentError` exception raised
  - Exception message contains "Designated agent"
- **Classification**: `error-case`

---

### SC-SL-006: Batch Selection State Tracking

- **Purpose**: Verify agent state is tracked during batch selection
- **Input:**
  - `agents`: `[AgentInfo(id=a1, available_slots={cpu: 10})]`
  - `requirements`: 2 kernels, each needing 4 CPU
- **Execution:** `selector.select_agents_for_batch_requirements(agents, criteria, config)`
- **Verification:**
  - After first selection, a1 tracked state: `additional_slots={cpu: 4}`
  - Second selection reflects tracked state
- **Classification**: `happy-path`

---

## RoundRobinAgentSelector Tests

### SC-SL-007: RoundRobin - Index-Based Selection

- **Purpose**: Verify agents selected by index (sorted by agent_id)
- **Input:**
  - `agents`: `[AgentInfo(id="a3"), AgentInfo(id="a1"), AgentInfo(id="a2")]`
  - `selector.next_index` = 0
- **Execution:** `select_tracker_by_strategy(trackers, ...)`
- **Verification:**
  - Sorted to `[a1, a2, a3]` → index 0 → `a1` selected
- **Note:** Index is not auto-incremented - managed by caller
- **Classification**: `happy-path`

---

### SC-SL-008: RoundRobin - Index Modulo Wrap

- **Purpose**: Verify index wraps via modulo when exceeding agent count
- **Input:**
  - `agents`: `[a1, a2]` (sorted)
  - `selector.next_index` = 5
- **Execution:** `select_tracker_by_strategy()`
- **Verification:**
  - `5 % 2 = 1` → `a2` selected
- **Classification**: `edge-case`

---

## ConcentratedAgentSelector Tests

### SC-SL-009: Concentrated - Minimum Resources Selected

- **Purpose**: Verify agent with least available resources selected
- **Input:**
  - `agents`:
    - `a1`: `available_slots={cpu: 10}`
    - `a2`: `available_slots={cpu: 5}`
- **Execution:** `concentrated_selector.select_tracker_by_strategy(...)`
- **Verification:**
  - `a2` selected (minimum resources)
- **Classification**: `happy-path`

---

### SC-SL-010: Concentrated - Minimize Unused Features

- **Purpose**: Verify agents without unused resource types preferred
- **Input:**
  - `a1`: `available_slots={cpu: 10, gpu: 4}` (GPU unused)
  - `a2`: `available_slots={cpu: 10}`
  - `requirements.requested_slots` = `{cpu: 4}` (no GPU needed)
- **Execution:** `concentrated_selector.select_tracker_by_strategy(...)`
- **Verification:**
  - `a2` selected (no unused features)
- **Classification**: `happy-path`

---

## DispersedAgentSelector Tests

### SC-SL-011: Dispersed - Maximum Resources Selected

- **Purpose**: Verify agent with most available resources selected
- **Input:**
  - `agents`:
    - `a1`: `available_slots={cpu: 10}`
    - `a2`: `available_slots={cpu: 20}`
- **Execution:** `dispersed_selector.select_tracker_by_strategy(...)`
- **Verification:**
  - `a2` selected (maximum resources)
- **Classification**: `happy-path`

---

### SC-SL-012: Dispersed - Load Distribution

- **Purpose**: Verify consecutive selections distribute to different agents
- **Input:**
  - `agents`:
    - `a1`: `available_slots={cpu: 20}`
    - `a2`: `available_slots={cpu: 20}`
  - `requirements`: 10 CPU needed
- **Execution:** Select twice
- **Verification:**
  - First: `a1` or `a2`
  - Second: different agent (state tracking reflects reduced availability)
- **Classification**: `happy-path`

---

# Part 5: Allocator Tests

## Overview

`RepositoryAllocator` delegates to `SchedulerRepository.allocate_sessions()` for allocation.

**Source Files:** `sokovan/scheduler/provisioner/allocators/`

---

### SC-AL-001: Successful Batch Allocation

- **Purpose**: Verify all allocations processed successfully
- **Dependencies (Mock):**
  - `repository.allocate_sessions(batch)`:
    - Returns: `[ScheduledSessionData(s1), ScheduledSessionData(s2)]`
- **Input:**
  - `batch`: 2 successful allocations
- **Execution:** `await allocator.allocate(batch)`
- **Verification:**
  - `len(result)` == 2
  - `repository.allocate_sessions.assert_called_once_with(batch)`
- **Classification**: `happy-path`

---

### SC-AL-002: Empty Batch Allocation

- **Purpose**: Verify empty batch returns empty result
- **Dependencies (Mock):**
  - `repository.allocate_sessions(batch)`:
    - Returns: `[]`
- **Input:**
  - `batch`: Empty batch
- **Execution:** `await allocator.allocate(batch)`
- **Verification:**
  - `result` == `[]`
- **Classification**: `edge-case`

---

### SC-AL-003: Partial Failure Batch

- **Purpose**: Verify batch with failures is handled correctly
- **Dependencies (Mock):**
  - `repository.allocate_sessions(batch)`:
    - Returns: `[ScheduledSessionData(s1)]` (s2 failed)
- **Input:**
  - `batch`: 1 success, 1 failure
- **Execution:** `await allocator.allocate(batch)`
- **Verification:**
  - `len(result)` == 1
  - Failed session not in result
- **Classification**: `error-case`

---

### SC-AL-004: Repository Exception Propagated

- **Purpose**: Verify repository exceptions are propagated appropriately
- **Dependencies (Mock):**
  - `repository.allocate_sessions(batch)`:
    - Raises: `DatabaseError("Connection failed")`
- **Execution:** `await allocator.allocate(batch)`
- **Verification:**
  - `DatabaseError` exception raised
- **Classification**: `error-case`
