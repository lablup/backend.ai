---
name: search-field-declarations
type: design-rationale
description: why a filter or order slot is left empty on three axes (impossible by type, sensitive values recoverable by repeated filtering, query cost by column kind and index), why a to-many opens some/every/none as filters but declares no order at all, and why a rolled-up child value becomes a parent column instead, why search filters and orders are declared per field instead of per-entity condition functions, why the declaration builds the data type from a row, why condition classes do not know filter DTOs, why operations reject None, the own / nested / linked split and its permission axes, nested versus flattened fields of other tables, the Correlation naming, why usage relations between entities stay out of the ownership graph, why an unreadable using entity refuses the search, why scopes and uses travel on the searcher, what field caps need from the declarations, how other services bound relational filters, which scopes a search accepts, why public is a scope rather than a login-only processor, membership versus relation into public, why global reads keep the action shape
scope: src/ai/backend/manager/models/specs/search
keywords: [ToManyCorrelation, order_by_aggregate, relation count order, EndpointStatus, RouteHealthStatus, endpoint_tokens.token, secret_key, bootstrap_script, startup_command, callback_url, allowed_client_ip, SecretColumn, DecimalType, SearchableField, NestedSearchableField, RowDataConverter, ToOneCorrelation, StringConditions, EnumConditions, MembershipConditions, ConditionOrder, apply_string_filter, apply_to_many_filter, UsageConditions, UsedBy, ScopeTarget, ScopedSearcher, GlobalSearcher, used_by, PublicImageTarget, CreatedInPublic, is_global, public scope, global scope, search scope table]
sources:
  - src/ai/backend/manager/models/specs/search
  - src/ai/backend/manager/models/specs/conditions
  - src/ai/backend/manager/models/specs/orders
  - src/ai/backend/manager/repositories/base/filter_adapter.py
  - src/ai/backend/manager/models/vfolder/searchable_fields.py
  - src/ai/backend/manager/models/session/row.py
  - src/ai/backend/manager/models/endpoint/row.py
  - src/ai/backend/manager/models/deployment_revision/row.py
  - src/ai/backend/manager/models/user/row.py
  - src/ai/backend/manager/models/routing/row.py
  - src/ai/backend/manager/api/gql_legacy/endpoint.py
  - src/ai/backend/manager/models/entity_label/searchable_fields.py
  - src/ai/backend/manager/models/scopes.py
  - src/ai/backend/manager/models/specs/searcher.py
  - src/ai/backend/manager/actions/v2/scope/validator/rbac.py
  - src/ai/backend/manager/models/image/scopes.py
  - src/ai/backend/manager/models/specs/created_in.py
  - src/ai/backend/manager/actions/registry/group.py
generated:
  by: claude-code/opus-5
  at: 2026-09-21
status: stable
---

# Search field declarations — Knowledge

> The rules are in `AGENTS.md` in the same directory.

This package replaces the condition functions and order methods written by hand per entity, one per field and operation, with one declaration per field. Filters, orders and permissions (field caps) all read the same list of fields.

## Declaring per field makes omissions checkable

- With functions, a "field" existed only in a naming convention, so a missing operation or order went unnoticed.
- A declaration carries a filter slot and an order slot together, so whether a field can be filtered or ordered shows in the declaration.
- mypy checks orders through `match` + `assert_never`; a sweep test checks that filter DTOs and declarations pair up.

## Building data from a row through the declaration makes omissions a type error

- Comparing declarations to data in a test misses an omission when the test, or the registration it relies on, is missing.
- `RowDataConverter.to_data` calls the data constructor directly and reads every value through the declaration's `read(row)`. Adding a data field without a declaration then fails mypy.
- `read` returns the column's value type, so mypy also checks that the declaration and the data field agree on type.
- Reading `row.x` directly instead of through the declaration cannot be stopped by types; review stops it.

## Why the reasons for an empty slot are split into three axes

- The earlier rule listed only what the type forbids. A value that works but is deliberately left out had no rule, so each entity's author decided again.
- Splitting the axes removes that decision. The type settles the impossible ones; sensitive and cost are settled by matching against a row of a table.
- Fixing the count at three is itself a rule. A slot emptied for a fourth reason carries that reason nowhere.

## The type settles what is impossible

