---
Author: BoKeum Kim (bkkim@lablup.com)
Status: Draft
Created: 2026-06-17
Created-Version:
Target-Version:
Implemented-Version:
---

# BEP-1054: Reconciler-Based Idle Checker

## Motivation

Backend.AI Manager's idle checker currently lives in `manager/idle.py`, driven by a dedicated `IdleCheckerHost` and `GlobalTimer`. As scheduling, deployment, and routing move onto the sokovan coordinator/reconciler pattern, idle checking is left behind on a separate timer and event path, with several structural problems:

1. **Detached from the sokovan lifecycle.** Idle checking runs on its own timer and `DoIdleCheckEvent` wiring instead of the generic reconciler flow the rest of the lifecycle is converging on.
2. **The idle checker is not a first-class object.** A checker today is a Python class plus config keys. There is no way to define one checker spec (e.g. "GPU under-utilized for 30 minutes") and reuse it across multiple domains, projects, or resource groups.
3. **Configuration is scattered.** Global config lives in `config.idle`, per-keypair values in the keypair resource policy, and runtime/report state in Valkey. Which setting applies to which session is hard to trace.
4. **Judgment, I/O, and reporting are entangled.** Checkers read Valkey, accumulate cross-tick state, and write reports inline, which makes them hard to test and extend.
5. **Utilization is tied to the legacy live-stat shape.** Utilization idle should be derivable from agent-emitted Prometheus metrics aggregated over a window.

This proposal re-homes idle checking onto a sokovan reconciler stage and promotes the idle checker to a reusable DB object. Each scope applies a checker through a separate association row.

### Goals

- Run idle checking as **two sokovan reconciler stages** — a deadline-refresh stage and an expiry-sweep stage — on the generic Source → Handler → Applier flow.
- Model the idle checker as a first-class, reusable DB object that is independent of any scope.
- Express scope application (domain / project / resource group) through a dedicated association table.
- Drive utilization decisions from agent-emitted Prometheus metrics.
- Keep checker I/O and judgment behind one batched per-type contract and keep reporting outside the checker; persist each check's projected cleanup time to the database (not Valkey) as the single source for both the sweep decision and client-facing reporting.
- Expose when a session is scheduled to be cleaned up — per checker and as a session-level aggregate — replacing the Valkey remaining-time report.

### Non-Goals

- The concrete judgment rules of each checker (timeout math, threshold comparison, metric names) are implementation concerns and are out of scope.
- Backfilling or falling back to legacy keypair resource-policy idle settings is out of scope. Reconciler-based idle checkers use only their own specs.

## Current Design

Idle checking runs as `IdleCheckerHost.start()` → `GlobalTimer` → `DoIdleCheckEvent` → `do_idle_check()`. Each tick reads live kernel/session rows, excludes inference sessions, loads keypair resource policies per access key, and runs every registered checker against each session; if any checker reports idle, a terminate event is emitted.

Two properties matter for this proposal:

- **Session-first iteration.** The host reads sessions and runs all checkers against each one. It does not start from checker definitions.
- **Checkers are code, not data.** A checker is a class plus config, not a DB-identifiable spec. Configuration is spread across `config.idle`, the keypair resource policy, and Valkey live/stat state.

### Limitations

- A checker spec has no DB identity and cannot be reused across scopes.
- There is no place to express per-binding enable/disable.
- Per-checker config shape is not validated at a single boundary.
- Utilization is coupled to the legacy Valkey live-stat shape.
- Report writes happen inline during a tick, coupling judgment with reporting.

## Proposed Design

### Overview

The redesign rests on two ideas:

1. **Idle checking becomes sokovan reconciler stages.** A `Source` gathers what to evaluate, a `Handler` drives each checker's batched I/O and judgment contract, and an `Applier` writes the outcome — the same shape as other reconciler stages. Computing each session's cleanup deadline and acting on an elapsed deadline are split into two such stages (see *Reconciler Stages*).
2. **The idle checker becomes a first-class DB object.** A checker is a reusable, scope-agnostic spec. Whether and where it applies is expressed by separate association rows that bind it to a domain, project, or resource group.

### Data Model

