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

A batch session that fails is never run again. This BEP adds a per-session **retry policy**. After a retriable failure, the manager re-queues **the same session** with a backoff delay and records each attempt.

Callers that retry today enqueue a new session for every attempt, so they cannot see why the session ended, and the session id changes on every attempt.

## 2. Current State & Scope, by Area

### 2.1 API

| | Item |
|---|---|
| ✅ | Batch sessions accept `batch_timeout` and `starts_at` (stored as `requested_starts_at`) at enqueue:<br>- REST v1 `POST /session` and `_/create-from-template`, as top-level fields with camelCase aliases<br>- REST v2 `/v2/sessions/enqueue`, in `BatchConfigInput`<br>- GraphQL v2 `enqueueSession`, in `SessionBatchConfigInput`<br>`_/create-cluster` has no batch fields |
| ✅ | REST v1 and v2 ignore unknown request fields. GraphQL v2 rejects them |
| ✅ | `GET /` is public and returns the API and manager versions |
| ➕ | `retry_policy` next to `batch_timeout` on each of those routes except `_/create-cluster`, plus the Python SDK (from the release that ships this BEP) and the CLI. REST v1 also accepts `retryPolicy` |
| ➕ | **Enqueue echo.** The accepted policy is returned in:<br>- REST v1: the `retryPolicy` key. On the reuse path (`created: false`) it shows the stored policy<br>- REST v2: `SessionNode.lifecycle.retry_policy` (`SessionLifecycleInfoGQLDTO`)<br>- GraphQL: `SessionV2.lifecycle.retryPolicy`<br>A missing echo means the policy was not applied, for example by an older manager |
| ➕ | **Read fields:** `retry_policy`, `attempt` (Int, 0-based), `retry_count` (Int), `retry_next_attempt_at` (DateTime, nullable) and `attempts`. `attempts` is a list of the §3.5 records, ordered by `attempt`; its `agent_ids` follow the session's agent-visibility rule. Where they appear:<br>- GraphQL v2 `SessionV2.lifecycle`: typed `SessionRetryPolicy` and `[SessionAttempt!]!`<br>- Legacy `ComputeSessionNode` and `ComputeSession` (`compute_session_list`, `legacy_compute_session_list`): `JSONString`, the same as `status_history`<br>- REST session info: objects |
| ➕ | **Feature flag:** shared (etcd) manager config `session.retry-policy.enabled`, default `false`.<br>- While it is off, enqueue rejects a `retry_policy` with 400, error type `https://api.backend.ai/probs/retry-policy-disabled`, and `error_code` `retry-policy-disabled` (GraphQL: `extensions.code`).<br>- While it is on, `GET /` lists `retry-policy` in a new `features` array. That array is a hint; the enqueue echo or the 400 is authoritative |

### 2.2 DB

| | Item |
|---|---|
| ✅ | `sessions.options` holds `SessionStoredOptions`, frozen at enqueue |
| ✅ | `sessions.status_info` holds the reason passed to `mark_sessions_for_termination`. The promotion to TERMINATED keeps it |
| ✅ | Only `SessionSuccess/FailureAnycastEvent` carries the batch exit code; −2 means batch timeout. `handle_batch_result` drops it, and `set_session_result` stores only `result` |
| ✅ | `status_history` is a map keyed by status. `starts_at` is cleared when a session returns to PENDING. Kernel rows, including `container_log`, are reused when a session is re-queued |
| ✅ | Session status writes filter by session id. `mark_sessions_status` also excludes terminal statuses, and nothing checks the status the writer read |
| ➕ | `SessionStoredOptions.retry_policy`, immutable after enqueue |
| ➕ | **`sessions.attempt`** (int, default 0): index of the current attempt. It increases only when a session returns to PENDING after one of its kernels was assigned an agent (§3.4 P4) |
| ➕ | **`sessions.retry_count`** (int, default 0): retries used, compared with `max_retries` |
| ➕ | **`sessions.retry_next_attempt_at`** (timestamptz, nullable): the earliest scheduling time of the next attempt. Set by a retry; cleared when a kernel is assigned an agent or the session reaches a terminal status. `requested_starts_at` is untouched |
| ➕ | **`sessions.exit_code`** (int, nullable): the current attempt's batch exit code. Reset on re-queue |
| ➕ | **`sessions.terminate_requested_at`** (timestamptz, nullable): set by a user terminate (§3.3) |
| ➕ | A `session_attempts` table (§3.5) |

