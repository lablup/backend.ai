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

This BEP defines a **general-purpose retention layer**: a super-admin declares a retention period **per data category**, and the manager periodically purges records older than that period, batched and referentially safe. The purpose is **system-level cleanup of DB records that accumulate indefinitely**.

**Non-goals:**

- **Per-scope (project/domain/user) retention.** The purpose is system-wide cleanup; policies apply **globally per category**. There is no current per-scope requirement, and mature schedulers keep purge global too (Slurm `slurmdbd.conf` `Purge*After` are all per-`slurmdbd`, not per-account). A future extension can add scope if a concrete need arises.
- **Soft-delete / archive.** Every category hard-deletes; a long default period, not archival, protects billing data.
- **Redis / non-DB store cleanup.** This BEP covers **DB records only**. Redis statistics and other non-DB stores are a separate concern and out of scope (the existing CLI keeps handling them).
- Artifact/object-storage retention (BA-4383) and docker image GC (BA-3037) — different substrates, tracked separately.
- **Cleanup of `vfolders` / `images` / `service_catalog` / `artifacts`** — each differs (no dedicated timestamp, a blocking `RESTRICT` FK, a runtime registry better swept by heartbeat age, or a separate epic) — out of scope here, handled separately.
- **`VACUUM FULL` automation** — it locks the table and stays a manual CLI operation.

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 2.1 Policy storage

| | Item |
|---|---|
| ✅ | `error_logs` retention is a single etcd key `config/logs/error/retention` (default 90d) |
| ➕ | `retention_policies` DB table, **one row per category** — retention period + enable (sweep cadence & batch size live in server config) |

### 2.2 Target coverage (catalog)

| | Item |
|---|---|
| ✅ | `error_logs` (timer) + terminated sessions/kernels & `error_logs` (CLI) |
| ➕ | Eight domain **categories** (`logs`/`login`/`reconcile_history`/`roles_invitations`/`deployments`/`sessions`/`usage_records`/`usage_buckets`), each with a referentially-safe delete procedure encoded in code |

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
| ➕ | Recurring DB deletes move to policies; the CLI is kept as a manual force-sweep + `VACUUM FULL` owner; the sweep relies on autovacuum |

## 3. Implementation Design

**Core flow:** a leader-only periodic task loads the enabled policies → resolves each policy's **category** delete via the repository → deletes rows older than `now − retention_period` in **batches, committed per batch** → stamps `last_swept_at`. autovacuum reclaims the freed space.

### (a) Policy storage — `retention_policies`

Retention policies are **data** a super-admin CRUDs per category at runtime, needing audit and querying. Alternatives considered:

| Option | Why not |
|---|---|
| etcd extension (error-retention precedent) | Flat key-value: no efficient enumeration of many categories, no audit, no type validation. Fits one key, not a catalog. |
| **new `retention_policies` DB table (chosen)** | Queryable, audited, standard v2 CRUD |

(Server config is not an alternative here — it holds **static operational knobs** like `batch_size` / `sweep_interval`, whereas policies are runtime-admin-CRUD data.)

This design is about **defining, per domain category, how its tables are cleaned up**. The cleanup method (boundary column + referentially-safe delete procedure) is **fixed in code by the nature of each table** (b); the policy row carries only the admin-tunable values (`retention_period`, `enabled`). `category` is just the **identifier** linking a policy row to its code-side cleanup — not an extensible discriminator/spec abstraction (unrelated to the idle-checker mechanism).

| Column | Type | Description |
|---|---|---|
| `id` | UUID, PK | Policy identity |
| `category` | string, unique | Cleanup-target identifier (a `RetentionCategory` enum value, stored as a string), validated against the code catalog; an unknown category is rejected. The enum carries no table references |
| `retention_period` | interval | Age threshold: rows older than `now − retention_period` are eligible |
| `enabled` | bool | Whether the sweep processes this policy |
| `last_swept_at` | timestamptz, nullable | **Read-only** observability field — when this policy was last swept (not a gate) |
| `created_at` / `updated_at` | timestamptz | Audit timestamps |

Unique on `category` — one policy per category. Migration seeds one row per catalog category with conservative defaults; admins tune them thereafter. A missing or disabled policy means "never sweep this category."

**The user-facing knobs are reduced to `retention_period` and `enabled`.** Sweep cadence and batch size live in **server config** (manager unified config, `retention` section, not user-facing):

