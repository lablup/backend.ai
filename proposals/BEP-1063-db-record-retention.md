---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-17
Created-Version: 26.7.0
Target-Version:
Implemented-Version:
---

# DB Record Retention Management

## Related Issues

- Epic **BA-6924**, this BEP **BA-6925**
- Adjacent (cross-reference only, not covered here): **BA-4383** (artifact storage retention), **BA-3037** (unused docker image GC)

## 1. Goal

Backend.AI accumulates historical rows — event/audit/login logs, reconcile and scheduling history, terminated session/kernel and destroyed deployment records, and usage aggregation — with **no unified way to bound their growth**. Only two partial mechanisms exist today: a dedicated `GlobalTimer` sweeping one table (`error_logs`) against one hard-coded etcd key, and a manual `clear-history` CLI over a fixed hand-coded set. Everything else grows without limit.

This BEP defines a **general-purpose retention layer**: a super-admin declares a retention period **per data category**, and the manager periodically purges records older than that period, batched and referentially safe. The purpose is **system-level cleanup of excessive accumulation**.

**Non-goals:**

- **Per-scope (project/domain/user) retention.** The purpose is system-wide cleanup; policies apply **globally per category**. There is no current per-scope requirement, and mature schedulers keep purge global too (Slurm `slurmdbd.conf` `Purge*After` are all per-`slurmdbd`, not per-account). A future extension can add scope if a concrete need arises.
- **Soft-delete / archive.** Every category hard-deletes; a long default period, not archival, protects billing data.
- Artifact/object-storage retention (BA-4383) and docker image GC (BA-3037) — different substrates, tracked separately.
- **Cleanup of `vfolders` / `images` / `service_catalog` / `artifacts`** — each differs (no dedicated timestamp, a blocking `RESTRICT` FK, a runtime registry better swept by heartbeat age, or a separate epic BA-4383) — **out of scope here, handled separately**.
- **`VACUUM FULL` automation** — it locks the table and stays a manual CLI operation.

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 2.1 Policy storage

| | Item |
|---|---|
| ✅ | `error_logs` retention is a single etcd key `config/logs/error/retention` (default 90d) |
| ➕ | `retention_policies` DB table, **one row per category** — retention period + enable; sweep cadence & batch size live in server config |

### 2.2 Target coverage (catalog)

| | Item |
|---|---|
| ✅ | `error_logs` (timer) + terminated sessions/kernels & `error_logs` (CLI) |
| ➕ | Full **category catalog**: append logs / lifecycle (sessions, kernels, **destroyed endpoints**) / usage — each with a referentially-safe delete procedure encoded in code |

### 2.3 Sweep execution

| | Item |
|---|---|
| ✅ | `GlobalTimer` + `LOCKID_LOG_CLEANUP_TIMER` distributed lock → `DoLogCleanupEvent` handler; plus the manual `clear-history` CLI |
| ➕ | One `PeriodicTask` on the manager's **`LeaderCron`**, a single global cadence that processes every enabled policy each tick; batched deletes |

### 2.4 Admin surface

| | Item |
|---|---|
| ✅ | none — edit etcd or run the CLI by hand |
| ➕ | **super-admin** v2 GraphQL + REST CRUD over `retention_policies`, authorized by a `UserRole.SUPERADMIN` role gate (not RBAC scope resolution) |

### 2.5 CLI & space reclaim

| | Item |
|---|---|
| ✅ | `clear-history` deletes terminated sessions/kernels + `error_logs` + Redis stats, then runs `VACUUM` / `VACUUM FULL` |
| ➕ | Recurring deletes move to policies; the CLI is kept as a manual force-sweep + `VACUUM FULL` owner; the sweep relies on autovacuum |

## 3. Implementation Design

**Core flow:** a leader-only periodic task loads the enabled policies → resolves each policy's **category handler** from the code catalog → deletes rows older than `now − retention_period` in **batches** → stamps `last_swept_at`. autovacuum reclaims the freed space.

### (a) Policy storage — `retention_policies`

Retention policies are **data** a super-admin CRUDs per category at runtime, needing audit and querying. Alternatives considered:

