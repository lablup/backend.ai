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
| ✅ | Batch sessions accept `batch_timeout` and `starts_at` (stored as `requested_starts_at`) at enqueue:<br>- REST v1 `/session/_/create` and `_/create-from-template`: top-level fields<br>- REST v2 `/v2/sessions/enqueue`: `BatchConfigInput`<br>- GraphQL v2 `enqueueSession`: `SessionBatchConfigInput`<br>`_/create-cluster` has no batch fields |
| ✅ | `PATCH /session/{name}` (restart) returns 501 |
| ✅ | REST v1 and v2 ignore unknown request fields. GraphQL v2 rejects them |
| ✅ | `GET /` is public and returns the API and manager versions |
| ➕ | `retry_policy` next to `batch_timeout` on every route above except `_/create-cluster`, plus the Python SDK and the CLI. REST v1 also accepts the `retryPolicy` alias, as it does for `batchTimeout` |
| ➕ | The accepted policy is echoed in the enqueue response:<br>- REST v1: a `retryPolicy` key<br>- REST v2: `SessionNode.lifecycle`<br>- GraphQL: `SessionV2` |
| ➕ | `retry_policy` (typed), `attempt`, `retry_count`, `retry_next_attempt_at` and `attempts` (a list of attempt records) appear on `SessionV2.lifecycle`, the legacy `ComputeSessionNode` and `ComputeSession` (which `compute_session_list` returns), and the REST session info. `agent_ids` inside `attempts` follows the visibility rule that applies to the session's agent fields |
| ➕ | Shared (etcd) manager config `session.retry-policy.enabled`, default `false`. While it is off, enqueue rejects a `retry_policy` with 400 and error type `https://api.backend.ai/probs/retry-policy-disabled`. While it is on, `GET /` lists `retry-policy` in a new `features` array |

### 2.2 DB

| | Item |
|---|---|
| ✅ | `sessions.options` holds `SessionStoredOptions`, frozen at enqueue |
| ✅ | `sessions.status_info` holds the reason passed to `mark_sessions_for_termination`, and the promotion to TERMINATED keeps it |
| ✅ | Only `SessionSuccess/FailureAnycastEvent` carries the batch exit code (−2 means batch timeout), and `handle_batch_result` drops it. The kernel's `status_data.kernel.exit_code` is −1 or null, because no kernel termination event passes a real code |
| ✅ | `status_history` is a map keyed by status, so a status repeated by a later attempt overwrites the earlier timestamp |
| ✅ | Kernel rows are reused when a session is re-queued |
| ➕ | `SessionStoredOptions.retry_policy`, immutable after enqueue |
| ➕ | `sessions.attempt` (int, default 0): index of the current run, or of the next run while the session is RESCHEDULING or PENDING. It increases on every re-queue, whether caused by a retry or by preemption |
| ➕ | `sessions.retry_count` (int, default 0): retries used, compared with `max_retries` |
| ➕ | `sessions.retry_next_attempt_at` (timestamptz, nullable): the earliest scheduling time of the next run. Set when a retry re-queues the session; cleared when the run is placed on agents. `requested_starts_at` is untouched |
| ➕ | `sessions.terminate_requested_at` (timestamptz, nullable): set by a user terminate (§3.3) |
| ➕ | A `session_attempts` table (§3.5) |

### 2.3 Sokovan

| | Item |
|---|---|
| ✅ | `promote-to-terminated` (`CHECK_TERMINATING_PROGRESS`) moves a TERMINATING session to TERMINATED once every kernel is terminal. It then runs `TerminatedTransitionHook`, which tears down the network. Promotions take no lock |
| ✅ | `RescheduleSessionsLifecycleHandler` returns a RESCHEDULING session to PENDING with the same id and config, by resetting the kernels and then the session as two separate writes. Today only BEP-1055 preemption in reschedule mode writes RESCHEDULING |
| ✅ | `HandlerOptions.max_retry_count` (default 5) bounds every lifecycle handler's repeated failures. None of these budgets re-runs a session that already reached RUNNING |
| ➕ | A handler that replaces `promote-to-terminated` and decides the retry (§3.2), plus the prerequisites in §3.4 |

### 2.4 Callbacks

