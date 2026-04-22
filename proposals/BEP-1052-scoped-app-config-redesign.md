---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2026-04-21
Created-Version: 26.5.0
Target-Version:
Implemented-Version:
---

# BEP-1052: Scoped App Config Redesign

## Overview

A GraphQL / REST API schema proposal for the per-domain settings, global
settings, and per-user personal settings used by the WebUI.

A single scope (e.g. one domain, one user) can hold **multiple named
configuration documents** — for instance, a domain may publish
`theme.json`, `menu.json`, and `branding.json` independently. Each
document is identified by `(scope, scopeId, name)`.

## User Stories

- There are settings that only an admin can apply across an entire
  domain. Users cannot change them.
  - e.g. theme, hiding/showing various UI elements, additional menu
    links, reordering or hiding menus.
  - Values that can only be set at the domain level (the user cannot
    override them).
- Some domain settings must be readable without logging in.
  - e.g. theme.
- An admin can configure the initial values of a user's personal
  settings on a per-domain basis.
  - This matches how the existing App Config `extraConfig` field
    behaves today.
- Users want their personal settings persisted on the server so they
  stay with the account.
  - e.g. recently created sessions, language, whether experimental
    features are enabled, the visible columns and column order of
    tables.
- The same scope may need to publish multiple, independently-managed
  configuration documents (`theme.json`, `menu.json`, …) — they are
  loaded by different parts of the WebUI and version-managed
  separately.

Summary matrix:

| Story                                                | Scope    | Read              | Write       |
|------------------------------------------------------|----------|-------------------|-------------|
| Theme, Branding (must work before login)             | `global` | Anyone            | Admin       |
| UI hide/show, menu config                            | `domain` | Logged-in users   | Admin       |
| Domain-only internal management settings             | `domain` | Admin             | Admin       |
| Per-user preference defaults (per-domain)            | `domain` | Logged-in users   | Admin       |
| Per-user personal settings                           | `user`   | Owner/Admin       | Owner/Admin |

## Design Principles

- **Schema-less JSON**: the backend is purely a storage layer; the
  structure and meaning of the configuration are owned by the frontend.
- **Scope = Entity**: access control is expressed at the scope (entity)
  level, not the field level.
  `global_app_config` (Public read / Admin write), `domain_app_config`
  (Admin read & write), `user_app_config` (Owner/Admin read / Owner-self
  + Admin write).
- **Named documents within a scope**: each row is identified by the
  natural composite key `(scope_type, scope_id, name)`. A scope can hold
  any number of named documents; clients address them explicitly by name
  (no hierarchical fall-through lookup — see §6).
- **Write mutations split admin/user.** `admin_update_app_config` /
  `update_my_app_config` **replace** the stored JSON wholesale with
  the input — there is no partial update / deep-merge / key-level
  removal at the write boundary. Upsert semantics: the target row is
  created on first write if it does not yet exist. Identification uses
  the `(scope, scopeId, name)` natural key, never Relay `id`.
  Record-level removal is `*_delete_app_config` (soft-delete, see
  below).
- **Soft delete**: rows carry a `status` column
  (`ALIVE` / `DELETED`). Record-level delete flips `status = DELETED`
  rather than dropping the row, so audit / undo flows stay possible.
  Read APIs filter to `ALIVE` by default.
- **Single source-of-truth table**: a single `app_configs` table holds
  every scope; only the exposure layer is split.
- **Relay style**: Input/Payload conventions and the Node interface.

---

## 1. DB Layer — `app_configs` table

### Schema changes

Add `name` and `status` columns to `app_configs`. The natural-key
uniqueness constraint becomes `(scope_type, scope_id, name)`.

```python
class AppConfigScopeType(enum.StrEnum):
    GLOBAL = "global"
    DOMAIN = "domain"
    DOMAIN_USER_DEFAULTS = "domain_user_defaults"   # per-domain defaults applied to users in that domain
    PROJECT = "project"
    USER = "user"


class AppConfigStatus(enum.StrEnum):
    ALIVE = "alive"
    DELETED = "deleted"   # soft-deleted; preserved for audit / undo


@dataclass(frozen=True, slots=True)
class AppConfigKey:
    """
    Natural-key identifier for a single app_configs row.
    Used everywhere the trio `(scope_type, scope_id, name)` would
    otherwise appear together as parameters.
    """
    scope_type: AppConfigScopeType
    scope_id: str
    name: str


class AppConfigRow(Base):
    __tablename__ = "app_configs"

    id: Mapped[uuid.UUID]

    scope_type: Mapped[AppConfigScopeType] = mapped_column(
        StrEnumType(AppConfigScopeType, length=32), nullable=False, index=True
    )
    scope_id: Mapped[str]                     # global: literal "global"; otherwise domain_name / user_id
    name: Mapped[str]                         # NEW — config document name (e.g. "theme", "menu")

    extra_config: Mapped[dict[str, Any]]      # the only payload column; meaning per scope

    # NEW — soft-delete marker. Default ALIVE; record-delete sets DELETED.
    status: Mapped[AppConfigStatus] = mapped_column(
        StrEnumType(AppConfigStatus, length=16),
        nullable=False,
        default=AppConfigStatus.ALIVE,
        index=True,
    )

    created_at: Mapped[datetime]
    modified_at: Mapped[datetime]

    __table_args__ = (
        sa.UniqueConstraint(
            "scope_type", "scope_id", "name", name="uq_app_configs_scope_name"
        ),
    )
```

