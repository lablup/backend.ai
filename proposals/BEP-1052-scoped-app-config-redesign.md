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

A GraphQL / REST API schema proposal for the per-domain settings,
public (pre-login) settings, and per-user personal settings used by
the WebUI.

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
| Theme, Branding (must work before login)             | `public` | Anyone            | Admin       |
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
- **Writes split into create / update / delete / restore.**
  `createAppConfig` strictly inserts a new row (errors if any row
  already exists for the key, even a soft-deleted one);
  `updateAppConfig` replaces an existing `ALIVE` row's stored JSON
  wholesale; `deleteAppConfig` soft-deletes (`ALIVE → DELETED`);
  `restoreAppConfig` is the explicit inverse of delete
  (`DELETED → ALIVE`, value unchanged). Neither `create` nor
  `update` does partial update / deep-merge / key-level removal at
  the write boundary. There is no upsert. Identification uses the
  `(scope, scopeId, name)` natural key, never Relay `id`.
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
    PUBLIC = "public"
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
    scope_id: Mapped[str]                     # public: literal "public"; otherwise domain_name / user_id
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
| `public`                | literal string `"public"` | one per `name`              | public (pre-login) value of the document                      |
| `domain`                | `domain_name`             | one per `(domain, name)`    | the domain's own value of the document                        |
| `domain_user_defaults`  | `domain_name`             | one per `(domain, name)`    | merge base for users in that domain (per-document)            |
| `user`                  | `user_id` (UUID string)   | one per `(user_id, name)`   | user-customized value of the document                         |

`UniqueConstraint` on `(scope_type, scope_id, name)` guarantees a
single row per natural key. A scope can hold any number of distinct
`name`s.

### Status filtering

