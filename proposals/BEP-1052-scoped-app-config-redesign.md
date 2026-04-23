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

| Story                                               | Scope                  | Read                            | Write       |
|-----------------------------------------------------|------------------------|---------------------------------|-------------|
| Theme, Branding (must work before login)            | `public`               | Anyone                          | Admin       |
| UI hide/show, menu config                           | `domain`               | Logged-in users (same domain)   | Admin       |
| Per-user preference defaults (per-domain)           | `domain_user_defaults` | Logged-in users (same domain)   | Admin       |
| Per-user personal settings                          | `user`                 | Owner/Admin                     | Owner/Admin |

> Difference between `domain` and `domain_user_defaults`: both are
> admin-write and readable by users of the domain, but only
> `domain_user_defaults` participates in the `myAppConfigs` merge as
> a base. Use `domain_user_defaults` for values a user can override
> in their own USER row; use `domain` for values that must not be
> user-overridable — see §5 for the full merge rules.

## Design Principles

- **Schema-less JSON**: the backend is purely a storage layer; the
  structure and meaning of the configuration are owned by the frontend.
- **Scope = Entity**: access control is expressed at the scope (entity)
  level, not the field level.
  `public_app_config` (Anonymous read / Admin write),
  `domain_app_config` (same-domain users read / Admin write),
  `domain_user_defaults_app_config` (same-domain users read, merge
  base participant / Admin write),
  `user_app_config` (Owner/Admin read / Owner-self + Admin write).
- **Named documents within a scope**: each row is identified by the
  natural composite key `(scope_type, scope_id, name)`. A scope can hold
  any number of named documents; clients address them explicitly by
  name (no hierarchical fall-through lookup).
- **All writes are bulk-only.** There are no single-item mutations —
  callers pass a list (even a 1-element list for a single write) and
  get a partial-success payload back. The same four verbs
  (`create` / `update` / `delete` / `restore`) are exposed
  symmetrically as admin-path mutations (`adminBulkCreateAppConfigs`, etc.
  — every scope, admin-only, return lists of raw `AppConfig`) and
  self-service path mutations (`bulkCreateMyAppConfigs`, etc. — `USER` +
  `current_user` implicit, any authenticated user on their own rows,
  return lists of merged `MyAppConfig`). `create` strictly inserts
  (per-item failure if any row exists for the key, soft-deleted
  included); `update` replaces an existing `ALIVE` row's stored JSON
  wholesale; `delete` soft-deletes (`ALIVE → DELETED`); `restore` is
  the explicit inverse of delete (`DELETED → ALIVE`, value unchanged).
  No partial update / deep-merge / key-level removal / upsert at the
  write boundary. Each item runs in its own transaction so one
  failure does not abort the rest. Identification uses the
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

### `name` format constraint

`name` is restricted to alphanumeric + `_`, `-`, `.` (regex:
`^[A-Za-z0-9_.\-]+$`, length 1–128). Reasons:
- Fits directly in REST URL path segments (`/v2/app-configs/.../{name}`)
  without escaping.
- Avoids collision with the `:` delimiter used in the
  `MyAppConfig.id` encoding (`base64("MyAppConfig:{user_id}:{name}")`).
- Keeps log / audit trails compact.

Validation runs both at `AppConfigKey` construction (`__post_init__`)
and at the service-layer entry point.

### Status filtering

All read paths filter `status = ALIVE` by default. Callers can
opt into seeing `DELETED` rows by passing an explicit status
filter on Connections that expose one (`AppConfigFilter.status`
in GraphQL — see §3) or the equivalent REST query parameter — this
is used for admin recovery / audit flows and for checking whether a
name is reusable after deletion. Revival uses the dedicated
`adminBulkRestoreAppConfigs` / `bulkRestoreMyAppConfigs` mutations, which flip
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
| `UserAppConfigRepository`               | CRUD: `get / get_by_id / create / update / soft_delete / restore / search` (all take `user_id` + `name`). Plus merge-specific: `get_merged(user_id, name)`, `search_merged(user_id, filter)` — see the note below for roles. |

`DomainUserDefaultsAppConfigRepository` mirrors
`DomainAppConfigRepository` (admin write + same-domain user read,
same call shape) but operates on
`(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name)` rows.
Splitting it from `DomainAppConfigRepository` keeps each repository
mapped to exactly one scope, matching the rest of the layout.

`UserAppConfigRepository` plays a **dual role** — raw `USER` row CRUD
(serving `UserAppConfig`) + read-side merged view (serving
`MyAppConfig`, see §5). It takes a single `AppConfigDBSource` like
the other scope repositories; the user → domain_name resolution
needed by the merge is done inside the merge-specific DB method via a
`users` subquery in a single SQL, so no separate `UserDBSource` is
injected at the repository level. The GraphQL schema exposes
`UserAppConfig` (raw) and `MyAppConfig` (merged) as separate types,
but internally they share one repository — there is no
`MyAppConfigRepository`.

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

    async def search(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
        filter: AppConfigFilter,
        pagination: Pagination,
    ) -> AppConfigPage:
        # Within-scope search — bound to (scope_type, scope_id) and
        # applies filter / pagination in SQL. Cross-scope search has
        # a separate `admin_search(filter, pagination)` overload
        # (omitted). The merge-specific search lives in §5.
        async with self._db.begin_readonly_session() as db_sess:
            ...   # default status = ALIVE, extendable via filter.status
