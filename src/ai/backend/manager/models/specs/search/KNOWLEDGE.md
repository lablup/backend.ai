---
name: search-field-declarations
type: design-rationale
description: why a filter or order slot is left empty on three axes (impossible by type, sensitive values recoverable by repeated filtering, query cost by column kind and index), why a to-many opens some/every/none as filters but declares no order, why a rolled-up child value becomes a parent column instead, why filters and orders are declared per field, why condition classes do not know filter DTOs, the own / nested / linked split, nested versus flattened fields, the Correlation naming, why usage relations stay out of the ownership graph, why a condition naming an unreadable entity rejects the search, what field caps need, how other services bound relations, which scopes a search accepts, the two kinds of membership in public
scope: src/ai/backend/manager/models/specs/search
keywords: [ToManyCorrelation, order_by_aggregate, SecretColumn, DecimalType, SearchableField, NestedSearchableField, RowDataConverter, ToOneCorrelation, StringConditions, EnumConditions, MembershipConditions, ConditionOrder, apply_string_filter, apply_to_many_filter, UsageConditions, UsedBy, uses, ScopeTarget, ScopedSearcher, GlobalSearcher, used_by, PublicImageTarget, CreatedInPublic, is_global, public scope, global scope]
sources:
  - src/ai/backend/manager/models/specs/search
  - src/ai/backend/manager/models/specs/conditions
  - src/ai/backend/manager/repositories/base/filter_adapter.py
  - src/ai/backend/manager/models/scopes.py
generated:
  by: claude-code/opus-5
  at: 2026-09-21
status: stable
---

# Search field declarations — Knowledge

> The rules are in `AGENTS.md` in the same directory.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

This package replaces the condition functions and order methods written by hand per entity with one declaration
per field. Filters, orders and field caps read the same list of fields.

## A per-field declaration makes omissions checkable

- With functions a "field" existed only in a naming convention, so a missing operation or order went unnoticed. A declaration carries the filter and order slots together; mypy checks orders through `match` + `assert_never`, and a sweep test checks that filter DTOs and declarations pair up.
- `RowDataConverter.to_data` calls the data constructor and reads every value through the declaration's `read(row)`, so a data field without a declaration fails mypy, and a type disagreement fails too. Reading `row.x` directly cannot be stopped by types; review stops it.

## A sensitive value leaks even when it is not in the response

- A filter reports whether a matching row exists, so repeating `starts_with` recovers the value one character at a time; an order gives the same information. Masking behind a field cap means nothing while filter and order stay open, so caps check orders too.
- Equality alone is not left as a compromise: a token's candidate set is narrow, so repeated equality confirms it. An access key is an identifier the response already carries, and its credential is `keypairs.secret_key`.
- `endpoint_tokens.token` is `sa.String`, not `SecretColumn`, so the type axis misses it; `huggingface_registries.token`, `reservoir_registries.secret_key` and `object_storages.secret_key` are the same. `sessions.bootstrap_script` and `startup_command` can hold credentials. `users.allowed_client_ip` is also an array, listed so it stays closed if that changes.

## The type settles what is impossible

- JSON/JSONB and arrays are a document structure, so comparing size means nothing. A `SecretColumn` compares ciphertext, which bears no relation to plaintext order, and equality hints at the value. A derived field has no column to put the operation on.
- `DecimalType` is stored as VARCHAR, so `"10" < "9"`; a cast makes it hold. An enum holds, but alphabetically, not in a meaningful order.

## Cost is settled by column kind and index

- A partial match on a large text column reaches no index and scans the whole table; a short string is cheap even when scanned in full.
- The single boundary is 1024. Declared lengths cluster at 16, 20, 32, 64, 128, 255, 256, 500, 512 and 1024, and the next is `16 * 1024`. At or below 1024 is a single-line value (name, path, URL, description) that users search by partial match; larger is `sa.Text` or a script.
- 256 would close partial matching on `endpoints.name` and `model_cards.name` (both 512). Two bands would leave 257 through 1023 without a rule, and `groups.description` also sits at 512.
- A to-many aggregate reruns its subquery for every outer row, so `ToManyCorrelation` has no `order`; a to-one is one row per outer row and stays open. An index ships with the declaration.

## Condition classes do not know filter DTOs