### Scope ID convention

| `scope_type`            | `scope_id` value          | Row count                   | Meaning of `extra_config`                                    |
|-------------------------|---------------------------|-----------------------------|--------------------------------------------------------------|
| `global`                | literal string `"global"` | one per `name`              | global-scope value of the document                            |
| `domain`                | `domain_name`             | one per `(domain, name)`    | the domain's own value of the document                        |
| `domain_user_defaults`  | `domain_name`             | one per `(domain, name)`    | merge base for users in that domain (per-document)            |
| `user`                  | `user_id` (UUID string)   | one per `(user_id, name)`   | user-customized value of the document                         |

`UniqueConstraint` on `(scope_type, scope_id, name)` guarantees a
single row per natural key. A scope can hold any number of distinct
`name`s.

### Status filtering

All read paths filter `status = ALIVE` by default. `DELETED` rows are
visible only to dedicated admin recovery / audit endpoints (out of
scope for this BEP). Re-creating a soft-deleted name via upsert flips
`status` back to `ALIVE` and overwrites the stored value with the
provided JSON.

---

## 2. Repository Layer — split per scope

Keep `models/app_config/row.py`'s `AppConfigRow` as a single class, but
**split the repository into three classes per scope**. Their access
policies and call patterns differ enough that combining them would make
method signatures unwieldy.

```
repositories/app_config/
├── db_source/
│   └── db_source.py         # single db_source
├── cache_source/
│   └── cache_source.py
├── global_app_config_repository.py
├── domain_app_config_repository.py
├── domain_user_defaults_app_config_repository.py
├── user_app_config_repository.py
└── repositories.py                    # exports all four repos
```

### Repository responsibility split

| Repository                              | Methods                                                                                                              |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| `GlobalAppConfigRepository`             | `get(name)`, `list()`, `upsert(name, extra_config)`, `soft_delete(name)`                                             |
| `DomainAppConfigRepository`             | `get(domain_name, name)`, `list(domain_name)`, `upsert(domain_name, name, extra_config)`, `soft_delete(domain_name, name)` |
| `DomainUserDefaultsAppConfigRepository` | `get(domain_name, name)`, `list(domain_name)`, `upsert(domain_name, name, extra_config)`, `soft_delete(domain_name, name)` |
| `UserAppConfigRepository`               | `get(user_id, name)`, `list(user_id)`, `upsert(user_id, name, extra_config)`, `soft_delete(user_id, name)`, `get_merged(user_id, name)`, `list_merged(user_id)` |

`DomainUserDefaultsAppConfigRepository` mirrors
`DomainAppConfigRepository` (admin-only, same call shape) but operates
on `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name)` rows.
Splitting it from `DomainAppConfigRepository` keeps each repository
mapped to exactly one scope, matching the rest of the layout.

All getters/listers filter `status = ALIVE`.

### `db_source` is a single module

The underlying table is the same, so the ORM query builder is managed
in one place.

```python
class AppConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get(self, key: AppConfigKey) -> AppConfigRow | None:
        async with self._db.begin_readonly_session() as db_sess:
            ...   # filters status = ALIVE

    async def list_in_scope(
        self, scope_type: AppConfigScopeType, scope_id: str
    ) -> list[AppConfigRow]:
        async with self._db.begin_readonly_session() as db_sess:
            ...   # filters status = ALIVE

    async def upsert(
        self,
        key: AppConfigKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigRow:
        # On natural-key conflict: replace the existing row's value
        # with `extra_config` and reset status = ALIVE (revives
        # soft-deleted records).
        async with self._db.begin_session() as db_sess:
            ...

    async def soft_delete(self, key: AppConfigKey) -> AppConfigRow | None:
        # Sets status = DELETED. No-op if the row doesn't exist or is already DELETED.
        async with self._db.begin_session() as db_sess:
            ...
```

`list_in_scope` keeps the two-arg form because it intentionally drops
the `name` part of the key (and therefore is not an `AppConfigKey`).

Permission checks and scope validation are performed in the service
layer.

---

## 3. GraphQL Schema — per-entity exposure

### Types

Each type carries `name` so callers can disambiguate between the
multiple named documents within a scope.

