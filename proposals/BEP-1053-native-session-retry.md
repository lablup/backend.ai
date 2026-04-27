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

- GitHub Epic: #11320
- GitHub: #11321

## Motivation

Backend.AI core has no session-level retry. A `BATCH` session that fails — image pull error, transient agent failure, OOM, scheduler timeout, kernel non-zero exit — becomes terminal in `ERROR`, and the user must manually re-create it.

The only retry-shaped logic in core today is infrastructure-level: DB transaction retry (`account_manager/models/utils.py`), kernel restart on the agent (`agent/agent.py:restarting_kernels`), and `tenacity`-wrapped HTTP/socket retries. None of these handle "the session as a whole failed; create a fresh one with the same spec."

This pushes the retry concern out to every higher-level orchestrator on top of Backend.AI. Each one re-implements the same logic, with inconsistent semantics. Pushing retry into core gives:

- A single source of truth for retry semantics — backoff, jitter, eligibility — shared by every caller.
- Resilience for plain batch workloads without requiring an external orchestrator.
- Reduced duplication; orchestrators above Backend.AI can thin out their retry layers.

## Current Design

Session statuses are defined in `src/ai/backend/manager/data/session/types.py:30-51`:

```
PENDING → SCHEDULED → PREPARING → PULLING → PREPARED → CREATING → RUNNING → TERMINATING → TERMINATED
```

Terminal statuses with no further transitions: `ERROR`, `TERMINATED`, `CANCELLED`. `SessionStatus.retriable_statuses()` (line 118) classifies which startup states are scheduling-retriable, but there is no notion of *re-creating* a terminal `ERROR` session.

Session creation flows through `API handler → SessionService.create_from_params() → repository → SessionRow`. `SessionRow.creation_id` already exists as an idempotency key. There are no fields for `parent_session_id`, `retry_count`, `max_retries`, or a retry policy.

The termination event handler (`event_dispatcher/handlers/session.py`) listens to `session.terminated` / `session.error` but has no retry decision hook.

No prior BEP covers session retry or fault tolerance.

## Proposed Design

### Mental model

`max_retries > 0` means "retry on failure." Users should not need to opt in twice. Apache Airflow takes the same stance — any non-fatal exception triggers retry up to `retries`. The classification's job is only to exclude failures that semantically must not retry (cancellation, validation, quota), not to gate ordinary failure modes.

### `RetryPolicy` schema

A Pydantic DTO accepted at session creation, modeled on Airflow's parameter surface:

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
        return frozenset({
            cls.AGENT_TRANSIENT, cls.SCHEDULER_TIMEOUT,
            cls.IMAGE_PULL_FAILURE, cls.KERNEL_NONZERO_EXIT,
            cls.OOM_KILLED, cls.UNKNOWN,
        })

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

Mapping to Airflow:

| Airflow | `RetryPolicy` |
|---|---|
| `retries` | `max_retries` (count, total attempts = `1 + max_retries`) |
| `retry_delay` | `retry_delay` (seconds) |
| `retry_exponential_backoff` (multiplier) | `backoff: fixed\|exponential` + `backoff_multiplier` |
| `max_retry_delay` (with 24 h hard ceiling) | `max_retry_delay` (24 h hard ceiling preserved) |
| SHA1-deterministic jitter | `jitter` (selectable: none / deterministic / random), `jitter_ratio` |
| Exception-typed eligibility | Structural enum `RetryEligibleCause` |
| `on_retry_callback` | `session.retry_scheduled` / `session.retry_exhausted` events |
| `default_args` precedence | Per-session > project/domain default > etcd cluster default |
| `email_on_retry` | Subsumed by event subscription via webhook plugin |

Deviations from Airflow and their reasons:

- **No callback parameter.** Keeps the policy serializable and the server's behavior auditable. Backend.AI is event-driven; downstream consumers subscribe to `session.retry_*` events.
- **Structural cause enum, not exception types.** Backend.AI does not surface user exceptions across the manager/agent boundary the way Airflow does intra-process.
- **`max_retries` is a count.** Total attempts = `1 + max_retries`, matching Backend.AI conventions and the existing pipeline orchestrator.

