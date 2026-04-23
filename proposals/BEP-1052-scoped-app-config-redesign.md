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

| Story                                                         | Scope                  | Read              | Write       |
|---------------------------------------------------------------|------------------------|-------------------|-------------|
| Theme, Branding (must work before login)                      | `public`               | Anyone            | Admin       |
| UI hide/show, menu config, per-user preference defaults       | `domain_user_defaults` | Logged-in users   | Admin       |
| Domain-only internal management settings                      | `domain`               | Admin             | Admin       |
| Per-user personal settings                                    | `user`                 | Owner/Admin       | Owner/Admin |

> The `domain` scope is admin-only policy and does **not** participate
> in the `myAppConfigs` merge. Documents users must be able to read
> (UI hide/show, etc.) must be published under `domain_user_defaults`
> so they reach users via the merge path — see §5 for the full split.

## Design Principles

- **Schema-less JSON**: the backend is purely a storage layer; the
  structure and meaning of the configuration are owned by the frontend.
- **Scope = Entity**: access control is expressed at the scope (entity)
  level, not the field level.
  `public_app_config` (Anonymous read / Admin write), `domain_app_config`
  (Admin read & write), `domain_user_defaults_app_config` (Admin write,
  reaches users via merge), `user_app_config` (Owner/Admin read /
  Owner-self + Admin write).
- **Named documents within a scope**: each row is identified by the
  natural composite key `(scope_type, scope_id, name)`. A scope can hold
  any number of named documents; clients address them explicitly by
  name (no hierarchical fall-through lookup).
- **Writes split into create / update / delete / restore, further
  split into admin / my paths.** The same four verbs are exposed
  symmetrically as admin-path mutations (`adminCreateAppConfig`, etc.
  — every scope, admin-only, return raw `AppConfig`) and self-service
  path mutations (`createMyAppConfig`, etc. — `USER` + `current_user`
  implicit, any authenticated user on their own row, return merged
  `MyAppConfig`). `create` strictly inserts a new row (errors if any
  row already exists for the key, even a soft-deleted one); `update`
  replaces an existing `ALIVE` row's stored JSON wholesale; `delete`
  soft-deletes (`ALIVE → DELETED`); `restore` is the explicit inverse
  of delete (`DELETED → ALIVE`, value unchanged). Neither `create`
  nor `update` does partial update / deep-merge / key-level removal
  at the write boundary. There is no upsert. Identification uses the
  `(scope, scopeId, name)` natural key, never Relay `id` — my-path
  mutations have scope/scopeId injected by the server.
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
    updated_at: Mapped[datetime]

    __table_args__ = (
        sa.UniqueConstraint(
            "scope_type", "scope_id", "name", name="uq_app_configs_scope_name"
        ),
    )
