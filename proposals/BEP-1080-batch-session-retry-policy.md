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
- Prior art: #9806, auto-restart of inference session containers (closed, not planned)

## 1. Goal

A batch session that fails is never run again. This BEP adds a per-session **retry policy**:

- After a retriable failure, the manager re-queues **the same session** with a backoff delay.
- Each attempt is recorded.
- The policy is accepted at enqueue time.

Callers that retry today, such as FastTrack, do it by enqueuing a new session for every attempt. That approach cannot see why the session ended, and it changes the session id on every attempt.

## 2. Current State & Scope, by Area

### 2.1 API

| | Item |
|---|---|
| ✅ | Batch sessions accept `batch_timeout` and `starts_at` (stored as `requested_starts_at`) at enqueue: REST v1 `/session/_/create*`, GraphQL v2 `enqueueSession` |
| ✅ | `PATCH /session/{name}` (restart) returns 501: "terminate the session and enqueue a new one" |
| ➕ | `retry_policy` on batch session enqueue (REST v1 create, GraphQL v2 `enqueueSession`, Python SDK, CLI); rejected for any other session type |
| ➕ | `retryPolicy`, `attempt` and an `attempts` connection on `SessionV2` |

### 2.2 DB

| | Item |
|---|---|
| ✅ | `sessions.options` holds `SessionStoredOptions`, frozen at enqueue; `handler_options` already lives there |
| ✅ | `sessions.result` (UNDEFINED / SUCCESS / FAILURE); `status_info` holds the reason given when the session was marked TERMINATING |
| ✅ | The batch exit code reaches the manager in `SessionSuccess/FailureAnycastEvent`, but `SessionRow.set_session_result` drops it (`# TODO: store exit code?`) |
| ➕ | `SessionStoredOptions.retry_policy` (JSONB, no column migration) |
| ➕ | A per-attempt record (§3.4) |

### 2.3 Sokovan

| | Item |
|---|---|
| ✅ | Per-phase retry budgets (`HandlerOptions.max_retry_count`, default 5) and need_retry / expired / give_up classification. They cover scheduling and startup only, never a session after RUNNING |
| ✅ | Every non-forced end of an active session converges on TERMINATING, then the `promote-to-terminated` promotion (`CHECK_TERMINATING_PROGRESS`) once all kernels are terminal |
| ✅ | `RescheduleSessionsLifecycleHandler` returns a RESCHEDULING session to PENDING with the same id, config and priorities. Today only BEP-1055 preemption (reschedule mode) feeds it |
| ✅ | `ReservedBatchSessionValidator` holds a batch session until `requested_starts_at` |
| ➕ | A retry decision in the `promote-to-terminated` transition (§3.2) |
| ➕ | A hold for a session that is not due yet, which must not use up the schedule handler's budget (§3.3) |
| ➕ | A reason stamped on the coordinator's expired and give_up transitions to TERMINATING. Today `_apply_transition` passes none, so a startup failure leaves no reason to classify |

### 2.4 Events

| | Item |
|---|---|
| ✅ | Session lifecycle events and `callback_url` deliver every status change |
| ➕ | A new `KernelLifecycleEventReason.RETRY_SCHEDULED` (`retry-scheduled`), carried on the move to RESCHEDULING |

## 3. Implementation Design

### 3.1 Policy

```yaml
retry_policy:
  max_retries: 3          # the session runs at most 1 + max_retries times
  delay_sec: 10
  backoff: fixed          # fixed | exponential
  max_delay_sec: 300      # cap for exponential
  retry_on: [EXIT_NONZERO, TIMEOUT, STARTUP, INFRA]   # default: all four
```

- **Delay before retry n (n starts at 0):**
  - `fixed`: `delay_sec`.
  - `exponential`: `min(delay_sec * 2**n, max_delay_sec)`, plus up to 25% random jitter.
- **No `retry_policy`:** behaviour is unchanged.

| Class | Session `status_info` when marked TERMINATING |
|---|---|
| `EXIT_NONZERO` | `task-failed` |
| `TIMEOUT` | `task-timeout` |
| `STARTUP` | The reason stamped on startup-phase expired / give_up transitions (§2.3 ➕) |
| `INFRA` | `abnormal-termination`, `agent-termination`, `container-not-found`, `stale-kernel`, `kernel-handler-failure` |
| Never retried | `user-requested`, `force-terminated`, `user-purged`, `task-cancelled`, `idle-*`, `pending-timeout`, any forced termination, and any reason not listed above |

### 3.2 Retry decision and core flow

The decision is made in exactly one place: the `promote-to-terminated` transition. By then every kernel is gone and `status_info` still holds the reason the session was marked TERMINATING for.

