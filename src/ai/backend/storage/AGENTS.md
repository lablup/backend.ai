# Storage Proxy — Guardrails

> For component overview, see `src/ai/backend/storage/README.md`.

## API Handlers

- All handlers MUST be methods on a typed handler class — no module-level async functions.
- Use `@api_handler` or `@stream_api_handler` decorators.
- Parse requests via `PathParam[T]` and `BodyParam[T]` — never access the raw request object.

## Exceptions

- All exceptions MUST inherit from `StorageProxyError` (which inherits `BackendAIError`).
- `storage/exception.py` is legacy — do NOT add new exceptions there.
- All new exceptions go in `storage/errors/` only, organized by feature:
  `object.py`, `quota.py`, `vfolder.py`, `volume.py`, `process.py`.
- Never raise built-in exceptions (`RuntimeError`, `OSError`, etc.) directly in business logic.

## Storage Volume Plugins

- New storage backends MUST be added as plugins under `storage/volumes/`.
- Every plugin MUST implement the abstract volume interface — no duck typing shortcuts.

## Authentication

- Use Storage's own `token_auth_middleware` — do NOT copy `@auth_required` from `manager/api/`.
- The Storage proxy has its own auth model independent of the Manager.

## Database Independence

- Storage has its own database — NEVER share a DB connection or session with the Manager.
- Do NOT import Manager ORM models (`manager/models/`) from Storage code.

## What Belongs Here

- File/volume operations, quota management, vfolder lifecycle.
- Background tasks related to storage (scan, cleanup, migration).
