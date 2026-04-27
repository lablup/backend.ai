---
Author: Jeongseok Kang (jskang@lablup.com)
Status: Draft
Created: 2026-04-27
Created-Version: 26.5.0
Target-Version:
Implemented-Version:
---

# Session Rescheduling on Terminal Failure

## Related Issues

- JIRA: BA-5851
- GitHub Epic: #11320
- GitHub: #11321
- Companion BEP: [BEP-1053 — Agent-level Batch Retry](BEP-1053-agent-batch-retry.md)

## Motivation

Some session failures are **node-level**: the kernel was OOM-killed on this host, the agent disconnected mid-run, the registry route used by this scaling group is briefly down, the network namespace setup failed for a node-specific reason. For these cases, re-running the script in place — Backend.AI's existing scheduler-internal retries, or BEP-1053's agent-level batch retry — does not help. What does help is **rescheduling the same session to a different node**, with the same resource allocation.

Today, terminal-failure sessions stay terminal. There is no path that takes a session in `ERROR` and pushes it back through the scheduler. Operators have to ask users to re-create their sessions, often after diagnosing that the failure was the host's fault, not the user's. This BEP closes that gap.

It is the companion to [BEP-1053](BEP-1053-agent-batch-retry.md), which handles in-script retry; together they cover the two distinct retry surfaces. They are designed to ship independently.

### Goals

- Re-dispatch a terminal-failed `BATCH` session through the scheduler when the failure is classified as **node-level**.
- Reuse existing scheduler infrastructure: `SessionLifecycleHandler`, `phase_attempts`, scheduling history, the `expired → PENDING` transition pattern.
- Make failure classification **operator-extensible** — etcd-driven pattern config, not a closed enum in code.
- Promote the standing `SERVICE_MAX_RETRIES = 5  # FIXME: make configurable` (`manager/defs.py:121`) to a real configuration knob as a side effect.
- Default off; opt-in per scaling group.

### Non-goals

- Mutating resource allocation (no "give it more memory and retry"). Resource decisions stay with the user/admin.
- User-facing per-session `RetryPolicy` with backoff/jitter/max. Rescheduling is operator-policy, not user-policy.
- Interactive or inference sessions. INTERACTIVE is user-driven; INFERENCE has BEP-1049 deployment-route handling.
- Re-running the user script in place. That is BEP-1053's job.

## Current Design

### Session lifecycle and terminal status

`SessionStatus` (`src/ai/backend/manager/data/session/types.py:30-50`) defines the lifecycle. `terminal_statuses()` (line 109) is `{ERROR, TERMINATED, CANCELLED}` — no transitions out today. `retriable_statuses()` (line 118) is the scheduler's *in-session* retriable set; it does not apply to sessions already in `ERROR`.

### Sokovan lifecycle handlers

Periodic `SessionLifecycleHandler`s drive scheduler decisions (`sokovan/scheduler/handlers/`). Each declares `success / need_retry / expired / give_up` outcomes and the status transitions for each (`base.py:62-93`). Existing handlers include `CheckPreconditionLifecycleHandler` and `StartSessionsLifecycleHandler`, which use the **`expired → PENDING`** transition pattern (`check_precondition.py:67`, `start_sessions.py:78`) — the canonical "re-schedule this session" mechanism, scoped today to startup-stage timeouts.

### Existing counters and caps

- `phase_attempts` (`sokovan/data/lifecycle.py:322`): per-session attempt counter sourced from scheduling history (`coordinator.py:756`). Documented as "give_up when >= max_retries."
- `SERVICE_MAX_RETRIES = 5  # FIXME: make configurable` (`manager/defs.py:121`): the global cap, used by both session and deployment coordinators (`coordinator.py:1228`, `deployment/coordinator.py:764`).

### Failure metadata

