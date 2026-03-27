# Scheduler Lifecycle Handler Test Scenarios

## Overview

Test scenarios for scheduler Lifecycle handlers based on actual code behavior.

**Source Files:**
- `sokovan/scheduler/handlers/lifecycle/check_precondition.py`
- `sokovan/scheduler/handlers/lifecycle/schedule_sessions.py`
- `sokovan/scheduler/handlers/lifecycle/start_sessions.py`
- `sokovan/scheduler/handlers/lifecycle/terminate_sessions.py`
- `sokovan/scheduler/handlers/lifecycle/deprioritize_sessions.py`
- `sokovan/scheduler/handlers/maintenance/sweep_sessions.py`

---

## CheckPreconditionLifecycleHandler

**Actual Behavior:**
1. Extract session IDs from input `SessionWithKernels`
2. Query `SessionDataForPull` from repository via `get_sessions_for_pull_by_ids()`
3. Call `launcher.trigger_image_pulling()` with sessions and image configs
4. Return all input sessions as success (image pulling is asynchronous)

**Dependencies (Mock Targets):**
- `launcher: SessionLauncher`
  - `trigger_image_pulling(sessions, image_configs)` → `None`
- `repository: SchedulerRepository`
  - `get_sessions_for_pull_by_ids(session_ids)` → `SessionsForPullResult`

**Note:** Schedule marking is handled by the Coordinator's PostProcessor.

**Status Transitions:**
```python
success = TransitionStatus(session=PREPARING, kernel=PREPARING)
expired = TransitionStatus(session=PENDING, kernel=PENDING)
```

---

### SC-CP-001: All Sessions Trigger Image Pulling

- **Purpose**: Verify that all SCHEDULED sessions trigger image pulling and are marked as success
- **Dependencies (Mock):**
  - `repository.get_sessions_for_pull_by_ids([s1, s2])`:
    - Returns: `SessionsForPullResult(sessions=[session1_data, session2_data], image_configs={...})`
  - `launcher.trigger_image_pulling(sessions_data, image_configs)`:
    - Returns: `None`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=SCHEDULED), SessionWithKernels(s2, status=SCHEDULED)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 2
    - `result.successes[0].session_id` == `s1`
    - `result.successes[0].from_status` == `SessionStatus.SCHEDULED`
    - `result.successes[0].reason` == `"passed-preconditions"`
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `repository.get_sessions_for_pull_by_ids.assert_called_once_with([s1, s2])`
    - `launcher.trigger_image_pulling.assert_called_once()`
- **Classification**: `happy-path`

---

### SC-CP-002: Empty Session List Returns Empty Result

- **Purpose**: Verify handler handles empty input without error
- **Dependencies (Mock):**
  - (No calls expected)
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **Execution:** `await handler.execute("default", [])`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `repository.get_sessions_for_pull_by_ids.assert_not_called()`
    - `launcher.trigger_image_pulling.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-CP-003: Launcher Exception Propagated

- **Purpose**: Verify launcher exception is propagated to Coordinator
- **Dependencies (Mock):**
  - `repository.get_sessions_for_pull_by_ids([s1])`:
    - Returns: `SessionsForPullResult(...)`
  - `launcher.trigger_image_pulling(...)`:
    - Raises: `AgentError("Connection failed")`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=SCHEDULED)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Exception**: `AgentError` raised (Coordinator handles with expired transition)
- **Classification**: `error-case`

---

## ScheduleSessionsLifecycleHandler

**Actual Behavior:**
1. Early return if input is empty
2. Build session map from session IDs (for subsequent lookup)
3. Call `repository.get_scheduling_data(scaling_group)` for full scheduling context
4. If scheduling_data is None, return all sessions as `skipped`
5. Call `provisioner.schedule_scaling_group(scaling_group, scheduling_data)`
6. Map `schedule_result.scheduled_sessions` to `SessionTransitionInfo` successes
7. Return non-scheduled sessions (priority/resource constraints) as `skipped`

**Dependencies (Mock Targets):**
- `provisioner: SessionProvisioner`
  - `schedule_scaling_group(scaling_group, scheduling_data)` → `ScheduleResult`
- `repository: SchedulerRepository`
  - `get_scheduling_data(scaling_group)` → `Optional[SchedulingData]`

**Note:** Schedule marking and cache invalidation are handled by the Coordinator's PostProcessor.

**Status Transitions:**
```python
success = TransitionStatus(session=SCHEDULED, kernel=SCHEDULED)
expired = TransitionStatus(session=TERMINATING, kernel=TERMINATING)
give_up = TransitionStatus(session=DEPRIORITIZING, kernel=None)
```

---

### SC-SS-001: Sessions Successfully Scheduled via Provisioner

- **Purpose**: Verify provisioner results are correctly mapped to handler results
- **Dependencies (Mock):**
  - `repository.get_scheduling_data("default")`:
    - Returns: `SchedulingData(...)`
  - `provisioner.schedule_scaling_group("default", scheduling_data)`:
    - Returns: `ScheduleResult(scheduled_sessions=[ScheduledSessionData(session_id=s1, ...), ScheduledSessionData(session_id=s2, ...)])`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 2
    - `result.successes[0].session_id` == `s1`
    - `result.successes[0].from_status` == `SessionStatus.PENDING`
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `repository.get_scheduling_data.assert_called_once_with("default")`
    - `provisioner.schedule_scaling_group.assert_called_once()`
- **Classification**: `happy-path`

---

### SC-SS-002: No Scheduling Data Returns All Sessions as Skipped

- **Purpose**: Verify all sessions are returned as skipped when scheduling_data is None
- **Dependencies (Mock):**
  - `repository.get_scheduling_data("default")`:
    - Returns: `None`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
    - `len(result.skipped)` == 2
    - `result.skipped[0].session_id` == `s1`
    - `result.skipped[0].reason` == `"no-scheduling-data"`
    - `result.skipped[1].session_id` == `s2`
  - **Mock Calls:**
    - `repository.get_scheduling_data.assert_called_once_with("default")`
    - `provisioner.schedule_scaling_group.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-SS-003: Provisioner Partial Success - Non-scheduled Sessions Returned as Skipped