```

### Scope ID convention

| `scope_type`            | `scope_id` value          | Meaning of `extra_config`                                    |
|-------------------------|---------------------------|--------------------------------------------------------------|
| `public`                | literal string `"public"` | public (pre-login) value of the document                      |
| `domain`                | `domain_name`             | the domain's own value of the document                        |
| `domain_user_defaults`  | `domain_name`             | merge base for users in that domain (per-document)            |
| `user`                  | `user_id` (UUID string)   | user-customized value of the document                         |

`UniqueConstraint` on `(scope_type, scope_id, name)` guarantees a
single row per natural key. A scope can hold any number of distinct
`name`s.

### Status filtering

All read paths filter `status = ALIVE` by default. Callers can
opt into seeing `DELETED` rows by passing an explicit status
filter on Connections that expose one (`AppConfigFilterGQL.status`
in GraphQL — see §3) or the equivalent REST query parameter — this
is used for admin recovery / audit flows and for checking whether a
name is reusable after deletion. Revival uses the dedicated
`adminRestoreAppConfig` / `restoreMyAppConfig` mutations, which flip
`status = DELETED → ALIVE` while preserving the stored value;
`*Create*` errors on any pre-existing row (ALIVE or DELETED), and
`*Update*` errors on a `DELETED` row.

---

## 2. Repository Layer — split per scope

Keep `models/app_config/row.py`'s `AppConfigRow` as a single class, but
**split the repository into four classes per scope**. Their access
policies and call patterns differ enough that combining them would make
method signatures unwieldy.

```
repositories/app_config/
├── db_source/
│   └── db_source.py         # single db_source
├── public_app_config_repository.py
├── domain_app_config_repository.py
├── domain_user_defaults_app_config_repository.py
├── user_app_config_repository.py     # USER row CRUD + merged view (MyAppConfig)
└── repositories.py                   # exports all four repos
```

### Repository responsibility split

| Repository                              | Methods                                                                                                              |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| `PublicAppConfigRepository`             | `get(name)`, `get_by_id(id)`, `create(name, extra_config)`, `update(name, extra_config)`, `soft_delete(name)`, `restore(name)`, `search(filter)`                                             |
| `DomainAppConfigRepository`             | `get(domain_name, name)`, `get_by_id(id)`, `create(domain_name, name, extra_config)`, `update(domain_name, name, extra_config)`, `soft_delete(domain_name, name)`, `restore(domain_name, name)`, `search(domain_name, filter)` |
| `DomainUserDefaultsAppConfigRepository` | `get(domain_name, name)`, `get_by_id(id)`, `create(domain_name, name, extra_config)`, `update(domain_name, name, extra_config)`, `soft_delete(domain_name, name)`, `restore(domain_name, name)`, `search(domain_name, filter)` |
| `UserAppConfigRepository`               | `get(user_id, name)`, `get_by_id(id)`, `create(user_id, name, extra_config)`, `update(user_id, name, extra_config)`, `soft_delete(user_id, name)`, `restore(user_id, name)`, `search(user_id, filter)`, `get_merged(user_id, name)`, `search_merged(user_id, filter)` — the first group is `USER` row CRUD (serves `UserAppConfig`); the last two delegate to `AppConfigDBSource`'s merge-specific method, which reads `DOMAIN_USER_DEFAULTS` + `USER` in a single SQL and returns the deep-merged view (serves `MyAppConfig`, see §5). `DOMAIN` is not part of the merge. `search_merged` backs the `myAppConfigs` Connection. |

`DomainUserDefaultsAppConfigRepository` mirrors
`DomainAppConfigRepository` (admin-only, same call shape) but operates
on `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name)` rows.
Splitting it from `DomainAppConfigRepository` keeps each repository
mapped to exactly one scope, matching the rest of the layout.

`UserAppConfigRepository` plays a **dual role**: raw `USER` row CRUD
(serving `UserAppConfig`) + read-side merged view (serving
`MyAppConfig`). It takes a single `AppConfigDBSource` in its
constructor like the other scope repositories — the user → domain_name
resolution needed by the merge is performed inside
`AppConfigDBSource`'s merge method in a single SQL (via a `users`
subquery), so no separate `UserDBSource` is injected at the
repository level. The GraphQL schema exposes `UserAppConfig` (raw)
and `MyAppConfig` (merged) as separate types, but internally they
share one repository — there is no `MyAppConfigRepository`. The
`DOMAIN` scope is admin-enforced domain policy and therefore never
participates in this merge; DOMAIN rows are only reachable via the
admin read paths (`DomainV2.appConfigs` / `adminAppConfigs` /
`node(id)`).

All read methods default to filtering `status = ALIVE` unless the
caller opts in via `filter.status` on `search(...)`.

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

    async def get_by_id(self, id: uuid.UUID) -> AppConfigRow | None:
        # ID-based lookup for Actions that have already resolved the
        # natural key to a row id (see §3 "Name → ID resolution").
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

Listing operations are not db_source primitives — listing is
expressed as search (filter + pagination) at the Connection layer,
which the service implements via a separate search path rather
than a scoped-list on the db_source.

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
  updatedAt: DateTime!
}

"""Domain config document. Admin read & write. The domain's own value."""
type DomainAppConfig implements Node {
  id: ID!

  """Owning domain (back-reference). Lookup only."""
  domain: DomainV2!

  """Document name (unique within this domain)."""
  name: String!

  """Stored config value for this document."""
  config: JSON!

  createdAt: DateTime!
  updatedAt: DateTime!
}

"""
User personal config document — a single `USER`-scope row, exposing
only the raw stored value (no domain merge). Shaped like the other
scope types (`PublicAppConfig`, `DomainAppConfig`) — a single
`config` field.

For the merged view (`domain_user_defaults ⊕ userCustomizedConfig`),
use `myAppConfigs` (returns `MyAppConfig`) — see §5. `DOMAIN`-scope
values do not participate in the merge (admin-enforced domain policy).

Owner or Admin read; owner or Admin write.
"""
type UserAppConfig implements Node {
  id: ID!

  """Owning user (back-reference)."""
  user: UserV2!

  """Document name (unique within this user)."""
  name: String!

  """Raw stored value — the user's `userCustomizedConfig`."""
  config: JSON!

  createdAt: DateTime!
  updatedAt: DateTime!
}

"""
Merged app-config view from the current user's perspective —
accessible only via `myAppConfigs`.

Serves a deep-merge of two same-`name` source rows
`(DOMAIN_USER_DEFAULTS, user.domain_name)` and `(USER, user.user_id)`.
An entry appears whenever at least one of these is `ALIVE`. Even
without a USER row, `userCustomizedConfig` is returned as `{}`.

`DOMAIN`-scope rows **do not participate** in this merge — they carry
admin-enforced domain policy (values users cannot override), so they
are never mixed with the user's defaults/overrides and are exposed
only via admin-only paths (`DomainV2.appConfigs` / `adminAppConfigs`
/ `node(id)`). By convention `UserAppConfig` /
`DomainUserDefaultsAppConfig` do not carry DOMAIN-policy keys. Admins
manage DOMAIN values via `adminCreateAppConfig` /
`adminUpdateAppConfig` / `adminDeleteAppConfig` with the appropriate
`key.scope`.

Although derived, `MyAppConfig` implements `Node` — for refetch
convenience it exposes the `(user_id, name)` composite as a
server-encoded global ID (`base64("MyAppConfig:{user_id}:{name}")`).
A `name` is only unique within a user scope, so pairing it with
`user_id` is required for global uniqueness. The `node(id)` resolver
decodes the id and returns the merged view only when
`decoded.user_id == current_user.id` (or the caller is admin) —
otherwise it would leak another user's merged view. Single-document
retrieval: `myAppConfigs` with a `name` filter, or `node(id)`.
"""
type MyAppConfig implements Node {
  """
  Server-encoded global ID — `base64("MyAppConfig:{user_id}:{name}")`.
  """
  id: ID!

  """Document name (unique within this user)."""
  name: String!

  """
  Raw value of the `USER`-scope row — what the user explicitly set.
  `{}` when no USER row exists.
  """
  userCustomizedConfig: JSON!

  """
  Raw value of the matching same-`name`
  `(scope=DOMAIN_USER_DEFAULTS, scopeId=user.domain_name)` row's
  `extra_config` — the admin-provided per-user default. `null` when
  no such row exists. Lets the Settings UI distinguish "admin-provided
  per-user default" from "what the user changed".
  """
  domainDefaultConfig: JSON

  """
  Effective applied value: deep merge of
  `domainDefaultConfig` ⊕ `userCustomizedConfig` (left = lowest
  priority, right = highest). Clients render the UI from this value.
  """
  mergedConfig: JSON!

  """Max of participating source rows' `updatedAt`."""
  updatedAt: DateTime!
}
```

### Added/extended fields (Relationship)

| Location      | Field                                                                                  |
|---------------|----------------------------------------------------------------------------------------|
| `DomainV2` | `appConfigs(filter, orderBy, ...pagination): DomainAppConfigConnection!`               |
| `UserV2`   | `appConfigs(filter, orderBy, ...pagination): UserAppConfigConnection!`                 |

### Permissions

Each `appConfigs` child field enforces its own access rule (not
simply inherited from the parent node) — see the permission matrix
below. In short: `DomainV2.appConfigs` is admin-only;
`UserV2.appConfigs` is owner-or-admin.

