---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Implemented
Created: 2026-07-03
Created-Version:
Target-Version:
Implemented-Version: 26.8.0
---

# Preemption Scheduler Mechanics

## Related Issues

- Epic **BA-3056**, this BEP **BA-6692** (blocks **BA-3058**, the implementation)
- Amended by **BA-6926** — scope-local `job_priority` for preemption (sections 2.4, 3.a, 3.b)
- Amended by **BA-7092** — as-built alignment: victim status set, the reservation-backed trigger, and the `RESERVED`/`RESCHEDULING` states (sections 2.2, 2.3, 3.a–3.c, Decision Summary, Open Questions)
- Upstream spec (motivation): **[BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md)** — referenced, not expanded
- Prerequisites (done): BA-3057 (RG config), BA-4912 (`is_preemptible`). Out of scope: BA-4913 (Not Planned)

## 1. Goal

When a high-priority pending session waits for lack of resources, **preempt an already-running low-priority session to free capacity**. Motivation and the upstream spec live in BEP-1014.

So far preemption has **only the data, config, and API surface**; there is **no scheduler logic that actually performs preemption**. This BEP defines that missing part: **how the scheduler carries out preemption**.

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**. ✅ / ➕ are read against the state *before* this BEP; the rows describe what was actually built, and every ➕ item shipped in 26.8.0 unless its row says otherwise.

### 2.1 API (user and admin triggers)

| | Item |
|---|---|
| ✅ | On session creation, the user sets `priority` (0..100) and `is_preemptible` (default True) — `services/session/actions/{create_from_params,enqueue_session}` |
| ✅ | An admin sets `preemptible_priority`, `order`, `mode` via the RG config — scaling group API |
| ➕ | Expose `preemption.enabled` (preemption on/off toggle) and `preemption_min_runtime` (the anti-thrashing knob in section 3) in the RG config |
| ➕ | On session creation, the user also sets `job_priority` — the session's **scope-local** preemption priority (used only for preemption; see 2.4). Distinct from the global scheduler `priority` |
| ➕ | Keypair (user) resource policy gains `max_priority` — caps the `priority` a user may declare on session creation (2.4) |
| ➕ | Retire admin `preemptible_priority` — unused once victims are chosen by relative `job_priority` (3.b). **As built the field is still accepted and returned by the RG config surface (REST/GQL/DB); no scheduler code reads it.** Removing it is a breaking API change — left as an Open Question |

> Preemption is never invoked directly by a user; the scheduler decides it automatically, so **there is no new trigger API**.

### 2.2 DB (stored data)

