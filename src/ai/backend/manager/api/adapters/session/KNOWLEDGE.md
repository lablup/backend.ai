---
name: session-adapter-scenarios
type: reference
description: what the session adapter guarantees: project scope permissions, and how bulk terminate and terminate report their results
scope: src/ai/backend/manager/api/adapters/session
keywords: [session, scenario, adapter, rbac, enqueue]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# session adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A session refers to the project it belongs to by name. The session permission therefore is on the project scope, and granting that role is the same as adding the user to the project member list.

## Get

The full get without a filter is blocked by the superadmin role. The get blocked by a scope permission is the search that takes a scope.

## Bulk terminate

Bulk terminate does not reject the whole call. Processed sessions enter the processed list with the finished status (cancelled, terminating, force-terminated, skipped), and failures are recorded in the failure list with the id and the reason. A session already finished or missing enters the processed list as skipped.

## Terminate (old name)

The old terminate calls the same processing as bulk terminate and splits the response into lists by finished status. When even one session is rejected, the whole call is rejected.
