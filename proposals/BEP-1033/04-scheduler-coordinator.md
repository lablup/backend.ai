# ScheduleCoordinator Test Scenarios

## Overview

Test scenarios for `ScheduleCoordinator` based on actual code behavior.

The Coordinator orchestrates the entire scheduling flow:
1. Acquire lock based on handler's `lock_id`
2. Iterate over scaling groups in parallel
3. Query sessions/kernels according to handler configuration
4. Execute handler
5. Classify failures as `give_up`, `expired`, or `need_retry`
6. Execute hooks for specific status transitions
7. Apply batch status updates with history recording
8. Broadcast transition events
9. Execute PostProcessor chain (schedule marking, cache invalidation)

**Source Files:**
- `sokovan/scheduler/coordinator.py`
- `sokovan/scheduler/post_processors/`

---

## Failure Classification

The Coordinator classifies failures based on the following criteria:

| Priority | Classification | Condition |
|----------|---------------|-----------|
| 1 | `give_up` | `phase_attempts >= SERVICE_MAX_RETRIES` (5) |
| 2 | `expired` | `elapsed > STATUS_TIMEOUT_MAP[status]` |
| 3 | `need_retry` | Default (neither give_up nor expired) |

**Timeout Thresholds:**
- PREPARING: 900 seconds (15 minutes)
- PULLING: 900 seconds (15 minutes)
- CREATING: 600 seconds (10 minutes)

---

### SC-CO-001: Failure Classified as give_up

- **Purpose**: Verify sessions exceeding max retries are classified as give_up
- **Setup:**
  - Session `s1` with `phase_attempts = 5` (equals SERVICE_MAX_RETRIES)
  - Handler returns `s1` as failure
- **Execution:** `_classify_failures([failure_s1], [session_s1])`
- **Verification:**
  - `result.give_up` contains `s1`
  - `result.expired` is empty
  - `result.need_retry` is empty
- **Classification**: `happy-path`

---

### SC-CO-002: Failure Classified as expired

- **Purpose**: Verify sessions exceeding timeout are classified as expired
- **Setup:**
  - Session `s1` in PREPARING status
  - `phase_started_at = now - 16 minutes` (exceeds 15-minute threshold)
  - `phase_attempts = 1` (below max retries)
- **Execution:** `_classify_failures([failure_s1], [session_s1])`
- **Verification:**
  - `result.expired` contains `s1`
  - `result.give_up` is empty
  - `result.need_retry` is empty
- **Classification**: `happy-path`

---

### SC-CO-003: Failure Classified as need_retry

- **Purpose**: Verify failures not matching give_up or expired are classified as need_retry
- **Setup:**
  - Session `s1` in PREPARING status
  - `phase_started_at = now - 5 minutes` (within threshold)
  - `phase_attempts = 1` (below max retries)
- **Execution:** `_classify_failures([failure_s1], [session_s1])`
- **Verification:**
  - `result.need_retry` contains `s1`
  - `result.give_up` is empty
  - `result.expired` is empty
- **Classification**: `happy-path`

---

### SC-CO-004: give_up Takes Priority Over expired

- **Purpose**: Verify give_up classification takes priority
- **Setup:**
  - Session `s1` with:
    - `phase_attempts = 5` (exceeds max retries)
    - `phase_started_at = now - 20 minutes` (also exceeds timeout)
- **Execution:** `_classify_failures([failure_s1], [session_s1])`
- **Verification:**
  - `result.give_up` contains `s1`
  - `result.expired` is empty (give_up takes priority)
- **Classification**: `edge-case`

---

## Hook Execution

### SC-CO-005: Hook Execution for RUNNING Transition

- **Purpose**: Verify hook is executed for sessions transitioning to RUNNING
- **Dependencies (Mock):**
  - `hook_registry.get_hook(SessionStatus.RUNNING)`:
    - Returns: `RunningStatusHook` (mocked)
  - `running_hook.execute(session_with_kernels)`:
    - Returns: `None`
  - `repository.search_sessions_with_kernels_for_handler(querier)`:
    - Returns: `[SessionWithKernels(s1)]`
- **Input:**
  - `session_infos`: `[SessionTransitionInfo(s1)]`
  - `target_status`: `SessionStatus.RUNNING`
- **Execution:** `await _execute_transition_hooks(session_infos, target_status)`
- **Verification:**
  - `hook_registry.get_hook.assert_called_with(SessionStatus.RUNNING)`
  - `running_hook.execute.assert_called_once()`
  - Result contains `s1` in `successful_sessions`
- **Classification**: `happy-path`

---

### SC-CO-006: Hook Failure Filters Sessions