### 2.3 Sokovan

| | Item |
|---|---|
| ✅ | `promote-to-terminated` (`CHECK_TERMINATING_PROGRESS`) promotes a TERMINATING session once every kernel is terminal. It runs `TerminatedTransitionHook` (network teardown) and then writes TERMINATED. Promotions have a single `success_status`, and the hook is chosen by target status |
| ✅ | `RescheduleSessionsLifecycleHandler` returns a RESCHEDULING session to PENDING with the same id and config, using two transactions: a kernel reset, then `mark_sessions_status(PENDING)`. Today only BEP-1055 preemption in reschedule mode writes RESCHEDULING |
| ✅ | `start-sessions`, `check-precondition` and `release-reserved-sessions` also return sessions to PENDING with their kernels reset |
| ✅ | The terminator skips kernels that have no agent |
| ➕ | A handler that replaces `promote-to-terminated` and decides whether to retry (§3.2), plus the prerequisites in §3.4 |

### 2.4 Callbacks

| | Item |
|---|---|
| ✅ | `callback_url` receives `success` or `failure`, sent only by `handle_batch_result`. The payload is `type`, `event`, `session_id`, `when`, `status_history`, `result` and `status_data`, all read from the session row. Delivery is one POST, with no retry and no ordering. Five other call sites exist, but nothing emits their events |
| ➕ | The §3.6 contract for sessions with a policy |

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
| `delay` | int, seconds | 10 | 1..86400 |
| `backoff` | enum `RetryBackoff` | `fixed` | `fixed`, `exponential` |
| `max_delay` | int, seconds | 300 | `delay`..86400 when `backoff` is `exponential`; ignored otherwise |
| `when` | list of `KernelLifecycleEventReason` | `[task-failed, task-timeout, abnormal-termination]` | Non-empty, unique, and only values from the list below |

- **Validation:** an invalid policy, or a policy on a session that is not BATCH, is rejected with 400.
- **Delay before retry `n`:** `n` is `retry_count` before the retry, so the first retry uses `n = 0`.
  - `fixed`: `delay`.
  - `exponential`: `min(delay * 2**n, max_delay)`.

  Either way, up to 25% jitter is then added.

**Allowed in `when`:**

| Reason | Meaning |
|---|---|
| `task-failed` | The batch exited with a non-zero code |
| `task-timeout` | The batch exceeded `batch_timeout` |
| `abnormal-termination` | A kernel died without a batch result. This includes an out-of-memory kill of the container, an external kill, and a container that failed to start |
| `exceeded-max-retries` | Startup gave up |
| `failed-to-create` | An image pull failed (P7) |
| `preempted-by-scheduler` | Preemption in terminate mode |

**Never retried:** every other reason, including `user-requested`, `pending-timeout`, `idle-timeout`, `idle-session-lifetime`, `idle-utilization`, `preempted-by-reservation`, `agent-resource-group-changed` and `killed-by-event`. Also never retried: any forced termination, and a NULL reason.

Each retry increases `retry_count`, so preemption in terminate mode uses up a retry. Preemption in reschedule mode re-queues the session without using one.

### 3.2 Retry decision

A lifecycle handler replaces the `promote-to-terminated` promotion. A promotion cannot branch: it has a single `success_status`, and its hook is chosen by the target status.

The handler owns its status write, the TERMINATED hook, the history row, the broadcast and the next scheduling trigger. Network teardown runs outside the database transaction. Sessions without a policy go to TERMINATED as before.

```
RUNNING ─(batch fails / kernel dies / startup gives up)─▶ TERMINATING (status_info = reason)
TERMINATING ─all kernels terminal─▶ retriable?
    yes ─▶ RESCHEDULING ─(P4: attempt += 1)─▶ PENDING ─▶ held until retry_next_attempt_at ─▶ …
    no  ─▶ TERMINATED
```

A session is **retriable** when all of these hold:

- it is BATCH and has a `retry_policy`;
- its `status_info` is in `when`;
- `retry_count < max_retries`;
- `terminate_requested_at` is NULL.