```

Listing is expressed via the `search` primitive — each scope
repository's `search(...)` is a thin-delegate that binds
`scope_type` / `scope_id`. Permission checks and scope validation
are performed in the service layer.

**Bulk mutation orchestration**: all eight bulk mutations
(`adminBulk{Create,Update,Delete,Restore}AppConfigs`,
`bulk{Create,Update,Delete,Restore}MyAppConfigs`) follow the same
service-layer orchestration — each item runs in its own DB
transaction so a single failure doesn't abort the rest
(partial success), successes and failures collected into
`BulkActionResult(success_list, failed_list)`. Admin bulk dispatches
each item on `item.key.scopeType` to the matching scope repository; my
bulk dispatches directly to `UserAppConfigRepository`. Not optimized
as a single SQL batch: items split by scope can fail for
heterogeneous reasons (unique-key violations, authorization
errors, …), and representing partial success in one SQL statement
is awkward.

`AppConfigFilter` / `AppConfigPage` / `Pagination` are internal
containers at the repository / service layer — Python dataclasses
corresponding to the GraphQL `AppConfigFilter`, intentionally
left unspecified here (defined in a small companion module at
implementation time).

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
accessible via `myAppConfigs` or `node(id)`. Deep-merges same-`name`
`(DOMAIN_USER_DEFAULTS, user.domain_name)` and
`(USER, user.user_id)` (DOMAIN is admin policy and excluded — see
§5). An entry appears whenever at least one is `ALIVE`; without a
USER row, `userCustomizedConfig` is returned as `{}`.

Although derived, `MyAppConfig` implements `Node` — the `(user_id,
name)` composite is encoded as a server-side global ID
(`base64("MyAppConfig:{user_id}:{name}")`). The `node(id)` resolver
decodes the id and returns the merged view only when
`decoded.user_id == current_user.id` or the caller is admin.
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
  Read access: same-domain users or admin. Write (via mutations) is
  admin only. Filter by `name` (or any combination) to retrieve a
  single document. `filter.scopeType` / `filter.scopeId` are ignored —
  already pinned to this domain.
  """
  appConfigs(
    filter: AppConfigFilter = null
    orderBy: [AppConfigOrderBy!] = null
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
  Filter by `name` to retrieve a single document. `filter.scopeType` /
  `filter.scopeId` are ignored — already pinned to this user.
  """
  appConfigs(
    filter: AppConfigFilter = null
    orderBy: [AppConfigOrderBy!] = null
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
    filter: AppConfigFilter = null
    orderBy: [AppConfigOrderBy!] = null
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
  retrieve a single document. `filter.scopeType` / `filter.scopeId` /
  `filter.status` are ignored here — the scope is pinned, and only
  `ALIVE` rows participate in the merge.
  """
  myAppConfigs(
    filter: AppConfigFilter = null
    orderBy: [AppConfigOrderBy!] = null
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
    filter: AppConfigFilter = null
    orderBy: [AppConfigOrderBy!] = null
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

Filter and orderBy types are unified — a single `AppConfigFilter`
and `AppConfigOrderBy` are reused across all Connections (admin
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
input AppConfigFilter {
  """
  Filter by scope type. Meaningful only on `adminAppConfigs`; on
  per-scope Connections (`publicAppConfigs`, `DomainV2.appConfigs`,
  `UserV2.appConfigs`, `myAppConfigs`) the scope
  is already pinned by the field, so this filter is ignored.
  """
  scopeType: AppConfigScopeTypeEnumFilter = null

  """
  Exact match on `scope_id`. Same constraint as `scopeType` above —
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
  is reusable after deletion. Ignored on `myAppConfigs` — the merge
  only uses `ALIVE` rows.
  """
  status: AppConfigStatusEnumFilter = null

  """All sub-filters must match (AND combination)."""
  AND: [AppConfigFilter!] = null

  """At least one sub-filter must match (OR combination)."""
  OR: [AppConfigFilter!] = null

  """None of the sub-filters may match (NOT combination)."""
  NOT: [AppConfigFilter!] = null
}

"""EnumFilter for AppConfigScopeType (equals / in / notEquals / notIn)."""
input AppConfigScopeTypeEnumFilter {
  equals: AppConfigScopeType
  in: [AppConfigScopeType!]
  notEquals: AppConfigScopeType
  notIn: [AppConfigScopeType!]
}

"""EnumFilter for AppConfigStatus (equals / in / notEquals / notIn)."""
input AppConfigStatusEnumFilter {
  equals: AppConfigStatus
  in: [AppConfigStatus!]
  notEquals: AppConfigStatus
  notIn: [AppConfigStatus!]
}

input AppConfigOrderBy {
  field: AppConfigOrderField!
  direction: OrderDirection! = ASC
}

"""
`SCOPE_TYPE` / `SCOPE_ID` are only useful on `adminAppConfigs`; on
per-scope Connections they degenerate to a constant and have no
effect. `UPDATED_AT` / `CREATED_AT` apply to raw-row Connections
only — `myAppConfigs` returns `MyAppConfig` (derived) which does
not expose timestamps, so these order keys fall back to `NAME`
internally in that context.
"""
enum AppConfigOrderField {
  SCOPE_TYPE
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

All write mutations are **bulk-only** — there are no single-item
variants (pass a 1-element array if you only need one). Split into an
**admin path** and a **self-service (my) path**, four verbs each for a
total of eight mutations:

- `adminBulk*AppConfigs` (4): each item carries an
  `AppConfigKey { scope, scopeId, name }` — covers every scope.
  **Admin-only**. Returns a list of raw `AppConfig` + a list of
  per-item failures.
- `bulk*MyAppConfigs` (4): each item carries only `name` (scope is
  `USER` + `scopeId = current_user.user_id` injected server-side).
  Callable by any authenticated user for their own documents. Returns
  a list of recomputed `MyAppConfig` + a list of per-item failures.

**Partial success**: every bulk mutation runs each item in its own
DB transaction — a single failure does not abort the rest, and the
payload separates successes from failures. Single-item callers get
the same shape, so error handling is uniform.

Routing:
- Admin-path: the service dispatches on each item's `key.scopeType` and
  routes to the matching scope repository (§2). Items across
  different scopes may be mixed in one call.
- My-path: the server synthesizes
  `(USER, current_user.id, item.name)` and calls
  `UserAppConfigRepository` directly (no natural-key resolve step).

Authorization is enforced in the **service layer** (see permission
matrix below).

```graphql
type Mutation {
  # ── Admin path — every scope, admin-only ─────────────────────

  """
  Bulk-create app config documents (admin-only). Each item is a
  strict insert — if any row already exists for the natural key
  (ALIVE or DELETED), that item fails (revival is
  `adminBulkRestoreAppConfigs`). Items may target any scope; admin-side
  seeding of a `USER`-scope row is also done via this mutation.
  """
  adminBulkCreateAppConfigs(input: AdminBulkCreateAppConfigInput!): AdminBulkCreateAppConfigsPayload!

  """
  Bulk-update app config documents (admin-only). Each item replaces
  the existing `ALIVE` row's stored JSON wholesale. If no `ALIVE`
  row exists for the natural key (missing or `DELETED`), that item
  fails.
  """
  adminBulkUpdateAppConfigs(input: AdminBulkUpdateAppConfigInput!): AdminBulkUpdateAppConfigsPayload!

  """
  Bulk soft-delete app config documents (`status = DELETED`,
  admin-only). Rows are preserved for audit and can be brought
  back by calling `adminBulkRestoreAppConfigs` on the same keys. Items
  whose row is missing or already `DELETED` are included in
  `deleted` as silent no-ops (idempotent).
  """
  adminBulkDeleteAppConfigs(input: AdminBulkDeleteAppConfigInput!): AdminBulkDeleteAppConfigsPayload!

  """
  Bulk restore soft-deleted app config documents (`DELETED → ALIVE`,
  admin-only). Stored values are preserved as-is — to change them,
  follow up with `adminBulkUpdateAppConfigs`. Items whose row is missing
  or already `ALIVE` fail.
  """
  adminBulkRestoreAppConfigs(input: AdminBulkRestoreAppConfigInput!): AdminBulkRestoreAppConfigsPayload!

  # ── Self-service (my) path — USER + current_user implicit ────

  """
  Bulk-create the current user's `USER`-scope documents (auth
  required). Each item has `name` + `config`;
  `scopeId = current_user.user_id` is injected server-side. Strict
  insert — if an `ALIVE` or `DELETED` USER row already exists for a
  `name`, that item fails (revival is `bulkRestoreMyAppConfigs`).
  """
  bulkCreateMyAppConfigs(input: BulkCreateMyAppConfigInput!): BulkCreateMyAppConfigsPayload!

  """
  Bulk-replace the current user's `USER`-scope documents (auth
  required). Items whose `ALIVE` USER row is missing fail.
  """
  bulkUpdateMyAppConfigs(input: BulkUpdateMyAppConfigInput!): BulkUpdateMyAppConfigsPayload!

  """
  Bulk soft-delete the current user's `USER`-scope documents (auth
  required). Each matching USER row flips to `DELETED` and the
  payload includes the recomputed `MyAppConfig` (reflecting any
  remaining `DOMAIN_USER_DEFAULTS`, or `null` if no source remains).
  Idempotent.
  """
  bulkDeleteMyAppConfigs(input: BulkDeleteMyAppConfigInput!): BulkDeleteMyAppConfigsPayload!

  """
  Bulk restore the current user's soft-deleted USER documents
  (`DELETED → ALIVE`). Stored values are preserved — to change them,
  follow up with `bulkUpdateMyAppConfigs`. Items whose row is missing
  or already `ALIVE` fail.
  """
  bulkRestoreMyAppConfigs(input: BulkRestoreMyAppConfigInput!): BulkRestoreMyAppConfigsPayload!
}