| | Item |
|---|---|
| ✅ | `SessionRow.priority` (default 10), `SessionRow.is_preemptible` (default True) |
| ✅ | `ScalingGroupOpts.preemption = PreemptionConfig(preemptible_priority=5, order, mode)`, `PreemptionMode=terminate\|reschedule`, `PreemptionOrder=oldest\|newest` (BEP-1014's "suspend" is a typo). **No on/off field** |
| ✅ | `SessionStatus`: PENDING, **DEPRIORITIZING** (on retry give-up, lowers its own priority by 10 and returns to PENDING), ..., TERMINATING, TERMINATED |
| ➕ | New `PreemptionConfig.enabled: bool` — preemption on/off toggle, **default False (opt-in)** |
| ➕ | New `SessionStatus.PREEMPTED` — the **single state** for a confirmed victim; it branches by mode to **`TERMINATING` (terminate) or `RESCHEDULING` (reschedule)** (3.(c)) |
| ➕ | New `SessionStatus.RESCHEDULING` (+ kernel counterpart) — a victim's kernels are torn down here before the session is re-enqueued as PENDING (3.(c)) |
| ➕ | New `SessionStatus.RESERVED` / `KernelStatus.RESERVED` — the **initiator** holds its placement while its victims drain (3.(c)) |
| ➕ | New `prereserved` bucket on the agent resource and allocation rows (with `prereserved_at`) — the initiator's hold before its kernels are admitted; counted as occupied by the capacity guard (3.(c)) |
| ➕ | New `preemption_min_runtime` config field (RG opts) |
| ➕ | New `SessionRow.job_priority` (default 10) — scope-local preemption priority, compared only within the same scope-owner (2.4, 3.b) |
| ➕ | New keypair resource-policy field `max_priority` — per-user cap on the global `priority` (2.4) |
| ➕ | Retire `PreemptionConfig.preemptible_priority` — the absolute RG threshold is unnecessary once victims are chosen by relative `job_priority` (3.b). **Still stored and served; unread by the scheduler** (2.1) |

### 2.3 Sokovan (scheduler behavior)

| | Item |
|---|---|
| ✅ | Scheduling loop: `ScheduleCoordinator` (timer, per-RG) → `ScheduleSessionsLifecycleHandler` → `provisioner.schedule_scaling_group()` |
| ✅ | Provisioner: sequence (top-priority band) → validate → select agent → allocate. **Additive-only** — it never frees resources |
| ✅ | Termination: `mark_sessions_terminating()` → next tick `TerminateSessionsLifecycleHandler` → `destroy_kernel` (**async**, finalized via agent events) |
| ✅ | `is_preemptible` is used **only for deployment defaults (False) and RG default merging**, and is **never read for scheduling decisions (the core gap)** |
| ➕ | Add the victim candidates (whole sessions, decomposed per agent) to the snapshot (3.(a)) |
| ➕ | Preemption **planner** — candidate filter + victim selection (3.(b)) |
| ➕ | **The (injected) controller reserves the initiator and marks victims PREEMPTED**, and a new preemption handler **branches by mode** (terminate/reschedule) (3.(c)) |
| ➕ | Two cycles that carry the reservation forward: `RELEASE_RESERVED` (admit prereserved kernels as capacity is restored) and `CHECK_RESERVED_PROGRESS` (promote a fully admitted session to SCHEDULED) (3.(c)) |

> Because termination is async, the provisioner cannot terminate synchronously, so **preemption is inherently multi-tick**.

### 2.4 Priority Model — `priority` vs `job_priority`

Preemption is decided by a **new axis, `job_priority`**, not the scheduler `priority`. Three axes answer three different questions and apply at different stages:

| Axis | What | Set by | Stage | This amendment |
|------|------|--------|-------|----------------|
| Scheduler `priority` (existing) | System-wide order of the pending queue | User, up to the keypair policy `max_priority` | **First — scheduling** | Kept; excluded from preemption |
| `job_priority` (new) | A user's ranking **among their own jobs**, within their scope | User, at session creation | **After scheduling — preemption** | Introduced; the **only** key for victim comparison |
| Fair-share | A difference in scheduling *method* (sequencer) | — | Scheduling (alternative) | **Unrelated** — untouched |

**How it plays out:** the scheduler orders the queue by `priority` first; when the front pending session cannot be placed, preemption evicts **that owner's own** running sessions with a lower `job_priority` — "my urgent job bumps my background job." Sessions of a different owner never enter the comparison.

**Scope of `job_priority`:**

| Scope | Owner key | v1 |
|-------|-----------|----|
| User | `session.user_uuid` | ✅ victims restricted to the pending session's `user_uuid` |
| Project | `session.group_id` | ➖ **future** — needs a "project session" concept (a session owned by a project, not a user) |

`job_priority` values are **only comparable within one owner** (no global meaning). v1 fixes the owner key to `user_uuid`; wider scopes reuse the same column and only change the owner key used for comparison.

> The keypair resource policy `max_priority` bounds the global `priority` a user may declare on session creation; `job_priority` needs no such cap since it only reorders the user's own jobs.

> **Caveat — v1's within-owner rule vs BEP-1014's motivation.** BEP-1014's original driver was *cross-tenant* preemption (evicting a *different* owner's low-priority work on a shared cluster). v1 restricts victims to the **same user**, so the case it actually opens is the narrow, safe one: "my urgent job preempts my own background job." This is intentional — cross-tenant preemption needs a policy for who may evict whose work, which must rest on an **admin-managed cross-scope axis**, not a user-declared `job_priority`. Cross-tenant is therefore left to the future axis in Open Questions.

## 3. Implementation Design

**Core flow:** pending placement fails → **planner selects victims** → **controller reserves the initiator's placement and marks the victims PREEMPTED, which branches by mode** → as the victims' resources come back the reservation is admitted and the initiator becomes SCHEDULED.

### (a) Data layer — victim candidates in the snapshot

Since allocation is per-agent, load the **victim candidates of the resource group grouped by scope-owner, each decomposed per agent** into the snapshot. Nothing is loaded when the group has preemption disabled.

- The **candidate unit is a whole session** (a victim dies once and frees everywhere it holds), carrying `job_priority` (victim comparison key), execution start time (for `order` and min-runtime; absent when the session never ran), and the **per-agent amounts preemption would actually free**.
- Reclaimable amount per (agent, slot) comes from the session's **live resource allocations** — the usage the agent has reported, falling back to the requested amount until it does. Allocations already released do not count.
- **Every candidate condition of (b) is applied at load time**, so the selection layer only compares and orders; it never re-filters by status. Candidates are keyed by owner so the same-owner rule is a lookup rather than a scan.

### (b) Provisioner — preemption planner (read + propose)

