---
name: error-code-and-status-axes
type: design-rationale
description: The error-code triple and its no-underscore constraint, error code and HTTP status as independent axes, mixin-less base errors, GraphQL carrying only the code, absence of a central code registry, the separation from common/exception.py and the legacy manager/exceptions.py, the errors that stay on BackendAIError for want of a declared row type
scope: src/ai/backend/manager/errors
keywords: [BackendAIError, ErrorCode, ErrorDomain, ErrorOperation, ErrorDetail, ObjectNotFound, EntityError, FieldError, problem+json, exceptions.py]
sources:
  - src/ai/backend/common/exception.py
  - src/ai/backend/manager/api/rest/middleware/exception.py
  - src/ai/backend/manager/api/gql/extensions/exception_handler.py
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: stable
---

# Manager errors — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

Domain errors are a public contract — every failure that leaves the manager
carries a machine-readable code and an RFC-7807 body, and clients branch on the
code instead of parsing messages. This package exists to keep that contract in
one place per domain.

## The code triple has exactly one format constraint

- `ErrorCode` is `(domain, operation, error_detail)`, rendered as `domain_operation_detail` and parsed by splitting on `_` — **no underscores in enum values** (hyphenate compound words).
- There is no central code registry — uniqueness is enforced nowhere, and the only machine-readable surface is the generated OpenAPI document.
- Before defining a new error, check both `manager/errors/` and `common/exception.py` (which holds about 40 concrete errors).

## Code and HTTP status are independent axes

- HTTP status comes solely from the class-base aiohttp mixin (`web.HTTPNotFound` → 404) — the code describes the failure, not the status.
- That is why concrete exceptions **must inherit a status mixin at definition time** — the defining side cannot know when an exception will surface externally (as an HTTP response), and a mixin-less exception that leaks out becomes a generic 500 instead of a meaningful status.
- Domain base errors (`RepositoryError` and 8 others) deliberately have no mixin — a status on the base would precede the subclass's own mixin in the MRO. Never raise them directly.
- GraphQL drops the status and carries only the code string in `extensions.code`; REST renders `problem+json`.
- A handler that leaks a non-`BackendAIError` exception loses the code — the middleware force-converts it to a generic code.

## Reuse by subclassing concrete errors

- `ObjectNotFound` builds its title from `object_name`, and about 20 domain not-found errors inherit it setting only `object_name`.
- When the meaning fits, extend an existing concrete error rather than deriving fresh from `BackendAIError`.

## Some errors stay on `BackendAIError`

These name no declared row type, so they keep an `ErrorDomain`. Declaring the
type is what reopens the decision.

| Error | Why it stays |
|---|---|
| `RoleAlreadyAssigned`, `RoleNotAssigned` | the `user_roles` row has no `EntityType` or `FieldType` |
| `InvalidFieldPermission` | validates a requested field scope for both permission entries and entity shares, so it names no one row kind |
| `VirtualEntityNotFound` | `data/entity/virtual_entity.py` declares an id alone, no `EntityType` |
| `NotEnoughPermission` | an authorization denial about the caller, not about a row |
| `DeploymentDefinitionFileReadError` | a file inside a vfolder, which no row type declares |
| `NoUpdatesToApply` | a modifier that changed nothing; the row is whichever one the caller was updating |
| `AppServiceStartFailed` | an app started inside a session is no row, and `ActionOperationType` has no `start` |
| `AppProxyConnectionError`, `AppProxyResponseError` | AppProxy is a system domain by the `AGENTS.md` table |

## The legacy neighbor is a different kind

- `manager/exceptions.py` is internal non-HTTP plumbing (`AgentError`, `RPCError`, the kernel `status_data` TypedDict) — not domain errors.
- Beware the name collision: its `ErrorDetail` TypedDict is unrelated to the `ErrorDetail` enum in `common/exception.py`.