### Failure classification

A central `classify_failure(session, status_data) → RetryEligibleCause`. Hardcoded non-retriable causes outside the enum: `USER_CANCELLED`, `VALIDATION_ERROR`, `QUOTA_EXCEEDED`. Users cannot opt these into retry.

| Cause | Default eligible | Notes |
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

`MAX_RETRY_DELAY` is a hard 24 h ceiling. Deterministic jitter takes `SHA1(session_id || retry_count) mod (base * jitter_ratio)`, yielding reproducible delays — useful for tests. Random jitter samples uniformly in `[base, base * (1 + jitter_ratio))`.

### Defaults precedence

Three layers, matching Airflow's `default_args` propagation:

1. Per-session policy in the create request.
2. Project / domain default (new optional field, admin-managed).
3. Cluster default in etcd: `config/manager/retry_policy_default`. Ship default: `max_retries=0` → no behavior change.

Effective policy = deep-merge top-down; per-session wins.

### Data model

One Alembic migration adds to `sessions`:

```
parent_session_id : UUID NULL  (self-FK)
retry_count       : INT  NOT NULL DEFAULT 0
max_retries       : INT  NOT NULL DEFAULT 0
retry_policy      : JSONB NULL
retry_cause       : TEXT NULL
```

Rationale: `parent_session_id`, `retry_count`, `max_retries` are first-class columns because they are queried for filters and joins. The rest live in JSONB. **No new history table** — the chain is a linked list of real `SessionRow`s, each with its own status, kernels, logs, and `status_data`. Cheaper than a separate history table and consistent with Backend.AI's existing model.

### Decision and dispatch

A new handler at `event_dispatcher/handlers/session_retry.py` subscribes to `session.terminated` / `session.error`:

1. Load session. If `retry_count >= max_retries` → emit `session.retry_exhausted` and return.
2. Classify failure. If cause not in `eligible_causes` (or in hardcoded never-retry set) → return.
3. Acquire row lock with `select_for_update()`. If a child with deterministic `creation_id = parent.creation_id + ":retry:" + (retry_count + 1)` already exists → return (idempotency).
4. Compute `delay` per the formula above.
5. Schedule retry creation through the existing background task / event mechanism with the computed delay. Do not block the handler on a sleep.

The retry path calls `SessionService.create_from_params()` with a `CreateFromParamsAction` derived from the parent (image, mounts, resource_slots, env, cluster spec, batch entrypoint). The child inherits `retry_policy`, sets `parent_session_id` to the parent, and `retry_count = parent.retry_count + 1`.

**No new `RETRYING` status.** The parent goes to `ERROR` as today; the child starts in `PENDING` as today. A computed `retry_state` field on the API tells clients "attempt N of M" / "this session has a pending child." This avoids touching the scheduler state machine.

### API surface

REST v2 (`api/rest/v2/sessions/`):

- `POST /sessions` — accept optional `retry_policy` in the request body.
- `GET /sessions/{id}` — return `parent_session_id`, `retry_count`, `max_retries`, `retry_policy`, `retry_cause`, plus computed `retry_chain` (oldest → newest IDs).
- `GET /sessions/{id}/attempts` — return the chain with status of each attempt.

GraphQL v2: mirror in `api/gql/session/types.py` — `parentSession`, `retryCount`, `maxRetries`, `retryPolicy`, `retryCause`, resolver `retryChain`.

Client SDK v2 + CLI v2: expose new fields; `./bai session info` shows `attempt N of M` and links to the parent.

**No retry mutation in v1.** Manual retry is deferred until the auto path is stable.

### Observability

- Counters: `bai_session_retry_scheduled_total{cause}`, `bai_session_retry_exhausted_total{cause}`, `bai_session_retry_succeeded_total`.
- Events: `session.retry_scheduled`, `session.retry_exhausted` — consumable by the webhook plugin. Replace the role of Airflow's `on_retry_callback` for downstream consumers.
- Audit log entry per retry dispatch (auto, cause, attempt N of M).

## Migration / Compatibility

### Backward compatibility