enum AppConfigScopeType {
  PUBLIC
  DOMAIN
  DOMAIN_USER_DEFAULTS
  USER
}

enum AppConfigStatus {
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
  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
}

# ── Admin Inputs — per-item + bulk wrappers ──────────────────

"""Per-item input for admin bulk create/update (key + config)."""
input AdminAppConfigItemInput {
  """Target row identifier."""
  key: AppConfigKey!

  """
  Stored value — initial on create, wholesale replacement on update.
  Pass `{}` to clear.
  - `PUBLIC` / `DOMAIN` / `DOMAIN_USER_DEFAULTS`: the document's `config`.
  - `USER`: that user's `userCustomizedConfig` (merged view is
    read-only computed).
  """
  config: JSON!
}

input AdminBulkCreateAppConfigInput {
  """Items to create. No schema-level cap; service applies a reasonable one."""
  items: [AdminAppConfigItemInput!]!
}

input AdminBulkUpdateAppConfigInput {
  """Items to update."""
  items: [AdminAppConfigItemInput!]!
}

input AdminBulkDeleteAppConfigInput {
  """Natural keys of the rows to soft-delete."""
  keys: [AppConfigKey!]!
}

input AdminBulkRestoreAppConfigInput {
  """Natural keys of the rows to restore."""
  keys: [AppConfigKey!]!
}

