---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-03
Created-Version:
Target-Version:
Implemented-Version:
---

# Preemption Scheduler Mechanics

## Related Issues

- Epic **BA-3056**, this BEP **BA-6692** (blocks **BA-3058**, the implementation)
- Upstream spec (motivation): **[BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md)** — referenced, not expanded
- Prerequisites (done): BA-3057 (RG config), BA-4912 (`is_preemptible`). Out of scope: BA-4913 (Not Planned)

## 1. Goal

When a high-priority pending session waits for lack of resources, **preempt an already-running low-priority session to free capacity**. Motivation and the upstream spec live in BEP-1014.

So far preemption has **only the data, config, and API surface**; there is **no scheduler logic that actually performs preemption**. This BEP defines that missing part: **how the scheduler carries out preemption**.

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 2.1 API (user and admin triggers)

| | Item |
|---|---|
| ✅ | On session creation, the user sets `priority` (0..100) and `is_preemptible` (default True) — `services/session/actions/{create_from_params,enqueue_session}` |
| ✅ | An admin sets `preemptible_priority`, `order`, `mode` via the RG config — scaling group API |
| ➕ | Expose `preemption.enabled` (preemption on/off toggle) and `preemption_min_runtime` (the anti-thrashing knob in section 3) in the RG config |

> Preemption is never invoked directly by a user; the scheduler decides it automatically, so **there is no new trigger API**.

### 2.2 DB (stored data)

