---
name: v2-action-spec-adoption
type: decision-table
description: entity_type judgment criteria and tables for the v2 action/spec adoption, standard wiring shapes per judgment, pass-through demotion tool mapping, non-DB target exception list
scope: src/ai/backend/manager/services
keywords: [action, spec, entity, field, global, scope, ops-direct, lookup, public, rbac, migration]
sources:
  - src/ai/backend/manager/actions/v2
  - src/ai/backend/manager/actions/registry.py
  - src/ai/backend/manager/models/specs
  - src/ai/backend/manager/repositories/ops
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: draft
---

# Manager Services layer — Knowledge

> Rules: `AGENTS.md` in the same directory. Action-framework design background:
> `../actions/KNOWLEDGE.md`. Write-spec design background: `../models/specs/KNOWLEDGE.md`.

## Why this document exists

The services layer is where domain validation and business rules live. This
document carries the layer's central judgment for the v2 transition — which
entity_type wires as which shape, and when a service method is kept. The bulk
replacement work (BA-7295~7302) is the job of aligning everything that differs
from these tables.

## Three judgment criteria, and always exactly one parent

- **Does it grant independent permissions** — is there real value in allowing/denying access to this target on its own?
- **Does it exist without a parent** — can the row be created and survive without another row (independent lifetime)?
- **Do users handle it directly** — does the API address this target for CRUD?
- The parent (`scope_of`) is always exactly one — additional access paths are expressed as memberships (`member_of`, sharing-like).
- Every entity doubles as a scope, so a non-scope entity (e.g. deployment) can parent children.

Judgment results and their wiring/spec mapping:

| Judgment | Condition | Action shape | Write spec |
|---|---|---|---|
| Scope-providing | All three yes, and it governs other entities | scope (create) / single etc. | `RoleManagedEntity*` (grants preset roles) |
| Entity | Has a parent, handled directly | scope (create) / single / bulk | `Entity*` (own VS node + member_of) |
| Global | Outside RBAC scopes, handled directly | global (gate: SA or public read) | `GlobalEntity*` (no registration) |
| Field | No independent permission, lifetime-bound | single_entity on the owner | `FieldEntity*` (requires owner_id) |
| Action-only | No target row (behavior / non-DB) | by the target's nature, no spec | — (service kept) |

## entity_type judgments — scope-providing and entity

Items still marked unresolved are settled in their migration work. Domains not
listed here split obviously by the criteria (mostly global or entity).

Scope-providing (`RoleManagedEntity*`):

| entity_type | Parent | Notes |
|---|---|---|
| domain | top level (global) | creation migrates last |
| project (group) | domain | |
| user | domain | |
| resource_group (scaling_group) | domain | |

Entity (`Entity*`):

| entity_type | Parent (scope) | Notes |
|---|---|---|
| session | project | owning user via member_of (settled) |
| vfolder | creating scope (user or project, exactly one) | |
| deployment (endpoint) | project | |
| artifact | artifact_registry | non-scope parent |
| artifact_revision | artifact | the import/approve state machine is per revision |
| model_card | project | |
| session_template | creating scope (domain/project/user) | |
| role | the scope the role belongs to | |

## entity_types demoted to fields

Authorized through their owner with no independent permission — `FieldEntity*`,
never entered into the membership graph.

| entity_type | Owner | Notes |
|---|---|---|
| kernel | session | entity registration forbidden (settled) |
| deployment:revision, route, access_token, auto_scaling_rule, replica, replica_group | deployment | (settled) |
| deployment:policy | deployment | the deployment's single (1:1, FK CASCADE) rollout-strategy config (settled) |
| role:permission, role:assignment | role | |
| keypair | user | credential — no independent permission, revoked/reissued rather than renamed |
| dotfile | keypair | packed column inside the keypairs row |
| image:alias, tag, resource_limit | image | |
| storage_namespace | object_storage | storage_id+namespace, lifetime-bound |
| fair_share x3, usage_bucket x3 | resource_group | every row carries `resource_group_id` (fair-share uniqueness is keyed on it) — the rows are the resource group's accounting decomposed by scope; domain/project/user access is a scope filter on reads, management writes are rg-level |
| resource_group:domain, resource_group:user_group | resource_group | association rows |

## entity_types judged global

Targets outside the RBAC scopes — `GlobalEntity*`, no membership registration.