When a session fails, `SessionRow.status_data` carries `{"error": {"name": ..., "src": ...}}` per `manager/exceptions.py:convert_to_status_data` and the `ErrorStatusInfo` / `ErrorDetail` TypedDicts (line 97). The shape is stable.

### What is missing

A handler that fires on **terminal-failure** sessions, classifies the failure, and either rescheduples or accepts the failure. Today's handlers run on non-terminal sessions only.

## Proposed Design

### A new lifecycle handler: `RescheduleFailedBatchSessionsLifecycleHandler`

Lives at `sokovan/scheduler/handlers/lifecycle/reschedule_failed_batch.py`, alongside the existing handlers. Targets sessions where:

- `session_type == SessionTypes.BATCH`
- `status == ERROR`
- `phase_attempts < effective_max_retries`
- `status_data["error"]` classifies as a *reschedulable* cause (see "Classification" below).

Outcomes:

- **`success`** (rescheduling fired): transition `ERROR → PENDING`. Re-uses the existing `expired → PENDING` machinery, just from a new starting status. Increments `phase_attempts` via the standard scheduling-history append.
- **`give_up`** (cap reached, or cause not reschedulable): no transition. Session stays in `ERROR`.
- **`need_retry`** (transient inability to act, e.g., DB contention): no transition; handler retries next cycle.

The handler reuses **everything** the existing lifecycle handlers reuse: `phase_attempts` from scheduling history is the counter, `SERVICE_MAX_RETRIES` (now configurable, see below) is the cap, the lifecycle-coordinator path applies the transition. No new column on `SessionRow`. No queue table. No child sessions.

### Same session, not a child

A reschedule keeps the original `SessionRow` — same `id`, same `creation_id`, same kernels record, same resource allocation. The session re-enters `PENDING` with `phase_attempts` incremented; the scheduler picks a new agent on the next dispatch cycle. The kernels associated with the previous attempt are cleaned up as part of the terminal-state transition that already runs today.

This is intentionally different from the original BEP-1053 draft: there are no parent-child rows, no retry chain, no `parent_session_id`. The "history" of attempts is what scheduling history already records.

### Failure classification — extensible, not closed

A closed enum of causes hardcodes runtime behavior into code; site-specific failure signatures (vendor accelerator faults, registry-specific image-pull errors, custom-plugin failures) cannot be classified without a manager release. Replace the closed enum with a **pattern-based config**, loaded from etcd and refreshed via `EtcdConfigWatcher` (`manager/config/provider.py:20`):

```yaml
# config/manager/session_failure_classification
default: give_up
by_error_name:
  OOMError: reschedule
  AgentDisconnected: reschedule
  ImagePullError: give_up      # agent's tenacity already retried
  HeartbeatTimeout: reschedule
  ValidationError: give_up
  QuotaExceededError: give_up
by_error_src:
  agent: reschedule            # fallback for agent-side errors not named above
```

Resolution order: `by_error_name` (most specific) → `by_error_src` → `default`. The result is one of three closed `Action` values: `reschedule`, `give_up`, or `ignore` (do not handle yet — leave for the next cycle, used rarely).

The **action catalog** stays a closed enum (the manager has to know what each action means), but the **cause catalog** is open: operators add patterns without code changes.

Hardcoded never-reschedulable causes: `USER_CANCELLED` (user intent), and any cause that originates *after* the session reached `RUNNING` and the user's script started — those are BEP-1053's domain. The handler short-circuits on these regardless of config.

### `SERVICE_MAX_RETRIES` becomes configurable

Same etcd path: `config/manager/scheduler_max_retries`. Read at startup, refreshed via `EtcdConfigWatcher`. Per-scaling-group overrides under `config/scaling-groups/{sg_name}/scheduler_max_retries`. Default `5` (matches current constant). The handler resolves the cap from scaling-group config first, then cluster, then default. Closes the standing `FIXME: make configurable`.

### Kill switch

