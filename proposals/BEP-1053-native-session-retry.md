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

`terminal_statuses()` (line 109) is `{ERROR, TERMINATED, CANCELLED}` — no transitions out. `retriable_statuses()` (line 118) classifies which startup states the **scheduler** considers retriable for re-dispatch within the same session, but there is no concept of *re-creating* a session that has already gone terminal.

### Session creation path

```
POST /v2/sessions
  → CreateFromParamsAction
  → SessionService.create_from_params (services/session/service.py:255)
  → repository → SessionRow (models/session/row.py:384)
```

`SessionRow.creation_id` (lines 389–390) is a 32-character idempotency key reused across kernel placements; we can extend it to also key retry attempts.

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

A Pydantic DTO at `common/dto/manager/v2/session/retry_policy.py` (per the manager `data/` layer rule that Pydantic models live under `dto/`, not `data/`). Schema modeled on Airflow's parameter surface:

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

### Defaults precedence

Three layers, matching Airflow's `default_args` propagation:

1. Per-session policy in the create request.
2. Project / domain default (new optional field on the project config; admin-managed).
3. Cluster default in etcd: `config/manager/retry_policy_default`.

Effective policy = deep-merge top-down; per-session wins. Ship default at layer 3 is `max_retries=0`.

### Data model

One Alembic migration adds to `sessions`:

| Column | Type | Description |
|---|---|---|
| `parent_session_id` | `UUID NULL` | Self-FK to `sessions.id`; null for the first attempt. |
| `retry_count` | `INT NOT NULL DEFAULT 0` | 0 for the first attempt. |
| `max_retries` | `INT NOT NULL DEFAULT 0` | Denormalized from policy for cheap filters. |
| `retry_policy` | `JSONB NULL` | Full policy. |
| `retry_cause` | `TEXT NULL` | Classified cause that triggered the most recent retry into this attempt. |

`parent_session_id`, `retry_count`, and `max_retries` are first-class columns because they appear in filters and joins; the rest live in JSONB. **No new history table** — the chain is already a linked list of real `SessionRow`s, each with its own status, kernels, logs, and `status_data`. The migration is idempotent and backportable per `src/ai/backend/manager/models/alembic/README.md`.

### Decision and dispatch

The retry decision is added to the existing termination-event path. Two integration points are equivalent in correctness; the implementation PR will pick one:

- **Extend `SessionEventHandler`** in `event_dispatcher/handlers/session.py` with a `handle_session_failure` method (or fold the decision into `handle_session_terminated`), since failure metadata is already read there for endpoint-route bookkeeping.
- **Add a sokovan post-processor** under `sokovan/scheduler/post_processors/`, invoked when the scheduler observes a session entering a terminal failure state.

The decision flow is the same regardless:

1. Load session. If `retry_count >= max_retries` → emit `session.retry_exhausted` and return.
2. Classify failure via `classify_failure(session, status_data)`. If the cause is hardcoded never-retriable, or not in `policy.eligible_causes`, return.
3. Acquire a row lock with `select_for_update()`. If a child whose deterministic `creation_id = parent.creation_id + ":retry:" + (retry_count + 1)` already exists, return (idempotency).
4. Compute `delay` per the formula above.
5. Schedule retry creation through the existing background task / event mechanism with the computed delay. Do not block the handler on a sleep.

The retry path calls `SessionService.create_from_params()` with a `CreateFromParamsAction` derived from the parent (image, mounts, `resource_slots`, env, cluster spec, batch entrypoint). The child inherits `retry_policy`, sets `parent_session_id` to the parent, and `retry_count = parent.retry_count + 1`.

**No new `RETRYING` status.** The parent goes to `ERROR` as today; the child starts in `PENDING` as today. A computed `retry_state` field on the API tells clients "attempt N of M" or "this session has a pending child." This avoids touching the scheduler state machine.

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

## Implementation Plan

Six PRs, each tracked by its own sub-issue under #11320:

1. **BEP draft** (this document) — #11321.
2. **Foundation:** `RetryPolicy` DTO, `classify_failure`, backoff utility with deterministic jitter. Pure, no I/O, unit-test heavy.
3. **Schema:** Alembic migration, `SessionRow` field expansion, repository read/write for the retry chain.
4. **Retry engine:** decision integration in the termination-event path, `SessionService.create_from_params` extension to inherit retry context, defaults precedence (project/domain/etcd), counters/events/audit.
5. **API surface:** REST v2 and GraphQL v2 fields, `attempts` endpoint.
6. **Client:** SDK v2, CLI v2 (`./bai session info` retry view), user docs.

Tests live with the code under test. Cross-cutting integration tests — transient → retry → success, exhaustion, concurrent dispatch idempotency, jitter determinism — ship with the retry-engine PR. Estimated effort: three to four weeks for one engineer.

## References

- Working draft: `docs/investigation/native-session-retry-plan.md`
- Apache Airflow retry implementation: `airflow-core/src/airflow/models/taskinstance.py:1109-1159`
- [BEP-1030: Sokovan Scheduler Status Transition Design](BEP-1030-sokovan-scheduler-status-transition.md)
- Alembic backport strategy: `src/ai/backend/manager/models/alembic/README.md`