- **Purpose**: Verify hook failure prevents session transition
- **Dependencies (Mock):**
  - `hook_registry.get_hook(SessionStatus.RUNNING)`:
    - Returns: `RunningStatusHook` (mocked)
  - `running_hook.execute(session_with_kernels)`:
    - Raises: `Exception("Hook failed")`
  - `repository.search_sessions_with_kernels_for_handler(querier)`:
    - Returns: `[SessionWithKernels(s1), SessionWithKernels(s2)]`
- **Input:**
  - `session_infos`: `[SessionTransitionInfo(s1), SessionTransitionInfo(s2)]`
  - `target_status`: `SessionStatus.RUNNING`
- **Execution:** `await _execute_transition_hooks(session_infos, target_status)`
- **Verification:**
  - `result.successful_sessions` contains only sessions where hook succeeded
  - Error logged for failed sessions
- **Classification**: `error-case`

---

### SC-CO-007: No Hook Registered - All Sessions Pass

- **Purpose**: Verify sessions pass through when no hook is registered
- **Dependencies (Mock):**
  - `hook_registry.get_hook(SessionStatus.RUNNING)`:
    - Returns: `None`
- **Input:**
  - `session_infos`: `[SessionTransitionInfo(s1)]`
  - `target_status`: `SessionStatus.RUNNING`
- **Execution:** `await _execute_transition_hooks(session_infos, target_status)`
- **Verification:**
  - This path is not called (hook is checked before calling _execute_transition_hooks)
- **Note**: Hook check actually happens before this method is called
- **Classification**: `edge-case`

---

## Status Transition Application

### SC-CO-008: Batch Status Update with History

- **Purpose**: Verify status updates and history are applied atomically
- **Dependencies (Mock):**
  - `repository.update_with_history(updater, creator)`:
    - Returns: `2` (update count)
- **Input:**
  - `handler_name`: `"schedule-sessions"`
  - `session_infos`: `[SessionTransitionInfo(s1), SessionTransitionInfo(s2)]`
  - `transition`: `TransitionStatus(session=SCHEDULED, kernel=SCHEDULED)`
  - `scheduling_result`: `SchedulingResult.SUCCESS`
- **Execution:** `await _apply_transition(handler_name, session_infos, transition, scheduling_result, records)`
- **Verification:**
  - `repository.update_with_history.assert_called_once()`
  - Updater spec contains `to_status=SCHEDULED`
  - History spec created for each session
- **Classification**: `happy-path`

---

### SC-CO-009: Reset Kernels to PENDING on give_up

- **Purpose**: Verify kernels are reset when session transitions to PENDING
- **Dependencies (Mock):**
  - `kernel_state_engine.reset_kernels_to_pending_for_sessions([s1])`:
    - Returns: `2` (reset count)
- **Input:**
  - `transition.kernel`: `KernelStatus.PENDING`
  - `session_ids`: `[s1]`
- **Execution:** Via `_apply_transition()` when `transition.kernel == PENDING`
- **Verification:**
  - `kernel_state_engine.reset_kernels_to_pending_for_sessions.assert_called_once_with([s1], reason="EXCEEDED_MAX_RETRIES")`
- **Classification**: `happy-path`

---

## Event Broadcasting

### SC-CO-010: Broadcast Events for Successful Transitions

- **Purpose**: Verify SchedulingBroadcastEvent is sent for transitions
- **Dependencies (Mock):**
  - `event_producer.broadcast_events_batch(events)`:
    - Returns: `None`
- **Input:**
  - `sessions`: `[SessionTransitionInfo(s1, creation_id=c1), SessionTransitionInfo(s2, creation_id=c2)]`
  - `to_status`: `SessionStatus.RUNNING`
- **Execution:** `await _broadcast_transition_events(sessions, to_status)`
- **Verification:**
  - `event_producer.broadcast_events_batch.assert_called_once()`
  - Event list contains 2 SchedulingBroadcastEvent items
  - Events include `session_id`, `creation_id`, `status_transition`
- **Classification**: `happy-path`

---

## Full Lifecycle Handler Processing

### SC-CO-011: Complete Lifecycle Handler Flow

- **Purpose**: End-to-end test of lifecycle handler processing
- **Setup:**
  - Scaling groups: `["default", "gpu"]`
  - Handler: `ScheduleSessionsLifecycleHandler`
  - Handler has `lock_id`
- **Dependencies (Mock):**
  - `lock_factory(lock_id, lifetime)`: Returns context manager
  - `repository.get_schedulable_scaling_groups()`: Returns `["default", "gpu"]`
  - `repository.get_sessions_for_handler()`: Returns sessions per scaling group
  - `repository.get_last_session_histories()`: Returns history map
  - `handler.execute()`: Returns result
  - `repository.update_with_history()`: Returns count
