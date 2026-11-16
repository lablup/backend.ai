---
name: session-group-adapter-scenarios
type: reference
description: what the session group adapter guarantees: where session groups live, how the permission graph and the global superadmin role gate each operation, and how deployment-owned groups are answered
scope: src/ai/backend/manager/api/adapters/session_group
keywords: [session_group, scenario, adapter, rbac, bulk_get_ids, scoped_search, create, update, purge, deployment]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-15
updated:
  by: claude-code/opus-5.5
  at: 2026-10-22
status: draft
---
# session_group adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A session group is created under a project and a session group owner. The permission graph therefore checks the calls that read and update one session group and the call that creates a session group in a project, and the global superadmin role checks the unscoped search.

There are two kinds of session group: one the user created, and one created together when a deployment creates a replica group and referenced by that replica group. The second is managed with the deployment. The reads exposed to the user (get one, read several, scope search) respond that a session group referenced by the replica group of a deployment does not exist even with permission, and the placement policy change and purge reject it as in use. Only the unscoped search shows both together.

Framework contract tests check the common contract (target existence, bulk composition, page). This document records only the representative success and representative failure of each operation and the differences the session group rules make.

## Get one

In the last row the user also holds the read permission on that session group. The rejection reason must therefore be a missing target, not a permission.

## Read several

Reading several does not reject the whole call and responds per entry. A session group referenced by the replica group of a deployment responds with the same empty value as a missing session group.

In the row of a missing id, superadmin performs the call. The permission check reads the permission graph per id, and the permission of an id absent from the graph cannot be checked, so a regular user receives an insufficient permission response. Only a user who passes the check sees the response of the read (the empty value).

## Unscoped search

A role, not the permission graph, checks the call of the unscoped search. The requester of the superadmin row is therefore superadmin. The scenario filters by project so the rows do not mix with the session groups another scenario seeded.

## Scope search

When even one scope lacks permission, the call rejects the whole search instead of showing the rest.

Several scopes are combined with OR. In the last row, a session group of the first project the user created is reachable only through the user scope, and a session group another user created only through the project scope. Both must appear for the combination to hold.

## Create

The response does not show that the session group is placed under the project and the creator. After the run the test counts the number of session groups, the number of session group nodes, and the number of projects and users holding those nodes in the database. A group must be placed under a project to appear in the scope search of that project.

The read permission row shows that create does not pass with the read permission. The other project row shows that the create permission must be held on the project where the session group is created.

## Purge

The response does not show that the session group and its graph node are gone and its member sessions remain. After the run the test counts the number of session groups, the number of session group nodes, and the number of sessions with and without a session group in the database.

In the row of a session group referenced by the replica group of a deployment, the user also holds the purge permission on that session group. The rejection reason must therefore be in use, not permission.

The read permission row shows that purge does not pass with the read permission. It is paired with the row without any permission.

## Changing the placement policy

- The pair of the permission row differs only in the permission received in the same scope by the same user. The read permission does not allow changing the placement policy.
- A session group the replica group of a deployment holds is created in the scope of the creating user too. Only a user with the update permission reaches this rejection, so the rejection reason must be that the deployment uses the session group, not permission.
- Only the placement direction and the strictness can change. Calling with both omitted is rejected by the request format.
- The changed policy applies to members placed afterwards. The scheduler reads the session group policy on every placement, and it does not move members already placed.
