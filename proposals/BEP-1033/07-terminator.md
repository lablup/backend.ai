# SessionTerminator Test Scenarios

## Overview

Test scenarios for `SessionTerminator` based on actual code behavior.

The Terminator handles:
1. **Session Termination**: Sends `destroy_kernel()` RPC to agents
2. **Stale Kernel Detection**: 2-stage verification (Valkey + Agent)

**Source Files:** `sokovan/scheduler/terminator/terminator.py`

---

## terminate_sessions_for_handler Flow

```python
async def terminate_sessions_for_handler(terminating_sessions) -> None:
    # 1. Collect termination tasks for all kernels with agents
    for session in terminating_sessions:
        for kernel in session.kernels:
            if kernel.agent_id:
                task = _terminate_kernel(agent_id, kernel_id, session_id, reason, slots)
                all_tasks.append(task)
            else:
                skipped_kernels += 1

    # 2. Execute all termination tasks concurrently
    results = await asyncio.gather(*all_tasks, return_exceptions=True)

    # 3. No return value (status updates via events)
    # Internally _terminate_sessions_internal() returns ScheduleResult but
    # public API returns None
```

---

## check_stale_kernels Flow

```python
async def check_stale_kernels(kernels) -> list[KernelId]:
    # Stage 1: Check presence status from Valkey
    statuses = await valkey_schedule.check_kernel_presence_status_batch(kernel_ids, agent_ids)

    # Filter STALE or None
    stale_kernel_id_set = {
        kernel_id for kernel_id in kernel_ids
        if statuses.get(kernel_id) is None or status.presence == STALE
    }

    # Stage 2: Verify with agent
    for kernel_info in kernels:
        if kernel_info.id not in stale_kernel_id_set:
            continue
        is_running = await client.check_running(kernel_info.id)
        if is_running is False:  # Explicit False only
            dead_kernel_ids.append(kernel_info.id)

    return dead_kernel_ids
```

---

## Dependencies (Mock Targets)

- `agent_client_pool: AgentClientPool`
  - `acquire(agent_id)` -> `AsyncContextManager[AgentClient]`
  - `AgentClient.destroy_kernel(kernel_id, session_id, reason, suppress_events)` -> `None`
  - `AgentClient.check_running(kernel_id)` -> `bool | None`
- `valkey_schedule: ValkeyScheduleClient`
  - `check_kernel_presence_status_batch(kernel_ids, agent_ids)` -> `dict[KernelId, HealthStatus]`

---

## Session Termination Scenarios

### SC-TE-001: All Kernels Terminated Successfully

- **Purpose**: Verify destroy_kernel is called for all kernels with agents
- **Dependencies (Mock):**
  - `agent_client.destroy_kernel(k1, s1, reason, suppress_events=False)`:
    - Returns: `None`
  - `agent_client.destroy_kernel(k2, s1, reason, suppress_events=False)`:
    - Returns: `None`
- **Input:**
  - Session `s1` with 2 kernels on agent `a1`
- **Execution:** `await terminator.terminate_sessions_for_handler([session])`
- **Verification:**
  - `destroy_kernel` called twice
  - No return value (`None`) - status updates handled via events
- **Classification**: `happy-path`

---

### SC-TE-002: Kernel Without Agent is Skipped

- **Purpose**: Verify kernels without agent assignment are skipped
- **Dependencies (Mock):**
  - Only one kernel has agent
- **Input:**
  - Session with 2 kernels: `k1` (agent=a1), `k2` (agent=None)
- **Execution:** `await terminator.terminate_sessions_for_handler([session])`
- **Verification:**
  - `destroy_kernel` called once (k1 only)
  - Log indicates skipped kernel
- **Classification**: `edge-case`

---

### SC-TE-003: Empty Session List Returns Immediately

- **Purpose**: Verify early return for empty input
- **Input:**
  - `terminating_sessions = []`
- **Execution:** `await terminator.terminate_sessions_for_handler([])`
- **Verification:**
  - No return value (`None`)
  - No agent calls
- **Classification**: `edge-case`

---

### SC-TE-004: Partial Termination Failure Logged

- **Purpose**: Verify partial failure doesn't block other terminations
- **Dependencies (Mock):**
  - `agent_client.destroy_kernel(k1, ...)`:
    - Raises: `AgentError("Agent offline")`
  - `agent_client.destroy_kernel(k2, ...)`:
    - Returns: `None`
- **Input:**
  - Session with kernels on 2 agents
- **Execution:** `await terminator.terminate_sessions_for_handler([session])`
- **Verification:**
  - Both destroy_kernel attempted (gather with return_exceptions)
  - Failure logged as warning
  - Success count: 1, Failure count: 1
- **Classification**: `error-case`

---

### SC-TE-005: Multiple Sessions Terminated in Parallel

- **Purpose**: Verify all sessions' kernels are processed concurrently
- **Dependencies (Mock):**
  - All destroy_kernel calls succeed
- **Input:**
  - 3 sessions with 2 kernels each (6 kernels total)
- **Execution:** `await terminator.terminate_sessions_for_handler(sessions)`
- **Verification:**
  - 6 termination tasks created
  - All executed via gather (parallel)
- **Classification**: `happy-path`

---

### SC-TE-006: KernelTerminationResult Captures Details

- **Purpose**: Verify termination result structure
- **Dependencies (Mock):**
  - `destroy_kernel` returns normally
- **Input:**
  - Kernel with `occupied_slots = ResourceSlot(cpu=4, mem=8GB)`
- **Execution:** Via `_terminate_kernel()`
- **Verification:**
  - Result contains: `kernel_id`, `agent_id`, `occupied_slots`, `success=True`