| Option | Why not |
|---|---|
| etcd extension (error-retention precedent) | Flat key-value: no efficient enumeration of many categories, no audit, no type validation. Fits one key, not a catalog. |
| **new `retention_policies` DB table (chosen)** | Queryable, audited, standard v2 CRUD. Mirrors the `idle_checkers` precedent (a policy row + a code discriminator). |

(Server config is not an alternative here — server config holds **static operational knobs** like `batch_size` / `sweep_interval`, whereas policies are runtime-admin-CRUD data and belong in a DB table.)

The policy row carries only **tunable knobs**; the referentially-safe delete *procedure* lives in the code catalog (b). This mirrors `idle_checkers` (`checker_type` discriminator + tunable `spec`): here the discriminator is `category`, and the per-category behavior is fixed code.

| Column | Type | Description |
|---|---|---|
| `id` | UUID, PK | Policy identity |
| `category` | string, unique | The data category this policy governs. Stored as a `StrEnum` (`RetentionCategory`) via `StrEnumType` — a string column validated against the code catalog, **not** a native Postgres enum (so a new category is code + a seed row, no `ALTER TYPE` migration). A policy for an unknown category is rejected. |
| `retention_period` | interval | Age threshold: rows older than `now − retention_period` are eligible |
| `enabled` | bool | Whether the sweep processes this policy |
| `last_swept_at` | timestamptz, nullable | **Read-only** observability field — when this policy was last swept (not a gate) |
| `created_at` / `updated_at` | timestamptz | Audit timestamps |

Unique on `category` — one policy per category. Migration seeds one row per catalog category with conservative defaults; admins tune them thereafter. A missing or disabled policy means "never sweep this category."

**The user-facing knobs are reduced to `retention_period` and `enabled`.** Sweep cadence and batch size are **not** policy-row fields; they live in **server config** (manager unified config, `retention` section, not user-facing):

| Server config | Meaning |
|---|---|
| `retention.sweep_interval` | The `PeriodicTask` tick cadence (one global value). Each tick processes every enabled policy |
| `retention.batch_size` | Rows deleted per batch (bounds lock duration) |
| `retention.per_tick_budget` (optional) | Cap on total rows deleted per tick |

- **Why `batch_size` is not a policy field:** it is a performance/safety knob, not a retention decision; letting a user set it to e.g. `1` is a footgun where deletion can never catch up with inflow. → server config / internal constant.
- **Why `sweep_interval` is not per-policy:** sweep cadence is operational tuning, not a per-category retention decision (the only meaningful policy knob is `retention_period`). The task runs on one tick and processes every enabled policy per tick, so no per-policy cadence gate is needed. → a single server config.

### (b) Target catalog — categories & safe-delete procedures

Every retention-eligible table is registered as a **category** in a code catalog binding its table, its **retention-boundary timestamp column**, and its **referentially-safe delete procedure**. The catalog — not the policy row — owns delete safety, because the safe procedure differs by category and is logic, not configuration.

**Boundary-column principle:** the boundary must be the **"last meaningful modification" timestamp**, so a recently-touched row is never purged. **In-place-updated tables use `updated_at`**, append-only tables use `created_at`, and lifecycle tables use the terminal-transition timestamp plus a terminal-status filter.

**Append-only logs — `created_at`** (no inbound FK, never updated):

| Category / table | Boundary | Note |
|---|---|---|
| `event_logs` | `created_at` | append-only, no FKs |
| `audit_logs` | `created_at` | has a `status` transition (running→success) but **no `updated_at` column** → `created_at` is the only boundary |
| `error_logs` | `created_at` | **deletes all rows past the boundary** (no `is_read`/`is_cleared` filter). Has mutable flags but no `updated_at`. Outbound `user` FK only. Generalizes the current etcd timer |
| `login_history` | `created_at` | append-only (a new row per attempt, not a retry update). `(user_id, created_at)` index |

**In-place-updated reconcile/scheduling history — `updated_at`** (rows are merged via `attempts++`; using `created_at` would risk deleting a recently-retried row):

