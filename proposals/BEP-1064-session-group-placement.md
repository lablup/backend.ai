---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-28
Created-Version: 26.7.0
Target-Version:
Implemented-Version:
---

# SessionGroup Placement for Grouped Sessions

## Related Issues

- Epic **BA-6990**, this BEP **BA-6991**
- Prerequisite (done): **BA-6135** (PR #13066) — the endpoint-replica spreading chain was found to be dead code with no producer and removed. This BEP redesigns that gap as a first-class concept.
- Adjacent: **[BEP-1055](BEP-1055-preemption-scheduler-mechanics.md)** — shares the same provisioner/selector pipeline on a different axis (preemption answers "who gets evicted", this BEP answers "where does it go")

## 1. Goal

**Make "keep these sessions apart (spread) or together (pack), per agent" a first-class placement policy.**

Today the only placement strategy is the resource group's `agent_selection_strategy` (dispersed/concentrated/roundrobin/legacy). That answers *how the cluster as a whole should be filled*; it cannot express *how a particular set of sessions should sit relative to each other*. The canonical case: the replica sessions of one deployment must land on different agents for the service to survive an agent failure, and the scheduler currently has no vocabulary for that requirement.

BA-6135 confirmed that the `kernel_counts_at_endpoint` spreading chain was never populated by any producer and removed it. The contract "replicas are spread out" therefore survives only in documentation and a config flag (`enforce_spreading_endpoint_replica`) that nothing enforces. This BEP restores the capability as a general concept rather than a replica-specific special case.

**SessionGroup** = a set of sessions sharing a common concern, holding their placement policy. Deployment replicas are the first case and the only path that creates groups automatically, but **the concept is not deployment-specific** — a user may name a group at session enqueue time, and workloads such as distributed training jobs use the same mechanism.

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 2.1 Concept and model

| | Item |
|---|---|
| ✅ | No concept of a session set exists. `sessions.group_id` is the project (user group), **not** a placement group — a naming hazard |
| ✅ | Deployment replicas are only indirectly identifiable via `sessions.replica_id → routings → replica_groups`; the scheduler never reads that path |
| ✅ | `sessions.designated_agent_ids` + `options.agent_selection_policy` — the axis that pins one session to specific agents |
| ➕ | New `session_groups` table — the holder of the placement policy |
| ➕ | `sessions.session_group_id`, **nullable** FK. NULL means "no placement constraint" and is the default for ordinary sessions |
| ➕ | `replica_groups.session_group_id`, **NOT NULL** FK — a replica group always creates its SessionGroup with itself (1:1) |

> **Not every session gets a group.** Most sessions need no placement constraint, and forcing a one-member group row onto each of them would add a row per session with nothing to show for it. Only sessions that need a constraint carry a group.

### 2.2 API

| | Item |
|---|---|
| ✅ | Session creation accepts `designated_agents` + `agent_selection_policy` (`strict`/`preferred`) — **the precedent for two enforcement levels** |
| ✅ | RG scheduler opts carry `agent_selection_strategy`, set by an admin per resource group |
| ✅ | RG scheduler opts carry `enforce_spreading_endpoint_replica: bool` — **an external contract with no enforcement behind it** |
| ➕ | SessionGroup v2 API, the standard 6 operations (create/get/search/update/delete/purge) |
| ➕ | **`session_group_id` at session enqueue** (optional). Omitted means NULL, i.e. no constraint |
| ➕ | Replica group creation creates its SessionGroup and accepts its placement policy. **Default `spread` + `preferred`** |
| ➕ | Deprecate `enforce_spreading_endpoint_replica`; its value migrates into the replica group's SessionGroup policy (3.f) |

> The user declares "how these sessions sit relative to each other" rather than "which agent this session goes to". This is a different layer from `designated_agents` and the two coexist (2.5).

### 2.3 DB

New `session_groups` table:

| Column | Type | Note |
|--------|------|------|
| `id` | GUID PK | Both users and replica groups reference a group by this id |
| `domain_id` | FK | Ownership scope |
| `project_id` | FK | Ownership scope |
| `owner_user_id` | FK | Ownership scope |
| `placement_direction` | enum `spread` \| `pack` \| `none` | `none` keeps the group but disengages placement |
| `placement_enforcement` | enum `preferred` \| `strict` | Enforcement level |
| `created_at` / `deleted_at` | timestamp | `deleted_at` is the retention boundary (3.e) |

**No `name` column.** `replica_groups` has none either and is identified through its deployment; a user-created group is likewise referenced by the id returned at creation. A human-readable name is better added when a real use case demands one.

**Ownership must line up with sessions and deployments.**

| Entity | Ownership fields |
|--------|------------------|
| `sessions` | `domain_id`, `group_id` (project), `user_uuid` |
| `endpoints` (deployment) | `domain`, `project`, `session_owner` (+ `created_user`) |
| **`session_groups` (new)** | `domain_id`, `project_id`, `owner_user_id` — **the same three axes** |

**Invariant: every member session of a group belongs to the same user** (`session.user_uuid == group.owner_user_id`). Sharing a project or domain does **not** make another user's session eligible for the group. A group policy dictates which agent its members land on, so admitting someone else's session would mean interfering with their placement. `domain_id`/`project_id` scope visibility and cleanup only; admission is decided by `owner_user_id` alone.

- A SessionGroup created by a deployment inherits the endpoint's `(domain, project, session_owner)`. Route sessions are created under `session_owner`'s `user_uuid`, so the invariant holds by construction.
- Admitting a session whose owner differs is rejected.
- Group visibility and policy-change permissions follow the existing RBAC rules of the ownership scope.

Changes to existing tables:

| | Item | Delete behavior |
|---|---|---|
| ➕ | `sessions.session_group_id`, **nullable** FK to `session_groups.id` (indexed — it is the join key of the per-agent membership query) | `ON DELETE SET NULL` — if the group goes first, the session simply becomes unconstrained |
| ➕ | `replica_groups.session_group_id`, **NOT NULL** FK to `session_groups.id` | Drained by the retention catalog ahead of the replica group itself (3.e) |
| ➖ | Remove `ScalingGroupOpts.enforce_spreading_endpoint_replica` after migration | |

> Direction and enforcement are separate columns because they are orthogonal. Collapsing them into one enum (`spread_strict` and friends) multiplies values for no gain.

### 2.4 Sokovan (scheduler behavior)

| | Item |
|---|---|
| ✅ | Selector pipeline: **exclusion filters → stateful filters → orders → strategy pick**. Orders narrow to a preferred tier and never exclude |
| ✅ | `DesignatedStrictTrackerFilter` (exclusion) / `DesignatedPreferredOrder` (order) — **the precedent that strict is a filter and preferred is an order** |
| ✅ | The exclusion-filter contract: *"drops agents that no state change can save (preemption included)"* — exactly the semantics a strict placement constraint needs (3.d) |
| ✅ | `AgentStateTracker` accumulates in-batch allocations (committed/pending) within one scheduling pass |
| ✅ | `SystemSnapshot` already carries per-RG scheduling state, including preemption candidates |
| ✅ | The scheduler has **no knowledge of group membership** (the core gap) |
| ➕ | Per-agent SessionGroup membership in the snapshot (3.b) |
| ➕ | Per-group in-batch member counts on `AgentStateTracker` — required when one pass places several sessions of the same group (3.c) |
| ➕ | `SessionGroupOrder` (preferred) + `SessionGroupStrictFilter` (**exclusion**) (3.c) |

### 2.5 Orthogonality and precedence

Three axes answer three different questions, and **the more local target always applies first.**

| Axis | Question | Set by | Target | Precedence |
|------|----------|--------|--------|------------|
| `designated_agents` (existing) | **Which agent** for this session | User, per session | One session | 1st (most local) |
| **SessionGroup policy (new)** | How these **sessions sit relative to each other** | Group owner | Group members | 2nd |
| RG `agent_selection_strategy` (existing) | **How the cluster is filled** | Admin, per RG | The whole RG | 3rd (most global) |

**Conflict rule: the SessionGroup policy wins over the RG strategy.** With an RG set to `concentrated` and a group set to `spread`, the candidates are first narrowed to agents holding no member, and concentrated then picks **within that set**. The RG strategy is not discarded; it operates on the candidate set the SessionGroup left behind.

> This precedence falls out of the existing pipeline order (filters → orders → strategy) with no arbitration logic. Not having to insert an arbiter for the new axis is the central benefit of this design.

## 3. Implementation Design

**Core flow:** for sessions that have a group, the snapshot carries per-agent member counts, the selector narrows the candidate agents by the group policy, and the RG strategy makes the final pick from what remains.

### (a) How a session gets a group

| Path | When | FK |
|------|------|----|
| **Session enqueue** | The user passes `session_group_id`; omitted means NULL | `sessions.session_group_id` (nullable) |
| **Replica group creation** | A SessionGroup is **always created together with** the replica group (1:1); its route sessions inherit it | `replica_groups.session_group_id` (not null) |

A session with a NULL `session_group_id` is placed exactly as before, by the RG strategy alone. Every group-related path in the scheduler is entered only for sessions that have a group.

**A replica group's default policy is `spread` + `preferred`** — replicas land on distinct agents where possible, without a full agent stopping a rollout.

### (b) Observation — per-agent member counts

The selector needs to know how many members of this group a given agent currently holds.

- The source is **`resource_allocations`** (the authority on occupancy) joined with `sessions.session_group_id`. `kernels.occupied_slots` is not read.
- The observation covers **every live session already bound to an agent**, not just RUNNING ones. Sessions holding a reservation (SCHEDULED/PREPARING) must count, or replicas that have not booted yet go uncounted and pile onto one agent.
- **A multi-node (cluster) session counts as 1 on each agent hosting one of its kernels.** It occupies several agents, so for spreading purposes all of them already hold the group.
- The snapshot's RG scope carries it as a per-group, per-agent count map, alongside the existing preemption-candidate snapshot.
- Loading is **restricted to the groups of this pass's pending sessions**. A pass with no grouped sessions loads nothing.

### (c) Placement decision — two additions to the existing pipeline

Which pipeline stage the enforcement level attaches to *is* the semantics. `designated_agents` is already built this way.

| Enforcement | Pipeline stage | Behavior |
|-------------|----------------|----------|
| `preferred` | **order** (`SessionGroupOrder`) | Narrows to the preferred tier only. When preferred agents have no capacity the remaining candidates stay and placement still succeeds |
| `strict` | **exclusion filter** (`SessionGroupStrictFilter`) | Removes non-conforming agents. An empty candidate set is a placement error (3.d) |
| `none` | — | The group is retained but does not participate in placement |

**Rank function (order, lower is preferred):**

| Direction | Rank | Effect |
|-----------|------|--------|
| `spread` | The agent's member count | Narrows to the agents holding the fewest members; if any hold none, only that tier survives |
| `pack` | The agent's member count, negated | Narrows to the agents holding the most members; the group converges onto as few agents as possible |

The two directions are the same rank in opposite signs. The pipeline takes the minimum rank **across every candidate**, so a negated count selects the global maximum — `pack` can express "the fullest agent" and does. The RG strategy still picks within whatever tier is left, which matters when several agents tie.

**Filter conditions (strict):**

| Direction | Passes when | Note |
|-----------|-------------|------|
| `spread` | The agent's member count is 0 | If every agent in the RG already holds a member, the candidate set empties and placement errors (3.d) |
| `pack` | The agent's member count is > 0 | **Anchor rule**: when no agent holds a member yet (the first member), the filter does not apply — otherwise the first session could never be placed. Because of this rule, `pack` + `strict` essentially never empties the candidate set |

**Accumulation within one pass.** Placing several sessions of the same group in one tick (a three-replica scale-out) is the normal path. Judged on the snapshot alone, all three see "zero members" and land on the same agent. `AgentStateTracker` therefore carries **per-group in-batch increments** the same way it carries slots and container counts, under the same all-or-nothing `commit()`/`rollback()` contract. Ranks and filters always read `observed + in-batch`.

### (d) An unsatisfiable strict constraint is not a preemption trigger

Placing strict in the **exclusion filter** stage is a semantic statement, and the stage's own contract is the rationale:

> *"Drops agents that no state change can save (preemption included)."*

An empty candidate set under `spread` + `strict` means **every agent in the RG already holds a member of this group**. Freeing resources does not help: evicting somebody else's session leaves this group's member on that agent regardless. Therefore:

| Aspect | Behavior |
|--------|----------|
| Empty candidate set | `NoCompatibleAgentError` — the same path as strict `designated_agents` |
| Preemption | **Not attempted.** The exclusion stage runs before the preemption planner is ever reached |
| Session state | The provisioner records a `SchedulingFailure`. **The session stays PENDING and is retried on the next tick** — a failed placement is not a terminated session |
| Recovery | Once another member terminates and frees an agent, the session is placed normally |

"Treated as an error" and "the session is killed" are different things. The user sees a failure reason naming the group and direction that blocked it, and the session places itself once the condition clears.

### (e) Group teardown — via the retention catalog

**Conclusion first: groups are not cleaned up by any existing cascade; the retention catalog needs explicit specs.**

The application never hard-deletes a replica group. It moves the lifecycle to a terminal state, and the row deletion is owned by the **retention sweep's bulk DELETE** (`RetentionCategory.DEPLOYMENTS` walks `routings` → `replica_groups` → `endpoints`, each on its own boundary). There is no application-level hook at deletion time to hang a cascade on.

A DB `ON DELETE CASCADE` is not available either: the FK runs `replica_groups.session_group_id → session_groups.id`, so a DB cascade would fire in the **opposite** direction (deleting a group would delete the replica group).

Both kinds of group are therefore drained by the retention catalog.

| Group kind | Cleanup |
|------------|---------|
| Owned by a replica group | A SessionGroup spec in the `DEPLOYMENTS` category, placed **before the `replica_groups` spec** so the still-present parent FK can drain it — the same pattern as draining `deployment_revisions` by endpoint id first |
| Created by a user | A spec in the `SESSIONS` category, on its own `deleted_at` boundary with a `NOT EXISTS (member sessions)` guard, so a group with live members is never removed |

**No new retention category.** One spec added to each of `DEPLOYMENTS` and `SESSIONS` is enough. A category is the unit an admin tunes, and there is no reason to tune group retention separately — a group never needs to outlive the replica group that owns it or its member sessions.

The replica-group spec matches the parent's boundary through the reverse FK: the group rows are selected by `session_groups.id IN (SELECT replica_groups.session_group_id ...)` over terminal replica groups, using the existing spec's parent-boundary form. **Spec order decides correctness** — if the `replica_groups` spec runs first the source is already empty and the groups are orphaned permanently. Catalog order is a contract here and must be called out in a comment.

A user-created group can also be removed through the explicit delete/purge API. It is not auto-deleted merely because its members ended, since reusing a group for new sessions is the normal pattern; abandoned groups are collected by the `deleted_at` sweep above.

**A group can disappear before its members.** `SESSIONS` and `DEPLOYMENTS` are separate categories with independent policies and thresholds, so their delete order is not ordered. That is why `sessions.session_group_id` is `ON DELETE SET NULL` — the session row survives a group that went first, and a placement already made is never revisited (3.g).

### (f) `enforce_spreading_endpoint_replica` migration

Only replica groups are migrated. Ordinary sessions have a NULL group and need no backfill.

| Step | Content |
|------|---------|
| 1 | Create a SessionGroup per existing replica group and backfill `replica_groups.session_group_id` (NOT NULL) |
| 2 | Set the policy to `spread` + **`preferred`** when the owning RG had the flag `true`, `none` otherwise |
| 3 | Mark the field deprecated and stop reading it (no behavior change — nothing enforced it) |
| 4 | Drop it from the schema and API in the next major |

Migrating to `preferred` rather than `strict`: the flag was never enforced, so promoting it to `strict` could push services that used to deploy fine into placement failures. **Migrate in the direction that cannot degrade observable behavior, and let users opt into strict explicitly.**

### (g) Scope of a policy change

**A policy change applies only to placements made after it.** Already-placed sessions are never relocated; there is no rebalancing. The policy decides where the group's *next* session goes, and does not retroactively constrain running sessions.

### Naming — `spread` / `pack`

The industry-standard pair is used. `dispersed`/`concentrated` is closer to Backend.AI-specific phrasing.

| System | Apart | Together |
|--------|-------|----------|
| Kubernetes | Pod Topology **Spread** Constraints, `LeastAllocated` | **Bin packing**, `MostAllocated` |
| Slurm | `--spread-job` | `CR_Pack_Nodes` |
| Nomad | `spread` block | Bin-packing (default) |
| Docker Swarm | `spread` | `binpack` |

The RG axis keeps its existing `dispersed`/`concentrated`. Distinct vocabulary for the two axes helps signal that they are orthogonal.

## Decision Summary

| Decision | Content |
|----------|---------|
| Concept | SessionGroup = a set of sessions sharing a common concern, holding a placement policy. **Not deployment-specific — selectable at session enqueue too** |
| Data model | New `session_groups` table. `sessions.session_group_id` is **nullable**, `replica_groups.session_group_id` is **NOT NULL** |
| Universal membership | **Rejected.** NULL means "unconstrained" and is the default for ordinary sessions |
| `name` column | Not added. `replica_groups` is likewise identified through its deployment; user groups are referenced by id |
| Ownership scope | `domain_id` / `project_id` / `owner_user_id`, the same three axes as sessions and endpoints. A deployment's group inherits the endpoint's values |
| Member ownership | **All members of a group belong to one user.** A shared project or domain does not admit another user's session — the policy would otherwise dictate their placement |
| Policy axes | **Direction (`spread`\|`pack`\|`none`) x enforcement (`preferred`\|`strict`)**, as two columns |
| Granularity | **Per agent.** An agent is normally a node, so no separate topology axis is introduced |
| Orthogonality | A separate axis from the RG `agent_selection_strategy`; the RG strategy operates on the candidate set the SessionGroup leaves |
| Precedence | `designated_agents` > **SessionGroup** > RG strategy. The more local target always applies first |
| Implementation point | `preferred` is a tracker **order**, `strict` is an **exclusion filter**, following the existing `designated_agents` precedent — no arbitration logic |
| Ranks | The same rank in opposite signs: spread = member count, pack = negated member count (the pipeline's minimum over all candidates makes that the global maximum). `pack` skips the constraint for the first member (**anchor rule**) |
| Unsatisfiable strict | **No preemption, recorded as an error.** The exclusion stage is where conditions unsalvageable by any state change (preemption included) belong. The session stays PENDING and retries |
| Observation | `resource_allocations` joined with `sessions.session_group_id`; every agent-bound live session counts; a multi-node session counts once per agent; only this pass's groups are loaded |
| In-batch accumulation | Per-group increments on `AgentStateTracker` under the existing commit/rollback contract |
| Deployment default | A replica group creates its SessionGroup with **`spread` + `preferred`** |
| Policy change | **Applies to new placements only.** Existing sessions are not relocated |
| Pre-validation | **None.** Even `spread` + `strict` with a target member count above the agent count is not rejected at creation — replica counts and agent counts both change at runtime, so a creation-time verdict goes stale immediately. It surfaces only as the runtime failure in 3.d |
| Teardown | **No existing cascade applies.** Deletion is owned by the retention sweep and the FK direction rules out a DB cascade, so a spec is added to `DEPLOYMENTS` (**before `replica_groups`**) and to `SESSIONS` (`deleted_at` + `NOT EXISTS` guard). **No new category** |
| Legacy | `enforce_spreading_endpoint_replica` migrates to `spread`+`preferred` (or `none`) for replica groups only, then is deprecated |
| Naming | `spread`/`pack`, following k8s/Slurm/Nomad/Swarm. The RG axis keeps `dispersed`/`concentrated` |

## Open Questions

- **Whether the fitting check honors group constraints.** The selector is shared by the scheduling pass and the compute-schedule fitting check. Applying group constraints there would make "can this session start now" more accurate, at the cost of loading group observations on that path too.

## References

- [BEP-1055](BEP-1055-preemption-scheduler-mechanics.md) — the same provisioner/selector pipeline; precedent for extending the snapshot and the tracker contract
- [BEP-1006](BEP-1006-service-deployment-strategy.md) — deployment and replica group structure
- [BEP-1063](BEP-1063-db-record-retention.md) — the retention catalog the teardown specs are added to
- Prior art: [Kubernetes Pod Topology Spread Constraints / Resource Bin Packing](https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/) (`whenUnsatisfiable: DoNotSchedule|ScheduleAnyway` maps onto strict/preferred), [Slurm `--spread-job` / `CR_Pack_Nodes`](https://slurm.schedmd.com/srun.html), Docker Swarm `spread`/`binpack`, Nomad `spread` block