Three tables. The checker carries no scope of its own; the association table carries the entire scope relationship; and a per-session result table records when each applied checker will next clean the session up.

#### `idle_checkers` — the reusable checker spec

| Column | Type | Description |
|---|---|---|
| `id` | UUID, PK | Identity of the reusable checker |
| `name` | string | Human-readable name |
| `description` | string, nullable | Optional description |
| `checker_type` | string | `session_lifetime` / `network_timeout` / `utilization` |
| `spec` | JSONB | Checker-type-specific configuration payload |
| `created_at` / `modified_at` | timestamptz | |

The checker is intentionally **scope-free** — it carries no `owner_scope_*` columns. A checker is a definition that can be bound to any number of scopes; making it scope-agnostic is exactly what lets one spec be reused everywhere. `checker_type` is a top-level column (for search and validation) and the `spec` payload is interpreted according to it.

#### `idle_checker_bindings` — the scope ↔ checker association

| Column | Type | Description |
|---|---|---|
| `id` | UUID, PK | |
| `scope_type` | string | `domain` / `project` / `resource_group` |
| `scope_id` | string | Domain name / project id / resource group name |
| `idle_checker_id` | UUID, FK → `idle_checkers.id` | The bound checker |
| `enabled` | bool | Whether this binding participates |
| `created_at` / `modified_at` | timestamptz | |

A binding is one `(scope_type, scope_id) → idle_checker` edge. **This association table — not a column on the checker — is the single place that expresses "this checker applies at this scope."** Keeping the relationship separate is what makes the checker a true first-class object: the same checker may be bound to many scopes, a scope may bind many checkers, and each binding carries its own `enabled` flag.

A dedicated association table (rather than reusing the RBAC `association_scopes_entities`) is chosen because idle application needs its own `enabled` flag and future binding-level metadata (e.g. priority), and because idle application semantics should not be conflated with RBAC permission semantics.

#### `session_idle_checks` — per-session projected cleanup time

The deadline-refresh stage records, for each running session and each checker applied to it, **when that checker would next clean the session up**. This is the value the sweep stage acts on and the value clients read.

| Column | Type | Description |
|---|---|---|
| `session_id` | UUID, FK → `sessions.id` (ON DELETE CASCADE) | The evaluated session |
| `idle_checker_id` | UUID, FK → `idle_checkers.id` (ON DELETE CASCADE) | The checker that produced this deadline |
| `expire_at` | timestamptz, nullable | When the session is scheduled to be cleaned up by this checker. `NULL` while the checker is in a grace period or cannot yet determine a deadline |
| `updated_at` | timestamptz | Last refresh |

Primary key `(session_id, idle_checker_id)` — one row per session × applied checker. `expire_at` is the **projected cleanup time, not a termination timestamp**: it is a future point (or just past, once due) at which the checker's condition elapses; the sweep stage — not this row — performs the actual `TERMINATING` transition. The FK to `idle_checkers` ties each deadline back to the checker that owns it, so a `SessionIdleCheck` node can name its checker and a deleted checker's rows are removed by cascade.

#### Scope-ID convention

| `scope_type` | `scope_id` |
|---|---|
| `domain` | domain name |
| `project` | project id |
| `resource_group` | resource group (scaling group) name |

`scope_id` is a polymorphic string key. Scope existence is validated on the write path rather than by a DB-level foreign key.

#### ERD

```mermaid
erDiagram
    IDLE_CHECKERS {
        uuid id PK
        string name UK
        string checker_type
        jsonb spec
    }
    IDLE_CHECKER_BINDINGS {
        uuid id PK
        string scope_type
        string scope_id
        uuid idle_checker_id FK
        boolean enabled
    }
    SESSION_IDLE_CHECKS {
        uuid session_id FK
        uuid idle_checker_id FK
        timestamptz expire_at
    }
    DOMAINS { string name PK }
    GROUPS { uuid id PK }
    SCALING_GROUPS { string name PK }
    SESSIONS { uuid id PK }

    IDLE_CHECKERS ||--o{ IDLE_CHECKER_BINDINGS : referenced_by
    DOMAINS ||--o{ IDLE_CHECKER_BINDINGS : scope_domain
    GROUPS ||--o{ IDLE_CHECKER_BINDINGS : scope_project
    SCALING_GROUPS ||--o{ IDLE_CHECKER_BINDINGS : scope_resource_group
    IDLE_CHECKERS ||--o{ SESSION_IDLE_CHECKS : produced_deadline
    SESSIONS ||--o{ SESSION_IDLE_CHECKS : has_deadline
```

