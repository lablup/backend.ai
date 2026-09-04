---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-08-31
Created-Version: 26.9.0
Target-Version:
Implemented-Version:
---

# Project-Scoped Ownership and Access

## Related Issues

- BA-7520 (this document), BA-6877 (shared-write migration), BA-7202, BA-7491, BA-7204 (legacy scope-mapping removal)
- BEP-1062 (Virtual Scope RBAC Ownership Model)
- BEP-1069 (Entity Lifecycle Deletion Management)
- BEP-1076 (Project Membership)

## 1. Motivation

1. Resource-holding entities are owned individually by users or projects, yet the UI presents them per project, leaving the user experience ambiguous.

2. Projects provide no visibility between members: only the owner can see an entity. Project admins and members need different levels of entity visibility.
     * Projects need a per-entity-kind visibility option. (The same mechanism must also apply to users within a project.)
          1. Do not expose entities between members.
          2. Expose only some fields of entities between members.
          3. Expose entities fully between members.

3. When a user wants to use an entity they can access from another project, there is no clear policy for how that other project reaches it.

4. When an entity's reach is wide, sharing its access can hand over far more authority than intended.

## 2. Goal

**Apply project-view-first RBAC across the board, and define access and sharing on top of it.**

1. The current UX must be expressible as configuration, and that configuration is the default.
2. Unify the ownership representation into `scope -> virtual_scope -> entity` and remove every other path.
3. Roles answer visibility, selectable below the entity kind at the field level.
4. Define one uniform set of operations for handing an entity to another scope.

## 3. Non-Goals

| Not doing | Why |
|---|---|
| Expressing business-logic relations through virtual scopes — resource-policy applicability, quota, resource-group and registry links | Virtual scopes handle access permissions only. The rest is answered by the entity row's project column and relation tables |
| Granting a way to create special objects inside a project | Objects private within an open project would hide who is consuming what from the project |
| Allowing resource entities that belong to no project | Every resource entity belongs to a project; otherwise nothing answers who deletes it or who pays for it |
| Relocating allowed storage hosts, allowed resource groups, and resource policies | Split into follow-up work. Only the direction is stated: keep the domain and project axes and remove the keypair axis (5.7) |
| Sharing to a project the sharer cannot see | There is no way to find it |
| Defining deletion and cleanup procedures | BEP-1069 defines them |

## 4. Current State & Scope, by Area

Each area states its question first, then splits **✅ what exists** from **➕ what to add**.

### 4.1 Business logic is owner-based

> An entity's project FK expresses its **owner**, not its reachability. Business logic — resource policies, quota, deletion rights — reads it; access permissions do not. Reading resource policy from the owner is the direction; the relocation itself is follow-up work (Non-Goals).

| | Content |
|---|---|
| ✅ | The owner representation differs per entity. Sessions, deployments, and model cards have a non-null project column; personal folders have a null `group` and point to no project; images have no column and are pointed to by a Docker label string — `models/vfolder/row.py:352`, `models/image/creators.py:87` |
| ✅ | Session commit allows only the personal scope, while the push destination is decided by the session's project — `services/session/service.py:413`, `models/project/row.py:205` |
| ✅ | Allowances and limits are scattered. Allowed storage hosts and allowed resource groups live on three axes — domain, project, keypair — while folder and image limits live in the user policy and the project policy — `models/resource_policy/row.py:104` |
| ➕ | Add a personal-project value to `ProjectType` and create one alongside every user |
| ➕ | Give every resource entity a project column. Personal ones point to the personal project; images move from label to column, with the label used only as the initial migration input |

### 4.2 How is permission on an entity checked

> One resolution walking `scope -> virtual_scope -> entity` answers. Single-entity checks and list queries use the same graph. Today the check unit is `(scope, entity kind, operation bits)`, so granting only part of an entity cannot be expressed, and actual list behavior lives in a legacy path.

