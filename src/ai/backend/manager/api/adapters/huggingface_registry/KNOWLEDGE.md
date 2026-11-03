---
name: huggingface-registry-adapter-scenarios
type: reference
description: what the huggingface registry adapter guarantees for update, purge and their partial bulk forms
scope: src/ai/backend/manager/api/adapters/huggingface_registry
keywords: [huggingface registry, artifact registry, scenario, adapter, rbac, partial bulk, purge]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# HuggingFace registry adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A registry is created in the global scope. One registry is two rows, one carrying the connection settings and one the name, written together and deleted together in one operation. The permission graph checks the calls that update and delete one registry. A user with a granted permission receives the artifact registry permission through a role granted in the global scope.

## Update

## purge

Both the single purge and the bulk purge check the purge permission.

## Bulk update

## Bulk purge

A bulk operation does not reject the whole call. Processed registries go into the processed list, and failures carry the id and the reason in the failure list. Each registry is written separately, so the rest is still applied even when one fails. The processed list of the bulk purge carries only the ids of deleted registries.

The requester of the missing id row is superadmin because superadmin passes every check and the missing target is exposed as is. To a user with a granted permission, a missing id is a target absent from the permission graph.