# ── My Inputs — scope=USER, scopeId=current_user.user_id implicit ──

"""Per-item input for my bulk create/update (name + config)."""
input MyAppConfigItemInput {
  """Document name (unique within the current user)."""
  name: String!

  """
  `userCustomizedConfig` value — initial on create, wholesale
  replacement on update. Pass `{}` to clear.
  `MyAppConfig.mergedConfig` is read-only computed and cannot be
  written.
  """
  config: JSON!
}

input BulkCreateMyAppConfigInput {
  """Items to create."""
  items: [MyAppConfigItemInput!]!
}

input BulkUpdateMyAppConfigInput {
  """Items to update."""
  items: [MyAppConfigItemInput!]!
}

input BulkDeleteMyAppConfigInput {
  """Document names to soft-delete."""
  names: [String!]!
}

input BulkRestoreMyAppConfigInput {
  """Document names to restore."""
  names: [String!]!
}

# ── Admin Payloads — return lists of raw AppConfig ───────────

"""
Per-item error info for a failed item in an admin bulk write.
Shared by all four admin bulk mutations.
"""
type AdminAppConfigError {
  """Scope of the failed item."""
  scopeType: AppConfigScopeType!

  """Scope ID of the failed item."""
  scopeId: String!

  """Name of the failed item."""
  name: String!

  """Error message describing the failure."""
  message: String!
}

"""Result of `adminBulkCreateAppConfigs`. Partial success."""
type AdminBulkCreateAppConfigsPayload {
  """Successfully created rows."""
  created: [AppConfig!]!

  """Per-item errors for entries that failed to create."""
  failed: [AdminAppConfigError!]!
}

"""Result of `adminBulkUpdateAppConfigs`. Partial success."""
type AdminBulkUpdateAppConfigsPayload {
  """Rows after replacement."""
  updated: [AppConfig!]!

  """Per-item errors for entries that failed to update."""
  failed: [AdminAppConfigError!]!
}

"""Result of `adminBulkDeleteAppConfigs`. Partial success."""
type AdminBulkDeleteAppConfigsPayload {
  """Rows transitioned to (or already at) `status = DELETED`."""
  deleted: [AppConfig!]!

  """Per-item errors for entries that failed to delete."""
  failed: [AdminAppConfigError!]!
}

"""Result of `adminBulkRestoreAppConfigs`. Partial success."""
type AdminBulkRestoreAppConfigsPayload {
  """Rows restored to `status = ALIVE` (stored value unchanged)."""
  restored: [AppConfig!]!

  """Per-item errors for entries that failed to restore."""
  failed: [AdminAppConfigError!]!
}

# ── My Payloads — return lists of merged MyAppConfig ────────

"""
Per-item error info for a failed item in a my bulk write. Shared by
all four my bulk mutations. (scope / scopeId are server-injected, so
`name` is the only identifier.)
"""
type MyAppConfigError {
  """Name of the failed item."""
  name: String!

  """Error message describing the failure."""
  message: String!
}

"""Result of `bulkCreateMyAppConfigs`. Partial success."""
type BulkCreateMyAppConfigsPayload {
  """Recomputed `MyAppConfig` list after the writes."""
  created: [MyAppConfig!]!

  """Per-item errors for entries that failed to create."""
  failed: [MyAppConfigError!]!
}

"""Result of `bulkUpdateMyAppConfigs`. Partial success."""
type BulkUpdateMyAppConfigsPayload {
  """Recomputed `MyAppConfig` list after the writes."""
  updated: [MyAppConfig!]!

  """Per-item errors for entries that failed to update."""
  failed: [MyAppConfigError!]!
}

"""
Per-item bulk-delete result — recomputed view after the USER row is
soft-deleted.
"""
type DeletedMyAppConfigResult {
  """Name of the deleted document."""
  name: String!

  """
  Recomputed `MyAppConfig` after the USER row was soft-deleted
  (reflecting any remaining `DOMAIN_USER_DEFAULTS`). `null` if no
  ALIVE source remains for this name.
  """
  myAppConfig: MyAppConfig
}

