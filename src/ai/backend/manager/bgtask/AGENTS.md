# Background Tasks

One task per file in `tasks/`. Base classes are in `ai.backend.common.bgtask.task.base`.

## Add a task

1. Add a `ManagerBgtaskName` value in `types.py`.
2. In `tasks/{name}.py` define three pieces:
   - **Manifest** (`BaseBackgroundTaskManifest`, frozen Pydantic) — task inputs; give each field `Field(description=...)`.
   - **Result** (`BaseBackgroundTaskResult`) — outputs, or `None`.
   - **Handler** (`BaseBackgroundTaskHandler[Manifest, Result]`) — implement `name()`, `manifest_type()`, and `async execute(manifest)`.
3. Register the handler in `dependencies/processing/bgtask_registry.py` (import + instantiate with its deps + `registry.register(...)`). Skipping this fails startup.

## Rules

- Raise `BgtaskFailedError` / `BgtaskCancelledError` (from `common.exception`), not generic exceptions.
- Progress reporting (`common/bgtask/reporter.py`) is not yet wired into manager handlers — do not build a task that depends on it.