| | Content |
|---|---|
| ✅ | The graph is the basis of permission resolution (BEP-1062). Creation-time enrollment is declared for twelve kinds; a virtual folder enrolls under either a user or a project, a session under both — `models/vfolder/creators.py:60` |
| ✅ | When a user joins a project, the user's virtual scope is bound into the project scope, so entities enrolled under the user are also reachable by project-scope permissions. Resolution is uniform over everything reachable; nothing splits rows within one scope — `repositories/permission_controller/db_source/db_source.py:1308` |
| ✅ | The backfill covered only `entity_type='user'`; existing resource entities have not a single graph row. The recursive CTE over `association_scopes_entities` is deprecated — `alembic/versions/3ebcf2c3c959`, `db_source.py:998,1131` |
| ✅ | `RBACElementType` is being merged into `EntityType`, and `permissions.entity_type` is a `String(32)`, so adding values needs no schema change — `common/data/permission/types.py:474` |
| ✅ | Actual list behavior sits in the legacy path and branches only on three roles. It is cleanup material — `api/gql_legacy/base.py:548` |
| ✅ | Global search serves superadmin and globally shared values only and skips permissions; that stays. The user data loader also skips permissions; that is to be fixed — `repositories/ops/repository.py:199`, `api/gql/data_loader/data_loaders.py:669` |
| ➕ | Backfill existing resource entities into the graph and **remove every path that is not `scope -> virtual_scope -> entity`**: the legacy recursive path, `association_scopes_entities`, `object_permissions`, `RBACElementType` (BA-7204) |
| ➕ | The graph has two relations, own and govern. Creation (`created_in`) writes both; a share writes a capped own only. Projects and users are created in their domain. A user's virtual entity is governed by its domain only; a user on a project roster is a READ-capped share |
| ➕ | Add a `field_permissions` table as a child of permission rows, and declare a catalog (fields, default-visible set) per entity. Checks always name the owning entity — the former colon sub-target names are fields |
| ➕ | Switch the list-membership condition from the owner column to graph enrollment, and add rows shared via `replace_share` to the accessible set |
| ➕ | Blank unreadable fields and refuse filtering or sorting by them. Replace the data loaders with permission-aware bulk queries |

### 4.3 Reaching an entity from another scope

> Sharing answers. Today it exists only for virtual folders and uses legacy tables.

| | Content |
|---|---|
| ✅ | Only virtual-folder invitations exist, on two legacy tables. Sessions, deployments, images, and model cards have none |
| ✅ | The share primitive takes the recipient as an entity identifier. The invitation table assumes an email recipient and has no expiry — `models/specs/membership.py:21`, `models/entity_invitation/row.py:32` |
| ✅ | `permission_cap` carries only operation bits, so it cannot express which fields are handed over |
| ➕ | A sharing-record table and named caps carrying a field axis |
| ➕ | Add sessions, deployments, images, and model cards as sharing targets |

## 5. Implementation Design

### 5.1 Ownership scope

Ownership of every entity is expressed as `scope -> virtual_scope -> entity`, not limited to resource entities.

**This path is the only one.** The recursive path over `association_scopes_entities`, `object_permissions`, and `RBACElementType` are removed. Keeping them leaves two answers to the same question.

The graph and permission rows — virtual scopes, enrollments, bindings, permissions, field permissions — are written only through the ops layer's named primitives. No other layer takes a creator or purger for these rows, and nothing creates or updates them piecemeal outside those primitives; role and preset editing hands over whole declarations that ops derives the rows from. Data migrations are the one writer outside ops. The admin mutations that address permission rows directly retire with the legacy paths.

The resource entities are sessions, virtual folders, deployments, images, and model cards. Their ownership scope is always a project. **A resource entity owned by an individual belongs to that person's personal project.** No resource entity sits under a user scope.

A user's own information is not a resource entity. Keypairs, SSH keys, dotfiles, and passwords stay under the user and do not move to a project.

