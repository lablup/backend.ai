---
name: resource-group-adapter-scenarios
type: reference
description: what the resource group adapter guarantees: a group is a global row that is its own scope, so a role sitting on the group reaches it, the name lookup is public so an unknown name is not found for anyone, the allow lists link a group to domains and projects, the fair share spec and the default options are edited apart from the group
scope: src/ai/backend/manager/api/adapters/resource_group
keywords: [resource group, scenario, adapter, rbac, superadmin, allowed, fair share, default options, scheduler]
generated:
  by: claude-code/opus-5
  at: 2026-09-17
status: draft
---
# resource_group adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A resource group is created outside every scope, and it is itself the scope of agents and sessions. Create and the unscoped search check whether the calling user is superadmin (a monitor passes the search too). The get, update and purge that refer to one group check the permission granted on that group, and since the group is its own scope, a role granted on the group gives that permission. The permission pairs in this document are therefore not superadmin and other users but a user who received a role granted on the group and a user who did not.

The call that finds an id by name checks authentication only. An unknown name is therefore rejected for everyone because the target is missing, and the permission check comes only after the lookup.

A session accesses a resource group in three ways: through the domain, through the project and through the user's keypair. The allow list calls write and read the relations to the domain and the project among them.

## Create

The `domain_name` value of the request is not read. The group is created without being added to any domain, and adding it to a domain is done by the calls in the allow list section.

There is one default group. The scenario that creates a second default group fails in the current code and was excluded from the run (BA-7946, duplicate default group constraint violation). The create path does not distinguish the violation of the constraint that enforces it from a duplicate name, so it rejects a second default group as a duplicate name. The update path distinguishes them (see the update section). The scenario records, as its expected value, that the request is rejected for the same reason as on the update path. Include it in the run again when it is fixed.

## Get

An unknown name is rejected for the same reason for superadmin and for other users. The call that finds an id by name checks authentication only, and the permission check runs only for the found id. Every unknown name scenario in the sections below is the same.

The resource status is the sum of the `agent_resource` rows of schedulable agents in the `ALIVE` status. A group with no agent has no entry in any of the three values.

## Finding an id by name

The REST handler and GQL resolver of another entity call this first when resolving a resource group name to an id.

Today it returns the id even to a user without permission. The plan is to change it into a read that checks permission so that a user without permission cannot access the group by name either, and that change is decided in the resource group work together with the effect on the calls that follow.

## Search

A scope search needs the permission to read resource groups within each named scope. The response for a domain scope is only the groups added to that domain. Even superadmin does not see a group that is not added.

## Update

Update takes an id. The settings update calls find-an-id-by-name first and leads to the same update. The old REST path and GQL mutation that take a name are the same path. So both pass the same permission check, return the same node and change the same fields. The adapter does not read the `name`, `total_resource_slots`, `allowed_vfolder_hosts`, `integration_name` and `resource_policy` values of the update request type.

## Bulk update

## Purge

There is only a purge, no delete. Setting `is_active` to false serves in place of delete. Purge takes an id. The old REST path and GQL mutation that take a name call find-an-id-by-name first and lead to the same call.

## Bulk purge

A bulk operation does not reject the whole call. Processed groups go into the processed list, and failures are recorded in the failure list with the id and the reason.

## Allow lists

Eight calls write and read the same relation on the domain side, the project side and the group side.

A call from the domain side or the project side passes only for superadmin, because the step that turns the group name into an id passes the superadmin check. A call from the group side turns the name into an id with authentication only, and the step that writes the relation checks permission on both scopes. A user without any permission is rejected on either side, but for a different reason.

The remove calls handle an unknown name differently on the two sides. The domain-side call skips an unknown group name, while the group-side call rejects an unknown domain name. The call does not catch the error raised by the step that turns the domain name into an id.

The project allow list read operation reads from three scopes: the caller's domain, the specified project and the caller. It passes only with the permission to read resource groups in all three scopes, so this document records only that superadmin passes and a user without any permission is rejected.

## Fair share settings

The settings read finds the group by the unscoped search and therefore passes the superadmin check first. A read role granted on the group can read the group itself but not this setting. The update passes only the permission check on the specified group and therefore passes with the update role.

No scenario checks that the entries of `resource_weights` are limited to the resources in the capacity of that group. The service decides it, and the service unit tests check it. The node returned by the update does not carry this setting.

## Default options

The processor names are read from those registered in the deployment coordinator and the scheduling coordinator. The scenarios run with both coordinators replaced by a mock that responds only with registered processors.
