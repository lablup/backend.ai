---
Author: Jeongseok Kang (jskang@lablup.com)
Status: Draft
Created: 2026-04-27
Created-Version: 26.5.0
Target-Version:
Implemented-Version:
---

# Agent-level Batch Retry

## Related Issues

- JIRA: BA-5851
- GitHub Epic: #11320
- GitHub: #11321
- Companion BEP: [BEP-1054 — Session Rescheduling on Terminal Failure](BEP-1054-session-rescheduling-on-terminal-failure.md)

## Motivation

When a `BATCH` session's entrypoint exits non-zero, the session is marked failed and the user must manually re-submit. Most batch failures in practice are transient (a flaky network call, a downstream service hiccup, an intermittent dependency error) and a simple in-place re-run would have succeeded. Today the user pays the cost of re-creating the session — re-scheduling, re-pulling the image, re-mounting volumes — for a problem that is purely inside the script.

This BEP adds a small **agent-side** knob: re-run the batch entrypoint inside the same kernel up to N times before reporting failure. It is the simpler, smaller half of the batch-retry feature; the companion BEP-1054 covers the case where the failure is at the *node* level and a fresh schedule is needed.

### Goals

- Opt-in retry of the batch entrypoint inside an existing kernel.
- No new manager-side state, tables, or events.
- Default `batch_retries = 0` keeps current behavior.
- Per-session knob; no policy framework needed at this layer.

### Non-goals

- Failures before the kernel is running (image pull, scheduling). Those go to BEP-1054.
- OOM and node-level failures. Re-running on the same node typically does not help; BEP-1054 handles them by rescheduling.
- A user-supplied retry-policy DSL with backoff and classification. Out of scope for v1; if needed, accrue evidence first and design separately.

## Current Design

The agent runs batch entrypoints in `Agent.execute_batch()` (`src/ai/backend/agent/agent.py:2406`). The path:

1. Kernel reaches the running state.
2. If `kernel_obj.session_type == SessionTypes.BATCH` (`agent.py:2274`), the agent enqueues `execute_batch(session_id, kernel_id, startup_command, batch_timeout)` into `_ongoing_exec_batch_tasks` (line 840).
3. `execute_batch` invokes the kernel runner via `kernel.execute(...)` once.
4. On a non-zero exit code (or timeout), the agent emits `SessionFailureAnycastEvent` and `SessionFailureBroadcastEvent` (lines 2375, 2389, 2464, 2478, 2492).
5. On success, it emits `SessionSuccessAnycastEvent`/`SessionSuccessBroadcastEvent`.

There is no in-script retry — the entrypoint runs exactly once per session. `RestartTracker` (line 757) handles *kernel* restart on agent crash recovery, not script re-execution.

## Proposed Design

### Knob

Two new fields on the batch session creation request, plumbed through the existing kernel-config path that already carries `startup_command` and `batch_timeout`:

| Field | Type | Default | Meaning |
|---|---|---|---|
| `batch_retries` | int (≥ 0) | `0` | Maximum number of additional `execute_batch` attempts after the first. Total attempts = `1 + batch_retries`. |
| `batch_retry_delay` | float seconds (≥ 0) | `0.0` | Wait between attempts. Constant; no backoff at this layer. |

The two fields sit alongside `startup_command`, `bootstrap_script`, and `batch_timeout` in the session creation DTO. They are batch-only — the agent ignores them when `session_type != SessionTypes.BATCH`.

### Execution loop

`execute_batch` becomes:

```python
async def execute_batch(self, session_id, kernel_id, startup_command, batch_timeout,
                       batch_retries: int = 0, batch_retry_delay: float = 0.0):
    last_exit_code: int | None = None
    for attempt in range(batch_retries + 1):
        if attempt > 0:
            log.info("execute_batch(k:{}) retry attempt {}/{}", kernel_id, attempt, batch_retries)
            await asyncio.sleep(batch_retry_delay)
        last_exit_code = await self._run_batch_once(session_id, kernel_id, startup_command, batch_timeout)
        if last_exit_code == 0:
            await self._emit_session_success(session_id, kernel_id)
            return
        # else: non-zero exit -> retry if attempts remain
    # exhausted
    await self._emit_session_failure(session_id, kernel_id, last_exit_code)
```

Only **non-zero exit codes** trigger a retry. Cancellation, timeout, and infrastructure errors (kernel disconnect, container crash) do **not** loop here:
- Cancellation propagates as today.
- Timeout (`KernelLifecycleEventReason.TASK_TIMEOUT`, `agent.py:2492`) emits failure as today; rerunning a script that already ran past `batch_timeout` is unhelpful.
- Container-level failures escalate to BEP-1054's domain.

### Observability

- `bai_agent_batch_retry_attempted_total{session_id_type=batch}` counter (per attempt beyond the first).
- `bai_agent_batch_retry_succeeded_total` counter (incremented when a retry attempt exits zero).
- `bai_agent_batch_retry_exhausted_total` counter (incremented when the loop ends with non-zero).
- Each retry attempt logged at INFO with `(kernel_id, attempt, max_attempts)`.
- The existing failure event is emitted only on final exhaustion; no new event types.

### What does **not** change

- Session lifecycle, statuses, or transitions.
- Manager-side handlers (`SessionEventHandler`, sokovan).
- Database schema.
- `creation_id`, `parent_session_id` (does not exist), retry chain (does not exist).
- API surface beyond the two new fields on the create request.

The only manager-side change is plumbing `batch_retries` and `batch_retry_delay` from the create request into the kernel config payload that the agent already receives.

## Migration / Compatibility

- Default `batch_retries = 0` preserves current behavior for every existing caller.
- New fields are additive on the create request and on responses (echoed back for visibility).
- No Alembic migration required.
- Operators have a per-session opt-out by leaving the field unset; no global kill switch needed because the feature is opt-in.

## Implementation Plan

Two PRs:

1. **BEP draft** (this document) plus the companion BEP-1054 — #11321.
2. **Agent change:** extend `execute_batch` with the retry loop, plumb `batch_retries`/`batch_retry_delay` from kernel config, add metrics, unit tests around the loop semantics.
3. **Client surface:** SDK v2 + CLI v2 accept the two new fields on `./bai session create -t batch`. REST v2 / GraphQL v2 echo them on session info responses.

Tests live with the code under test. The agent's batch executor has existing test scaffolding; the loop is the smallest possible delta.

Estimated effort: under one week for one engineer, given the constrained scope.

## References

- Companion: [BEP-1054 — Session Rescheduling on Terminal Failure](BEP-1054-session-rescheduling-on-terminal-failure.md)
- Working draft of the prior single-BEP design and the pivot rationale: `docs/investigation/bep-1053-design-pivot.md`
- Apache Airflow's `retries` parameter (the inspirational reference): `airflow-core/src/airflow/models/taskinstance.py:1109-1159`
- [BEP-1030: Sokovan Scheduler Status Transition Design](BEP-1030-sokovan-scheduler-status-transition.md)
