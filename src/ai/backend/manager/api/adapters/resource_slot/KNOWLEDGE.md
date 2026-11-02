---
name: resource-slot-adapter-scenarios
type: reference
description: what the resource slot adapter guarantees: the name-keyed slot type catalog with the superadmin role on create and update against the entity gate on purge and the rows that reject a purge while referenced, the agent resource reads gated by a role in the agent's resource group, the kernel allocation reads gated by a role over the kernel's session with a lookup that treats a missing kernel and a missing permission alike, and the domain and project overviews gated by session read in that scope
scope: src/ai/backend/manager/api/adapters/resource_slot
keywords: [resource slot type, agent resource, kernel allocation, resource overview, scenario, adapter, superadmin, lookup, purge, in use, public read]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# resource_slot adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

This adapter handles the `resource_slot_type` catalog, the get of `agent_resource` rows (the resources an agent reports), the get of `resource_allocation` rows (the resources a kernel is allocated), and the resource overview of a domain and a project.

A `resource_slot_type` row is created in both global and public. Create and update check whether the calling user is superadmin. Only delete checks the `HARD_DELETE` permission on that `resource_slot_type` row, and that permission comes from global only, so only superadmin passes. Get and search check READ in public. Every account automatically receives the public membership role, so every signed-in user can read.

The get and update of a `resource_slot_type` take a name. They find the id by name first and then run the operation. Delete and bulk delete take an id. The old delete calls that take a name (GQL `admin_purge_resource_slot_type`, REST `DELETE /slot-types/{slot_name}`) call the step that finds an id by name first and lead to the same delete. A write checks whether the calling user may write before finding the target. A user who is not superadmin or has no permission is rejected for the same reason whether the target exists or not.

The unscoped search of `agent_resource` and `resource_allocation` checks whether the caller is superadmin, and since a search is a read operation, a monitor passes too. The get and search that name one agent check the permission on that agent. An agent is created inside its resource group, so a role in the resource group scope grants that permission. The `resource_allocation` get of one kernel checks the permission on the session the kernel belongs to. A session is created inside its project, so a role in the project scope or in its domain scope grants that permission. An overview checks the session get permission in the domain or project scope.

With the permission check setting off, the permission checks on an entity and a scope all pass, but the superadmin check does not read that setting.

## Create

The adapter rejects a name already in use instead of overwriting it because the `agent_resources`, `resource_allocations`, `model_card_resource_requirements`, `preset_resource_slots` and `deployment_revision_resource_slots` tables reference this row. An overwrite would change the meaning of every allocation recorded under that name.

The id of the node is the slot name, not a uuid. Copying the check that ignores the id from another entity would lose the name check, so this entity checks the id and ignores the uuid.

## Get

Get checks READ in public. The step that finds an id by name is followed by a permission check on the found target, so an unknown name and an unreachable name are rejected for the same reason. The scenario where a user with only the public get permission succeeds proves it and is contrasted with the scenario rejected for an insufficient role in the create section.

An unauthenticated call is not a scenario. A scenario always calls as a user prepared beforehand.

## Search

Every field the request type accepts is read: the name, `slot_type` and `display_name` filters, `limit` and `offset`, and the `first`, `after`, `last` and `before` fields. No field is accepted and ignored.

## Update

The name and the `slot_type` value cannot be changed. The request type does not accept them, so they are not scenarios.

The core of this section is the scenario where a user who is not superadmin updates an unknown name. A user who is not superadmin is rejected for the same reason as when the name exists. If the step that finds an id by name ran before the superadmin check, the rejection reason for a missing target would be exposed; this row checks that the steps run in the opposite order. It stands beside the same scenario in the delete section.

## Finding an id by name

The call checks READ in public on the found target. Every account receives that permission, so even a user without any permission finds it.

## Delete

There is one scenario per referencing table. The `agent_resources`, `resource_allocations`, `model_card_resource_requirements`, `preset_resource_slots` and `deployment_revision_resource_slots` checks run separately, and if one is left out that case fails with a constraint violation, not a rejection. Merged into one scenario, it passes even when only one of the checks remains.

Update and delete reject the same `resource_slot_type` row for different reasons. Update is an insufficient role and delete an insufficient permission.

This adapter has no delete that keeps the row.

## Deleting several

Bulk delete does not reject the whole call. Processed `resource_slot_type` rows go into the processed list, and failures are recorded in the failure list with the id and the reason. A `resource_slot_type` still referenced also enters the failure list alone.

## `agent_resource` get

The step that finds the agent by the `agent_id` value checks authentication only. The proof is that a user without any permission calling with a missing `agent_id` value is rejected for a missing target. The permission is checked on the found agent before the slots are found.

## `agent_resource` search

Without a sort, the rows come back in slot name order. This search does not look at the slot rank.

## `agent_resource` search of a specified agent

The adapter checks the permission per specified agent, and when one is unreadable it rejects the whole call instead of returning only the readable side.

## `resource_allocation` get

The step that finds the session by the kernel id checks the permission on that session. A lack of permission and a missing kernel are rejected for the same reason, so the rejection reason alone does not reveal whether the kernel exists. Only superadmin, who passes every check, sees that the kernel is missing as it is.

## `resource_allocation` search

## Domain resource overview

The overview counts only kernels that occupy or are allocated resources, and does not count kernels that only requested and are waiting. The proof is that the overview of a domain with only waiting kernels is empty.

## Project resource overview

The session get permission in a domain scope reaches the projects inside it, and a permission in a project scope does not reach the domain. The domain scope scenario in this section and the project scope scenario in the domain overview section check it in each case.

A project is identified by id, not by name, so there is no id lookup step and the adapter does not check whether the project exists. A get with a non-existent id returns an empty overview, not a rejection.