All read paths filter `status = ALIVE` by default. `DELETED` rows are
visible only to dedicated admin recovery / audit endpoints (out of
scope for this BEP). Revival uses the dedicated `restoreAppConfig`
mutation, which flips `status = DELETED → ALIVE` while preserving
the stored value; `createAppConfig` errors on any pre-existing row
(ALIVE or DELETED), and `updateAppConfig` errors on a `DELETED` row.

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
| `PublicAppConfigRepository`             | `get(name)`, `list()`, `create(name, extra_config)`, `update(name, extra_config)`, `soft_delete(name)`, `restore(name)`                                             |
| `DomainAppConfigRepository`             | `get(domain_name, name)`, `list(domain_name)`, `create(domain_name, name, extra_config)`, `update(domain_name, name, extra_config)`, `soft_delete(domain_name, name)`, `restore(domain_name, name)` |
| `DomainUserDefaultsAppConfigRepository` | `get(domain_name, name)`, `list(domain_name)`, `create(domain_name, name, extra_config)`, `update(domain_name, name, extra_config)`, `soft_delete(domain_name, name)`, `restore(domain_name, name)` |
| `UserAppConfigRepository`               | `get(user_id, name)`, `list(user_id)`, `create(user_id, name, extra_config)`, `update(user_id, name, extra_config)`, `soft_delete(user_id, name)`, `restore(user_id, name)`, `get_merged(user_id, name)`, `list_merged(user_id)` |

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

    async def create(
        self,
        key: AppConfigKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigRow:
        # Strict insert. Errors if any row already exists for the
        # natural key, regardless of status (to revive a DELETED row,
        # use `restore` instead).
        async with self._db.begin_session() as db_sess:
            ...

    async def update(
        self,
        key: AppConfigKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigRow:
        # Replace the existing ALIVE row's value with `extra_config`.
        # Errors if no ALIVE row exists for the natural key (missing
        # or DELETED).
        async with self._db.begin_session() as db_sess:
            ...

    async def soft_delete(self, key: AppConfigKey) -> AppConfigRow | None:
        # Sets status = DELETED. No-op if the row doesn't exist or is already DELETED.
        async with self._db.begin_session() as db_sess:
            ...

    async def restore(self, key: AppConfigKey) -> AppConfigRow:
        # Sets status = ALIVE, value unchanged. Errors if no row
        # exists or the row is already ALIVE.
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
"""Public config document. Readable without authentication."""
type PublicAppConfig implements Node {
  id: ID!

  """Document name (unique within the public scope)."""
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

`DOMAIN` and `DOMAIN_USER_DEFAULTS` rows are not exposed as their
own Node type — their values enter this graph through
`domainConfig` / `domainDefaultConfig` below (plus the merged
`mergedConfig`). Admin-side direct manipulation goes through the
unified `createAppConfig` / `updateAppConfig` / `deleteAppConfig`
mutations with the appropriate `key.scope`; read-side access is via
`adminAppConfigs` or `node(id)` returning the generic `AppConfig`.
`Domain.appConfigs` is not exposed to non-admins — domain values
reach the user only via this merge.
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
  `extra_config`. `null` when no such defaults row exists.
  """
  domainDefaultConfig: JSON

  """
  Raw value of the matching same-`name`
  `(scope=DOMAIN, scopeId=user.domain_name)` row's `extra_config` —
  the domain's own public value that applies to every user in the
  domain. `null` when no such row exists. Lets the WebUI separate
  "the domain-wide rule", "the domain's per-user default", and
  "what the user changed" for settings UIs.
  """
  domainConfig: JSON

  """
  Effective applied value: deep merge of `domainConfig` ⊕
  `domainDefaultConfig` ⊕ `userCustomizedConfig` (left = lowest
  priority, right = highest). Clients render the UI from this
  value.
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
  Public config documents (no auth). Filter by `name` to retrieve a
  single document.
  """
  publicAppConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): PublicAppConfigConnection!

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

type PublicAppConfigConnection {
  edges: [PublicAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type PublicAppConfigEdge {
  cursor: String!
  node: PublicAppConfig!
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
  per-scope Connections (`publicAppConfigs`, `Domain.appConfigs`,
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

Writes are expressed as four separate mutations — **create**,
**update**, **delete**, **restore** — so that each has an
unambiguous precondition (no upsert magic; revival is explicit).
Each accepts an `AppConfigKey` and covers every scope (admin writes
in any scope, as well as users writing their own USER rows).
Per-scope branching lives in the **internal layer** only: queries
are split for typing ergonomics (`Domain.appConfigs`,
`UserNode.appConfigs`, `myAppConfigs`, `publicAppConfigs`,
`adminAppConfigs`), and the repository / service split in §2 routes
the write to the right backend. Scope-dependent authorization is
enforced in the **service layer** (see permission rules below).

```graphql
type Mutation {
  """
  Create a new app config document. Identified by
  `AppConfigKey { scope, scopeId, name }`. Strictly an insert —
  errors if any row already exists for the natural key, regardless
  of `status` (to revive a soft-deleted document, use
  `restoreAppConfig`).

  For `USER` scope the input `config` is stored as
  `userCustomizedConfig`; the merged view is recomputed on the next
  read and is never written directly.

  Authorization (scope-dependent, enforced in the service layer):
  - `PUBLIC` / `DOMAIN` / `DOMAIN_USER_DEFAULTS`: admin only.
  - `USER`: admin, or the owner themselves — `scopeId` must equal
    the caller's `user_id`.
  """
  createAppConfig(input: CreateAppConfigInput!): CreateAppConfigPayload!

  """
  Replace an existing app config document's stored JSON wholesale
  with the input. Errors if no `ALIVE` row exists for the natural
  key (missing or `DELETED`). Same scope-dependent authorization as
  `createAppConfig`.

  For `USER` scope the input `config` replaces that row's
  `userCustomizedConfig`; the merged view is recomputed on the next
  read and is never written directly.
  """
  updateAppConfig(input: UpdateAppConfigInput!): UpdateAppConfigPayload!

  """
  Soft-delete an app config document (`status = DELETED`). Same
  scope-dependent authorization as the other write mutations. The
  row is preserved for audit; call `restoreAppConfig` on the same
  key to bring it back. Idempotent — silent no-op if the row is
  absent or already `DELETED`.
  """
  deleteAppConfig(input: DeleteAppConfigInput!): DeleteAppConfigPayload!

  """
  Restore a soft-deleted app config document (`status = DELETED →
  ALIVE`). The stored value is preserved as-is — to change the
  value, follow up with `updateAppConfig`. Same scope-dependent
  authorization as the other write mutations. Errors if the row is
  missing or already `ALIVE`.
  """
  restoreAppConfig(input: RestoreAppConfigInput!): RestoreAppConfigPayload!
}

enum AppConfigScopeGQL {
  PUBLIC
  DOMAIN
  DOMAIN_USER_DEFAULTS
  USER
}

enum AppConfigStatusGQL {
  ALIVE
  DELETED
}

# ── Composite key shared by write mutations ──────────────────

"""
Natural composite key identifying a single app config row.
Mirrors the Python `AppConfigKey` dataclass used by the repository /
db_source layer.
- `PUBLIC`:               `scopeId` is the literal string `"public"`.
- `DOMAIN`:               `scopeId` is `domain_name`.
- `DOMAIN_USER_DEFAULTS`: `scopeId` is `domain_name`.
- `USER`:                 `scopeId` is `user_id` (UUID string).
- `name` is the document name (unique within the scope).
"""
input AppConfigKey {
  scope: AppConfigScopeGQL!
  scopeId: String!
  name: String!
}

# ── Inputs ────────────────────────────────────────────────────

input CreateAppConfigInput {
  """Target row identifier."""
  key: AppConfigKey!

  """
  Initial stored value — pass `{}` to create the row with an empty
  document.
  - `PUBLIC` / `DOMAIN` / `DOMAIN_USER_DEFAULTS`: set as the
    document's `config`.
  - `USER`: set as that user's `userCustomizedConfig`.
  """
  config: JSON!
}

input UpdateAppConfigInput {
  """Target row identifier."""
  key: AppConfigKey!

  """
  New stored value — replaces the row's content wholesale. Pass `{}`
  to clear the document while keeping the row.
  - `PUBLIC` / `DOMAIN` / `DOMAIN_USER_DEFAULTS`: replaces the
    document's `config` directly.
  - `USER`: replaces that user's `userCustomizedConfig` (the merged
    `config` is read-only computed and cannot be written).
  """
  config: JSON!
}

input DeleteAppConfigInput {
  """Target row identifier."""
  key: AppConfigKey!
}

input RestoreAppConfigInput {
  """Target row identifier."""
  key: AppConfigKey!
}

# ── Payload ──────────────────────────────────────────────────

"""
Result of `createAppConfig`. Exposes the newly created row via the
generic `AppConfig`. For `USER`-scope writes, clients that need the
recomputed merged view should re-query `myAppConfigs` or
`UserNode.appConfigs`.
"""
type CreateAppConfigPayload {
  appConfig: AppConfig!
}

"""
Result of `updateAppConfig`. Exposes the affected row via the
generic `AppConfig` regardless of which scope the mutation
targeted. For `USER`-scope writes, clients that need the recomputed
merged view should re-query `myAppConfigs` or `UserNode.appConfigs`
(they expose `mergedConfig` / `domainDefaultConfig` /
`domainConfig`), since `AppConfig.config` is the raw stored value
only.
"""
type UpdateAppConfigPayload {
  appConfig: AppConfig!
}

"""
Result of `deleteAppConfig`. The returned row reflects the post
soft-delete state (`status = DELETED`).
"""
type DeleteAppConfigPayload {
  appConfig: AppConfig!
}

"""
Result of `restoreAppConfig`. The returned row reflects the post
restore state (`status = ALIVE`, stored value unchanged).
"""
type RestoreAppConfigPayload {
  appConfig: AppConfig!
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

Queries:

| Operation                | Anonymous | User       | Admin |
|--------------------------|-----------|------------|-------|
| `publicAppConfigs`       | ✅        | ✅         | ✅    |
| `myAppConfigs`           | ❌        | ✅ (self)  | ✅    |
| `Domain.appConfigs`      | ❌        | ❌         | ✅    |
| `UserNode.appConfigs`    | ❌        | ✅ (self)  | ✅    |
| `adminAppConfigs`        | ❌        | ❌         | ✅    |

Write mutations (`createAppConfig`, `updateAppConfig`,
`deleteAppConfig`, `restoreAppConfig`) share the same
scope-dependent rule based on `input.key.scope`:

| `input.key.scope`        | Anonymous | User                                             | Admin |
|--------------------------|-----------|--------------------------------------------------|-------|
| `PUBLIC`                 | ❌        | ❌                                               | ✅    |
| `DOMAIN`                 | ❌        | ❌                                               | ✅    |
| `DOMAIN_USER_DEFAULTS`   | ❌        | ❌                                               | ✅    |
| `USER`                   | ❌        | ✅ *only if* `input.key.scopeId == current_user.user_id` | ✅    |

Where the checks live:
- `createAppConfig` / `updateAppConfig` / `deleteAppConfig` /
  `restoreAppConfig` resolver: thin pass-through to the service
  layer. The service dispatches on `input.key.scope`, routes to the
  matching repository (§2), and enforces the scope-dependent rule
  above — admin-only for non-`USER` scopes; for `USER`, admin *or*
  `scopeId == current_user.user_id`. Any other caller combination
  returns a permission error; there is no silent reinterpretation of
  `scopeId`.
- `Domain.appConfigs` field resolver: `check_admin_only()`; returns
  an empty Connection for non-admin callers.
- `UserNode.appConfigs` field resolver: returns an empty Connection
  when the parent node's `user_id` differs from `current_user` and the
  caller is not an admin.

---

## 4. REST Schema — `/v2/app-configs/...`

Mounted under the existing `app-configs` prefix
(`RouteRegistry.create("app-configs", ...)` in
`api/rest/v2/app_config/registry.py`). Scope is expressed as **named
sub-resources** (`domains/`, `users/`, `public`, `my`) and documents
are addressed by their `name` segment, matching the project-wide v2
conventions in `api/rest/v2/CLAUDE.md`.

### Endpoints

Write endpoints map 1:1 onto the GQL mutations: `POST` = create
(strict insert; errors `409` if any row exists), `PUT` = update
(errors `404` if no `ALIVE` row), `DELETE` = soft-delete, and a
dedicated `POST {path}:restore` action reverses the soft-delete
(`DELETED → ALIVE`, value unchanged; errors `404` / `409` if
missing / already `ALIVE`).

| Method | Path                                                                  | Access     | Description                                          |
|--------|-----------------------------------------------------------------------|------------|------------------------------------------------------|
| GET    | `/v2/app-configs/public`                                              | Anonymous  | List all public documents                            |
| GET    | `/v2/app-configs/public/{name}`                                       | Anonymous  | Read one public document                             |
| GET    | `/v2/app-configs/domains/{domain_name}`                               | Admin      | List a domain's own documents                        |
| GET    | `/v2/app-configs/domains/{domain_name}/{name}`                        | Admin      | Read one of a domain's own documents                 |
| POST   | `/v2/app-configs/domains/{domain_name}/{name}`                        | Admin      | Create one of a domain's own documents               |
| PUT    | `/v2/app-configs/domains/{domain_name}/{name}`                        | Admin      | Replace one of a domain's own documents              |
| DELETE | `/v2/app-configs/domains/{domain_name}/{name}`                        | Admin      | Soft-delete one of a domain's own documents          |
| POST   | `/v2/app-configs/domains/{domain_name}/{name}:restore`                | Admin      | Restore a soft-deleted domain document               |
| GET    | `/v2/app-configs/domains/{domain_name}/user-defaults`                 | Admin      | List a domain's user-defaults documents              |
| GET    | `/v2/app-configs/domains/{domain_name}/user-defaults/{name}`          | Admin      | Read one user-defaults document                      |
| POST   | `/v2/app-configs/domains/{domain_name}/user-defaults/{name}`          | Admin      | Create one user-defaults document                    |
| PUT    | `/v2/app-configs/domains/{domain_name}/user-defaults/{name}`          | Admin      | Replace one user-defaults document                   |
| DELETE | `/v2/app-configs/domains/{domain_name}/user-defaults/{name}`          | Admin      | Soft-delete one user-defaults document               |
| POST   | `/v2/app-configs/domains/{domain_name}/user-defaults/{name}:restore`  | Admin      | Restore a soft-deleted user-defaults document        |
| GET    | `/v2/app-configs/users/{user_id}`                                     | Admin      | List a user's documents                              |
| GET    | `/v2/app-configs/users/{user_id}/{name}`                              | Admin      | Read one of a user's documents (raw)                 |
| POST   | `/v2/app-configs/users/{user_id}/{name}`                              | Admin      | Create one of a user's documents                     |
| PUT    | `/v2/app-configs/users/{user_id}/{name}`                              | Admin      | Replace one of a user's documents                    |
| DELETE | `/v2/app-configs/users/{user_id}/{name}`                              | Admin      | Soft-delete one of a user's documents                |
| POST   | `/v2/app-configs/users/{user_id}/{name}:restore`                      | Admin      | Restore a soft-deleted user document                 |
| POST   | `/v2/app-configs/search`                                              | Admin      | Cross-scope search (filter / order / paginate)       |
| GET    | `/v2/app-configs/my`                                                  | User       | List own documents (each with merged result)         |
| GET    | `/v2/app-configs/my/{name}`                                           | User       | Read own document (with merged result)               |
| POST   | `/v2/app-configs/my/{name}`                                           | User       | Create own document                                  |
| PUT    | `/v2/app-configs/my/{name}`                                           | User       | Replace own document                                 |
| DELETE | `/v2/app-configs/my/{name}`                                           | User       | Soft-delete own document                             |
| POST   | `/v2/app-configs/my/{name}:restore`                                   | User       | Restore own soft-deleted document                    |

`POST /v2/app-configs/search` accepts the same input schema as the
GQL `adminAppConfigs` field (`filter` / `orderBy` / pagination
arguments) in the request body and returns the same result.

> `/v2/app-configs/my/...` follows the `my_` self-service convention
> (`api/rest/v2/CLAUDE.md`) — the adapter resolves `current_user()`
> internally and fixes `scope_id` to the caller's `user_id`. The
> body for PUT accepts only `userCustomizedConfig` (snake-case
> `user_customized_config` in REST); there is no input field that
> can target another user.

> Read endpoints filter to `status = ALIVE` by default. Revival
> goes through the dedicated `POST {path}:restore` action;
> `PUT`/`POST` on a soft-deleted natural key does *not* revive and
> instead errors (`404` for PUT since no ALIVE row, `409` for POST
> since a row already exists).

---

## 5. `user_app_config` semantics — Merge policy

### Storage

- `user_app_config.extra_config` (the DB column, exposed as
  `userCustomizedConfig` in GQL) stores **only the values the user has
  explicitly set** — for the named document.
- The domain-side inputs to the merge live in their own scopes:
  `(scope_type=DOMAIN, scope_id=domain_name, name=N)` (the domain's
  own public value) and
  `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name, name=N)`
  (the per-user default). Neither is copied into user rows — to
  avoid having to rewrite every user row when the domain admin edits
  a domain-side value.
- Domain-side values are applied **per-name**: the DOMAIN and
  DOMAIN_USER_DEFAULTS rows for a given `name` form the merge base
  for the same-`name` `USER` row's `userCustomizedConfig`. Different
  `name`s are independent.

### Read (Merge)

The merge — for a given `(user_id, name)` — proceeds as follows in a
single transaction:

1. Caller (repository / service) resolves the user's `domain_name`
   and passes it in. The app-config db_source itself never queries
   the `users` table.
2. Read the
   `(scope_type=domain, scope_id=domain_name, name=name)` row to get
   its `extra_config` (the domain's own value).
3. Read the
   `(scope_type=domain_user_defaults, scope_id=domain_name, name=name)`
   row to get its `extra_config` (the user-defaults).
4. Read the `(scope_type=user, scope_id=user_id, name=name)` row to
   get `extra_config` (= `userCustomizedConfig`).
5. **Deep merge**, low → high priority:
   `domain ⊕ domain_user_defaults ⊕ userCustomizedConfig`. Nested
   objects are merged recursively per key; at leaf keys, the
   higher-priority value wins. Lists are treated as leaves and
   replaced wholesale by the higher-priority value (element-level
   merge of arrays has no unambiguous semantics). The result is
   exposed as `UserAppConfig.mergedConfig`; the raw DOMAIN row's
   `extra_config` is exposed as `UserAppConfig.domainConfig` and the
   raw DOMAIN_USER_DEFAULTS row's as
   `UserAppConfig.domainDefaultConfig`.

> Reading the DOMAIN row for merge is done by the service with the
> caller's own `domain_name` — it does *not* go through
> `Domain.appConfigs` (admin-only) and is not an authorization hole:
> users can only read their own domain's value, and only via merge.

A list variant returns one merged result per `name` for which at
least one of the three rows (DOMAIN, DOMAIN_USER_DEFAULTS, USER)
exists.

> **Note**: the Python sketch below is illustrative only — it shows
> the data flow / SQL shape. Method names, signatures, and class
> placement are *not* part of this BEP's contract and may differ in
> the actual implementation.

```python
class AppConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_merged(
        self, user_id: str, domain_name: str, name: str
    ) -> MergedAppConfig:
        # Caller (repository / service) resolves the user's domain_name
        # before calling — this db_source touches only app_configs rows.
        # Three scoped queries on the same readonly session — each
        # natural key returns at most one row, so no post-query
        # filtering needed.
        async with self._db.begin_readonly_session() as db_sess:
            domain_row = (await db_sess.execute(
                sa.select(AppConfigRow).where(
                    AppConfigRow.status == AppConfigStatus.ALIVE,
                    AppConfigRow.scope_type == AppConfigScopeType.DOMAIN,
                    AppConfigRow.scope_id == domain_name,
                    AppConfigRow.name == name,
                )
            )).scalar_one_or_none()

            defaults_row = (await db_sess.execute(
                sa.select(AppConfigRow).where(
                    AppConfigRow.status == AppConfigStatus.ALIVE,
                    AppConfigRow.scope_type == AppConfigScopeType.DOMAIN_USER_DEFAULTS,
                    AppConfigRow.scope_id == domain_name,
                    AppConfigRow.name == name,
                )
            )).scalar_one_or_none()

            user_row = (await db_sess.execute(
                sa.select(AppConfigRow).where(
                    AppConfigRow.status == AppConfigStatus.ALIVE,
                    AppConfigRow.scope_type == AppConfigScopeType.USER,
                    AppConfigRow.scope_id == user_id,
                    AppConfigRow.name == name,
                )
            )).scalar_one_or_none()

        domain_value = domain_row.extra_config if domain_row else {}
        domain_defaults = defaults_row.extra_config if defaults_row else {}
        user_customized = user_row.extra_config if user_row else {}
        return MergedAppConfig(
            domain_name=domain_name,
            user_id=user_id,
            name=name,
            user_customized_config=user_customized,
            domain_default_config=domain_defaults,                            # GQL: UserAppConfig.domainDefaultConfig
            domain_config=domain_value,                                       # GQL: UserAppConfig.domainConfig
            merged_config=deep_merge(domain_value, domain_defaults, user_customized),  # GQL: UserAppConfig.mergedConfig
        )


class UserAppConfigRepository:
    _db_source: AppConfigDBSource
    _user_db_source: UserDBSource    # supplies the user → domain_name lookup

    def __init__(
        self,
        db_source: AppConfigDBSource,
        user_db_source: UserDBSource,
    ) -> None:
        self._db_source = db_source
        self._user_db_source = user_db_source

    async def get_merged(self, user_id: str, name: str) -> MergedAppConfig:
        domain_name = await self._user_db_source.get_domain_name(user_id)
        return await self._db_source.get_merged(user_id, domain_name, name)
```

### Exposure

`UserAppConfig` exposes four views of the same logical document so
the WebUI can render and edit cleanly:

- `userCustomizedConfig` — what the user explicitly set (raw)
- `domainDefaultConfig` — the matching `DOMAIN_USER_DEFAULTS` row's
  raw `extra_config` (`null` if no row exists)
- `domainConfig` — the matching `DOMAIN` row's raw `extra_config`
  (`null` if no row exists)
- `mergedConfig` — `domainConfig ⊕ domainDefaultConfig ⊕
  userCustomizedConfig`, what the UI actually applies

The REST `GET /v2/app-configs/my/{name}` response carries the same
four views (snake_case: `user_customized_config`,
`domain_default_config`, `domain_config`, `merged_config`).

---

## 6. Client Integration — WebUI bootstrap

The WebUI requests configs by addressing them explicitly with
`(scope, scopeId, name)`. There is no server-side hierarchical
fall-through — clients know which scope they are asking about. The
list of public documents the WebUI must load before login is owned
entirely by the frontend (hard-coded or shipped in the WebUI
bundle) — the server does not publish a bootstrap list.

### Bootstrap flow

All of the use cases below use the GraphQL endpoint. The REST
schema (§4) is an equivalent surface for non-GraphQL clients, but
the WebUI bootstrap is specified in GQL.

1. **Pre-login (anonymous)** — for each document the WebUI wants
   before login, it issues a `publicAppConfigs` query with a `name`
   filter (no auth). The `theme` / `branding` shapes are pulled via
   a single document fetch each — see S1 in §7. On no-edge /
   network error the WebUI falls back to its built-in defaults for
   that document.

2. **Post-login** — the WebUI issues a single `myAppConfigs` query
   (optionally combined with `publicAppConfigs` in the same GQL
   document) to fetch *all* of the caller's user documents in one
   round trip. Each entry carries `userCustomizedConfig`,
   `domainDefaultConfig`, `domainConfig`, and the three-way merged
   `mergedConfig` (§5). See S2 in §7.

3. **Domain-scoped reads** (admin UI) — the WebUI traverses
   `domain(name: "...") { appConfigs { ... } }` (or a single
   document via `filter: { name: { equals: "..." } }`) with admin
   credentials. The root `adminAppConfigs` is available for
   cross-scope admin search — S6 in §7.

---

## 7. User Scenarios — end-to-end caller flows

Each scenario describes *who* calls *when* and *what they want to
achieve*, paired with the actual call spec. Intended as a reference
for client-side implementation.

### S1. Pre-login public config loading (anonymous)

The WebUI fetches the public `theme` document before rendering the
login screen. (The JSON shape inside `config` is owned by the
frontend; backend stores it opaquely.)

```graphql
query LoadPublicTheme {
  publicAppConfigs(filter: { name: { equals: "theme" } }, first: 1) {
    edges { node { name config modifiedAt } }
  }
}
```

- No auth token.
- Single-document retrieval is just a Connection query with a `name`
  filter — there is no singular root field.
- On failure (no edge returned, network error) the WebUI falls back
  to its built-in defaults. The set of pre-login documents is
  hard-coded in the WebUI (see §6).

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
        domainConfig
        mergedConfig
        modifiedAt
      }
    }
  }
  publicAppConfigs {
    edges { node { name config } }
  }
}
```

- Server: `myAppConfigs` returns one entry per `name` for which any
  of the three source rows (`USER`, `DOMAIN_USER_DEFAULTS`,
  `DOMAIN` — all keyed to the caller / caller's domain) is `ALIVE`.
  Rows that are absent contribute `{}` to the merge. Merge per §5.
- The WebUI initializes UI state from `mergedConfig` per document
  and keeps the raw views around so the Settings page can show
  user-changed vs. domain-default vs. domain-wide value.

### S3. The user saves their own document

The user replaces their `theme` document. They call the unified
`updateAppConfig` with `key.scope = USER` and `key.scopeId =
current_user.user_id`; the service layer authorizes the write by
matching `scopeId` against the caller. To see the recomputed merge
the client re-queries `myAppConfigs` (or reads the row through
`UserNode.appConfigs` / `node(id)`), since the mutation payload
returns the raw `AppConfig` only.

```graphql
mutation SaveMyTheme($input: UpdateAppConfigInput!) {
  updateAppConfig(input: $input) {
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
      "name": "theme"
    },
    "config": {
      "sectionA": { "optionX": "value-1" },
      "sectionB": "value-2"
    }
  }
}
```

- Authorization: `scope=USER` → service allows admin *or* caller
  whose `user_id == key.scopeId`. Any other `scope` submitted by a
  non-admin is rejected here.
- For `USER` scope, the input `config` replaces the row's
  `userCustomizedConfig` wholesale. The merged view is recomputed on
  the next read.
- **Replace** semantics: anything the caller wants to keep must be
  sent in the same payload — there is no partial-merge or per-key
  patch.
- **First write vs. subsequent writes**: `updateAppConfig` errors if
  no `ALIVE` row exists. For the very first save of a given `name`
  (or after a soft-delete), the client calls `createAppConfig` with
  the same `key` and `config` payload shape instead. Clients should
  pick the mutation based on whether `myAppConfigs` already returned
  an entry for that `name` — the list-or-create decision is the
  client's, not the server's.

### S4. Admin publishes the per-user defaults for a domain

The domain admin publishes a new `preferences` document that every
user in the domain inherits as the merge base — e.g. the default
visible columns and column order for the main tables. The first
publish uses `createAppConfig` with `key.scope =
DOMAIN_USER_DEFAULTS`; later edits on the same document use
`updateAppConfig` with the identical input shape. DOMAIN-scope
publishes (the domain's own public value, e.g. a `menu` document)
go through the same mutations with `key.scope = DOMAIN`.

```graphql
mutation CreateAppConfig($input: CreateAppConfigInput!) {
  createAppConfig(input: $input) {
    appConfig { id scope scopeId name status config modifiedAt }
  }
}
```

```json
{
  "input": {
    "key": {
      "scope": "DOMAIN_USER_DEFAULTS",
      "scopeId": "default",
      "name": "preferences"
    },
    "config": { "tableColumns": { "sessions": ["name", "status", "createdAt"] } }
  }
}
```

- Authorization: admin required — the service rejects non-admin
  writes to `DOMAIN_USER_DEFAULTS` (and to `DOMAIN` / `PUBLIC`).
- Internally, the service routes to the matching repository (§2)
  and strictly inserts a new `ALIVE` row. Errors if any row (ALIVE
  or DELETED) already exists for the key — the admin either uses
  `updateAppConfig` (when ALIVE) or `restoreAppConfig` (when
  DELETED) instead.
- Effect: every user in the domain picks up the new defaults on the
  next `myAppConfigs` read (merged per §5).

### S5. Admin writes a specific user's document on their behalf

For a support request, an admin overwrites user A's `preferences`
`userCustomizedConfig` — same `updateAppConfig`, now with
`key.scope = USER` and `key.scopeId = user A's user_id`. The
service's USER-scope rule allows this call because the caller is an
admin (owner-only would require matching `scopeId`). The merged
`config` is always read-only and never written directly.

```graphql
mutation ReplaceAppConfig($input: UpdateAppConfigInput!) {
  updateAppConfig(input: $input) {
    appConfig { id scope scopeId name status config modifiedAt }
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

- For `USER` scope the `config` input replaces that user's
  `userCustomizedConfig` wholesale.
- If user A has never saved `preferences` before, the admin uses
  `createAppConfig` instead (same input shape) — `updateAppConfig`
  errors on missing rows.
- The next time that user calls `myAppConfigs`, the new
  `preferences` `userCustomizedConfig` is merged with the matching
  domain defaults in the response.

### S6. Admin audits all AppConfigs (cross-scope search)

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

### S7. Operator removes an entire document (soft-delete)

Removing a stale or deprecated document — e.g. retiring an old
`legacy_menu` document for a domain:

```graphql
mutation RemoveDomainLegacyMenu($input: DeleteAppConfigInput!) {
  deleteAppConfig(input: $input) {
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

- Authorization: admin required for non-`USER` scopes; a user can
  call `deleteAppConfig` only when `key.scope = USER` and
  `key.scopeId == current_user.user_id`.
- Service flips `status = DELETED` on the matching row. Subsequent
  reads (`Domain.appConfigs`, `UserNode.appConfigs`,
  `adminAppConfigs`, etc.) hide the document.
- **Idempotent**: no-op when the row is absent or already `DELETED`.
- **Recoverable**: `restoreAppConfig` on the same `key` flips the
  row back to `ALIVE` with its stored value unchanged. To change
  the value after restoring, chain an `updateAppConfig` call.
  `createAppConfig` does *not* revive — it errors on any
  pre-existing row.

A user removing their own document uses the same `deleteAppConfig`
mutation with `key.scope = USER` and `key.scopeId =
current_user.user_id` — the service's USER-scope rule authorizes
the call.
