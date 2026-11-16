---
name: deployment-revision-preset-adapter-scenarios
type: reference
description: what the deployment revision preset adapter guarantees; the preset lives in the public scope, general users read it, and the bulk purge answers per preset
scope: src/ai/backend/manager/api/adapters/deployment_revision_preset
keywords: [deployment revision preset, scenario, adapter, partial bulk]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# deployment_revision_preset adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A preset lives in the public scope. A general user receives read permission only, and only a user who passes the permission check on the preset updates or purges it.

## Bulk update

## Bulk purge

A bulk operation does not reject the whole call. Processed presets go into the processed list, and failures carry the id and the reason in the failure list.