A personal project is distinguished by one `ProjectType` value. `groups.type` already exists with two values, `general` and `model-store`.

| Personal project | |
|---|---|
| Creation | **Together with the user.** Always created, no exceptions, with that person as the sole member |
| Members | That one person. No additions |
| Lifetime | Tied to the user |
| Resource policy | Relocation is follow-up work (Non-Goals). Until then, personal-folder limits and allowances are answered by today's keypair-policy path |

The places where the type changes behavior are fixed as a list: no member additions, deletion tied to user purge, excluded from metrics aggregation. Everything else behaves like a regular project.

Virtual folders split by creation location.

| | Personal folder | Project folder |
|---|---|---|
| Created in | One's own personal project | That project |
| In a team project | Enrollment only, via a cap-0 share (5.4) | Belonging itself |

Personal folders are not created inside team projects. Every folder reachable by permission in a team-project scope is a project folder.

Relocating allowed storage hosts so that the owning project alone answers is follow-up work (Non-Goals). Until then, personal-folder allowance is answered by today's union path (`get_allowed_vfolder_hosts_by_user`) unchanged.

Quota scope keeps the folder row's `quota_scope_id` as is. The existing user quota scope is reinterpreted as the personal project's quota scope. No physical data moves.

Sharing puts an entity into a virtual scope, not a person into a project. Sharing into someone else's personal project adds no member to it. Sharing only adds rows to `entity_memberships` and never changes the project column, so the target of resource policies never changes.

The graph has two relations. **own** is a virtual entity holding an entity: the entity is on that virtual entity's list and one hop away. **govern** is a scope ruling a virtual entity: the scope's roles reach everything that virtual entity owns. govern is the wider of the two. Creation and sharing compose them.

| Declaration | own | govern | Rule |
|---|---|---|---|
| `created_in` at creation | yes | yes | A session is created in its project and user, a project and a user in their domain. It is on the creator's list, and the creator's roles reach what is under it (invitations). Not removed by unsharing. Ownership moves with `transfer(from_scopes, to_scopes, entity)`. A user's virtual entity is governed by its domain only, never by a project — so what the user owns does not leak into the project |
| relation `create_relation(scope, target)` | the target holds the scope under cap READ | the scope governs the target under cap READ | A project reads a resource group or registry and the agents or images it owns; the resource group or registry reads the project itself only. The only place a govern-side cap is written |
| share `replace_share(scope, entity, cap)` / `replace_share_fields(scope, entity, {READ: paths, UPDATE: paths})` | yes, capped | no | `replace_share` covers every field up to the cap — the cap is always explicit, 0 included. `replace_share_fields` puts READ/UPDATE on field paths only (5.2). Removed by `unshare`. A share is lent to the receiving scope, so it answers through that scope's own govern only and for the shared entity itself only |

A user on a project roster is a share: `replace_share_fields(project, user, {READ: the default public fields})`. There is no domain roster — a user is created in its domain. Granting auto_assign roles on joining is a separate primitive.

| Question | Answered by |
|---|---|
| Whose project is it — target of resource policy and quota, deletion rights | The entity row's project column (`vfolders.group`, `sessions.group_id`) |
| What can be done with it | Permission resolution walking `scope -> virtual_scope -> entity` |
| Which view does it appear in | Graph enrollment: the union of creation enrollment and share enrollment (5.4) |

Relations with resource groups and container registries go on the graph per the table above. A resource group seeing sessions and deployments is answered by sharing the session to the resource group under READ at scheduling (follow-up). Whether quota and resource policies apply is answered by the relation tables and the entity row, not by the graph.

### 5.2 FieldPermission

Permission below the entity kind is field-level. What the colon declarations named as sub-target types (`deployment:token`, `vfolder:data`, ...) are fields of their owning entity — token rows, folder contents, session environment — and none is promoted to an entity type. Checks always name the owning entity. The colon declarations, wired nowhere, retire together with `RBACElementType` (BA-7204).

