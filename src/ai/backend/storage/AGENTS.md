# Storage Proxy: Guardrails

> For a component overview, see `src/ai/backend/storage/README.md`.

## API handlers

- Every handler must be a method of a typed handler class: no module-level async functions.
- Use the `@api_handler` or `@stream_api_handler` decorator.
- Parse requests with `PathParam[T]`, `BodyParam[T]`: do not access the raw request object directly.

## Exceptions

- All exceptions must inherit from `StorageProxyError` (which inherits from `BackendAIError`).
- `storage/exception.py` is legacy: do not add new exceptions here.
- Put new exceptions only in `storage/errors/`, organized by feature: `object.py`, `quota.py`, `vfolder.py`,
  `volume.py`, `process.py`.

## Storage volume plugins

- Add new storage backends as plugins under `storage/volumes/`.
- Every plugin must implement the abstract volume interface: no duck-typing shortcuts.

## State storage

- Storage does not use a relational DB: state uses etcd and Valkey only.

## What belongs here

- File/volume operations, quota management, vfolder lifecycle.
- Storage-related background tasks (scan, cleanup, migration).