```graphql
extend type DomainV2 {
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

extend type UserV2 {
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
going through `admin_user_v2(user_id:)`.

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
  Current user's merged app-config view (auth required). Deep-merges
  `(DOMAIN_USER_DEFAULTS, user.domain_name)` + `(USER, user.user_id)`
  per `name` (see §5). `DOMAIN` scope is not a merge input — domain
  policy is exposed only through admin paths. Filter by `name` to
  retrieve a single document. `filter.scope` / `filter.scopeId` /
  `filter.status` are ignored here — the scope is pinned, and only
  `ALIVE` rows participate in the merge.
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
  ): MyAppConfigConnection!

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
  # admin_user_v2(user_id: UUID!): UserV2
  #                                — admin → admin_user_v2(user_id: ...) { appConfigs { ... } }
  # domain_v2(name: String!): DomainV2
  #                                — admin → domain_v2(name: ...) { appConfigs { ... } }
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

"""Relay Connection holding the current user's merged view — backs `myAppConfigs`."""
type MyAppConfigConnection {
  edges: [MyAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type MyAppConfigEdge {
  cursor: String!
  node: MyAppConfig!
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
  per-scope Connections (`publicAppConfigs`, `DomainV2.appConfigs`,
  `UserV2.appConfigs`, `myAppConfigs`) the scope
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

  """`updated_at` range filter."""
  updatedAt: DateTimeFilter = null

  """
  Filter by row `status`. When omitted, Connections only return
  `ALIVE` rows. Pass `{ equals: DELETED }` (or `{ in: [ALIVE,
  DELETED] }`) to include soft-deleted rows — used by admin
  recovery / audit flows and by callers checking whether a name
  is reusable after deletion.
  """
  status: AppConfigStatusEnumFilter = null

  """All sub-filters must match (AND combination)."""
  AND: [AppConfigFilterGQL!] = null

  """At least one sub-filter must match (OR combination)."""
  OR: [AppConfigFilterGQL!] = null

  """None of the sub-filters may match (NOT combination)."""
  NOT: [AppConfigFilterGQL!] = null
}

"""EnumFilter for AppConfigScopeGQL (equals / in / notEquals / notIn)."""
input AppConfigScopeEnumFilter {
  equals: AppConfigScopeGQL
  in: [AppConfigScopeGQL!]
  notEquals: AppConfigScopeGQL
  notIn: [AppConfigScopeGQL!]
}

"""EnumFilter for AppConfigStatusGQL (equals / in / notEquals / notIn)."""
input AppConfigStatusEnumFilter {
  equals: AppConfigStatusGQL
  in: [AppConfigStatusGQL!]
  notEquals: AppConfigStatusGQL
  notIn: [AppConfigStatusGQL!]
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
  UPDATED_AT
  CREATED_AT
}
```

All Connections filter to `status = ALIVE` by default. Callers can
opt into seeing `DELETED` rows (or both) by passing
`filter.status` on the Connection — admin recovery / audit flows
read deleted rows this way.

### Mutations

Writes are split into an **admin path** and a **self-service (my)
path**, for a total of eight mutations.

- `admin*AppConfig` (4): accept `AppConfigKey { scope, scopeId,
  name }` and cover every scope. **Admin-only**. Return the raw
  `AppConfig`.
- `*MyAppConfig` (4): imply `scope = USER` + `scopeId =
  current_user.user_id`. Input is just `name` (+ `config` for writes).
  Callable by any authenticated user on their own documents.
  Return the **merged `MyAppConfig`** — one round-trip to get the
  latest merged view after a write.

Per-scope branching lives in the **internal layer** only: queries
are split for typing ergonomics (`DomainV2.appConfigs`,
`UserV2.appConfigs`, `myAppConfigs`, `publicAppConfigs`,
`adminAppConfigs`), and the repository split in §2 routes the write
to the right backend. Authorization is enforced in the **service
layer** (see permission matrix below).

