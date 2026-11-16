# Manager Views layer: Guardrails

## Purpose

The place for values used internally only across the board. Unlike `data/`, these are not converted to DTOs and sent
externally (`manager/data/AGENTS.md`). For example, a read-projection assembled from an ORM row and passed to the
sokovan coordinator and scheduling layer belongs here.

## Type rules

- A plain `@dataclass` (no framework dependencies such as SQLAlchemy, Pydantic, aiohttp).
- May import enums and identifiers from `data/` and `common/data/entity/` (views sit above data).
- No business-logic methods: pure containers.