A permission row without `FieldPermission` covers all fields. With `FieldPermission` attached, it covers only the listed fields, per operation (read and update). Adding and removing a field's rows — issuing a token — is update on that field. The catalog's default-visible set is the base list presets reference when opening only part.

Field checks are performed by the query, search, and update specs. Fields without permission are blanked on reads and dropped from update input. Interfaces where fields are requested explicitly, such as GraphQL, must answer with a rejection.

Each entity declares a catalog. A name not in the list can receive no permission, and a field not in the list is visible to no one.

| The catalog answers | |
|---|---|
| Field list | The names used in queries, sorting, and updates |
| Default-visible fields | The base set presets use when building field lists |

Four specs ground themselves on the catalog: query data conversion, conditions and ordering, updates, and natural-key lookup. A natural-key lookup requires read on the field the key belongs to. Divergence is caught by an exhaustive test.

### 5.3 Visibility

What a role holds is the visibility. No separate concept exists.

```
Resource entity: visible = a role or an individual grant grants it
Person field:    visible = a role grants it, or I fall inside the subject's disclosure range
Editable = permission grants it (same for both)
```

Resource entities have no subject axis. Making individual objects privately invisible is forbidden in Non-Goals.

The three options of Motivation 2 are expressed as role presets.

| Option | Expression |
|---|---|
| No exposure | The member role gets create only, no read or update. Only admins see |
| Some fields only | Attach a `FieldPermission` list to read. The default-visible set is the starting point |
| Full exposure | Grant the entity permission without `FieldPermission`. All fields open |

Entities are enrolled in the project but invisible without read on the member role. Creators see through the self-ownership path; admins through role permissions.

Default presets differ per entity kind. Reproducing today's behavior is the default; opening member creation of project folders is the one intended expansion.

| Kind | Member | Project admin | Owner |
|---|---|---|---|
| Virtual folder (project folder) | All operations | All operations | - |
| Session, deployment | Create only, no read | Default-visible set | Everything of one's own |
| Image, model card | None | Default-visible set | Everything of one's own |
| User (roster) | None — peers see each other through disclosure ranges | Read, default-visible fields | - |

A member without session read still sees their own sessions: self-ownership is a separate source of the accessible set (5.4).

Person fields have a disclosure range set by the subject.

```
self / project / domain / authenticated users
```

- Admins are not on this list. Admins see through the permission path.
- The project policy sets the minimum disclosure range; the subject can only pick wider.
- Fields visible to no one, like passwords, are answered by catalog non-listing. They are outside this setting.
- Updating a user belongs to domain roles and always carries a FieldPermission list. Credential secrets — secret keys, passwords, private keys — are never in any administrator's field list: administration is reissue and disable, not read, with the secret shown once to its owner at issuance.
- Session environment variables are not person fields. They are handled as session fields.

| Field | Default disclosure |
|---|---|
| Access key identifier, allowed IPs, two-factor state | Self |
| Container uid and gid | Self |
| Email, display name | Domain |

This setting depends only on the subject and the field, so it never joins into the permission-resolution query. The setting points to a named profile by reference. Opening toward a named recipient is sharing, not visibility.

### 5.4 Queries

```
Project-view query = entities enrolled in that project  AND  entities accessible to me
```

Membership judgment moves from the owner column to graph enrollment — the union of creation enrollment and share enrollment. The view filter and permission resolution walk the same graph, so the two criteria cannot diverge. The owner column remains dedicated to resource-policy and quota judgment.

The accessible set has three sources: self-ownership, scope permission, and individual shares. Scope permission does not vary per row and is a constant; only individual shares vary per row.

Every resource-entity query is a project view. The only difference is whether one looks at their own personal project or another project.

| View | Condition |
|---|---|
| Project view | Enrollment AND accessible |
| Shared with me | Individual shares only |

