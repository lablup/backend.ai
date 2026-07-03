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

- Epic: **BA-3056** — Preemption of low-priority sessions
- This BEP: **BA-6692** — blocks **BA-3058** (implementation)
- Upstream spec (motivation): **[BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md)**
- Prerequisites (done): BA-3057 (RG preemption config), BA-4912 (`SessionRow.is_preemptible`), BA-4911 (`ScalingGroupOpts` Pydantic migration)
- Out of scope: BA-4913 (resource-policy priority validation — Not Planned)

## Motivation

The motivation and high-level specification live in **BEP-1014** and are not repeated or expanded here. In short: sessions carry a `priority` (0..100, default 10); the scheduler places higher-priority pending sessions first. When a high-priority pending session cannot start for lack of resources, operators want the scheduler to **preempt** already-running lower-priority sessions to free capacity.

This BEP defines **how the scheduler actually performs that preemption** — the implementation-level mechanics: candidate eligibility, victim-selection algorithm, the `terminate` / `reschedule` lifecycles, the multi-tick asynchronous model, and where preemption sits in the scheduling pipeline. BEP-1014 remains the upstream motivation/spec.

## Current Design

Preemption today is **data model + resource-group config + API surface only**. Nothing under `sokovan/scheduler/` reads `is_preemptible` or the `preemption` config; the consumer path does not exist.

Shipped schema (correcting BEP-1014 prose, which says "suspend"):

| Item | Value | Source |
|------|-------|--------|
| `PreemptionMode` | `terminate` \| `reschedule` | BA-3057 |
| `PreemptionOrder` | `oldest` \| `newest` | BA-3057 |
| RG config `preemptible_priority` | default `5` | BA-3057 |
| `SessionRow.is_preemptible` | default `True` | BA-4912 |

Relevant existing flows:

- **Scheduling loop** — `ScheduleCoordinator` (timer-driven, per-resource-group, under lock) → `ScheduleSessionsLifecycleHandler` → `repository.get_scheduling_data(sg)` → `provisioner.schedule_scaling_group()`.
- **Provisioner pipeline** — sequence (top-priority band only) → per-workload validate → select agent → allocate. It is **additive-only**: it never frees capacity and has no preemption stage.
- **Termination flow** — `repository.mark_sessions_terminating()` → next tick `TerminateSessionsLifecycleHandler` → `destroy_kernel` RPC. **Termination is asynchronous** (finalized via agent events), so the provisioner cannot terminate synchronously. **Preemption is therefore inherently multi-tick.**

## Proposed Design

### 1. Candidate Eligibility

A running session is a preemption candidate only when **all** of the following hold:

| Condition | Rationale |
|-----------|-----------|
| `status == RUNNING` | Excludes already-`TERMINATING`/`RESCHEDULING`/`PREPARING` sessions so in-flight victims are not re-picked |
| `is_preemptible == True` | Per-session opt-out (like k8s `preemptionPolicy: Never`); deployment/inference sessions are already `False` |
| not private / not SFTP | Infrastructure sessions are excluded regardless of the flag |
| `priority <= sg.preemptible_priority` | Resource-group config eligibility threshold |
| **`priority < pending.priority` (strict)** | Only sessions **strictly lower** than the pending session. **Equal-priority sessions are never preempted** |
| `now - started_at >= preemption_min_runtime` | Minimum-runtime exemption window (anti-thrashing, §4); default `0` (disabled) |

> **Emphasis:** equal-priority sessions are never preempted. The `oldest`/`newest` order is a **tie-break among victims**, not a license to preempt a running session whose priority equals the pending session's.

### 2. Victim Selection

**Trigger scope (v1):** only **SINGLE_NODE** pending sessions trigger preemption. Cross-agent gang preemption for multi-node (cluster) pending sessions is out of scope for v1 (§ Open Questions).

Allocation is per-agent, so selection uses **per-agent precise matching**:

1. For each candidate agent `A` on which the pending session could be placed, gather the candidate victims that hold a kernel on `A`.
2. Sort candidates by **priority ascending → `order` (oldest/newest) tie-break**.
3. Accumulate victims until `free(A) + Σ (victim's A-resident slots) >= requested`, stopping as soon as the requirement is met (Slurm-style greedy).
4. (Optional refinement) k8s-style reverse scan: add victims back in priority-descending order to **minimize the number and priority of victims**.
5. When several agents qualify, pick the agent with the **lowest cost**.

**Full-satisfaction principle (no partial preemption):** if no agent yields a victim set that **fully** satisfies the pending session, **do not preempt**. Partial preemption wastes kills and causes livelock, so it is forbidden.

**Cost function:** fewest victims → lowest aggregate victim priority → `order` tie-break. **Multi-node victims carry a penalty** (evicting one kills its entire gang), so they are chosen only when necessary.