- models (`conditions/`, `orders/`, `search/`) hold columns and SQL operations; the adapter base (`BaseFilterAdapter.apply_*_filter`) holds the branches turning DTO fields into operation calls; common DTOs hold fields only, and `EnumFilter[E]` and `ToManyFilter[F]` carry no logic.
- The branches live in the adapter so models do not import API DTOs; they used to exist in the DTO, the adapter and the GQL type. `apply_*_filter` skips an unset field, and operations do not take `None`: it would give callers that surely hold a value `QueryCondition | None` and branches that never run. `@overload` narrowing would multiply declarations per operation.

## own / nested / linked split by how permission applies

- own is the entity's own columns, under its field cap; nested is rows in another table that the entity owns, also under its field cap (path `labels.key`); linked is connections to other entities, under scopes and the other entity's permission.
- The split follows ownership, not tables: labels live elsewhere but are the vfolder's data. One entry point means the sweep test and the permission check start from one place; the classes behind it are private.

## Fields of other tables are nested, not flattened

- Flattened (`label_key`, `label_value`) needs one EXISTS per field, so a key and a value matching different labels still pass; some / every / none are not expressible; the path needs a new name.
- Nested (`labels.key`) uses one EXISTS over all conditions, so they match the same label; `ToManyCorrelation` provides some / every / none; the path has the same shape as the field cap and read paths.
- every is `NOT EXISTS(NOT P)`, so it is true when there are no children (BEP-1060). A dangling field (labels) differs only in linking by `(entity_type, entity_id)` instead of a foreign key.

## A to-many opens filters and declares no order

- some is `EXISTS(P)`, every and none are `NOT EXISTS(NOT P)` and `NOT EXISTS(P)`; all three open a filter and no order. An aggregate is a correlated subquery with neither.
- Filters are open and orders are not for different reasons. some / every / none stop at the first child and the planner rewrites them into a semi-join driven from the child's index; an aggregate has no value until the children are read to the end, once per outer row.
- The same EXISTS used as an order must produce a value for every row, so it cannot fold into a semi-join. A filter is cheap only as a filter.

## A child condition is not an order key

- What is asked for is not a boolean: not "the ones with a running child first" but "healthy first, then the ones in trouble". `Endpoint.status` (`api/gql_legacy/endpoint.py`) encodes that in five values from four predicates, which a boolean order does not produce.
- The value is folded in Python today. The answer is a parent column, which becomes an `own` field with filter and order open and an index reachable; that is a schema change. `endpoints.replicas` is the desired count, not the number of live children.
- Three shipped MIN scalar subqueries fall under the ban: `UserV2OrderField.PROJECT_NAME`, `ProjectV2OrderField.USER_USERNAME`, `ProjectV2OrderField.USER_EMAIL` (26.2.0). Mark them deprecated, remove them next release, and keep them working until then.

## How other services bound a to-many order and relational filters

- Hasura opens aggregates only, Prisma `_count` alone, Hasura ndc-spec `OrderByTarget: aggregate` behind `relationships.order_by_aggregate`; OData takes a field path or a sortable function and keeps `any` / `all` for `$filter`; Elasticsearch orders by a child column only through a `mode` and a restated `nested_filter`; GitHub opens a precounted counter behind a named enum value. None orders by a predicate.
- Even the services that open a to-many order fold it into an aggregate in the end. Ordering by a condition exists nowhere; Prisma's tracker has requests for child column ordering and filtered counts, none for a predicate. This package closes the aggregate as well and sends it to a parent column, as GitHub does.
- A relation to another entity is opened to identifiers (Stripe, GitHub, Jira: FK ids and names, depth 0–1; Kubernetes: its own labels, depth 0) or not at all. Linear, Prisma and Hasura open the related entity's full filter without limit; Hasura's depth limit counts only the selection set. The more public the API, the more it stops at identifiers and owned parts. This package opens what is owned, narrows it with field caps, and expresses relations to other entities as scopes.

## No nested filters into other entities, because nothing checks permission there

