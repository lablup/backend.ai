---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-09
Created-Version:
Target-Version:
Implemented-Version:
---

# Agent↔Resource Group Registration: Make the Manager DB the Source of Truth

## Related Issues

- Epic **BA-6800**, this BEP **BA-6801**
- Must stay consistent with the in-flight `scaling_group` name → `resource_group_id`
  migration: BA-6706, BA-6780, BA-6050/6051, BA-6644/6710/6713
- Background: a production scheduling incident (sessions stayed pinned to an agent
  whose resource-group assumption broke at deploy time)

## 1. Goal

**Move the source of truth for an agent's resource-group membership from its local config
to the manager DB.**

Today the agent's local `scaling-group` config is effectively the source of truth. The
agent reports `scaling_group` in every heartbeat, and the manager's upsert overwrites
`agents.scaling_group` / `agents.resource_group_id` on **every** beat
(`ON CONFLICT DO UPDATE`). So an agent that boots with a stale/default config **silently
moves itself to the wrong resource group** on the next heartbeat, orphaning the sessions
running on it. There is no reconciliation / cleanup / reschedule on a group change.

This BEP defines:
1. Stop the heartbeat from overwriting the group; make the DB authoritative (config is a
   first-registration seed only).
2. Remove the compensation-debt manager→agent RPC push (the `agent.toml` rewrite).
3. Give a deliberate group change a real orchestration path (session cleanup).

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 2.1 Agent (heartbeat report)

| | Item |
|---|---|
| ✅ | Every heartbeat sends the local config value (`self.local_config.agent.scaling_group`) in `AgentInfo` — `agent/agent.py:1277` |
| ➕ | Remove agent config `scaling-group`, replace with new `initial_resource_group_name` (first-registration seed only). The agent keeps reporting (compat), but the reported value no longer changes the DB group |

### 2.2 Manager — heartbeat DB write

| | Item |
|---|---|
| ✅ | Upsert overwrites `scaling_group` (string) + `resource_group_id` (FK) every beat. `scaling_group` is in **both** `insert_fields` and `update_fields` — `repositories/agent/db_source/db_source.py:106-133`, `data/agent/types.py:127,147` |
| ✅ | `from_state_comparison` sets `need_resource_slot_update=True` on a group change — `data/agent/types.py:206` |
| ➕ | Restrict the heartbeat to updating **only the agent's status/resources**, never the group: drop `scaling_group`/`resource_group_id` from `update_fields`; keep them in `insert_fields` (first-registration seed) |
| ➕ | Add `scaling_groups.is_default` (at most one default; partial unique index). First-registration resolution falls back to the default group when the config name is null or unresolvable (warn on an unresolvable explicit name) |

### 2.3 API — group change (superadmin)

| | Item |
|---|---|
| ✅ | `ModifyAgent` (gql_legacy) writes both columns + the `registry.update_scaling_group` RPC push. **No** session cleanup/reschedule/idle check. A TODO notes the RPC is not skipped for a dead agent — `api/gql_legacy/agent.py:906-930` |
| ✅ | `registry.update_scaling_group` → RPC that rewrites the agent's `agent.toml` (+`.bak`) + in-memory config. The only caller is `ModifyAgent` — `registry.py:1395`, `agent/server.py:630`, `agent/agent.py:1569` |
| ➕ | Implement conflicting-session cleanup as a **single service-layer path** (params: policy enum + `force`), shared by v1/v2 |
| ➕ | Remove the RPC push. **v1 `ModifyAgent`** calls the service with hardcoded values (`TERMINATE` + `force`) → always terminate immediately |
| ➕ | **New v2 API**: takes the policy enum (reschedule/terminate) + `force` as user input, plus a web-UI surface |

### 2.4 Sokovan — liveness sweep

| | Item |
|---|---|
| ✅ | The stale-kernel sweep scopes by the kernel's **frozen** `resource_group_id` + owning agent, never the agent's *current* group — `sokovan/scheduler/coordinator.py:641`, `terminator/terminator.py:187`, `models/kernel/conditions.py:126` |
| ➕ | No change. The source-of-truth flip prevents heartbeat-driven orphans at the source, and orphans from a deliberate move are cleaned up by the new API (2.3) |

### 2.5 etcd — sgroup config scope

| | Item |
|---|---|
| ✅ | The agent builds the `sgroup/<name>` scope prefix from its local config; startup reads use the default MERGED scope, so any sgroup override would merge over the global value — `agent/server.py:1461`, `common/etcd.py:636-672` |
| ✅ | **No code writes sgroup-scoped keys** (install seeds GLOBAL only; only unit tests use SGROUP scope). Overrides are settable only via the manual CLI (`mgr etcd put --scope sgroup`) → a dormant capability — `install/context.py:409`, `manager/cli/etcd.py:45` |
| ➕ | Assume no sgroup overrides exist → **remove the agent SGROUP scope entirely**. The RPC / config toml-rewrite / prefix-construction paths all become pure deletions |

