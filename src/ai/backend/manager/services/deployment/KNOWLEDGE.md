---
name: deployment-service-composition
type: decision-table
description: why the two deployment searches keep a service method instead of the generic search service
scope: src/ai/backend/manager/services/deployment
keywords:
  - DeploymentProcessors
  - GlobalSearchDeploymentsAction
  - ScopedSearchDeploymentsAction
  - DeploymentSearcher
  - DeploymentPolicyData
sources:
  - src/ai/backend/manager/services/deployment/processors.py
  - src/ai/backend/manager/repositories/deployment/db_source/db_source.py
  - src/ai/backend/manager/models/endpoint/searchers.py
generated:
  by: claude-code/opus-5
  at: 2026-11-16
status: draft
---

# Deployment service

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## The processor composition

`backend.ai mgr ops list --concern deployment --entity deployment` prints the wired list.
Its output gives the entity type, shape, operation, gate and backing.

## The two deployment searches keep a service method

- `global_search` and `scoped_search` keep the generic actions, so the gates and the
  used-by check are the generic ones.
- Each result item carries the deployment's policy, which lives on its own row.
  `DeploymentSearcher` reads the deployment row alone, so the generic search service
  cannot fill it.
- `DeploymentDBSource` reads the page and the policies of its deployments in one read
  transaction.