`status_info` at decision time decides. A batch result for the current attempt replaces `abnormal-termination` until the decision commits (P5).

**The decision transaction.** The handler locks the session row, reads it, and in one transaction:

- writes the attempt row for `attempt`;
- then takes one of two branches:
  - **retry:** RESCHEDULING, `retry_count + 1`, `retry_next_attempt_at`;
  - **terminate:** TERMINATED.

Both branches are guarded by `status = TERMINATING AND attempt = N` (P0). The retry branch also requires `terminate_requested_at IS NULL`. If the guard matches no row, the handler does nothing. If the attempt row already exists, it is kept and the status is still written.

| Contract | |
|---|---|
| Dependents | `DependenciesValidator` requires TERMINATED + SUCCESS, so dependents wait for the final attempt |
| Timers per attempt | `batch_timeout` and the session-lifetime idle checker restart with every attempt. Priority carries over, including DEPRIORITIZING decrements |
| Cluster sessions | A retry re-runs every kernel. `KernelGroup.failure_policy` is not enforced yet and has no effect |

### 3.3 User termination

A user terminate on a session with a policy is a single guarded write (P0). It sets `terminate_requested_at` in every non-terminal status. `status_info` is never overwritten in TERMINATING, whether the terminate is forced or not. Terminations by the batch result, idle checks or preemption do not set `terminate_requested_at`.

| Status at a user terminate | Non-forced | Forced |
|---|---|---|
| PENDING | CANCELLED (unchanged) | CANCELLED (unchanged) |
| RESERVED, DEPRIORITIZING, SCHEDULED … RUNNING, PREEMPTED | TERMINATING → decision → TERMINATED | TERMINATED; the forced path writes the attempt row and runs the TERMINATED hook (P8) |
| TERMINATING | The decision's guard refuses the retry → TERMINATED. The call is reported as a success (today it is skipped) | TERMINATED (P8) |
| RESCHEDULING | Only the flag is set. P4 then ends the session TERMINATED instead of re-queueing it | TERMINATED (P8) |

The WebUI disables Terminate in TERMINATING today, so it cannot use the TERMINATING row until that changes.

### 3.4 Prerequisites

| # | Change | Why |
|---|---|---|
| P0 | Every session status write is guarded by the status it read and, for a session with a policy, by `attempt`. This applies to the coordinator, every lifecycle handler, the repository's mark, cancel and force paths, and the stale-kernel sweep. A write that matches no row has no effect | Today writes filter by id alone. Concurrent writers, such as preemption, `detect-termination`, the sweep, a re-queue or a second replica, can overwrite a user terminate or a decision. For example, the re-queue overwrites a TERMINATING session with PENDING, and the session runs again. A late RUNNING write can leave a session RUNNING with TERMINATING kernels |
| P1 | Coordinator transitions to TERMINATING write the reason of the failure that caused them:<br>- `detect-termination` writes `abnormal-termination`<br>- the `start-sessions` and `check-precondition` give-ups write `exceeded-max-retries`<br>- `schedule-sessions` and `sweep-sessions` expiry write the failure's own reason | The coordinator writes no reason today |
| P2 | A session waiting for `requested_starts_at`, `retry_next_attempt_at` or an unmet dependency is reported to the scheduler as skipped, not failed | A validation failure counts toward `max_retry_count`, so a waiting session is moved to DEPRIORITIZING and loses 10 priority every budget cycle. This already affects reserved batch sessions |
| P3 | `pending_timeout` is measured from the latest of: entry into PENDING, `retry_next_attempt_at`, and `requested_starts_at` | It is measured from `created_at`, so when an operator configures the expiry, a re-queued session is timed out as soon as it is re-queued |
| P4 | **Every return to PENDING after a kernel was assigned an agent** goes through one guarded transaction. It covers re-queue from RESCHEDULING, and the `start-sessions`, `check-precondition` and `release-reserved-sessions` re-queues. The transaction:<br>- writes the attempt row for `attempt` if the decision has not;<br>- increments `attempt`;<br>- resets the kernels and the session's `result`, `exit_code`, `status_data` and `status_history`;<br>- moves the session to PENDING.<br>If `terminate_requested_at` is set, the session ends TERMINATED instead. Before the transaction, it tears down the volatile network and records the failed agents | Today the re-queue is two writes, and network names derive from the session id. Without one place that increments `attempt`, a reschedule-mode preemption either counts twice or leaves its own teardown events ignored |
| P5 | The agent includes `attempt` (given at kernel creation) in every kernel lifecycle event, batch result and log sync, and keeps it across restarts. The manager drops an event when either holds:<br>- its `attempt` differs from `sessions.attempt`;<br>- its source agent differs from the kernel row's agent (this also covers events sent without `attempt`).<br>The batch result writes `result`, `exit_code` and `status_info`, and marks TERMINATING, in one write guarded by `attempt` and a non-terminal status. The agent sends −1 when `execute_batch` has no exit code | Kernel rows are reused, so a late event from an earlier attempt or another agent would end or rewire the next attempt. Today, a missing exit code on `execute_batch` fails event validation and the session stays RUNNING |
| P6 | Marking a session TERMINATING cancels, in the same write, its kernels that have no agent | The terminator skips kernels without an agent. A session terminated or expired before placement, or terminated while DEPRIORITIZING, therefore stays TERMINATING forever. This affects every session today |
| P7 | An image-pull failure marks the session TERMINATING with `failed-to-create` in the transaction that cancels the kernels, and triggers `CHECK_TERMINATING_PROGRESS` | Today a full cancel ends the session CANCELLED in a separate transaction, while a partial cancel reaches `detect-termination` as `abnormal-termination` |
| P8 | Forced termination runs the TERMINATED hook and writes the attempt row and the final callback | It writes TERMINATED directly today, so the volatile network leaks and the attempt is not recorded |

