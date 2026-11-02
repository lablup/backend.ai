---
name: fair-share-adapter-scenarios
type: reference
description: "what the fair share adapter guarantees: the global authorization check on weight writes and the single transaction of bulk upsert"
scope: src/ai/backend/manager/api/adapters/fair_share
keywords: [fair share, weight, upsert, atomic bulk, scenario, adapter, rbac]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-16
status: draft
---
# fair_share adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A fair share record takes a resource group and one of domain, project and user together as its key. The call that writes a weight is a permission check that refers to that resource group, but the target type it checks is global, not resource group. A role cannot grant a global type permission, so a user who received update permission through a role granted in that resource group cannot write a weight either. Only superadmin can write a weight today.

## Setting one weight

## Setting several weights at once

Setting several is one transaction. It does not respond per item, and a failure rejects the whole call.
