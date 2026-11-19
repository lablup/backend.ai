# `common/tristate`: Guardrails

The sentinel for a field an update request did not send: `Unset` (annotation), `UNSET` (value).
It lives on the wire only; nothing stores it.

Schema declaration and conversion rules are in `common/dto/AGENTS.md`.

## Dependency direction (leaf)

- Do not import any other `ai.backend` module, including the rest of `common`.

## Use

- Read a field only through `TriState.from_unset` / `OptionalState.from_unset`.
- Do not use `from_nullable`: it reads `UNSET` as a value to write.
- Do not test it with `bool()`: `UNSET` is truthy.
- Narrow a nested request model on that model's own class.
- A direct test uses `isinstance(value, Unset)`. `value is UNSET` does not narrow the type.
