---
Author: Jeongseok Kang (jskang@lablup.com)
Status: Draft
Created: 2026-10-21
Created-Version: 26.10.0
Target-Version:
Implemented-Version:
---

# Batch Session Retry Policy

## Related Issues

- Epic: #15935, this BEP: #15934
- First consumer: lablup/backend.ai-fasttrack#6454, which moves FastTrack's task auto-retry into the manager
- Prior art: #9806 (auto-restart of inference session containers, closed as not planned)

## 1. Goal

A batch session that fails is never run again. This BEP adds a per-session **retry policy**: after a retriable failure the manager re-queues **the same session** with a backoff delay and records each attempt.

Callers that retry today enqueue a new session per attempt. They cannot see why the session ended, and the session id changes on every attempt.

## 2. Current State & Scope, by Area

### 2.1 API

| | Item |
|---|---|
| ✅ | Batch sessions accept `batch_timeout` and `starts_at` (stored as `requested_starts_at`) at enqueue: REST v1 `/session/_/create*`, REST v2 `/v2/sessions/enqueue` and GraphQL v2 `enqueueSession` (`BatchConfigInput`) |
| ✅ | `PATCH /session/{name}` (restart) returns 501 |
| ➕ | `retry_policy` in `BatchConfigInput`, next to `batch_timeout`, on every enqueue route, plus the Python SDK and the CLI. The enqueue response echoes the accepted policy |
| ➕ | `retry_policy`, `retry_attempt`, `retry_next_attempt_at` and `attempts` on `SessionV2` and on the REST session info |

### 2.2 DB

| | Item |
|---|---|
| ✅ | `sessions.options` holds `SessionStoredOptions`, frozen at enqueue |
| ✅ | `sessions.status_info` holds the reason passed to `mark_sessions_for_termination`, and the promotion to TERMINATED keeps it |
| ✅ | Kernel `status_data.exit_code`; `SessionRow.set_session_result` drops the exit code (`# TODO: store exit code?`) |
| ✅ | `status_history` is a map keyed by status, so a repeated status overwrites its timestamp |
| ➕ | `SessionStoredOptions.retry_policy` (immutable after enqueue) |
| ➕ | `sessions.retry_attempt` (int, default 0): the 0-based index of the run in progress |
| ➕ | `sessions.retry_next_attempt_at` (timestamptz, nullable): the earliest time the next attempt may be scheduled. `requested_starts_at` stays untouched |
| ➕ | A `session_attempts` table (§3.5) |

### 2.3 Sokovan

| | Item |
|---|---|
| ✅ | `promote-to-terminated` (`CHECK_TERMINATING_PROGRESS`) moves a TERMINATING session to TERMINATED once all kernels are terminal, and runs `TerminatedTransitionHook` (network teardown) |
| ✅ | `RescheduleSessionsLifecycleHandler` returns a RESCHEDULING session to PENDING with the same id and config. Today only BEP-1055 preemption in reschedule mode writes RESCHEDULING |
| ✅ | Per-phase retry budgets (`HandlerOptions.max_retry_count`, default 5) for scheduling and startup only |
| ➕ | A retry branch in the promotion (§3.2) |
| ➕ | The prerequisites in §3.4. Three of them fix bugs that already affect preemption reschedule mode and reserved batch sessions |

### 2.4 Callbacks

| | Item |
|---|---|
| ✅ | `callback_url` receives `session_success` / `session_failure` only, sent by `handle_batch_result` when the agent reports the batch result. No other session status change reaches it |
| ➕ | For sessions with a policy, one callback per finished attempt, sent from the retry decision (§3.6) |

## 3. Implementation Design

### 3.1 Policy

```yaml
retry_policy:
  max_retries: 3          # the session runs at most 1 + max_retries times
  delay: 10              # seconds
  backoff: fixed          # fixed | exponential
  max_delay: 300         # seconds
  retry_on: [task-failed, task-timeout, abnormal-termination]
```

| Field | Type | Default | Bounds |
|---|---|---|---|
| `max_retries` | int | 3 | 1..999 |
| `delay` | int, seconds | 10 | ≥ 1 |
| `backoff` | enum | `fixed` | `fixed`, `exponential` |
| `max_delay` | int, seconds | 300 | ≥ `delay`; read only for `exponential` |
| `retry_on` | list of `KernelLifecycleEventReason` | `[task-failed, task-timeout, abnormal-termination]` | non-empty, unique, and a subset of the retriable reasons below |

- **Validation:** an invalid policy, or a policy on a non-BATCH session, is rejected with 400.
- **Delay before retry `n`:** `fixed` waits `delay`. `exponential` waits `min(delay * 2**n, max_delay)` and then adds up to 25% jitter, so the jittered delay can exceed `max_delay`.
- **Naming:** no unit suffix, matching `batch_timeout` in the same `BatchConfigInput`.