```graphql
"""Global config document. Readable without authentication."""
type GlobalAppConfig implements Node {
  id: ID!

  """Document name (unique within the global scope)."""
  name: String!

  """Stored config value."""
  config: JSON!

  createdAt: DateTime!
  modifiedAt: DateTime!
}

"""Domain config document. Admin read & write. The domain's own value."""
type DomainAppConfig implements Node {
  id: ID!

  """Owning domain (back-reference). Lookup only."""
  domain: Domain!

  """Document name (unique within this domain)."""
  name: String!

  """Stored config value for this document."""
  config: JSON!

  createdAt: DateTime!
  modifiedAt: DateTime!
}

"""User personal config document. Owner/Admin read; owner or admin can write.

`DOMAIN_USER_DEFAULTS` rows are not exposed as their own Node type —
their value enters this graph through `domainDefaultConfig` below
(plus the merged `mergedConfig`). Admin-side direct manipulation of
`DOMAIN_USER_DEFAULTS` rows still goes through `adminAppConfigs` /
`adminUpdateAppConfig` / `node(id)` returning the generic `AppConfig`.
"""
type UserAppConfig implements Node {
  id: ID!

  """Owning user (back-reference)."""
  user: User!

  """Document name (unique within this user)."""
  name: String!

  """Raw value the user customized (pre-merge)."""
  userCustomizedConfig: JSON!

  """
  Raw value of the matching same-`name`
  `(scope=DOMAIN_USER_DEFAULTS, scopeId=user.domain_name)` row's
  `extra_config`. `null` when no such defaults row exists. Lets the
  WebUI distinguish "what the domain provides" from "what the user
  changed".
  """
  domainDefaultConfig: JSON

  """
  Effective applied value: deep merge of `domainDefaultConfig` ⊕
  `userCustomizedConfig`. Clients render the UI from this value.
  """
  mergedConfig: JSON!

  createdAt: DateTime!
  modifiedAt: DateTime!
}
```

### Added/extended fields (Relationship)

| Location   | Field                                                                                  |
|------------|----------------------------------------------------------------------------------------|
| `Domain`   | `appConfigs(filter, orderBy, ...pagination): DomainAppConfigConnection!`               |
| `UserNode` | `appConfigs(filter, orderBy, ...pagination): UserAppConfigConnection!`                 |

### Permissions

Each `appConfigs` child field inherits the parent resolver's
permission policy — see the permission matrix below for the resulting
access rules.

```graphql
extend type Domain {
  """
  App config documents owned by this domain (DOMAIN scope rows).
  Admin only. Filter by `name` (or any combination) to retrieve a
  single document. `filter.scope` / `filter.scopeId` are ignored —
  already pinned to this domain.
  """
  appConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): DomainAppConfigConnection!
}

extend type UserNode {
  """
  App config documents owned by this user. Owner or admin only.
  Filter by `name` to retrieve a single document. `filter.scope` /
  `filter.scopeId` are ignored — already pinned to this user.
  """
  appConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): UserAppConfigConnection!
}
```

A self-fetch shortcut root field `myAppConfigs` (Connection) is
provided so callers can pull their own documents directly without
going through `user_node(id)`.

### Queries

```graphql
type Query {
  """
  Global config documents (no auth). Filter by `name` to retrieve a
  single document.
  """
  globalAppConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): GlobalAppConfigConnection!

  """
  Current user's app config documents (auth required). Filter by
  `name` to retrieve a single document.
  """
  myAppConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): UserAppConfigConnection!

  """
  Cross-scope AppConfig search (Admin only). Returns a Relay
  Connection with filter / order / pagination applied.
  """
  adminAppConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigConnection!

  # ─ The following are not new additions; existing root fields are reused ─
  #
  # user_node(id: String!): UserNode
  #                                — admin → user_node(id: ...) { appConfigs { ... } }
  # domain(name: String!): Domain  — admin → domain(name: ...) { appConfigs { ... } }
  # node(id: ID!): Node            — Relay standard, direct access by global ID
}
```

#### Connection / Filter / OrderBy

Filter and orderBy types are unified — a single `AppConfigFilterGQL`
and `AppConfigOrderByGQL` are reused across all Connections (admin
cross-scope and per-scope typed). Connection types themselves remain
typed per scope so the `node` payload carries the right concrete type.

