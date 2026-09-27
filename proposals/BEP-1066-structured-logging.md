---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-28
Created-Version: 26.9.0
Target-Version:
Implemented-Version:
---

# Structured Logging Across Components

## Related Issues

- Epic: BA-7025 — Structured logging across Backend.AI components
- JIRA: BA-7029 (this BEP)

## Motivation

- Log values are interpolated into the message string. They cannot be filtered or aggregated by value.
  - Of 1,996 `log.<level>()` calls, about 1,600 use positional interpolation; 0 pass values as fields.
- There is no agreed way to add fields.
  - At the call site: `BraceStyleAdapter` kwargs are used for named interpolation (`"{name}"`) and never become fields. `extra=` takes an arbitrary dict, so names are not agreed.
  - At higher layers: `with_log_context_fields()` takes an arbitrary dict. Each of its 3 users picks its own names.
- Goal: define **two interfaces that add log fields**, and agree on **which fields are added at which point**.

| Interface | Values it carries | Where it is set |
|---|---|---|
| Scope fields | Values every log line inside the scope carries, wherever it is logged | Entry point of a unit of work (request, action, event, RPC, schedule, ...) |
| Call-site fields | Values needed by one log line only | The log call |

Fields from both interfaces are emitted as attributes of the OTel log record. Storage backends (Loki, Elasticsearch, ...) are out of scope.

## Current Design

| Item | Current |
|---|---|
| Logger | `BraceStyleAdapter` — 571 files. Lazy `str.format` via `BraceMessage` |
| Call kwargs | Named interpolation arguments. `tests/unit/logging/test_adapter.py` verifies this as a contract |
| Context fields | `with_log_context_fields(dict)` → contextvar → merged into `extra` by the adapter's `process()` |
| Context field users | request_id middleware, REST auth middleware (`user_id`), `MessageMetadata.apply_context()` — 3 places |
| `contexts.*` | `request_id`, `user`, `triggered_user`, `client_ip` contextvars. Set separately from log fields |
| OTel handler | `apply_otel_loggers()` attaches `CustomJsonFormatter`, so the body becomes a JSON string and the same fields also appear in attributes |
| OTel coverage | The handler is attached only to loggers that exist at call time. Logs from loggers created afterwards never reach OTel (Appendix D-2) |
| Trace correlation | The OTel SDK adds `trace_id`/`span_id` to logs emitted inside a span (Appendix H-2) |

## Proposed Design

### 1. Call-site fields — the logger interface

A new logger, `StructuredLogger`, lives in `ai.backend.logging.structured`. The message is a constant; values are fields.

```python
log = StructuredLogger(logging.getLogger(__spec__.name))

log.info("kernel creation started")
log.warning("image pull retried", attempt=3, delay_sec=1.5)
log.exception("kernel creation failed", kernel_id=kernel_id)
log.debug("allocation candidates: {}", candidates, resource_group_id=rg_id)   # formatting only in debug/trace
```

```python
type LogValue = str | int | float | bool | None | UUID | Enum | Path | Decimal | datetime

class StructuredLogger:
    def trace(self, msg: LiteralString, /, *args: object, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def debug(self, msg: LiteralString, /, *args: object, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def info(self, msg: LiteralString, /, *, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def warning(self, msg: LiteralString, /, *, exc_info: ExcInfo = None, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def error(self, msg: LiteralString, /, *, exc_info: ExcInfo = None, stacklevel: int = 1, **fields: LogValue) -> None: ...
    def exception(self, msg: LiteralString, /, *, stacklevel: int = 1, **fields: LogValue) -> None: ...
```

| Rule | Content |
|---|---|
| Message (`info` and above) | Constant. No formatting. The same event has the same message, so it groups into one bucket at the collector |
| Message (`debug`, `trace`) | Takes `{}` formatting and positional arguments. Formatted only after the level check |
| Positional arguments | Not accepted by `info` and above. Every value is a keyword field |
| Value types | `LogValue` only. No `list`/`dict` (mixed-type sequences are silently dropped by OTel, Appendix E) |
| Value normalization | `UUID`/`Path`/`Decimal` → `str`, `Enum` → `.value`, `datetime` → ISO 8601. Everything else as is |
| Field name prefix | Every field is emitted as `log_tag_<name>`. Field names never collide with `LogRecord` attributes (Appendix H-1), so a log call never raises |
| Conflict with scope | On the same name, the call-site value wins |
| Level disabled | Fields are not normalized (`isEnabledFor` first) |

#### Log levels

| Level | Use for |
|---|---|
| error | A server fault. Logged once, where it happens. Where an exception is caught, log it with `exception()` so the traceback is kept |
| warning | A transient server-side failure, a retry, degradation |
| info | Server lifecycle events an operator needs (start, stop, config applied, leader change) |
| debug | Per-cycle summaries of periodic work, progress steps |
| trace | Outcomes of user requests (scheduling failure, resource exhaustion, quota exceeded, 4xx). History and the API are the record |