Conditions attach in exactly one place: scoped search. Global search remains dedicated to superadmin and globally shared values and skips permissions. It does not enter the searcher specs. Input names only the scope; whether the requester holds permission is fixed internally. User data loaders are replaced with permission-aware bulk queries.

Permission resolution serves only the admission decision at the API boundary. Internal calls run no permission queries.

A cap-0 share enrollment joins the enrollment set but grants nothing. It exists so an owner can surface their personal folder in a team project's view; other members and admins see nothing because their accessible set is empty.

Scoped read actions filter instead of rejecting. Write-natured scoped actions keep rejecting as today, marked per action.

Filling only readable fields happens by one more resolution pass after rows are fetched. Rows never shrink, so pagination stays intact.

Unreadable fields cannot be used for filtering or sorting. Identifiers pointing at other entities belong to the default-visible set. Following an identifier into that entity takes that entity's permission and is rejected without it. The response carries the list of fields filled this time and never explains why one is empty.

### 5.5 Sharing

A target must pass three checks: does ownership differ per instance, does the owner have a reason to show it, and does use in another scope make sense.

| Entity | |
|---|---|
| Virtual folder, deployment, model card | Target |
| Session | Observation only; entering excluded |
| Image | Target after ownership moves to a column |
| Keypair, secret | Not a target |
| Kernel, route, session group | Not a target |

Entering sessions is excluded because mounts bypass access control. Mounting a personal folder is allowed only when no one but the owner can enter that session, checked at mount time. Mountability is an ownership-based check independent of enrollment; enrollment answers exposure only.

An invisible target cannot be named.

| Target | Address | Acceptance |
|---|---|---|
| Person (same-domain account) | Email | Not needed |
| Person (outside the domain or unregistered) | Email | Needed |
| A project I am a member of | Project | Not needed; the receiving side's acceptance setting answers |
| Ownership transfer | | Recipient must accept |

To give to an outside team, give to a person on that team who then puts it into their own team. What is given to a person lands in that person's personal project.

A cap is a row per bit on each share row. `replace_share(scope, entity, cap)` writes one "every field" row per bit of the cap; `replace_share_fields(scope, entity, fields)` writes "path" rows on the READ/UPDATE bits — sharing a deployment without its token is `replace_share_fields` with the token path left out. A path covers its descendants, and there is no deny. The effective fields are the intersection of the role's field scope and the field scopes of the caps on the path. A named cap (a preset) is a convenience calling these two; it is not a stored unit.

| Place | Meaning | Composition |
|---|---|---|
| Preset default | What is given | Union per kind |
| Role setting | What is given | Union per kind |
| One share's cap | Ceiling | Intersection |
| Cap carried by an invitation | Ceiling | Intersection |

```
granted[entity][element_type] |= permission(scope, element_type) & scope_cap & entity_cap
```

A shareable kind must exist in the recipient's own-scope role. Caps only narrow, so without one the share grants nothing. A cap of zero is valid: it grants nothing while leaving the enrollment (5.4).

Re-sharing is expressed by the cap's create bit and defaults to closed. Opening it requires cascading revocation, which requires recording the parent share. No combination opens re-sharing without the cascade. Fields one does not hold cannot be passed on.

Revocation can be done both by anyone who can share and by the recipient, and is not retroactive on running work.

Invitations, shares, and revocations live in one table, separate from `entity_memberships`.

| State | Graph row |
|---|---|
| Invited | None |
| Active | Present |
| Declined, expired | None |
| Revoked | Deleted |

A direct share skips the invited state and starts active. Nothing about the recipient is exposed beyond what the inviter already knows. The recipient's user identifier is not recorded; email reuse is blocked by expiry and cleanup at user purge.

Deletion is defined by BEP-1069. The sharing side decides three things.

| | |
|---|---|
| When the owning side deletes | It disappears from every shared target |
| Soft delete | Sharing rows are kept |
| Purge | Sharing rows are deleted |

A non-owning project has no delete operation, only unshare.

