---
name: system-session-environ-adapter-scenarios
type: reference
description: what the system session environ adapter guarantees; rows are created in a public, domain or project scope, the global search is protected by the superadmin role check and lets the monitor role read, the value source list any logged-in user reads, the update and delete rules, and the per-row permission checks when reading several rows by id with different responses for unknown ids
scope: src/ai/backend/manager/api/adapters/system_session_environ
keywords: [system session environ, scenario, adapter, superadmin, monitor, global_search, scoped_search, public_list_value_sources, create, update, delete, restore, purge, bulk_get_ids, partial bulk]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-23
updated:
  by: claude-code/opus-5.5
  at: 2026-10-30
status: draft
---
# System session environ adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A system session environ row is created in one of the public, domain, or project scopes. This adapter provides the call that searches every row, the call that searches within a specified scope, the call that reads the value source list, the call that creates a row, the call that changes the key of a row, the calls that delete and restore a row, the call that purges a row, and the call that reads several rows by id.

The search is protected by the global superadmin role check. It does not select the rows actually injected into a session and returns every row that matches the condition, regardless of scope and deletion.

Reading several rows by id checks permission per row. Every user can read the rows of the public scope, and the administrators of a domain and of a project can read the rows of that domain and project. A member who is not an administrator cannot read the rows of the domain and project.

## Unscoped search

The monitor role passes the global superadmin role check for reads only. The REST handler and GQL resolver pass only superadmin before calling the adapter, so the search of the monitor role passes only when the adapter is called directly.

## Search within a scope

## Value source list

A value source is a list the manager provides, not a row, so the call checks only whether the caller is signed in and returns the list. The value source of a row is returned as a name in this list, and a search condition uses this name too.

## Create

## Update

The scope and the value source cannot be changed. Within one scope, keys cannot collide, including deleted rows.

## Delete

A deleted row is not injected into sessions that start afterwards.

## Restore

## Purge

## Reading several rows by id

Reading several rows does not reject the whole call and responds per entry.

A missing id receives a different response for superadmin and for other users. The permission check reads the permission graph per id, and the permission of an id absent from the graph cannot be checked, so a user who is not superadmin receives an insufficient permission response. Only superadmin, who passes that check, receives an empty value.
