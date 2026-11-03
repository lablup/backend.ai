---
name: deployment-adapter-scenarios
type: reference
description: what the deployment adapter guarantees; its own calls, its revisions, and the partial bulk writes of its auto-scaling rules and deployment tokens
scope: src/ai/backend/manager/api/adapters/deployment
keywords: [deployment, scenario, adapter, rbac, project, revision, auto-scaling rule, deployment token, partial bulk]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# deployment adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A deployment is created in a project scope. The create permission applies to the project, and after creation it applies to the deployment itself. Only the global browse and the full revision refresh are protected by a global role.

The rows a deployment owns (revisions, replicas and routes, deployment tokens, the deployment policy, auto-scaling rules) are not written in this section. They have no scope of their own and are authorized by the owning deployment, so each field has its own section.

## Create

The scenario that disables enforcement has the opposite result to the domain one. The permission graph protects this call rather than a role, so the switch applies. It is the scenario paired with the same scenario in the domain document.

Create writes the deployment policy row together. There are three branches for choosing the strategy, one row each: a rolling setting given, a blue-green setting given, and only a strategy name given with neither setting.

The request cannot decide the revision retention count. Create sets the value.

A request whose name is only whitespace and a request with a negative replica count are not rows. The request type already blocks them, so the adapter does not guarantee them.

The default deployment strategy in the response is rolling whatever the request chose. The chosen strategy is carried on the deployment policy side.

## Read

A missing id is rejected differently for superadmin and for anyone else. The permission check runs first and a missing row has no granted permission either, so only superadmin, who passes that check, sees the missing target. Every missing id row in the sections below is the same.

The current revision read joins two reads. No one holds permission to read the deployment but not its revisions, so a row pins that the second call blocks nothing extra.

## Browse

There are three browse calls. A role protects the global browse. The read permission on that project protects the project browse, and the read permission on the caller's own scope protects the own browse. The own browse does not merely narrow the scope either. The browse has no separate permission. Browse and read look at the same bit.

## Update

A request whose name is only whitespace is not a row. The request type blocks it, as in create.

The request type accepts the preferred domain name and the deployment strategy, but the update path uses neither. They are dropped silently today. Before writing the row, settle whether to drop or to use them.

## Replacing the options

The options are how long the processor that runs the deployment stage waits and how many times it retries. Create copies the default values of the resource group, so they are never empty, and a later change on the resource group side does not move them. So this is the only call that changes the values of an existing deployment.

The replacement does not merge. It reads easily as a partial update, so a row states that what is not sent disappears.

The processor name is checked against the live registry. A scenario does not write the name as a literal but reads it from the registered entries.

The response is only the replaced options, not the whole deployment. The checked range differs from other calls.

## Activating a revision

Activation does not check that the revision belongs to that deployment. Settle what should happen when the id of another deployment's revision is sent, then write the row.

The full refresh is designed for partial success. A row pins that the rest run even when one fails.

## Matching the replica count

Matching does not finish within the request. The response only says it started, and whether the replicas actually start is checked elsewhere.

## Delete

A row with a user who holds only update permission pins that delete is a different call from update. Among the requests that delete an owned row, some use this call and some use the update call.

This adapter has no purge. Delete marks the deployment as deleting and the rest runs later. When a purge call appears it carries its own permission, so the row is added then.

## Revisions

A revision is a row the deployment owns. It has no scope of its own and opens under the permission of the owning deployment. Add requires create permission on the deployment, and read and browse require read permission. The current revision read, activation and the full refresh are in the sections above: they choose a revision but what they write is the current revision of the deployment.

One revision is built by stacking several layers: the defaults of the model mount path, the defaults of the inference runtime variant, the revision preset, the config file inside the model vfolder, and the request. A later layer overrides an earlier one. Every nested setting of the request may be omitted, and an earlier layer fills an omitted place.

### Add

The response is the added revision only. The following four are not rows because they do not appear in the response or cannot be seeded.

- Auto-activation changes the deploying revision of the deployment.
- Exceeding the retention count deletes the older revisions. The current revision and the deploying revision are not counted and are kept.
- Without naming a mount permission, the permission the caller holds on the model vfolder is attached. The mount setting in the response has no permission slot.
- For an inference runtime variant that reads vfolder files, the definition file inside the vfolder becomes a layer. The write spec of the variant does not accept that property, so it cannot be seeded.

The model definition is never empty because the mount path default always includes one model. Without a layer that fills the name, the validation blocks that model.

The mount permission is bounded by two layers. The model vfolder cannot exceed the permission the caller holds on that vfolder, and an attached vfolder cannot exceed the permission of that vfolder itself. Only the exceeding side of the first is a row. The second is added when the attached vfolder seed exists.

The model vfolder permission is read from the permission bits the caller holds on that vfolder. Read mounts as read-only, update as read and write, and purge as delete too. Without read, the call is blocked for a missing vfolder. Superadmin holds every bit on the vfolder without a granted permission. Except the row that looks at a user without vfolder read permission, every add row that passes the permission checks holds vfolder read permission.

Only the preset and the config file inside the vfolder fill the resource slots. The inference runtime variant gives the model definition only.

The retention count is the value create sets.

### Read

The call that reads a revision finds the owning deployment first and checks the permission of that deployment. That lookup gives the same rejection for a missing id and an unreadable id. Only superadmin, who passes every check, sees the missing target.

### Browse

The resource slot browse refers to one revision yet a global role protects it. A user who can read that revision cannot see the slots, so a pair pins it.

## Auto-scaling rules

A rule is a row the deployment owns. Update requires the update permission on the owning deployment, and purge requires the purge permission, for both the single and the bulk call.

### Updating several

### Purging several

## Deployment tokens

A token is a row the deployment owns. Purge requires the purge permission on the owning deployment, for both the single and the bulk call.

### Purging several

A bulk operation does not reject the whole call. Processed rows go into the processed list, and failures carry the id and the reason in the failure list.
