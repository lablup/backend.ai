# Manager Data Layer — Guardrails

> Pure domain types only — no framework dependencies allowed here.

## Purpose

Immutable value objects that sit between ORM Row objects and the Service/API layers.
No SQLAlchemy, Pydantic, or aiohttp imports are permitted in this package.

## Directory Structure (per domain)

Each domain follows: `data/{domain}/__init__.py` (re-exports) + `types.py` (frozen dataclasses).

## Type Rules

- All data classes MUST be `@dataclass(frozen=True)`.
- Allowed imports: Python stdlib and `ai.backend.common.types` — nothing else.
- Do NOT import from `manager/models/`, `manager/repositories/`, `manager/services/`,
  or any external framework (`pydantic`, `sqlalchemy`, `aiohttp`).

## What Does NOT Belong Here

- Business logic methods (pure data containers only).
- Pydantic models — use `manager/dto/` or `common/dto/` for request/response types.
- Mutable state or default-factory fields that hide complexity.