**Multi-node victims (decision):** a **multi-node running session** that holds a kernel on `A` is also a candidate. If selected, **all of its kernels are evicted atomically** (Slurm whole-allocation style). **Partial preemption of a gang is forbidden** — killing only some kernels wastes resources and risks deadlock. Only the A-resident kernel's slots count toward the fit; slots freed on the victim's other agents return to the pool as a side effect.

**Double-count guard:** within a single tick's sequenced loop, keep a set of already-selected victims so one running session is not counted toward two pending sessions.

### 3. Lifecycle: terminate vs reschedule

#### terminate
Kill the victim's kernels → session `TERMINATED`, nothing restored. Reason `PREEMPTED_BY_SCHEDULER`. Equivalent to Slurm `CANCEL` / k8s delete.

#### reschedule
Tear down **all** of the victim's kernels, then **re-enqueue the same session as `PENDING`** — session id/config/identity preserved; fresh kernels are created later when capacity frees. Equivalent to Slurm `REQUEUE`.

- **Priority preserved** — the re-enqueued session keeps its original priority (no demotion).
- **Kernel cleanup order** — `destroy_kernel` for all of the victim's kernels → confirm termination (agent events) → re-enqueue the session as `PENDING`.
- **Dedicated intermediate state `RESCHEDULING`** — the session passes through a **new, dedicated status** before returning to `PENDING`. The existing `DEPRIORITIZING → PENDING` transition is **not reused**: deprioritize lowers a session's priority, whereas reschedule preserves priority and recreates kernels — different semantics. `RESCHEDULING` denotes "preempted, kernels being cleaned up, will re-enqueue as PENDING," keeping it clearly distinct from `TERMINATING` (terminate-cleanup). Final enum naming is settled during implementation; working name `RESCHEDULING`.
- **Applicability** — suited to **batch** jobs with checkpointing. **Interactive** sessions lose in-container state, so reschedule is effectively terminate+restart for them; document this.

State transitions:

```
[terminate]
 RUNNING --(preempt)--> TERMINATING --(agent event)--> TERMINATED

[reschedule]
 RUNNING --(preempt)--> RESCHEDULING --(all kernels cleaned up)--> PENDING
                        (new dedicated state)                     (priority preserved, re-competes)
```

Both `TERMINATING` and `RESCHEDULING` remove a session from the RUNNING candidate set, so preempted victims are never re-picked (§5).

### 4. Anti-thrashing / Starvation

| Mechanism | Effect |
|-----------|--------|
| **Preempt only on full satisfaction** (no partial) | No wasted kills, no high-priority livelock |
| **Never preempt equal priority** (strict `<`) | Blocks same-tier oscillation |
| **Minimum-runtime exemption** `preemption_min_runtime` | Protects just-started / just-rescheduled sessions → blocks ping-pong. Analogue of Slurm `PreemptExemptTime` (minimum run time before a job is eligible for preemption). **Default `0` (disabled = admin opt-in)**, matching Slurm; configured as a duration at RG scope |
| **Natural backoff** | A rescheduled session waits in `PENDING` and is only preempted again if a *new* higher-priority session arrives; the sequencer processes the top-priority band first (like a k8s priority heap) |

**Starvation:** because the sequencer processes the top-priority band first, the triggering pending session sits at the front of the queue and naturally acquires the freed capacity.

### 5. Multi-tick Asynchronous Model

Since termination is asynchronous, preemption cannot free resources within the same tick.

- **Tick N** — select victims → stop them (mark `TERMINATING` / `RESCHEDULING`). The pending session stays pending.
- **Tick N+k** — kernels finish terminating (agent events) → resources free → normal allocation places the pending session.

**Re-trigger guard:** once a victim is `TERMINATING`/`RESCHEDULING` it leaves the RUNNING candidate set and is not re-picked. But a still-unschedulable pending session could trigger a **new** preemption of *other* sessions on the next tick, so an **in-flight marker** is required: record a per-pending "preemption in flight" (victims + expected freed slots, in schedule state). On later ticks, skip re-triggering while enough preemption is already in flight (until victims finish or a timeout elapses, then re-evaluate).

**Capacity reservation:** freed capacity is **not hard-reserved** for the trigger. Use a soft hint plus per-tick re-validation (k8s `nominatedNodeName` model); the sequencer's top-priority-first ordering keeps the trigger ahead. A higher-priority pending session arriving mid-termination may take the slot — documented as **acceptable risk** for v1; strict reservation is a follow-up.

### 6. Pipeline Placement

The **provisioner invokes the preemption planner on allocation failure** — it already holds the snapshot and knows the shortfall. The planner **only reads and proposes**, returning victim decisions (and mode) up to the handler; the actual **stop / re-enqueue is a side effect owned by the handler**, so the provisioner stays additive. (Analogous to the k8s PostFilter `SelectVictimsOnNode` placement.)