## 3. Implementation Design

**Core flow:** the heartbeat still reports the group but the manager ignores it → the DB is
authoritative → the group can change only via an explicit API, and the new API is
responsible for session cleanup.

### 3.1 Source-of-truth flip (decisions #1, #2)

- **First registration = INSERT-time seed only.** Config `scaling-group` is applied only
  when the `agents` row is first created. Drop `scaling_group`/`resource_group_id` from the
  heartbeat `update_fields`; keep them in `insert_fields`. The DB is authoritative thereafter.
- **Definition of "first registration":** because a LOST row persists, INSERT-only seeding
  means "apply config only when no row exists." A redeploy (reboot under the same agent_id)
  hits the UPDATE path, so config is not re-applied — **intended**. An agent is moved via the
  admin API, not by editing config.
- Consequently, the manager updates only the agent's status/resources on a heartbeat and
  ignores the self-reported group.
- **Config field change:** remove agent config `scaling-group`, introduce new **nullable**
  `initial_resource_group_name` (immediate swap, no deprecation period). The config holds the
  human-known **resource-group name** — the UUID is hard to know up front and treating config
  as an id is inappropriate. The manager **resolves name → `resource_group_id` at INSERT**
  (reusing the existing `_resolve_scaling_group_id` path). Because the config is name-based,
  it is independent of the in-flight id migration.
- **Default resource group + fallback (first registration only):** add an `is_default` flag
  to `scaling_groups`, with **at most one** default enforced by a partial unique index
  (`WHERE is_default`); a minimum of one is **not** guaranteed. At first registration the
  manager resolves the config name; if the name is **null or does not resolve**, it falls back
  to the `is_default` group. An unresolvable *explicit* name also falls back but **logs a
  warning** (a null name is the normal zero-config path and needs no warning). If there is no
  default group and no usable name, registration fails with a clear error. Setting `is_default`
  on a group clears the previous default in the same transaction. Fixtures designate one
  default group. This keeps the agent registering reliably (heartbeat is event-based, so a
  hard failure would just leave the agent invisible) while topology stays DB-authoritative.

### 3.2 Remove the RPC push (decision #3)

- Delete `registry.update_scaling_group` + the agent-side `agent.toml` rewrite (+`.bak`) +
  in-memory update.
- That RPC exists only to keep the next heartbeat from reverting the change — pure
  **compensation debt** — and loses its reason to exist once the DB is authoritative. Its only
  caller is `ModifyAgent`.

### 3.3 Group-change orchestration (decision #4)

On a group move, reconcile the conflicting sessions
(`kernel.resource_group_id != agent.current_resource_group`). Reconciliation is a **single
service-layer path** that takes a policy enum `{RESCHEDULE, TERMINATE}` and `force` as
parameters. v1 and v2 call this service **identically**; only the values passed from the API
layer differ.

- The **policy enum `{RESCHEDULE, TERMINATE}`** applies to all conflicting sessions uniformly
  (no automatic split by session type).
- **`force` behavior (v2):**
  - `force` unset: succeed if there are no conflicting sessions, fail if there are (the admin
    drains first).
  - `force` set: immediately transition conflicting sessions to the chosen policy's state
    (terminate → TERMINATING, reschedule → re-enqueue/PENDING). The actual cleanup then
    proceeds **asynchronously**, since the underlying termination path is async.
- **v1 `ModifyAgent` (superadmin):** calls the same service with **hardcoded values**
  (`policy=TERMINATE`, `force=True`) → always terminate conflicting sessions immediately. The
  RPC push is removed.
- **v2 new API:** takes the policy enum and `force` as **user input** and surfaces conflicting
  sessions / policy / result in the web UI (frontend work item).
- **What reschedule actually means:** the session **keeps its resource group** (its original
  group). It is re-enqueued to be placed on a different agent within that same group; batch
  sessions resume by re-competing, but interactive sessions have no live container migration,
  so reschedule is effectively terminate + recreate (state loss). It is the caller's explicit
  choice and the UI warns about it.
- **`RESCHEDULING` state dependency (ordering):** the intermediate re-enqueue state
  `RESCHEDULING` is introduced by the preemption work
  ([BEP-1055](BEP-1055-preemption-scheduler-mechanics.md) / BA-3058). The reschedule path in
  this BEP is therefore **implemented after** that state lands; for now it is only considered
  in the design. Until then, the terminate policy is the primary implementation target.
- **No grace window.** Since the heartbeat no longer moves agents, the "a transient config
  error kills live sessions" risk is gone, and `force` is an immediate-transition model, so a
  timer-based grace period is unnecessary.

