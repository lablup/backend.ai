---
name: write-spec-design
type: design-rationale
description: write-spec selection criteria (Entity/Global/Field), why the three roots share no common ABC, why the role-managed root is not an EntityCreator subtype, the distinction between member_of and cap-based sharing, open scope-type strings
scope: src/ai/backend/manager/models/specs
keywords: [EntityCreator, GlobalEntityCreator, FieldEntityCreator, RoleManagedEntityCreator, RoleTemplateSource, member_of, scope_of, virtual-scope, preset-role, DataUpdater, soft-delete]
sources:
  - src/ai/backend/manager/models/specs/creator.py
  - src/ai/backend/manager/models/specs/role_template.py
  - src/ai/backend/manager/repositories/ops/v2
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Write specs — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

Write specs turn "what to write" (rows, scopes, memberships, integrity checks)
into declarations next to the schema, while execution is owned by the ops layer.
It exists so that the RBAC side effects of a write (scope provisioning,
membership registration) are decided by the **spec's type**, not by the
execution path.

## Spec selection: the only remaining question is "is it an entity"

**Every entity doubles as a scope** — it can own memberships and can be shared.

| Spec | Criterion | Write behavior |
|--------|-----------|----------------|
| Entity | First-class entity (vfolder/session/...) | create provisions the row's virtual scope node (self membership + self binding) and joins each `member_of()` scope; purge tears down symmetrically; upsert stays idempotent |
| Entity, role-managed | Entities that grant preset roles (domain/project/user) | Entity behavior + preset role creation — must be declared via the combined `RoleManagedEntity*` root (see section below) |
| Global | System-wide state outside the scope hierarchy | Plain insert/delete/upsert |
| Field  | Owned by another entity and authorized through its owner (even with its own get/delete API) | create requires `owner_id`; purge is a plain delete |

## The absence of a common ABC is itself the enforcement mechanism

- With a shared supertype, an entity spec passed to a scope-less execution path would pass type checking and silently skip scope provisioning — exactly the bug this lineage is meant to prevent.
- Duplicating method declarations across roots is the price of making that path inexpressible.
- Execution-logic reuse happens via ops helpers that take plain values — not via a shared supertype.

## The role-managed root not being a subtype is the same mechanism

- If `RoleManagedEntityCreator` were a subtype of `EntityCreator`, it would pass type checking on the plain `create_entity` path and silently skip preset roles.
- The entity hooks are duplicated onto the combined root so that the only path that accepts it is the role-managed path.
- `RoleTemplateSource` remains the sole shared base because no write path accepts it on its own.

## Soft delete is guarded by the absence of a field

The same mechanism as the spec roots: what stops a write is the shape of the
declaration, not a check at execution time.

A soft delete is an UPDATE at the DB, so ops cannot tell it apart from an edit —
there is no delete operation to generalize and no place there to enforce
anything. What separates them is the action's `operation_type()`, which decides
the RBAC permission and the audit row's `operation`.

That leaves one hole: an ordinary edit that writes the lifecycle column would be
recorded as `UPDATE`, and the deletion would never appear in the trail. Removing
the field from the general updater closes it — the edit path has nothing to make
the transition with. Splitting delete and restore into their own updaters with
constant `build_values()` closes the rest: a transition value taken as an
argument is a value that can be passed wrong.

Which column carries the state is domain knowledge and varies (`deleted` on a
role preset, `status` on a vfolder or user), which is why this is a rule about
the general updater's fields rather than about a column name.

## member_of is membership, not sharing

- `member_of(row)` declares ontological belonging at creation time — a project joins its domain, a keypair joins its user.
- It carries no permission caps — cap-bounded access is the object-sharing mechanism applied to existing entities and has its own audit trail.
- Keeping the two separate keeps creation declarative and sharing revocable.

## Scope-type is an open string

- This is so a new scope-like type can register members before the permission layer knows about it — only permission-carrying paths convert lazily and reject there.
- The registration-time integrity guarantee is: "a write against a target without a virtual scope node fails".
- Direction: **scope type will be unified into entity type** — since every entity doubles as a scope, there is no remaining reason to keep a separate type axis.