| Server config | Meaning |
|---|---|
| `retention.sweep_interval` | The `PeriodicTask` tick cadence (one global value). Each tick processes every enabled policy |
| `retention.batch_size` | Rows deleted per batch (bounds lock duration) |
| `retention.per_tick_budget` (optional) | Cap on total rows deleted per tick |

- **Why `batch_size` is not a policy field:** it is a performance/safety knob, not a retention decision; letting a user set it to e.g. `1` is a footgun where deletion can never catch up. → server config.
- **Why `sweep_interval` is not per-policy:** sweep cadence is operational tuning, not a per-category retention decision (the only meaningful policy knob is `retention_period`). The task runs on one tick and processes every enabled policy per tick, so no per-policy gate is needed. → a single server config.

### (b) Target catalog — domain categories & safe delete

Retention targets are grouped into **domain categories**; each category's cleanup method (boundary column + referentially-safe delete procedure) is **fixed in code**, driven by table nature, and the policy row carries only `retention_period` / `enabled`. A category may span several tables: tables sharing a boundary column are handled together via a **mixin**; tables with different boundaries share the category but each provides its own spec (they share the `retention_period`).

**Boundary-column principle:** the boundary must be the **"last meaningful modification" timestamp**, so a recently-touched row is never purged — in-place-updated tables use `updated_at`, append-only use `created_at`, lifecycle records use the terminal-transition timestamp (`terminated_at` / `destroyed_at` / `invalidated_at` / `expires_at`) plus a terminal-status filter.

**category naming:** the identifier is user-facing (super-admin API), so it uses the external domain name (physical table `endpoints` → the `deployments` domain).

**The eight categories:**

| Category | Tables | Boundary | Default | Handling |
|---|---|---|---|---|
| `logs` | `event_logs`, `audit_logs`, `error_logs` | `created_at` | 1yr | common-column mixin (group). `error_logs` deletes all rows past the boundary |
| `login` | `login_history`, `login_sessions` | login_history `created_at`; login_sessions `invalidated_at` + `{INVALIDATED, REVOKED}` | 1yr | domain group, per-table spec |
| `reconcile_history` | `session_scheduling_history`, `kernel_scheduling_history`, `deployment_history`, `route_history`, `replica_group_history` | `updated_at` (`attempts++` merge) | 1yr | common-column mixin (group) |
| `roles_invitations` | `roles`, `role_invitations`, `vfolder_invitations` | roles `deleted_at`+`DELETED`; invitations terminal state + `updated_at`/`modified_at` (proxy) | 1yr | domain group (invitations unified), per-table spec |
| `deployments` | `endpoints` (destroyed), `endpoint_tokens` (expired) | endpoints `DESTROYED`+`destroyed_at`; tokens `expires_at` | 1yr | domain group; endpoints bespoke, tokens simple |
| `sessions` | `sessions` (+ `kernels`) | session/kernel `DEAD_*_STATUSES {TERMINATED, CANCELLED}` + `terminated_at` | 1yr | bespoke (ordered delete) |
| `usage_records` | `kernel_usage_records` | `period_end` | **90d** | simple; raw records aggregated into buckets, so kept briefly |
| `usage_buckets` | `domain/project/user_usage_buckets` (+ `usage_bucket_entries`) | `period_end` | 2yr | bespoke (entries → buckets) |

**Bespoke procedures:**

- `sessions`: delete `kernels` first (`sessions.id` has no cascade from kernels) → `sessions`. `session_dependencies` / `vfolder_attachment` cascade. `routings.session` is `ON DELETE RESTRICT`, so filter to sessions with no surviving routing. Reuse the canonical `DEAD_SESSION_STATUSES` / `DEAD_KERNEL_STATUSES` frozensets (`models/session/row.py`, `models/kernel/row.py`).
- `deployments` (endpoints): children cascade (`replica_groups`, `routings`, `endpoint_auto_scaling_rules`, `deployment_policies`). FK-less GUID children (`deployment_revisions`) are deleted by endpoint id. `routings` (`TERMINATED`) / `replica_groups` (`DRAINED`) have no termination timestamp, so they purge transitively via the endpoint cascade. `endpoint_tokens` is cleaned in the same category by `expires_at`.
- `usage_buckets`: `usage_bucket_entries` has no timestamp and no FK — delete entries by the purged bucket ids, then the buckets.