#### Guardrail — no formatting at `info` and above

| Means | What it catches |
|---|---|
| Signature | mypy rejects positional arguments passed to `info`/`warning`/`error`/`exception` |
| Message type | The message is a `LiteralString`, so mypy rejects a message built with an f-string, `.format()`, `%` or `+` |

ruff `G001`–`G004` stay off. The `StructuredLogger` signature is the guardrail; `BraceStyleAdapter` call sites stay as they are until they are migrated.

`StructuredLogger` shares nothing with `BraceStyleAdapter`. `BraceStyleAdapter` and `with_log_context_fields` stay as is and do not receive `with_log_context` fields; both are removed once their call sites move to `StructuredLogger` and `with_log_context`. New code and any log line being touched use `StructuredLogger`.

### 2. Scope fields — `with_log_context`

The one public interface for adding fields from higher layers is `with_log_context`, in `ai.backend.logging.structured`. It keeps its own contextvar, separate from `with_log_context_fields`.

```python
@contextmanager
def with_log_context(**fields: LogValue) -> Iterator[None]: ...

with with_log_context(action_id=action_id, action_name=action_name):
    ...   # every log line inside carries both fields
```

| Rule | Content |
|---|---|
| Shape | Keyword arguments only. Value types, normalization, and the field name prefix follow `StructuredLogger` in section 1 |
| Nesting | Merged into the outer fields. On the same name, the inner value wins |
| Inside loops | A loop over several entities opens one per iteration (e.g. `session_id` in a session loop) |
| Wrappers | Frequently used combinations, or values that must be set together with `contexts.*`, get a wrapper function. A wrapper calls `with_log_context` and sets the matching `contexts.*` contextvar to the same value. Wrappers live in `ai.backend.common.contexts` |
| Existing API | `with_log_context_fields`, which takes a dict, is replaced by `with_log_context` and removed together with `BraceStyleAdapter` |

| Wrapper | Fields | `contexts` set together |
|---|---|---|
| `with_request_context` | `request_id` | `contexts.request_id` |
| `with_user_context` | `user_id`, `triggered_user_id` (only when acting on behalf of another user) | `contexts.user`, `contexts.triggered_user` |

Values that do not change for the process lifetime (component name, node) go into OTel Resource attributes (`service.name`, `host.name`), not into a scope. `agent_id` is not a Resource attribute: one agent process can run several agents, so it goes in with `with_log_context`.

### 3. OTel delivery contract

| Item | Contract |
|---|---|
| body | The message string only |
| attributes | Scope fields + call-site fields + SDK automatic attributes (`code.*`, `trace_id`, `span_id`) |
| Handler split | A new OTel handler sends `StructuredLogger` records, told apart by the message type (`StructuredMessage`). The legacy handler filters them out and otherwise stays as is until it is removed |
| Formatter | The new handler has no formatter and does not overwrite the formatters of other handlers |
| Coverage | The new handler is attached to the root and the `pkg-ns` loggers (propagation boundary) instead of a snapshot of loggers |
| Resource | The new handler's Resource adds `host.name` |
| Explicit field count | At most 10 per line, `with_log_context` and call-site fields combined. Automatic attributes are not counted |

### 4. Field naming rules

The rules apply to the name before the `log_tag_` prefix.

| Kind | Form | Examples |
|---|---|---|
| Identifier | `<entity>_id` | `session_id`, `kernel_id`, `resource_group_id` |
| Name | `<thing>_name` | `action_name`, `task_name`, `handler_name` |
| Kind / status | `<thing>_type`, `<thing>_status` | `operation_type`, `schedule_type` |
| Count | `<thing>_count` | `allocation_count` |
| Duration | `_sec`, `_ms` suffix | `delay_sec`, `elapsed_ms` |
| Size | `_bytes` suffix | `transferred_bytes` |
| Forbidden | Generic names such as `id`, `name`, `entity_id` | — |

### 5. Which fields go where

#### 5.1 Injection points and fields