| Column kind | Why it does not hold |
|---|---|
| JSON/JSONB, arrays | A document structure; comparing size means nothing |
| `SecretColumn` | Comparing ciphertext bears no relation to plaintext order, and equality hints at the value |
| Derived field | There is no column to put the operation on |
| `DecimalType` | Stored as VARCHAR, so `"10" < "9"`. A cast makes it hold |
| enum | Holds. Alphabetical, not a meaningful order |

## A sensitive value leaks even when it is not in the response

- A filter reports whether a row satisfying the condition exists. Repeating `starts_with` one character at a time recovers the whole value. An order gives the same information.
- So masking a value behind a field cap means nothing while its filter and order stay open. It is why caps check orders too.
- Leaving equality alone as a compromise is not used. A token has a narrow candidate set, so repeated equality confirms it.
- An access key is an identifier the response already carries, and the credential is its pair `keypairs.secret_key`, a `SecretColumn`. A value the response ships has nothing for a repeated filter to recover, so it does not belong on this axis.
- The rows of the table are the cases found in the survey. `endpoint_tokens.token` is `sa.String`, not `SecretColumn`, so the type axis does not catch it. `sessions.bootstrap_script` and `startup_command` are scripts the user wrote and can hold credentials verbatim.
- `users.allowed_client_ip` is caught by the type axis as well, being an array. It is listed as sensitive too so that it stays closed if it ever stops being an array.

## Cost is settled by column kind and index

- A partial match on a large text column reaches no index and becomes a full scan; one search reads the whole table. A short string is not held to the same bar, since even scanned in full the per-row comparison is cheap.
- The single boundary at 1024 comes from counting the schema. Declared lengths cluster at 16, 20, 32, 64, 128, 255, 256, 500, 512 and 1024, and the next one up is `16 * 1024`. Everything at 1024 or below is a single-line value — a name, a path, a URL, a description — and is what users actually search by partial match. Anything larger is `sa.Text` or a script.
- A boundary at 256 would close partial matching on `endpoints.name` and `model_cards.name`, both 512. A rule that closes name search removes a feature rather than saving cost.
- Two bands would leave 257 through 1023 with no rule, and columns do sit there (`endpoints.name`, `model_cards.name` and `groups.description` are all 512), so the boundary has to be single.
- A to-many aggregate runs its subquery again for every outer row. `ToManyCorrelation` having no `order` is not an inability to express it but the decision not to open aggregates. A to-one is one row per outer row, so it stays open.
- An index ships in the same change as the declaration. A partial match opened without one stays until the load shows up.

## Condition classes do not know filter DTOs

| Layer | Holds |
|---|---|
| models (`conditions/`, `orders/`, `search/`) | Columns and SQL operations |
| adapter base (`BaseFilterAdapter.apply_*_filter`) | The branches turning DTO fields into operation calls |
| common DTOs | Fields only. Generic bases such as `EnumFilter[E]` and `ToManyFilter[F]` carry no logic either |

- The branches live in the adapter so that models do not import API DTOs.
- They used to exist three times — in the DTO, the adapter and the GQL type — and now exist once, in the adapter.

## Operations reject None

- Accepting `None` would make even callers that surely hold a value (guards, handlers) receive `QueryCondition | None`, adding branches that never run.
- Narrowing with `@overload` is not used: it multiplies the declarations per operation.
- Skipping an unset field happens in one place, `apply_*_filter`.

## own / nested / linked split by how permission applies

| Part | Criterion | Permission |
|---|---|---|
| own | The entity's own columns | The entity's field cap |
| nested | Rows in another table that the entity owns | The entity's field cap (path `labels.key`) |
| linked | Connections to other entities | Scopes, the other entity's permission |

- The split follows ownership, not tables. Labels live in another table but are the vfolder's data.
- One entry point means the sweep test and the permission check start from one place. The classes behind it are never referenced by name, so they are private.

## Fields of other tables are nested, not flattened

| | Flattened (`label_key`, `label_value`) | Nested (`labels.key`) |
|---|---|---|
| Grouping | One EXISTS per field, so a key and a value matching different labels still pass | One EXISTS over all conditions; they must match the same label |
| some / every / none | Not expressible | Provided by `ToManyCorrelation` |
| Path | Needs a new name | Same shape as the field cap and read paths |

- every is `NOT EXISTS(NOT P)`, so it is true when there are no children (BEP-1060).
- A dangling field (labels) differs only in linking by `(entity_type, entity_id)` instead of a foreign key; it is the same to-many.

## A to-many opens filters and declares no order