```graphql
# ── Connections (typed per scope) ─────────────────────────────

"""Relay Connection holding AppConfig rows from any scope."""
type AppConfigConnection {
  edges: [AppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type AppConfigEdge {
  cursor: String!
  node: AppConfig!
}

type GlobalAppConfigConnection {
  edges: [GlobalAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type GlobalAppConfigEdge {
  cursor: String!
  node: GlobalAppConfig!
}

type DomainAppConfigConnection {
  edges: [DomainAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type DomainAppConfigEdge {
  cursor: String!
  node: DomainAppConfig!
}

type UserAppConfigConnection {
  edges: [UserAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type UserAppConfigEdge {
  cursor: String!
  node: UserAppConfig!
}

# ── Filter / OrderBy (shared by all Connections) ──────────────

"""
AppConfig search filter. Scalar fields at the top level are
AND-combined. For arbitrary boolean shapes, nest predicates under
`AND` / `OR` / `NOT`.
"""
input AppConfigFilterGQL {
  """
  Filter by scope type. Meaningful only on `adminAppConfigs`; on
  per-scope Connections (`globalAppConfigs`, `Domain.appConfigs`,
  `UserNode.appConfigs`, `myAppConfigs`) the scope
  is already pinned by the field, so this filter is ignored.
  """
  scope: AppConfigScopeEnumFilter = null

  """
  Exact match on `scope_id`. Same constraint as `scope` above —
  ignored on per-scope Connections where `scope_id` is implied.
  """
  scopeId: StringFilter = null

  """Filter on document `name`."""
  name: StringFilter = null

  """`created_at` range filter."""
  createdAt: DateTimeFilter = null

  """`modified_at` range filter."""
  modifiedAt: DateTimeFilter = null

  """All sub-filters must match (AND combination)."""
  AND: [AppConfigFilterGQL!] = null

  """At least one sub-filter must match (OR combination)."""
  OR: [AppConfigFilterGQL!] = null

  """None of the sub-filters may match (NOT combination)."""
  NOT: [AppConfigFilterGQL!] = null
}

"""EnumFilter for AppConfigScopeGQL (equals / in / not_equals / not_in)."""
input AppConfigScopeEnumFilter {
  equals: AppConfigScopeGQL
  in: [AppConfigScopeGQL!]
  notEquals: AppConfigScopeGQL
  notIn: [AppConfigScopeGQL!]
}

input AppConfigOrderByGQL {
  field: AppConfigOrderField!
  direction: OrderDirection! = ASC
}

"""
`SCOPE` / `SCOPE_ID` are only useful on `adminAppConfigs`; on
per-scope Connections they degenerate to a constant and have no
effect.
"""
enum AppConfigOrderField {
  SCOPE
  SCOPE_ID
  NAME
  MODIFIED_AT
  CREATED_AT
}
```

All Connections filter to `status = ALIVE` by default. (A separate
admin endpoint can expose `DELETED` rows for recovery if needed; out
of scope for this BEP.)

### Mutations

Write mutations come in two flavors that match the access model. Each
flavor exposes two operations:

- **update** — replace the named document's stored JSON wholesale
  with the input (upsert: creates the row on first write, revives it
  if soft-deleted).
- **delete** — soft-delete the entire document (`status = DELETED`).

Admin mutations identify rows by the **`AppConfigKey` input type**
that bundles `(scope, scopeId, name)`. Self mutations only take
`name` — the server fixes `scope = USER` and
`scopeId = current_user.user_id`.

```graphql
type Mutation {
  """
  App config write (Admin only). Identifies a row of any scope by
  `AppConfigKey { scope, scopeId, name }` and replaces its stored
  JSON with the input. Creates the row if it does not exist (upsert);
  revives the row to `status = ALIVE` if it was previously
  soft-deleted.
  """
  adminUpdateAppConfig(input: AdminUpdateAppConfigInput!): UpdateAppConfigPayload!

  """
  Soft-delete an entire app config document (Admin only). Sets
  `status = DELETED`; the row remains for audit. Silent no-op if
  already deleted or non-existent. Use `adminUpdateAppConfig` to
  revive.
  """
  adminDeleteAppConfig(input: AdminDeleteAppConfigInput!): DeleteAppConfigPayload!

  """Self user_app_config write for the named document. Target is the caller."""
  updateMyAppConfig(input: UpdateMyAppConfigInput!): UpdateMyAppConfigPayload!

  """Soft-delete the caller's named document."""
  deleteMyAppConfig(input: DeleteMyAppConfigInput!): DeleteMyAppConfigPayload!
}

enum AppConfigScopeGQL {
  GLOBAL
  DOMAIN
  DOMAIN_USER_DEFAULTS
  USER
}

enum AppConfigStatusGQL {
  ALIVE
  DELETED
}

# ── Composite key shared by admin mutations ──────────────────

"""
Natural composite key identifying a single app config row.
Mirrors the Python `AppConfigKey` dataclass used by the repository /
db_source layer.
- GLOBAL: `scopeId` must be the literal string `"global"`.
- DOMAIN: `scopeId` is `domain_name`.
- USER:   `scopeId` is `user_id` (UUID string).
- `name` is the document name (unique within the scope).
"""
input AppConfigKey {
  scope: AppConfigScopeGQL!
  scopeId: String!
  name: String!
}

# ── Admin input ───────────────────────────────────────────────

input AdminUpdateAppConfigInput {
  """Target row identifier."""
  key: AppConfigKey!

  """
  New stored value — replaces the row's content wholesale. Pass `{}`
  to clear the document while keeping the row.
  - GLOBAL / DOMAIN / DOMAIN_USER_DEFAULTS scope: replaces the
    document's `config` field directly.
  - USER scope: replaces that user's `userCustomizedConfig`
    (the merged `config` is read-only computed and cannot be written
    directly).
  """
  config: JSON!
}

input AdminDeleteAppConfigInput {
  """Target row identifier."""
  key: AppConfigKey!
}

# ── My (self) input ──────────────────────────────────────────

input UpdateMyAppConfigInput {
  """
  Document name. The server fixes `scope = USER` and
  `scopeId = current_user.user_id`; there is no input field that can
  target another user.
  """
  name: String!

  """
  New stored value — replaces the caller's `userCustomizedConfig`
  for the named document wholesale. Pass `{}` to clear it.
  """
  userCustomizedConfig: JSON!
}

input DeleteMyAppConfigInput {
  """Document name (server-fixed scope as above). Soft-deletes the document."""
  name: String!
}

# ── Payload ──────────────────────────────────────────────────

"""Result of `adminUpdateAppConfig`."""
type UpdateAppConfigPayload {
  appConfig: AppConfig!
}

"""
Result of `adminDeleteAppConfig`. The returned row reflects the post
soft-delete state (`status = DELETED`).
"""
type DeleteAppConfigPayload {
  appConfig: AppConfig!
}

"""Result of `updateMyAppConfig` (includes `mergedConfig`)."""
type UpdateMyAppConfigPayload {
  appConfig: UserAppConfig!
}

"""Result of `deleteMyAppConfig` (post soft-delete state)."""
type DeleteMyAppConfigPayload {
  appConfig: UserAppConfig!
}

"""Generic AppConfig type used in the admin mutation payload — exposes the raw stored value."""
type AppConfig implements Node {
  id: ID!
  scope: AppConfigScopeGQL!
  scopeId: String!
  name: String!
  status: AppConfigStatusGQL!

  """
  Raw stored value (`extra_config`). For USER scope this is the
  user-customized value, not the merged result.
  """
  config: JSON!

  createdAt: DateTime!
  modifiedAt: DateTime!
}
```

