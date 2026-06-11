# Common Package — Guardrails

> Every component (manager, agent, storage, client SDK) depends on this package.
> A change here affects the entire system — verify all callers before modifying anything.

## What Belongs Here

- Abstractions and utilities shared by two or more components.
- Base exception classes, event types, DTO base classes, shared type definitions.
- Infrastructure clients (Redis, etcd, message queue) used across components.

## What Does NOT Belong Here

- Component-specific logic (manager session management, agent kernel handling, etc.).
- Any import from `manager/`, `agent/`, or `storage/` — dependency must flow inward only.

## Adding to This Package

- Before adding a new module, confirm it is genuinely needed by multiple components.
- Single-component utilities belong in that component's own package, not here.

## Sub-package Highlights

| Sub-package | Purpose |
|-------------|---------|
| `common/events/` | Event type definitions and dispatcher — see existing AbstractEvent subclasses |
| `common/bgtask/` | Background task framework — extend `BaseBackgroundTaskHandler` |
| `common/dto/` | Cross-component DTOs — see `common/dto/CLAUDE.md` |
| `common/exception.py` | Root `BackendAIError` and `ErrorCode` — all component exceptions inherit from here |
| `common/types.py` | Shared primitive types used across layers |

## Exceptions

- `common/exception.py` defines the root hierarchy — do NOT add component-specific exceptions here.
- New shared exception base classes are acceptable; concrete domain exceptions are not.
