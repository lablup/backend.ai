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

- Epic: #15935; this BEP: #15934
- First consumer: lablup/backend.ai-fasttrack#6454, which moves FastTrack's task auto-retry into the manager
- Prior art: #9806, auto-restart of inference session containers (closed, not planned)

## 1. Goal

A batch session that fails is never run again. This BEP adds a per-session **retry policy**: after a retriable failure, the manager re-queues **the same session** with a backoff delay and records each attempt.

Callers that retry today enqueue a new session for every attempt. They cannot see why the session ended, and the session id changes on every attempt.

## 2. Current State & Scope, by Area

### 2.1 API

| | Item |
|---|---|
| ✅ | Batch sessions accept `batch_timeout` and `starts_at` (stored as `requested_starts_at`) at enqueue:<br>- REST v1 `/session/_/create*`: top-level fields<br>- REST v2 `/v2/sessions/enqueue`: `BatchConfigInput`<br>- GraphQL v2 `enqueueSession`: `SessionBatchConfigInput` |
| ✅ | `PATCH /session/{name}` (restart) returns 501 |
| ✅ | REST v1 and v2 ignore unknown request fields. GraphQL v2 rejects them |
| ➕ | `retry_policy` next to `batch_timeout` on every enqueue route, plus the Python SDK and the CLI. The session returned by enqueue carries the accepted policy |
| ➕ | `retry_policy`, `retry_attempt`, `retry_next_attempt_at` and `attempts` on `SessionV2`, on the legacy `ComputeSessionNode`, and in the REST session info |
| ➕ | Manager config `session.retry-policy.enabled` (default `false`). While it is off, a request carrying `retry_policy` is rejected with 400 |

### 2.2 DB

| | Item |
|---|---|
| ✅ | `sessions.options` holds `SessionStoredOptions`, frozen at enqueue |
| ✅ | `sessions.status_info` holds the reason passed to `mark_sessions_for_termination`, and the promotion to TERMINATED keeps it |
| ✅ | Only `SessionSuccess/FailureAnycastEvent` carries the batch exit code (−2 means batch timeout), and `handle_batch_result` drops it. A kernel's `status_data.exit_code` is always −1, because no `KernelTerminatedAnycastEvent` passes one |
| ✅ | `status_history` is a map keyed by status, so a repeated status overwrites its timestamp |
| ➕ | `SessionStoredOptions.retry_policy`, immutable after enqueue |
| ➕ | `sessions.retry_attempt` (int, default 0): the 0-based index of the run in progress |
| ➕ | `sessions.retry_next_attempt_at` (timestamptz, nullable): the earliest time the next attempt may be scheduled. `requested_starts_at` is left untouched |
| ➕ | `sessions.terminate_requested_at` (timestamptz, nullable): set by a user terminate (§3.3) |
| ➕ | A `session_attempts` table (§3.5) |

### 2.3 Sokovan

| | Item |
|---|---|
| ✅ | `promote-to-terminated` (`CHECK_TERMINATING_PROGRESS`) moves a TERMINATING session to TERMINATED once all of its kernels are terminal, and runs `TerminatedTransitionHook`, which tears down the network |
| ✅ | `RescheduleSessionsLifecycleHandler` returns a RESCHEDULING session to PENDING with the same id and config. Today only BEP-1055 preemption in reschedule mode writes RESCHEDULING |
| ✅ | Per-phase retry budgets exist (`HandlerOptions.max_retry_count`, default 5), but only for scheduling and startup |
| ➕ | A retry branch at the promotion (§3.2), and the prerequisites in §3.4 |

### 2.4 Callbacks

| | Item |
|---|---|
| ✅ | `callback_url` receives `success` or `failure` (the event name with its `session_` prefix stripped). Only `handle_batch_result` sends them, when the agent reports the batch result. No other status change reaches `callback_url` |
| ➕ | For sessions with a policy: one callback per finished attempt, plus one when the session ends (§3.6) |

## 3. Implementation Design

### 3.1 Policy