| Retriable reasons (allowed in `retry_on`) | Never retried |
|---|---|
| `task-failed`, `task-timeout`, `abnormal-termination`, `exceeded-max-retries` (startup give-up, §3.4), `preempted-by-scheduler` (preemption in terminate mode; does not use up the budget) | `user-requested`, any forced termination, `idle-*`, `pending-timeout`, any other reason, and a NULL reason |

`abnormal-termination` covers a dead container, including an out-of-memory kill of the container itself, an external `docker kill` and agent loss.

### 3.2 Retry decision

The decision runs in `promote-to-terminated`. At that point every kernel is terminal, so the attempt's exit codes and timestamps are final when the attempt record is written.

```
RUNNING ─(batch fails / kernel dies / startup gives up)─▶ TERMINATING (status_info = reason)
TERMINATING ─all kernels terminal─▶ retriable?
    yes ─▶ RESCHEDULING  (attempt recorded, callback, retry_attempt += 1, retry_next_attempt_at set)
            └─ RescheduleSessionsLifecycleHandler ─▶ PENDING ─▶ held until retry_next_attempt_at ─▶ …
    no  ─▶ TERMINATED    (attempt recorded, callback)
```

A session is retriable when all of these hold:

- its type is BATCH;
- it has a `retry_policy`;
- its `status_info` is in `retry_on`;
- `retry_attempt < max_retries`;
- no user terminate is recorded (§3.3).

| Contract | |
|---|---|
| **Promotion becomes a lifecycle handler** | The branch cannot be a `PromotionSpec` because a spec has a single `success_status`. A lifecycle handler with its own `LockID` owns the TERMINATING → TERMINATED / RESCHEDULING move. Sessions without a policy go to TERMINATED exactly as before |
| **One transaction, compare-and-set** | The status move, the attempt record, `retry_attempt += 1`, the `result` reset to UNDEFINED and `retry_next_attempt_at` are written in one transaction guarded by `status = TERMINATING AND retry_attempt = N`. A second manager replica that loses the race changes nothing |
| **The TERMINATED hook is skipped** | Its per-attempt work moves into the reschedule path (§3.4) |
| **Dependents** | `DependenciesValidator` requires TERMINATED + SUCCESS, so dependents wait for the final attempt and see only its outcome |
| **Priority** | Each attempt keeps the session's current priority, including any DEPRIORITIZING decrements |
| **`batch_timeout`** | Applies per attempt; the agent arms it on every start |
| **Cluster sessions** | A retry re-runs every kernel. `KernelGroup.failure_policy` is not enforced yet, so it has no effect on the retry decision |

### 3.3 User terminate wins

A non-forced terminate on a TERMINATING session is skipped today: TERMINATING is not in `terminatable_statuses()`.

For a session with a policy, the terminate request on a TERMINATING session overwrites `status_info` with `user-requested`, so the decision sees a never-retried reason. In the other statuses:

| Status when the user terminates | Outcome |
|---|---|
| RUNNING | TERMINATING with `user-requested`, then TERMINATED |
| TERMINATING | `status_info` becomes `user-requested`, then TERMINATED |
| RESCHEDULING | TERMINATING (RESCHEDULING is terminatable), then TERMINATED |
| PENDING, waiting for `retry_next_attempt_at` | CANCELLED (the existing pending cancel) |

### 3.4 Prerequisites

| # | Change | Why |
|---|---|---|
| P1 | `detect-termination` writes `abnormal-termination` to the session's `status_info`. Startup give-up and expired transitions to TERMINATING write `exceeded-max-retries`. The stamping is scoped to these transitions, because a generic reason in `_apply_transition` would let the promotion overwrite the TERMINATING reason | Today `_apply_transition` writes no reason, and RUNNING clears `status_info`, so a dead container reaches the promotion with NULL |
| P2 | A held session is reported to the scheduler as **skipped**, not as a failure. This covers `requested_starts_at`, `retry_next_attempt_at` and unmet dependencies | A `SchedulingValidationError` is recorded as a failure, so a reserved batch session is moved to DEPRIORITIZING after `max_retry_count` passes and loses 10 priority each budget cycle. This was reproduced with the real provisioner and handler |
| P3 | `pending_timeout` is measured from the session's latest entry into PENDING, not from `created_at` | Otherwise a re-queued session that ran longer than `pending_timeout` is cancelled as `pending-timeout` straight away. Preemption reschedule mode has the same bug |
| P4 | The reschedule path destroys the volatile network and records the failed agents (as `_apply_kernel_pending_resets` does), so the next attempt avoids the failed node | Network names derive from the session id, so a re-queued session collides with or leaks its previous network. Preemption reschedule mode has the same bug |
| P5 | `handle_batch_result` accepts a result only for a session that is RUNNING | A late result from attempt N must not mark attempt N+1 as finished |