| entity_type | Notes |
|---|---|
| agent, image, container_registry, artifact_registry, object_storage, vfs_storage | administrator-domain infrastructure |
| resource_slot_type, retention_policy, runtime_variant(+preset), prometheus_query_preset(+category), login_client_type, role_preset, idle_checker(+assignment), notification_channel, notification_rule, the 3 resource policies, service_catalog, app_config_definition | system settings/catalogs; only read publicity differs (public) |
| audit_log, error_log, the scheduling_history records | system records; only the `*:scoped_history` variants are scoped searches |
| invitation (today `vfolder:invitation`) | direction: split into one global invitation usable by every entity, taking entity_type/entity_id; permission granting flows through the two paths Grant / Invite |

## entity_types that stay action-only — no target row

Behaviors or non-DB targets — no spec, service kept.

| entity_type | Notes |
|---|---|
| vfolder:file | vfolder behavior, subtypes kept |
| auth | behaviors on user/keypair |
| session:file, commit, log and other subtypes | session behaviors; subtypes not split off |
| stream | target is the session — wiring axis confirmed during migration |
| etcd_config, manager_admin, metric | non-DB — see the exception list below |
| export, events, resource_overview | query/report behaviors over scoped data |

## A pass-through needs exactly one combined base

An ops-direct action inherits one `<Operation><Shape>OpsAction` combined base,
which brings `operation_type()` along; all it declares is entity_type /
action_name / the spec getter (+ the shape's target method). Real code,
`services/resource_slot/actions/create.py`:

```python
@dataclass(frozen=True)
class CreateResourceSlotTypeAction(CreateGlobalOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]):
    creator: ResourceSlotTypeCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType: ...
    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_resource_slot_type"
    @override
    def to_creator(self) -> ResourceSlotTypeCreator:
        return self.creator
```

## Wiring is nothing but factory calls

- A domain made entirely of pass-throughs has no service at all. Real code, `services/app_config_allow_list/processors.py`:

```python
class AppConfigAllowListProcessors:
    def __init__(self, group: ProcessorGroup[AppConfigAllowListData]) -> None:
        self.create = group.global_create_ops(CreateAppConfigAllowListAction)
        self.get = group.single_get_ops(GetAppConfigAllowListAction)
        self.update = group.single_update_ops(UpdateAppConfigAllowListAction)
        self.purge = group.global_purge_ops(PurgeAppConfigAllowListAction)
        self.admin_search = group.global_search_ops(AdminSearchAppConfigAllowListAction)
```

- A public global read is the variant whose gate swaps SUPERADMIN for authentication — `group.public_get_ops(...)` / `group.public_search_ops(...)`.
- A service-backed action passes the service method into the shape factory — `group.single_entity(CloneVFolderAction, service.clone)` — distinguishable by name from ops-direct (`*_ops`). The factories exist but have no callers yet; the replacement issues are the first consumers.
- The two search scopes: `operation_scopes()` is the query scope injected into the models-layer statement; `scope_targets()` is the RBAC target. An empty `operation_scopes()` is rejected, never widened to global.

## Hard actions can still be demoted to pass-throughs

Consult this table before deciding to keep a service method.

| Legacy pattern | Demotion tool | Status |
|---|---|---|
| id/name double-lookup branch | a lookup action composed with the real action by the adapter | foundation exists, zero usages |
| 1-2 lines of validation (state check, name rule) | the factory's `validators=` extra argument | available |
| folding lifecycle values into a status (pure function) | the spec's `to_data()` / the Searcher's data conversion | available |
| soft delete | `DataUpdater` (treated as a status transition; no deleter spec exists) | available |
| rank allocation | `NextValuePolicy` | **v2 gap** — legacy provider only |
| parent+child rows created together | children of an existing owner use `FieldEntity*`; creating parent and children together needs `DependentCreatorSpec` | **v2 gap** — legacy provider only |

- Until the two gaps close, only the affected actions stay service-backed.

## Non-DB targets are not ops-direct candidates

- A target with no DB row migrates with no spec — service kept, only the action bases move to v2.
- The value of the v2 move is that audit/metrics/gates apply uniformly at the action layer.

| Group | Target system | Wiring |
|---|---|---|
| etcd_config (6) | etcd | global (SA); the 3 authenticated reads are public |
| manager_admin (6) | etcd, valkey, socket | global (SA); the 3 anonymous status reads confirmed during migration |
| stream (7) | agent RPC, valkey | session-target actions — single_entity(session); only the internal GC is global |
| metric (3) | Prometheus | global + public reads |
| prometheus_query_preset preview/execute | Prometheus execution | service kept |
| vfolder file/quota/usage operations | storage proxy | service kept (vfolder permission axis) |
| agent watcher (4) | watcher HTTP | service kept |
| container_registry quota etc. | Harbor API | service kept |
