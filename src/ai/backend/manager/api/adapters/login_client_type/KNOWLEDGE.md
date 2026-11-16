---
name: login-client-type-adapter-scenarios
type: reference
description: "what the login client type adapter guarantees: the reads open to every authenticated user, the superadmin role on create, the entity gate nobody but a superadmin passes on update and purge, single and partial bulk, the page size of fifty"
scope: src/ai/backend/manager/api/adapters/login_client_type
keywords: [login client type, scenario, adapter, superadmin, public read, page size]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# login_client_type adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A `login_client_type` entity belongs to both global and public. Create checks whether the calling user is superadmin, and a call that updates or purges an entity by id checks the permission granted on that `login_client_type` row, which comes from global only. Create, update and purge all succeed only for superadmin, but the rejection reason differs. Get and search check READ in public. Every account automatically receives the public membership role, so every signed-in user can read.

## Create

A request whose name is empty or exceeds the length limit is not a scenario. The request type already blocks it.

## Get

Get checks READ in public. The scenario where a user with only the public get permission succeeds proves it, and the matching rejection scenario is the one rejected for an insufficient role in the create section. A non-existent id and an unreachable id are rejected for the same reason.

An unauthenticated call is not a scenario. A scenario always calls as a user prepared beforehand.

## Search

What the name filter narrows and the paging method (the default size of 50, and whether a request that specifies only `first` is read by cursor, BA-7927, which tracks the cursor pagination decision) are not scenarios. Moving a filter into a condition and splitting a page belong to the unit tests.

## Update

Update takes the target id as a separate argument outside the request body. The adapter keeps this structure so that a scenario does not write the id in both the argument and the body.

Superadmin and other users are rejected for different reasons for a non-existent id. The permission check runs first and a non-existent row has no granted permission either, so only superadmin, who passes that check, is rejected for a missing target. The same applies to purge.

A duplicate name is rejected with a different error on create and on update. Create rejects it with the error dedicated to this entity, and update propagates the constraint violation error of the repository as is. Before writing the scenario, decide whether to unify them.

## Purge

This adapter has no delete that keeps the row.

## Bulk update

## Bulk purge

A bulk operation does not reject the whole call. Processed items go into the processed list, and the failure list contains the id and the reason.