### Permission matrix

| Operation                            | Anonymous | User       | Admin |
|--------------------------------------|-----------|------------|-------|
| `globalAppConfigs`                   | ✅        | ✅         | ✅    |
| `myAppConfigs`                       | ❌        | ✅ (self)  | ✅    |
| `Domain.appConfigs`                  | ❌        | ❌         | ✅    |
| `UserNode.appConfigs`                | ❌        | ✅ (self)  | ✅    |
| `adminAppConfigs`                    | ❌        | ❌         | ✅    |
| `adminUpdateAppConfig`               | ❌        | ❌         | ✅    |
| `adminDeleteAppConfig`               | ❌        | ❌         | ✅    |
| `updateMyAppConfig`                  | ❌        | ✅ (self)  | ✅    |
| `deleteMyAppConfig`                  | ❌        | ✅ (self)  | ✅    |

Where the checks live:
- `admin*` mutation resolver: `check_admin_only()` at entry.
- `*My*` mutation resolver: `current_user()` for auth, then the
  server hard-fixes `scope = USER` and `scope_id =
  current_user.user_id` — there is literally no input field that can
  target another user.
- `Domain.appConfigs` field resolver: `check_admin_only()`; returns
  an empty Connection for non-admin callers.
- `UserNode.appConfigs` field resolver: returns an empty Connection
  when the parent node's `user_id` differs from `current_user` and the
  caller is not an admin.

---

## 4. REST Schema — `/app_config/{scope_type}/{scope_id}/{name}`

Scope and document name are expressed as URL path segments, consistent
with the v2 routing convention.

### Endpoints

REST splits along the same Admin/User axis as GraphQL. Admin handles
arbitrary scopes via `/v2/app_config/{scope_type}/{scope_id}/{name}`;
users have a self-service path `/v2/app_config/user/me/{name}`.

| Method | Path                                                       | Access     | Description                                          |
|--------|------------------------------------------------------------|------------|------------------------------------------------------|
| GET    | `/v2/app_config/global`                                    | Anonymous  | List all global documents                            |
| GET    | `/v2/app_config/global/{name}`                             | Anonymous  | Read a single global document                        |
| GET    | `/v2/app_config/domain/{domain_name}`                      | Admin      | List all documents of a domain                       |
| GET    | `/v2/app_config/domain/{domain_name}/{name}`               | Admin      | Read one domain document                             |
| GET    | `/v2/app_config/user/{user_id}`                            | Admin      | List all documents of a user                         |
| GET    | `/v2/app_config/user/{user_id}/{name}`                     | Admin      | Read one user document                               |
| POST   | `/v2/app_config/admin/search`                              | Admin      | Cross-scope search (filter / order / paginate)       |
| PUT    | `/v2/app_config/{scope_type}/{scope_id}/{name}`            | Admin      | Replace one document (upsert)                        |
| DELETE | `/v2/app_config/{scope_type}/{scope_id}/{name}`            | Admin      | Soft-delete one document                             |
| GET    | `/v2/app_config/user/me`                                   | User       | List all own documents (each with merged result)     |
| GET    | `/v2/app_config/user/me/{name}`                            | User       | Read one own document (with merged result)           |
| PUT    | `/v2/app_config/user/me/{name}`                            | User       | Replace one own document                             |
| DELETE | `/v2/app_config/user/me/{name}`                            | User       | Soft-delete one own document                         |