### Checker Spec Model

The `spec` column is **not free-form JSON** — it holds a typed, polymorphic payload whose shape is fixed by the row's `checker_type`. Two layers express this:

- **`ABCColumn` — a generic, reusable polymorphic JSONB column.** It is not idle-specific: it persists any value that satisfies a load/write contract (JSONB dict ↔ typed object) and rehydrates the typed object on read. Idle checking is its first user, but the column type is meant to back any table that stores polymorphic, validated config.
- **`IdleCheckerABC` — the idle-specific payload the column carries.** On load it dispatches by the `checker_type` discriminator to the concrete spec (`session_lifetime` / `network_timeout` / `utilization`), and it declares the behavior contract every checker implements: how it batch-loads runtime signals and renders judgments for its assignments, each judgment carrying the projected `expire_at` for that session.

Conceptually (the contract only — bodies are an implementation concern):

```text
ABCColumnPayload                  # storage contract ABCColumn speaks to
  load(raw)  -> payload           # JSONB dict   -> typed object
  write()    -> raw               # typed object -> JSONB dict

IdleCheckerABC(ABCColumnPayload)  # the value stored in idle_checkers.spec
  load(raw)  -> concrete spec     # dispatch by checker_type discriminator
  judge(assignments) -> judgments  # batched I/O -> projected expire_at per assignment
```

This buys three things:

- **One validation boundary.** Unknown or malformed specs are rejected at load, so an `idle_checkers` row can never hold a payload its `checker_type` cannot interpret.
- **Config lives with its checker.** Each `checker_type` owns its own spec fields instead of a shared column shape every checker must understand.
- **Extensible without schema change.** A new `checker_type` adds a new `IdleCheckerABC` subtype; the table and column are untouched.

`judge` is the behavioral half of this contract; the orchestration that drives it is described under *Checker-Owned Runtime State* below.

### Reconciler Stages

Idle checking is split into **two reconciler stages** so that computing a deadline — which needs the checkers' batched runtime reads — is separated from acting on an elapsed deadline, a pure time comparison:

**1. Deadline-refresh stage** — recomputes, per running session, when each applied checker would next terminate it, and persists that time.

- **Source** — gathers the sessions to evaluate and the checkers that apply to them (see *Source Fetch Direction*).
- **Handler** — pivots the batch by checker type and invokes each checker's single batched `judge` contract, producing a projected `expire_at` per (session, checker). Checker-owned external reads occur behind this contract; the Handler performs no external I/O beyond it.
- **Applier** — upserts one `session_idle_checks` row per (session, checker) with the computed `expire_at`, and **prunes rows for checkers no longer applicable** to the session (binding removed or disabled). It marks nothing for termination.

**2. Expiry-sweep stage** — terminates sessions whose deadline has already passed.

- **Source** — reads `session_idle_checks` rows with `expire_at <= now`, joined to still-eligible running sessions. No per-resource-group iteration and no checker `judge` call.
- **Handler** — trivial: the rows already are the verdict.
- **Applier** — marks those sessions `TERMINATING` through the existing scheduler termination lifecycle.

Splitting this way keeps termination correct under change: because the refresh stage rewrites `expire_at` every tick from the *current* effective checker set and deletes rows whose checker no longer applies, the sweep never terminates on a checker that would no longer judge the session idle. The one constraint is cadence — a deadline must be refreshed before it elapses, so the refresh interval bounds worst-case late termination (see Open Questions).

### Source Fetch Direction

This describes the **deadline-refresh** stage's Source; the sweep stage instead reads due `session_idle_checks` rows directly (see *Reconciler Stages*). The refresh stage lives on the **generic reconciler** — one fetch per tick, not per resource group. Even so, its Source reads sessions **per resource group**, following the pattern the scheduler coordinator already uses (`ScheduleCoordinator` iterates scaling groups and reads each with `get_sessions_for_handler(scaling_group, …)`).