| | Item |
|---|---|
| ✅ | `callback_url` receives `success` or `failure` (the event name without its `session_` prefix), and only from `handle_batch_result`. The payload is read from the session row. Delivery is one POST with no retry and no ordering |
| ➕ | For sessions with a policy, the callback contract in §3.6 |

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
| `when` | list of `KernelLifecycleEventReason` | `[task-failed, task-timeout, abnormal-termination]` | non-empty, unique, and taken from the "Allowed in `when`" column below |

- An invalid policy, or a policy on a non-BATCH session, is rejected with 400.
- **Delay before the retry with index `n`:** `n` is `retry_count` before the retry, so the first retry uses `n = 0`.
  - `fixed`: `delay`.
  - `exponential`: `min(delay * 2**n, max_delay)`.
  - Either way, up to 25% jitter is added afterwards, so the result can exceed `max_delay`.

| Allowed in `when` | Never retried |
|---|---|
| `task-failed` | `user-requested` |
| `task-timeout` | `pending-timeout` |
| `abnormal-termination`: a container died, including an out-of-memory kill of the container and an external kill | `idle-*` |
| `exceeded-max-retries`: startup gave up | `agent-resource-group-changed` |
| `failed-to-create`: image pull failed (§3.4 P7) | `killed-by-event` |
| `preempted-by-scheduler`: preemption in terminate mode | Any forced termination, any other reason, or a NULL reason |

- Each retry triggered by a reason in `when` increases `retry_count`.
- Preemption in terminate mode uses up a retry. Preemption in reschedule mode re-queues the session without one.

### 3.2 Retry decision

A new lifecycle handler replaces `promote-to-terminated`. A promotion cannot do the job, because it has a single `success_status` and takes no lock.

The handler owns its own status write, the TERMINATED hook, the scheduling history row, the status broadcast, and the trigger for the next scheduling pass. Sessions without a policy go to TERMINATED exactly as before.

```
RUNNING ─(batch fails / container dies / startup gives up)─▶ TERMINATING (status_info = reason)
TERMINATING ─all kernels terminal─▶ retriable?
    yes ─▶ RESCHEDULING ─(§3.4 P4)─▶ PENDING ─▶ held until retry_next_attempt_at ─▶ placed …
    no  ─▶ TERMINATED  (TERMINATED hook runs)
```

A session is retriable when all of these hold:

- it is a BATCH session with a `retry_policy`;
- its `status_info` is in `when`;
- `retry_count < max_retries`;
- `terminate_requested_at` is NULL.

The decision uses the batch result if it has arrived. A container that dies sends no batch result at all.

**Transaction.** The handler locks the session row, reads it and writes both branches in one transaction:

- **Guard (both branches):** `status = TERMINATING AND attempt = N`. A retry also requires `terminate_requested_at IS NULL`.
- **Retry branch:** writes RESCHEDULING, the attempt row, `attempt + 1`, `retry_count + 1` and `retry_next_attempt_at`, and resets `result` and `status_data`.
- **Terminate branch:** writes TERMINATED and the attempt row.
- **Conflicts:** a guard that matches no row, or a conflict on the attempt row's primary key, means another path already ended the attempt, and the handler does nothing.

| Contract | |
|---|---|
| **Dependents** | `DependenciesValidator` requires TERMINATED + SUCCESS, so dependents wait for the final attempt |
| **Per-run timers** | `batch_timeout` and the session-lifetime idle checker restart with each run. Priority carries over, including DEPRIORITIZING decrements |
| **Cluster sessions** | A retry re-runs every kernel. `KernelGroup.failure_policy` is not enforced yet and has no effect |

### 3.3 User termination

A user terminate on a session with a policy sets `terminate_requested_at` in every non-terminal status, TERMINATING included. In TERMINATING the call is reported as a success; today it is skipped. `status_info` is not overwritten in TERMINATING. Termination by the batch result, idle checks or preemption does not set `terminate_requested_at`.

A run **was placed** once its kernels were assigned agents. Only placed runs get an attempt row.

| Status at a user terminate | Non-forced | Forced |
|---|---|---|
| PENDING, RESERVED, DEPRIORITIZING (run not placed) | CANCELLED | CANCELLED |
| SCHEDULED … RUNNING, PREEMPTED (run placed) | TERMINATING → TERMINATED, terminate branch | TERMINATED |
| TERMINATING | Guard rejects the retry → TERMINATED | TERMINATED |
| RESCHEDULING | TERMINATING → TERMINATED | TERMINATED |

