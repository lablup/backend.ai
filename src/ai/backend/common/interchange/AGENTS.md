# `common/interchange` guardrails

The bodies components send each other. A type belongs here when one component produces it,
another consumes it, and it therefore has to survive serialization — event payloads and RPC
payloads.

## Rules

- **Contents**: pydantic models only. Every field must be JSON-representable and round-trip
  unchanged — no `Any`, and no type that only survives pickling (`ResourceSlot`, `SlotName`,
  `BinarySize`, `Path` used as a bare value).
- **Carry what the consumer reads.** A payload mirrors the contract between the two components,
  not the producer's internal struct. A field no consumer reads does not belong on the wire; keep
  it in the producing component.
- **Organized by domain**, one module per domain (`interchange/kernel.py`), not by component —
  a payload has two sides, so neither side owns the directory.
- **Dependency direction (leaf)**: depend only on lower `common` modules (`common.types`,
  `common.identifier`). MUST NOT import from `manager` / `agent` / `storage`, or from
  `common.dto`.
- **No business logic.** A conversion that only reshapes the payload's own fields is fine
  (`to_resource_slot_entries()`); anything that needs a repository, a config, or another entity is
  not.

## How this differs from its neighbours

| Package | Holds |
|---------|-------|
| `interchange/` | Payloads crossing a component boundary — serialized by definition |
| `dto/` | API request/response contracts, per target component (`dto/manager/v2/...`) |
| `schema/` | Pydantic types the manager persists as a JSON DB column |
| `data/` | Value objects passed within a component |

When a payload type also has to be persisted as a column, it belongs in `schema/`, and
`interchange/` may reference it.
