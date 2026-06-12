# Common package — Guardrails

> All components (manager, agent, storage, client SDK) depend on this package.
> Changes here affect the entire system — check all callers before modifying anything.

## What belongs here

- Abstractions and utilities shared by two or more components.
- Base exception classes, event types, DTO base classes, common type definitions.
- Infrastructure clients used across components (Redis, etcd, message queue).

## What does NOT belong here

- Component-specific logic (manager session management, agent kernel handling, etc.).
- Imports from `manager/`, `agent/`, `storage/` — dependencies must flow inward only.

## Adding to this package

- Before adding a new module, confirm that multiple components really need it.
- Put single-component utilities in that component's package, not here.

## Sub-packages

| Sub-package | Purpose |
|-------------|------|
| `common/events/` | Event type definitions and dispatcher — see existing `AbstractEvent` subclasses |
| `common/bgtask/` | Background task framework — extend `BaseBackgroundTaskHandler` |
| `common/dto/` | Inter-component DTOs — see `common/dto/AGENTS.md` |
| `common/exception.py` | Root `BackendAIError` and `ErrorCode` — all component exceptions inherit from here |
| `common/types.py` | Common base types used across layers |

## Exceptions

- `common/exception.py` defines the root hierarchy — do NOT add component-specific exceptions here.
- Adding common exception base classes is allowed, concrete domain exceptions are not.