A lost agent leaves its sessions RUNNING; this BEP does not change that.

### 3.5 Attempt record

`session_attempts` has one row for every attempt in which a kernel was assigned an agent:

| Column | |
|---|---|
| `session_id`, `attempt` | Primary key |
| `status_info`, `result`, `exit_code` | The attempt's reason, result and batch exit code. `exit_code` is NULL when no batch result arrived |
| `status_data`, `status_history` | The attempt's error payload and status timeline, as they stood at the end of the attempt |
| `started_at` | The session's `starts_at` when the attempt ended; NULL if it never reached RUNNING |
| `terminated_at` | When the attempt ended |
| `agent_ids` | Per kernel |

Container logs of earlier attempts are not kept. A consumer that needs them fetches the logs when it receives each callback.

### 3.6 Callback contract

For a session with a policy, `handle_batch_result` and the other five call sites send no callback. The paths in the table below send it after their transaction commits, and only for rows their guarded write moved.

| Path | Session status | `event` | `attempt` | `will_retry` |
|---|---|---|---|---|
| Decision, retry branch | RESCHEDULING | `failure` | the ended attempt | `true` |
| Decision, terminate branch | TERMINATED | `success` if the result is SUCCESS, otherwise `failure` | the ended attempt | `false` |
| P4 re-queue after reschedule-mode preemption | PENDING | `rescheduled` | the preempted attempt | `true` |
| P4 ending a session whose terminate was requested | TERMINATED | `cancelled` | null | `false` |
| P8 forced termination | TERMINATED | `cancelled` | the attempt whose row this path wrote, otherwise null | `false` |
| Cancel of a PENDING session | CANCELLED | `cancelled` | null | `false` |

- **No callback:** P4 re-queues by `start-sessions`, `check-precondition` and `release-reserved-sessions` send none. Their attempt rows appear in `attempts`.
- **Fields added** to the existing payload: `attempt` (Int, nullable), `will_retry` (Boolean), `retry_count` (Int), `retry_next_attempt_at` (ISO 8601, nullable), `status_info` (string), `started_at` and `terminated_at` (ISO 8601, nullable), `exit_code` (Int, nullable).
- **Where the values come from:**
  - When `attempt` is set, `result`, `status_info`, `status_data`, `status_history`, `started_at`, `terminated_at` and `exit_code` come from that attempt's row.
  - When `attempt` is null, they describe how the session ended: the ending reason, `result` UNDEFINED, `started_at` null, and `status_data` / `status_history` as `{}`.