```
RUNNING ──(batch fails / kernel dies / startup gives up)──▶ TERMINATING
TERMINATING ──all kernels terminal──▶ retriable and attempts left?
    yes ─▶ RESCHEDULING (reason retry-scheduled; attempt recorded; result reset; not-before = now + delay)
            └─ RescheduleSessionsLifecycleHandler ─▶ PENDING ─▶ (held until not-before) ─▶ SCHEDULED …
    no  ─▶ TERMINATED (unchanged)
```

A session is retriable when all of these hold:

- its type is BATCH;
- its `retry_policy` is set;
- the reason maps to a class in `retry_on`;
- `attempt < max_retries`.

| Rule | Why |
|---|---|
| The same session is re-queued | The session id stays stable for `callback_url`, `session_dependencies` and external watchers. The per-user unique-name index never sees two live rows. TERMINATED stays final |
| The decision sits at TERMINATING → TERMINATED, not at each place that marks TERMINATING | Batch results, abnormal-termination detection and startup give-up all converge there, so the classification lives in one place |
| RESCHEDULING is reused | Kernel teardown and re-queueing already exist for preemption; this BEP adds no second path |
| `result` is reset to UNDEFINED on re-queue | `DependenciesValidator` requires TERMINATED + SUCCESS. A dependent keeps waiting until the final attempt and sees only its outcome |
| Preemption does not count as an attempt | BEP-1055 reschedule mode already re-queues a preempted session without going through TERMINATING |

### 3.3 Backoff hold

A re-queued session must not be scheduled before its not-before time.

- **The problem:** `ReservedBatchSessionValidator` already holds on `requested_starts_at`, but it raises a `SchedulingValidationError`. The provisioner records that as a scheduling **failure**, and after `max_retry_count` failures the schedule handler gives up and moves the session to DEPRIORITIZING (priority −10). With a 2 s tick and the default budget of 5, any backoff longer than about 10 s would deprioritize the retried session. This was read from the code, not reproduced.
- **The fix:** a session whose not-before time has not arrived is reported as **skipped**, which does not count toward the budget. Retry backoff and reserved batch sessions share this hold. If the reserved-batch path deprioritizes today, it is fixed by the same change.

### 3.4 Attempt record

One record per finished attempt:

- session id
- attempt number
- the reason (`status_info`)
- `result`
- the exit code
- `started_at` and `terminated_at`
- the agent ids

It is exposed as `SessionV2.attempts`. `SessionV2.attempt` is the current attempt number, starting at 0.

The exit code that `set_session_result` drops today (§2.2) is stored here for every attempt, including the final one.

## 4. Migration / Compatibility

- **Additive.** Sessions without `retry_policy` behave as before, and no stored data changes meaning.
- **New observable sequence for policy sessions:** TERMINATING → RESCHEDULING → PENDING. `callback_url` consumers that treat TERMINATING as the end must wait for TERMINATED instead.
- **Clients:** the WebUI gates its launcher fields on the manager version that ships this BEP. FastTrack keeps its own retry engine for older managers.

## 5. Implementation Plan

1. **Classification inputs:** stamp a reason on the coordinator's startup expired / give_up transitions, and store the batch exit code.
2. **API:** `retry_policy` on enqueue, stored in `SessionStoredOptions`, in REST v1, GraphQL v2, the SDK and the CLI. Nothing is enforced yet.
3. **Sokovan:** the retry decision in `promote-to-terminated`, the not-before hold as a skip, and the attempt record.
4. **Exposure:** `SessionV2.retryPolicy`, `attempt` and `attempts`, and the `retry-scheduled` reason on events and `callback_url`.

## 6. Decision Summary

| Decision | Alternative rejected | Rationale |
|---|---|---|
| Re-queue the same session | A new session per attempt, linked to the previous one | A stable id for every watcher; the name index and dependencies need no change |
| Decide at TERMINATING → TERMINATED | Decide at each place that marks TERMINATING | One decision point; the reason is already on the row |
| BATCH sessions only | Every session type | Only batch sessions have a success or failure result. Inference replicas are replaced by deployment scaling (#9806 closed) |
| `max_retries` (retries, not runs) | `max_attempts` | Avoids the off-by-one that `max_attempts` invites |
| No per-policy jitter knob | A configurable `jitter` | No consumer needs it; exponential always jitters |
| No resource-group default policy | `DefaultSessionOptions.retry_policy` | YAGNI; it can be added later next to `handler_options` |

## 7. Open Questions

- Does a session waiting out its backoff (PENDING, not due yet) count toward the keypair's pending-session limits? The proposal is yes, the same as any PENDING session.
- Is the attempt record a new table, or an extension of the scheduling history rows? Those rows are per phase and merge repeats into an `attempts` counter, which is a different granularity.
- Should OOM become its own class? The agent does not record OOM as a reason today (it is exit code 137 under `self-terminated`), so it falls under `EXIT_NONZERO` until it does.

## 8. References

- [BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md): need_retry / expired / give_up
- [BEP-1055](BEP-1055-preemption-scheduler-mechanics.md): RESCHEDULING and preemption reschedule mode
- [BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md): preemption of low-priority sessions
