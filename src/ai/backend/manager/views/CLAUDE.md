# Manager Views Layer — Guardrails

> Internal read-projection dataclasses passed to coordinators / scheduling.

## Purpose

Read-projections assembled from ORM rows and handed to the coordinator /
scheduling layer. Unlike `data/`, these are **never serialized to an external
API** — they exist only to carry the slice of state a scheduling decision needs.

## Type Rules

- Plain `@dataclass` (no framework deps — no SQLAlchemy, Pydantic, aiohttp).
- May import enums / identifiers from `data/` and `common/identifier/`
  (views sit above data).
- No business logic methods — pure containers.