- **Delivery** is at most once and unordered. Consumers dedupe on `(session_id, attempt, event)`, and recover a lost callback by polling `attempt`, `retry_count` and `attempts`.
- **Sessions without a policy:** callbacks are unchanged.

## 4. Migration / Compatibility

- **Behaviour changes for every session:**
  - P0 makes concurrent writers that lose a race have no effect.
  - P6 ends sessions that used to be stuck in TERMINATING; they now finish TERMINATED.
  - P7 ends full image-pull failures TERMINATED with `failed-to-create` instead of CANCELLED.
  - P8 tears down networks on forced termination.
- **Status sequence:** a session with a policy can go TERMINATING → RESCHEDULING → PENDING → … on the same id. Consumers treat {TERMINATED, CANCELLED} as final.
- **Narrower than retrying in the caller.** Callers that retry every result other than SUCCESS lose retries for:
  - the "never retried" reasons;
  - sessions on a lost agent;
  - failures before a session exists (enqueue rejected, mount resolution).
- **Client support detection:** a client sends `retry_policy` and checks the enqueue echo. A missing echo means the policy was not applied, which is what happens on a manager older than this BEP, because REST ignores unknown fields.
- **Enabling:** operators turn the flag on after every manager replica runs this version.
  - The scheduler places a session that has a policy only on an agent whose reported version supports P5.
  - The flag gates enqueue only. A session that already has a policy keeps being retried whatever the flag says.
- **Downgrade:**
  1. Turn the flag off.
  2. Wait until no non-terminal session has a policy.
  3. Downgrade. The schema downgrade drops `session_attempts` and the new columns.
- **Out of scope; callers keep these:**
  - a fresh scratch folder for each attempt;
  - re-reading configuration at retry time (mounts, environment and image are fixed at enqueue);
  - container logs of earlier attempts.

## 5. Implementation Plan

1. **Prerequisites P0–P8.** Each can be merged on its own. P0 comes first.
2. **API:** `retry_policy` on the enqueue routes, the SDK and the CLI, behind the flag. Storage only.
3. **Sokovan:** the decision handler, the new columns, `session_attempts` and the user-termination rule.
4. **Exposure:** the read fields, `features` on `GET /`, and the callback contract.

## 6. Decision Summary

| Decision | Alternative rejected | Rationale |
|---|---|---|
| Re-queue the same session | A new session per attempt, with lineage | A stable id for callbacks, dependencies and watchers; the name index needs no change |
| Decide at the promotion to TERMINATED | Decide wherever TERMINATING is marked | Every kernel is terminal there, so the attempt row is complete. One decision site |
| `when` takes `KernelLifecycleEventReason` values | New failure classes; naming the field `on`, `trigger` or `retry_on` | The same strings users see in `status_info`. YAML 1.1 parses a bare `on` key as `true` |
| BATCH sessions only | Every session type | Only batch sessions have a result. Inference replicas are replaced by deployment scaling (#9806) |
| Guard every status write (P0) | Guarding each racing writer as it is found | Each review round found another unguarded writer; one rule closes them all |
| `attempt` increases only in P4 | Increasing it on retry and on preemption separately | One place, after every kernel is terminal, so teardown events are never dropped and nothing counts twice |
| Separate `attempt` and `retry_count` | One counter | Reschedule-mode preemption starts a new attempt without using a retry |
| `terminate_requested_at` | Overwriting `status_info` | The guard can check it, and the attempt keeps its real reason |
| Attempt fields on `SessionV2`, `ComputeSessionNode` and `ComputeSession` | `SessionV2` only | FastTrack polls `compute_session_list` and the WebUI session pages read `ComputeSessionNode`. Polling recovers lost callbacks |
| A shared config flag that gates enqueue | Accepting the field as soon as one replica supports it | Every manager must handle a session with a policy before any such session exists |

## 7. Open Questions

- Does a session waiting for `retry_next_attempt_at` count toward pending-session limits? The limit is checked only at enqueue, and a re-queue does not pass through enqueue.

## 8. References

- [BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md): need_retry, expired, give_up and promotions
- [BEP-1055](BEP-1055-preemption-scheduler-mechanics.md): preemption reschedule mode, implemented by `RescheduleSessionsLifecycleHandler`
- [BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md): preemption of low-priority sessions
