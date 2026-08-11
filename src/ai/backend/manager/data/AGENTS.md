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

## A row projection mirrors one row

Two kinds of type live here, and only the first takes this rule:

- **Row projection** — what a `Row.to_data()` returns. It carries its own table's
  columns and nothing else. Another entity is named by its foreign-key value
  (`channel_id`), never embedded.
- **Composite** — assembled by a repository, service or adapter from several
  reads. It may nest row projections, because nothing converts a single row into
  it.

A row projection that nests another entity forces the conversion to read a
relationship, which forces an ORM `relationship()` and an eager load on every
read that produces it — and puts the domain out of reach of the single-entity
read/write specs (`models/specs/`). Assemble the composition one layer up
instead: a GraphQL field resolver over a dataloader, or a repository method that
joins and returns the pair.

## Legacy distinction

- For types that support legacy paths rather than the v2 / GraphQL path, it is recommended to add `Legacy` to the name —
  so that, where possible, legacy types can be distinguished from v2 types.

## What does NOT belong here

- Business-logic methods (pure data containers only).
- Pydantic models — use `manager/dto/` or `common/dto/` for request/response types.
- default-factory fields that hide mutable state or complexity.
