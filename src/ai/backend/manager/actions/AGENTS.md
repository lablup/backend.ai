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

## Many-row writes

- An action that writes several rows says which failure mode it takes: an
  `AtomicCreate*` base raises and the run is recorded as one failure, a
  `PartialBulk*` base returns per-entity verdicts and the run itself succeeds.
  No base is unmarked, and the mode is never an argument.
- `Bulk` in a base name means the `BaseBulkAction` shape — the caller named the
  entities, so each is answered for. A many-row write whose target is a single
  scope, owner, or the system is not bulk-shaped.

## Soft delete

- A soft delete inherits a `Delete*` base so it declares
  `operation_type() == DELETE`, and carries an updater that writes only the
  lifecycle column (`models/specs/AGENTS.md`). It runs through the update path;
  the declared operation is what RBAC checks and what the audit row records.
- The reverse transition inherits a `Restore*` base and declares `RESTORE`, never
  `UPDATE` — the audit says restore while the permission checked stays
  soft-delete.
- Do NOT reach the same transition through an update-shaped action — the run
  would be recorded as `UPDATE` and the deletion would vanish from the trail.

## Gates

- `global` extends `scope` to the whole installation and runs behind the SUPERADMIN
  gate. Global reads open to all authenticated users are wired via the `public_*`
  factories — read operations only; the constructor rejects writes.
- `lookup` verifies authentication only. Adapters must return the same response
  for a lookup miss and for a permission denial on the follow-up action
  (no existence leakage).
- An operation that designates entities by id is `single_entity` (one) or `bulk`
  (several).
- `BaseGlobalAction` declares no `entity_id()`.

## Monitors

- Monitors must never fail an action — swallow and log.
- Do not move validation outside the monitor lifecycle — denials must also
  leave an audit row.
