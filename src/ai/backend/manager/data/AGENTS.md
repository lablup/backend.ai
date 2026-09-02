# Manager Data layer — Guardrails

> Pure domain types only — no framework dependencies.

## Purpose

Immutable value objects that sit between the ORM Row and the Service/API layers. These are **values converted to DTOs when
sent externally** (the transmission itself is done by the DTO, which is constructed from these `data` values). Values used
internally only, without being converted to DTOs, go in `views/` (`manager/views/AGENTS.md`).

This package does not allow SQLAlchemy, Pydantic, or aiohttp imports.

## Directory structure (per domain)

Per domain: `data/{domain}/__init__.py` + `types.py` (frozen dataclass). Existing `__init__.py` re-export the
dataclasses (established pattern); for new code, do not add re-exports — import the module directly (root global rule).

## Type rules

- Every data class must be a `@dataclass(frozen=True)`.
- Allowed imports: Python stdlib and `ai.backend.common.types` — nothing else.
- Do NOT import from `manager/models/`, `manager/repositories/`, `manager/services/`, or external frameworks (`pydantic`,
  `sqlalchemy`, `aiohttp`).

## `EntityData` / `FieldData` carries what its own domain's row holds

- Its own row's columns only. Reading a relationship or carrying a joined value is not
  allowed; another entity is named by its foreign-key value (`channel_id`).
- A composite type that inherits neither is the exception.
- A value spanning several rows is served by a repository in the service layer, not
  folded into ops. Where a calculation is involved or many rows are, it becomes a
  repository method of that domain.
- A virtual entity id (`virtual_entities.id`) never appears on a data type. It names a
  graph node, not an entity or a field; the data type carries the entity the node
  stands for, read by the query that read the row.
- An entity a row names is carried as one `EntityIdentifier` (`RuntimeEntityID` where
  the kind is a value), not as an `entity_type` / `entity_id` pair.

## Legacy distinction

- For types that support legacy paths rather than the v2 / GraphQL path, it is recommended to add `Legacy` to the name —
  so that, where possible, legacy types can be distinguished from v2 types.

## What does NOT belong here

- Business-logic methods (pure data containers only).
- Pydantic models — use `manager/dto/` or `common/dto/` for request/response types.
- default-factory fields that hide mutable state or complexity.
