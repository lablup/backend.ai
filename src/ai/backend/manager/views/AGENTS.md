# Manager Views layer — Guardrails

> The place for internal-only value objects (read-projections, etc.).

## Purpose

The place for values used internally only across the board. Unlike `data/`, these are not converted to DTOs and sent
externally (`manager/data/AGENTS.md`). For example, a read-projection assembled from an ORM row and passed to the
coordinator / scheduling layer belongs here.

## Type rules

- A plain `@dataclass` (no framework dependencies — no SQLAlchemy, Pydantic, aiohttp).
- May import enums / identifiers from `data/` and `common/identifier/` (views sits above data).
- No business-logic methods — pure containers.
