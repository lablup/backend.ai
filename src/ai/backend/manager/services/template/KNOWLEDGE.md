---
name: template-service-shapes
type: design-rationale
description: session template and cluster template service knowledge - the action shape of each processor, why a template list is a scope read or a global read that the REST handler chooses between, which scopes the scope read covers, how both reads build the entry, what the project filter and is_owner mean
scope: src/ai/backend/manager/services/template
keywords: [TemplateProcessors, SessionTemplateSearcher, SessionTemplateWithOwnerEmailAndProjectName, TemplateService, ListTaskTemplatesAction, GlobalListTaskTemplatesAction, ListClusterTemplatesAction, GlobalListClusterTemplatesAction, list_templates_in_scopes, joined_project_ids, SessionTemplateTarget]
sources:
  - src/ai/backend/manager/services/template
  - src/ai/backend/manager/repositories/template
  - src/ai/backend/manager/models/session_template
  - src/ai/backend/manager/api/rest/session_template/handler.py
  - src/ai/backend/manager/api/rest/cluster_template/handler.py
generated:
  by: claude-code/opus-5.5
  at: 2026-11-09
status: draft
---

# Template service: Knowledge

> Rules: `../AGENTS.md`. Action shapes and gates: `../../actions/AGENTS.md`.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

This service serves the REST v1 session template and cluster template routes. Both kinds
are rows of `session_templates`, distinguished by `type`, and each is created in its owner's
user scope and in its project's scope (`SessionTemplateCreator.created_in`).

## Each processor has one shape

| Processor field | Shape | Authorized against |
|---|---|---|
| `create_task`, `create_cluster` | scope | the requesting project |
| `list_task`, `list_cluster` | scope | the requester's user scope |
| `global_list_task`, `global_list_cluster` | global | the global gate, which a superadmin passes |
| `get_*`, `update_*`, `delete_*` | single_entity | the template |

- A create names no template yet, so it is authorized against the project it writes into.
- A list is split into two actions because the two reads are authorized differently: a
  scope read against one user, a read of every template against the global gate.

## The REST handler chooses the list action

- `all=true` from a superadmin runs the global action, which reads every template through
  `list_templates_in_global`.
- `all=true` from a caller who is not a superadmin is rejected with `InsufficientPrivilege`
  rather than served the scope read, so the caller never takes a partial list for the whole.
- Every request without `all` runs the scope action.
- The handler checks the role before it chooses, and the global gate checks it again when
  the action runs.

## The scope read covers the user and the projects they joined

- The service builds one `UserSessionTemplateTarget` for the requester and one
  `ProjectSessionTemplateTarget` per project in `joined_project_ids`;
  `list_templates_in_scopes` ORs their conditions.
- The action is authorized against the user scope alone. The projects come from the
  user's own roster, so the gate does not check them one by one.
- No branch serves a domain admin: an admin gets the same list as a project member.

## Both reads run a Searcher and fill the names in the same read

- `list_templates_in_scopes` runs `SessionTemplateSearcher` through `search_with_scopes`,
  and `list_templates_in_global` through `search_in_global`.
- A `Searcher` selects one table, so the owner's email and the project name come from
  `BulkUserQuerier` and `BulkProjectQuerier` in the same `read_ops()`, as
  `SessionTemplateWithOwnerEmailAndProjectName`.

## The project filter only narrows, and is_owner is computed by the REST handler

- `group_id` keeps the rows of one project among the scopes' rows. A project outside the
  scopes still returns nothing.
- `is_owner` is true when a row's `user_uuid` is the requester. The handler compares them,
  so neither read takes the requester.
