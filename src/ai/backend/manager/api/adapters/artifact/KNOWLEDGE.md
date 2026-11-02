---
name: artifact-adapter-scenarios
type: reference
description: what the artifact adapter guarantees for update, soft delete and restore, and for the bulk and legacy id-list calls; artifacts in no scope, the permission graph on single calls, the global role on the id-list calls, no purge
scope: src/ai/backend/manager/api/adapters/artifact
keywords: [artifact, scenario, adapter, partial_bulk, soft delete, restore]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# artifact adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

An artifact is created outside every scope. The permission graph protects the calls that update, delete and restore one artifact, and a global role protects the legacy calls that delete and restore several by an id list.

The framework contract tests verify the common contract (target existence, bulk composition). This document records only the representative success and the representative failure of each operation and the differences the artifact rules make.

## Update

## Delete and restore

There is no purge.

## Updating several

## Bulk delete and restore

A bulk operation does not reject the whole call. Processed artifacts go into the processed list, and the operation records failures in the failure list with the id and the reason.

## Bulk delete and restore by an id list

This is the call from before the bulk operations existed. The old REST path and GQL mutation call it.
