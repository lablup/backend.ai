---
name: idle-checker-service-shapes
type: decision-table
description: idle_checker knowledge - why the definition catalog and the session exclude/include edits share one package, why two groups are wired, why create and update keep a service, why the purge is bulk while the API names one
scope: src/ai/backend/manager/services/idle_checker
keywords: [CreateIdleCheckerAction, UpdateIdleCheckerAction, BulkPurgeIdleCheckersAction, AdminSearchIdleCheckersAction, ExcludeSessionIdleChecksAction, IdleCheckerCreator, IdleCheckerUpdater, global_scope, global_partial_bulk_purge_ops, IdleCheckerEntityType]
sources:
  - src/ai/backend/manager/services/idle_checker
  - src/ai/backend/manager/api/adapters/idle_checker
generated:
  by: claude-code/opus-5
  at: 2026-09-07
status: draft
---

# Idle checker service — Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`.

An idle checker definition is a system-wide catalog entry; excluding and including a
session is the edit that turns that definition off for one session. They share a
package because the latter is meaningless without the former, and they are answered
for by different entities.

## The processor fields

`backend.ai mgr ops list --concern session` prints the wired list. Its output answers
the entity type, shape, operation, gate and backing.

## Two groups, because two entities answer

- The four catalog operations come from the `idle_checker` group; exclude and include
  come from the `session` group.
- Those two are answered for by the session, not by the checker — the permission to
  turn a session's idle check off is a permission on that session.
- So one package takes two `ProcessorGroup`s. Folded into one, one side's audit rows
  would name the wrong entity.

## A checker definition is global

- An `idle_checkers` row belongs to no scope. What attaches to a domain or a project
  is the binding (`idle_checker_assignment`), not the definition.
- Nothing is granted per definition, so there is no per-entity permission to express
  and nothing to share.
- All four REST and GQL entry points run a hand-written superadmin check, so the
  global gate matches the surface.

## Create and update keep a service

- Both read another entity before writing: they fetch the prometheus query preset the
  utilization spec names and reject filter and group labels that preset does not
  declare as allowed.
- A check that reads another repository is past what an action validator absorbs, and
  a spec cannot issue SQL — that is the criterion for keeping a service method.
- Past the check the service hands the action's spec to ops unchanged. It does nothing
  else.

## The purge is bulk while the API names one

- The catalog's delete is wired through `global_partial_bulk_purge_ops`, which answers
  per entity.
- Today's REST and GQL surface names one checker, so the adapter calls it with a
  single-id list and raises the one failure it can report. The API names one checker
  and either removes it or fails.
- The bindings and session rows referencing a removed definition follow it through
  `ON DELETE CASCADE`. No precondition blocks the delete.

## A missing row is not a domain error

- An update or purge naming no row raises `EntityNotFoundError`, not
  `IdleCheckerNotFound`.
- ops knows no domain, so the entity type travels in the message. Both are 404 and
  only the `error_type` string differs.
