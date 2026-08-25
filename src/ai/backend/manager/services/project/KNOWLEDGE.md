---
name: project-service-composition
type: decision-table
description: why a project's operations take the shapes they do, why dotfiles are a column of the project row, why membership takes a path of its own
scope: src/ai/backend/manager/services/project
keywords:
  - GroupProcessors
  - GroupCreator
  - GroupUpdater
  - GroupDotfilesUpdater
  - assign_users_to_project
  - RoleManagedEntityCreator
sources:
  - src/ai/backend/manager/services/project/processors.py
  - src/ai/backend/manager/models/project
generated:
  by: claude-code/opus-5
  at: 2026-08-22
status: draft
---

# Project service

A project sits under a domain, so creation is scope-shaped with the domain as the
scope, and an operation naming an existing project is single-entity.

## The processor composition

`backend.ai mgr ops list --concern organization --entity project` prints the wired
list. Its output answers the entity type, shape, operation, gate and backing.