**Proxy-timestamp caveat:** role/vfolder invitations have no dedicated terminal timestamp, so `updated_at` / `modified_at` is the grace boundary — approximately safe (no updates after the terminal state) but less precise.

**Deferred / excluded** (Non-goals): `vfolders` (`DELETE_COMPLETE`, `model_cards.vfolder` `RESTRICT` may block), `images` (`DELETED`, no dedicated timestamp → needs `deleted_at`), `service_catalog` (`DEREGISTERED`, better swept by heartbeat age), `artifacts` (`DELETED`, BA-4383's scope), `artifact_revisions` (`FAILED`/`REJECTED` are retryable), `agents` (`kernels.agent` FK has no cascade), `users` / `keypairs` (reversible, wide references).

**Default retention seed** (all admin-tunable):

| Category | Default | Rationale |
|---|---|---|
| `logs`, `login`, `reconcile_history`, `roles_invitations`, `deployments`, `sessions` | **1 year** | LTS support window |
| `usage_records` | **90 days** | raw records are aggregated into buckets, so kept briefly |
| `usage_buckets` | **2 years** | billing reconciliation / compliance |

### (c) Sweep — a LeaderCron periodic task

The sweep runs as one `PeriodicTask` on the manager's **`LeaderCron`**, **not** the `GlobalTimer` + distributed-lock path and **not** a sokovan reconciler.

- **Leadership replaces the distributed lock.** `LeaderCron` runs its tasks only on the elected leader (`ValkeyLeaderElection`), so single-execution is guaranteed; `LOCKID_LOG_CLEANUP_TIMER` is no longer needed.
- **Not a reconciler.** Retention has no per-entity convergence, retryable outcomes, or cross-tick state; it is periodic batched deletion.

Each tick processes **every enabled policy**, computing `threshold = now − retention_period` per category and deleting older rows in `retention.batch_size` chunks up to `retention.per_tick_budget`, then stamps `last_swept_at`.

**Deletion semantics (implementation contract):** deletes go through the repository's batch-purge over the shared write-ops (the existing `BatchPurger` framework), never raw SQL at the wiring site; the `category → tables` mapping lives inside the single retention repository (no module global), with common-column tables sharing a mixin and multi-table categories running ordered purges. Deletion is **chunk-based (delete-and-advance)**, not pagination — deleted rows leave the predicate set, so each chunk of `batch_size` naturally advances with no cursor/offset. Each chunk is **committed as its own transaction** (short locks, resumable, honoring `per_tick_budget`); a multi-table category's related deletes for one batch are atomic within that transaction; different categories run in independent transactions. autovacuum reclaims space; the sweep never runs `VACUUM`.

**Long-running safety.** Unlike existing LeaderCron tasks this sweep can run long, but the batched design contains it: separate asyncio task (no event-loop/other-task blocking), per-batch commits (no long transaction), no same-leader re-entry, and idempotent deletes (a mid-run leadership change causes at most harmless overlap). `per_tick_budget` spreads the backlog across ticks so no single run is long.

### (d) Admin API — super-admin v2 CRUD

`retention_policies` is a v2 entity exposed through the full stack (REST v2 + Strawberry GraphQL + shared adapter + SDK v2 + CLI v2), **super-admin only**, with the standard 6 operations. `category` is validated against the catalog. Since the category set is fixed, the common operation is `update` (tune period / enable) on seeded rows; reads expose `last_swept_at`.

**Authorization is a super-admin role gate, not RBAC scope resolution.** `retention_policies` is a global singleton config belonging to no scope, and the RBAC scope hierarchy has deprecated `ScopeType.GLOBAL` / `GLOBAL_SCOPE_ID`. So this entity is **not registered as an RBAC `EntityType`/`ScopeType` and is not wired into virtual scope**; it is authorized by a `UserRole.SUPERADMIN` role gate, the same as other global super-admin-only operations (resource policy/preset mutations, agent search). With no scope, the service layer has no scope-resolution burden and no `scope_entity_combinations` entry.

### (e) `clear-history` CLI — absorb recurring, keep the escape hatch

| Responsibility | New home |
|---|---|
| Recurring `error_logs` deletion (old etcd timer) | `logs` policy (incl. error_logs) — auto-swept; the `GlobalTimer` + `DoLogCleanupEvent` path and the etcd key are retired (default 1yr) |
| Recurring terminated session/kernel **DB** deletion | `sessions` policy — auto-swept (DB records only) |
| Terminated-kernel Redis-stat deletion | **out of scope** (DB-only) — Redis is a separate store; the CLI keeps handling it |
| One-shot forced cleanup | CLI retained — trigger an immediate sweep of a category |
| `VACUUM` / `VACUUM FULL` | CLI retained — the disruptive reclaim the automated sweep never runs |

The CLI is **not removed**; it becomes a manual escape hatch over the automated policy layer.

### (f) Migration / Compatibility

- New table `retention_policies`, seeded one row per catalog category with the defaults above.
- Retire the `error_logs` `GlobalTimer` dependency and `DoLogCleanupEvent` handler; free `LOCKID_LOG_CLEANUP_TIMER`. Retire the etcd key `config/logs/error/retention` (`error_logs` defaults to 1yr under the `logs` category).
- No breaking change to the `clear-history` CLI surface; its recurring DB role is superseded but the command still runs.

## 4. Decision Summary

| Decision | Content |
|---|---|
| Storage | New `retention_policies` DB table (not etcd) — policies are runtime admin-CRUD data needing query/audit/standard v2 CRUD |
| Keying | One flat table keyed by `category` — one global policy per category |
| Scope | **Per-scope (project/domain/user) is a non-goal** — system-wide cleanup, per-category global policies. Slurm keeps purge global too |
| Logic location | Admin-tunable `retention_period` / `enabled` on the policy row; boundary column + delete procedure are **fixed code by table nature** (not an extensible discriminator/spec abstraction) |
| Categories | Eight by domain: `logs`, `login`, `reconcile_history`, `roles_invitations`, `deployments`, `sessions`, `usage_records`, `usage_buckets`. Common-column tables share a mixin; the rest use per-table specs under a shared `retention_period` |
| Boundary column | "Last meaningful modification": in-place → `updated_at`, append-only → `created_at`, lifecycle → terminal-transition timestamp + terminal status. audit/error lack `updated_at`, so `created_at` |
| Sweep | A `LeaderCron` `PeriodicTask` — not `GlobalTimer`+lock (leadership guarantees single execution), not a reconciler. Chunk-based (delete-and-advance) via repository `BatchPurger`, committed per batch; categories in independent transactions |
| Policy knobs | User-facing knobs are `retention_period` / `enabled` only. `sweep_interval` / `batch_size` are server config — avoids a footgun (batch=1). `last_swept_at` is read-only observability |
| Defaults | Most **1 year (LTS)**; `usage_records` **90 days** (raw, aggregated into buckets); `usage_buckets` **2 years**; all admin-tunable |
| Scope of stores | **DB records only** — Redis / non-DB cleanup is out of scope (stays with the CLI) |
| Billing | Hard delete with a long default period — not soft-delete/archive |
| Space reclaim | Automated sweep never runs `VACUUM`; `VACUUM FULL` stays in the CLI |
| Authorization | `UserRole.SUPERADMIN` role gate — not an RBAC `EntityType`/`ScopeType`, not wired into virtual scope. A global singleton config has no scope to attach to |

## 5. Open Questions

- First-class treatment of global super-admin-only actions in the RBAC action framework — split into a **separate issue** at the RBAC-framework level (this BEP uses the existing `UserRole.SUPERADMIN` gate, non-blocking).
- Concrete server-config defaults (`retention.sweep_interval`, `retention.batch_size`, `retention.per_tick_budget`) — settled at implementation.

## 6. References

- `dependencies/processing/log_cleanup_timer.py`, `event_dispatcher/handlers/log_cleanup.py`, `cli/__main__.py::clear_history`
- `common/leader/tasks/leader_cron.py`, `dependencies/orchestration/leader_election.py`
- `repositories/base/purger.py` (`BatchPurger`), `repositories/ops/base/provider.py` (`WriteOps.batch_purge`)
- `models/endpoint/row.py` (`destroyed_at` / `lifecycle_stage`), `models/session/row.py` & `models/kernel/row.py` (`DEAD_*_STATUSES`)
- Prior art: Slurm `slurmdbd.conf` `Purge*After` / `Archive*` — per-category, global purge ([docs](https://slurm.schedmd.com/slurmdbd.conf.html))
- [BEP-1054](BEP-1054-reconciler-based-idle-checker.md) (reconciler idle checker)
