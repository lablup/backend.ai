---
name: role-preset-adapter-scenarios
type: reference
description: what the role preset adapter guarantees for its writes and its search; the permission graph guarding each write, the scope type filter comparing the stored scope type, bulk operations answering per id, and role permission presets added all-or-nothing and removed one by one
scope: src/ai/backend/manager/api/adapters/role_preset
keywords: [role preset, scenario, adapter, search, scope_type, scope_id, partial bulk, soft delete, restore, purge, permission entry]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
updated:
  by: claude-code/opus-5.5
  at: 2026-11-02
status: draft
---
# role_preset adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A role preset (preset below) is created in the global scope. The permission graph on the preset checks update, delete, restore, purge, and the addition and removal of permission entries. A user who received no role has no permission from the global scope and so is rejected. This document covers the write operations and search. Create and the reads other than search are not covered yet.

Framework contract tests check the common contract (target existence, bulk composition). This document records only the representative success and representative failure of each operation.

## Search

- Only global presets have a `scope_id`. Domain, project and user presets have no `scope_id`, whether the seed or the API creates them, so each creates its role in every scope of its type.
- The `scope_type` filter compares the stored `scope_type`. `global` selects every global preset, including the one the API shows with the `scope_type` `public`.

## Update

## Delete, restore and purge

## Bulk update

## Bulk delete, restore and purge

A bulk operation does not reject the whole call. Processed presets go into the processed list, and failures are recorded in the failure list with the id and the reason.

## Adding and removing role permission presets

Adding is all or nothing. Removing responds per entry.