- Default `max_retries=0` ⇒ zero behavior change for existing callers.
- All new columns are nullable or default to safe zero values.
- Existing GraphQL and REST clients continue to work; new fields are additive.

### Migration steps

1. Apply Alembic migration adding the five columns. Migration is idempotent and backportable per `src/ai/backend/manager/models/alembic/README.md`.
2. Deploy manager with retry handler and surface, default off via etcd.
3. Operators opt in by setting cluster default or per-session policy.
4. External orchestrators may continue using their own retry layers; migration to native retry is independent and incremental.

### Breaking changes

None.

## Implementation Plan

Six PRs, each tracked by its own sub-issue under #11320:

1. **BEP draft** (this document) — #11321.
2. **Foundation:** `RetryPolicy` DTO, `classify_failure` module, backoff utility (with deterministic jitter). Pure functions, no I/O, unit-test heavy.
3. **Schema:** Alembic migration, `SessionRow` field expansion, repository read/write for retry chain. Backportable.
4. **Retry engine:** event handler, `SessionService.create_from_params` extension, defaults precedence (project/domain/etcd), counters/events/audit.
5. **API surface:** REST v2 and GraphQL v2 fields, `attempts` endpoint.
6. **Client:** SDK v2, CLI v2 (`./bai session info` retry view), user docs.

Tests live with the code under test. Cross-cutting integration tests (transient → retry → success; exhaustion path; concurrent dispatch idempotency; jitter determinism) ship with the retry-engine PR.

Estimated effort: three to four weeks for one engineer.

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-27 | Batch sessions only in v1 | Interactive sessions are user-driven and do not fit auto-retry semantics. |
| 2026-04-27 | Each retry is a fresh session, linked via `parent_session_id` | Matches existing pipeline orchestrator semantics; avoids reusing kernels/scratch and the complexity that would entail. |
| 2026-04-27 | No new `RETRYING` status | Parent goes to `ERROR`, child starts `PENDING` — avoids touching the scheduler state machine. Computed `retry_state` on the API is enough for clients. |
| 2026-04-27 | Linked-list chain, not a separate history table | The chain is already a list of real `SessionRow`s; no need to duplicate. |
| 2026-04-27 | Structural `RetryEligibleCause` enum, not exception-typed | Backend.AI does not surface user exceptions across the manager/agent boundary the way Airflow does intra-process. |
| 2026-04-27 | `KERNEL_NONZERO_EXIT` is in the default eligible set | `max_retries > 0` should be the only knob a typical user touches; matches Airflow's "retry on failure, period" model. |
| 2026-04-27 | `USER_CANCELLED` / `VALIDATION_ERROR` / `QUOTA_EXCEEDED` are hardcoded non-retriable | These are permanent by definition; users cannot opt them into retry. |
| 2026-04-27 | No retry mutation in v1 | Auto path stabilizes first; manual retry's interaction with `max_retries` is itself a design decision. |
| 2026-04-27 | Idempotency via deterministic child `creation_id` | Reuses an existing field; no new uniqueness constraint required. |
| 2026-04-27 | Deterministic jitter seed = `(session_id, retry_count)` | Reproducible for tests; trade-off vs. unpredictability is acceptable for a server-side retry. |

## Open Questions

- Quota accounting: do retries count against concurrent-session limits? Likely yes, but needs a product call.
- Retry-storm kill switch: should the etcd default be a single boolean toggle, a rate limit, or both? Leaning toward a boolean for v1 with a rate limit deferred.
- Manual retry in v2: counts toward `max_retries` or independent? Decide before exposing.
- Default for `max_retry_delay`: 1 h is conservative for long-running batch jobs that might benefit from a longer cooldown after repeated failures. Revisit after telemetry.
- Project/domain defaults table location: extend an existing table or add a small new `project_retry_defaults` table?

## References

- Working draft: `docs/investigation/native-session-retry-plan.md`
- Apache Airflow retry implementation: `airflow-core/src/airflow/models/taskinstance.py:1109-1159`
- Existing scheduler state-machine BEP: [BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md)
- Alembic backport strategy: `src/ai/backend/manager/models/alembic/README.md`
