---
name: idle-checker-adapter-scenarios
type: reference
description: what the idle checker adapter guarantees
scope: src/ai/backend/manager/api/adapters/idle_checker
keywords: [idle checker, scenario, adapter, superadmin, partial bulk, purge]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# idle_checker adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

An idle checker lives in the global catalog and belongs to no scope. Writes require the global superadmin role.

## Bulk purge

The bulk purge does not reject the whole call. Deleted checkers go into the processed list, and failures carry the id and the reason in the failure list.