| Shape | SQL | Filter | Order |
|---|---|---|---|
| some | `EXISTS(P)` | Open | Not open |
| every / none | `NOT EXISTS(NOT P)` / `NOT EXISTS(P)` | Open | Not open |
| aggregate | Correlated aggregate subquery | Not open | Not open |

The reason the filters are open differs from the reason the orders are not.

- some / every / none can stop at the first child that satisfies (or breaks) the condition, and the planner can rewrite them into a semi-join driven from the child's index. They do not touch every outer row.
- An aggregate has no value until the children are read to the end, and that repeats once per outer row.
- The same EXISTS used as an order has to produce a value for every row in the result, so it does not fold into a semi-join. A filter is cheap only as a filter.

## Why a child condition does not become an order key

- Ahead of cost: what is actually asked for is not a boolean. The request is not "the ones with a running child first" but "healthy first, then the ones in trouble".
- `Endpoint.status` (`api/gql_legacy/endpoint.py`) is that request in code. No children is DEGRADED, no active children is UNHEALTHY, all HEALTHY is HEALTHY, all UNHEALTHY is UNHEALTHY, and the rest is DEGRADED. Five values woven from four predicates.
- Opening a boolean order does not produce that sequence. What would be opened is not what is asked for, so opening it leaves the request standing.
- The value is currently folded in Python after loading every child row. The answer is not to open the order but to have the server keep the value as a column. It then becomes an `own` field, filter and order open together, and an index reaches it. That is a schema change and stays separate work.
- `endpoints.replicas` is the desired count, not the number of live children. A folded value promoted to a column says in its name what it counted.

## A to-many order already exposed leaves through deprecation

| Exposed value | Implementation | Exposed in |
|---|---|---|
| `UserV2OrderField.PROJECT_NAME` | `UserOrders.by_project_name` — `MIN(projects.name)` scalar subquery | 26.2.0 |
| `ProjectV2OrderField.USER_USERNAME` | `ProjectOrders.by_user_username` — `MIN(users.username)` | 26.2.0 |
| `ProjectV2OrderField.USER_EMAIL` | `ProjectOrders.by_user_email` — `MIN(users.email)` | 26.2.0 |

- All three fold M:N children with `MIN` to order by them. That is the shape being banned.
- The rule is not loosened to fit them. What already shipped is a migration target, not a counterexample to the rule.
- Deleting an exposed order field outright breaks the queries of clients already using it. Mark it deprecated, remove it in the next release, and keep it working until then.
- This is why the rule is written down first. Without it, a fourth and a fifth arrive the same way.

## Other services open a to-many order no further than aggregates

This is about child rows an entity owns. Filters reaching into another entity are in `How other services open relational filters`.

| Service | Opens for a to-many order | Predicate order |
|---|---|---|
| Hasura | Aggregates only — "array relationships only supporting aggregates for sorting" | None |
| Prisma | `_count` alone | None |
| Hasura ndc-spec | `OrderByTarget: aggregate`, split out behind the `relationships.order_by_aggregate` capability | None |
| OData | `$orderby` takes a field path or a sortable function. The `any` / `all` lambdas are for `$filter` | None |
| Elasticsearch | Opens child column ordering, but requires `mode` (min/max/avg/sum) and a restated `nested_filter` | None |
| GitHub | A precounted counter behind a named enum value (`STARGAZERS`, `COMMENTS`) | None |

- Even the services that decided to give a to-many order fold it into an aggregate in the end. Elasticsearch is the one case that orders by a child column, and it requires a `mode` to fold the several children into one.
- Taking a condition as an order key exists nowhere. Prisma's tracker carries requests for child column ordering and for ordering by a filtered count, but none for ordering by a predicate.
- This package closes the aggregate as well and sends it to a parent column, the way GitHub opens a counter.

## No nested filters into other entities, because nothing checks permission there