Resource-group allowance is checked against the submitting subject and stays ownership-based. Every action on something shared is checked against the owning project.

### 5.6 What differs per entity

| Entity | Ownership | Access | Sharing | Migration |
|---|---|---|---|---|
| Virtual folder | Personal folders in personal projects, project folders in their project | Folder data served as a field; members get all operations on project folders | New; includes cap-0 enrollment | Move personal folders' ownership and enrollment to personal projects |
| Session | Already project | Members create only; detail and environment split as fields | Observation only | None |
| Deployment | Already project | Members create only; token and revision served as fields | New | None |
| Image | Label to column; committed images owned by personal projects | Nothing to split | After the column migration | Label backfill |
| Model card | Already project | Nothing to split | New | None |
| User | Is a scope itself | Credentials and profile split as fields | Not a target | None |

### 5.7 Migration / Compatibility

| Step | What |
|---|---|
| 1 | Backfill virtual-scope membership for resource entities |
| 2 | Add the `ProjectType` value and create a personal project per user; the user-creation path creates them from then on |
| 3 | Move personal folders' owner column and enrollment to personal projects. `quota_scope_id` stays |
| 4 | Move image labels into the owner column, targeting personal projects. The label serves only as this initial input |
| 5 | Migrate the legacy virtual-folder sharing tables into the sharing record and the graph |

Without step 1 nothing else does anything. Sessions, deployments, and model cards have non-null project columns, so there is nothing to move.

Relocating resource policies and allowances is follow-up work (Non-Goals). Until then, personal-folder limits and allowances are answered by today's keypair-policy path unchanged, so this migration does not alter check behavior. The follow-up direction: keep allowed storage hosts and allowed resource groups on the domain and project axes only, removing the keypair axis; move the user policy's folder and image limits into the project policy; absorb the `allowed_vfolder_types` setting into policy and retire it.

Committed images stay personal-only as today, with the ownership scope becoming the personal project. The physical registry pushed to still follows the session's project settings, independent of ownership. Physical placement does not change.

A personal project left behind becomes an ownerless project. Either block purging the user until it is empty, or purge it together after a grace period.

| Today | After |
|---|---|
| Regular users see only their own sessions | Same. Not granting session read to the member role is the default |
| Domain admins see the whole domain | Same |
| Personal folders visible only to the owner and grantees | Same, sitting in personal projects that are not bound into team-project scopes |
| Storage hosts usable for personal folders | Same. Check paths do not change |
| Project folders visible to all members | Same |
| Project folder creation | Widens: from admin-only to all members — `services/vfolder/services/vfolder.py:329` |
| Folder invitations | Same, with projects added as targets |
| Session commit | Same, personal-owned only |
| Teammates' user information | Narrows: credentials become hidden |
| Admins reading keypair secrets | Narrows: credential secrets become unreadable for everyone; administration becomes reissue and disable |

Opening project-folder creation and narrowing user information are the intended changes.

| The UI needs | |
|---|---|
| Shared-with-me list | A query using individual grants only |
| Owner display | The owning project's name only |
| Delete button | Absent in non-owning projects |

## 6. Decision Summary