When a requirement cannot be placed, the provisioner falls back to the planner. The planner **only reads and proposes**; the controller initiates the actual eviction (the provisioner stays additive). Victim decisions are returned in `ScheduleResult`, paired with the initiator that claimed them.

**Victim candidate conditions** (all AND):

| Condition | Note |
|-----------|------|
| The session **occupies resources and can still be terminated** — `SessionStatus.preemption_victim_statuses()` | **Not RUNNING-only.** A session being provisioned (SCHEDULED through CREATING) already holds an agent's slots, so it is a victim too. The set excludes TERMINATING (its resources free without preemption), PREEMPTED/RESCHEDULING (in-flight victims, so they are never re-picked) and RESERVED (that hold belongs to another preemption plan) |
| The kernel is bound to an agent and its allocation is **not yet freed** | Only holds that preemption would actually release count |
| `is_preemptible` and not private/SFTP | Per-session opt-out + infrastructure sessions excluded — as victim **and** as initiator (a private session never triggers preemption) |
| `victim.user_uuid == pending.user_uuid` | **Same scope-owner (v1: user scope). `job_priority` is only comparable within one owner** |
| `victim.job_priority < pending.job_priority` (strict) | **Preempt by scope-local `job_priority`, not the global `priority`. Equal `job_priority` is never preempted.** Loaded against the owner's **highest** pending `job_priority`; the exact per-pending comparison happens in the selection layer |
| `now - started_at >= preemption_min_runtime` | Anti-thrashing. **Default 0 (disabled)** |

**Victim selection** (per-agent):
- On an agent where the pending session could fit, pick victims by **`job_priority` ascending, then the configured `order` strategy** — `oldest`/`newest` break ties by start time; `fewest-sessions`/`smallest-resources` choose deficit-aware against the pending session's shortfall. `preemption_order` is retained (only the `preemptible_priority` threshold is retired).
- Preempt **only when fully satisfied**. Feasibility is decided by **re-running the normal placement chain with every unclaimed victim provisionally credited back** to its agents; if no agent fits even then, the session is not placed and nothing is preempted (no partial preemption, avoiding wasted kills and livelock). Only after an agent is chosen are the victims collected — just enough to cover *that* agent's shortfall, so crediting all of them is a feasibility probe, not the eviction set.
- A victim's whole allocation is credited on **every agent it touches** — a session dies once, so a multi-node victim is **evicted atomically across all its kernels** (no partial gang preemption).
- **Multi-node initiators are supported**: a multi-node session is placed one requirement (kernel group) per agent, each requirement may fall back to preemption, and the victims of all its requirements are collected into one plan.
- Victim proposals never leak into the state other sessions see: the probe is rolled back per requirement, and a **claimed-victim set spanning the pass** keeps one session from being counted for two initiators.

### (c) Eviction — the initiator reserves, the victims branch by mode

The schedule pass (handler) **only judges and proposes**; it does not mutate sessions directly (its target is PENDING, keeping side effects minimal). Given the plan (`ScheduleResult`), **the injected `scheduling_controller` writes both sides of it** — the same controller-entry pattern user-requested termination uses via `mark_sessions_for_termination`:

| Side | Written state | Meaning |
|------|---------------|---------|
| Initiator | `RESERVED` (kernels `RESERVED`, slots **prereserved** on the chosen agents) | The placement is already decided and held; the session is waiting only for its victims to drain |
| Victims | `PREEMPTED` | Confirmed victims, plus an event broadcast and a request for the preemption cycle next tick |

**The reservation gates the eviction.** Victims are marked only for initiators whose reservation was actually written — the reservation batch is all-or-nothing against the agents' capacity guard, and a batch that rolls back leaves its sessions PENDING with no victim touched. Nothing is ever killed for a placement that did not take hold.

Then **a preemption lifecycle handler targeting `PREEMPTED` picks the branch `preemption.mode` asks for** — both branches tear the kernels down under reason `PREEMPTED_BY_SCHEDULER`, and the follow-up belongs to the destination state's own handler:

- **terminate**: hand off to the existing termination path → `TERMINATING` → `TERMINATED`.
- **reschedule**: `RESCHEDULING`, whose handler re-sends the destruction request until every kernel is gone and then **re-enqueues the same session as `PENDING`** (session id/config/priority/`job_priority` preserved, Slurm REQUEUE). Suited to batch jobs with checkpointing; **interactive sessions lose in-container state (accepted, documented).**

```
initiator -> RESERVED ---(victims freed, kernels admitted)--> SCHEDULED

victim selected -> PREEMPTED
  ├ [terminate]  -> TERMINATING  -> TERMINATED
  └ [reschedule] -> RESCHEDULING -> PENDING   (priority preserved, re-competes)
```