| Category / table | Boundary | Note |
|---|---|---|
| `session_scheduling_history` / `kernel_scheduling_history` | **`updated_at`** | `attempts` merge + `updated_at` onupdate. Parent refs indexed, no FK |
| `deployment_history` / `route_history` / `replica_group_history` | **`updated_at`** | `ReconcileHistoryMixin` (`attempts`, `updated_at` onupdate). No FK |

**Lifecycle records — terminal state + grace period** (not append-only; ordered deletion):

| Category | Table(s) | Terminal signal | Safe-delete procedure |
|---|---|---|---|
| `terminated_sessions` | `sessions` (+ `kernels`) | session `status ∈ DEAD_SESSION_STATUSES {TERMINATED, CANCELLED}` + `terminated_at`; kernel `status ∈ DEAD_KERNEL_STATUSES {TERMINATED, CANCELLED}` + `terminated_at`. Reuse both canonical frozensets (`models/session/row.py`, `models/kernel/row.py`) rather than hard-coding | Delete `kernels` first (`sessions.id` has no cascade from kernels), then `sessions`. `session_dependencies` / `vfolder_attachment` cascade. `routings.session` is `ON DELETE RESTRICT`, so filter to sessions with no surviving routing. Also purge the deleted kernels' Redis statistics (absorbs a `clear-history` duty) |
| `destroyed_endpoints` (deployment) | `endpoints` | `lifecycle_stage = DESTROYED` + `destroyed_at` | Children cascade (`replica_groups`, `routings`, `endpoint_auto_scaling_rules`, `deployment_policies`). FK-less GUID children (`endpoint_tokens`, `deployment_revisions`) are deleted by the handler via endpoint id |

`routings` (`TERMINATED`) and `replica_groups` (`DRAINED`) carry **no dedicated termination timestamp**, so they are not standalone categories — they are purged transitively via the `endpoints` cascade.

**Auxiliary terminal/expiry records** (cleaned once terminal or expired; most have no inbound FK, so a direct batched delete is safe):

| Category | Table | Terminal / expiry signal | Safe delete |
|---|---|---|---|
| `invalidated_login_sessions` | `login_sessions` | `status ∈ {INVALIDATED, REVOKED}` + `invalidated_at` (dedicated) | no inbound FK → direct batched delete |
| `deleted_roles` | `roles` (RBAC) | `status = DELETED` + `deleted_at` (dedicated) | all inbound FKs CASCADE (`user_roles`, `permissions`, `role_invitations`) |
| `resolved_role_invitations` | `role_invitations` | `state ∈ {ACCEPTED, REJECTED, CANCELED}` (no dedicated terminal timestamp → `updated_at` proxy) | no inbound FK |
| `resolved_vfolder_invitations` | `vfolder_invitations` | `state ∈ {ACCEPTED, REJECTED, CANCELED}` (`modified_at` proxy) | no inbound FK |
| `expired_endpoint_tokens` | `endpoint_tokens` | `expires_at < now` (no terminal enum, expiry-based) | no inbound FK; the endpoint link is unconstrained, so these orphan easily |

> **Proxy-timestamp caveat:** invitations have no dedicated terminal timestamp, so `updated_at` / `modified_at` is used as the grace boundary. Since a row is not updated after entering a terminal state this is approximately safe, but less precise than a dedicated column.

