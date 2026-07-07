# `common/schema` guardrails

Shared pydantic schema definitions used across components. A type belongs here when it is a
pydantic schema that both the manager (as a **pydantic column type**, persisted as JSON on ORM
rows) and lower layers such as `manager/data` must reference, and keeping it in an upper layer
would force an upward import.

## Rules

- **Contents**: pydantic schema definitions. Plain value dataclasses are allowed only when they
  are the I/O of a schema's methods and cannot live elsewhere without recreating an upward import.
- **May be referenced by**: any component, including `manager` and `manager/data`.
- **Dependency direction (leaf)**: depend only on lower `common` modules (e.g. `common.types`).
  - MUST NOT import from `manager`, or from any component/upper layer.
  - MUST NOT import from `common.dto`. The direction is one-way: **`dto` may depend on `schema`,
    `schema` MUST NOT depend on `dto`.**
