# Scheduler Kernel Handler Test Scenarios

## Overview

Test scenarios for scheduler Kernel handlers based on actual code behavior.

Kernel handlers operate directly on `KernelInfo` objects (not sessions). The Coordinator
queries kernels via `search_kernels_for_handler()` and applies kernel-level state transitions.

**Source Files:**
- `sokovan/scheduler/handlers/kernel/sweep_stale_kernels.py`

---

## SweepStaleKernelsKernelHandler (SWEEP_STALE_KERNELS)

**Actual Behavior:**
1. Receive `KernelInfo` list from Coordinator (RUNNING kernels)
2. Delegate to `terminator.check_stale_kernels()` for 2-stage verification:
   - Stage 1: Check presence status in Valkey
   - Stage 2: Verify with agent's `check_running()` RPC
3. Classify kernels:
   - **successes**: Alive kernels (no state change)
   - **failures**: Dead/stale kernels (transition to TERMINATED)

**Dependencies (Mock Targets):**
- `terminator: SessionTerminator`
  - `check_stale_kernels(kernels)` -> `list[KernelId]` (dead kernel IDs)

**Note:** Schedule marking is handled directly by the Coordinator based on kernel failure results.

**Status Transitions:**
```python
success = None  # Maintain current status (kernel is alive)
failure = KernelStatus.TERMINATED  # Kernel is dead/stale
```

---

### SC-SK-001: All Kernels Alive - No State Change

- **Purpose**: Verify kernels confirmed alive are returned as successes
- **Dependencies (Mock):**
  - `terminator.check_stale_kernels([k1, k2])`:
    - Returns: `[]`  # No dead kernels
- **Input:**
  - `scaling_group`: `"default"`
  - `kernels`: `[KernelInfo(k1, status=RUNNING), KernelInfo(k2, status=RUNNING)]`
- **Execution:** `await handler.execute("default", kernels)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 2
    - `result.successes[0].kernel_id` == `k1`
    - `result.successes[0].from_status` == `KernelStatus.RUNNING`
    - `result.successes[0].reason` == `None`
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `terminator.check_stale_kernels.assert_called_once()`
- **Classification**: `happy-path`

---

### SC-SK-002: Dead Kernel Detected - Marked as Failure

- **Purpose**: Verify dead kernels are returned as failures for TERMINATED transition
- **Dependencies (Mock):**
  - `terminator.check_stale_kernels([k1, k2, k3])`:
    - Returns: `[k2]`  # k2 is dead
- **Input:**
  - `scaling_group`: `"default"`
  - `kernels`: `[KernelInfo(k1, status=RUNNING), KernelInfo(k2, status=RUNNING), KernelInfo(k3, status=RUNNING)]`
- **Execution:** `await handler.execute("default", kernels)`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 2  # k1 and k3
    - `len(result.failures)` == 1
    - `result.failures[0].kernel_id` == `k2`
    - `result.failures[0].from_status` == `KernelStatus.RUNNING`
    - `result.failures[0].reason` == `"STALE_KERNEL"`
- **Classification**: `happy-path`

---

### SC-SK-003: Empty Kernel List Returns Empty Result

- **Purpose**: Verify handler handles empty input without error
- **Dependencies (Mock):**
  - (No calls expected - early return)
- **Input:**
  - `scaling_group`: `"default"`
  - `kernels`: `[]`
- **Execution:** `await handler.execute("default", [])`
- **Verification:**
  - **Return Value:**
    - `len(result.successes)` == 0
    - `len(result.failures)` == 0
  - **Mock Calls:**
    - `terminator.check_stale_kernels.assert_not_called()`
- **Classification**: `edge-case`

---

## Integration: Kernel Handler + Coordinator Flow

### SC-KH-INT-001: Full Stale Kernel Sweep Flow

- **Purpose**: End-to-end test of stale kernel detection and status update
- **Setup:**
  - 3 RUNNING kernels: `k1`, `k2`, `k3`
  - Valkey presence: `k1` = STALE, `k2` = ALIVE, `k3` = STALE
  - Agent verification: `k1` = False (dead), `k3` = True (actually alive)
- **Execution Flow:**
  1. Coordinator queries RUNNING kernels via `search_kernels_for_handler()`
  2. Coordinator calls `handler.execute("default", [k1, k2, k3])`
  3. Handler calls `terminator.check_stale_kernels()`
  4. Terminator returns `[k1]` (only k1 is actually dead)
  5. Handler returns `successes=[k2, k3], failures=[k1]`
  6. Coordinator calls `_handle_kernel_result()`
  7. Coordinator calls `kernel_state_engine.mark_kernel_terminated(k1, "kernel_handler_failure")`
  8. Coordinator calls `handler.post_process(result)`
- **Verification:**
  - Only `k1` marked as TERMINATED
  - `k2` and `k3` remain RUNNING
  - DETECT_KERNEL_TERMINATION triggered
- **Classification**: `happy-path`

---

### SC-KH-INT-002: Lock Acquisition for Kernel Handler

- **Purpose**: Verify Coordinator acquires correct lock for Kernel handler
- **Dependencies (Mock):**
  - `lock_factory(LockID.LOCKID_SOKOVAN_TARGET_TERMINATING, lifetime)`:
    - Returns: AsyncContextManager (mocked)
- **Input:**
  - Handler: `SweepStaleKernelsKernelHandler` (has `lock_id`)
- **Execution:** Via Coordinator `_process_kernel_schedule()`
- **Verification:**
  - Lock acquired with `LockID.LOCKID_SOKOVAN_TARGET_TERMINATING`
  - Lock released after handler execution
- **Classification**: `happy-path`

---

## Terminator's check_stale_kernels Implementation

The `SessionTerminator`'s `check_stale_kernels()` method performs 2-stage verification:

### Stage 1: Valkey Presence Check

```python
statuses = await self._valkey_schedule.check_kernel_presence_status_batch(
    kernel_ids, agent_ids=agent_ids
)
# Filter STALE or None status
stale_kernel_id_set = {
    kernel_id for kernel_id in kernel_ids
    if (status := statuses.get(kernel_id)) is None
    or status.presence == HealthCheckStatus.STALE
}
```

### Stage 2: Agent Verification

```python
for kernel_info in kernels:
    if kernel_info.id not in stale_kernel_id_set:
        continue
    async with self._agent_client_pool.acquire(agent_id) as client:
        is_running = await client.check_running(kernel_info.id)
    if is_running is False:  # Explicit False only
        dead_kernel_ids.append(kernel_info.id)
