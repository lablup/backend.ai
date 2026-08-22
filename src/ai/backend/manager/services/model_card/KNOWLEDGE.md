---
name: model-card-service-shapes
type: decision-table
description: which model card operations keep a service method and what each one checks
scope: src/ai/backend/manager/services/model_card
keywords: [ModelCardCreator, ModelCardResourceRequirementCreator, bulk_scoped_search_ops, entity_create_with_fields_ops, ScanProjectModelCardsAction, AvailablePresetsAction]
sources:
  - src/ai/backend/manager/services/model_card
  - src/ai/backend/manager/models/model_card
  - src/ai/backend/manager/repositories/model_card
generated:
  by: claude-code/opus-5
  at: 2026-08-21
status: draft
---

# Model card service — Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`.

A model card names, inside a project, a model held in a VFolder. It states the minimum
resources the model needs to run alongside it, so this package covers two tables.

## The processor composition

`backend.ai mgr ops list --concern deployment --entity model_card` prints the wired
list. Its output answers the entity type, shape, operation, gate and backing.
