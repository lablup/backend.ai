---
Author: Jeongseok Kang (jskang@lablup.com)
Status: Draft
Created: 2026-04-27
Created-Version: 26.5.0
Target-Version:
Implemented-Version:
---

# Native Session Retry

## Related Issues

- JIRA: BA-5851
- GitHub Epic: #11320
- GitHub: #11321

## Motivation

Backend.AI core has no session-level retry. A `BATCH` session that fails — image pull error, transient agent failure, OOM, scheduler timeout, kernel non-zero exit — becomes terminal in `ERROR`, and the user must manually re-create it. The only retry-shaped logic in core today is infrastructure-level: DB transaction retry (`account_manager/models/utils.py:execute_with_txn_retry`), kernel restart on the agent (`agent.py:RestartTracker`), and `tenacity`-wrapped HTTP/socket retries. None of these handle "the session as a whole failed; create a fresh one with the same spec."

The retry concern is therefore pushed to every higher-level orchestrator on top of Backend.AI, each of which re-implements the same logic with inconsistent semantics. Lifting retry into core gives one source of truth, resilience for plain batch workloads, and lets orchestrators thin out their own retry layers.

### Goals

- Opt-in automatic retry for `BATCH` sessions with a `RetryPolicy` accepted at session creation.
- Each retry is a fresh session linked to its parent — no kernel reuse, no new status state.
- Default `max_retries=0` keeps current behavior intact.
- A single user-facing knob: setting `max_retries > 0` retries on any non-permanent failure.

## Current Design

### Session lifecycle

`SessionStatus` (`src/ai/backend/manager/data/session/types.py:30-50`) defines the lifecycle:

```
PENDING → SCHEDULED → PREPARING → PULLING → PREPARED → CREATING → RUNNING → TERMINATING → TERMINATED
```

`terminal_statuses()` (line 109) is `{ERROR, TERMINATED, CANCELLED}` — no transitions out. `retriable_statuses()` (line 118) is unrelated to this BEP: it tells the scheduler which **startup** states are still safe to re-dispatch *within the same session*. This BEP introduces a separate concept — re-creating a fresh session after the previous one has gone terminal.

### Session creation path

```
POST /v2/sessions
  → CreateFromParamsAction
  → SessionService.create_from_params (services/session/service.py:255)
  → repository → SessionRow (models/session/row.py:384)
```

`SessionRow.creation_id` (lines 389–390) is a 32-character idempotency key reused across kernel placements; today it is generated as `secrets.token_urlsafe(16)` (`services/session/service.py:1593`). It is **not** extended to encode retry chains — those use a separate first-class column (see Data Model).

There are no fields for `parent_session_id`, `retry_count`, `max_retries`, or a retry policy on `SessionRow`.

### Termination event handling

`SessionEventHandler` (`event_dispatcher/handlers/session.py:52`) already subscribes to the relevant events:

| Method | Event | Line |
|---|---|---|
| `handle_session_started` | `SessionStartedAnycastEvent` | 88 |
| `handle_session_cancelled` | `SessionFailureAnycastEvent` | 105 |
| `handle_session_terminating` | `SessionTerminatingAnycastEvent` | 118 |
| `handle_session_terminated` | `SessionTerminatedAnycastEvent` | 130 |

`handle_session_terminated` already consults `session.status_data["error"]` for endpoint-route bookkeeping, so the failure metadata needed for retry classification is already on hand at this point. What is missing is the decision: "should we spawn a child session?"

No prior BEP covers session retry or fault tolerance. BEP-1030 (scheduler status transitions) covers in-session retries by the scheduler, not session re-creation.

## Proposed Design

### Mental model

`max_retries > 0` means "retry on failure." Users should not need to opt in twice. Apache Airflow takes the same stance — any non-fatal exception triggers retry up to `retries`. Classification's job is only to exclude failures that semantically must not retry (cancellation, validation, quota), not to gate ordinary failure modes.

### `RetryPolicy` schema

A Pydantic DTO at `src/ai/backend/common/dto/manager/v2/session/retry_policy.py`, matching the v2 DTO location used by other recent BEPs. Per `src/ai/backend/manager/data/CLAUDE.md`, `data/` is reserved for frozen dataclasses with no framework deps; Pydantic models live under `common/dto/` so they can be shared across REST v2 and GraphQL. Schema modeled on Airflow's parameter surface:

