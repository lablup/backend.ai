# `common/tristate` — Guardrails

The sentinel for a field an update request did not send — `Unset` (annotation), `UNSET` (value).
It lives on the wire only; nothing stores it.

Schema declaration and conversion rules are in `common/dto/AGENTS.md`.

## Dependency direction (leaf)

- Depend only on lower `common` modules.
- Do NOT import `manager`, `agent`, `storage`, or `common.dto`.

## Use

- Read a field only through `TriState.from_unset` / `OptionalState.from_unset`.
- Do NOT use `from_nullable` — it reads `UNSET` as a value to write.
- Do NOT test it with `bool()` — `UNSET` is truthy.
- Narrow a nested request model on that model's own class.
- A direct test uses `isinstance(value, Unset)`. `value is UNSET` does not narrow the type.