`POST /v2/app_config/admin/search` accepts the same input schema as
the GQL `adminAppConfigs` field (`filter` / `orderBy` / pagination
arguments) in the request body and returns the same result.

> `/v2/app_config/user/me/...` follows the `my_` self-service
> convention — the adapter resolves `current_user()` internally and
> fixes `scope_id` to the caller's `user_id`. The body for PUT
> accepts only `userCustomizedConfig` (snake-case
> `user_customized_config` in REST); there is no input field that can
> target another user.

> Read endpoints filter to `status = ALIVE` by default. PUT on a
> soft-deleted document revives it (`status = ALIVE`) and overwrites
> the stored value with the provided JSON.

---

## 5. `user_app_config` semantics — Merge policy

### Storage

- `user_app_config.extra_config` (the DB column, exposed as
  `userCustomizedConfig` in GQL) stores **only the values the user has
  explicitly set** — for the named document.
- Domain-provided defaults live in their own scope:
  `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name,
  name=N)`'s `extra_config`. They are *not* copied into user rows —
  to avoid having to rewrite every user row whenever the domain admin
  changes a default.
- Defaults are applied **per-name**: a `DOMAIN_USER_DEFAULTS` row's
  `extra_config` is the merge base for the same-`name` `USER` row's
  `userCustomizedConfig`. Different `name`s are independent.

### Read (Merge)

The merge — for a given `(user_id, name)` — proceeds as follows in a
single transaction:

1. Look up the `domain_name` for `user_id` from `users`.
2. Read the
   `(scope_type=domain_user_defaults, scope_id=domain_name, name=name)`
   row to get its `extra_config` (the user-defaults).
3. Read the `(scope_type=user, scope_id=user_id, name=name)` row to
   get `extra_config` (= `userCustomizedConfig`).
4. **Deep merge**: nested objects are merged recursively per key; at
   leaf keys, the user value wins over the domain default. Lists are
   treated as leaves and replaced wholesale by the user value
   (element-level merge of arrays has no unambiguous semantics). The
   result is exposed as `UserAppConfig.mergedConfig`; the raw
   defaults row's `extra_config` is exposed as
   `UserAppConfig.domainDefaultConfig`.

A list variant returns one merged result per `name` for which either
a domain row or a user row exists.

> **Note**: the Python sketch below is illustrative only — it shows
> the data flow / SQL shape. Method names, signatures, and class
> placement are *not* part of this BEP's contract and may differ in
> the actual implementation.

```python
class AppConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_merged(self, user_id: str, name: str) -> MergedAppConfig:
        async with self._db.begin_readonly_session() as db_sess:
            user_row_meta = (await db_sess.execute(
                sa.select(UserRow.domain_name).where(UserRow.uuid == user_id)
            )).one_or_none()
            if not user_row_meta:
                raise UserNotFound(f"User {user_id} not found")
            domain_name = user_row_meta.domain_name

            rows = (await db_sess.execute(
                sa.select(AppConfigRow).where(
                    AppConfigRow.status == AppConfigStatus.ALIVE,
                    AppConfigRow.name == name,
                    sa.or_(
                        sa.and_(
                            AppConfigRow.scope_type == AppConfigScopeType.DOMAIN_USER_DEFAULTS,
                            AppConfigRow.scope_id == domain_name,
                        ),
                        sa.and_(
                            AppConfigRow.scope_type == AppConfigScopeType.USER,
                            AppConfigRow.scope_id == user_id,
                        ),
                    )
                )
            )).scalars().all()

        defaults_row = next(
            (r for r in rows if r.scope_type == AppConfigScopeType.DOMAIN_USER_DEFAULTS), None
        )
        user_row = next((r for r in rows if r.scope_type == AppConfigScopeType.USER), None)

        domain_defaults = defaults_row.extra_config if defaults_row else {}
        user_customized = user_row.extra_config if user_row else {}
        return MergedAppConfig(
            domain_name=domain_name,
            user_id=user_id,
            name=name,
            user_customized_config=user_customized,
            domain_default_config=domain_defaults,                # GQL: UserAppConfig.domainDefaultConfig
            merged_config=deep_merge(domain_defaults, user_customized),  # GQL: UserAppConfig.mergedConfig
        )


class UserAppConfigRepository:
    _db_source: AppConfigDBSource

    def __init__(self, db_source: AppConfigDBSource) -> None:
        self._db_source = db_source

    async def get_merged(self, user_id: str, name: str) -> MergedAppConfig:
        return await self._db_source.get_merged(user_id, name)
```

### Exposure

`UserAppConfig` exposes three views of the same logical document so
the WebUI can render and edit cleanly:

- `userCustomizedConfig` — what the user explicitly set (raw)
- `domainDefaultConfig` — the matching `DOMAIN_USER_DEFAULTS` row's
  raw `extra_config` (what the domain provides as the default; `null`
  if no defaults row exists)
- `mergedConfig` — `domainDefaultConfig` ⊕ `userCustomizedConfig`,
  what the UI actually applies

The REST `GET /v2/app_config/user/me/{name}` response carries the
same three views (snake_case in REST: `user_customized_config`,
`domain_default_config`, `merged_config`).