- **Classification**: `happy-path`

---

### SC-TE-007: Termination Error Captured in Result

- **Purpose**: Verify error details are captured on failure
- **Dependencies (Mock):**
  - `destroy_kernel` raises `AgentError("Connection timeout")`
- **Execution:** Via `_terminate_kernel()`
- **Verification:**
  - Result contains: `success=False`, `error="Connection timeout"`
- **Classification**: `error-case`

---

## Stale Kernel Detection Scenarios

### SC-TE-008: No Stale Kernels - All ALIVE from Valkey

- **Purpose**: Verify early return when no stale kernels
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1, k2], ...)`:
    - Returns: `{k1: ALIVE, k2: ALIVE}`
- **Input:**
  - `kernels = [KernelInfo(k1, agent=a1), KernelInfo(k2, agent=a1)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - Returns: `[]`
  - `agent_client.check_running.assert_not_called()` (stage 2 not needed)
- **Classification**: `happy-path`

---

### SC-TE-009: STALE from Valkey, Agent Confirms Dead

- **Purpose**: Verify full 2-stage detection for dead kernel
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - Returns: `{k1: STALE}`
  - `agent_client.check_running(k1)`:
    - Returns: `False`
- **Input:**
  - `kernels = [KernelInfo(k1, agent=a1)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - Returns: `[k1]`
  - `check_running` called for verification
- **Classification**: `happy-path`

---

### SC-TE-010: STALE from Valkey, But Agent Shows Alive

- **Purpose**: Verify false positive handling (kernel actually running)
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - Returns: `{k1: STALE}`
  - `agent_client.check_running(k1)`:
    - Returns: `True`
- **Input:**
  - `kernels = [KernelInfo(k1, agent=a1)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - Returns: `[]` (kernel is alive, not dead)
- **Classification**: `edge-case`

---

### SC-TE-011: No Presence Info (None) Treated as Stale

- **Purpose**: Verify None status triggers agent verification
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - Returns: `{}` (k1 not in result)
  - `agent_client.check_running(k1)`:
    - Returns: `False`
- **Input:**
  - `kernels = [KernelInfo(k1, agent=a1)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - Returns: `[k1]`
  - Missing status treated same as STALE
- **Classification**: `edge-case`

---

### SC-TE-012: Agent Verification Fails - Kernel Skipped

- **Purpose**: Verify graceful handling of agent communication error
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch(...)`:
    - Returns: `{k1: STALE, k2: STALE}`
  - `agent_client.check_running(k1)`:
    - Raises: `Exception("Agent unreachable")`
  - `agent_client.check_running(k2)`:
    - Returns: `False`
- **Input:**
  - 2 kernels both stale
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - Returns: `[k2]` (k1 skipped due to error)
  - Warning logged for k1
- **Classification**: `error-case`

---

### SC-TE-013: Kernel Without Agent Skipped in Stage 2

- **Purpose**: Verify kernels without agent cannot be verified
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - Returns: `{k1: STALE}`
- **Input:**
  - `kernels = [KernelInfo(k1, agent=None)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - Returns: `[]` (cannot verify without agent)
  - `agent_client_pool.acquire.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-TE-014: Empty Kernel List Returns Immediately

- **Purpose**: Verify early return for empty input
- **Input:**
  - `kernels = []`
- **Execution:** `await terminator.check_stale_kernels([])`
- **Verification:**
  - Returns: `[]`
  - No Valkey or agent calls
- **Classification**: `edge-case`

---

### SC-TE-015: Mixed Results - Some Alive, Some Dead

- **Purpose**: Verify correct filtering across multiple kernels
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1, k2, k3], ...)`:
    - Returns: `{k1: ALIVE, k2: STALE, k3: STALE}`
  - `agent_client.check_running(k2)`:
    - Returns: `False` (dead)
  - `agent_client.check_running(k3)`:
    - Returns: `True` (alive)
- **Input:**
  - 3 kernels: k1 (ALIVE), k2 (STALE+dead), k3 (STALE+alive)
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - Returns: `[k2]` (only k2 is truly dead)
  - `check_running` called only for k2 and k3
  - `check_running` not called for k1 (ALIVE from Valkey)
- **Classification**: `happy-path`

---

### SC-TE-016: Agent Verification Returns None - Kernel Skipped

- **Purpose**: Verify None response from agent doesn't terminate kernel
- **Dependencies (Mock):**
  - `valkey_schedule.check_kernel_presence_status_batch([k1], ...)`:
    - Returns: `{k1: STALE}`
  - `agent_client.check_running(k1)`:
    - Returns: `None` (uncertain)
- **Input:**
  - `kernels = [KernelInfo(k1, agent=a1)]`
- **Execution:** `await terminator.check_stale_kernels(kernels)`
- **Verification:**
  - Returns: `[]` (explicit False required to terminate)
- **Note**: Only `is_running is False` triggers termination
- **Classification**: `edge-case`

---

## Integration with Handler

### SC-TE-INT-001: Full Stale Sweep Flow

- **Purpose**: End-to-end test via SweepStaleKernelsKernelHandler
- **Setup:**
  - 5 RUNNING kernels
  - Valkey: 2 ALIVE, 3 STALE
  - Agent verification: 1 dead among stale, 2 alive
- **Execution Flow:**
  1. Coordinator queries RUNNING kernels
  2. Handler calls `terminator.check_stale_kernels()`
  3. Terminator checks Valkey, then agents
  4. Returns 1 dead kernel ID
  5. Handler returns failure for dead kernel
  6. Coordinator marks kernel as TERMINATED
- **Verification:**
  - Only 1 kernel terminated (correct filtering)
- **Classification**: `happy-path`
