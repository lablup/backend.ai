---
name: rbac-graph-write-boundary
type: decision-table
description: rbac service knowledge: why the relations and the project roster are wired here rather than in the domains they are about, what shape each takes, and where the counting and the tolerating live
scope: src/ai/backend/manager/services/rbac
keywords: [RbacRelationService, RbacRosterService, CreateRelationAction, PurgeRelationAction, BaseEntityRelationAction, ProjectRosterAction, EnrollUsersInProjectAction, WithdrawUsersFromProjectAction, RbacRelationRepository, RbacRosterRepository, V2RosterWriteOps]
sources:
  - src/ai/backend/manager/services/rbac
  - src/ai/backend/manager/repositories/rbac
  - src/ai/backend/manager/repositories/ops/v2/roster
generated:
  by: claude-code/opus-5
  at: 2026-09-07
status: stable
---

# RBAC graph writes — Knowledge

> Rules: `../AGENTS.md`. Design: `proposals/BEP-1075-entity-relation-operations.md`,
> `proposals/BEP-1076-project-membership.md`, `proposals/BEP-1077-project-scoped-ownership.md`.

The operations that build the permission graph are wired here rather than in the domains
they are about. A registry's allowed projects and a resource group's domains are the
same operation on two different pairs, and while each lived in its own domain the
permission asked was that domain's alone.

## The processor fields

`backend.ai mgr ops list --concern rbac` prints the wired list. Its output answers the
entity type, shape, operation, gate and backing.

## Why a relation is not the owning domain's operation

- A registry's allowed projects used to travel as an updater field, so the registry's
  UPDATE permission alone let a caller write the row and the project was never asked.
- A relation names two scopes and no entity type, so both are asked and neither answers
  for the other.
- The resource group's four association operations carried a binder that wrote
  `association_scopes_entities` beside the mapping row. The relation ops write the
  graph instead: the scope governs the target under READ, the target holds the scope
  under a READ share.

## Two actions cover every relation

- `CreateRelationAction` and `PurgeRelationAction` carry the pairs and the spec that
  says which relation they are, so one wiring per direction serves the registry, the
  resource group and whatever comes next.
- The spec is chosen where the request is read. An adapter holds a registry's projects
  or a resource group's allow list and knows which relation it is looking at; the
  service and the repository never do.
- A run carries every pair the request named, so no caller loops over the service. Each
  entity is asked once however many pairs name it, and the answer is per pair.
- A pair already linked is skipped in ops and answered `False`. Naming one twice is not
  something a caller has to avoid, so no call site catches a duplicate.
- The audit row records `create_relation` or `purge_relation` and the scopes it named.
  The pair is what tells one relation from another, not the name.
- What a run of several pairs *means* is still the caller's: the registry's "removing
  where nothing was linked raises" counts what came back.

## The roster is the contained case

- A user inside a project is one scope, not two: `scope_targets` is the project and
  `entity_type` is `user` (BEP-1076). It is a scope action, not a relation.
- Enrolling and the role grant land in one ops primitive. A user on a roster without the
  role the caller named is not a state the operation may leave behind.
- `enroll_members` narrows to the project's own domain and to users not already on the
  roster; `enroll_member` does neither, because the caller that uses it — a
  project-scoped role grant — has already decided.

## The personal-project refusal is an ops invariant

- A personal project takes no member beyond the user it was created with. The refusal is
  in `V2RosterWriteOps`, so no path reaches around it.
- The user provisioning path joins through the underlying primitive instead, because the
  owner is the one member such a project ever takes.
- The projects a user is enrolled in are narrowed by several callers, and a filter each
  of them applies is a filter each of them can forget.
- A roster write onto a project that is not there is refused for the same reason: an
  edge to nothing is not a state any caller asked for.

## Leaving takes the legacy association with it

- Nothing writes `association_scopes_entities` for a roster any more, but what an
  earlier release wrote is still what the legacy reads answer from. `_leave` deletes it,
  so a withdrawn member does not stay listed there until that table retires (BA-7204).