| Injection point | Fields | Method |
|---|---|---|
| manager REST request_id middleware, storage-proxy manager/client API, appproxy coordinator and worker request middleware, account-manager API middleware, webserver (new middleware) | `request_id` | `with_request_context` |
| manager REST auth middleware, `MessageMetadata.apply_context()` | `user_id`, `triggered_user_id` | `with_user_context` |
| `run` of the `actions/v2/*` processors, 16 places (single_entity, field, scope, global_scope x3, bulk x2, field bulk x2, lookup x2, membership, relation) | `action_id`, `action_name` | `with_log_context` |
| `EventDispatcher._handle` — metadata restore and the exception log inside one scope | `event_name`, `handler_name` | `with_log_context` |
| bgtask `_observe_bgtask`/`_execute_new_task`/`_revive_task` | `task_name`, `bgtask_id` | `with_log_context` |
| `LeaderCron._run_task`, `LocalCron._run_task`, `GlobalTimer` tick | `task_name` | `with_log_context` |
| sokovan `coordinator._process_*_schedule` | `schedule_type`, `handler_name` | `with_log_context` |
| sokovan `_process_resource_group`, provisioner `schedule_resource_group` | `resource_group_id` | `with_log_context` |
| provisioner session loop, launcher `_start_single_session`, terminator `_terminate_kernel` | `session_id` | `with_log_context` |
| deployment coordinator `_run_handler`, route coordinator `process_route_lifecycle` | `lifecycle_type`, `handler_name` | `with_log_context` |
| agent `RPCFunctionRegistry`/`RPCFunctionRegistryV2`, v3 RPC routing | `rpc_method` | `with_log_context` |
| agent `create_kernels` (per kernel), `destroy_kernel`, `restart_kernel`, `execute`, container lifecycle event handling | `session_id`, `kernel_id` | `with_log_context` |
| storage `VolumeService` methods | `volume_id`, `vfolder_id` or `quota_scope_id` | `with_log_context` |
| appproxy worker proxy `ensure_slot_middleware` | `circuit_id` | `with_log_context` |

Deepest nesting a single request reaches (manager): `request_id`, `user_id`, `triggered_user_id`, `action_id`, `action_name` = 5 fields.

A field combination repeated at several points is promoted to a wrapper.

#### 5.2 Carrying scope across boundaries

| Boundary | Method |
|---|---|
| Event publish → consume | Keep the current `MessageMetadata` |
| manager → agent RPC | Carry the same shape as `MessageMetadata` in the RPC request and restore it at the agent RPC entry point with `with_request_context` and `with_user_context` |
| manager → storage-proxy HTTP | Forward the `X-BackendAI-RequestID` header |
| webserver → manager HTTP | Forward the `X-BackendAI-RequestID` header |
| appproxy worker → coordinator | Keep the current header forwarding |
| `loop.run_in_executor` | Go through a common helper that copies contextvars (162 places: agent 72, storage 52, accelerator 26, other 12) |
| `threading.Thread` | 2 places handled individually |

#### 5.3 Call-site field migration targets

Only values a scope cannot express move to call-site fields. Files with the most log calls go first.

| File | Log calls |
|---|---|
| agent/agent.py | 131 |
| agent/server.py | 67 |
| kernel/base.py | 55 |
| storage/services/artifacts/reservoir.py | 41 |
| manager/sokovan/scheduler/coordinator.py | 41 |
| agent/docker/agent.py | 38 |
| appproxy/coordinator/server.py | 33 |
| storage/services/artifacts/huggingface.py | 31 |
| appproxy/worker/server.py | 28 |
| manager/sokovan/deployment/route/executor.py | 22 |

Conversion examples:

| Current | After |
|---|---|
| `"Processing {} allocations, {} reservations, {} failures and {} skips in resource group {}"` | A per-cycle summary, so `debug`: `"resource group scheduled"`, `allocation_count`, `reservation_count`, `failure_count`, `skip_count` (`resource_group_id` comes from the scope). Per-session scheduling outcomes (failure, skip, deprioritize) are `trace` |
| `"Evicted unreachable route {} after {}s"` | `"unreachable route evicted"`, `route_address`, `unreachable_sec` |

### 6. Interface verification

| Target | Scenario |
|---|---|
| `StructuredLogger` | The message goes to the body as is; fields become record attributes |
| | Value normalization: `UUID`, `Enum`, `Path`, `Decimal`, `datetime` |
| | Every field gets the `log_tag_` prefix, including `LogRecord` attribute names, and the log line is kept |
| | A call-site field overrides a scope field of the same name |
| | Fields are not normalized when the level is disabled |
| | `debug`/`trace` format positional arguments and also carry fields |
| | `info` and above reject positional arguments (mypy rejects, runtime `TypeError`) |
| | `exception()` carries the traceback; `stacklevel` points at the caller |
| `with_log_context` | Every log line inside the scope carries the fields; they disappear on exit |
| | Nested merge, inner wins |
| | Value normalization and the field name prefix match `StructuredLogger` |
| Wrappers | Log fields equal the matching `contexts.*` values |
| | Carried through `create_task`/`gather`, and into executors through the context-copy helper |
| `BraceStyleAdapter` | Existing tests kept; does not receive `with_log_context` fields, and `StructuredLogger` does not receive `with_log_context_fields` fields |
| OTel | New handler: body = message and attributes = fields. Loggers created after the handler is attached also arrive. `BraceStyleAdapter` records are not sent |
| | Legacy handler: `StructuredLogger` records are not sent; `BraceStyleAdapter` records are sent as before |