```yaml
retry_policy:
  max_retries: 3          # the session runs at most 1 + max_retries times
  delay: 10
  backoff: fixed          # fixed | exponential
  max_delay: 300
  when: [task-failed, task-timeout, abnormal-termination]
```

| Field | Type | Default | Bounds |
|---|---|---|---|
| `max_retries` | int | 3 | 1..999 |
| `delay` | int, seconds | 10 | ≥ 1 |
| `backoff` | enum | `fixed` | `fixed`, `exponential` |
| `max_delay` | int, seconds | 300 | ≥ `delay` when `backoff` is `exponential`; ignored otherwise |
| `when` | list of `KernelLifecycleEventReason` | `[task-failed, task-timeout, abnormal-termination]` | Non-empty, unique, and drawn from the retriable reasons below |

- **Validation:** an invalid policy, or a policy on a non-BATCH session, is rejected with 400.
- **Delay before retry `n`:**
  - `fixed`: `delay`.
  - `exponential`: `min(delay * 2**n, max_delay)`, plus up to 25% jitter. The jittered delay can exceed `max_delay`.

| Retriable reasons (allowed in `when`) | Never retried |
|---|---|
| `task-failed`, `task-timeout`, `abnormal-termination` (the container died, including an out-of-memory kill of the container and an external `docker kill`), `exceeded-max-retries` (startup gave up), `preempted-by-scheduler` (preemption in terminate mode) | `user-requested`, `pending-timeout`, `idle-*`, any forced termination, any other reason, a NULL reason |

Each retriable reason uses up one attempt of `max_retries`.

### 3.2 Retry decision

The decision runs at the promotion to TERMINATED. By then every kernel is terminal and the batch result for the attempt has arrived, so the attempt record is complete when it is written.

```
RUNNING ─(batch fails / container dies / startup gives up)─▶ TERMINATING (status_info = reason)
TERMINATING ─all kernels terminal─▶ retriable?
    yes ─▶ RESCHEDULING  (attempt row, callback will_retry=true, retry_attempt += 1, retry_next_attempt_at set)
            └─ RescheduleSessionsLifecycleHandler ─▶ PENDING ─▶ held until retry_next_attempt_at ─▶ …
    no  ─▶ TERMINATED    (attempt row, callback will_retry=false)
```

A session is retriable only when all of these hold:

- it is BATCH and has a `retry_policy`;
- its `status_info` is in `when`;
- `retry_attempt < max_retries`;
- `terminate_requested_at` is NULL.

| Contract | |
|---|---|
| **One handler, one lock** | A lifecycle handler replaces the `promote-to-terminated` promotion, because a `PromotionSpec` has only one `success_status`. It shares `LOCKID_SOKOVAN_TARGET_TERMINATING` with `TerminateSessionsLifecycleHandler`. Sessions without a policy go to TERMINATED and run the TERMINATED hook as before |
| **One transaction, compare-and-set** | One transaction writes the status move, the attempt row, `retry_attempt += 1`, the reset of `result` to UNDEFINED, and `retry_next_attempt_at`. It is guarded by `status = TERMINATING AND retry_attempt = N AND terminate_requested_at IS NULL`. A replica that loses the race, or a terminate that lands first, leaves it nothing to do |
| **Every final path finishes the attempt** | The decision handler, the forced termination path and the pending-session cancel all use one shared step. It writes the final attempt row when that attempt ran, and sends the final callback |
| **Re-queue is guarded** | `RescheduleSessionsLifecycleHandler` moves a session to PENDING only while it is RESCHEDULING, so a terminate that lands first is kept. This also fixes the same race in preemption reschedule mode |
| **Dependents** | `DependenciesValidator` requires TERMINATED + SUCCESS, so dependents wait for the final attempt |
| **Per-attempt clocks** | `batch_timeout` and the session-lifetime idle checker restart with each attempt. Priority carries over, including any DEPRIORITIZING decrements |
| **Cluster sessions** | A retry re-runs every kernel. `KernelGroup.failure_policy` is not enforced yet and has no effect on the decision |

### 3.3 User terminate wins

