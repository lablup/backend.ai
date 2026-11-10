---
name: idle-checker-assignment-adapter-scenarios
type: reference
description: what the idle checker assignment adapter guarantees
scope: src/ai/backend/manager/api/adapters/idle_checker_assignment
keywords: [idle checker assignment, scenario, adapter, rbac, partial bulk, relation]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# idle_checker_assignment adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

An assignment is a relation that links a scope and an idle checker. A write checks the permission of both entities. A bulk operation runs the single write separately per entry.

## Updating several

## Purging several

For a user without permission, the step that finds the assignment id gives the same response as a missing id, so the call does not reveal whether an assignment exists. For superadmin, a missing id comes as a missing target.

A bulk operation does not reject the whole call. Processed assignments go into the processed list, and entries that could not be processed go into the failure list with the id and the reason.

The database creates the assignment id. The scenario obtains an id by searching assignments as one superadmin, then calls as the caller.