## Migration / Compatibility

| Item | Impact |
|---|---|
| Existing call sites | No change. Scope fields reach a log line once its call site moves to `StructuredLogger` |
| OTel body | JSON string → message string, for each line once its call site moves to `StructuredLogger`. Queries relying on fields inside the body move to attributes. Two OTel log exporters run during the transition |
| console/file/logstash/graylog | No change. The relay not forwarding fields stays as is |
| `with_log_context_fields`, `BraceStyleAdapter` | Removed after their call sites move to `with_log_context` or a wrapper and to `StructuredLogger` |

## Implementation Plan

| Phase | Content |
|---|---|
| 1 (this BEP PR) | Commit 1: the BEP. Commit 2: `StructuredLogger`, `LogValue` and normalization, the field name prefix, `with_log_context`, and the section 6 tests |
| 2 | `AGENTS.md` logging rules |
| 3 | The `StructuredLogger` OTel handler and the record split with the legacy handler (section 3) |
| 4 | The 2 wrappers, 5.1 injection-point wiring |
| 5 | 5.2 boundary propagation — RPC metadata, HTTP headers, executor helper migration |
| 6 | Per-family issues move every call site to `StructuredLogger`, then `BraceStyleAdapter`, `with_log_context_fields` and the legacy OTel handler are removed |

The core contract of the interface is its signature (types), so it is reviewed as code in the same PR as the BEP.

## Open Questions

None.

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-09-27 | The 162 executor helper migrations are bundled into one phase 5 issue | The helper and its first consumer land together; the rest of the migration is mechanical |
| 2026-09-27 | Per-cycle summaries are `debug`; per-session scheduling outcomes are `trace` | History and the API are the record of user-request outcomes |
| 2026-09-27 | `agent_id` goes in with `with_log_context`, not as a Resource attribute | One agent process can run several agents |
| 2026-09-27 | ruff `G001`–`G004` stay off | The `StructuredLogger` signature already prevents it, and existing call sites go away as they are migrated |
| 2026-09-27 | A new OTel handler is added and the legacy handler is kept until removal | Existing logs reach OTel unchanged; the legacy handler is removed once every call site is replaced |

## References

- Code: `src/ai/backend/logging/{utils,otel,formatter}.py`, `src/ai/backend/common/contexts/`, `src/ai/backend/common/message_queue/types.py`
- Tests: `tests/unit/logging/test_adapter.py`
- Enforcement precedent: `pyproject.toml` `[tool.ruff.lint.flake8-tidy-imports.banned-api]`

---

## Appendix. Measurements

Environment: opentelemetry-sdk 1.39.1, halfstack `observability` profile.

### A — What OTel receives

| Call | body (formatter attached) | attributes |
|---|---|---|
| `log.info("started session {} on agent {}", sid, aid)` | `{"message": "started session sess-abc on agent agent-01", ...}` | No fields (`code.*` only) |
| `log.info("session started", extra={"session_id": ...})` | `{"message": "session started", "session_id": "sess-abc", ...}` | `session_id` |
| `log.info("session {sid} started", sid=...)` | `{"message": "session sess-abc started", ...}` | No fields |

With the formatter detached, the body becomes `session started` and the attributes are the same.

### D — Loss

```
D-1  keys sent by the relay: [levelname, levelno, lineno, msg, name, pathname, process, processName] → no fields
D-2  logger created before apply_otel → reaches OTel / created after → does not reach OTel
```

### E — Value types

| Input | Result |
|---|---|
| `str`, `int`, `float`, `bool`, `None` | As is |
| `UUID`, `Path`, `Decimal`, `set` | `str` |
| `["a", "b"]` | tuple |
| `["a", 1]` | `None` — dropped after a warning |
| `{"cpu": 4}` | dict |
| `StrEnum` member | The Enum object as is |

### G — contextvar propagation boundaries

```
OK    await / create_task / gather / call_soon / asyncio.to_thread
LOST  loop.run_in_executor
LOST  threading.Thread
```

### H — `LogRecord` attribute collisions, trace, overhead

H-1 `LogRecord` attributes that break `extra=` (on collision, `KeyError: Attempt to overwrite '<name>' in LogRecord` and the log line is lost):

```
name  module  message  asctime  process  processName  thread  threadName
filename  lineno  levelname  msg  args  exc_text  created  taskName
```

H-2 Logs inside a span carry `trace_id`/`span_id` automatically.

H-3 Cost per call (200,000 calls):

| Condition | ns/call |
|---|---|
| Level disabled, 0 / 10 fields | 299 / 300 |
| Level enabled, 0 / 2 / 10 fields | 4,622 / 4,832 / 5,673 |
