---
name: resource-policy-adapter-scenarios
type: reference
description: what the resource policy adapter guarantees, one chapter per policy: the project, keypair and user policies
scope: src/ai/backend/manager/api/adapters/resource_policy
keywords: [resource policy, keypair resource policy, user resource policy, project resource policy, scenario, adapter, superadmin, lookup, scope]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# resource_policy adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

One adapter handles three kinds of policy: project policy, keypair policy and user resource policy. Each kind has one section, and the same call is written separately per section. The paragraphs below are common to the project policy, keypair policy and user resource policy sections.

A policy is created outside every scope, so no permission can be granted on an individual policy. Create and the unscoped search check whether the calling user is superadmin, and the get, update and delete by name pass a permission check, but no role in the permission graph has a permission on a policy, so only superadmin passes in the end.

Get specifies the policy by name. Single update and delete take an id, and the old REST path and GQL mutation that take a name call find-an-id-by-name first and lead to the same call. The update and delete tables below call through that path. The step that finds a policy by name runs first, and a user without permission is rejected for the same reason ("not found") regardless of whether the name exists. When superadmin specifies a non-existent name, the call is rejected for a missing target, not for insufficient permission. A user without permission is rejected at this step before update or delete runs, so update and delete are rejected for the same reason as get.

A duplicate name and the deletion of a policy still in use are blocked by a database constraint, not by the spec. The spec does not distinguish that violation as a separate error and the repository propagates the constraint violation as it is, so the request is rejected with the constraint violation error of the repository, not with a policy-specific error. A request whose name is only whitespace is not a scenario in any section. The request type already blocks it, so the adapter does not guarantee it.

## Project policy

It is the simplest of the project policy, keypair policy and user resource policy. It has no entry that may be omitted on create or emptied on update, and no call that gets one's own policy. One user belongs to several projects, so which project's policy is the user's own is not decided yet.

### Create

The `max_quota_scope_size` value is accepted in a human-readable notation ("1g") and returned in both the exact byte count and the human-readable notation.

### Get by name

### Search

A monitor role passes the search and does not pass create. The superadmin check allows a monitor role for reads only.

### Update

A request that empties an entry that cannot be emptied is treated as unspecified, and the value stays. One can easily expect a rejection, so it is a scenario.

### Delete

This adapter has no delete that keeps the row. Deleting makes the row disappear at once and there is no call that brings it back.

### Bulk update

### Bulk delete

For a project that uses the policy, the scenario uses the personal project created together with a user. A personal project references the project policy with the name `default`, so a scenario that prepares a user first must create that policy first.

## Keypair policy

It is the most complex of the project policy, keypair policy and user resource policy. The only entries that may be omitted on create are the `max_pending_session_count`, `max_priority` and `max_pending_session_resource_slots` values, and the only entries that may be emptied on update are the same three. The `max_priority` value has a range constraint on the priority a session may have. The own policy get finds the policy through the keypair of the caller.

### Create

An out-of-range `max_priority` value is blocked by a database constraint like a duplicate name and is rejected with the constraint violation error of the repository.

The `is_default` column cannot be set by any call. Create stores it as false and the response does not include it. The rule that there must be one default policy cannot be checked through this adapter.

### Get by name

### Search

### Update

A request that empties a value is handled differently per entry. An entry that can be emptied is emptied, and an entry that cannot is treated as absent from the request and stays. "empty an entry that can be emptied" and "try to empty an entry that cannot be emptied" stand side by side.

### Delete

### Bulk update

### Bulk delete

### Getting one's own policy

The request has no body and the policy is found from caller information only. The call finds the policy assigned to the default access key among the caller's active keypairs, or, without one, to the keypair created first.

The own policy get checks permission even after narrowing the scope to one's own policy. A user without permission is rejected even though the only accessible policy is their own.

The keypair created together with a user is the default access key, and whether that keypair is active follows whether the user is active. The situation where the default access key is inactive and the situation with no active keypair are built with an inactive user.

## User resource policy

The only entry that may be omitted on create is the `max_concurrent_logins` value, and the only entry that may be emptied on update is the same. The own policy get reads the policy the user row references as it is.

### Create

The `max_quota_scope_size` value is accepted in a human-readable notation ("1g") and returned in both the exact byte count and the human-readable notation.

### Get by name

### Search

### Update

### Delete

### Bulk update

### Bulk delete

### Getting one's own policy

The request has no body and the policy is found from caller information only. A user row cannot store an empty policy name, so a policy always exists when the user exists. There is therefore no scenario rejected for a missing target.