- **Execution:** `await process_lifecycle_schedule(ScheduleType.SCHEDULE)`
- **Verification:**
  - Lock acquired and released
  - Both scaling groups processed (parallel)
  - Handler executed for each scaling group
  - Status updates applied
- **Classification**: `happy-path`

---

### SC-CO-012: Lock Acquisition for Handler with lock_id

- **Purpose**: Verify lock is acquired when handler has lock_id
- **Dependencies (Mock):**
  - `lock_factory(LockID.LOCKID_SOKOVAN_TARGET_PENDING, lifetime)`:
    - Returns: AsyncContextManager
  - `config_provider.config.manager.session_schedule_lock_lifetime`:
    - Returns: `30.0`
- **Input:**
  - Handler with `lock_id = LockID.LOCKID_SOKOVAN_TARGET_PENDING`
- **Execution:** Via `_process_lifecycle_handler_schedule()`
- **Verification:**
  - `lock_factory.assert_called_with(LockID.LOCKID_SOKOVAN_TARGET_PENDING, 30.0)`
- **Classification**: `happy-path`

---

### SC-CO-013: No Lock for Handler Without lock_id

- **Purpose**: Verify no lock is acquired for handler without lock_id
- **Dependencies (Mock):**
  - (No lock factory call expected)
- **Input:**
  - Handler with `lock_id = None`
- **Execution:** Via `_process_lifecycle_handler_schedule()`
- **Verification:**
  - `lock_factory.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-CO-014: Scaling Group Processing Error Logging

- **Purpose**: Verify errors in parallel processing are logged
- **Dependencies (Mock):**
  - `repository.get_schedulable_scaling_groups()`: Returns `["default", "gpu"]`
  - `_process_scaling_group("default", ...)`: Returns normally
  - `_process_scaling_group("gpu", ...)`: Raises `Exception("DB error")`
- **Execution:** `await process_lifecycle_schedule(ScheduleType.SCHEDULE)`
- **Verification:**
  - Error logged for "gpu" scaling group
  - "default" scaling group still processed
  - Method returns True (partial success)
- **Classification**: `error-case`

---

## Promotion Handler Processing

### SC-CO-015: Promotion Spec Uses Kernel Match Conditions

- **Purpose**: Verify promotion spec queries include kernel matching
- **Dependencies (Mock):**
  - `repository.search_sessions_for_handler(querier)`:
    - Returns: `[SessionInfo(s1)]`
- **Input:**
  - spec: `PromotionSpec(name="promote-to-running", kernel_match_type=NOT_ANY, target_kernel_statuses=pre_running_statuses())`
- **Execution:** Via `_process_promotion_scaling_group(spec, schedule_type, scaling_group)`
- **Verification:**
  - Querier conditions include `by_kernel_match(pre_running_statuses(), NOT_ANY)`
- **Classification**: `happy-path`

---

## Kernel Handler Processing

### SC-CO-016: Kernel Handler Processes Kernel Results

- **Purpose**: Verify kernel status transitions are applied
- **Dependencies (Mock):**
  - `repository.search_kernels_for_handler(querier)`:
    - Returns: `KernelSearchResult(items=[k1, k2])`
  - `handler.execute()`:
    - Returns: `KernelExecutionResult(successes=[k1], failures=[k2])`
  - `kernel_state_engine.mark_kernel_terminated(k2, reason)`:
    - Returns: `True`
- **Execution:** Via `_process_kernel_scaling_group()`
- **Verification:**
  - `kernel_state_engine.mark_kernel_terminated.assert_called_with(k2, "kernel_handler_failure")`
  - Metrics observed for handler
- **Classification**: `happy-path`

---

## History Recording

### SC-CO-017: phase_attempts Set from History

- **Purpose**: Verify phase_attempts is set from last matching history
- **Dependencies (Mock):**
  - `repository.get_last_session_histories([s1])`:
    - Returns: `{s1: SchedulingHistoryRecord(phase="schedule-sessions", attempts=2)}`
- **Input:**
  - Session `s1` with handler `schedule-sessions`
- **Execution:** Via `_process_scaling_group()`
- **Verification:**
  - `session.phase_attempts == 2`
  - `session.phase_started_at` is set
- **Classification**: `happy-path`

---

### SC-CO-018: phase_attempts Reset When Phase Differs

- **Purpose**: Verify phase_attempts is 0 when history phase doesn't match
- **Dependencies (Mock):**
  - `repository.get_last_session_histories([s1])`:
    - Returns: `{s1: SchedulingHistoryRecord(phase="start-sessions", attempts=5)}`
- **Input:**
  - Session `s1` with handler `schedule-sessions` (different from history)
- **Execution:** Via `_process_scaling_group()`
- **Verification:**
  - `session.phase_attempts == 0` (history phase doesn't match)
  - `session.phase_started_at == None`
- **Classification**: `edge-case`

---

### SC-CO-019: Skipped Sessions Recorded Without Status Change

- **Purpose**: Verify skipped sessions are recorded in history
- **Dependencies (Mock):**
  - `handler.execute()`:
    - Returns: `SessionExecutionResult(skipped=[SessionTransitionInfo(s1, reason="blocked")])`
  - `repository.create_scheduling_history(creator)`:
    - Returns: `None`
- **Execution:** Via `_record_skipped_history()`
- **Verification:**
  - History created with `result=SKIPPED`
  - `from_status == to_status` (no change)
- **Classification**: `happy-path`

---

## PostProcessor Chain Execution

The Coordinator performs common post-processing tasks through a PostProcessor chain after handler execution.

**Source Files:** `sokovan/scheduler/post_processors/`

### SC-CO-020: ScheduleMarkingPostProcessor Marks Next Schedule Type

- **Purpose**: Verify correct schedule type is marked after status transition
- **Dependencies (Mock):**
  - `scheduling_controller.mark_scheduling_needed(ScheduleType.CHECK_PRECONDITION)`:
    - Returns: `None`
- **Input:**
  - `context.target_status`: `SessionStatus.SCHEDULED`
  - `context.result`: `SessionExecutionResult(successes=[...])`
- **Execution:** `await schedule_marking_post_processor.execute(context)`
- **Verification:**
  - `scheduling_controller.mark_scheduling_needed.assert_called_once_with(ScheduleType.CHECK_PRECONDITION)`
- **Classification**: `happy-path`

---

### SC-CO-021: ScheduleMarkingPostProcessor Skips for Unmapped Status

- **Purpose**: Verify marking is skipped when status has no mapping
- **Dependencies (Mock):**
  - (No calls expected)
- **Input:**
  - `context.target_status`: `SessionStatus.PENDING` (mapping = None)
  - `context.result`: `SessionExecutionResult(successes=[...])`
- **Execution:** `await schedule_marking_post_processor.execute(context)`
- **Verification:**
  - `scheduling_controller.mark_scheduling_needed.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-CO-022: ScheduleMarkingPostProcessor Skips for target_status=None