### 3.4 etcd sgroup scope handling (decision #5)

- **Assume no sgroup overrides exist.** Rationale: zero automated writers (install seeds
  GLOBAL only; sgroup writes appear only in unit tests), no documentation, and a dormant
  capability that merges only at agent **startup**.
- Therefore **remove the agent SGROUP scope itself** → the RPC / config toml-rewrite / prefix
  construction all become pure deletions.
- **Migration note:** if a deployment happened to set `sgroup/<name>/...` overrides manually,
  those values must be moved to GLOBAL/NODE scope (documented).

### 3.5 New-agent vs reassigned-agent (decision #6)

The flip closes the deploy-time bug in both cases:
- Fresh provisioning: INSERT reads config once as a seed → correct.
- Redeploy: the UPDATE path keeps the DB value → a stale config can no longer move a live
  agent.

### 3.6 Migration / Compatibility (decision #7)

- **Agent config is a fail-fast breaking change.** `scaling-group` is removed; leaving it in
  place makes the agent **fail at startup** (no silent ignore/alias). Operators must switch to
  `initial_resource_group_name`. The old habit of moving an agent by editing config no longer
  works (moves go through the API). Call this out in the rollout note.
- The config is **name-based**, so it is **independent** of the in-flight name →
  `resource_group_id` migration (BA-6706, BA-6780, BA-6050/6051, BA-6644/6710/6713) — the
  manager resolves name → id at INSERT. However, `data/agent/types.py`'s
  `from_state_comparison` already sets `need_resource_slot_update` on a group change, so its
  interaction needs review.
- **Schema:** add `scaling_groups.is_default` with a partial unique index (`WHERE is_default`)
  so at most one group is default; fixtures mark one group as the default.

## 4. Decision Summary

| Decision | Content |
|----------|---------|
| Source of truth | The manager DB is authoritative. The heartbeat updates only the agent's status/resources, never the group |
| Config field | Remove agent `scaling-group` → new **nullable** `initial_resource_group_name` (**name**-based, resolved to id at INSERT). **Fail-fast breaking change** (old config fails at startup) |
| Default resource group | New `scaling_groups.is_default` (at most one; partial unique index; min not guaranteed). First registration falls back to the default when the config name is null/unresolvable — an unresolvable explicit name still falls back but logs a warning; no default + no usable name → registration fails |
| First-registration definition | Seed config only when no row exists (INSERT). Redeploy (UPDATE) keeps the DB value — intended |
| Heartbeat | Ignore the self-reported group (drop `scaling_group`/`resource_group_id` from `update_fields`, keep in `insert_fields`) |
| RPC removal | Delete `registry.update_scaling_group` + the agent `agent.toml` rewrite (compensation debt) |
| Orchestration structure | Conflicting-session cleanup is a single service-layer path (params: policy enum + `force`); v1/v2 share it, only the passed values differ |
| v1 `ModifyAgent` | Calls the service hardcoded (`TERMINATE` + `force`) → always terminate immediately |
| v2 new API | Policy enum + `force` as user input. `force` unset = succeed if no conflicts / fail if any; set = immediate transition |
| Cleanup policy | Apply enum `{RESCHEDULE, TERMINATE}` to all conflicting sessions uniformly (no auto split). Interactive reschedule loses state |
| Reschedule scope | The session keeps its resource group (re-enqueued within the original group). `RESCHEDULING` state comes with the preemption work (BEP-1055/BA-3058) — terminate first for now |
| force behavior | Immediate transition to TERMINATING / re-enqueue, then async. No grace window |
| etcd sgroup | Assume no overrides → remove the agent SGROUP scope (pure deletion). Manual overrides move to GLOBAL/NODE |

## 5. Open Questions

- Whether `is_default` should also drive **session** default-group selection (a session that
  omits a group currently just picks the first allowed candidate, `registry.py:2022`). Out of
  scope for this BEP; possible follow-up.
- Other implementation details, such as the exact endpoint / GraphQL naming of the new v2 API,
  are settled in the implementation PR.

> Items decided and moved to the Decision Summary / body: ModifyAgent default policy
> (terminate), `force`-unset behavior, config swap (name-based + fail-fast breaking, resolved
> to id at INSERT → independent of the id migration), reschedule scope (keeps the resource
> group + `RESCHEDULING` follows the preemption work).

## 6. References

- Epic **BA-6800**
- Related migration: BA-6706, BA-6780, BA-6050/6051, BA-6644/6710/6713
- `RESCHEDULING` state dependency: [BEP-1055](BEP-1055-preemption-scheduler-mechanics.md)
  / BA-3058 (reschedule/terminate branching, interactive state loss when live migration is
  absent)