- **Purpose**: Verify scheduled sessions are success, non-scheduled sessions are skipped
- **Dependencies (Mock):**
  - `repository.get_scheduling_data("default")`:
    - Returns: `SchedulingData(...)`
  - `provisioner.schedule_scaling_group("default", scheduling_data)`:
    - Returns: `ScheduleResult(scheduled_sessions=[ScheduledSessionData(session_id=s1, ...)])`
    - Note: s2 not scheduled this cycle due to priority or resource constraints
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 1
    - `result.successes[0].session_id` == `s1`
    - `len(result.failures)` == 0
    - `len(result.skipped)` == 1
    - `result.skipped[0].session_id` == `s2`
    - `result.skipped[0].from_status` == `SessionStatus.PENDING`
    - `result.skipped[0].reason` == `"not-scheduled-this-cycle"`
- **Classification**: `happy-path`

---

### SC-SS-004: Empty Session List Returns Empty Result

- **Purpose**: Verify handler handles empty input without error
- **Dependencies (Mock):**
  - (No calls expected)
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **Execution:** `await handler.execute("default", [])`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.skipped)` == 0
  - **Mock Calls:**
    - `repository.get_scheduling_data.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-SS-005: Insufficient Resources - All Sessions Skipped

- **Purpose**: Verify all sessions are returned as skipped when provisioner schedules none
- **Dependencies (Mock):**
  - `repository.get_scheduling_data("default")`:
    - Returns: `SchedulingData(...)`
  - `provisioner.schedule_scaling_group("default", scheduling_data)`:
    - Returns: `ScheduleResult(scheduled_sessions=[])` # Nothing scheduled due to insufficient resources
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
    - `len(result.skipped)` == 2
    - `result.skipped[0].session_id` == `s1`
    - `result.skipped[0].reason` == `"not-scheduled-this-cycle"`
    - `result.skipped[1].session_id` == `s2`
    - `result.skipped[1].reason` == `"not-scheduled-this-cycle"`
  - **Mock Calls:**
    - `repository.get_scheduling_data.assert_called_once_with("default")`
    - `provisioner.schedule_scaling_group.assert_called_once()`
- **Classification**: `edge-case`

---

## StartSessionsLifecycleHandler

**Actual Behavior:**
1. Early return if input is empty
2. Extract session IDs from input `SessionWithKernels`
3. Query `SessionDataForStart` from repository via `search_sessions_with_kernels_and_user()`
4. Call `launcher.start_sessions_for_handler()` with sessions and image configs
5. Return all input sessions as successes (kernel creation is asynchronous)

**Dependencies (Mock Targets):**
- `launcher: SessionLauncher`
  - `start_sessions_for_handler(sessions, image_configs)` → `None`
- `repository: SchedulerRepository`
  - `search_sessions_with_kernels_and_user(querier)` → `SessionsWithUserResult`

**Status Transitions:**
```python
success = TransitionStatus(session=CREATING, kernel=CREATING)
expired = TransitionStatus(session=PENDING, kernel=PENDING)
```

---

### SC-ST-001: All Sessions Start Successfully