**Per resource group, the Source:**

1. reads the idle-eligible running sessions with a recorded start time in the group;
2. collects the distinct scopes those sessions belong to — the resource group, their projects, their domains;
3. loads only the enabled `idle_checker_bindings` (with their checker specs) attached to those scopes;
4. composes each session's effective checker set from the bindings on its own scopes.

**Why session-first, per resource group:**

- **Consistent.** Reuses the scheduler coordinator's per-resource-group read shape instead of a new global query. The idle stage does its own read — the generic reconciler has no fetch to literally share — but keeps the same shape.
- **Minimal checker load.** Only checkers bound to scopes that have running sessions are loaded; scopes with none are never consulted.
- **No global scan.** No per-tick scan over all bindings.

**Why not binding-first** — scan every enabled binding, build a combined scope predicate, then fetch sessions across all bound scopes:

- forces a global binding scan on every tick, and
- reads sessions across all bound scopes regardless of where running sessions actually are — departing from the per-resource-group read pattern the scheduler already uses.

### Scope Resolution

Each session maps to exactly three candidate scopes, computed explicitly:

```text
resource_group: the session's resource group
project:        the session's project
domain:         the session's domain
```

RBAC scope-chain traversal is not used: a resource group can be linked to many domains/projects, so following parent relationships could attach checkers unrelated to the session.

A session's **effective checkers** are the union of enabled bindings attached to its resource group, its project, and its domain. The handler evaluates every implemented checker, and each yields its own `expire_at` for the session, persisted as a separate `session_idle_checks` row. The earliest of those deadlines governs when the session is swept, so one session still yields at most one termination.

#### Matching across scopes

Because a session belongs to three scopes at once and each scope may carry several bindings, three matching cases arise. All three reduce to one rule: **take the union, de-duplicate by checker, evaluate every checker, and record each one's `expire_at` as its own row.**

- **Different checkers across scopes.** A `network_timeout` bound at the domain, a `utilization` at the project, and another checker at the resource group all apply; the effective set is their union and every checker contributes its own `expire_at` row.
- **The same checker reachable from multiple scopes.** One `idle_checker_id` may be bound at both the session's domain and its project. It resolves to a **single** effective checker, de-duplicated by checker id and evaluated once for that session.
- **Multiple checkers bound to one scope.** A single scope (e.g. one resource group) may carry many bindings, each its own row with its own `enabled` flag; all enabled checkers participate. Multiple definitions of the same `checker_type` are batched into one implementation call.

A binding with `enabled = false` is dropped from the union before any of this, so a disabled binding never contributes a checker.

### Checker-Owned Runtime State

The Source does not branch centrally on checker type to read Valkey or Prometheus. The Handler groups assignments by checker type and calls each implementation once per tick. Each checker owns its batched external reads and internal judgment material; the public contract exposes only assignments and judgments. This keeps query shapes inside the checker without exposing preparer state to the orchestration layer.

### Checker Types

| `checker_type` | Terminates when… | Runtime signal |
|---|---|---|
| `session_lifetime` | a started session has run longer than its maximum lifetime; zero disables the definition | none (session start time) |
| `network_timeout` | an interactive session has had no access and no active connections beyond a timeout | last-access / active-connection signals |
| `utilization` | a session's resource utilization stays below thresholds across a window, after a grace period | windowed utilization metrics |

The exact judgment rules for each checker are an implementation concern and are intentionally not specified here. A single scope can bind multiple checkers of the same `checker_type`.

Checker specs are the sole configuration source for reconciler-based idle decisions. The Source and checker implementations do not read `keypair_resource_policies.idle_timeout` or `keypair_resource_policies.max_session_lifetime`, and those legacy values are neither fallback values nor implicit defaults. Whether a checker applies is controlled only by its scope bindings; its threshold or lifetime is controlled only by its spec.

### Utilization via Prometheus

Utilization is evaluated from agent-emitted Prometheus metrics aggregated over a window, not from the legacy Valkey live-stat shape. The concrete metric names and label sets are settled together with the agent metric design. This decouples utilization judgment from the legacy stat-accumulation path and lets it evolve with the metric pipeline.