"""Result of `bulkDeleteMyAppConfigs`. Partial success."""
type BulkDeleteMyAppConfigsPayload {
  """Per-item results (name + optional recomputed view)."""
  deleted: [DeletedMyAppConfigResult!]!

  """Per-item errors for entries that failed to delete."""
  failed: [MyAppConfigError!]!
}

"""Result of `bulkRestoreMyAppConfigs`. Partial success."""
type BulkRestoreMyAppConfigsPayload {
  """Recomputed `MyAppConfig` list after restore."""
  restored: [MyAppConfig!]!

  """Per-item errors for entries that failed to restore."""
  failed: [MyAppConfigError!]!
}

"""
Generic AppConfig type shared by the admin-path payloads,
`adminAppConfigs`, and `node(id)`. Exposes the raw stored value.
"""
type AppConfig implements Node {
  """
  Relay global ID — `base64("AppConfig:<row_uuid>")`. The distinct
  prefix lets `node(id)` dispatch correctly between `AppConfig` and
  `MyAppConfig`.
  """
  id: ID!

  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
  status: AppConfigStatus!

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

| Operation                       | Anonymous | User                             | Admin |
|---------------------------------|-----------|----------------------------------|-------|
| `publicAppConfigs`              | ✅        | ✅                               | ✅    |
| `myAppConfigs`                  | ❌        | ✅ (self)                        | ✅    |
| `DomainV2.appConfigs`           | ❌        | ✅ (same domain only)            | ✅    |
| `UserV2.appConfigs`             | ❌        | ✅ (self)                        | ✅    |
| `adminAppConfigs`               | ❌        | ❌                               | ✅    |
| `node(id)` → `AppConfig`        | ❌        | ❌                               | ✅    |
| `node(id)` → `MyAppConfig`      | ❌        | ✅ (id's `user_id` is self)      | ✅    |
| `node(id)` → `PublicAppConfig`  | ✅        | ✅                               | ✅    |
| `node(id)` → `DomainAppConfig`  | ❌        | ✅ (same-domain rows only)       | ✅    |
| `node(id)` → `UserAppConfig`    | ❌        | ✅ (self)                        | ✅    |

Write mutations split into two paths with distinct rules. All
bulk-only.

**Admin path** — `adminBulkCreateAppConfigs`, `adminBulkUpdateAppConfigs`,
`adminBulkDeleteAppConfigs`, `adminBulkRestoreAppConfigs`. Admin regardless
of each item's `key.scopeType`:

| Operation              | Anonymous | User | Admin |
|------------------------|-----------|------|-------|
| `adminBulk*AppConfigs`     | ❌        | ❌   | ✅    |

**Self-service (my) path** — `bulkCreateMyAppConfigs`,
`bulkUpdateMyAppConfigs`, `bulkDeleteMyAppConfigs`, `bulkRestoreMyAppConfigs`.
Imply `scope = USER` + `scopeId = current_user.user_id`:

| Operation              | Anonymous | User (self) | Admin (self) |
|------------------------|-----------|-------------|--------------|
| `bulk*MyAppConfigs`        | ❌        | ✅          | ✅           |

> Admins operating on another user's `USER` row must use the admin
> path with an explicit `AppConfigKey { scope: USER, scopeId:
> target_user_id, name }` on each item — the my path cannot target
> another user.

Where the checks live:
- Admin-path resolvers: `check_admin_only()` at entry, then dispatch
  each item on `item.key.scopeType` to the matching repository (§2). No
  silent reinterpretation of `scopeId` — partial-success means some
  items may succeed while others fail, but non-admin callers are
  rejected up-front.
- My-path resolvers: reject anonymous callers, then resolve
  `current_user` and delegate each item to
  `UserAppConfigRepository.{create|update|soft_delete|restore}` —
  `scopeId` is not part of the input and is injected server-side.
- `DomainV2.appConfigs` field resolver: if the caller is not admin
  and the parent `DomainV2.domain_name` differs from
  `current_user.domain_name`, raise a permission error (helper in
  `src/ai/backend/manager/api/gql/utils.py` raises
  `web.HTTPForbidden`). Same-domain users and admins are allowed
  through. Writes (mutations) remain admin-only.
- `UserV2.appConfigs` field resolver: raises a permission error
  when the parent node's `user_id` differs from `current_user` and
  the caller is not an admin.

#### Name → ID resolution and ID-based Actions

**Admin path only.** The actions implementing the admin-path
mutations operate on the **row ID** internally — never on the raw
natural key. For each item of a bulk input:

1. Resolve `(scope, scopeId, name)` → row `id` via the matching
   repository. This lookup is **permission-agnostic** — it only
   needs the natural key and may run for any caller. Returning an
   `id` for a row the caller cannot access is fine (see next step).
2. Run the RBAC check against the resolved `id` (using the standard
   RBAC plumbing that consumes scope + actor context).
3. Dispatch the ID-based Action (update, delete, restore, etc.) to
   the repository. A failure on this item lands in `failed` while
   the remaining items continue.

My-path mutations (`bulkCreateMyAppConfigs`, etc.) **skip this step**:
scope / scopeId are fixed server-side (`USER`,
`current_user.user_id`), RBAC only needs to confirm "authenticated
self", and each item calls
`UserAppConfigRepository.{create|update|soft_delete|restore}` with
`user_id` + `item.name` directly.

The result: admin-path Actions stay uniform (ID-only) while the API
surface still accepts natural-key identification — clients never
need to know row IDs.

---

## 4. REST Schema — `/v2/app-configs/...`

Mounted under the existing `app-configs` prefix
(`RouteRegistry.create("app-configs", ...)` in
`src/ai/backend/manager/api/rest/v2/app_config/registry.py`), matching the project-wide v2
conventions in `src/ai/backend/manager/api/rest/v2/CLAUDE.md`.

### Endpoints

REST mirrors the GQL admin / my split — the scope-parameterized
path handles **admin writes + per-scope read rules** (maps to GQL
`adminBulk*AppConfigs` mutations and the scoped queries), and the `/my`
path is **self-only** (maps to GQL `bulk*MyAppConfigs` mutations).

#### Scope-parameterized path — admin writes / per-scope reads

```
/v2/app-configs/{scope_type}/{scope_id}[/{name}]
```

- `{scope_type}` ∈ `public | domain | domain_user_defaults | user`
  (matches `AppConfigScopeType` in §1).
- `{scope_id}` follows the §1 Scope ID convention — the literal
  `"public"` for `public`, `domain_name` for `domain` /
  `domain_user_defaults`, `user_id` (UUID) for `user`.
- `{name}` is the document name (§1 format constraint).

Reads (`GET`) go through the scope-parameterized path — writes are
handled exclusively via the bulk endpoints (see "Admin bulk" / "My
bulk" below).

| Method | Path                                             | Description                                        |
|--------|--------------------------------------------------|----------------------------------------------------|
| GET    | `/v2/app-configs/{scope_type}/{scope_id}`        | List documents in a scope (`status=ALIVE` default) |
| GET    | `/v2/app-configs/{scope_type}/{scope_id}/{name}` | Read one document                                  |

Read permissions per-scope match the GQL permission matrix:
- `/v2/app-configs/public/public[/{name}]` — anonymous allowed.
- `/v2/app-configs/domain/{domain_name}[/{name}]` — admin or the
  caller whose `current_user.domain_name == {domain_name}`.
- `/v2/app-configs/domain_user_defaults/{domain_name}[/{name}]` —
  same.
- `/v2/app-configs/user/{user_id}[/{name}]` — admin or the caller
  whose `current_user.user_id == {user_id}`.

#### My path — self-only (auth required)

The adapter resolves `current_user()` internally and pins
`scope=USER` + `scope_id = current_user.user_id`. There is no input
field capable of targeting another user.

| Method | Path                                | Description                             |
|--------|-------------------------------------|-----------------------------------------|
| GET    | `/v2/app-configs/my[/{name}]`       | List / read own documents (merged view) |

Writes use the "My bulk" endpoints below.

Response body is the **merged MyAppConfig** (snake_case projection
of the GQL `MyAppConfig`):

```json
{
  "name": "preferences",
  "user_customized_config": { ... },
  "domain_default_config": { ... } | null,
  "merged_config": { ... }
}
```

#### Admin writes (bulk-only)

| Method | Path                              | Access | Maps to                         |
|--------|-----------------------------------|--------|---------------------------------|
| POST   | `/v2/app-configs/bulk-create`     | Admin  | `adminBulkCreateAppConfigs`         |
| POST   | `/v2/app-configs/bulk-update`     | Admin  | `adminBulkUpdateAppConfigs`         |
| POST   | `/v2/app-configs/bulk-delete`     | Admin  | `adminBulkDeleteAppConfigs`         |
| POST   | `/v2/app-configs/bulk-restore`    | Admin  | `adminBulkRestoreAppConfigs`        |

Request / response bodies are the snake_case projection of the
corresponding GQL input / payload. Example (`bulk-create`):

```json
// Request
{
  "items": [
    { "key": { "scope_type": "...", "scope_id": "...", "name": "..." },
      "config": { ... } }
  ]
}

// Response
{
  "created": [ /* AppConfig objects */ ],
  "failed": [
    { "scope_type": "USER", "scope_id": "...",
      "name": "...", "message": "..." }
  ]
}
```

`bulk-delete` / `bulk-restore` take `{ "keys": [...] }` and return
`{ "deleted" | "restored": [AppConfig], "failed": [...] }`.

#### My writes (bulk-only)

| Method | Path                                 | Access | Maps to                       |
|--------|--------------------------------------|--------|-------------------------------|
| POST   | `/v2/app-configs/my/bulk-create`     | User   | `bulkCreateMyAppConfigs`          |
| POST   | `/v2/app-configs/my/bulk-update`     | User   | `bulkUpdateMyAppConfigs`          |
| POST   | `/v2/app-configs/my/bulk-delete`     | User   | `bulkDeleteMyAppConfigs`          |
| POST   | `/v2/app-configs/my/bulk-restore`    | User   | `bulkRestoreMyAppConfigs`         |

Response bodies are the snake_case projection of the corresponding
GQL `Bulk*MyAppConfigsPayload` (a success list plus `failed`). For
`bulk-delete`, each success entry is
`{ "name": "...", "my_app_config": { ... } | null }`.

#### Admin cross-scope search

| Method | Path                        | Access | Description                                                |
|--------|-----------------------------|--------|------------------------------------------------------------|
| POST   | `/v2/app-configs/search`    | Admin  | Cross-scope search — same body schema as `adminAppConfigs` |

> Read endpoints filter to `status = ALIVE` by default. Revival
> goes through the dedicated `POST {path}/restore` action;
> `PUT`/`POST` on a soft-deleted natural key does *not* revive and
> instead errors (`404` for PUT since no ALIVE row, `409` for POST
> since a row already exists).

---

## 5. `MyAppConfig` — Merge policy

> The merge semantics here apply **only to `MyAppConfig`**. Other
> scope types (`PublicAppConfig` / `DomainAppConfig` /
> `UserAppConfig`) expose the raw `extra_config` as a single
> `config` field.

### Storage

- `user_app_config.extra_config` (the DB column, exposed as
  `UserAppConfig.config` = `MyAppConfig.userCustomizedConfig`) stores
  **only the values the user has explicitly set** for the named
  document.
- The domain-side merge input is a single row:
  `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name, name=N)`
  — the admin-provided per-user default. Not copied into user rows,
  so editing the default never requires rewriting every user row.
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
   `MyAppConfig.userCustomizedConfig`.

The Connection query (`myAppConfigs`) is backed by the search-specific
method on `AppConfigDBSource` — a single SQL applies filter /
pagination in the query and returns one merged result per `name` for
which at least one of the two scopes (`DOMAIN_USER_DEFAULTS`, `USER`)
has an `ALIVE` row.

`MergedAppConfig` / `MergedAppConfigPage` are service-layer return
dataclasses — 1:1 mappings to the GraphQL `MyAppConfig` /
`MyAppConfigConnection`. `AppConfigFilter` / `Pagination` are the
same internal containers introduced for `db_source.search` in §2.

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
        # filter generalized to `filter`. Pagination uses `name` as a
        # stable cursor key (unique within the pinned scope) applied
        # in SQL. Full implementation lives in the §3 Connection
        # resolver.
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
   and the 2-way merged `mergedConfig` (§5). Admins use the same
   query for their own session (admins are also users for the
   purpose of personal settings). DOMAIN-scope policy does not
   participate in the merge, so an admin UI that needs to manage
   domain policy issues a separate `DomainV2.appConfigs` /
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
call the self-service `bulkUpdateMyAppConfigs` — each item carries
only `name` + `config`, with `scopeType` / `scopeId` injected server-side
as `USER` + `current_user.user_id`. Even a single-item write goes
through the bulk path (1-element `items` array); the recomputed
`MyAppConfig` comes back as `updated[0]`, so no separate
`myAppConfigs` re-query is needed.

```graphql
mutation SaveMyConfig($input: BulkUpdateMyAppConfigInput!) {
  bulkUpdateMyAppConfigs(input: $input) {
    updated {
      name
      userCustomizedConfig
      domainDefaultConfig
      mergedConfig
    }
    failed { name message }
  }
}
```

```json
{
  "input": {
    "items": [
      {
        "name": "preferences",
        "config": {
          "language": "ko",
          "experimentalFeatures": { "multiNodeScheduler": true }
        }
      }
    ]
  }
}
```

- Authorization: authenticated user. The server injects `scopeId =
  current_user.user_id`, so the mutation cannot touch another user's
  row (admins operating on other users use
  `adminBulkUpdateAppConfigs`).
- The input `config` replaces the USER row's `userCustomizedConfig`
  wholesale. `MyAppConfig.mergedConfig` is read-only computed and
  cannot be written.
- **Replace** semantics: anything the caller wants to keep must be
  sent in the same payload — there is no partial-merge or per-key
  patch.
- **First write vs. subsequent writes**: `bulkUpdateMyAppConfigs`
  places items with no `ALIVE` USER row into `failed`. For the very
  first save of a given `name`, the client calls
  `bulkCreateMyAppConfigs` with the same shape (after a soft-delete,
  use `bulkRestoreMyAppConfigs` followed by `bulkUpdateMyAppConfigs`).
  Clients can disambiguate by checking whether the `myAppConfigs`
  entry for that `name` already has a `userCustomizedConfig`.

### S4. Admin publishes a per-user default for a domain

The domain admin publishes a new `theme` document that every user
in the domain inherits as the merge base — `theme` is admin-only
per the user stories, so this is the only path by which the
domain's theme reaches users. The first publish uses
`adminBulkCreateAppConfigs` with `key.scopeType = DOMAIN_USER_DEFAULTS`;
later edits use `adminBulkUpdateAppConfigs` with the identical input
shape. Multiple domains can be seeded in one call by passing
multiple items. `DOMAIN`-scope publishes (admin-enforced policy,
e.g. a domain-internal config document) use the same mutations with
`key.scopeType = DOMAIN` — but DOMAIN values are not included in the
`myAppConfigs` merge, so any document users must be able to read
should be published under `DOMAIN_USER_DEFAULTS` instead.

```graphql
mutation AdminCreateAppConfigs($input: AdminBulkCreateAppConfigInput!) {
  adminBulkCreateAppConfigs(input: $input) {
    created { id scope scopeId name status config updatedAt }
    failed { scope scopeId name message }
  }
}
```

```json
{
  "input": {
    "items": [
      {
        "key": {
          "scopeType": "DOMAIN_USER_DEFAULTS",
          "scopeId": "default",
          "name": "theme"
        },
        "config": { "mode": "dark", "accent": "#6f5ae8" }
      }
    ]
  }
}
```

- Authorization: admin required — the service rejects non-admin
  calls on any admin-path mutation.
- Internally, the service dispatches each item on `item.key.scopeType`
  to the matching repository (§2) and strictly inserts a new `ALIVE`
  row. Items whose key already has a row (ALIVE or DELETED) land in
  `failed` — the admin falls back to `adminBulkUpdateAppConfigs`
  (ALIVE) or `adminBulkRestoreAppConfigs` (DELETED).
- Effect: every user in the domain picks up the new defaults on the
  next `myAppConfigs` read (merged per §5).

### S5. Admin seeds a specific user's document on their behalf

For a support request, an admin seeds user A's `preferences`
`userCustomizedConfig` for the first time. Since the target is
another user's row, this must use the admin path —
`adminBulkCreateAppConfigs` with `key.scopeType = USER` and
`key.scopeId = user A's user_id`, not the self-service bulk path.
Items whose key already has a row (ALIVE or DELETED) land in
`failed`, in which case the admin falls back to
`adminBulkUpdateAppConfigs` (ALIVE) or
`adminBulkRestoreAppConfigs` (DELETED).

```graphql
mutation AdminCreateAppConfigsForUser($input: AdminBulkCreateAppConfigInput!) {
  adminBulkCreateAppConfigs(input: $input) {
    created { id scope scopeId name status config updatedAt }
    failed { scope scopeId name message }
  }
}
```

```json
{
  "input": {
    "items": [
      {
        "key": {
          "scopeType": "USER",
          "scopeId": "00000000-0000-0000-0000-000000000123",
          "name": "preferences"
        },
        "config": { "experimentalFeatures": { "multiNodeScheduler": true } }
      }
    ]
  }
}
```

- For `USER` scope the `config` input is stored as that user's
  `userCustomizedConfig`.
- `adminBulkCreateAppConfigs` does *not* revive a `DELETED` row —
  that is what `adminBulkRestoreAppConfigs` is for; `create` fails
  the item on any pre-existing row regardless of status.
- The response is a list of raw `AppConfig`; the target user's
  merged view reflects the new `userCustomizedConfig` (merged with
  the matching domain defaults) on the next `myAppConfigs` read from
  that user's session.

### S6. Admin audits all AppConfigs (cross-scope search)

Cases such as "list every domain that touched `theme` in the last
week" or "every domain that customized the `menu` document":

```graphql
query AuditConfigs(
  $filter: AppConfigFilter!
  $orderBy: [AppConfigOrderBy!]
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
    "scopeType": { "in": ["DOMAIN", "DOMAIN_USER_DEFAULTS"] },
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
mutation RemoveDomainLegacyMenu($input: AdminBulkDeleteAppConfigInput!) {
  adminBulkDeleteAppConfigs(input: $input) {
    deleted { id scope scopeId name status updatedAt }
    failed { scope scopeId name message }
  }
}
```

```json
{
  "input": {
    "keys": [
      { "scopeType": "DOMAIN", "scopeId": "default", "name": "legacy_menu" }
    ]
  }
}
```

- Authorization: admin required (every `adminBulk*AppConfigs`
  mutation is admin-only).
- The service flips each item's matching row to `status = DELETED`.
  Subsequent reads (`DomainV2.appConfigs`, `UserV2.appConfigs`,
  `adminAppConfigs`, etc.) hide the document.
- **Idempotent**: items whose row is absent or already `DELETED`
  still land in `deleted` (no-op).
- **Recoverable**: `adminBulkRestoreAppConfigs` on the same keys
  flips rows back to `ALIVE` with stored values unchanged. To change
  the value after restoring, chain an `adminBulkUpdateAppConfigs` call.

A user removing their own document uses the self-service
`bulkDeleteMyAppConfigs` — a `names` list is the only input; the
server injects `scope = USER` + `scopeId = current_user.user_id`.
Each entry in the response's `deleted[]` is a `name` + a recomputed
`myAppConfig` (reflecting any remaining `DOMAIN_USER_DEFAULTS`, or
`null` if no ALIVE source remains for that `name`).

```graphql
mutation RemoveMyConfig($input: BulkDeleteMyAppConfigInput!) {
  bulkDeleteMyAppConfigs(input: $input) {
    deleted {
      name
      myAppConfig {
        name
        userCustomizedConfig
        domainDefaultConfig
        mergedConfig
      }
    }
    failed { name message }
  }
}
```

```json
{ "input": { "names": ["preferences"] } }
```