```

---

### SC-CSK-001: Valkey Returns All ALIVE

- **Purpose**: Test early return when no potentially stale kernels
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - Returns: `{k1: HealthCheckStatus.ALIVE, k2: HealthCheckStatus.ALIVE}`
- **Input:**
  - `kernels`: `[KernelInfo(k1, agent=a1), KernelInfo(k2, agent=a1)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - **Return Value:** `[]` (no dead kernels)
  - **Mock Calls:**
    - `agent_client_pool.acquire.assert_not_called()` (no agent verification needed)
- **Classification**: `happy-path`

---

### SC-CSK-002: Valkey Returns STALE, Agent Confirms Dead

- **Purpose**: Test full 2-stage verification for confirmed dead kernel
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - Returns: `{k1: HealthCheckStatus.STALE}`
  - `agent_client.check_running(k1)`:
    - Returns: `False`
- **Input:**
  - `kernels`: `[KernelInfo(k1, agent=a1)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - **Return Value:** `[k1]`
  - **Mock Calls:**
    - `agent_client.check_running.assert_called_once_with(k1)`
- **Classification**: `happy-path`

---

### SC-CSK-003: Valkey Returns STALE, Agent Shows Still Running

- **Purpose**: Test false positive from Valkey (kernel actually alive)
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - Returns: `{k1: HealthCheckStatus.STALE}`
  - `agent_client.check_running(k1)`:
    - Returns: `True`
- **Input:**
  - `kernels`: `[KernelInfo(k1, agent=a1)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - **Return Value:** `[]` (kernel is actually alive)
- **Classification**: `edge-case`

---

### SC-CSK-004: Agent Verification Fails - Kernel Skipped

- **Purpose**: Test graceful handling of agent communication failure
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - Returns: `{k1: HealthCheckStatus.STALE, k2: HealthCheckStatus.STALE}`
  - `agent_client.check_running(k1)`:
    - Raises: `Exception("Connection refused")`
  - `agent_client.check_running(k2)`:
    - Returns: `False`
- **Input:**
  - `kernels`: `[KernelInfo(k1, agent=a1), KernelInfo(k2, agent=a2)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - **Return Value:** `[k2]` (k1 skipped due to error, k2 confirmed dead)
  - Warning logged for k1
- **Classification**: `error-case`

---

### SC-CSK-005: Kernel Without Agent - Skipped

- **Purpose**: Test kernels without assigned agent are skipped
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch()`:
    - Returns: `{k1: HealthCheckStatus.STALE}`
- **Input:**
  - `kernels`: `[KernelInfo(k1, agent=None)]`  # No agent assigned
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - **Return Value:** `[]` (cannot verify without agent)
  - `agent_client_pool.acquire.assert_not_called()`
- **Classification**: `edge-case`