- **Purpose**: Verify all PREPARED sessions trigger kernel creation and are marked as success
- **Dependencies (Mock):**
  - `repository.search_sessions_with_kernels_and_user(querier)`:
    - Returns: `SessionsWithUserResult(sessions=[session1_data, session2_data], image_configs={...})`
  - `launcher.start_sessions_for_handler(sessions_data, image_configs)`:
    - Returns: `None`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PREPARED), SessionWithKernels(s2, status=PREPARED)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 2
    - `result.successes[0].session_id` == `s1`
    - `result.successes[0].from_status` == `SessionStatus.PREPARED`
    - `result.successes[0].reason` == `"triggered-by-scheduler"`
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `repository.search_sessions_with_kernels_and_user.assert_called_once()`
    - `launcher.start_sessions_for_handler.assert_called_once()`
- **Classification**: `happy-path`

---

### SC-ST-002: Empty Session List Returns Empty Result

- **Purpose**: Verify handler handles empty input without error
- **Dependencies (Mock):**
  - (No calls expected)
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **Execution:** `await handler.execute("default", [])`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `launcher.start_sessions_for_handler.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-ST-003: Launcher Exception Propagated

- **Purpose**: Verify launcher exception is propagated to Coordinator
- **Dependencies (Mock):**
  - `repository.search_sessions_with_kernels_and_user(querier)`:
    - Returns: `SessionsWithUserResult(...)`
  - `launcher.start_sessions_for_handler(...)`:
    - Raises: `AgentError("Connection failed")`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PREPARED)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Exception**: `AgentError` raised (Coordinator handles with expired transition)
- **Classification**: `error-case`

---

## TerminateSessionsLifecycleHandler

**Actual Behavior:**
1. Early return if input is empty
2. Extract session IDs from input `SessionWithKernels`
3. Query `TerminatingSessionData` from repository via `get_terminating_sessions_by_ids()`
4. Early return if no terminating sessions found
5. Call `terminator.terminate_sessions_for_handler()` to send termination RPCs
6. Return empty result (status updates happen via agent events)

**Dependencies (Mock Targets):**
- `terminator: SessionTerminator`
  - `terminate_sessions_for_handler(terminating_sessions)` → `None`
- `repository: SchedulerRepository`
  - `get_terminating_sessions_by_ids(session_ids)` → `list[TerminatingSessionData]`

**Status Transitions:**
```python
success = None  # Handled via agent events
expired = TransitionStatus(session=TERMINATED, kernel=TERMINATED)
give_up = TransitionStatus(session=TERMINATED, kernel=TERMINATED)
```

---

### SC-TS-001: Sessions Trigger Termination RPC, Returns Empty Result

- **Purpose**: Verify termination RPC is called but handler returns empty result
- **Dependencies (Mock):**
  - `repository.get_terminating_sessions_by_ids([s1, s2])`:
    - Returns: `[TerminatingSessionData(s1, ...), TerminatingSessionData(s2, ...)]`
  - `terminator.terminate_sessions_for_handler(terminating_sessions)`:
    - Returns: `None`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=TERMINATING), SessionWithKernels(s2, status=TERMINATING)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0  # No state transition here
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `repository.get_terminating_sessions_by_ids.assert_called_once_with([s1, s2])`
    - `terminator.terminate_sessions_for_handler.assert_called_once()`
- **Classification**: `happy-path`

---

### SC-TS-002: No Terminating Sessions Returns Empty Result

- **Purpose**: Verify handler handles empty repository result
- **Dependencies (Mock):**
  - `repository.get_terminating_sessions_by_ids([s1])`:
    - Returns: `[]`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=TERMINATING)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `terminator.terminate_sessions_for_handler.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-TS-003: Empty Session List Returns Empty Result

- **Purpose**: Verify handler handles empty input without error
- **Dependencies (Mock):**
  - (No calls expected)
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **Execution:** `await handler.execute("default", [])`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
  - **Mock Calls:**
    - `repository.get_terminating_sessions_by_ids.assert_not_called()`
- **Classification**: `edge-case`

---

## DeprioritizeSessionsLifecycleHandler

**Actual Behavior:**
1. Early return if input is empty
2. Extract session IDs from input `SessionWithKernels`
3. Call `repository.lower_session_priority()` to lower priority by DEPRIORITIZE_AMOUNT (10)
4. Return all input sessions as successes (transitioned to PENDING)

**Dependencies (Mock Targets):**
- `repository: SchedulerRepository`
  - `lower_session_priority(session_ids, amount, min_priority)` → `None`

**Status Transitions:**
```python
success = TransitionStatus(session=PENDING, kernel=None)  # No kernel change
```

---

### SC-DP-001: Sessions Successfully Deprioritized