```graphql
type Mutation {
  # ── Admin path — every scope, admin-only ─────────────────────

  """
  Create a new app config document (admin-only). Identified by
  `AppConfigKey { scope, scopeId, name }`. Strictly an insert —
  errors if any row already exists for the natural key, regardless
  of `status` (to revive a soft-deleted document, use
  `adminRestoreAppConfig`).

  Admin-side seeding of a `USER`-scope row also uses this mutation.
  The response is the raw `AppConfig`; the target user's merged view
  updates naturally on their next `myAppConfigs` read.
  """
  adminCreateAppConfig(input: AdminCreateAppConfigInput!): AdminCreateAppConfigPayload!

  """
  Replace an existing app config document's stored JSON wholesale
  (admin-only). Errors if no `ALIVE` row exists for the natural key
  (missing or `DELETED`).
  """
  adminUpdateAppConfig(input: AdminUpdateAppConfigInput!): AdminUpdateAppConfigPayload!

  """
  Soft-delete an app config document (`status = DELETED`, admin-only).
  The row is preserved for audit; call `adminRestoreAppConfig` on the
  same key to bring it back. Idempotent — silent no-op if the row is
  absent or already `DELETED`.
  """
  adminDeleteAppConfig(input: AdminDeleteAppConfigInput!): AdminDeleteAppConfigPayload!

  """
  Restore a soft-deleted app config document (`status = DELETED →
  ALIVE`, admin-only). The stored value is preserved as-is — to
  change the value, follow up with `adminUpdateAppConfig`. Errors if
  the row is missing or already `ALIVE`.
  """
  adminRestoreAppConfig(input: AdminRestoreAppConfigInput!): AdminRestoreAppConfigPayload!

  # ── Self-service (my) path — USER + current_user implicit ────

  """
  Create the current user's `USER`-scope document (auth required).
  `name` from the input + implicit `scopeId = current_user.user_id`
  — stores the input `config` as `userCustomizedConfig`. Strictly an
  insert: errors if an `ALIVE` or `DELETED` USER row already exists
  for that `name` (revival is `restoreMyAppConfig`).

  The response is the recomputed `MyAppConfig` — a 2-way merge with
  `DOMAIN_USER_DEFAULTS`, returned in one round-trip.
  """
  createMyAppConfig(input: CreateMyAppConfigInput!): CreateMyAppConfigPayload!

  """
  Replace the current user's `USER`-scope document (auth required).
  Errors if no `ALIVE` USER row exists for that `name`. The response
  is the recomputed `MyAppConfig`.
  """
  updateMyAppConfig(input: UpdateMyAppConfigInput!): UpdateMyAppConfigPayload!

  """
  Soft-delete the current user's `USER`-scope document (auth required).
  The USER row for that `name` flips to `DELETED`. Idempotent. The
  response is the recomputed `MyAppConfig` reflecting only what
  remains (`DOMAIN_USER_DEFAULTS`); `null` if no ALIVE source remains
  for the `name`.
  """
  deleteMyAppConfig(input: DeleteMyAppConfigInput!): DeleteMyAppConfigPayload!

  """
  Restore the current user's soft-deleted USER document
  (`DELETED → ALIVE`). The stored value is preserved as-is — to
  change it, follow up with `updateMyAppConfig`. Errors if the row
  is missing or already `ALIVE`. The response is the recomputed
  `MyAppConfig`.
  """
  restoreMyAppConfig(input: RestoreMyAppConfigInput!): RestoreMyAppConfigPayload!
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

# ── Admin Inputs ─────────────────────────────────────────────

input AdminCreateAppConfigInput {
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

input AdminUpdateAppConfigInput {
  """Target row identifier."""
  key: AppConfigKey!

  """
  New stored value — replaces the row's content wholesale. Pass `{}`
  to clear the document while keeping the row.
  - `PUBLIC` / `DOMAIN` / `DOMAIN_USER_DEFAULTS`: replaces the
    document's `config` directly.
  - `USER`: replaces that user's `userCustomizedConfig`
    (`MyAppConfig.mergedConfig` is read-only computed and cannot be
    written).
  """
  config: JSON!
}

input AdminDeleteAppConfigInput {
  """Target row identifier."""
  key: AppConfigKey!
}

input AdminRestoreAppConfigInput {
  """Target row identifier."""
  key: AppConfigKey!
}

# ── My Inputs — scope=USER, scopeId=current_user.user_id implicit ──

input CreateMyAppConfigInput {
  """Document name (unique within the current user)."""
  name: String!

  """
  Initial `userCustomizedConfig` value — pass `{}` to create the
  row with an empty document. `MyAppConfig.mergedConfig` is
  read-only computed and cannot be written.
  """
  config: JSON!
}

input UpdateMyAppConfigInput {
  """Target document name."""
  name: String!

  """New `userCustomizedConfig` value — replaces wholesale."""
  config: JSON!
}

input DeleteMyAppConfigInput {
  """Target document name."""
  name: String!
}

input RestoreMyAppConfigInput {
  """Target document name."""
  name: String!
}

# ── Admin Payloads — return raw AppConfig ────────────────────

"""
Result of `adminCreateAppConfig`. Exposes the newly created row
via the generic `AppConfig`. The target user's merged view updates
naturally on their next `myAppConfigs` read.
"""
type AdminCreateAppConfigPayload {
  appConfig: AppConfig!
}

"""
Result of `adminUpdateAppConfig`. Exposes the affected row via the
generic `AppConfig` regardless of which scope the mutation targeted
— `AppConfig.config` is the raw stored value only. To inspect a
specific user's raw USER row, use `UserV2.appConfigs` (returns
`UserAppConfig`).
"""
type AdminUpdateAppConfigPayload {
  appConfig: AppConfig!
}

"""
Result of `adminDeleteAppConfig`. The returned row reflects the
post soft-delete state (`status = DELETED`).
"""
type AdminDeleteAppConfigPayload {
  appConfig: AppConfig!
}

"""
Result of `adminRestoreAppConfig`. The returned row reflects the
post restore state (`status = ALIVE`, stored value unchanged).
"""
type AdminRestoreAppConfigPayload {
  appConfig: AppConfig!
}

# ── My Payloads — return merged MyAppConfig ─────────────────

"""Result of `createMyAppConfig`. Recomputed `MyAppConfig` after the write."""
type CreateMyAppConfigPayload {
  myAppConfig: MyAppConfig!
}

"""Result of `updateMyAppConfig`. Recomputed `MyAppConfig` after the write."""
type UpdateMyAppConfigPayload {
  myAppConfig: MyAppConfig!
}

"""
Result of `deleteMyAppConfig`. Recomputed `MyAppConfig` using only
the remaining merge source (`DOMAIN_USER_DEFAULTS`). `null` if no
ALIVE source remains for the `name` after the USER row is soft-deleted.
"""
type DeleteMyAppConfigPayload {
  myAppConfig: MyAppConfig
}

"""Result of `restoreMyAppConfig`. Recomputed `MyAppConfig` after restore."""
type RestoreMyAppConfigPayload {
  myAppConfig: MyAppConfig!
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
  updatedAt: DateTime!
}
```

### Permission matrix

Queries:

| Operation                | Anonymous | User       | Admin |
|--------------------------|-----------|------------|-------|
| `publicAppConfigs`       | ✅        | ✅         | ✅    |
| `myAppConfigs`           | ❌        | ✅ (self)  | ✅    |
| `DomainV2.appConfigs`      | ❌        | ❌         | ✅    |
| `UserV2.appConfigs`    | ❌        | ✅ (self)  | ✅    |
| `adminAppConfigs`        | ❌        | ❌         | ✅    |

Write mutations split into two paths with distinct rules:

**Admin path** — `adminCreateAppConfig`, `adminUpdateAppConfig`,
`adminDeleteAppConfig`, `adminRestoreAppConfig`. All require admin
regardless of `input.key.scope`:

| Operation              | Anonymous | User | Admin |
|------------------------|-----------|------|-------|
| `admin*AppConfig`      | ❌        | ❌   | ✅    |

**Self-service (my) path** — `createMyAppConfig`,
`updateMyAppConfig`, `deleteMyAppConfig`, `restoreMyAppConfig`.
Imply `scope = USER` + `scopeId = current_user.user_id`:

| Operation              | Anonymous | User (self) | Admin (self) |
|------------------------|-----------|-------------|--------------|
| `*MyAppConfig`         | ❌        | ✅          | ✅           |

> Admins operating on another user's `USER` row must use the admin
> path with an explicit `AppConfigKey { scope: USER, scopeId:
> target_user_id, name }` — the my path cannot target another user.

Where the checks live:
- Admin-path resolvers: `check_admin_only()` at entry, then dispatch
  on `input.key.scope` and route to the matching repository (§2). No
  silent reinterpretation of `scopeId` — non-admin callers are
  rejected.