A user-initiated terminate on a session with a policy sets `terminate_requested_at`; `status_info` keeps the attempt's reason. Non-user callers of `mark_sessions_for_termination` (the batch result, idle checks, preemption) do not set it.

| Status when the user terminates | Outcome |
|---|---|
| RUNNING | TERMINATING, then TERMINATED. The attempt row is written; the callback has `will_retry: false` |
| TERMINATING | Same as RUNNING: the compare-and-set rejects the retry |
| RESCHEDULING | TERMINATING, then TERMINATED. No attempt row, because the attempt never ran. The callback is `cancelled` |
| PENDING, waiting for `retry_next_attempt_at` | CANCELLED. No attempt row; the callback is `cancelled` |
| Any status, forced | TERMINATED. The attempt row is written if the attempt ran; the callback has `will_retry: false` |

### 3.4 Prerequisites

| # | Change | Why |
|---|---|---|
| P1 | Every transition to TERMINATING records the reason of the failure that caused it:<br>- `detect-termination` writes `abnormal-termination`<br>- `start-sessions` and `check-precondition` give-up write `exceeded-max-retries`<br>- `sweep-sessions` keeps `pending-timeout`<br>The move to RUNNING applies only to a session that is still starting | The coordinator's transitions write no reason today, and the move to RUNNING clears `status_info`. A fast batch result can mark the session TERMINATING before the late RUNNING write lands and overwrites it |
| P2 | A session that is waiting for `requested_starts_at`, `retry_next_attempt_at` or an unmet dependency is reported to the scheduler as skipped, not as failed | A validation failure counts toward `max_retry_count`. A waiting session is therefore moved to DEPRIORITIZING and loses 10 priority every budget cycle. This already affects reserved batch sessions |
| P3 | `pending_timeout` is measured from the latest entry into PENDING | It is measured from `created_at`, so a re-queued session would be reported as `pending-timeout` on its first sweep |
| P4 | The re-queue tears down the volatile network and records the failed agents, so the next attempt ranks those agents last | Network names derive from the session id, so a re-queued session would collide with or leak its previous network. This already affects preemption reschedule mode |
| P5 | The agent echoes `retry_attempt` in the batch result. The manager accepts a result only for the current attempt and only in a non-terminal status. That result sets `status_info` even when the session is already TERMINATING with `abnormal-termination`. The agent sends −1 in place of a missing exit code | Kernel rows are reused across attempts, so a late result from an earlier attempt could end the next one. The batch result also races container-death detection to mark TERMINATING, and the batch reason should win. A missing exit code fails event validation, so no result is sent and the session stays RUNNING |

These failures never reach the decision, and none of them is retried:

- an image-pull failure that cancels every kernel ends CANCELLED;
- a lost agent leaves its sessions RUNNING;
- a session expired to TERMINATING before any kernel got an agent never reaches the promotion.

### 3.5 Attempt record

`session_attempts` holds one row per attempt that ran:

| Column | |
|---|---|
| `session_id`, `attempt` | Primary key. `attempt` is the value of `retry_attempt` during the run |
| `status_info`, `result`, `status_data` | The attempt's reason, result and error payload |
| `exit_code` | Taken from the batch result event. −1 means unknown, −2 means batch timeout, NULL means no result arrived |
| `started_at`, `terminated_at` | The attempt's own timestamps, which `status_history` cannot keep |
| `agent_ids` | One per kernel |

With `max_retries: 3`, the runs are attempts 0 to 3. A non-NULL `retry_next_attempt_at` tells a retry re-queue apart from a preemption reschedule.

### 3.6 Callback contract

For a session with a policy, the callbacks are sent by the shared final step (§3.2) after its transaction commits; `handle_batch_result` no longer sends them. The existing payload fields are unchanged, and three are added:

| Field | |
|---|---|
| `attempt` | The index of the finished attempt |
| `will_retry` | `true` when the session went to RESCHEDULING |
| `exit_code` | From the attempt row |

- **`event` values:**
  - `success`: the attempt's result is SUCCESS.
  - `failure`: any other finished attempt, including one whose result is UNDEFINED.
  - `cancelled`: the session ended between attempts. `attempt` is the last attempt that ran.
