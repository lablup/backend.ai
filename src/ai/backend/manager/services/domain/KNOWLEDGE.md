---
name: domain-service-composition
type: decision-table
description: why a domain's operations take the shapes they do, why dotfiles are a column of the domain row, which operations keep a service method and why
scope: src/ai/backend/manager/services/domain
keywords:
  - DomainProcessors
  - DomainCreator
  - DomainUpdater
  - DomainDotfilesUpdater
  - dotfile
  - create_domain_node
  - RoleManagedEntityCreator
sources:
  - src/ai/backend/manager/services/domain/processors.py
  - src/ai/backend/manager/models/domain
generated:
  by: claude-code/opus-5
  at: 2026-08-19
status: draft
---

# Domain service

A domain is the top scope everything else is created under. No parent entity sits
above it, so creation is global-shaped, and an operation naming an existing domain is
single-entity.

## The processor composition

`backend.ai mgr ops list --concern organization --entity domain` prints the wired list.
Its output answers the entity type, shape, operation, gate and backing.