- My-path resolvers: reject anonymous callers, then resolve
  `current_user` and delegate to
  `UserAppConfigRepository.{create|update|soft_delete|restore}` —
  `scopeId` is not part of the input and is injected server-side.
- `DomainV2.appConfigs` field resolver: `check_admin_only()` at
  entry — raises a permission error (the helper in
  `src/ai/backend/manager/api/gql/utils.py` raises
  `web.HTTPForbidden`) for non-admin callers; does not silently
  return an empty Connection.
- `UserV2.appConfigs` field resolver: raises a permission error
  when the parent node's `user_id` differs from `current_user` and
  the caller is not an admin.

#### Name → ID resolution and ID-based Actions

The actions that implement search / update / mutate all operate on
the **row ID** internally — never on the raw natural key.
Resolution is one extra service-layer step before the RBAC check:

1. Resolve `(scope, scopeId, name)` → row `id` via the matching
   repository. This lookup is **permission-agnostic** — it only
   needs the natural key and may run for any caller. Returning an
   `id` for a row the caller cannot access is fine (see next step).
2. Run the RBAC check against the resolved `id` (using the standard
   RBAC plumbing that consumes scope + actor context).
3. Dispatch the ID-based Action (search, update, delete, restore,
   etc.) to the repository.

This keeps Actions themselves uniform (ID-only) while still
accepting natural-key identification at the API surface — clients
never need to know row IDs.

---

## 4. REST Schema — `/v2/app-configs/...`

Mounted under the existing `app-configs` prefix
(`RouteRegistry.create("app-configs", ...)` in
`src/ai/backend/manager/api/rest/v2/app_config/registry.py`), matching the project-wide v2
conventions in `src/ai/backend/manager/api/rest/v2/CLAUDE.md`.

### Endpoints

All scope-parameterized endpoints follow a single URL shape:
`/v2/app-configs/{scope_type}/{scope_id}[/{name}]`, where

- `{scope_type}` ∈ `public | domain | domain_user_defaults | user`
  (matches `AppConfigScopeType` in §1).
- `{scope_id}` follows the §1 Scope ID convention — the literal
  `"public"` for `public`, `domain_name` for `domain` /
  `domain_user_defaults`, `user_id` (UUID) for `user`.
- `{name}` is the document name.

Verbs map 1:1 onto the GQL mutations. `POST` / `PUT` accept a
`{ "config": ... }` JSON body (same shape as
`CreateAppConfigInput.config` / `UpdateAppConfigInput.config` in
§3); `GET` / `DELETE` / `POST .../restore` take no body.

| Method | Path                                                     | Description                                             |
|--------|----------------------------------------------------------|---------------------------------------------------------|
| GET    | `/v2/app-configs/{scope_type}/{scope_id}`                | List documents in a scope (`status=ALIVE` default)      |
| GET    | `/v2/app-configs/{scope_type}/{scope_id}/{name}`         | Read one document                                       |
| POST   | `/v2/app-configs/{scope_type}/{scope_id}/{name}`         | Create (strict insert; `409` if any row exists)         |
| PUT    | `/v2/app-configs/{scope_type}/{scope_id}/{name}`         | Replace (`404` if no `ALIVE` row)                       |
| DELETE | `/v2/app-configs/{scope_type}/{scope_id}/{name}`         | Soft-delete                                             |
| POST   | `/v2/app-configs/{scope_type}/{scope_id}/{name}/restore` | Restore (`DELETED → ALIVE`, value unchanged)            |

Authorization follows the §3 permission matrix and the
`input.key.scope` table — anonymous read is allowed only on
`scope_type=public` reads; writes to non-`user` scopes require
admin; for `scope_type=user`, admin or the owner
(`{scope_id} == current_user.user_id`).

Two shortcut endpoint families sit outside the scope-parameterized
shape:

| Method | Path                                | Access | Description                                            |
|--------|-------------------------------------|--------|--------------------------------------------------------|
| GET    | `/v2/app-configs/my[/{name}]`       | User   | List / read own documents (with merged result)         |
| POST   | `/v2/app-configs/my/{name}`         | User   | Create own document                                    |
| PUT    | `/v2/app-configs/my/{name}`         | User   | Replace own document                                   |
| DELETE | `/v2/app-configs/my/{name}`         | User   | Soft-delete own document                               |
| POST   | `/v2/app-configs/my/{name}/restore` | User   | Restore own soft-deleted document                      |
| POST   | `/v2/app-configs/search`            | Admin  | Cross-scope search — same body schema as `adminAppConfigs` |

`POST /v2/app-configs/search` accepts the same input schema as the
GQL `adminAppConfigs` field (`filter` / `orderBy` / pagination
arguments) in the request body and returns the same result.