| Decision | Content |
|---|---|
| Ownership representation | Unified into `scope -> virtual_scope -> entity`, not limited to resource entities |
| Other paths | Removed: the legacy recursive path, `association_scopes_entities`, `object_permissions`, `RBACElementType` |
| Writing the graph and permission rows | Only through the ops primitives — no creator/purger surface for these rows elsewhere. Role and preset editing passes whole declarations; direct permission-row mutations retire with the legacy paths |
| Resource-entity ownership scope | Always a project; individually owned ones go to personal projects |
| Personal folders | Created only in personal projects; none inside team projects |
| Allowed storage hosts and resource policies | Relocation is follow-up work; until then the keypair-policy path answers, so check behavior does not change |
| Quota scope | `quota_scope_id` kept; the user quota scope reinterpreted as the personal project's. No physical moves |
| A user's own information | Not a resource entity; stays under the user |
| Column vs. graph | The column answers resource policy and quota, permission resolution answers capability, graph enrollment answers view membership |
| Relations | own and govern. `created_in` writes both; a share and a relation write a capped own only. A user's virtual entity is governed by its domain only |
| Rosters | A user on a project roster is a READ-capped share (the default public fields). domain → user is govern |
| Joining a project | Project admins invite, with the invitee's acceptance; direct registration is a domain-admin operation (BEP-1076) |
| Credential secrets | Never readable by any administrator; administration is reissue and disable. The secret is shown once to its owner at issuance |
| relation | The scope governs the target under READ; the target holds the scope under a READ share. Resource groups and container registries alike. Quota is answered by the relation table |
| The `created_in` rows | Not removed by unsharing, and carry no cap |
| Former colon sub-targets | Fields of their owning entity — none is promoted to an entity type; the colon declarations retire with `RBACElementType` |
| Fields | `FieldPermission` — child of a permission row, read and update. Absent means all fields; present means only the list |
| Catalog | Declared per entity; unlisted names get no permission and unlisted fields are invisible |
| Visibility | Roles answer. Resource entities use the permission axis only; person fields use permission or the subject's disclosure range |
| Member default preset | All operations on project folders; create-only for sessions and deployments; none for images and model cards |
| Person-field disclosure | self / project / domain / authenticated users. The project policy sets the minimum; subjects can only widen |
| Queries | Graph enrollment AND accessible (self-owned / scope permission / individual share), in one scoped-search spot. Every query is a project view |
| Global search and data loaders | Global search stays superadmin- and global-share-only; data loaders replaced with permission-aware bulk queries |
| Where resolution runs | Only the admission decision at the API boundary; internal calls run no permission queries |
| Cap-0 sharing | Leaves enrollment only and grants nothing; for surfacing in the owner's project view |
| Reference fields | Identifiers are default-visible; dereferencing takes the target entity's permission and is rejected without it |
| Scoped reads | Filter instead of rejecting; write actions keep rejecting |
| Sharing address | Invisible targets cannot be named. People by email, projects only those I am a member of |
| Share acceptance | Unneeded when only capability grows; projects answer with an acceptance setting |
| Share caps | One cap row per bit on each share row. `replace_share` covers every field, `replace_share_fields` field paths. A named cap is a convenience calling both |
| Re-sharing | Closed by default; opening requires cascading revocation |
| Sharing records | Separate from `entity_memberships`; the invited state has no graph row |
| Non-owning projects | No delete operation, only unshare |
| Resource-group allowance | Ownership-based; sharing moves no placement rights |
| Committed images | Personal-owned only as today; ownership scope is the personal project, physical registry follows session-project settings |
| Migration order | Graph backfill first; check behavior does not change |
| Personal-project creation | Together with the user, always, no exceptions |
| Personal-project distinction | A `ProjectType` value, with the behavior-changing spots fixed as a list |

## 7. Open Questions

- Whether the catalog (fields, default-visible set) lives in code declarations or a table
- Whether user purge is blocked until the personal project is empty, or auto-purged after a grace period
- Whether model cards fold into virtual folders or stay a separate entity
- Whether admins should be able to observe cap-0 enrollments (external folders hooked into a project); if so, putting read into the cap is a separate decision
- Whether to provide converting a personal folder into a project folder
- At which layer GraphQL turns explicitly requested, unpermitted fields into rejections
- Whether to show how many places use an entity before deletion

## 8. References

- [BEP-1062: Virtual Scope RBAC Ownership Model](BEP-1062-virtual-scope-rbac.md)
- [BEP-1069: Entity Lifecycle Deletion Management](BEP-1069-entity-lifecycle-deletion.md)
- [BEP-1076: Project Membership](BEP-1076-project-membership.md)
