# Errors

`errors/{domain}.py` holds this component's `BackendAIError` subclasses (e.g. `user.py`, `session.py`). The "inherit from `BackendAIError`, never raise built-ins" rule lives in the root `AGENTS.md`.

## Base and enums

`ai.backend.common.exception` defines `BackendAIError` and the enums `ErrorDomain` / `ErrorOperation` / `ErrorDetail` / `ErrorCode`. Other components mirror this layout: `{agent,storage,appproxy/*}/errors/{domain}.py`.

## Find an existing error before defining a new one

```bash
grep -rn "class .*BackendAIError" src/ai/backend/manager/errors   # this component
grep -rn "class .*BackendAIError" src/ai/backend                  # all components
```

## Define

Subclass `BackendAIError` plus the matching aiohttp HTTP type, and implement `error_code()`:

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

Pick `domain` / `operation` / `error_detail` from the enums in `common/exception.py`; add a new enum value there if none fits.