The final callback for each row is in §3.6.

### 3.4 Prerequisites

| # | Change | Why |
|---|---|---|
| P1 | The coordinator's transitions to TERMINATING write the reason of the failure that caused them: `detect-termination` writes `abnormal-termination`, and the `start-sessions` and `check-precondition` give-ups write `exceeded-max-retries`. The move to RUNNING applies only to a session that is still starting | The coordinator writes no reason today. The batch is triggered before the RUNNING write, so a fast batch result can mark TERMINATING and then be reverted to RUNNING with `status_info` cleared |
| P2 | A session waiting for `requested_starts_at`, `retry_next_attempt_at` or an unmet dependency is reported to the scheduler as skipped, not failed | A validation failure counts toward `max_retry_count`, so a waiting session is moved to DEPRIORITIZING and loses 10 priority every budget cycle. Reserved batch sessions are affected today |
| P3 | `pending_timeout` is measured from the latest of: the entry into PENDING, `retry_next_attempt_at` and `requested_starts_at` | It is measured from `created_at`. When an operator sets a `sweep-sessions` timeout, a re-queued session would be reported as timed out as soon as it is re-queued |
| P4 | The re-queue resets the kernels and moves the session to PENDING in one transaction, guarded by `status = RESCHEDULING`. It tears down the volatile network and records the failed agents, so the next run ranks them last | A terminate that lands between today's two writes leaves a TERMINATING session whose kernels have no agent, which never ends. Network names derive from the session id, so a re-queued session collides with or leaks its previous network. Preemption in reschedule mode is affected today |
| P5 | The manager passes `attempt` to the agent in the kernel's `internal_data`. The agent keeps it with the kernel across restarts and includes it in every kernel termination event and batch result. The manager ignores an event whose `attempt` differs from `sessions.attempt`. A batch result for the current attempt sets `status_info` even when `detect-termination` already marked TERMINATING. The agent sends −1 in place of a missing exit code | Kernel rows are reused, so a late event from an earlier run (for example from an agent that comes back) would end the next run. A missing exit code fails event validation, so no result is sent and the session stays RUNNING |
| P6 | A session that expires to TERMINATING (`schedule-sessions`, `sweep-sessions`) before any of its kernels has an agent ends CANCELLED, with the failure's reason | Such a session never reaches the promotion: the terminator skips kernels that have no agent, so it stays TERMINATING forever. This affects every session today |
| P7 | For a session with a policy, an image-pull failure marks the session TERMINATING with `failed-to-create`, in the same transaction that cancels the kernels | Today a full cancel ends the session CANCELLED directly, while a partial cancel reaches `detect-termination` and becomes `abnormal-termination`. With P7 both reach the retry decision with one reason |

A lost agent leaves its sessions RUNNING. That is not detected today, and this BEP does not change it.

### 3.5 Attempt record

`session_attempts` holds one row per run that was placed:

| Column | |
|---|---|
| `session_id`, `attempt` | Primary key |
| `status_info`, `result`, `status_data`, `status_history` | The run's reason, result, error payload and status timeline |
| `exit_code` | From the batch result: −1 unknown, −2 batch timeout, NULL when no result arrived |
| `started_at` | Entry into RUNNING; NULL if the run never got there |
| `terminated_at` | When the run ended |
| `agent_ids` | Per kernel |

### 3.6 Callback contract

For a session with a policy, `handle_batch_result` stops sending callbacks. Callbacks are sent by the paths in the table below, after their transaction commits, and only for rows their guarded update moved.

| Path | Session ends in | `event` | `attempt` | `will_retry` |
|---|---|---|---|---|
| Retry decision, retry branch | RESCHEDULING | `failure` | the finished run | `true` |
| Retry decision, terminate branch | TERMINATED | `success` if the run's result is SUCCESS, otherwise `failure` | the finished run | `false` |
| Preemption, reschedule mode | RESCHEDULING | `failure` | the preempted run | `true` |
| Forced termination of a placed run | TERMINATED | `failure` | the run | `false` |
| User termination while the next run is not yet placed (RESCHEDULING, PENDING, RESERVED, DEPRIORITIZING), forced or not | TERMINATED from RESCHEDULING, CANCELLED otherwise | `cancelled` | the last placed run, or null | `false` |
| P6 expiry before placement | CANCELLED | `cancelled` | the last placed run, or null | `false` |

