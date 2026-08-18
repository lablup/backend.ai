# Manager Actions layer — Guardrails

> For design background, see `KNOWLEDGE.md` in the same directory. Action classes
> live in `services/{domain}/actions/`; file placement and naming rules are in
> `services/AGENTS.md`.

## Bases

New actions inherit only from the v2 bases (`actions/v2/`). The shape of the target
decides the shape. Do not create new subclasses of the legacy `BaseAction` bases
(`actions/action/`).

| Shape | Target |
|---|---|
| `single_entity` | one entity |
| `bulk` | several entities |
| `scope` | the scope itself — searches within it, and creates |
| `global` | none (system-wide) |
| `lookup` / `bulk_lookup` | an external key into an internal id |
| `single_field` / `bulk_field` | field rows |

## What an action takes

- **An operation naming existing rows** (`single_entity` / `bulk` / the field shapes)
  takes those rows' ids and nothing else. A field action does not take the owning
  entity's id alongside: confirming that the two really stand in that relation takes
  the same query anyway, and trusting the value without it lets a caller pass its own
  owner beside somebody else's row.
- **A create** takes the scope it applies to — the parent entity for an entity, the
  owning entity's id for a field row. There is no row to name yet, so this is an input.

## Actions naming a field row

- Every operation is answered for by an entity: both validation and the audit trail
  ask which entity it was about.
- A field row carries no membership of its own. What it belongs to is only knowable
  through the entity that owns it.
- **Which end the operation starts from decides the check.** Starting from a field row
  means its membership is unknown and the owner has to be read first; starting from an
  entity means the value to check is already in hand.
- So a field action names no entity directly — it names the **lookup action** that
  reads the owning one. The processor runs that lookup first, then runs the same
  `single_entity` / `bulk` validators and monitors against what came back.
- The other direction — **an entity id and no field id** — names where to look, not
  what to touch, so it is `scope`-shaped: the owner is the scope. Reading one owner's
  field rows is that, and ops applies the scope's condition rather than leaving it to
  the searcher. Nothing was named, so there is no owner to read.
- Its result names no entity: a field row is not one. Which owner the read stayed
  inside is on the action's scope targets, which the audit row is tied to.
- Creating a field row takes the owning entity's id for the same reason: it writes
  inside that entity's scope and is answered for by it.
- Neither contradicts "an operation naming existing rows takes their ids and nothing
  else". What that forbids is passing an owner **alongside a named row**.
- Every write to a field row declares `operation_type() == UPDATE` — create, edit,
  delete and purge alike. Adding or removing a row is a change to that entity, and it
  is that entity's permission that answers for it. Only a read is `GET`.
- A bulk reads the owners in one go. They may be several, and every one is checked.
- The answer is per **row** the caller named; the record is per **entity** owning
  those rows. Which row it was goes in the description — the entity columns take
  entity ids only.
- A row that is gone ends at the lookup, whose record carries the key in
  `lookup_kind` / `lookup_key`.

## Wiring

- Create every v2 processor through the `ProcessorGroup` factory, passing the action
  class as the first argument — the registry accumulates the wired actions
  (`ProcessorRegistry.wired_actions()`).
- Field operations come from the sub-group `ProcessorGroup.field_group(data type,
  lookup action, bulk lookup action)` hands out. It builds the owner lookups itself:
  they are not operations a domain wires, only the step every field operation runs
  first.
- Register all new wiring in `tests/unit/manager/actions/test_registry_catalog.py`.

## Many-row writes

- The failure mode is named, never an argument: an `AtomicCreate*` base raises and the
  run is recorded as one failure, a `PartialBulk*` base answers per target and the run
  itself succeeds. No base is unmarked.
- `Bulk` in a name means the bulk shape — the caller named the targets, so each is
  answered for. A many-row write whose target is a single scope, a single owner, or
  the system is not bulk-shaped.

## Soft delete

- A soft delete inherits a `Delete*` base so it declares `operation_type() == DELETE`,
  and carries an updater that writes only the lifecycle column
  (`models/specs/AGENTS.md`). It runs through the update path; the declared operation
  is what RBAC checks and what the audit row records.
- The reverse transition inherits a `Restore*` base and declares `RESTORE`: the audit
  says restore while the permission checked stays soft-delete.
- Do NOT reach the same transition through an update-shaped action — it would be
  recorded as `UPDATE` and the deletion would vanish from the trail.

## Gates

- `global` extends `scope` to the whole installation and runs behind the SUPERADMIN
  gate. Global reads open to all authenticated users are wired via the `public_*`
  factories — read operations only; the constructor rejects writes.
- `lookup` and `bulk_lookup` check authentication first and the permission on whatever
  the key resolved to after. The check splits in two because the entity a key names is
  not known until the run produces it. The second half takes the `single_entity` and
  `bulk` validators respectively — `LOOKUP` is a read, so it asks for read on that
  entity.
- A key that named nothing offers no entity to check. It is one failed key.
- Wiring through `public_lookup_ops` leaves the second half empty, so every
  authenticated caller may resolve.
- Adapters must return the same response for a lookup miss and for a permission denial
  (no existence leakage).
- The owner lookup a field operation runs first is checked the same way. It is a
  different permission from the write that follows — the lookup asks for read, the
  write for write.
- `BaseGlobalAction` declares no `entity_id()`.

## Monitors

- Monitors must never fail an action — swallow and log.
- Do not move validation outside the monitor lifecycle — denials must also leave an
  audit row.