`config/manager/reschedule_disabled` (etcd boolean, default `false`). Loaded at startup, watched. Checked at the top of the handler's per-cycle execution. When `true`, the handler is a no-op for that cycle. Useful for incident response (e.g., stop rescheduling cluster-wide during a cascade).

### Observability

- Counters: `bai_session_reschedule_attempted_total{cause}`, `bai_session_reschedule_capped_total{cause}` (cap reached), `bai_session_reschedule_succeeded_total` (subsequent attempt reached `RUNNING`).
- Event: `session.rescheduled` emitted when `ERROR → PENDING` transition fires. Reuses the existing event-publication path from the lifecycle coordinator.
- Audit log entry per reschedule: `(session_id, cause, attempt N of M, source_agent, target_after = scheduler_choice)`.
- The existing scheduling-history rows already record per-attempt timestamps and outcomes; that is the durable trail.

## Migration / Compatibility

### Backward compatibility

- Default `reschedule_disabled = false` *and* default classification config produces no `reschedule` actions for any cause. So **the feature is effectively off until an operator populates the classification config** — zero behavior change on rollout.
- All etcd keys are additive; no existing key changes shape.
- No Alembic migration required.
- `SERVICE_MAX_RETRIES` constant in `manager/defs.py:121` remains as the default if the etcd key is absent. The `FIXME` is closed; the constant becomes a fallback.

### Quota and accounting

A reschedule does not create a new `SessionRow`, so concurrent-session limits are unaffected. Resource consumption from the previous attempt is not refunded — the user *did* consume those resources on the failed node — but the next attempt re-uses the same allocation request, so quota is not double-counted.

### Interaction with BEP-1053

The two BEPs are designed to compose:

- **BEP-1053** runs first inside the failing kernel; non-zero exit → re-run script; only if all attempts fail does the agent emit `SessionFailureAnycastEvent`.
- **BEP-1054** then evaluates the resulting terminal-failure session. If the cause is node-level, the scheduler reschedules. If the cause is "user script failed after all in-place retries," the classification config maps it to `give_up` and the session stays terminal.

A session can therefore experience: agent-side script retries → manager-side reschedule → on a new node, agent-side script retries again. Each attempt's history is recorded in scheduling history; users see one logical job, operators see the full trail.

## Implementation Plan

Five PRs, each tracked under #11320:

1. **BEP draft** (this document and the companion BEP-1053) — #11321.
2. **Foundation:** `FailureClassifier` (pattern-based, etcd-driven, refreshed via `EtcdConfigWatcher`) and the `Action` enum. Pure logic, unit-test heavy.
3. **`SERVICE_MAX_RETRIES` configurability:** etcd source + per-scaling-group override + fallback to the `defs.py` constant. Closes the standing FIXME.
4. **Lifecycle handler:** `RescheduleFailedBatchSessionsLifecycleHandler`, kill switch, the `ERROR → PENDING` transition (extending the existing pattern to a new starting status), counters/events/audit.
5. **API surface:** session info responses include `reschedule_count` (= `phase_attempts` view) and the latest `reschedule_cause`. No mutation; this is read-only observability.
6. **Client:** SDK v2 + CLI v2 surface the new info fields; user docs.

Tests live with the code under test. Cross-cutting integration tests — node-level failure → reschedule → success on different agent; cap-reached → terminal; classification-config-empty → terminal; kill-switch-on → no rescheduling — ship with the lifecycle-handler PR. Estimated effort: two to three weeks for one engineer.

## References

- Companion: [BEP-1053 — Agent-level Batch Retry](BEP-1053-agent-batch-retry.md)
- Working draft and design pivot rationale: `docs/investigation/bep-1053-design-pivot.md`
- [BEP-1030: Sokovan Scheduler Status Transition Design](BEP-1030-sokovan-scheduler-status-transition.md)
- [BEP-1049: Zero-Downtime Deployment Strategy Architecture](BEP-1049-deployment-strategy-handler.md) — analogous handler-pattern for routes
