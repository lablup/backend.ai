# Manager Actions layer — Guardrails

> For design background, see `KNOWLEDGE.md` in the same directory. Action classes
> live in `services/{domain}/actions/`; file placement and naming rules are in
> `services/AGENTS.md`.

## Bases

- New actions inherit only from the v2 bases (`actions/v2/`). There are five families:
  - `single_entity` — one target id
  - `bulk` — a list of target ids
  - `scope` — the scope is the target (search within a scope, and create)
  - `global` — no RBAC target (system-wide)
  - `lookup` — resolve an external key to an internal id
- Do not create new subclasses of the legacy `BaseAction` family (`actions/action/`).

## Wiring

- Create every v2 processor through the `ProcessorGroup` factory, passing the
  action class as the first argument — the registry accumulates wired specs
  (`ProcessorRegistry.wired_specs()`); no hand-written action list exists.
- Register all new wiring in
  `tests/unit/manager/actions/test_registry_catalog.py` —
  otherwise `test_every_defined_v2_action_is_wired` fails.

## Gates

- `global` runs behind the SUPERADMIN gate. Global reads open to all
  authenticated users are wired via the `public_*` factories — read operations
  only; the constructor rejects writes.
- `lookup` verifies authentication only. Adapters must return the same response
  for a lookup miss and for a permission denial on the follow-up action
  (no existence leakage).

## Monitors

- Monitors must never fail an action — swallow and log.
- Do not move validation outside the monitor lifecycle — denials must also
  leave an audit row.