- A nested filter evaluates the other row inside EXISTS without asking whether the caller can read it, so a result can reveal values of rows the caller cannot read (another user's email).
- Use a two-step lookup or an identifier copied into the entity's own column. Opening it needs a shared part that adds "rows the caller can read" inside the EXISTS. For the same reason rows with their own permission type, such as entity shares, are not `nested`.

## Called Correlation, not Relation

- In BEP-1075 `Relation` is "a link row two entities own together". These types only find rows through a correlated subquery, so they take the SQL term. `.correlate()` removes the table from the subquery's FROM only when the outer SELECT has it; used without an outer query it becomes a cross join.

## Usage relations stay out of the graph

- govern makes a project role reach the vfolders a session mounts, and a scoped search's reach ignores caps, so the listing would leak. A usage only narrows and grants nothing; its source of truth stays one foreign key column.
- Which table holds the column does not decide: `roles.role_preset_id` sits on the searched row and is one. An id inside JSON (`extra_mounts`, `vfolder_mounts`) is not a usage until it is normalized into rows with a foreign key.

## A condition naming an entity the caller cannot read rejects the search

- A scope is checked as permission to read the result entity within it (govern) and widens the result with OR; a usage (`used_by`, `uses`) is checked as own READ on the named entity and narrows with AND; a filter checks no permission and narrows.
- Results come only from rows the scopes allow, so a row reached through a usage is left out when the caller cannot read it. Search APIs with a permission model (GitHub `repo:`, GCP Cloud Asset scopes) reject a target the caller cannot read; this follows them.
- The named entity's permission is checked before the query, so SQL carries only the usage condition. BA-8024 merged `used_by` into the scope validator, which reads both in one round trip. A global search does not check named entities: the SUPERADMIN gate answers.
- The two directions sit in one bundle because the check and the narrowing are the same; the direction settles which column the condition lands on. A plain column filter checks no permission and would reveal that an unreadable row exists.
- "Who uses my resource" is `uses`. A condition joining a session and an agent sent as `used_by` alone does not say which side is wanted.

## Scopes and uses travel on the searcher

- `ScopedSearcher(scopes, used_by, searcher)` and `GlobalSearcher(used_by, searcher)` are the ops inputs. A `ScopeTarget` holds the scope id and row restriction; a `UsedBy` holds the entity and its condition, so what is checked cannot drift from what is queried.
- BA-8022 merged `ScopeItem` into `OperationScope`. `RouteHistoryTarget` stays on `OperationScope` because it is keyed by a `ReplicaID`, a `FieldIdentifier`, and naming the owning deployment needs an id the target does not carry.

## What field caps need from the declarations

- The declaration name, filter DTO field, data field and cap path are one string, so the requested path is used as the cap path without translation.
- Masking is per row because shares are per field path, so filters become `cap AND condition` and orders `CASE WHEN cap THEN column END`.
- Orders are checked too: values leak through ordering and repeated filtering even when not in the response.

## Scopes a search accepts

The tables state, for each entity package under `models/`, which scopes its search accepts. Each package's
migration implements what its row says, and review checks against it.

- Every owning scope is accepted: with one missing, a role in that scope holds the permission and still has no way to list, and only the superadmin global search remains.
- A relation that grants READ is the same: it makes the scope govern the target under a READ cap (BEP-1075). A field row holds nothing in the graph, so its scope is the owning entity.
- Owning scopes come from `created_in` in `creators.py` and `upserters.py`; READ relations from `RelationCreator` declarations and share writes; public membership from BEP-1077 5.8; existing Targets from `scopes.py`. Missing Targets are the difference.
- A `global` row is created through `CreatedInGlobal` and a global read keeps the action shape, so it is not counted as missing. A domain governs its projects and users, so an entity owned by a project or user also gets a Domain Target. A package with no search says "no search" and lists the scopes to accept once one is added.

### Why public is a scope

- A public processor checks only that the caller is logged in and adds no row condition, and it is not accepted with other scopes; a public scope checks READ on the entity type at the public singleton, declares the row condition (rows registered in public), and mixes into the Target list.
- A public processor asks for no permission, so a read still passes after READ is taken out of the public role. It has no row condition either: the four public reads of `image` return the images of registries not registered in public. As a scope, the check and the row condition sit in one class.

### Two kinds of membership in public

- Whole type: an entity whose whole type is public is written by `CreatedInPublic` and needs no row condition. Per row: a container registry, image or resource preset is written by the creator's `created_in` and the switching action, and reads a column (`container_registries.is_global`, `resource_presets.scaling_group_name`).
- public owns and governs the row either way; what differs is whether a row condition applies. An image's row condition is the `is_global` of its registry. `is_global` keeps its name because renaming moves the API and a migration with it; it means "registered in public", and code calls it public.
- Every entity in global belongs to the one global singleton, so a scope condition would filter out no row. A global read keeps the action shape: permission is per type at the global singleton, and a Target for global is not counted as missing.

### Entity, field and relation scope tables

A package whose Targets are complete declares them in its `scopes.py` and has no row here. These are the
packages with a gap or a non-obvious scope.

| Package | Scope or gap |
|---|---|
| `vfolder` | Personal folder is in a personal project; shares reach users and projects. The shared ABC `VFolderTarget` is missing |
| `image` | Container registry and optional project; per-row public on the registry's `is_global`. `PublicImageTarget` exists |
| `agent` | Resource group; global search only. `ResourceGroupAgentTarget`, `DomainAgentTarget`, `ProjectAgentTarget`, `UserAgentTarget` are missing |
| `app_config_fragment` | The row's owner (domain, user), or global and public; per-row public on `scope_type='public'` |
| `entity_share` | The attached entity; recipients are a user or a project |
| `rbac_models/role` | The scope the role is placed in; users holding it |
| `network`, `session_template` | No search. `ProjectNetworkTarget`, `DomainNetworkTarget`, `UserSessionTemplateTarget`, `ProjectSessionTemplateTarget`, `DomainSessionTemplateTarget` |
| `session_group` | Every Target leaves out the groups a replica group holds |
| `container_registry` | Per-row public on `is_global`. `ProjectContainerRegistryTarget` and `PublicContainerRegistryTarget` are missing |
| `resource_preset` | Per-row public on a NULL `scaling_group_name`. `PublicResourcePresetTarget` is missing, and a `ResourceGroupResourcePresetTarget` taking the bound rows is planned |
| `idle_checker`, `resource_policy` | Reached through `IdleCheckerAssignmentTarget` binding rows; a policy row is picked by the column naming it on the user or project row |
| `runtime_variant`, `runtime_variant_preset`, `prometheus_query_preset`, `prometheus_query_preset_category`, `resource_slot` (slot type), `login_client_type`, `deployment_revision_preset` | Whole type is public. Their `Public*Target` classes are missing |
| `scheduling_history` (route) | deployment; `RouteHistoryTarget` stays on `OperationScope`. A Target finding the owning deployment through the replica is planned |
| `session` (dependency), `resource_slot` (allocation), `resource_usage_history` (kernel usage record), `image` (alias), `service_catalog` (endpoint), `deployment_auto_scaling_policy` | No search. `SessionDependencyTarget` and `ImageAliasTarget` are planned |
| `replica_group`, `vfolder` (user mount policy) | Read as `nested` on the owning entity's declaration |
| `association_container_registries_groups`, `resource_group` relation rows, `agent_installed_image`, `event_log`, `association_artifacts_storages`, `global_entity`, `virtual_entity`, `rbac_models/entity_field` | Relations read through the two entities' Targets; no creator; singleton and graph rows are not searched |

The remaining packages declare their complete Target sets in `scopes.py`. `domain` and `resource_group` are
global and reached through linked scopes; `container_registry`, `resource_preset` and the whole-type public
packages are listed above. `alembic`, `hasher`, `minilang`, `mixins`, `rbac` and `specs` are not entity
packages.

### Reads wired through a public processor

Every read `services/*/processors.py` wires to a public processor, which checks that the caller is logged in and
checks no permission. "Login only" marks a read that does not read entities registered in public.

| Service | Wiring | Reads | Scope to move to |
|---|---|---|---|
| `login_client_type`, `prometheus_query_preset`, `prometheus_query_preset_category`, `resource_slot`, `runtime_variant`, `runtime_variant_preset` | `public_*` | All rows of the type; a name to its id | public (the whole type is in public) |
| `image` | `public_get_all_images`, `public_get_image_by_id`, `public_get_image_by_identifier`, `public_get_images_by_canonicals` | All of `images`; a status condition only | public and the owning scopes (the `ImageTarget` list). Images of registries not registered in public are read on login alone, by the legacy GQL and REST v1 |
| `resource_preset` | `list_presets`, `check_presets`, `lookup` | `resource_presets`; without a resource group the NULL `scaling_group_name` rows | public, and the resource group's scope for the bound rows (planned) |
| Nothing left | — | — | `resource_group.get_wsproxy_version` became a scope action, and `domain.bulk_get` moved to a read that checks READ per domain |
| `agent`, `artifact_registry`, `domain`, `project`, `resource_group`, `session` | `lookup`, `bulk_lookup` | A name or pair to its id | Not moved. The id only; the get that follows checks permission for the value |
| `etcd_config`, `metric`, `export`, `permission_contoller` | `public_*` | etcd settings, valkey metadata, Prometheus metric names, code constants and the wired action list | Not moved. Not an entity |
| `auth` | `public_resolve_access_key_scope` | The user owning an access key, with their domain and role | Not moved. The service decides whether the caller may act for that user |