- **Purpose**: Verify marking is skipped when target_status is None
- **Dependencies (Mock):**
  - (No calls expected)
- **Input:**
  - `context.target_status`: `None`
  - `context.result`: `SessionExecutionResult(successes=[...])`
- **Execution:** `await schedule_marking_post_processor.execute(context)`
- **Verification:**
  - `scheduling_controller.mark_scheduling_needed.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-CO-023: CacheInvalidationPostProcessor Invalidates Affected Access Key Cache

- **Purpose**: Verify access keys are collected from successes and failures to invalidate cache
- **Dependencies (Mock):**
  - `repository.invalidate_kernel_related_cache([ak1, ak2, ak3])`:
    - Returns: `None`
- **Input:**
  - `context.result`:
    ```python
    SessionExecutionResult(
        successes=[SessionTransitionInfo(access_key=ak1), SessionTransitionInfo(access_key=ak2)],
        failures=[SessionTransitionInfo(access_key=ak3)]
    )
    ```
- **Execution:** `await cache_invalidation_post_processor.execute(context)`
- **Verification:**
  - `repository.invalidate_kernel_related_cache` called
  - Arguments contain `{ak1, ak2, ak3}` (order independent)
- **Classification**: `happy-path`

---

### SC-CO-024: CacheInvalidationPostProcessor Skips Without Access Keys

- **Purpose**: Verify cache invalidation is skipped when no affected access keys
- **Dependencies (Mock):**
  - (No calls expected)
- **Input:**
  - `context.result`:
    ```python
    SessionExecutionResult(
        successes=[SessionTransitionInfo(access_key=None)],
        failures=[]
    )
    ```
- **Execution:** `await cache_invalidation_post_processor.execute(context)`
- **Verification:**
  - `repository.invalidate_kernel_related_cache.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-CO-025: All PostProcessors Are Called

- **Purpose**: Verify Coordinator calls all registered PostProcessors
- **Dependencies (Mock):**
  - `schedule_marking_post_processor.execute()`:
    - Returns: `None`
  - `cache_invalidation_post_processor.execute()`:
    - Returns: `None`
- **Input:**
  - `result`: `SessionExecutionResult(successes=[SessionTransitionInfo(...)])`
  - `target_status`: `SessionStatus.SCHEDULED`
- **Execution:** `await coordinator._run_post_processors(result, target_status)`
- **Verification:**
  - `schedule_marking_post_processor.execute.assert_called_once()`
  - `cache_invalidation_post_processor.execute.assert_called_once()`
- **Classification**: `happy-path`
