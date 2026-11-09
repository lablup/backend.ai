---
name: audit-log-adapter-scenarios
type: reference
description: what the audit log adapter guarantees: the superadmin role on the whole-table search that a monitor passes, the per-entity read permission on the scoped search that refuses the whole page when one named entity is unreadable, the any-owner read on the by-id read and on the scope search of one record (the entity a record is about, each scope it recorded, the user who triggered it), the two axes a scope item names
scope: src/ai/backend/manager/api/adapters/audit_log
keywords: [audit log, scenario, adapter, superadmin, monitor, scoped search, triggered by, entity scope, owner candidates, search scopes]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# audit_log adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

An `audit_log` entity has no fixed owner. Each executed operation records one row automatically for the entity it handled, so the owner differs per record and a record of a global operation has no owner. This adapter therefore has no write: only the unscoped search, the get by several ids, the scoped search and the scope search of one record. A scenario cannot create the records it assumes through the adapter, so they are prepared through the write path that records them.

Permission is checked in three ways. The unscoped search checks whether the calling user is superadmin, and since it is a read, a user with the monitor role passes too. The scoped search checks the read permission granted on each named entity and rejects the whole request when even one is unreadable. The get by several ids and the scope search of one record check, per record, whether any of its owners is readable. The owners of a record are the entity the record is about, the scope entities recorded in it, and the user who ran it. The rejection reason differs per way, so the paired scenarios are written separately.

A scope can be named in two ways: as the target entity of the record, or as the `triggered_by` user. Naming an entity checks the permission granted on that entity; naming a user checks the permission granted on that user.

## Unscoped search

The scenario "a monitor role user searches" checks that the unscoped search passes a monitor role user for reads. It is paired with "a monitor role user gets without permission" and "a monitor role user searches by scope without permission", with the opposite result.

The `client_ip` value in the response is the value that passed the masking policy when recorded, as it is. The read does not mask it again, so the masking policy document covers what value the policy keeps.

## Getting by several ids

The adapter checks, per id, whether any owner of that record is readable, and responds per entry. An unreadable record is rejected in that entry only and the rest are returned. Unlike the scoped search, it has partial success.

A record is readable through the scope it recorded or the user who ran it even when its target entity is unreadable. This is the same condition under which the record appears in the scoped search.

A missing id is an empty entry for every caller. No entity is referenced, so there is no target on which to check permission.

A monitor role user does not pass here. Unlike the unscoped search, this read checks the permission graph.

## Scoped search

There is no partial success. Every named entity is authorized before the search, so when even one entity is unreadable the adapter rejects the whole request instead of returning the rest. This differs from the get by several ids, which responds per entry, so "the request is rejected entirely when even one unreadable entity is mixed in" is written separately.

Naming an entity returns both the records about that entity and the records of operations run with that entity as their scope. Naming a project therefore also returns the records of operations run inside that project, and "records of operations run inside the named entity are also returned" checks it.

There is no separate call that reads only one's own records. A record the user ran is read with the read permission granted on the caller's own user entity, so without that permission the user cannot see even their own records.

The only check a monitor role passes is the superadmin check. The scoped search checks the permission graph, so a monitor role user also needs the permission.

The adapter does not check separately whether the named entity exists. The permission check runs first, and no one has a permission on a missing entity. This is not a rejection for a missing target. Superadmin passes that check, so naming a missing entity is not rejected and the search runs and returns an empty page.

A request that names nothing is not a scenario. The request type already rejects it, so the adapter does not guarantee it.

## The scope search of one record

When a record is readable, all its scopes are read. Even when the record was accessed through one scope, the other scopes recorded in it are returned too. Scope rows have no permission check of their own.

Permission is checked on the same basis as the get by several ids. Only one record is named, so there is no partial success, and the request is rejected when none of the owners is readable.

A monitor role user does not pass here. Unlike the unscoped search, this search checks the permission graph.