- The validator checks the caller's permission on a scope beforehand, but a nested filter only evaluates the other row's values inside EXISTS, row by row, without asking whether the caller can read that row.
- A filter result could then reveal values of rows the caller cannot read (another user's email, for example).
- Where it is needed (the related entity's status, searching by a display value, ordering by a related attribute), use a two-step lookup or an identifier copied into the entity's own column.
- Opening it would first need a shared part that adds "rows the caller can read" inside the EXISTS.
- For the same reason, rows with their own permission type, such as entity shares, are not `nested`.

## Called Correlation, not Relation

- In BEP-1075, `Relation` means "a link row two entities own together".
- The types here only find rows of another table linked to the outer row through a correlated subquery, so they take the SQL term.
- `.correlate()` removes the table from the subquery's FROM only when the outer SELECT has it. Used without an outer query it becomes a cross join.

## Usage relations stay out of the graph

- govern means "the scope's roles reach everything the target owns", so a project role governing a session would reach the vfolders it mounts.
- own + cap (a share) does not spread for per-entity permission, but a scoped search's reach ignores caps, so the listing would leak.
- So a usage only narrows and grants nothing. Its source of truth stays one foreign key column on the using side.
- An id inside a JSON value (`extra_mounts`, `vfolder_mounts`) is not a foreign key and is not a usage. It becomes one after it is normalized into rows with a foreign key.

## An unreadable using entity refuses the search

| Input | Check | Effect on the result |
|---|---|---|
| scope | Permission to read the result entity within the scope (govern) | Widens (OR) |
| used_by | Permission to read the using entity itself (own READ) | Narrows (AND) |
| filter | None | Narrows |

- Results only come from rows the scopes allow, so a row a using entity uses is still left out when the caller cannot read it.
- Search APIs with a permission model (GitHub search `repo:`, GCP Cloud Asset scopes) refuse a condition target the caller cannot read and limit results to what the caller can read. This follows them.
- The using side's permission is checked before the query, so SQL carries only the usage condition.
- used_by exists only on searches and means nothing to other scope actions such as create, so it started as a separate validator. BA-8024 merged it into the scope validator, which now reads both in one database round trip.
- A global search does not check using entities: the SUPERADMIN gate answers for the unscoped read.
- This does not answer an owner asking "who uses my resource". That needs a limited usage listing on the result entity's side.

## Scopes and uses travel on the searcher

- `ScopedSearcher(scopes, used_by, searcher)` and `GlobalSearcher(used_by, searcher)` are the ops inputs. The action takes that one object as its field, and the checks read their targets from it.
- A `ScopeTarget` holds the scope id to check and the row restriction; a `UsedBy` holds the entity to check and its condition. What is checked cannot drift from what is queried.
- Before this, a `ScopeItem` wrapped an `OperationScope` one-to-one to form that pair. 31 of the 72 `OperationScope` classes had no item, so no authorization target was declared for them. BA-8022 merged every wrapper into its scope and moved the rest over, so the pair is one class.
- `RouteHistoryTarget` is the exception still on `OperationScope`: it is keyed by a `ReplicaID`, which is a `FieldIdentifier`, and a replica is authorized through the deployment that owns it. Naming that scope needs the owning deployment id, which the target does not carry.

## What field caps need from the declarations

| Need | Why |
|---|---|
| Declaration name = filter DTO field = data field = cap path | The requested path is used as the cap path without translation |
| Masking per row | Shares are per field path, so the same field has a different cap per row. Filters become `cap AND condition`, orders `CASE WHEN cap THEN column END` |
| Checking orders too | Values leak through ordering and repeated filtering even when not in the response |

## How other services open relational filters

| Service | Opens | Depth |
|---|---|---|
| Stripe, GitHub, Jira | Identifiers such as FK ids and names | 0–1 |
| Kubernetes | Its own labels | 0 |
| Linear, Prisma, Hasura | The related entity's full filter | Unlimited |
| Hasura depth limit | Counts only the selection set, not filter conditions | n/a |

- The more public the API, the more it stops at identifiers and owned parts.
- This package opens everything owned, narrows it with field caps, and expresses relations to other entities as scopes.

## Scopes a search accepts

The tables below state, for each entity package under `models/`, which scopes its search accepts. Each package's migration implements what its row says, and review checks against it.

### Why every owning scope is accepted

- With one owning scope missing, a role in that scope holds the permission and still has no way to list. What remains is the global search, which belongs to superadmin.
- A relation that grants READ is the same. A relation makes the scope govern the target under a READ cap (BEP-1075), so the scope's roles read the target and what it owns. This is how a project reads the images of a container registry.
- A field row holds nothing in the graph. Its owning entity answers whether it can be read, so its scope is the owning entity.

### Why public is a scope

| | public processor | public scope |
|---|---|---|
| Check | Whether the caller is logged in | READ on the entity type at the public singleton |
| Row condition | None | Declared by the Target (rows registered in public) |
| Accepted together with other scopes | No | Mixed into the Target list |

- A public processor asks for no permission, so a read still passes after READ is taken out of the public role. It has no row condition either: the four public reads of `image` return the images of registries not registered in public.
- As a scope, what is checked and the row condition sit in one class, for the reason in `Scopes and uses travel on the searcher`.

### Two ways into public

| Way | Applies to | Written by | Row condition |
|---|---|---|---|
| Membership | An entity whose whole type is public | `CreatedInPublic` | None |
| Relation | An entity switched per row. Today only container registry | A relation to public, purged when switched off | A column (`is_global`) |

- The source of a relation into public is the column. Recovery and query conditions read it (BEP-1077 5.8).
- `is_global` keeps its name: renaming it moves the API and a migration with it. It does not mean the global singleton, so code calls it public.

### Why a global read keeps the action shape

- Every entity in global belongs to the one global singleton. A scope condition would filter out no row.
- Permission is per type. READ on the type at the global singleton reads all of it; without it, none.

### Reading the scope tables

| Column | Meaning | Read from |
|---|---|---|
| Owning scopes | The scopes that own and govern the row when it is created | `created_in` in `creators.py` and `upserters.py` |
| READ relations | Links that are not ownership and still grant READ | `RelationCreator` declarations, share writes |
| public | Membership (the whole type is in public) / relation (registered in public per row) / n/a | The classification table in BEP-1077 5.8, columns |
| Existing Targets | Classes declared in `scopes.py` | `scopes.py` |
| Missing Targets | What the rules call for and is absent | The difference from the three columns above |

- A `global` row is one created through `CreatedInGlobal`. A global read keeps the action shape, so a Target for global is not counted as missing.
- A domain governs its projects and users. An entity owned by a project or a user also gets a Domain Target, as the pilots (vfolder, session, deployment, model card) do.
- A package with no search yet says "no search" under missing Targets, followed by the scopes to accept once a search is added.

### Cells still to be decided

| No. | Subject | Question | Options |
|---|---|---|---|
| 1 | resource preset | Whether a preset whose `scaling_group_name` is NULL is a relation to public | A relation to public (the BEP-1077 5.8 classification; migration step 8 already links them) / a global read only |
| 2 | resource preset | Whether a preset bound to a resource group is accepted under that resource group's scope. Ownership is global and the link is one column | `ResourceGroupResourcePresetTarget` with a column condition / a filter only |
| 3 | The 7 types that are public as a whole (runtime variant, runtime variant preset, prometheus query preset, prometheus query preset category, resource slot type, login client type, deployment preset) | BEP-1077 puts them in global and public, but their creators are `CreatedInGlobal`. A newly created row has no public membership | Change the creators to `CreatedInPublic` / let the public Target read the whole type with no condition |
| 4 | project resource policy | The user and keypair policies have a Target for "the policy this user is subject to". Whether the project policy gets the same shape | Add `ProjectResourcePolicyTarget` / a global read only |
| 5 | fair share, usage bucket | The Targets are authorized against a resource group while the rows name a domain, project or user. Which side is the owning entity | Keep the resource group / accept the domain, project or user the row names / accept both |
| 6 | idle checker | A relation (binding) grants the scope READ on the checker. Today's Target reads binding rows and the checker is read through global only | Add per-scope checker Targets / the binding Target is enough |
| 7 | `is_public` on resource group | No search or permission path reads the column (only export reports do). Its name overlaps with registration in public | Move it to a relation to public / leave it as an unrelated column |
| 8 | route history | `RouteHistoryTarget` cannot declare what it is authorized against (keyed by a replica, with no owning deployment id) | The Target also takes the deployment id / replace it with a deployment-keyed Target |
| 9 | `bulk_get` of domain | The public processor is the only way a regular user reads their own domain | Grant a user READ on their domain and move it to the domain scope / split off a read carrying only the fields to expose and keep it in public / do not move it |
| 10 | `lookup` of user | Whether resolving an email to an id stays a login-only read | Do not move it / move it to the domain and project scopes |

### Entities owned by a domain, project, user or another entity

| Package | Owning scopes | READ relations | public | Existing Targets | Missing Targets |
|---|---|---|---|---|---|
| `session` | user, project | None | n/a | `DomainSessionTarget`, `UserSessionTarget`, `ProjectSessionTarget` | None |
| `endpoint` (deployment) | project, user | None | n/a | `DomainDeploymentTarget`, `ProjectDeploymentTarget`, `UserDeploymentTarget` | None |
| `vfolder` | project (a personal folder is in a personal project) | Users and projects it is shared to | n/a | `DomainVFolderTarget`, `ProjectVFolderTarget`, `UserVFolderTarget` | The shared ABC `VFolderTarget` |
| `model_card` | project, user | None | n/a | `DomainModelCardTarget`, `UserModelCardTarget`, `ProjectModelCardTarget` | None |
| `image` | container registry, project (optional) | Projects linked to the registry | Relation (the registry's `is_global`) | `DomainImageTarget`, `ProjectImageTarget`, `UserImageTarget`, `ContainerRegistryImageTarget`, `PublicImageTarget` | None |
| `project` | domain, global | Users on its roster, linked resource groups | n/a | `DomainProjectTarget`, `UserProjectTarget`, `ResourceGroupProjectTarget` | None |
| `user` | domain, global | Projects whose roster it is on, roles | n/a | `DomainUserTarget`, `ProjectUserTarget`, `RoleUserTarget` | None |
| `agent` | resource group | Domains, projects and users linked to the resource group | n/a | None (global search only) | `ResourceGroupAgentTarget`, `DomainAgentTarget`, `ProjectAgentTarget`, `UserAgentTarget` |
| `app_config_fragment` | The row's owner (domain, user), or global and public | None | Membership (rows with `scope_type='public'`) | `AppConfigFragmentTarget`, `VisibleAppConfigFragmentTarget`, `PublicAppConfigFragmentTarget` | None |
| `entity_share` | The entity the offer is attached to | The receiving user or project | n/a | `RecipientUserEntityShareTarget`, `RecipientProjectEntityShareTarget`, `OwningEntityShareTarget` | None |
| `rbac_models/role` | The scope the role is placed in | Users holding the role | n/a | `ScopedRoleTarget`, `HeldRoleTarget` | None |
| `network` | project | None | n/a | None | No search. `ProjectNetworkTarget`, `DomainNetworkTarget` |
| `session_group` | project, user | None | n/a | None | No search. `ProjectSessionGroupTarget`, `UserSessionGroupTarget`, `DomainSessionGroupTarget` |
| `session_template` | user, project (optional) | None | n/a | None | No search. `UserSessionTemplateTarget`, `ProjectSessionTemplateTarget`, `DomainSessionTemplateTarget` |

### Entities owned by global

| Package | READ relations | public | Existing Targets | Missing Targets |
|---|---|---|---|---|
| `domain` | Linked resource groups | n/a | `ResourceGroupDomainTarget` | None |
| `resource_group` | Linked domains, projects and users (through keypairs) | n/a (decision 7) | `DomainResourceGroupTarget`, `ProjectResourceGroupTarget`, `UserResourceGroupTarget` | None |
| `container_registry` | Linked projects | Relation (`is_global`) | None | `ProjectContainerRegistryTarget`, `PublicContainerRegistryTarget` |
| `resource_preset` | None (decision 2) | Decision 1 | None | Decisions 1, 2 |
| `idle_checker` | Domains, projects, resource groups and users linked by a binding, sessions | n/a | `IdleCheckerAssignmentTarget` (binding rows) | Decision 6 |
| `resource_policy` | None. The user and keypair policies are read through a column on the user row | n/a | `UserKeypairResourcePolicyTarget`, `UserResourcePolicyTarget` | Decision 4 |
| `runtime_variant` | None | Membership (decision 3) | None | `PublicRuntimeVariantTarget` |
| `runtime_variant_preset` | None | Membership (decision 3) | None | `PublicRuntimeVariantPresetTarget` |
| `prometheus_query_preset` | None | Membership (decision 3) | None | `PublicPrometheusQueryPresetTarget` |
| `prometheus_query_preset_category` | None | Membership (decision 3) | None | `PublicPrometheusQueryPresetCategoryTarget` |
| `resource_slot` (slot type) | None | Membership (decision 3) | None | `PublicResourceSlotTypeTarget` |
| `login_client_type` | None | Membership (decision 3) | None | `PublicLoginClientTypeTarget` |
| `deployment_revision_preset` | None | Membership (decision 3). Read through the global search only today, with no public wiring | None (a field Target only) | `PublicDeploymentPresetTarget` |
| `app_config_allow_list`, `app_config_definition` | None | n/a | None | None |
| `artifact`, `artifact_registries`, `huggingface_registry`, `reservoir_registry` | None | n/a | None | None |
| `object_storage`, `vfs_storage`, `storage_namespace` | None | n/a | None | None |
| `notification` (channel, rule) | None | n/a | None | None |
| `retention`, `client_ip_masking`, `service_catalog` | None | n/a | None | None |
| `rbac_models/role_preset` | None | n/a | None | None |

### Fields, by owning entity

| Package (row) | Owning entity | Existing Targets | Missing Targets |
|---|---|---|---|
| `kernel` | session | `SessionKernelTarget` | None |
| `session` (dependency) | session | None | No search. `SessionDependencyTarget` |
| `scheduling_history` (session) | session | `SessionSchedulingHistoryTarget` | None |
| `scheduling_history` (kernel) | session | `SessionKernelHistoryTarget`, `KernelKernelHistoryTarget` | None |
| `scheduling_history` (deployment) | deployment | `DeploymentHistoryTarget` | None |
| `scheduling_history` (route) | deployment | `RouteHistoryTarget` (`OperationScope`) | Decision 8 |
| `replica_group_history` | deployment | `DeploymentReplicaGroupHistoryTarget` | None |
| `deployment_revision` | deployment | `DeploymentRevisionTarget` | None |
| `endpoint` (access token) | deployment | `DeploymentAccessTokenTarget` | None |
| `routing` (replica) | deployment | `DeploymentReplicaTarget` | None |
| `replica_group` | deployment | None (read as `nested` on the deployment declaration) | None |
| `deployment_policy` | deployment | None | `DeploymentPolicyTarget` |
| `deployment_auto_scaling_policy` | deployment | None | No search |
| `keypair` | user | `UserKeypairTarget` | None |
| `login_session` (session, history) | user | `MyLoginSessionTarget`, `MyLoginHistoryTarget` | None |
| `error_log` | user | `UserErrorLogTarget` | None |
| `image` (alias) | image | None | No search. `ImageAliasTarget` |
| `model_card` (resource requirement) | model card | `ModelCardResourceRequirementTarget` | None |
| `vfolder` (user mount policy) | vfolder | None (read as `nested` on the vfolder declaration) | None |
| `artifact_revision` | artifact | `ArtifactRevisionTarget` | None |
| `deployment_revision_preset` (slot) | deployment preset | `DeploymentPresetSlotTarget` | None |
| `service_catalog` (endpoint) | service catalog | None | No search |
| `resource_slot` (agent resource) | agent | `AgentResourceTarget` | None |
| `resource_slot` (allocation) | session, through its kernel | None | No search |
| `resource_usage_history` (kernel usage record) | session, through its kernel | None | No search |
| `resource_usage_history` (usage bucket) | Decision 5 | `DomainUsageBucketTarget`, `ProjectUsageBucketTarget`, `UserUsageBucketTarget` (authorized against the resource group) | Decision 5 |
| `fair_share` | Decision 5 | `DomainFairShareTarget`, `ProjectFairShareTarget`, `UserFairShareTarget` (authorized against the resource group) | Decision 5 |
| `entity_label` | The entity the label is on | `EntityLabelTarget` | None |
| `audit_log` | The entity the record names. A record naming none is in global | `EntityAuditLogTarget`, `ScopeAuditLogTarget`, `TriggeredByAuditLogTarget` | None |
| `rbac_models/permission` | role | `RolePermissionTarget` | None |
| `rbac_models/role_permission_preset` | role preset | `RolePresetPermissionTarget` | None |

### Relation rows and the rest

| Package | What it is | Search |
|---|---|---|
| `association_container_registries_groups` | The relation between a project and a container registry | Read through the Targets of the two entities |
| `resource_group` (for-domain, for-project, for-keypair rows) | The relation between a scope and a resource group | Read through the Targets of the two entities |
| `idle_checker` (binding, session idle check) | The relations between a scope and an idle checker, and a session and an idle checker | `IdleCheckerAssignmentTarget` |
| `rbac_models/user_role` | The relation between a role and a user | `UserRoleAssignmentTarget`, `RoleRoleAssignmentTarget` |
| `association_artifacts_storages` | Rows linking an artifact and a storage. Not written as a graph relation | None |
| `agent_installed_image`, `event_log` | No creator | None |
| `global_entity`, `virtual_entity`, `rbac_models/entity_field` | Singleton rows and graph rows | Not searched |
| `alembic`, `hasher`, `minilang`, `mixins`, `rbac`, `specs` | Not entity packages | None |

### Reads wired through a public processor

Every read `services/*/processors.py` wires to a public processor. A public processor checks that the caller is logged in and checks no permission at the public singleton (`actions/registry/group.py`).

"Login only" marks a read that does not read entities registered in public.

#### Reads of entities registered in public

| Service | Wiring | Reads | Scope to move to | Why |
|---|---|---|---|---|
| `login_client_type` | `public_get`, `public_search` | All of `login_client_types` | public | The whole type is in public (decision 3) |
| `prometheus_query_preset` | `public_get_preset`, `public_search_presets` | All of `prometheus_query_presets` | public | Same |
| `prometheus_query_preset_category` | `public_get_category`, `public_bulk_get_categories`, `public_search_categories` | All of `prometheus_query_preset_categories` | public | Same |
| `resource_slot` | `public_get_resource_slot_type`, `public_search_resource_slot_types`, `public_lookup_resource_slot_type` | All of `resource_slot_types`; a name to its id | public | Same |
| `runtime_variant` | `public_get`, `public_bulk_get`, `public_search`, `public_lookup` | All of `runtime_variants`; a name to its id | public | Same |
| `runtime_variant_preset` | `public_get`, `public_search` | All of `runtime_variant_presets` | public | Same |
| `image` | `public_get_all_images`, `public_get_image_by_id`, `public_get_image_by_identifier`, `public_get_images_by_canonicals` | All of `images`. A status condition only; neither the registry's `is_global` nor ownership is looked at | public and the owning scopes (the `ImageTarget` list) | Images of registries not registered in public are read on login alone. Called by the legacy GQL and REST v1 |
| `resource_preset` | `list_presets`, `check_presets`, `lookup` | `resource_presets`. Without a resource group, the rows with `scaling_group_name IS NULL`; with one, those rows too. `list_presets` and `lookup` do not check permission on the resource group given | Decisions 1, 2 | The NULL rows are candidates for public, the bound rows for the resource group's scope |

#### Reads that belong to an owning scope

| Service | Wiring | Reads | Scope to move to | Why |
|---|---|---|---|---|
| `resource_group` | `get_wsproxy_version` | One `scaling_groups` row narrowed by the caller's domain, project and user Targets, and the AppProxy status | The owning scopes (the `ResourceGroupTarget` list) | The service already narrows by the same Targets. The check moves up to the processor |
| `domain` | `bulk_get` | The full `DomainData` by `domains` id (resource limits, allowed registries and dotfiles included) | Decision 9 | Opened as public because a regular user holds no READ on their domain. Other domains are read the same way |

#### Login only

| Service | Wiring | Reads | Scope to move to | Why |
|---|---|---|---|---|
| `agent` | `lookup`, `bulk_lookup` | A name in `agents` to its id | Not moved | Returns the id only. The get that follows checks permission for the value |
| `artifact_registry` | `lookup` | A name in `artifact_registries` to its id | Not moved | Same |
| `domain` | `lookup`, `bulk_lookup` | A name in `domains` to its id | Not moved | Same |
| `project` | `lookup` | A (domain name, name) pair in `groups` to its id | Not moved | Same |
| `resource_group` | `lookup`, `bulk_lookup` | A name in `scaling_groups` to its id | Not moved | Same |
| `session` | `lookup` | A (user, name, non-terminal status) in `sessions` to its id | Not moved | Same. The handler decides the user |
| `user` | `lookup` | An email in `users` to its id | Decision 10 | Returns the id only, but anyone logged in can confirm that an email is an account |
| `etcd_config` | `get_resource_slots`, `get_resource_metadata`, `get_vfolder_types` | etcd settings, device metadata in valkey | Not moved | Not an entity |
| `manager_admin` | `get_announcement` | The announcement in etcd | Not moved | Not an entity |
| `metric` | `metadata_public_search` | Container metric names in Prometheus | Not moved | Not an entity |
| `export` | `public_get_report` | Report definitions registered in code. The export query is authorized separately | Not moved | Not an entity |
| `permission_contoller` | `public_get_scope_types`, `public_get_entity_types`, `public_get_permission_matrix` | Code constants and the list of wired actions | Not moved | Not an entity |
| `auth` | `public_resolve_access_key_scope` | The user owning an access key, with their domain and role | Not moved | The service itself decides whether the caller may act for that user |