```
provisioner.schedule_scaling_group()
  → allocation fails
  → preemption planner (read + propose): victim decisions (+ mode)
  → ScheduleResult carries the preemption decisions
ScheduleSessionsLifecycleHandler.execute():
  mode == terminate  → repository.mark_sessions_terminating(victims, reason="PREEMPTED_BY_SCHEDULER")
  mode == reschedule → clean up all kernels + re-enqueue as PENDING via the RESCHEDULING state
→ the existing TerminateSessionsLifecycleHandler carries victims through TERMINATING → TERMINATED
```

### 7. Data Layer (Snapshot Extension)

Per-agent matching requires running-session information in the snapshot:

- `RunningSessionInfo(session_id, access_key, priority, is_preemptible, occupied_slots, agent_ids, created_at, cluster_mode, session_type)`.
- `SystemSnapshot` gains running sessions **grouped by agent**.
- The repository queries `RUNNING` sessions with per-session / per-agent occupied slots (extending the existing kernel-occupancy query).

## Migration / Compatibility

- **Config already exists** (BA-3057). Default `preemptible_priority=5`, but the strict candidate conditions and the full-satisfaction principle mean preemption fires only when every condition is met.
- **New config knob** `preemption_min_runtime` (RG scope, duration), **default `0` (disabled, admin opt-in)** — matches Slurm `PreemptExemptTime`, so the default behavior adds no exemption and operators enable it explicitly.
- **Backward compatibility** — `is_preemptible` defaults to `True`, but deployment/inference sessions are already `False`, and private/SFTP are hard-excluded, so impact on existing workloads is minimal.
- **Rollout** — preemption activates only when conditions are met, so it is inherently gradual. (Whether to gate behind a feature flag vs. rely on the existing config is an Open Question.)

## Implementation Plan

Implemented in BA-3058, layer-down:

1. **Snapshot extension** — running sessions (per-agent) in the data layer.
2. **Preemption planner module** — candidate filter + victim selection + per-agent matching + atomic multi-node victim handling + double-count guard + cost function.
3. **Trigger + stop integration** — extend `ScheduleResult`; handler branches for terminate / reschedule; the **reschedule re-enqueue mechanism (the largest net-new piece — the new `RESCHEDULING` state and its transition — scoped carefully)**.
4. **Multi-tick** — in-flight marker + `preemption_min_runtime` knob.
5. **Observability (minimal) + tests** — see below.

Tests: planner units (priority order; oldest/newest tie-break; `is_preemptible=False` excluded; equal/higher priority excluded; per-agent fit; atomic multi-node victim; no double-count; preempt only on full satisfaction), snapshot population, and integration (trigger → `TERMINATING` of correct victims; reschedule re-enqueues).

**Observability (minimal):** emit the preemption reason (`PREEMPTED_BY_SCHEDULER` + trigger session id) on the preemption event so an admin can minimally trace "why was this preempted." Detailed metrics and audit trail are a follow-up.

## Decision Log

| Decision | Summary | Rationale |
|----------|---------|-----------|
| D1 reschedule semantics | Tear down all victim kernels, then **re-enqueue the same session as PENDING** (id/config/priority preserved) via a **new dedicated `RESCHEDULING` state** (DEPRIORITIZING not reused) | Slurm REQUEUE; distinct semantics from deprioritize |
| D2 reservation | Soft hint + in-flight marker; no hard reserve | k8s nominatedNodeName; multi-tick re-validation |
| D3 scope | **v1 single-node trigger + atomic multi-node victim eviction**; no partial preemption | Cross-node/gang trigger deferred; node-by-node is the industry default |
| D4 anti-thrashing | Preempt only on full satisfaction + **`preemption_min_runtime` (default 0 = opt-in)** + **never preempt equal priority** | Slurm `PreemptExemptTime` (default 0) |
| D5 candidates | RUNNING ∧ preemptible ∧ non-private ∧ `priority <= preemptible_priority` ∧ `priority < pending` ∧ min-runtime elapsed | k8s hard opt-out |
| D6 placement | Provisioner planner (read + propose) + handler executes | Co-locate the decision with resource knowledge |
| Out of scope | BA-4913 (resource-policy priority validation) | Not Planned |
| Observability | Minimal (reason log/event) for v1; detailed audit is a follow-up | Keep v1 focused |

## Open Questions

- Final enum name for the new `RESCHEDULING` state (settled during implementation).
- Whether v1 needs strict capacity reservation (soft in v1) — decide from follow-up need.
- **Multi-node (cross-agent gang) trigger** — out of scope for v1; a follow-up BEP/Epic.
- UX for interactive sessions under reschedule, given state loss (warn / reject / document).
- Rollout: keep preemption enabled by the existing config vs. gate behind a feature flag.

## References

- [BEP-1014: Preemption of Low-priority Sessions](BEP-1014-preemption-of-low-priority-sessions.md) — upstream motivation/spec
- Prior art: Slurm (preempt / gang scheduling, `REQUEUE`, `PreemptExemptTime`), Kubernetes (Pod Priority & Preemption, `nominatedNodeName`, Workload-Aware Preemption KEP-5710), Volcano (preempt / reclaim), YuniKorn, Kueue