| | Item |
|---|---|
| ✅ | `SessionRow.priority` (default 10), `SessionRow.is_preemptible` (default True) |
| ✅ | `ScalingGroupOpts.preemption = PreemptionConfig(preemptible_priority=5, order, mode)`, `PreemptionMode=terminate\|reschedule`, `PreemptionOrder=oldest\|newest` (BEP-1014's "suspend" is a typo). **No on/off field** |
| ✅ | `SessionStatus`: PENDING, **DEPRIORITIZING** (on retry give-up, lowers its own priority by 10 and returns to PENDING), ..., TERMINATING, TERMINATED |
| ➕ | New `PreemptionConfig.enabled: bool` — preemption on/off toggle, **default False (opt-in)** |
| ➕ | New `SessionStatus.PREEMPTED` — the **single state** for a confirmed victim; after kernel cleanup it branches by mode to **PENDING (reschedule) or TERMINATED (terminate)** (3.(c)) |
| ➕ | New `preemption_min_runtime` config field (RG opts) |

### 2.3 Sokovan (scheduler behavior)

| | Item |
|---|---|
| ✅ | Scheduling loop: `ScheduleCoordinator` (timer, per-RG) → `ScheduleSessionsLifecycleHandler` → `provisioner.schedule_scaling_group()` |
| ✅ | Provisioner: sequence (top-priority band) → validate → select agent → allocate. **Additive-only** — it never frees resources |
| ✅ | Termination: `mark_sessions_terminating()` → next tick `TerminateSessionsLifecycleHandler` → `destroy_kernel` (**async**, finalized via agent events) |
| ✅ | `is_preemptible` is used **only for deployment defaults (False) and RG default merging**, and is **never read for scheduling decisions (the core gap)** |
| ➕ | Add running sessions (grouped by agent) to the snapshot (3.(a)) |
| ➕ | Preemption **planner** — candidate filter + victim selection (3.(b)) |
| ➕ | **The (injected) controller marks victims PREEMPTED**, and a new preemption handler **branches by mode** (terminate/reschedule) + a multi-tick in-flight marker (3.(c)) |

> Because termination is async, the provisioner cannot terminate synchronously, so **preemption is inherently multi-tick**.

## 3. Implementation Design

**Core flow:** pending placement fails → **planner selects victims** → **controller marks PREEMPTED and branches by mode** → (next tick) once resources free, normal allocation places the pending session.

### (a) Data layer — running sessions in the snapshot

Since allocation is per-agent, load the running sessions' **preemption-relevant data grouped by agent** into the snapshot:

- priority, is_preemptible, occupied slots, agent binding, created-at (for `order` and min-runtime), cluster_mode (for multi-node victim handling), session_type and private flag (candidate exclusion).
- The repository fetches `RUNNING` sessions with per-agent occupied slots. (Exact types and field signatures are an implementation detail.)

### (b) Provisioner — preemption planner (read + propose)

On allocation failure the provisioner calls the planner. The planner **only reads and proposes**; the controller initiates the actual eviction (the provisioner stays additive). Victim decisions are returned in `ScheduleResult`.

**Victim candidate conditions** (all AND):

| Condition | Note |
|-----------|------|
| `status == RUNNING` | Excludes PREEMPTED/TERMINATING so in-flight victims are not re-picked |
| `is_preemptible` and not private/SFTP | Per-session opt-out + infrastructure sessions excluded |
| `priority <= preemptible_priority` | RG config threshold |
| `priority < pending.priority` (strict) | **Equal priority is never preempted** |
| `now - started_at >= preemption_min_runtime` | Anti-thrashing. **Default 0 (disabled)** |

**Victim selection** (per-agent):
- On an agent where the pending session could fit, sort candidates by **priority ascending, then `order` (oldest/newest)** and accumulate.
- Preempt **only when fully satisfied**: `free(A) + sum(victim slots) >= requested` (no partial preemption, avoiding wasted kills and livelock).
- **v1 trigger = single-node pending only.** Multi-node victims are allowed but **evicted atomically across all kernels** (no partial gang preemption). Multi-node (cross-agent) triggers are out of scope.
- Keep a selected-victim set within a tick so one session is not double-counted for two pending sessions.

### (c) Eviction — controller marks PREEMPTED, then branches by mode

The schedule pass (handler) **only judges and proposes**; it does not mutate victims directly (its target is PENDING, keeping side effects minimal). Given the victim decisions (`ScheduleResult`), **the injected `scheduling_controller` marks victims into the common `PREEMPTED` state** (plus event broadcast + requesting a schedule pass next tick) — the same controller-entry pattern user-requested termination uses via `mark_sessions_for_termination`.

Then **a new preemption lifecycle handler targeting `PREEMPTED` cleans up kernels and decides the destination by `preemption.mode`**:

- **terminate**: hand off to the existing termination path → `TERMINATED`. Reason `PREEMPTED_BY_SCHEDULER`.
- **reschedule**: **re-enqueue the same session as `PENDING`** (session id/config/priority preserved, Slurm REQUEUE). Suited to batch jobs with checkpointing; **interactive sessions lose in-container state (accepted, documented).**

```
victim selected -> PREEMPTED (kernel cleanup)
  ├ [terminate]  -> TERMINATED
  └ [reschedule] -> PENDING   (priority preserved, re-competes)
```

There is no separate `RESCHEDULING` state. `PREEMPTED` covers the kernel-cleanup phase, and **only the final destination (PENDING/TERMINATED) differs by mode.** This separates "the preemption decision" from "mode-specific execution."

**Multi-tick:** a victim in PREEMPTED (or the following TERMINATING) leaves the candidate set, so it is not re-picked. To keep a still-waiting pending session from preempting *other* sessions, suppress re-triggering with an **in-flight marker** (until resources free or a timeout). Freed resources are not hard-reserved; the pass relies on the sequencer's top-priority-first ordering (soft).

## Decision Summary

| Decision | Content |
|----------|---------|
| Enable toggle | New RG `PreemptionConfig.enabled`, default False (opt-in). No preemption when off |
| Trigger | Preempt when normal allocation fails AND preemption is on AND a fully-satisfying victim set exists |
| Eviction path | Schedule pass only proposes; **the (injected) controller marks victims `PREEMPTED`**; a new preemption handler branches by mode |
| State model | Single new state `PREEMPTED` → terminate: TERMINATED / reschedule: PENDING (REQUEUE, id/priority preserved). No separate RESCHEDULING |
| Scope | v1 single-node trigger + atomic multi-node victim eviction, no partial preemption |
| Anti-thrashing | Preempt only on full satisfaction, never preempt equal priority, `preemption_min_runtime` (default 0). Slurm's `PreemptExemptTime` is likewise no-exemption when unset (-1 equals 0) |
| Pipeline | provisioner planner (read + propose) + controller initiates eviction |
| Out of scope | BA-4913 (resource-policy priority validation) |

## Open Questions

- Multi-node (cross-agent) trigger preemption — out of scope for v1, a follow-up BEP/Epic.
- Strict reservation of freed resources (soft in v1) — decide the need in a follow-up.

## References

- [BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md) — upstream motivation/spec
- Prior art: Slurm (REQUEUE, PreemptExemptTime), Kubernetes (Pod Preemption, node-by-node), Volcano/Kueue (gang)