- **Purpose**: Verify session priorities are lowered and marked as success
- **Dependencies (Mock):**
  - `repository.lower_session_priority([s1, s2], 10, SESSION_PRIORITY_MIN)`:
    - Returns: `None`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=DEPRIORITIZING), SessionWithKernels(s2, status=DEPRIORITIZING)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 2
    - `result.successes[0].session_id` == `s1`
    - `result.successes[0].from_status` == `SessionStatus.DEPRIORITIZING`
    - `result.successes[0].reason` == `"deprioritized-for-rescheduling"`
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `repository.lower_session_priority.assert_called_once_with([s1, s2], 10, SESSION_PRIORITY_MIN)`
- **Classification**: `happy-path`

---

### SC-DP-002: Empty Session List Returns Empty Result

- **Purpose**: Verify handler handles empty input without error
- **Dependencies (Mock):**
  - (No calls expected)
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **Execution:** `await handler.execute("default", [])`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
  - **Mock Calls:**
    - `repository.lower_session_priority.assert_not_called()`
- **Classification**: `edge-case`

---

## SweepSessionsLifecycleHandler

**Actual Behavior:**
1. Early return if input is empty
2. Extract session IDs from input `SessionWithKernels`
3. Query timed-out sessions from repository via `get_pending_timeout_sessions_by_ids()`
4. Early return if no timed-out sessions
5. Return timed-out sessions as FAILURES (Coordinator classifies as expired)

**Dependencies (Mock Targets):**
- `repository: SchedulerRepository`
  - `get_pending_timeout_sessions_by_ids(session_ids)` → `list[PendingTimeoutSessionData]`

**Note:** Cache invalidation is handled by the Coordinator's PostProcessor.

**Status Transitions:**
```python
success = None  # No success transition for sweep
expired = TransitionStatus(session=TERMINATING, kernel=TERMINATING)
```

---

### SC-SW-001: Timed-out Sessions Returned as Failures

- **Purpose**: Verify sessions exceeding pending timeout are returned as failures
- **Dependencies (Mock):**
  - `repository.get_pending_timeout_sessions_by_ids([s1, s2])`:
    - Returns: `[PendingTimeoutSessionData(session_id=s1, ...)]` # Only s1 timed out
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING), SessionWithKernels(s2, status=PENDING)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 1
    - `result.failures[0].session_id` == `s1`
    - `result.failures[0].from_status` == `SessionStatus.PENDING`
    - `result.failures[0].reason` == `"PENDING_TIMEOUT_EXCEEDED"`
- **Classification**: `happy-path`

---

### SC-SW-002: No Timed-out Sessions Returns Empty Result

- **Purpose**: Verify handler handles no-timeout case
- **Dependencies (Mock):**
  - `repository.get_pending_timeout_sessions_by_ids([s1])`:
    - Returns: `[]`
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[SessionWithKernels(s1, status=PENDING)]`
- **Execution:** `await handler.execute("default", sessions)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
- **Classification**: `edge-case`

---

### SC-SW-003: Empty Session List Returns Empty Result

- **Purpose**: Verify handler handles empty input without error
- **Dependencies (Mock):**
  - (No calls expected)
- **Input:**
  - `scaling_group`: `"default"`
  - `sessions`: `[]`
- **Execution:** `await handler.execute("default", [])`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `repository.get_pending_timeout_sessions_by_ids.assert_not_called()`
- **Classification**: `edge-case`

---

## Test Coverage Summary

| Handler | happy-path | edge-case | error-case | Total |
|---------|------------|-----------|------------|-------|
| CheckPrecondition | SC-CP-001 | SC-CP-002 | SC-CP-003 | 3 |
| ScheduleSessions | SC-SS-001, SC-SS-003 | SC-SS-002, SC-SS-004, SC-SS-005 | - | 5 |
| StartSessions | SC-ST-001 | SC-ST-002 | SC-ST-003 | 3 |
| TerminateSessions | SC-TS-001 | SC-TS-002, SC-TS-003 | - | 3 |
| DeprioritizeSessions | SC-DP-001 | SC-DP-002 | - | 2 |
| SweepSessions | SC-SW-001 | SC-SW-002, SC-SW-003 | - | 3 |
| **Total** | **7** | **9** | **3** | **19** |

### Key Verification Points

1. **Dependency Call Verification**: Verify mocked dependencies (repository, launcher, provisioner, terminator) are called with correct parameters
2. **Return Value Verification**: Verify successes/failures/skipped list sizes, session_id, from_status, reason
3. **Skipped Return Verification**: Verify sessions not scheduled due to priority/resource constraints are returned as skipped
4. **Exception Propagation Verification**: Verify dependency exceptions are properly propagated to Coordinator
5. **Empty Input Handling**: Graceful handling of empty session lists