> `/v2/app-configs/my/...` follows the `my_` self-service convention
> (`src/ai/backend/manager/api/rest/v2/CLAUDE.md`) — the adapter resolves `current_user()`
> internally and fixes `scope_id` to the caller's `user_id`. The
> body shape is the same `{ "config": ... }` as above (maps to
> the user row's `user_customized_config` internally); there is no
> input field that can target another user.

> Read endpoints filter to `status = ALIVE` by default. Revival
> goes through the dedicated `POST {path}/restore` action;
> `PUT`/`POST` on a soft-deleted natural key does *not* revive and
> instead errors (`404` for PUT since no ALIVE row, `409` for POST
> since a row already exists).

---

## 5. `MyAppConfig` — Merge policy

> The merge semantics described here apply **only to `MyAppConfig`
> (= the return type of `myAppConfigs`)**. `PublicAppConfig` /
> `DomainAppConfig` / `UserAppConfig` (raw USER row view) are read
> as-is — no cross-scope merge, no `mergedConfig` /
> `domainDefaultConfig` companion views, just the raw stored
> `extra_config` exposed as the single `config` field. `DOMAIN`-scope
> values are admin-only policy and **do not participate in the
> merge** — they are exposed only via admin paths.

### Storage

- `user_app_config.extra_config` (the DB column, exposed as
  `UserAppConfig.config` = `MyAppConfig.userCustomizedConfig`) stores
  **only the values the user has explicitly set** — for the named
  document.
- The domain-side merge input is a single scope:
  `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name, name=N)`
  (the admin-provided per-user default). Not copied into user rows —
  to avoid having to rewrite every user row when the admin edits the
  default.
- `DOMAIN`-scope rows are admin-enforced policy and **do not
  participate** in this merge — values users cannot override should
  never be mixed with `DOMAIN_USER_DEFAULTS` / `USER`. By convention
  `UserAppConfig` / `DomainUserDefaultsAppConfig` never carry
  DOMAIN-policy keys. Management and exposure of DOMAIN values are
  entirely via admin paths (`DomainV2.appConfigs` /
  `adminAppConfigs`).
- Domain-side values are applied **per-name**: the
  `DOMAIN_USER_DEFAULTS` row for a given `name` is the merge base
  for the same-`name` `USER` row's `userCustomizedConfig`. Different
  `name`s are independent.

### Read (Merge)

Merge is owned by `UserAppConfigRepository`, with DB access performed
in a single call to `AppConfigDBSource`'s merge-specific method —
**one SQL query** that reads `DOMAIN_USER_DEFAULTS` + `USER` in the
same snapshot. Bounded to at most 2 rows thanks to the natural-key
`UniqueConstraint`. For a given `(user_id, name)`:

1. Call `AppConfigDBSource.get_user_merged_config(user_id, name)` —
   a single SQL resolves the user's `domain_name` via a `users`
   subquery and pulls both source rows from `app_configs` together:
   - `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=<user's domain_name>, name=name)`
     → the per-user default.
   - `(scope_type=USER, scope_id=user_id, name=name)` → the user's
     customized value.
2. Deep-merge the rows, low → high priority:
   `domain_user_defaults ⊕ userCustomizedConfig`. Nested objects are
   merged recursively per key; at leaf keys the higher-priority value
   wins. Lists are treated as leaves and replaced wholesale by the
   higher-priority value (element-level array merge has no
   unambiguous semantics). The result is exposed as
   `MyAppConfig.mergedConfig`; each source row's raw `extra_config`
   is exposed as `MyAppConfig.domainDefaultConfig` /
   `MyAppConfig.userCustomizedConfig`. `MyAppConfig.updatedAt` is the
   max of the participating rows' `updatedAt`.

Since both rows are read inside a single read-only transaction,
callers never see a half-applied state from concurrent admin writes.

`DOMAIN`-scope rows are not read here — admin-enforced domain policy
is kept out of user-facing merge to avoid mixing with user defaults
and overrides. Management and reads go entirely through admin paths
(`DomainV2.appConfigs` / `adminAppConfigs` / `node(id)`).
`UserAppConfigRepository` therefore never reads DOMAIN rows, and no
non-admin user can peek at DOMAIN content via the merge path.

> Reading the `DOMAIN_USER_DEFAULTS` row for the merge is done
> entirely inside `AppConfigDBSource` — the single SQL resolves the
> caller's `domain_name` via a `users` subquery. No admin path is
> involved and this is not an authorization hole: users can only
> read their own domain's default, and only via the merge.

The Connection query (`myAppConfigs`) is backed by the search-specific
method on `AppConfigDBSource` — a single SQL applies filter /
pagination in the query and returns one merged result per `name` for
which at least one of the two scopes (`DOMAIN_USER_DEFAULTS`, `USER`)
has an `ALIVE` row.

```python
class AppConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_user_merged_config(
        self, user_id: str, name: str
    ) -> MergedAppConfig:
        # A single SQL resolves the caller's domain_name via a `users`
        # subquery and pulls both source rows (DOMAIN_USER_DEFAULTS on
        # that domain_name, USER on user_id) together — bounded to at
        # most 2 rows by the natural-key UniqueConstraint. DOMAIN is
        # admin-only policy and is intentionally excluded from the merge.
        user_domain_sq = (
            sa.select(UserRow.domain_name)
            .where(UserRow.id == sa.cast(user_id, sa.UUID))
            .scalar_subquery()
        )
        async with self._db.begin_readonly_session() as db_sess:
            rows = (await db_sess.execute(
                sa.select(AppConfigRow).where(
                    AppConfigRow.status == AppConfigStatus.ALIVE,
                    AppConfigRow.name == name,
                    sa.or_(
                        sa.and_(
                            AppConfigRow.scope_type
                                == AppConfigScopeType.DOMAIN_USER_DEFAULTS,
                            AppConfigRow.scope_id == user_domain_sq,
                        ),
                        sa.and_(
                            AppConfigRow.scope_type == AppConfigScopeType.USER,
                            AppConfigRow.scope_id == user_id,
                        ),
                    ),
                )
            )).scalars().all()

        by_scope = {row.scope_type: row for row in rows}
        domain_defaults_row = by_scope.get(AppConfigScopeType.DOMAIN_USER_DEFAULTS)
        user_row = by_scope.get(AppConfigScopeType.USER)

        domain_defaults = domain_defaults_row.extra_config if domain_defaults_row else None
        user_customized = user_row.extra_config if user_row else {}

        return MergedAppConfig(
            user_id=user_id,
            name=name,
            user_customized_config=user_customized,                 # MyAppConfig.userCustomizedConfig
            domain_default_config=domain_defaults,                  # MyAppConfig.domainDefaultConfig
            merged_config=deep_merge(                               # MyAppConfig.mergedConfig
                domain_defaults or {},
                user_customized,
            ),
            updated_at=max_updated_at([domain_defaults_row, user_row]),
        )

    async def search_user_merged_configs(
        self,
        user_id: str,
        filter: AppConfigFilter,
        pagination: Pagination,
    ) -> MergedAppConfigPage:
        # A single SQL resolves domain_name (users subquery) + pulls
        # ALIVE rows for both scopes (DOMAIN_USER_DEFAULTS, USER) —
        # same WHERE shape as `get_user_merged_config`, with the `name`
        # filter generalized to `filter`. Pagination uses `(name,
        # updated_at)` as a stable cursor key applied in SQL. Full
        # implementation lives in the §3 Connection resolver.
        ...


class UserAppConfigRepository:
    """
    Dual role: `USER` row CRUD (serving `UserAppConfig`) + read-side
    merged view (serving `MyAppConfig`). The merge path delegates to
    `AppConfigDBSource`'s merge-specific method, which reads two
    source rows in a single SQL while never touching DOMAIN. No
    separate `MyAppConfigRepository` — both roles live here.
    """

    _db_source: AppConfigDBSource

    def __init__(self, db_source: AppConfigDBSource) -> None:
        self._db_source = db_source

    # ── USER row CRUD (UserAppConfig) ─────────────────────────────

    async def get(self, user_id: str, name: str) -> AppConfigRow | None:
        return await self._db_source.get(
            AppConfigKey(AppConfigScopeType.USER, user_id, name)
        )

    async def get_by_id(self, id: uuid.UUID) -> AppConfigRow | None:
        return await self._db_source.get_by_id(id)

    async def create(
        self, user_id: str, name: str, extra_config: Mapping[str, Any]
    ) -> AppConfigRow:
        return await self._db_source.create(
            AppConfigKey(AppConfigScopeType.USER, user_id, name),
            extra_config,
        )

    async def update(
        self, user_id: str, name: str, extra_config: Mapping[str, Any]
    ) -> AppConfigRow:
        return await self._db_source.update(
            AppConfigKey(AppConfigScopeType.USER, user_id, name),
            extra_config,
        )

    async def soft_delete(self, user_id: str, name: str) -> AppConfigRow | None:
        return await self._db_source.soft_delete(
            AppConfigKey(AppConfigScopeType.USER, user_id, name)
        )

    async def restore(self, user_id: str, name: str) -> AppConfigRow:
        return await self._db_source.restore(
            AppConfigKey(AppConfigScopeType.USER, user_id, name)
        )

    async def search(
        self,
        user_id: str,
        filter: AppConfigFilter,
        pagination: Pagination,
    ) -> AppConfigPage:
        # Raw USER row search pinned to scope=USER + scope_id=user_id.
        return await self._db_source.search(
            scope_type=AppConfigScopeType.USER,
            scope_id=user_id,
            filter=filter,
            pagination=pagination,
        )

    # ── Merged view (MyAppConfig) ─────────────────────────────────
    # `AppConfigDBSource`'s merge-specific method already performs
    # the users-subquery resolution inside a single SQL, so the
    # repository here is a thin delegate.

    async def get_merged(self, user_id: str, name: str) -> MergedAppConfig:
        return await self._db_source.get_user_merged_config(user_id, name)

    async def search_merged(
        self,
        user_id: str,
        filter: AppConfigFilter,
        pagination: Pagination,
    ) -> MergedAppConfigPage:
        return await self._db_source.search_user_merged_configs(
            user_id, filter, pagination
        )
```

### Exposure

`MyAppConfig` exposes three views of the same logical document so
the WebUI can render and edit cleanly:

- `userCustomizedConfig` — what the user explicitly set (raw; `{}`
  when no USER row exists)
- `domainDefaultConfig` — the matching `DOMAIN_USER_DEFAULTS` row's
  raw `extra_config` — admin-provided per-user default (`null` when
  no row exists)
- `mergedConfig` — `domainDefaultConfig ⊕ userCustomizedConfig`,
  what the UI actually applies

The REST `GET /v2/app-configs/my/{name}` response carries the same
three views (snake_case: `user_customized_config`,
`domain_default_config`, `merged_config`).

`DOMAIN`-scope rows are not exposed through this view at all —
admins manage / read DOMAIN values via their dedicated path
(`DomainV2.appConfigs` / `adminAppConfigs` / REST
`/v2/app-configs/domain/...`).

---

## 6. Client Integration — WebUI bootstrap

The WebUI requests configs by addressing them explicitly with
`(scope, scopeId, name)`. The list of public documents the WebUI
must load before login is owned entirely by the frontend
(hard-coded or shipped in the WebUI bundle) — the server does not
publish a bootstrap list.

### Bootstrap flow

1. **Pre-login (anonymous)** — for each document the WebUI wants
   before login, it issues a `publicAppConfigs` query with a `name`
   filter (no auth). The `theme` / `branding` shapes are pulled via
   a single document fetch each — see S1 in §7. On no-edge /
   network error the WebUI falls back to its built-in defaults for
   that document.

2. **Post-login** — the WebUI issues a single `myAppConfigs` query
   to fetch *all* of the caller's user documents in one round trip.
   Each entry carries `userCustomizedConfig`, `domainDefaultConfig`,
   and the 2-way merged `mergedConfig` (§5). DOMAIN-scope policy
   does not participate in the merge, so an admin UI needing to
   inspect domain policy issues a separate `DomainV2.appConfigs` /
   `adminAppConfigs` query. See S2 in §7.

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
  publicAppConfigs(filter: { name: { equals: "theme" } }) {
    edges { node { name config updatedAt } }
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
        mergedConfig
        updatedAt
      }
    }
  }
  publicAppConfigs {
    edges { node { name config } }
  }
}
```

- Server: `myAppConfigs` returns one entry per `name` for which
  either source row (`USER`, `DOMAIN_USER_DEFAULTS` — keyed to the
  caller / caller's domain) is `ALIVE`. Rows that are absent
  contribute `{}` to the merge. `DOMAIN`-scope is excluded from the
  merge. Merge per §5.
- The WebUI initializes UI state from `mergedConfig` per document
  and keeps the raw views around so the Settings page can show
  user-changed vs. domain-default.

### S3. The user saves their own document

The user replaces their `preferences` document — e.g. language,
experimental-feature toggles, visible-column choices per table. They
call the self-service `updateMyAppConfig` — the input is just `name`
+ `config`, with `scope` / `scopeId` injected server-side as `USER`
+ `current_user.user_id`. The payload returns the recomputed
`MyAppConfig` (including the merged view), so no separate
`myAppConfigs` re-query is needed.

```graphql
mutation SaveMyConfig($input: UpdateMyAppConfigInput!) {
  updateMyAppConfig(input: $input) {
    myAppConfig {
      name
      userCustomizedConfig
      domainDefaultConfig
      mergedConfig
      updatedAt
    }
  }
}
```

```json
{
  "input": {
    "name": "preferences",
    "config": {
      "language": "ko",
      "experimentalFeatures": { "multiNodeScheduler": true }
    }
  }
}
```

- Authorization: authenticated user. The server injects `scopeId =
  current_user.user_id`, so the mutation cannot touch another user's
  row (admins operating on other users use `adminUpdateAppConfig`).
- The input `config` replaces the USER row's `userCustomizedConfig`
  wholesale. `MyAppConfig.mergedConfig` is read-only computed and
  cannot be written.
- **Replace** semantics: anything the caller wants to keep must be
  sent in the same payload — there is no partial-merge or per-key
  patch.
- **First write vs. subsequent writes**: `updateMyAppConfig` errors
  if no `ALIVE` USER row exists. For the very first save of a given
  `name`, the client calls `createMyAppConfig` with the same shape
  (after a soft-delete, use `restoreMyAppConfig` followed by
  `updateMyAppConfig`). Clients can disambiguate by checking whether
  the `myAppConfigs` entry for that `name` already has a
  `userCustomizedConfig`.

### S4. Admin publishes a per-user default for a domain

The domain admin publishes a new `theme` document that every user
in the domain inherits as the merge base — `theme` is admin-only
per the user stories, so this is the only path by which the
domain's theme reaches users. The first publish uses
`adminCreateAppConfig` with `key.scope = DOMAIN_USER_DEFAULTS`;
later edits on the same document use `adminUpdateAppConfig` with
the identical input shape. `DOMAIN`-scope publishes
(admin-enforced policy, e.g. a domain-internal config document) use
the same mutations with `key.scope = DOMAIN` — but note that DOMAIN
values are not included in the `myAppConfigs` merge, so any
document users must be able to read should be published under
`DOMAIN_USER_DEFAULTS` instead.

```graphql
mutation AdminCreateAppConfig($input: AdminCreateAppConfigInput!) {
  adminCreateAppConfig(input: $input) {
    appConfig { id scope scopeId name status config updatedAt }
  }
}
```

```json
{
  "input": {
    "key": {
      "scope": "DOMAIN_USER_DEFAULTS",
      "scopeId": "default",
      "name": "theme"
    },
    "config": {
      "mode": "dark",
      "accent": "#6f5ae8"
    }
  }
}
```

- Authorization: admin required — the service rejects non-admin
  calls on any admin-path mutation.
- Internally, the service routes to the matching repository (§2)
  and strictly inserts a new `ALIVE` row. Errors if any row (ALIVE
  or DELETED) already exists for the key — the admin either uses
  `adminUpdateAppConfig` (when ALIVE) or `adminRestoreAppConfig`
  (when DELETED) instead.
- Effect: every user in the domain picks up the new defaults on the
  next `myAppConfigs` read (merged per §5).

### S5. Admin seeds a specific user's document on their behalf

For a support request, an admin seeds user A's `preferences`
`userCustomizedConfig` for the first time. Since the target is
another user's row, this must use the admin path —
`adminCreateAppConfig` with `key.scope = USER` and `key.scopeId =
user A's user_id`, not the self-service `createMyAppConfig`.
`create` errors if user A already has a `preferences` row (ALIVE
or DELETED), in which case the admin falls back to
`adminUpdateAppConfig` (when ALIVE) or `adminRestoreAppConfig`
(when DELETED) with the same input shape.
`MyAppConfig.mergedConfig` is always read-only computed and cannot
be written directly.

```graphql
mutation AdminCreateAppConfigForUser($input: AdminCreateAppConfigInput!) {
  adminCreateAppConfig(input: $input) {
    appConfig { id scope scopeId name status config updatedAt }
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
    "config": { "experimentalFeatures": { "multiNodeScheduler": true } }
  }
}
```

- For `USER` scope the `config` input is stored as that user's
  `userCustomizedConfig`.
- `adminCreateAppConfig` does *not* revive a `DELETED` row — that
  is what `adminRestoreAppConfig` is for; `create` errors on any
  pre-existing row regardless of status.
- The response is the raw `AppConfig`; the target user's merged
  view reflects the new `userCustomizedConfig` (merged with the
  matching domain defaults) on the next `myAppConfigs` read from
  that user's session.

### S6. Admin audits all AppConfigs (cross-scope search)

Cases such as "list every domain that touched `theme` in the last
week" or "every domain that customized the `menu` document":

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
      node { id scope scopeId name status config updatedAt }
    }
    pageInfo { hasNextPage endCursor }
    count
  }
}
```

```json
{
  "filter": {
    "scope": { "in": ["DOMAIN", "DOMAIN_USER_DEFAULTS"] },
    "name": { "equals": "theme" },
    "updatedAt": { "gte": "2026-04-14T00:00:00Z" }
  },
  "orderBy": [{ "field": "UPDATED_AT", "direction": "DESC" }],
  "first": 50
}
```

- Server: service-layer admin check → Connection search. In cursor
  mode the sort order is pinned to the cursor key. By default
  returns `ALIVE` rows only — pass `filter.status` to include
  `DELETED` rows.

### S7. Operator removes an entire document (soft-delete)

Removing a stale or deprecated document — e.g. retiring an old
`legacy_menu` document for a domain:

```graphql
mutation RemoveDomainLegacyMenu($input: AdminDeleteAppConfigInput!) {
  adminDeleteAppConfig(input: $input) {
    appConfig { id scope scopeId name status updatedAt }
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

- Authorization: admin required (every `admin*AppConfig` mutation
  is admin-only).
- Service flips `status = DELETED` on the matching row. Subsequent
  reads (`DomainV2.appConfigs`, `UserV2.appConfigs`,
  `adminAppConfigs`, etc.) hide the document.
- **Idempotent**: no-op when the row is absent or already `DELETED`.
- **Recoverable**: `adminRestoreAppConfig` on the same `key` flips
  the row back to `ALIVE` with its stored value unchanged. To change
  the value after restoring, chain an `adminUpdateAppConfig` call.
  `adminCreateAppConfig` does *not* revive — it errors on any
  pre-existing row.

A user removing their own document uses the self-service
`deleteMyAppConfig` — just `name` in the input; the server injects
`scope = USER` + `scopeId = current_user.user_id`. The payload
returns the recomputed `MyAppConfig` reflecting what remains
(`DOMAIN_USER_DEFAULTS` only), or `null` if no ALIVE source remains
for that `name`.

```graphql
mutation RemoveMyConfig($input: DeleteMyAppConfigInput!) {
  deleteMyAppConfig(input: $input) {
    myAppConfig {
      name
      userCustomizedConfig
      domainDefaultConfig
      mergedConfig
      updatedAt
    }
  }
}
```

```json
{ "input": { "name": "preferences" } }
```