```python
class BackoffStrategy(StrEnum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"

class JitterMode(StrEnum):
    NONE = "none"
    DETERMINISTIC = "deterministic"
    RANDOM = "random"

class RetryEligibleCause(StrEnum):
    AGENT_TRANSIENT = "agent_transient"
    SCHEDULER_TIMEOUT = "scheduler_timeout"
    IMAGE_PULL_FAILURE = "image_pull_failure"
    KERNEL_NONZERO_EXIT = "kernel_nonzero_exit"
    OOM_KILLED = "oom_killed"
    UNKNOWN = "unknown"

    @classmethod
    def defaults(cls) -> frozenset["RetryEligibleCause"]:
        return frozenset(cls)

class RetryPolicy(BaseModel):
    max_retries: NonNegativeInt = 0
    retry_delay: PositiveFloat = 60.0
    backoff: BackoffStrategy = BackoffStrategy.FIXED
    backoff_multiplier: PositiveFloat = 2.0
    max_retry_delay: PositiveFloat | None = 3600.0
    jitter: JitterMode = JitterMode.DETERMINISTIC
    jitter_ratio: confloat(ge=0, le=1) = 0.25
    eligible_causes: frozenset[RetryEligibleCause] = Field(
        default_factory=RetryEligibleCause.defaults
    )
    emit_retry_events: bool = True
```

Notable deviations from Airflow:

- **No callback parameter.** Backend.AI is event-driven; downstream consumers subscribe to `session.retry_*` events instead of registering an `on_retry_callback`. Keeps the policy serializable and the server's behavior fully auditable.
- **Structural cause enum, not exception types.** Backend.AI does not surface user exceptions across the manager/agent boundary the way Airflow does intra-process; classification reads `status_data` instead.
- **`max_retries` is a count.** Total attempts = `1 + max_retries`, matching Backend.AI naming and the existing pipeline orchestrator on top of Backend.AI.

### Failure classification

A central `classify_failure(session, status_data) → RetryEligibleCause`. Hardcoded never-retriable causes live outside the enum: `USER_CANCELLED`, `VALIDATION_ERROR`, `QUOTA_EXCEEDED`. Users cannot opt these into retry.

| Cause | In default eligible set | Notes |
|---|---|---|
| `AGENT_TRANSIENT` | yes | Lost heartbeat, agent restart mid-run. |
| `SCHEDULER_TIMEOUT` | yes | Kernel-creation timeout under cluster pressure. |
| `IMAGE_PULL_FAILURE` | yes | Typo wastes a few seconds with backoff; registry blip is real. |
| `KERNEL_NONZERO_EXIT` | yes | The most common reason batch users want retry. |
| `OOM_KILLED` | yes | Retry without resource bump usually fails again, but exhausting `max_retries` is cheap. |
| `UNKNOWN` | yes | Conservative for unclassified failures. |
| `USER_CANCELLED` | hardcoded never | Permanent. |
| `VALIDATION_ERROR` / `QUOTA_EXCEEDED` | hardcoded never | Permanent. |

### Backoff formula

```
base = retry_delay                                                    if backoff == FIXED
       min(retry_delay * backoff_multiplier ** retry_count,            otherwise
           max_retry_delay or MAX_RETRY_DELAY)
delay = apply_jitter(base, mode=jitter, ratio=jitter_ratio,
                     seed=(session_id, retry_count))
delay = min(delay, max_retry_delay or MAX_RETRY_DELAY)
```

`MAX_RETRY_DELAY` is a hard 24 h ceiling, matching Airflow. Deterministic jitter is `SHA1(session_id || retry_count) mod (base * jitter_ratio)`, yielding reproducible delays — useful for tests. Random jitter samples uniformly in `[base, base * (1 + jitter_ratio))`.

### Defaults and kill switch

Two distinct concepts, kept separate to avoid the precedence trap of "default doubles as kill switch":

- **Cluster default** in etcd: `config/manager/retry_policy_default` (ship default `max_retries=0` — no behavior change). This is a default; per-session policy wins on merge. Effective policy = deep-merge of cluster default and per-session policy.
- **Cluster kill switch** in etcd: `config/manager/retry_disabled` (boolean, default `false`). Loaded at startup and refreshed via the existing `EtcdConfigWatcher` (`manager/config/provider.py:20`) so changes propagate without per-event etcd reads. Checked at the **top** of the decision flow, before any policy merge, **and** by the dispatcher worker before claiming a queue row — so flipping the switch mid-incident also halts in-flight queued retries. When `true`, no retries are scheduled or dispatched regardless of per-session policy. Useful for incident response (e.g., disabling retries cluster-wide during a registry outage that would otherwise cause a retry storm).