**Deferred / excluded** (Non-goals): `vfolders` (`DELETE_COMPLETE`, `model_cards.vfolder` `RESTRICT` may block), `images` (`DELETED`, no dedicated timestamp → needs a `deleted_at`), `service_catalog` (`DEREGISTERED`, a runtime registry better swept by heartbeat age), `artifacts` (`DELETED`, no timestamp + BA-4383's scope), `artifact_revisions` (`FAILED`/`REJECTED` are retryable, not terminal), `agents` (`kernels.agent` FK has no cascade), `users` / `keypairs` (reversible, no timestamp, wide references).

**Usage / billing — hard delete, long default period:**

| Category | Table(s) | Boundary | Note |
|---|---|---|---|
| `kernel_usage_records` | `kernel_usage_records` | `period_end` | Highest-volume; append-only raw, no FK |
| `usage_buckets` | `domain/project/user_usage_buckets` (+ `usage_bucket_entries`) | `period_end` / `period_start` | `usage_bucket_entries` has no timestamp and no FK — delete entries by the purged bucket ids, then the buckets |

**Default retention seed** (all admin-tunable):

| Category group | Default | Rationale |
|---|---|---|
| All append logs (event / audit / error / login / all scheduling & reconcile history) | **1 year** | Matches the LTS support window |
| Lifecycle (`terminated_sessions`, `destroyed_endpoints`, auxiliary terminal/expiry records) | **1 year** | LTS |
| Usage / billing (`kernel_usage_records`, `usage_buckets`) | **2 years** | Longer for billing reconciliation / compliance |

`error_logs` seeds from the existing etcd value if present (preserving today's 90d), else 1 year.

### (c) Sweep — a LeaderCron periodic task

The sweep runs as one `PeriodicTask` on the manager's **`LeaderCron`**, **not** the `GlobalTimer` + distributed-lock path and **not** a sokovan reconciler.

- **Leadership replaces the distributed lock.** `LeaderCron` runs its tasks only on the elected leader (`ValkeyLeaderElection`), so single-execution is already guaranteed; `LOCKID_LOG_CLEANUP_TIMER` is no longer needed. This is why the sweep does not reuse `GlobalTimer`.
- **Not a reconciler.** Retention has no per-entity convergence, retryable outcomes, or cross-tick state; it is periodic batched deletion. The reconciler pattern (BEP-1054) would be pure overhead.

The tick cadence is the single `retention.sweep_interval`. Each tick: load **every enabled policy** → resolve its catalog handler, compute `threshold = now − retention_period`, delete in `retention.batch_size` batches (chunk by primary key / `LIMIT`) until no older rows remain or `retention.per_tick_budget` is hit → record `last_swept_at` (observability). Whether the task deletes inline or fires a `DoRetentionSweepEvent` for a handler (keeping delete logic in a testable event handler, as `log_cleanup` does) is an implementation choice. Space is reclaimed by **autovacuum**; the sweep never runs `VACUUM`.

**Long-running safety.** Unlike existing LeaderCron tasks, this sweep can run long, but the batched design contains it: (1) each task is a separate asyncio task, so a long sweep blocks neither other leader tasks nor the event loop (async DB I/O yields between batches); (2) per-batch commits mean no long transaction or held locks; (3) no re-entry on the same leader (the next tick waits for `run()` to finish); (4) if leadership is lost mid-run, the old and new leaders may briefly overlap, but deletes are idempotent so this is harmless. Bounding each run with `retention.per_tick_budget` spreads the backlog across ticks so no single run is long (useful for the initial backlog).

### (d) Admin API — super-admin v2 CRUD

`retention_policies` is a v2 entity exposed through the full stack (REST v2 + Strawberry GraphQL + shared adapter + SDK v2 + CLI v2), **super-admin only**, with the standard 6 operations. `category` is validated against the catalog on create/update. Because the category set is fixed by the catalog, the common operation is `update` (tune period / enable) on seeded rows; reads expose `last_swept_at` for sweep visibility.

**Authorization is a super-admin role gate, not RBAC scope resolution.** `retention_policies` is a global singleton config belonging to no scope (domain/project/user), and the RBAC scope hierarchy has already deprecated `ScopeType.GLOBAL` / `GLOBAL_SCOPE_ID` (nothing to delegate over a scope). So this entity is **not registered as an RBAC `EntityType`/`ScopeType` and is not wired into virtual scope**; it is authorized by a `UserRole.SUPERADMIN` role gate, the same as other global super-admin-only operations (resource policy/preset mutations, agent search). With no scope, the service layer has no scope resolution / scope-entity-combination burden — no entry is added to the RBAC `scope_entity_combinations`.

### (e) `clear-history` CLI — absorb recurring, keep the escape hatch

| Responsibility | New home |
|---|---|
| Recurring `error_logs` deletion (old etcd timer) | `error_logs` policy — auto-swept; the `GlobalTimer` + `DoLogCleanupEvent` path is retired and the etcd value is absorbed as its seed |
| Recurring terminated session/kernel + Redis-stat deletion | `terminated_sessions` policy — auto-swept, Redis stats included |
| One-shot forced cleanup | CLI retained — trigger an immediate sweep of a category |
| `VACUUM` / `VACUUM FULL` | CLI retained — the disruptive reclaim the automated sweep never runs |

The CLI is **not removed**; it becomes a manual escape hatch over the automated policy layer.

### (f) Migration / Compatibility

- New table `retention_policies`, seeded one row per catalog category with the defaults above.
- Retire the `error_logs` `GlobalTimer` dependency and `DoLogCleanupEvent` handler; free `LOCKID_LOG_CLEANUP_TIMER`. The etcd key is read once to seed, then no longer consulted.
- No breaking change to the `clear-history` CLI surface; its recurring role is superseded but the command still runs.

## 4. Decision Summary

| Decision | Content |
|---|---|
| Storage | New `retention_policies` DB table (not etcd) — policies are runtime admin-CRUD data needing query/audit/standard v2 CRUD; mirrors `idle_checkers` |
| Keying | One flat table keyed by `category` — one global policy per category |
| Scope | **Per-scope (project/domain/user) is a non-goal** — system-wide cleanup, per-category global policies. Slurm keeps purge global too; a future extension can add scope |
| Knob/code split | Tunable knobs on the policy row; the referentially-safe delete procedure in a code catalog per category |
| Boundary column | "Last meaningful modification": in-place-updated (reconcile/scheduling history `attempts++`) → `updated_at`, append-only (event/audit/error/login) → `created_at`, lifecycle → terminal-transition timestamp (`terminated_at` / `destroyed_at`) + terminal status. audit/error are updated but lack an `updated_at` column, so `created_at` |
| Lifecycle coverage | Terminated sessions/kernels + destroyed endpoints (deployments) + auxiliary terminal/expiry records (login_sessions, roles, role/vfolder invitations, endpoint_tokens); routings/replica_groups purge transitively via endpoint cascade |
| Sweep | A `LeaderCron` `PeriodicTask` — not `GlobalTimer`+lock (leadership guarantees single execution), not a reconciler (no convergence state) |
| Policy knobs | User-facing knobs are `retention_period` / `enabled` only. `sweep_interval` / `batch_size` are server config (`retention.*`), not policy fields — avoids a user footgun (batch=1) and treats cadence as operational tuning. `last_swept_at` is read-only observability |
| Defaults | Logs & lifecycle **1 year (LTS)**; usage/billing **2 years**; all admin-tunable |
| Billing | Hard delete with a long default period — not soft-delete/archive |
| Space reclaim | Automated sweep never runs `VACUUM`; `VACUUM FULL` stays in the CLI (autovacuum reclaims dead tuples) |
| CLI | Recurring duties absorbed; retained as a manual force-sweep + `VACUUM FULL` owner |
| Authorization | `UserRole.SUPERADMIN` role gate — not registered as an RBAC `EntityType`/`ScopeType`, not wired into virtual scope. A global singleton config has no scope to attach to (consistent with `GLOBAL` scope's deprecation); no service-layer scope-resolution burden |

## 5. Open Questions

- First-class treatment of global super-admin-only actions in the RBAC action framework — split into a **separate issue** at the RBAC-framework level (this BEP uses the existing `UserRole.SUPERADMIN` gate, non-blocking).
- Concrete server-config defaults (`retention.sweep_interval`, `retention.batch_size`, `retention.per_tick_budget`) — settled at implementation.

## 6. References

- `dependencies/processing/log_cleanup_timer.py`, `event_dispatcher/handlers/log_cleanup.py`, `cli/__main__.py::clear_history`
- `common/leader/tasks/leader_cron.py`, `dependencies/orchestration/leader_election.py`
- `models/idle_checker/row.py` (policy row + code discriminator precedent), `models/endpoint/row.py` (`destroyed_at` / `lifecycle_stage`)
- Prior art: Slurm `slurmdbd.conf` `Purge*After` / `Archive*` — per-category, global purge ([docs](https://slurm.schedmd.com/slurmdbd.conf.html))
- [BEP-1054](BEP-1054-reconciler-based-idle-checker.md) (reconciler idle checker)