Image-pull failures that cancel every kernel move the session straight to CANCELLED, so they never reach the promotion and are not retried.

### 3.5 Attempt record

`session_attempts` holds one row per finished attempt:

| Column | |
|---|---|
| `session_id`, `attempt` | Primary key |
| `status_info` | The reason the attempt ended |
| `result` | UNDEFINED, SUCCESS or FAILURE |
| `exit_code` | Per kernel, from the kernel's `status_data` (−1 unknown, −2 batch timeout) |
| `started_at`, `terminated_at` | The attempt's own timestamps; `status_history` cannot hold them |
| `agent_ids` | Per kernel |

`retry_attempt` is the 0-based index of the run in progress. With `max_retries: 3`, the runs are attempts 0 to 3.

### 3.6 Callback contract

For a session with a policy, `handle_batch_result` no longer sends the callback. Instead, the retry decision sends exactly one callback per finished attempt, after its transaction commits:

| Field | |
|---|---|
| `event` | `session_success` or `session_failure`, unchanged |
| `attempt` | The finished attempt's index |
| `will_retry` | `true` when the session went to RESCHEDULING |
| `status_info`, `exit_code` | From the attempt record |

The last callback has `will_retry: false`. A session cancelled while waiting for `retry_next_attempt_at` sends `session_failure` with `will_retry: false` and `status_info: user-requested`. Sessions without a policy send callbacks exactly as today.

## 4. Migration / Compatibility

- **Additive.** Sessions without `retry_policy` behave as before, apart from P2–P5, which fix existing bugs.
- **Status sequence:** a session with a policy can go TERMINATING → RESCHEDULING → PENDING → … on the same id. Consumers must treat {TERMINATED, CANCELLED} as final and read `will_retry`.
- **Rolling upgrade:** an older replica that wins the promotion terminates the session, which is the current behaviour. The enqueue response echoes `retry_policy`. An older manager ignores unknown fields, so it accepts the request but omits the policy from its response; that is how a client detects the manager does not support it.
- **Downgrade:** the new columns and table are ignored, and sessions in RESCHEDULING continue as a plain reschedule.
- **Out of scope; callers keep these:**
  - failures before a session exists (enqueue rejected, mount resolution);
  - a fresh scratch folder per attempt;
  - re-reading the configuration at retry time.

  Mounts, environment and image are fixed at enqueue.

## 5. Implementation Plan

1. **Prerequisites P1–P5.** Each is independently mergeable; P2–P4 fix bugs that exist today.
2. **API:** `retry_policy` in `BatchConfigInput` on every enqueue route, the SDK and the CLI; storage only.
3. **Sokovan:** the promotion lifecycle handler with the retry branch, the new columns, `session_attempts`, and the user-terminate rule.
4. **Exposure:** the read fields on `SessionV2` and the REST session info, and the callback contract.

## 6. Decision Summary

| Decision | Alternative rejected | Rationale |
|---|---|---|
| Re-queue the same session | A new session per attempt with lineage | A stable id for callbacks, dependencies and watchers; the name index needs no change |
| Decide in the promotion to TERMINATED | Decide in each place that marks TERMINATING | Every kernel is terminal, so the attempt record is complete and teardown is done before the decision. A single decision site |
| `retry_on` takes `KernelLifecycleEventReason` values | New failure classes | The same strings users see in `status_info`; no mapping table |
| BATCH sessions only | Every session type | Only batch sessions have a result; inference replicas are replaced by deployment scaling (#9806) |
| New columns for the attempt index and the next attempt time | Reusing `requested_starts_at`, or counting attempt rows | `requested_starts_at` is never overwritten after enqueue; a counter guarded by compare-and-set avoids lost updates |
| No resource-group default policy | `DefaultSessionOptions.retry_policy` | Can be added later next to `handler_options` |

## 7. Open Questions

- Does a session waiting for `retry_next_attempt_at` count toward pending-session limits? The pending limit is checked only at enqueue, and a re-queue does not pass through enqueue.
- Should the legacy `ComputeSessionNode` also expose `retry_attempt` and `attempts`? FastTrack polls `compute_session_list`, and the WebUI session pages read `ComputeSessionNode`.
- Should image-pull failures be retried? That would need the all-kernels-cancelled path to go through TERMINATING.

## 8. References

- [BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md): need_retry / expired / give_up and promotions
- [BEP-1055](BEP-1055-preemption-scheduler-mechanics.md): preemption reschedule mode. It states there is no separate RESCHEDULING state, but the code now has one (`RescheduleSessionsLifecycleHandler`)
- [BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md): preemption of low-priority sessions
