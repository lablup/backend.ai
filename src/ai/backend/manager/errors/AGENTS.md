# Errors

`errors/{domain}.py` holds this component's `BackendAIError` subclasses (e.g. `user.py`, `session.py`); `errors/base/` holds the two bases they build on. The "inherit from `BackendAIError`, never raise built-ins" rule lives in the root `AGENTS.md`.

## Rules

1. An error about an entity inherits `EntityError` (`errors/base/entity.py`); one about a field row inherits `FieldError` (`errors/base/field.py`). Their `ErrorCode.domain` comes from the row's type; do not pick an `ErrorDomain` for them.
2. An error class is defined under `manager/errors/` and nowhere else. `exceptions.py` modules in `sokovan`, `plugin`, `dependencies`, `models` are to be moved here, not extended.
3. Error modules are split per domain (`errors/{domain}.py`, later `errors/{domain}/`).
4. One meaning, one class. Before defining, search for an existing class with the same name or the same code.

Three bases, drawn by what the error is about:

| The error is about | Base | `ErrorCode.domain` |
|---|---|---|
| An entity (user, session, vfolder, ...) | `EntityError` | `EntityType` of that entity |
| A field row (kernel, keypair, replica, ...) | `FieldError` | `{owner entity}-{field row}`; a dangling kind (`DanglingFieldType`, e.g. audit_log) reports its own alone |
| The system (api, auth, database, bgtask, plugin, leader-election, message-queue, event, watcher, health-check, metric, storage-proxy, appproxy, external-system) | `BackendAIError` | `ErrorDomain` |

The row types come from the identifiers: `EntityIdentifier.entity_type()`, `FieldIdentifier.field_type()`. A field type answers its own owner, so nothing beside it declares one. A spec that names a row by key declares the type on itself (`DataLookup.entity_type()`, `FieldKeyLookup.field_type()`).

## Base and enums

`ai.backend.common.exception` defines `BackendAIError` and the enums `ErrorDomain` / `ErrorOperation` / `ErrorDetail` / `ErrorCode`. `ErrorCode.domain` is an open `str`: an `ErrorDomain` value for a system error, the row's type for an entity or field error. `str(ErrorCode)` stays `{domain}_{operation}_{detail}` and splits on `_`, so **no part carries an underscore**. A type spells itself in snake_case for the database and the graph; the error bases hyphenate it on the way into the domain and nothing else rewrites it. Other components mirror this layout: `{agent,storage,appproxy/*}/errors/{domain}.py`.

## Find an existing error before defining a new one

```bash
grep -rn "class .*BackendAIError" src/ai/backend/manager/errors   # this component
grep -rn "class .*BackendAIError" src/ai/backend                  # all components
```

## Define

An entity or field error subclasses `EntityError` / `FieldError` plus the matching aiohttp
HTTP type, and **answers with its triple instead of declaring it in fields** — the way
every error answers with its code. `operation` is an `ActionOperationType`, not an
`ErrorOperation`: a row is acted on with the action vocabulary, and the base maps it to
the code's operation.

```python
class AgentAlreadyExited(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/agent-already-exited"
    error_title = "Agent has already exited."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            AgentEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )

raise EntityNotFoundError(msg, entity_type=entity_id.entity_type(), operation=ActionOperationType.PURGE)
raise FieldNotFoundError(msg, field_type=field_id.field_type())
```

A root that still owes its code cannot be constructed: `ErrorMeta` refuses it, because
`Exception.__new__` skips the check `ABCMeta` records for an ordinary abstract class.

`EntityNotFoundError` and `FieldNotFoundError` share `NotFoundError`, so a caller that
answers the same way for a missing entity and a missing field row catches that one name.

A system error subclasses `BackendAIError` plus the matching aiohttp HTTP type, and implements `error_code()`:

- A concrete exception **MUST inherit an HTTP status type (`web.HTTP*`) at definition
  time** — there is no telling when it will surface externally, and a status-less
  exception leaks out as a generic 500. Only domain bases that are never raised
  directly stay mixin-less.

```python
class UserNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/user-not-found"
    error_title = "The user does not exist."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
```

Pick `domain` / `operation` / `error_detail` from the enums in `common/exception.py`; add a new enum value there if none fits. Do not add an entity name to `ErrorDomain`: that is what `EntityError` is for.