**Project / domain default is deferred.** [BEP-1052 (Scoped App Config Redesign)](BEP-1052-scoped-app-config-redesign.md) is concurrently rewriting the project / domain config surface around scoped `AppConfigFragment` rows. Adding `retry_policy_default` to the legacy project config row would conflict with that work. After BEP-1052 lands, a follow-up BEP can wire retry defaults into `AppConfigFragment` as a third precedence layer.

### Data model

One Alembic migration adds to `sessions`:

| Column | Type | Description |
|---|---|---|
| `parent_session_id` | `UUID NULL` | Self-FK to `sessions.id`; null for the first attempt. |
| `retry_count` | `INT NOT NULL DEFAULT 0` | 0 for the first attempt. |
| `max_retries` | `INT NOT NULL DEFAULT 0` | Denormalized from policy for cheap filters. |
| `retry_policy` | `JSONB NULL` | Full policy. |
| `retry_cause` | `TEXT NULL` | Classified cause that triggered the most recent retry into this attempt. |

The migration also adds a **partial unique index** on `(parent_session_id, retry_count) WHERE parent_session_id IS NOT NULL`. This is the actual idempotency guarantee for retry dispatch: even if two workers race past the parent row lock (different transactions, different timing), the second `INSERT` of a child with the same `(parent, attempt-number)` fails on the unique violation. `creation_id` is unchanged and remains a per-attempt random token (no retry encoding).

A second small table `session_retry_dispatch_queue` is added for durable delayed dispatch (see "Decision and dispatch"):

| Column | Type | Description |
|---|---|---|
| `parent_session_id` | `UUID NOT NULL` | FK to `sessions.id`. |
| `retry_count` | `INT NOT NULL` | Target attempt number (= parent.retry_count + 1). |
| `scheduled_at` | `TIMESTAMPTZ NOT NULL` | Earliest dispatch time. |
| `claimed_at` | `TIMESTAMPTZ NULL` | Set when a dispatcher worker claims the row. |
| `dispatched_at` | `TIMESTAMPTZ NULL` | Set when the child session has been created. |

Primary key `(parent_session_id, retry_count)` — the same constraint that protects `sessions` also serializes queue inserts. The queue lets retry decisions survive manager restarts, mirrors the durable-outbox pattern used by the existing pipeline orchestrator on top of Backend.AI, and avoids inventing in-memory scheduling.

`parent_session_id`, `retry_count`, and `max_retries` are first-class columns because they appear in filters, joins, and the unique index; the rest live in JSONB. `parent_session_id` is the canonical query for "show me the retry chain of this session." **No new history table** — the chain is already a linked list of real `SessionRow`s, each with its own status, kernels, logs, and `status_data`. The migration is idempotent and backportable per `src/ai/backend/manager/models/alembic/README.md`.

### Decision and dispatch

The retry decision is **folded into the existing `SessionEventHandler.handle_batch_result`** (`event_dispatcher/handlers/session.py:152`), not added as a sibling handler. Rationale:

