---
name: idle-checker-assignment-service-shapes
type: decision-table
description: idle_checker_assignment knowledge - why a binding is a relation and not an entity, why its writes are the rbac boundary's and only the reads stay here, why the id the API names is resolved by a lookup first, what a permission on a binding has to name, why enabled is the relation lifecycle
scope: src/ai/backend/manager/services/idle_checker_assignment
keywords: [CreateRelationAction, DeleteRelationAction, RestoreRelationAction, PurgeRelationAction, LookupIdleCheckerAssignmentAction, LookupIdleCheckerAssignmentByPairAction, ScopedSearchIdleCheckerAssignmentsAction, IdleCheckerAssignmentCreator, RelationCreator, RelationLifecycleUpdater, relation_group, IDLE_CHECKER_ENTITY_TYPE]
sources:
  - src/ai/backend/manager/services/idle_checker_assignment
  - src/ai/backend/manager/api/adapters/idle_checker_assignment
  - src/ai/backend/manager/repositories/idle_checker
  - src/ai/backend/manager/models/idle_checker
generated:
  by: claude-code/fable-5.1
  at: 2026-09-08
status: draft
---

# Idle checker assignment service — Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`. Relation
> rationale: `proposals/BEP-1075-entity-relation-operations.md`. The definition
> catalog: `../idle_checker/KNOWLEDGE.md`.

## A binding is a relation

- `idle_checker_bindings` links a scope (a domain, project, resource group, or user) to
  an idle checker. BEP-1075 lists it among the relation tables: both sides own it, so
  it is neither an entity nor a field, and it gets no virtual entity node.
- The scope is the relation's scope and the checker is its target, as a project is the
  scope of a container registry relation. Linking makes the scope govern the checker
  under READ and the checker read the scope.
- `enabled` is the row's lifecycle column. Switching it is `DeleteRelationAction` and
  `RestoreRelationAction`: the row alone changes and both reads stay, so a binding
  turned off is still listed and can be turned back on. Honouring the off state is the
  reconciler's job.

## The shapes

| Action | Shape | Wiring | Answered for by |
|--------|-------|--------|-----------------|
| link, switch off, switch back on, unlink | relation | `services/rbac` | the scope and the checker, each as itself |
| lookup, lookup by pair | lookup | `group.lookup` | READ on the resolved checker |
| admin_search | global | `group.global_scope` | the SUPERADMIN gate |
| scoped_search | scope | `group.scope` | READ on `idle_checker` in every named scope |

- The four writes are the rbac boundary's four relation actions, carrying this
  domain's creator, lifecycle updaters and purger as values. This domain declares no
  relation action of its own: which relation a run is about travels on the spec, so
  one wiring per direction serves every relation this system writes.
- A relation write answers with the pair alone, so the adapter reads the binding back
  through `lookup_by_pair` to build its payload.
- The reads and the lookups take the `idle_checker` group and declare that type. A
  scope reader sees a binding's checker through the READ govern the link wrote.
- The reads and the lookup are reads of what the relation reaches, the checker, so
  they take the `idle_checker` group and declare that type. A scope reader sees a
  binding's checker through the READ govern the link wrote.
- The scope row is a precondition on the creator. Its side of the pair carries no
  foreign key, so the spec declares the row that must be there and the relation write
  refuses with `IdleCheckerAssignmentScopeNotFound` before it looks for the node.
- The bindings never touch the legacy source: writes go through the relation write
  ops and reads through the same provider's read ops, always as a searcher. A row id
  is not an entity id, so no querier names one. The reconciler's reads stay on the
  legacy source beside them.

## The id the API names is resolved first

- The REST and GQL surfaces update and purge by binding id, while a relation is named
  by its pair. The adapter runs the lookup to turn the id into the pair, then the
  relation action.
- The lookup's resolved entity is the checker, so resolving costs READ on it, which a
  scope reader holds through the scope's govern. A caller who reads the checker
  nowhere gets the lookup shape's single answer, a 400 that hides whether the id
  exists; one who reads it through another scope resolves the pair and is then
  refused by the relation check with a 403.
- This keeps the API shape while BEP-1075 says a relation's row id does not leave.
  Naming the pair on the API is the follow-up that removes the lookup.

## What a permission on a binding has to name

- A relation is answered for by both sides. Turning a project's binding off costs
  SOFT_DELETE on the project and on the checker; unlinking costs HARD_DELETE on both.
  A scope grant alone does not reach it.
- The checker is a global entity, so a non-superadmin needs a grant naming it. In
  practice a scope administrator without one cannot toggle the bindings of that scope.
- A binding on a user's own scope names the user. Rights on a project the user
  belongs to do not reach it.

## Two searches, two gates

- `scoped_search` names every scope up front and is refused whole when one is out of
  reach; the rows are then OR'd across scopes. Its result reports the checkers the
  page reached, since a relation read answers with what the relation links.
- `admin_search` reads the whole table behind the SUPERADMIN gate.