---

## 6. Client Integration — WebUI bootstrap

The WebUI requests configs by addressing them explicitly with
`(scope, scopeId, name)`. There is no server-side hierarchical
fall-through — clients know which scope they are asking about.

### `webserver.conf` — bootstrap document list

The web server is configured with the list of **global** documents the
WebUI must load before the login screen renders. Domain / user
documents are addressed by the WebUI at runtime once the auth context
is known.

```toml
[app_config]
# Global documents fetched anonymously before login.
# Each entry is a name fetched from /v2/app_config/global/{name}.
bootstrap_global = ["theme", "branding"]
```

### Bootstrap flow

1. **Pre-login (anonymous)** — for each `name` in
   `bootstrap_global`, the WebUI calls
   `GET /v2/app_config/global/{name}` (no auth). On 404 or network
   error, the WebUI falls back to its built-in defaults for that
   document.

2. **Post-login** — the WebUI calls
   `GET /v2/app_config/user/me` to fetch *all* of the caller's user
   documents in one round trip. Each entry includes the merged
   `config` (per-`name` merge with the matching
   `DOMAIN_USER_DEFAULTS` row).

3. **Domain-scoped reads** (admin UI) — the WebUI calls
   `GET /v2/app_config/domain/{domain_name}` /
   `GET /v2/app_config/domain/{domain_name}/{name}` directly with
   admin credentials.

---

## 7. User Scenarios — end-to-end caller flows

Each scenario describes *who* calls *when* and *what they want to
achieve*, paired with the actual call spec. Intended as a reference
for client-side implementation.

### S1. Pre-login global config loading (anonymous)

The WebUI fetches the global `theme` document before rendering the
login screen. (The JSON shape inside `config` is owned by the
frontend; backend stores it opaquely.)

```graphql
query LoadGlobalTheme {
  globalAppConfigs(filter: { name: { equals: "theme" } }, first: 1) {
    edges { node { name config modifiedAt } }
  }
}
```

- No auth token.
- Single-document retrieval is just a Connection query with a `name`
  filter — there is no singular root field.
- On failure (no edge returned, network error) the WebUI falls back
  to its built-in defaults. The list of bootstrap documents is in
  `webserver.conf` (§6).

### S2. Bootstrapping right after login

Right after a successful login, the WebUI fetches everything it needs
to initialize the UI state for this user in a single round trip — all
of the caller's named documents at once.

```graphql
query BootstrapMe {
  myAppConfigs {
    edges {
      node {
        name
        userCustomizedConfig
        domainDefaultConfig
        mergedConfig
        modifiedAt
      }
    }
  }
  globalAppConfigs {
    edges { node { name config } }
  }
}
```

- Server: `myAppConfigs` resolver identifies the caller via
  `current_user()`, lists all `(scope=USER, scope_id=current_user)`
  rows that are `ALIVE`, and for each row deep-merges the same-`name`
  `DOMAIN_USER_DEFAULTS` row's `extra_config` into
  `userCustomizedConfig`, exposing the result as `mergedConfig`.
  `domainDefaultConfig` exposes that defaults row's raw value
  separately.
- The WebUI initializes UI state from `mergedConfig` per document, and
  keeps `userCustomizedConfig` and `domainDefaultConfig` around
  separately so the Settings page can show "what the user explicitly
  changed" against "what the domain provides".

### S3. The user saves their own document

The user replaces their `theme` document.

```graphql
mutation SaveMyTheme($input: UpdateMyAppConfigInput!) {
  updateMyAppConfig(input: $input) {
    appConfig {
      name
      userCustomizedConfig
      domainDefaultConfig
      mergedConfig
      modifiedAt
    }
  }
}
```

```json
{
  "input": {
    "name": "theme",
    "userCustomizedConfig": {
      "sectionA": { "optionX": "value-1" },
      "sectionB": "value-2"
    }
  }
}
```

- Server fixes `scope = USER`, `scope_id = current_user.user_id`.
  Only `name` is taken from the input.
- **Replace** semantics: the document's `userCustomizedConfig` is set
  to the input as-is. Anything the caller wants to keep must be sent
  in the same payload — there is no partial-merge or per-key patch.
- **Upsert**: if the user has never written `theme` before, the row
  is created with this value (and `status = ALIVE`).
- `appConfig.mergedConfig` in the response already reflects the
  re-computed read-merge of the new `userCustomizedConfig` with the
  same-`name` `DOMAIN_USER_DEFAULTS` row.

### S4. Admin writes a domain's document and the user-defaults document

The domain's own value and the per-user defaults are two separate
rows in two scopes — written via two `adminUpdateAppConfig` calls
(or one batched mutation client-side). Single-step per row,
identified by `AppConfigKey`:

```graphql
mutation UpdateDomainTheme($input: AdminUpdateAppConfigInput!) {
  adminUpdateAppConfig(input: $input) {
    appConfig { id scope scopeId name status config modifiedAt }
  }
}
```