- **Payload:** for a session with a policy, `result`, `status_info`, `status_data`, `status_history`, `started_at`, `terminated_at` and `exit_code` come from the attempt row, not the session row. `attempt` and `will_retry` are added. The other existing fields are unchanged.
- **Delivery** is at most once and unordered. Consumers dedupe on `(session_id, attempt, event)`. They recover a lost callback by polling `attempts` and `attempt` on the session.
- **Sessions without a policy:** callbacks are unchanged.

## 4. Migration / Compatibility

- **Additive.** Sessions without `retry_policy` behave as before, apart from the bug fixes in P1–P6.
- **Status sequence:** a session with a policy can go TERMINATING → RESCHEDULING → PENDING → … on the same id. Consumers treat {TERMINATED, CANCELLED} as final.
- **Narrower than caller retry.** Callers that retry every non-SUCCESS result lose retries for these:
  - `pending-timeout`, `idle-*` and user terminations;
  - operator actions such as `agent-resource-group-changed`;
  - sessions on a lost agent;
  - failures before a session exists (enqueue rejected, mount resolution).
- **Enabling.** Operators turn the flag on after every manager replica and every agent runs this version.
  - The flag gates enqueue only. A session that already carries a policy is retried whatever the flag says.
  - Events without `attempt` come only from older agents, and are accepted as today.
- **Downgrade.** Turn the flag off and wait until no non-terminal session carries a policy, then downgrade.
- **Out of scope; callers keep these:**
  - a fresh scratch folder per run;
  - re-reading configuration at retry time.

  Mounts, environment and image are fixed at enqueue.

## 5. Implementation Plan

1. **Prerequisites P1–P7.** Each is mergeable on its own.
2. **API.** `retry_policy` on the enqueue routes, the SDK and the CLI, behind the flag. Storage only.
3. **Sokovan.** The handler that replaces `promote-to-terminated`, the new columns, `session_attempts`, the user-termination rule and the callback paths.
4. **Exposure.** The read fields, `features` on `GET /`, and the payload changes.

## 6. Decision Summary

| Decision | Alternative rejected | Rationale |
|---|---|---|
| Re-queue the same session | A new session per attempt, with lineage | A stable id for callbacks, dependencies and watchers. The name index needs no change |
| Decide at the promotion to TERMINATED | Decide wherever TERMINATING is marked | Every kernel is terminal there, so the attempt row is complete. One decision site |
| `when` takes `KernelLifecycleEventReason` values | New failure classes; naming the field `on`, `trigger` or `retry_on` | The same strings users see in `status_info`. YAML 1.1 parses a bare `on` key as `true` |
| BATCH sessions only | Every session type | Only batch sessions have a result. Inference replicas are replaced by deployment scaling (#9806) |
| `terminate_requested_at` | Overwriting `status_info` | The guard can check it, and the attempt keeps its real reason |
| Separate `attempt` and `retry_count` | One counter | Reschedule-mode preemption starts a new run without using up a retry |
| Attempt fields on `SessionV2`, `ComputeSessionNode` and `ComputeSession` | `SessionV2` only | FastTrack polls `compute_session_list`, and the WebUI session pages read `ComputeSessionNode`. Polling recovers lost callbacks |
| A shared config flag that gates enqueue | Accepting the field as soon as one replica supports it | Every manager and agent must handle a policy session before any exists |
| No resource-group default policy | `DefaultSessionOptions.retry_policy` | It can be added later next to `handler_options` |

## 7. Open Questions

- Does a session waiting for `retry_next_attempt_at` count toward pending-session limits? The limit is checked only at enqueue, and a re-queue does not go through enqueue.

## 8. References

- [BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md): need_retry, expired, give_up and promotions
- [BEP-1055](BEP-1055-preemption-scheduler-mechanics.md): preemption reschedule mode, implemented by `RescheduleSessionsLifecycleHandler`
- [BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md): preemption of low-priority sessions