### Termination Handling

The **sweep** stage's Applier does not kill containers or perform the final `TERMINATED` transition. It marks expired sessions as `TERMINATING` through the existing scheduler termination lifecycle, which is idempotent for sessions already terminating or terminal. The existing session scheduler coordinator then reads `TERMINATING` sessions per resource group and drives agent termination as it does today.

The generic reconciler's per-entity retry/history classification (`decisions()`) is intentionally unused in both stages: neither a set of `expire_at` upserts nor a list of expired sessions is a set of retryable per-entity outcomes. Both stages leave the classification path empty.

### Deadline Persistence & Reporting

Each check's projected cleanup time is stored in `session_idle_checks.expire_at` as an **absolute timestamp**, not a countdown. Remaining time is derived on read as `expire_at - now` (negative once past due). Storing the absolute time means a value is written only when it actually changes, needs no per-tick rewrite to "tick down", and never drifts between refresh ticks.

This DB-backed report **replaces the Valkey remaining-time report** previously published per checker under `session.{session_id}.idle_checker.{checker_id}.remaining`. That Valkey path and `IdleCheckerHost.get_idle_check_report` are retired; `session_idle_checks` is the single source for both the sweep decision and client-facing remaining time.

### GraphQL Exposure

`session_idle_checks` is exposed so clients can read a session-level aggregate and drill into each checker's contribution:

- **`SessionIdleCheck` node** — one per `session_idle_checks` row: the bound `idle_checker` (id / name / `checker_type`), `expire_at`, and a derived `remaining_seconds` (`expire_at - now`, computed at read). Reachable from the session.
- **`Session.idle_expire_at`** — the `min` of the session's non-null `expire_at` values: the earliest time the session is scheduled to be cleaned up. `NULL` when no applied checker has a deadline yet.

These replace the legacy `Session.idle_checks` JSONString, which read the Valkey report.

### Data Flow

```mermaid
flowchart TB
    subgraph DB[PostgreSQL]
        Sessions[sessions]
        Checkers[idle_checkers]
        Bindings[idle_checker_bindings]
        Deadlines[session_idle_checks]
    end

    subgraph Refresh[Deadline-refresh stage]
        ReadSessions[read RG sessions + resolve scopes]
        LoadCheckers[load bound checkers]
        Judge[judge -> expire_at per checker]
        Upsert[upsert + prune rows]
    end

    subgraph Sweep[Expiry-sweep stage]
        ReadDue[read rows where expire_at <= now]
        Mark[mark sessions TERMINATING]
    end

    Sessions --> ReadSessions --> LoadCheckers
    Checkers --> LoadCheckers
    Bindings --> LoadCheckers
    LoadCheckers --> Judge --> Upsert --> Deadlines
    Deadlines --> ReadDue --> Mark
```


## Open Questions

- Should utilization `and` / `or` threshold semantics match the legacy behavior or be redefined?
- Refresh cadence vs. deadline granularity: the refresh stage must rewrite `expire_at` before it elapses, so the tick interval bounds worst-case late termination. Is one shared interval enough, or should near-due deadlines be refreshed more eagerly?
- Row lifecycle: rows are removed by `ON DELETE CASCADE` when a session or checker is deleted, and pruned by the refresh stage when a checker stops applying. Is an additional sweep of orphaned rows (e.g. sessions that left the running set out-of-band) needed?
- Should a checker with no current deadline store a `NULL`-`expire_at` row, or no row at all?

## References

- `src/ai/backend/manager/idle.py`
- `src/ai/backend/manager/sokovan/reconciler/base.py`
- `src/ai/backend/manager/sokovan/stages/factory.py`
- `src/ai/backend/manager/models/idle_checker/row.py` (new `session_idle_checks` table)
- `src/ai/backend/manager/api/gql_legacy/session.py` (session idle-check exposure)
- `docs/superpowers/specs/2026-06-17-first-class-idle-checker-design.md`
- [BEP-1029: Sokovan Observer Handler](BEP-1029-sokovan-observer-handler.md)
- [BEP-1050: Prometheus Query Preset System](BEP-1050-prometheus-query-preset-system.md)