Step A — replace the domain's own `theme`:

```json
{
  "input": {
    "key": { "scope": "DOMAIN", "scopeId": "default", "name": "theme" },
    "config": { "sectionA": { "optionX": "new-value" } }
  }
}
```

Step B — replace the user-defaults `theme` for the same domain:

```json
{
  "input": {
    "key": { "scope": "DOMAIN_USER_DEFAULTS", "scopeId": "default", "name": "theme" },
    "config": { "sectionB": "default-value" }
  }
}
```

- Server: `check_admin_only()` → locates each row by its full key →
  replaces that row's `extra_config` with the input wholesale.
- **Upsert**: if the document doesn't exist yet, the row is created
  with this value.
- **Revive**: if the row was previously soft-deleted, `status` flips
  back to `ALIVE`.
- Effect of Step B: on the next `myAppConfigs` call, every user in
  that domain receives the updated `theme` defaults merged with their
  own `theme` `userCustomizedConfig`. Step A only affects readers of
  `Domain.appConfigs` (the admin view of the domain's own value).

### S5. Admin writes a specific user's document on their behalf

For a support request, an admin overwrites user A's `preferences`
`userCustomizedConfig`:

```graphql
mutation OverrideUserPrefs($input: AdminUpdateAppConfigInput!) {
  adminUpdateAppConfig(input: $input) {
    appConfig { id scope scopeId name config modifiedAt }
  }
}
```

```json
{
  "input": {
    "key": {
      "scope": "USER",
      "scopeId": "00000000-0000-0000-0000-000000000123",
      "name": "preferences"
    },
    "config": { "sectionA": { "flag": true } }
  }
}
```

- For the USER scope, the `config` input replaces that user's
  `userCustomizedConfig` for the `preferences` document wholesale
  (the merged `config` is read-only computed).
- **Upsert**: creates the row if user A has never saved `preferences`
  before.
- The next time that user calls `myAppConfigs`, the new
  `preferences` `userCustomizedConfig` is merged with the matching
  domain defaults in the response.

### S6. Admin lists every document of a single user

Operational case — "what's stored in user A's app configs?". Use the
typed parent-node child Connection on `UserNode`:

```graphql
query ListUserConfigs($userId: String!) {
  user_node(id: $userId) {
    appConfigs(first: 50) {
      edges {
        cursor
        node { id name userCustomizedConfig domainDefaultConfig mergedConfig modifiedAt }
      }
      pageInfo { hasNextPage endCursor }
      count
    }
  }
}
```

- `user_node` resolver enforces "owner or admin". Admin reaches any
  user, so this works for the operational use case. Each
  `node.mergedConfig` is the per-`name` merged value;
  `node.userCustomizedConfig` / `node.domainDefaultConfig` show the
  raw inputs to the merge.
- For cross-user audits use `adminAppConfigs(filter: { scope: { equals: USER }, ... })`
  in S7 instead.

### S7. Admin audits all AppConfigs (cross-scope search)

Cases such as "list every user document modified in the last week" or
"every domain that customized the `menu` document":

```graphql
query AuditConfigs(
  $filter: AppConfigFilterGQL!
  $orderBy: [AppConfigOrderByGQL!]
  $first: Int
  $after: String
) {
  adminAppConfigs(filter: $filter, orderBy: $orderBy, first: $first, after: $after) {
    edges {
      cursor
      node { id scope scopeId name status config modifiedAt }
    }
    pageInfo { hasNextPage endCursor }
    count
  }
}
```

```json
{
  "filter": {
    "scope": { "equals": "USER" },
    "name": { "equals": "preferences" },
    "modifiedAt": { "gte": "2026-04-14T00:00:00Z" }
  },
  "orderBy": [{ "field": "MODIFIED_AT", "direction": "DESC" }],
  "first": 50
}
```

- Server: `check_admin_only()` → Connection search. In cursor mode
  the sort order is pinned to the cursor key. By default returns
  `ALIVE` rows only.

### S8. Operator removes an entire document (soft-delete)

Removing a stale or deprecated document — e.g. retiring an old
`legacy_menu` document for a domain:

```graphql
mutation RemoveDomainLegacyMenu($input: AdminDeleteAppConfigInput!) {
  adminDeleteAppConfig(input: $input) {
    appConfig { id scope scopeId name status modifiedAt }
  }
}
```

```json
{
  "input": {
    "key": { "scope": "DOMAIN", "scopeId": "default", "name": "legacy_menu" }
  }
}
```

- Server: `check_admin_only()` → flips `status = DELETED` on the
  matching row. Subsequent reads (`Domain.appConfigs`,
  `UserNode.appConfigs`, `adminAppConfigs`, etc.) hide the document.
- **Idempotent**: no-op when the row is absent or already `DELETED`.
- **Recoverable**: `adminUpdateAppConfig` on the same key revives the
  row to `ALIVE`, overwriting the stored value with the provided JSON.

The self-service equivalent is `deleteMyAppConfig`, which only takes
a `name` and soft-deletes that document of the caller.
