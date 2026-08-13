---
name: error-code-and-status-axes
type: design-rationale
description: The error-code triple and its no-underscore constraint, error code and HTTP status as independent axes, mixin-less base errors, GraphQL carrying only the code, absence of a central code registry, the separation from common/exception.py and the legacy manager/exceptions.py
scope: src/ai/backend/manager/errors
keywords: [BackendAIError, ErrorCode, ErrorDomain, ErrorOperation, ErrorDetail, ObjectNotFound, problem+json, exceptions.py]
sources:
  - src/ai/backend/common/exception.py
  - src/ai/backend/manager/api/rest/middleware/exception.py
  - src/ai/backend/manager/api/gql/extensions/exception_handler.py
generated:
  by: claude-code/fable-5
  at: 2026-08-10
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

## The legacy neighbor is a different kind

- `manager/exceptions.py` is internal non-HTTP plumbing (`AgentError`, `RPCError`, the kernel `status_data` TypedDict) — not domain errors.
- Beware the name collision: its `ErrorDetail` TypedDict is unrelated to the `ErrorDetail` enum in `common/exception.py`.