- **Final callback:** each session with a policy gets exactly one final callback, either `will_retry: false` or `cancelled`.
- **Sessions without a policy:** callbacks are unchanged.

## 4. Migration / Compatibility

- **Additive.** Sessions without `retry_policy` behave as before, except for the bug fixes in P1–P5.
- **Status sequence:** a session with a policy can go TERMINATING → RESCHEDULING → PENDING → … with the same id. Consumers treat {TERMINATED, CANCELLED} as final, and read `will_retry` and `cancelled`.
- **Narrower than caller retry:** callers that retry every non-SUCCESS result today lose retries for `pending-timeout`, `idle-*`, user terminations and image-pull failures.
- **Rolling upgrade:**
  - Operators turn on `session.retry-policy.enabled` after every manager replica runs this version. Until then no session carries a policy, so an older replica never acts on a policy or sends an old-format callback for one.
  - Clients detect support from the policy echoed by enqueue (REST), or from the schema (GraphQL).
- **Downgrade:** turn the flag off first. Sessions already in RESCHEDULING continue as a plain reschedule.
- **Out of scope:** callers keep handling these themselves:
  - failures before a session exists (enqueue rejected, mount resolution);
  - a fresh scratch folder for each attempt;
  - re-reading the configuration at retry time. Mounts, environment and image are fixed at enqueue.

## 5. Implementation Plan

1. **Prerequisites P1–P5**, each mergeable on its own.
2. **API:** `retry_policy` on every enqueue route, the SDK and the CLI, behind the config flag. Storage only.
3. **Sokovan:** the decision handler, the new columns, `session_attempts`, the shared final step and the user-terminate rule.
4. **Exposure:** the read fields and the callback contract.

## 6. Decision Summary

| Decision | Alternative rejected | Rationale |
|---|---|---|
| Re-queue the same session | A new session per attempt, with lineage | A stable id for callbacks, dependencies and watchers; the name index needs no change |
| Decide at the promotion to TERMINATED | Decide wherever TERMINATING is marked | Every kernel is terminal and the batch result has arrived, so the attempt record is complete. There is one decision site |
| `when` takes `KernelLifecycleEventReason` values | New failure classes; the names `on`, `trigger` or `retry_on` | They are the same strings users see in `status_info`. `when` matches GitLab CI's `retry.when`, and YAML 1.1 parses a bare `on` key as `true` |
| BATCH sessions only | Every session type | Only batch sessions have a result. Inference replicas are replaced by deployment scaling (#9806) |
| A separate `terminate_requested_at` | Overwriting `status_info` | The compare-and-set can check it, and the attempt keeps its real reason |
| New columns for the attempt index and the next attempt time | Reusing `requested_starts_at`, or counting attempt rows | `requested_starts_at` is never overwritten after enqueue. A counter guarded by compare-and-set avoids lost updates |
| Attempt fields also on `ComputeSessionNode` | `SessionV2` only | FastTrack polls `compute_session_list`, and the WebUI session pages read `ComputeSessionNode`. Polling is the only way to recover from a lost callback |
| A config flag | Accepting the field as soon as one replica supports it | During a rolling upgrade, an older replica would otherwise terminate a session that has a policy, or send it an old-format callback |
| No resource-group default policy | `DefaultSessionOptions.retry_policy` | Can be added later, next to `handler_options` |

## 7. Open Questions

- Does a session waiting for `retry_next_attempt_at` count toward pending-session limits? The limit is checked only at enqueue, and a re-queue does not pass through enqueue.
- Should image-pull failures be retried? That would require the all-kernels-cancelled path to go through TERMINATING.

## 8. References

- [BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md): need_retry, expired, give_up and promotions
- [BEP-1055](BEP-1055-preemption-scheduler-mechanics.md): preemption reschedule mode. That BEP states there is no separate RESCHEDULING state, but the code has one (`RescheduleSessionsLifecycleHandler`)
- [BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md): preemption of low-priority sessions
