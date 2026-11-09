---
name: model-card-adapter-scenarios
type: reference
description: what the model card adapter guarantees; update and purge authorization, and the partial bulk result shape
scope: src/ai/backend/manager/api/adapters/model_card
keywords: [model card, scenario, adapter, rbac, purge, partial_bulk]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# model card adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## Get

## Update

A card is attached to a vfolder placed in a project. The user who created the card and the caller differ. The permission comes from the project the card is placed in. Update reads the updated card together with the minimum resource requirements and responds with it, so it needs the read permission too.

## purge

Purge deletes the card row. With the option, it moves the card's vfolder into the trash.

## Bulk update

## Bulk purge

A bulk operation does not reject the whole call. Processed cards go into the processed list, and failures carry the id and the reason in the failure list. The minimum resource requirements of a purged card are deleted with the card and are not in the processed list.