- `SessionFailureAnycastEvent` is **already** subscribed by `handle_batch_result` (`event_dispatcher/dispatch.py:520`). Adding a second handler on the same event would race against bookkeeping work (`set_session_result`, etc.) and depend on undefined dispatch ordering.
- Failure metadata (`session.status_data["error"]`) is already loaded in `handle_batch_result` for the existing failure path; the retry decision can reuse it without new DB roundtrips.
- The handler runs after the session has reached a terminal status, so parent state is settled, and the change does not interact with the recently refactored sokovan termination flow (#11250 — `mark_sessions_for_termination()` in `sokovan/scheduling_controller/scheduling_controller.py:266`).

A sokovan post-processor was considered but rejected for v1: post-processors run *during* scheduling iterations, complicating idempotency and timing without adding capability the event-handler path lacks.

**Dispatch primitive.** `BackgroundTaskManager.start_retriable()` (`common/bgtask/bgtask.py:444`) is **not** suitable: it accepts no `delay` parameter and fires the task immediately via `asyncio.create_task` ("retriable" refers to the task body retrying on failure, not delayed scheduling). Instead, retries are persisted to the new `session_retry_dispatch_queue` table (see Data Model). A periodic loop in the manager (placed under `sokovan/` alongside other periodic workers, e.g., `sokovan/scheduler/retry_dispatcher.py`) claims **one row at a time** via:

```sql
UPDATE session_retry_dispatch_queue
SET claimed_at = now()
WHERE (parent_session_id, retry_count) = (
    SELECT parent_session_id, retry_count
    FROM session_retry_dispatch_queue
    WHERE scheduled_at <= now()
      AND claimed_at IS NULL
      AND dispatched_at IS NULL
    ORDER BY scheduled_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING parent_session_id, retry_count;
```

`FOR UPDATE SKIP LOCKED` lets multiple manager replicas claim disjoint rows without contention, and `LIMIT 1` avoids multi-row claim deadlocks. The worker invokes `SessionService.create_from_params()` for the claimed row and stamps `dispatched_at = now()` on success or `dispatched_at = '1970-01-01'::timestamptz` (sentinel) on failure. This pattern is durable across manager restarts and matches the outbox approach used by the sibling pipeline orchestrator.

The decision flow inside `handle_batch_result` (in the `SessionFailureAnycastEvent` arm):

1. Load the parent session. **Short-circuit unless `session.session_type == SessionTypes.BATCH`** — interactive and inference sessions share `SessionEventHandler` and are out of scope for v1. Then, if `retry_count >= max_retries`, emit `session.retry_exhausted` and return.
2. Classify failure via `classify_failure(session, status_data)`. The shape of `status_data["error"]` is defined by `manager/exceptions.py:convert_to_status_data` (returns `ErrorStatusInfo` / `ErrorDetail` TypedDicts at line 97); classification reads `error.name` and `error.src` to map to a `RetryEligibleCause`. **Malformed-input fallback:** if `status_data` is `None`, `status_data["error"]` is missing, or required keys (`name`, `src`) are missing, `classify_failure` does **not** return `UNKNOWN`. Instead it logs a WARNING and returns the hardcoded never-retriable sentinel — a malformed error envelope is treated as a permanent failure to avoid retry storms on serialization bugs. Only well-formed failures with an unrecognized `error.name` map to `UNKNOWN`. If the cause is hardcoded never-retriable, or not in `policy.eligible_causes`, return.
3. Inside the session repository's `begin_session()` transaction, lock the parent row with `sa.select(SessionRow).where(SessionRow.id == parent.id).with_for_update()` and re-read `retry_count`.
4. Compute `delay` per the formula above.
5. `INSERT` into `session_retry_dispatch_queue` with `(parent_session_id, retry_count + 1, now() + delay)`. The PK on `(parent_session_id, retry_count)` makes this idempotent: a duplicate dispatch (handler replay, concurrent handlers) hits a unique-violation and the `INSERT` is skipped. Emit `session.retry_scheduled`.
6. The dispatcher worker eventually claims the row, runs `SessionService.create_from_params` with a `CreateFromParamsAction` derived from the parent, and stamps `dispatched_at`. The child `INSERT` is the second idempotency boundary: the partial unique index on `sessions.(parent_session_id, retry_count)` rejects duplicate child rows even if two workers claim the same queue row through PG bug, replication lag, or operational error.

The child inherits `retry_policy`, sets `parent_session_id` to the parent, and `retry_count = parent.retry_count + 1`. The `CreateFromParamsAction` carries the same image, mounts, `resource_slots`, env, cluster spec, and batch entrypoint as the parent.

**Failure mode of the retry decision.** If `classify_failure` raises, the session stays in its terminal state and the failure is logged at ERROR level — no retry, no crash propagation. If the queue `INSERT` fails (DB unavailable), the parent's `status_data` is annotated with the dispatch failure and `session.retry_exhausted` is emitted. The decision must not raise out of `handle_batch_result`; an unhandled exception there would also break existing batch-result bookkeeping.

**Failure mode of the dispatcher worker.** If `create_from_params` raises after the queue row is claimed, the worker stamps `dispatched_at` to a sentinel value and emits `session.retry_exhausted` with the underlying error. Manager restart while a row is claimed-but-not-dispatched: the worker re-claims rows whose `claimed_at` is older than a configurable lease (e.g., 5 minutes) on startup.

**No new `RETRYING` status.** The parent goes to `ERROR` as today; the child starts in `PENDING` as today. A computed `retry_state` (resolved at the API layer, not stored) tells clients "attempt N of M" or "this session has a pending child." This avoids touching the scheduler state machine entirely.

### API surface

REST v2 (`api/rest/v2/sessions/`):

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/sessions` | Accept optional `retry_policy` in `SessionCreateRequest`. |
| `GET` | `/sessions/{id}` | Return `parent_session_id`, `retry_count`, `max_retries`, `retry_policy`, `retry_cause`, plus computed `retry_chain` (oldest → newest IDs). |
| `GET` | `/sessions/{id}/attempts` | Return the chain with the status of each attempt. |

GraphQL v2: mirror in `api/gql/session/types.py` — `parentSession`, `retryCount`, `maxRetries`, `retryPolicy`, `retryCause`, `retryChain` resolver.

Client SDK v2 + CLI v2: expose the new fields; `./bai session info` shows `attempt N of M` and links to the parent.

No retry mutation in v1; manual retry is deferred until the auto path stabilizes.

### Observability

- Counters: `bai_session_retry_scheduled_total{cause}`, `bai_session_retry_exhausted_total{cause}`, `bai_session_retry_succeeded_total`.
- Events: `session.retry_scheduled`, `session.retry_exhausted` — consumable by the webhook plugin, replacing the role of Airflow's `on_retry_callback` for downstream consumers.
- Audit log entry per retry dispatch: cause and attempt N of M.

## Migration / Compatibility

- Default `max_retries=0` keeps behavior unchanged for every existing caller.
- All new columns are nullable or default to safe zero values; the Alembic migration is purely additive.
- Existing GraphQL and REST clients continue to work; new fields are additive on responses.
- Operators opt in by setting the cluster default in etcd or a per-session policy.
- External orchestrators may continue using their own retry layers; migration to native retry is independent and incremental.
- No breaking changes.

### Quota and accounting

A retry attempt is a fresh `SessionRow` and counts against the user's concurrent-session limit while it is alive — same as if the user had re-submitted manually. The previous attempt's resource consumption is not refunded; this matches the principle that "actual GPU/CPU time was spent, regardless of why the session ended." The API exposes the chain so accounting tools can group attempts under one logical job if they choose.

### Operational kill switch

`config/manager/retry_disabled` (etcd, boolean) is the cluster-level kill switch — see "Defaults and kill switch" above. Per-project / per-user kill switches are deferred until the project-default layer lands (see [BEP-1052](BEP-1052-scoped-app-config-redesign.md) dependency above).

## Implementation Plan

Six PRs, each tracked by its own sub-issue under #11320:

1. **BEP draft** (this document) — #11321.
2. **Foundation:** `RetryPolicy` DTO, `classify_failure`, backoff utility with deterministic jitter. Pure, no I/O, unit-test heavy.
3. **Schema:** Alembic migration adding `SessionRow` retry columns (with the partial unique index) and the `session_retry_dispatch_queue` table; repository read/write for the retry chain.
4. **Retry decision:** fold the decision into `handle_batch_result` in `SessionEventHandler`, queue insert with idempotency, etcd kill switch and cluster default, counters/events/audit.
5. **Dispatcher worker:** periodic claim loop on `session_retry_dispatch_queue`, `SessionService.create_from_params` extension to inherit retry context, lease-based recovery on manager restart.
6. **API surface:** REST v2 and GraphQL v2 fields, `attempts` endpoint.
7. **Client:** SDK v2, CLI v2 (`./bai session info` retry view), user docs.

Tests live with the code under test. Cross-cutting integration tests — transient → retry → success, exhaustion, concurrent dispatch idempotency, jitter determinism, manager-restart recovery of claimed-but-undispatched queue rows — ship with the dispatcher-worker PR. Estimated effort: four to five weeks for one engineer.

## References

- Working draft: `docs/investigation/native-session-retry-plan.md`
- Apache Airflow retry implementation: `airflow-core/src/airflow/models/taskinstance.py:1109-1159`
- [BEP-1030: Sokovan Scheduler Status Transition Design](BEP-1030-sokovan-scheduler-status-transition.md)
- Alembic backport strategy: `src/ai/backend/manager/models/alembic/README.md`