`PREEMPTED` is the **single decision state**: it says "this session is a confirmed victim" and nothing about how it dies. Each mode's teardown-and-destination work lives in its own handler, so the preemption decision stays separate from mode-specific execution.

**Multi-tick.** A victim in PREEMPTED (or the following TERMINATING/RESCHEDULING) is outside the candidate set, so it is not re-picked. The **reservation is what keeps the initiator quiet**: a RESERVED session is no longer a pending candidate, so it cannot preempt anything further, and its prereserved hold counts as occupied capacity — no other session can consume the resources it is waiting for. Admission is **first reserved, first released**: each cycle the repository moves the prereserved holds of the longest-waiting reservations into place within each agent's restored capacity, and a session whose kernels are all admitted is promoted to SCHEDULED. When the operator opts into a phase timeout or retry limit, a reservation that waits too long is reset to PENDING, which releases its holds.

## Decision Summary

| Decision | Content |
|----------|---------|
| Enable toggle | New RG `PreemptionConfig.enabled`, default False (opt-in). No preemption when off |
| Trigger | Preempt when normal allocation fails AND preemption is on AND a fully-satisfying victim set exists |
| Eviction path | Schedule pass only proposes; **the (injected) controller reserves the initiator and marks victims `PREEMPTED`**; a preemption handler branches by mode |
| State model | Decision state `PREEMPTED` → terminate: TERMINATING → TERMINATED / reschedule: RESCHEDULING → PENDING (REQUEUE, id/priority/`job_priority` preserved) |
| Victim status set | Any session that **occupies resources and is still terminatable** — provisioning sessions (SCHEDULED…CREATING) included, not RUNNING-only. In-flight victims (PREEMPTED/RESCHEDULING), TERMINATING and other plans' RESERVED holds are excluded |
| Freed resources | **Hard-reserved.** The initiator goes `RESERVED` with its slots prereserved at plan time; holds are admitted first-reserved-first as capacity returns, and released if the reservation is reset to PENDING. Supersedes the original soft "in-flight marker + top-priority-first ordering" design |
| Preemption axis | Preempt by the new **`job_priority`** (scope-local), not the global scheduler `priority`; victims chosen by relative comparison within the same owner |
| Priority scope | v1 = user scope only (`victim.user_uuid == pending.user_uuid`); project scope is future (needs a "project session") |
| Config change | Retire RG `preemptible_priority` (absolute threshold unneeded) — as built it survives on the config surface, unread by the scheduler; keep `preemption_order`, extended to `oldest\|newest\|fewest-sessions\|smallest-resources` (BA-6748) — the latter two select victims deficit-aware against the pending session |
| Priority cap | Keypair resource policy `max_priority` caps the global `priority` a user may declare; `job_priority` needs no cap (self-scoped) |
| Scope | Single- and multi-node initiators (one requirement per agent, victims of all requirements in one plan) + atomic multi-node victim eviction, no partial preemption |
| Anti-thrashing | Preempt only on full satisfaction, never preempt equal `job_priority`, `preemption_min_runtime` (default 0). Slurm's `PreemptExemptTime` is likewise no-exemption when unset (-1 equals 0) |
| Pipeline | provisioner planner (read + propose) + controller initiates eviction |
| Out of scope | Broad BA-4913 resource-policy priority validation (Not Planned). Only the keypair `max_priority` cap for the global `priority` is in scope (2.4) |

## Open Questions

- Cross-tenant (cross-scope) preemption — v1's same-owner rule cannot evict *another* owner's session. Evicting a different tenant's low-priority work belongs to a separate **admin-managed cross-scope (project) axis**, gated on the "project session" concept, and must not be conflated with the user-declared `job_priority`.
- **Should the victim set be narrowed?** Preempting a session that is still being provisioned wastes an in-flight image pull or container creation. Whether such a victim is ever actually evicted is **untested**, and the reservation guard makes it doubtful: the guard deliberately ignores the `used` bucket (a running victim's own usage, which the initiator is meant to overlap) but does count `reserved` — where a provisioning victim's slots still sit. The reservation would then roll back and the batch leaves every victim untouched. So the broad set may be inert in practice rather than harmful. Narrowing it (fully, or with a grace rule) is a **behavior change to victim selection** and needs its own decision; the RUNNING-only classifier that once declared the stricter policy was removed rather than wired in, because nothing enforced it (BA-7092).
- Removing `preemptible_priority` from the RG config surface — a breaking API change, so the field still ships unread (2.1).

## References

- [BEP-1014](BEP-1014-preemption-of-low-priority-sessions.md) — upstream motivation/spec
- Prior art: Slurm (REQUEUE, PreemptExemptTime), Kubernetes (Pod Preemption, node-by-node), Volcano/Kueue (gang)
