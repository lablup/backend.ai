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

This BEP redesigns that surface as **scoped entities** — one row per
`(scope_type, scope_id, name)` — so access control and merge
semantics live at the scope level, not at the field level. A single
scope (e.g. one domain, one user) can hold **multiple named
configuration documents** — for instance, a domain may publish
`theme.json`, `menu.json`, and `branding.json` independently — and
each audience gets its own GraphQL type / REST path with permissions
that fit its use.

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
> admin-write and readable by users of the domain, with the same
> row-level access rules. Whether either scope (or both) contributes
> to a user's resolved view is an **admin decision expressed through
> `AppConfigPolicy.scope_sources`** (§1, §5) — not a property of the
> scope type itself. The split is an organizing convention for admin
> tooling:
> - `domain` — values semantically owned by the domain, often
>   admin-only (e.g. a `theme` policy with `scope_sources=["domain"]`
>   and `userWritable=false`; see §7 S4).
> - `domain_user_defaults` — values positioned as per-user seeds the
>   user can override (e.g. a `preferences` policy with
>   `scope_sources=["domain_user_defaults", "user"]` and
>   `userWritable=true`; see §7 S5 and S8).
>
> Both can participate in any resolved chain when the policy says so.

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
  get a partial-success payload back. The admin path exposes three
  verbs (`create` / `update` / `purge`) — `adminBulkCreateAppConfigFragments`
  and siblings cover every scope, admin-only, return raw `AppConfigFragment`
  lists. The self-service (my) path exposes two verbs
  (`create` / `update`) — `bulkCreateMyAppConfigFragments` and siblings, with
  `USER` + `current_user` implicit and merged `AppConfig` in
  the response. `create` strictly inserts (per-item failure if any
  row exists for the key); `update` replaces the existing row's
  stored JSON wholesale; `purge` is an **admin-only cleanup verb**
  (§3) for removing misconfigured rows — users cannot purge. No
  partial update / deep-merge / key-level removal / upsert at the
  write boundary. Each item runs in its own transaction so one
  failure does not abort the rest. Identification uses the
  `(scope, scopeId, name)` natural key, never Relay `id` — my-path
  mutations have scope/scopeId injected by the server.
- **Single source-of-truth table**: a single `app_config_fragments` table holds
  every scope; only the exposure layer is split.
- **Relay style**: Input/Payload conventions and the Node interface.

---

## 1. DB Layer — `app_config_fragments` table

### Schema changes

Add a `name` column to `app_config_fragments`. The natural-key uniqueness
constraint becomes `(scope_type, scope_id, name)`.

```python
class AppConfigScopeType(enum.StrEnum):
    PUBLIC = "public"
    DOMAIN = "domain"
    DOMAIN_USER_DEFAULTS = "domain_user_defaults"   # per-domain defaults applied to users in that domain
    USER = "user"


@dataclass(frozen=True, slots=True)
class AppConfigFragmentKey:
    """Natural key for an app_config_fragments row."""
    scope_type: AppConfigScopeType
    scope_id: str
    name: str


class AppConfigFragmentRow(Base):
    __tablename__ = "app_config_fragments"

    id: Mapped[uuid.UUID]

    scope_type: Mapped[AppConfigScopeType] = mapped_column(
        StrEnumType(AppConfigScopeType, length=32), nullable=False, index=True
    )
    scope_id: Mapped[str]     # literal "public" / domain_name / user_id
    name: Mapped[str] = mapped_column(
        # FK to `app_config_policies.config_name`; default NO ACTION
        # forbids policy deletion while referencing rows exist.
        # `config_name` is immutable, so ON UPDATE never fires.
        sa.ForeignKey("app_config_policies.config_name"),
        nullable=False,
    )

    extra_config: Mapped[dict[str, Any]]  # payload; meaning per scope

    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    __table_args__ = (
        sa.UniqueConstraint(
            "scope_type", "scope_id", "name", name="uq_app_config_fragments_scope_name"
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

### Write semantics

`*Create*` errors if the natural key already exists; `*Update*`
errors if it does not. The only deletion verb is `*Purge*`
(admin-only, §3) — for cleanup of misconfigured rows. Otherwise
rows persist: callers "clear" a document by `*Update*`-ing with
`{}`, which reads back as `null` (§3 null projection).

**A matching `app_config_policies` row is required for every write
(required-policy invariant).** The service layer rejects items
per-row when:
- no policy exists for `name` (policy-not-found),
- `scope_type ∉ policy.scope_sources`, or
- the caller is on the my-path and `policy.user_writable = False`.
  The admin-path ignores `user_writable` — admins may seed USER
  rows regardless.

Because every row is created under a matching policy, the merge
chain (§5) always resolves — no "policy-less fallback" path.

### App Config Policy table

A separate `app_config_policies` table holds the rules per document
— which app-config rows get merged as fragments into the resolved
view, and which scopes may be written. Configs and policies are
joined by `config_name` value, backed by a **FK** on
`app_config_fragments.name → app_config_policies.config_name` with no
`ON DELETE` / `ON UPDATE` action (Postgres default `NO ACTION`).
The **service layer also enforces the required-policy invariant**
explicitly with friendly per-item errors; the FK is defense-in-depth
for raw SQL or any service code path that bypasses the orchestrator.

```python
class AppConfigPolicyRow(Base):
    __tablename__ = "app_config_policies"

    id: Mapped[uuid.UUID]
    config_name: Mapped[str]     # UNIQUE; FK target of `app_config_fragments.name`.
                                 # IMMUTABLE — rename rejected at service layer
                                 # (fix via purge + recreate).
    scope_sources: Mapped[list[str]]  # Ordered scope chain (low → high priority):
                                 # drives both the merge order (§5) and the
                                 # write allow-list. String-typed so that
                                 # adding a scope does not require migration.
    user_writable: Mapped[bool]  # Gate for the `bulk*MyAppConfigFragments` path.
                                 # Admin-path writes are not gated.
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    __table_args__ = (
        sa.UniqueConstraint("config_name", name="uq_app_config_policies_config_name"),
    )
```

**Integrity (FK + service layer)**:

- **Create**: service rejects items with no matching policy
  (friendly error); FK catches any bypass path.
- **Policy rename**: forbidden — `config_name` is immutable
  (updates touch `scope_sources` / `user_writable` only). Removes
  the "rename orphans configs" failure mode.
- **Policy purge**: only via `adminBulkPurgeAppConfigPolicies` (§3);
  the service rejects if any AppConfigFragment row still references
  the policy. Admin purges referencing rows first, then the policy.
  FK `ON DELETE NO ACTION` is the backstop.
- **AppConfigFragment purge**: `adminBulkPurgeAppConfigFragments` is the
  cleanup-only escape hatch, not a general delete.

The FK has no cascade — the schema forbids orphans and refuses to
drop a referenced policy, but never silently deletes. Service
orchestration stays the primary enforcement point.

---

## 2. Repository Layer — single AppConfigFragmentRepository

Keep `models/app_config_fragment/row.py`'s `AppConfigFragmentRow` as a
single class, and use **a single `AppConfigFragmentRepository`** for
all scopes. Prior drafts split the repository four ways (one per
scope); the split added surface without real benefit because each
scope variant was a thin `scope_type` / `scope_id` binding on the
same table. One scope-parameterized repository is simpler.

```
repositories/app_config_fragment/
├── db_source/
│   └── db_source.py                  # single db_source
├── app_config_fragment_repository.py   # all scopes; AppConfigFragmentKey-addressed
└── repositories.py

repositories/app_config_policy/
├── db_source/
│   └── db_source.py                  # separate db_source (different table)
├── app_config_policy_repository.py
└── repositories.py
```

### Repository responsibility split

| Repository                   | Methods                                                                                                              |
|------------------------------|----------------------------------------------------------------------------------------------------------------------|
| `AppConfigFragmentRepository`  | Scope-parameterized CRUD (`get / get_by_id / create / update / purge`) taking an `AppConfigFragmentKey`. `search(scope, querier)` for a bound scope (via `AppConfigFragmentSearchScope`), `admin_search(querier)` for cross-scope (admin). Plus merge-specific reads that serve the merged view (`AppConfig`): `get_app_config(user_id, config_name)`, `search_app_configs(scope, querier)` (`UserAppConfigSearchScope`), and `admin_search_app_configs(querier)` for cross-user admin search. All three derive the chain in SQL via a policy join — see §5. |
| `AppConfigPolicyRepository`  | `get(config_name)`, `get_by_id(id)`, `create(config_name, scope_sources, user_writable)`, `update(config_name, scope_sources, user_writable)`, `purge(config_name)`, `search(querier)`. Updates do not touch `config_name` (immutable — §1). The `purge` call rejects at the service layer if any `AppConfigFragment` row still references the `config_name`. |

`AppConfigFragmentRepository` plays a **dual role** — raw CRUD (served
as `AppConfigFragment`) + merged-view reads (served as `AppConfig`,
§5). `domain_name` resolution for the merge lives inside the SQL
(`users` subquery), so no `UserDBSource` is injected. No separate
`AppConfigRepository`.

### `db_source` is a single module

```python
class AppConfigFragmentDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get(self, key: AppConfigFragmentKey) -> AppConfigFragmentRow | None:
        async with self._db.begin_readonly_session() as db_sess:
            ...

    async def get_by_id(self, id: uuid.UUID) -> AppConfigFragmentRow | None:
        # ID-based lookup for Actions that have already resolved the
        # natural key to a row id (see §3 "Name → ID resolution").
        async with self._db.begin_readonly_session() as db_sess:
            ...

    async def create(
        self,
        key: AppConfigFragmentKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigFragmentRow:
        # Strict insert. Errors if any row already exists for the
        # natural key.
        async with self._db.begin_session() as db_sess:
            ...

    async def update(
        self,
        key: AppConfigFragmentKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigFragmentRow:
        # Replace the existing row's value with `extra_config`.
        # Errors if no row exists for the natural key.
        async with self._db.begin_session() as db_sess:
            ...

    async def search(
        self,
        scope: AppConfigFragmentSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        # Scope-bound; cross-scope uses `admin_search`. Merge search: §5.
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigFragmentRow)
            result = await execute_batch_querier(
                db_sess, query, querier, scope=scope,
            )
            items = [row.AppConfigFragmentRow.to_data() for row in result.rows]
            return AppConfigFragmentSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        # Cross-scope admin search — no scope binding. Authorization
        # is enforced at the service layer before this is reached.
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigFragmentRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.AppConfigFragmentRow.to_data() for row in result.rows]
            return AppConfigFragmentSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
```

Listing is expressed via the `search` primitive — callers build a
`AppConfigFragmentSearchScope(scope_type, scope_id)` plus a
`BatchQuerier` and pass both in. Permission checks and scope
validation are performed in the service layer; the db_source only
runs the resulting SQL.

**Bulk mutation orchestration**: every bulk mutation (fragments
and policies) runs each item in its own DB transaction, collects
successes/failures into `BulkActionResult(success_list,
failed_list)`, and preserves input positions for the per-verb
error `index` field (matching `BulkCreateUserV2Error` convention).
Admin bulks dispatch on `item.key`; my bulks inject
`(USER, current_user.user_id)` server-side. Not a single-SQL
batch — heterogeneous per-item failures (unique violations, auth,
policy) don't compose cleanly in one statement.

Search follows the shared **BatchQuerier** pattern
(`repositories/base/querier.py`):

- `AppConfigFragmentSearchScope(SearchScope)` — frozen dataclass
  pinning `scope_type` + `scope_id` via `to_condition()`; no
  `existence_checks`.
- `BatchQuerier` — `conditions` (from the GQL filter at the adapter
  boundary) + `orders` + `pagination`.
- `AppConfigFragmentSearchResult` — standard `items` / `total_count` /
  `has_next_page` / `has_previous_page` (cf. `GroupSearchResult`).

The GQL `AppConfigFragmentFilter` is the wire format; the adapter
lowers it to `BatchQuerier.conditions` (+ `AppConfigFragmentSearchScope`
for per-scope reads). Filter-to-condition translation is deferred
to implementation.

### Policy repository

`AppConfigPolicyRepository` lives under
`repositories/app_config_policy/` with its own `AppConfigPolicyDBSource`,
kept separate from `AppConfigFragmentDBSource` — the tables share no
FK-driven join surface. Exposes the six-operation shape (§1 allows
`get` / `get_by_id` / `create` / `update` / `search`; no
`delete`).

Write orchestration for `app_config_fragments` consults policies in
the **service layer**: for each batch the service fetches the
distinct `name`s' policies once (batch cache), then applies §1's
three checks (policy-not-found / `scope_type ∉ scope_sources` /
`user_writable = False` on the my-path) before calling the
fragment repository. `AppConfigPolicyRepository.update` refuses to change
`config_name`; `.purge` rejects when any `app_config_fragments` row
still references the policy (required-policy invariant preserved).

Reads don't consult the policy repository from the fragment
repository. The merge path (§5) resolves the chain inside SQL via
a join with `app_config_policies`; per-scope raw reads don't need
a policy lookup at all.

---

## 3. GraphQL Schema — per-entity exposure

### Types

There are two GQL types for app-config data:

- `AppConfigFragment` — one raw row from `app_config_fragments`, regardless of scope.
  Carries `scopeType` + `scopeId` + `name` + `config` + `policy` so
  callers can disambiguate across scopes at read time. Defined
  further below (after the inputs/payloads that also reference it).
- `AppConfig` — the merged per-user view backed by the
  matching `AppConfigPolicy.scope_sources` chain (§5).

Per-scope wrapper types (historical `PublicAppConfig`,
`DomainAppConfig`, `UserAppConfig`) are **not** defined — they offered
no information a single `AppConfigFragment` type doesn't and added three
Connection / Edge / filter triples of boilerplate. Callers
disambiguate scope by reading `AppConfigFragment.scopeType` instead.

```graphql
"""
Merged per-user view — non-admins use `myAppConfigs` (own view);
admins also have `adminAppConfigs` to resolve any user. Deep-merges
same-`name` fragments in the matching policy's `scope_sources`
order; appears whenever at least one fragment exists (§5).

Implements `Node` with server-side ID
`base64("AppConfig:{user_id}:{name}")`. `node(id)` resolves when
`decoded.user_id == current_user.id`, or for any `user_id` when the
caller is admin.
"""
type AppConfig implements Node {
  id: ID!
  name: String!

  """
  Fragments in merge order (low → high). Callers distinguish
  admin-provided defaults from user overrides via each row's
  `scopeType`.
  """
  fragments: [AppConfigFragment!]!

  """
  Deep-merge of `fragments` in order (last wins). `null` when every
  contributing row has an empty stored `config` (clients fall back
  to built-in defaults).
  """
  config: JSON
}
```

### Added/extended fields (Relationship)

| Location      | Field                                                                                  |
|---------------|----------------------------------------------------------------------------------------|
| `DomainV2` | `appConfigFragments(filter, orderBy, ...pagination): AppConfigFragmentConnection!` (`scopeType = DOMAIN`, `scopeId = domain_name` pinned) |
| `UserV2`   | `appConfigFragments(filter, orderBy, ...pagination): AppConfigFragmentConnection!` (`scopeType = USER`, `scopeId = user_id` pinned)       |

### Permissions

Each `appConfigFragments` child field enforces its own access rule (not
simply inherited from the parent node) — see the permission matrix
below. In short: `DomainV2.appConfigFragments` is same-domain users or
admin; `UserV2.appConfigFragments` is owner or admin. Writes (mutations) on
both are admin-only.

```graphql
extend type DomainV2 {
  """DOMAIN-scope rows. Same-domain users or admin; `filter.scopeType`/`scopeId` ignored."""
  appConfigFragments(
    filter: AppConfigFragmentFilter = null
    orderBy: [AppConfigFragmentOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigFragmentConnection!
}

extend type UserV2 {
  """USER-scope rows. Owner or admin; `filter.scopeType`/`scopeId` ignored."""
  appConfigFragments(
    filter: AppConfigFragmentFilter = null
    orderBy: [AppConfigFragmentOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigFragmentConnection!
}
```

Root field `myAppConfigs` returns the caller's merged view
(`AppConfig`), the only query that performs the merge (§5). All
other queries expose raw `AppConfigFragment` rows.

### Queries

```graphql
type Query {
  """Public config documents. No auth."""
  publicAppConfigFragments(
    filter: AppConfigFragmentFilter = null
    orderBy: [AppConfigFragmentOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigFragmentConnection!

  """
  Caller's merged view (auth required). Chain per policy (§5);
  `filter.scopeType` / `filter.scopeId` are ignored.
  """
  myAppConfigs(
    filter: AppConfigFragmentFilter = null
    orderBy: [AppConfigFragmentOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigConnection!

  """Cross-scope admin search."""
  adminAppConfigFragments(
    filter: AppConfigFragmentFilter = null
    orderBy: [AppConfigFragmentOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigFragmentConnection!

  """
  Cross-user merged-view search (admin only). Resolves any user's
  `AppConfig` for audit / support. Pin to a single user with
  `filter.userId`; otherwise paginates across all users.
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

  """Policy lookup by `configName`. Any authenticated user."""
  appConfigPolicy(configName: String!): AppConfigPolicy

  """Policies Connection. Any authenticated user."""
  appConfigPolicies(
    filter: AppConfigPolicyFilter = null
    orderBy: [AppConfigPolicyOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigPolicyConnection!

  # Reused existing root fields (not new):
  #   admin_user_v2(user_id: UUID!) { appConfigFragments { ... } }
  #   domain_v2(name: String!)      { appConfigFragments { ... } }
  #   node(id: ID!): Node
}
```

#### Connection / Filter / OrderBy

A single `AppConfigFragmentFilter` + `AppConfigFragmentOrderBy` is reused
across every raw-row query — each call pins `scopeType` / `scopeId`
internally.

```graphql
# ── Connections ───────────────────────────────────────────────

"""Relay Connection over raw `AppConfigFragment` rows (any scope)."""
type AppConfigFragmentConnection {
  edges: [AppConfigFragmentEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type AppConfigFragmentEdge {
  cursor: String!
  node: AppConfigFragment!
}

"""Relay Connection over the caller's merged `AppConfig` — backs `myAppConfigs`."""
type AppConfigConnection {
  edges: [AppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type AppConfigEdge {
  cursor: String!
  node: AppConfig!
}

"""Relay Connection of app-config policies."""
type AppConfigPolicyConnection {
  edges: [AppConfigPolicyEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type AppConfigPolicyEdge {
  cursor: String!
  node: AppConfigPolicy!
}

# ── Filter / OrderBy (shared by all Connections) ──────────────

"""
AppConfigFragment search filter. Scalar fields at the top level are
AND-combined. For arbitrary boolean shapes, nest predicates under
`AND` / `OR` / `NOT`.
"""
input AppConfigFragmentFilter {
  """Scope filters are ignored on per-scope Connections (scope pinned by the field)."""
  scopeType: AppConfigScopeTypeEnumFilter = null
  scopeId: StringFilter = null

  name: StringFilter = null
  createdAt: DateTimeFilter = null
  updatedAt: DateTimeFilter = null

  AND: [AppConfigFragmentFilter!] = null
  OR: [AppConfigFragmentFilter!] = null
  NOT: [AppConfigFragmentFilter!] = null
}

input AppConfigScopeTypeEnumFilter {
  equals: AppConfigScopeType
  in: [AppConfigScopeType!]
  notEquals: AppConfigScopeType
  notIn: [AppConfigScopeType!]
}

input AppConfigFragmentOrderBy {
  field: AppConfigFragmentOrderField!
  direction: OrderDirection! = ASC
}

"""
`SCOPE_TYPE` / `SCOPE_ID` degenerate to constants on per-scope
Connections. `UPDATED_AT` / `CREATED_AT` fall back to `NAME` on
`myAppConfigs` (derived `AppConfig` has no timestamps).
"""
enum AppConfigFragmentOrderField {
  SCOPE_TYPE
  SCOPE_ID
  NAME
  UPDATED_AT
  CREATED_AT
}

"""
Filter for the merged `AppConfig` view. On `myAppConfigs` `userId`
is pinned to the caller and ignored; on `adminAppConfigs` admins
use it to scope to a target user.
"""
input AppConfigFilter {
  userId: StringFilter = null
  name: StringFilter = null

  AND: [AppConfigFilter!] = null
  OR: [AppConfigFilter!] = null
  NOT: [AppConfigFilter!] = null
}

input AppConfigOrderBy {
  field: AppConfigOrderField!
  direction: OrderDirection! = ASC
}

enum AppConfigOrderField {
  USER_ID
  NAME
}

input AppConfigPolicyFilter {
  configName: StringFilter = null
  userWritable: Boolean = null
  createdAt: DateTimeFilter = null
  updatedAt: DateTimeFilter = null
  AND: [AppConfigPolicyFilter!] = null
  OR: [AppConfigPolicyFilter!] = null
  NOT: [AppConfigPolicyFilter!] = null
}

input AppConfigPolicyOrderBy {
  field: AppConfigPolicyOrderField!
  direction: OrderDirection! = ASC
}

enum AppConfigPolicyOrderField {
  CONFIG_NAME
  UPDATED_AT
  CREATED_AT
}
```

### Mutations

All writes are **bulk-only** (pass a 1-element array for a single
write). Eight mutations total across three paths:

- `adminBulk{Create,Update,Purge}AppConfigFragments` — admin-only.
  Items carry `AppConfigFragmentKey { scopeType, scopeId, name }`, so
  scopes may be mixed in one call. Create/Update return raw
  `AppConfigFragment` lists; Purge returns the purged keys.
- `bulk{Create,Update}MyAppConfigFragments` — any authenticated
  user, `USER` + `current_user.user_id` injected server-side.
  Returns recomputed `AppConfig`s. No Purge (admin-only cleanup).
- `adminBulk{Create,Update,Purge}AppConfigPolicies` — admin-only.
  Update rejects `configName` changes; Purge rejects items whose
  `configName` still has referencing rows (§1).

All mutations run each item in its own transaction — **partial
success**, failures collected per-item; auth enforced in the service
layer (permission matrix below).

```graphql
type Mutation {
  # ── Admin path — every scope, admin-only ─────────────────────

  """Strict insert across any scope; admin USER-row seeding also goes here."""
  adminBulkCreateAppConfigFragments(input: AdminBulkCreateAppConfigFragmentInput!): AdminBulkCreateAppConfigFragmentsPayload!

  """Wholesale JSON replacement; items with no existing row fail."""
  adminBulkUpdateAppConfigFragments(input: AdminBulkUpdateAppConfigFragmentInput!): AdminBulkUpdateAppConfigFragmentsPayload!

  """Cleanup-only deletion (see §1); absent keys are no-oped."""
  adminBulkPurgeAppConfigFragments(input: AdminBulkPurgeAppConfigFragmentInput!): AdminBulkPurgeAppConfigFragmentsPayload!

  # ── Self-service (my) path — USER + current_user implicit ────

  """Strict insert on the caller's USER row; duplicates fail."""
  bulkCreateMyAppConfigFragments(input: BulkCreateMyAppConfigFragmentInput!): BulkCreateMyAppConfigFragmentsPayload!

  """Wholesale replacement; items with no existing USER row fail."""
  bulkUpdateMyAppConfigFragments(input: BulkUpdateMyAppConfigFragmentInput!): BulkUpdateMyAppConfigFragmentsPayload!

  # ── Admin policy path — admin-only ─────────────────────────

  """Strict insert keyed on `configName`."""
  adminBulkCreateAppConfigPolicies(
    input: AdminBulkCreateAppConfigPolicyInput!
  ): AdminBulkCreateAppConfigPoliciesPayload!

  """Replace `scope_sources` / `user_writable`; `configName` is immutable (§1)."""
  adminBulkUpdateAppConfigPolicies(
    input: AdminBulkUpdateAppConfigPolicyInput!
  ): AdminBulkUpdateAppConfigPoliciesPayload!

  """Rejects items whose `configName` still has referencing rows (§1)."""
  adminBulkPurgeAppConfigPolicies(
    input: AdminBulkPurgeAppConfigPolicyInput!
  ): AdminBulkPurgeAppConfigPoliciesPayload!
}

enum AppConfigScopeType {
  PUBLIC
  DOMAIN
  DOMAIN_USER_DEFAULTS
  USER
}

# ── Composite key shared by write mutations ──────────────────

"""
Natural composite key identifying a single app config row.
Mirrors the Python `AppConfigFragmentKey` dataclass used by the repository /
db_source layer.
- `PUBLIC`:               `scopeId` is the literal string `"public"`.
- `DOMAIN`:               `scopeId` is `domain_name`.
- `DOMAIN_USER_DEFAULTS`: `scopeId` is `domain_name`.
- `USER`:                 `scopeId` is `user_id` (UUID string).
- `name` is the document name (unique within the scope).
"""
input AppConfigFragmentKey {
  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
}

# ── Admin Inputs — per-item + bulk wrappers ──────────────────
# `config` is the stored row value: initial on create, wholesale
# replacement on update. Pass `{}` to clear (reads back as `null`).
# Service applies a reasonable item cap.

input AdminAppConfigFragmentItemInput {
  key: AppConfigFragmentKey!
  config: JSON!
}

input AdminBulkCreateAppConfigFragmentInput {
  items: [AdminAppConfigFragmentItemInput!]!
}

input AdminBulkUpdateAppConfigFragmentInput {
  items: [AdminAppConfigFragmentItemInput!]!
}

"""Purge is keyed by `AppConfigFragmentKey` alone."""
input AdminBulkPurgeAppConfigFragmentInput {
  keys: [AppConfigFragmentKey!]!
}

# ── My Inputs — scope=USER, scopeId=current_user.user_id implicit ──
# `AppConfig.config` is read-only; writes go through these inputs.

input MyAppConfigFragmentItemInput {
  name: String!
  config: JSON!
}

input BulkCreateMyAppConfigFragmentInput {
  items: [MyAppConfigFragmentItemInput!]!
}

input BulkUpdateMyAppConfigFragmentInput {
  items: [MyAppConfigFragmentItemInput!]!
}

# ── Admin Payloads — raw AppConfigFragment ───────────────────────
# Error types are per-verb (matching BulkCreateUserV2Error convention).
# `index` = original position in the input list.

type AdminBulkCreateAppConfigFragmentError {
  index: Int!
  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
  message: String!
}

type AdminBulkUpdateAppConfigFragmentError {
  index: Int!
  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
  message: String!
}

type AdminBulkPurgeAppConfigFragmentError {
  index: Int!
  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
  message: String!
}

type AdminBulkCreateAppConfigFragmentsPayload {
  created: [AppConfigFragment!]!
  failed: [AdminBulkCreateAppConfigFragmentError!]!
}

type AdminBulkUpdateAppConfigFragmentsPayload {
  updated: [AppConfigFragment!]!
  failed: [AdminBulkUpdateAppConfigFragmentError!]!
}

type AdminBulkPurgeAppConfigFragmentsPayload {
  """Keys of rows actually removed (absent keys are no-oped)."""
  purged: [AppConfigFragmentKey!]!
  failed: [AdminBulkPurgeAppConfigFragmentError!]!
}

# ── My Payloads — recomputed AppConfig ─────────────────────────
# scope / scopeId are server-injected, so `name` is the only identifier.

type BulkCreateMyAppConfigFragmentError {
  index: Int!
  name: String!
  message: String!
}

type BulkUpdateMyAppConfigFragmentError {
  index: Int!
  name: String!
  message: String!
}

type BulkCreateMyAppConfigFragmentsPayload {
  created: [AppConfig!]!
  failed: [BulkCreateMyAppConfigFragmentError!]!
}

type BulkUpdateMyAppConfigFragmentsPayload {
  updated: [AppConfig!]!
  failed: [BulkUpdateMyAppConfigFragmentError!]!
}

# ── Admin Policy Inputs / Payloads ──────────────────────────

"""Per-item input for `adminBulkCreate/UpdateAppConfigPolicies`."""
input AdminAppConfigPolicyItemInput {
  configName: String!

  """
  Scope chain in merge order (low → high priority). Also the
  write allow-list.
  """
  scopeSources: [String!]!

  """Whether the owner may write their own `USER` row (my-path gate)."""
  userWritable: Boolean!
}

input AdminBulkCreateAppConfigPolicyInput {
  items: [AdminAppConfigPolicyItemInput!]!
}

input AdminBulkUpdateAppConfigPolicyInput {
  items: [AdminAppConfigPolicyItemInput!]!
}

"""Purge is keyed by `configName` alone."""
input AdminBulkPurgeAppConfigPolicyInput {
  configNames: [String!]!
}

type AdminBulkCreateAppConfigPolicyError {
  index: Int!
  configName: String!
  message: String!
}

type AdminBulkUpdateAppConfigPolicyError {
  index: Int!
  configName: String!
  message: String!
}

type AdminBulkPurgeAppConfigPolicyError {
  index: Int!
  configName: String!
  message: String!
}

type AdminBulkCreateAppConfigPoliciesPayload {
  created: [AppConfigPolicy!]!
  failed: [AdminBulkCreateAppConfigPolicyError!]!
}

type AdminBulkUpdateAppConfigPoliciesPayload {
  updated: [AppConfigPolicy!]!
  failed: [AdminBulkUpdateAppConfigPolicyError!]!
}

type AdminBulkPurgeAppConfigPoliciesPayload {
  purgedConfigNames: [String!]!
  failed: [AdminBulkPurgeAppConfigPolicyError!]!
}

"""
Raw `app_config_fragments` row — any scope. No back-refs to parent
`DomainV2` / `UserV2`; callers re-query as needed.
"""
type AppConfigFragment implements Node {
  """Relay ID — `base64("AppConfigFragment:<row_uuid>")`."""
  id: ID!

  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!

  """
  Raw stored value (`extra_config`). For USER scope this is the
  user's own value, not the merged result. `null` when cleared to
  `{}` (§3 null projection).
  """
  config: JSON

  """
  Matching `AppConfigPolicy` (joined by `name = config_name`).
  Non-null per §1's required-policy invariant. Resolved via a
  per-request DataLoader keyed on `name` to avoid N+1 in Connections;
  callers who only want the raw row can omit the selection.
  """
  policy: AppConfigPolicy!

  createdAt: DateTime!
  updatedAt: DateTime!
}

# ── App Config Policy ────────────────────────────────────────

"""
Per-document policy: which scopes get merged into `AppConfig` (§5)
and which scopes may be written. FK-backed (§1), joined by
`configName` value. Read: any authenticated user; write: admin only.
"""
type AppConfigPolicy implements Node {
  """Relay ID — `base64("AppConfigPolicy:<row_uuid>")`."""
  id: ID!

  """
  Governed document name. Immutable (§1) — fix via purge + recreate
  (see §7 S7).
  """
  configName: String!

  """
  Ordered scope chain (low → high): both the merge sources and the
  write allow-list. String-typed to avoid migration when scopes are
  added.
  """
  scopeSources: [String!]!

  """Gate for the `bulk*MyAppConfigFragments` path. Admin-path is ungated."""
  userWritable: Boolean!

  createdAt: DateTime!
  updatedAt: DateTime!
}
```

### Permission matrix

Queries:

| Operation                          | Anonymous | User                             | Admin |
|------------------------------------|-----------|----------------------------------|-------|
| `publicAppConfigFragments`                 | ✅        | ✅                               | ✅    |
| `myAppConfigs`                     | ❌        | ✅ (self)                        | ✅    |
| `DomainV2.appConfigFragments`              | ❌        | ✅ (same domain only)            | ✅    |
| `UserV2.appConfigFragments`                | ❌        | ✅ (self)                        | ✅    |
| `adminAppConfigFragments`                  | ❌        | ❌                               | ✅    |
| `adminAppConfigs`                        | ❌        | ❌                               | ✅    |
| `appConfigPolicy` / `appConfigPolicies` | ❌   | ✅                               | ✅    |
| `node(id)` → `AppConfigFragment`           | ✅ iff row `scopeType = PUBLIC` | ✅ (PUBLIC always; DOMAIN / DOMAIN_USER_DEFAULTS same-domain only; USER self only) | ✅ |
| `node(id)` → `AppConfig`   | ❌        | ✅ (id's `user_id` is self)      | ✅ (any `user_id`)         |
| `node(id)` → `AppConfigPolicy`     | ❌        | ✅                               | ✅    |

Write mutations split into two paths with distinct rules. All
bulk-only.

**Admin path** — `adminBulkCreateAppConfigFragments`,
`adminBulkUpdateAppConfigFragments`. Admin regardless of each item's
`key.scopeType`:

| Operation                                  | Anonymous | User | Admin |
|--------------------------------------------|-----------|------|-------|
| `adminBulk{Create,Update,Purge}AppConfigFragments` | ❌        | ❌   | ✅    |

**Self-service (my) path** — `bulkCreateMyAppConfigFragments`,
`bulkUpdateMyAppConfigFragments`. Imply `scope = USER` +
`scopeId = current_user.user_id`:

| Operation              | Anonymous | User (self) | Admin (self) |
|------------------------|-----------|-------------|--------------|
| `bulk*MyAppConfigFragments`    | ❌        | ✅          | ✅           |

> Admins operating on another user's `USER` row must use the admin
> path with an explicit `AppConfigFragmentKey { scopeType: USER, scopeId:
> target_user_id, name }` on each item — the my path cannot target
> another user.

**Admin policy path** — `adminBulkCreateAppConfigPolicies`,
`adminBulkUpdateAppConfigPolicies`,
`adminBulkPurgeAppConfigPolicies`:

| Operation                                           | Anonymous | User | Admin |
|-----------------------------------------------------|-----------|------|-------|
| `adminBulk{Create,Update,Purge}AppConfigPolicies`   | ❌        | ❌   | ✅    |

Where the checks live:
- Admin paths: `check_admin_only()` at entry, then per-item dispatch
  on `item.key.scopeType`.
- My paths: authenticated-only; `scopeId` is server-injected.
- `DomainV2.appConfigFragments`: same-domain users or admin (helper in
  `src/ai/backend/manager/api/gql/utils.py`).
- `UserV2.appConfigFragments`: owner or admin.

#### Name → ID resolution and ID-based Actions

**Admin path only.** Admin-path Actions are ID-only. For each item:
(1) resolve `(scope, scopeId, name)` → row `id` via the repository
(permission-agnostic lookup), (2) RBAC-check against the resolved
`id`, (3) dispatch the ID-based Action. Clients never see row IDs.

My-path mutations skip resolution — `scopeId = current_user.user_id`
is fixed server-side and the repository is called with
`user_id` + `item.name` directly.

`adminBulk*AppConfigPolicies` follows the same resolve-by-name
pattern via `AppConfigPolicyRepository.get(name)`.

---

## 4. REST Schema

REST exposes three prefix trees that mirror the GQL surface:

- `/v2/app-config-fragments/...` — raw fragment operations (admin
  CRUD, cross-scope search, per-scope search, single reads, my-path
  writes).
- `/v2/app-configs/my/...` — **merged `AppConfig` view** per user
  (read-only; writes go through the fragment prefix).
- `/v2/app-config-policies/...` — policy CRUD + reads.

Mounted via `RouteRegistry.create("app-config-fragments", ...)`,
`RouteRegistry.create("app-configs", ...)`, and
`RouteRegistry.create("app-config-policies", ...)` respectively,
matching the project-wide v2 conventions in
`src/ai/backend/manager/api/rest/v2/CLAUDE.md`.

### Listing convention

All list operations are exposed as `POST .../search` with a typed
request body — **no `GET` list endpoints, no query-string
pagination**. Listing is always paginated, and pagination
parameters live in the request body.

Search bodies share a common pagination shape:

- `limit` — maximum items per page. A request-validation error
  is raised for out-of-range values, so there is no way to request
  an unbounded page.
- `offset` — for offset pagination (non-negative).
- Admin cross-scope variants additionally accept cursor pagination
  (`first` / `after` / `last` / `before`).

Single-resource reads (`GET .../{name}`) remain `GET` — one row,
no pagination.

### App Config Fragment endpoints

REST mirrors the GQL admin / my split — the scope-parameterized
path handles **admin writes + per-scope reads / search** (maps to
GQL `adminBulk*AppConfigFragments` mutations and the scoped queries),
and the `/my` path is **self-only** (maps to GQL
`bulk*MyAppConfigFragments` mutations).

#### Scope-parameterized path — admin writes / per-scope reads

```
/v2/app-config-fragments/{scope_type}/{scope_id}/{name}     # single GET
/v2/app-config-fragments/{scope_type}/{scope_id}/search     # POST search
```

- `{scope_type}` ∈ `public | domain | domain_user_defaults | user`.
- `{scope_id}` per §1 scope-ID convention (`"public"` / `domain_name` /
  `user_id`).
- `{name}` is the document name.

Reads use single `GET` + `POST search` (above); writes go through
the bulk endpoints (below).

| Method | Path                                                           | Description                           |
|--------|----------------------------------------------------------------|---------------------------------------|
| GET    | `/v2/app-config-fragments/{scope_type}/{scope_id}/{name}`        | Read one fragment                    |
| POST   | `/v2/app-config-fragments/{scope_type}/{scope_id}/search`        | Paginated list within this scope       |

`POST .../search` accepts the shared search body (filter + order +
`limit/offset`); `filter.scopeType` / `filter.scopeId` are ignored
because the scope is already pinned by the path.

Per-scope read permissions mirror the GQL matrix: `public` anonymous;
`domain` / `domain_user_defaults` require same-domain or admin;
`user` requires self or admin.

### AppConfig endpoint — `/v2/app-configs/my`

Read-only per-user `AppConfig` at its own prefix to make the
"merged view, not raw row" framing explicit in the URL. The
adapter pins `(USER, current_user.user_id)`; no way to target
another user, no writes (those go through
`/v2/app-config-fragments/my/bulk-*`).

| Method | Path                                | Description                              |
|--------|-------------------------------------|------------------------------------------|
| GET    | `/v2/app-configs/my/{name}`         | Read one `AppConfig`                     |
| POST   | `/v2/app-configs/my/search`         | Paginated list of own `AppConfig`s       |

#### Admin cross-user search

Admins can resolve any user's merged view (audit / support; maps
to GQL `adminAppConfigs`).

| Method | Path                                       | Access | Description                                                            |
|--------|--------------------------------------------|--------|------------------------------------------------------------------------|
| POST   | `/v2/app-configs/search`                   | Admin  | Cross-user paginated search — pin to a single user via `userId` filter |
| GET    | `/v2/app-configs/{user_id}/{name}`         | Admin  | Read one user's `AppConfig`                                            |

Response body for the single `GET` is the snake_case projection
of the GQL `AppConfig`:

```json
{
  "name": "preferences",
  "fragments": [
    { "scope_type": "domain_user_defaults",
      "scope_id": "default", "name": "preferences",
      "config": { ... }, "created_at": "...", "updated_at": "..." },
    { "scope_type": "user",
      "scope_id": "<user_uuid>", "name": "preferences",
      "config": { ... }, "created_at": "...", "updated_at": "..." }
  ],
  "config": { ... }
}
```

`fragments` is ordered low → high (policy's `scope_sources`).
Elements appear only where a row exists for `(user, name)`. Each
`config` and the top-level `config` mirror GQL nullability
(§3) — empty → `null`, never bare `{}`.

#### Admin writes (bulk-only)

| Method | Path                                       | Access | Maps to                             |
|--------|--------------------------------------------|--------|-------------------------------------|
| POST   | `/v2/app-config-fragments/bulk-create`       | Admin  | `adminBulkCreateAppConfigFragments`   |
| POST   | `/v2/app-config-fragments/bulk-update`       | Admin  | `adminBulkUpdateAppConfigFragments`   |
| POST   | `/v2/app-config-fragments/bulk-purge`        | Admin  | `adminBulkPurgeAppConfigFragments`    |

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
  "created": [ /* AppConfigFragment objects */ ],
  "failed": [
    { "scope_type": "USER", "scope_id": "...",
      "name": "...", "message": "..." }
  ]
}
```

#### My writes (bulk-only)

| Method | Path                                          | Access | Maps to                          |
|--------|-----------------------------------------------|--------|----------------------------------|
| POST   | `/v2/app-config-fragments/my/bulk-create`       | User   | `bulkCreateMyAppConfigFragments`   |
| POST   | `/v2/app-config-fragments/my/bulk-update`       | User   | `bulkUpdateMyAppConfigFragments`   |

Response bodies are the snake_case projection of the corresponding
GQL `Bulk*MyAppConfigFragmentsPayload` (a success list plus `failed`).

#### Admin cross-scope search

| Method | Path                                | Access | Description                                                                                  |
|--------|-------------------------------------|--------|----------------------------------------------------------------------------------------------|
| POST   | `/v2/app-config-fragments/search`     | Admin  | Cross-scope paginated search — same body schema as `adminAppConfigFragments` (offset + cursor) |

### App Config Policy endpoints

Mounted at a sibling prefix (`/v2/app-config-policies/...`). Reads
are available to any authenticated user; writes are admin-only.

| Method | Path                                         | Access | Maps to                               |
|--------|----------------------------------------------|--------|---------------------------------------|
| GET    | `/v2/app-config-policies/{config_name}`      | User   | `appConfigPolicy(configName)`         |
| POST   | `/v2/app-config-policies/search`             | User   | `appConfigPolicies` (Connection)      |
| POST   | `/v2/app-config-policies/bulk-create`        | Admin  | `adminBulkCreateAppConfigPolicies`    |
| POST   | `/v2/app-config-policies/bulk-update`        | Admin  | `adminBulkUpdateAppConfigPolicies`    |
| POST   | `/v2/app-config-policies/bulk-purge`         | Admin  | `adminBulkPurgeAppConfigPolicies`     |

Request / response bodies are the snake_case projection of the
corresponding GQL input / payload — `items[]` for writes, the
shared search body (`filter` + `order` + `limit/offset`) for
`search`, a `{ data: [...], page_info: {...}, count: N }` envelope
for search results, and a single policy object for the
`{config_name}` `GET`.

---

## 5. `AppConfig` — Merge policy

### Storage

Each scope holds its own row for a given `name`; rows are never
copied between scopes. Editing an admin default doesn't touch user
rows — the merge materializes at read time. `name`s are independent
(the `preferences` merge is unaffected by `theme`'s rows).

### Chain order (policy-driven)

The chain for `(user_id, name)` is the matching policy's
`scope_sources` in order (low → high, last wins on deep merge, §1).
Each scope contributes its natural `scope_id` — `"public"` literal,
caller's `domain_name`, or caller's `user_id`. Policies can be
single-scope (`["domain"]`), 2-chain (`["domain", "user"]`), or
wider as the use case demands.

### Read (Merge)

Single-document (`AppConfigFragmentDBSource.get_user_app_config(user_id,
config_name)`): one SQL resolves `domain_name` via a `users`
subquery, joins `app_config_policies` to derive the chain
(`scope_sources`), and pulls only the scope rows that are part of
that chain. Rows are
ordered per the chain; absent scopes contribute `{}`; the deep-merge
treats nested objects recursively, leaves as scalar replacement, and
lists as wholesale replacement. Output: ordered `fragments` + merged
`config`. Callers don't pre-resolve the chain — the same pattern
applies to search (below).

Connection (`myAppConfigs` → `search_user_app_configs`): same
single-SQL approach, generalized — joins `app_config_fragments` with
`app_config_policies ON name = config_name`, filters
`scope_type = ANY(policy.scope_sources)`, orders by
`array_position(policy.scope_sources, scope_type)`. Each `name`'s
chain is evaluated independently in SQL; no per-name chain map is
precomputed in service code.

Cross-user (`adminAppConfigs` → `admin_search_app_configs`): same
SQL joined with `users` to drop the user_id binding — paginates at
the `(user_id, name)` level. Authorization is admin-only, enforced
at the service layer; `querier.conditions` filters on user_id /
name as needed.

`AppConfigData` is the service return for a single document;
`AppConfigSearchResult` is its search counterpart (standard `items`
/ `total_count` / `has_next_page` / `has_previous_page`). Search
inputs reuse the shared **BatchQuerier** + a
`UserAppConfigSearchScope(SearchScope)` pinning
`user_id` (its `to_condition()` scopes the underlying SELECT to
rows readable for that user: PUBLIC, user's DOMAIN /
DOMAIN_USER_DEFAULTS, and USER rows). No Python callable is
threaded through — chain derivation lives entirely in SQL.

```python
class AppConfigFragmentDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @staticmethod
    def _merge_chain(
        rows: Sequence[AppConfigFragmentRow],
        chain: Sequence[str],
    ) -> tuple[list[AppConfigFragmentRow], dict | None]:
        # Order `rows` by `chain` (low → high) and deep-merge their
        # `extra_config` in that order. Empty result projects to None
        # per §3 null projection. Shared by get / search / admin_search.
        by_scope = {row.scope_type: row for row in rows}
        ordered_fragments = [
            by_scope[AppConfigScopeType(s)]
            for s in chain
            if AppConfigScopeType(s) in by_scope
        ]
        merged: dict = {}
        for row in ordered_fragments:
            merged = deep_merge(merged, row.extra_config)
        return ordered_fragments, merged or None

    async def get_user_app_config(
        self,
        user_id: uuid.UUID,
        config_name: str,
    ) -> AppConfigData:
        # Single SQL: resolve `domain_name` via a `users` subquery,
        # join `app_config_policies` to derive the chain
        # (`scope_sources`), and fetch only the scope rows that are
        # part of that chain. Bounded by the natural-key
        # UniqueConstraint.
        user_domain_sq = (
            sa.select(UserRow.domain_name)
            .where(UserRow.id == user_id)
            .scalar_subquery()
        )
        scope_id_match = sa.case(
            (AppConfigFragmentRow.scope_type == AppConfigScopeType.PUBLIC,
             sa.literal("public")),
            (AppConfigFragmentRow.scope_type.in_([
                AppConfigScopeType.DOMAIN,
                AppConfigScopeType.DOMAIN_USER_DEFAULTS,
            ]), user_domain_sq),
            (AppConfigFragmentRow.scope_type == AppConfigScopeType.USER,
             sa.literal(str(user_id))),
        )
        query = (
            sa.select(AppConfigFragmentRow, AppConfigPolicyRow.scope_sources)
            .join(
                AppConfigPolicyRow,
                AppConfigPolicyRow.config_name == AppConfigFragmentRow.name,
            )
            .where(
                AppConfigFragmentRow.name == config_name,
                AppConfigFragmentRow.scope_id == scope_id_match,
                sa.cast(AppConfigFragmentRow.scope_type, sa.Text)
                    == sa.any_(AppConfigPolicyRow.scope_sources),
            )
        )
        async with self._db.begin_readonly_session() as db_sess:
            result = (await db_sess.execute(query)).all()

        if not result:
            return AppConfigData(
                user_id=user_id, name=config_name, fragments=[], config=None,
            )

        # `config_name` is UNIQUE and we filtered on a single value,
        # so every result row carries the same `scope_sources`.
        chain = result[0].scope_sources
        rows = [r.AppConfigFragmentRow for r in result]
        ordered_fragments, config = self._merge_chain(rows, chain)

        return AppConfigData(
            user_id=user_id,
            name=config_name,
            fragments=ordered_fragments,
            config=config,
        )

    async def search_user_app_configs(
        self,
        scope: UserAppConfigSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        # Connection counterpart. Single SQL joins policies:
        #
        #   SELECT s.*, p.scope_sources
        #   FROM app_config_fragments AS s
        #   JOIN app_config_policies AS p ON s.name = p.config_name
        #   WHERE <scope.to_condition()>
        #     AND s.scope_type::text = ANY(p.scope_sources)
        #   ORDER BY s.name,
        #     array_position(p.scope_sources, s.scope_type::text)
        #
        # `execute_batch_querier` paginates at the distinct-`name`
        # level; each group's (rows, scope_sources) is fed to
        # `_merge_chain` to produce one `AppConfigData`.
        ...

    async def admin_search_app_configs(
        self,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        # Cross-user merged search — no user_id binding. Joins
        # `users` so each user × applicable `name` combination is
        # produced. Authorization is enforced at the service layer
        # before this is reached. `querier.conditions` filters on
        # user_id / name as needed; `execute_batch_querier` paginates
        # at the distinct-`(user_id, name)` level, each group's
        # (rows, scope_sources) fed to `_merge_chain` to produce one
        # `AppConfigData`.
        ...


class AppConfigFragmentRepository:
    """
    CRUD for raw `app_config_fragments` rows (any scope, addressed by
    `AppConfigFragmentKey`) + merge-specific reads for `AppConfig` (§5).
    No separate `AppConfigRepository`.
    """

    _db_source: AppConfigFragmentDBSource

    def __init__(self, db_source: AppConfigFragmentDBSource) -> None:
        self._db_source = db_source

    # ── Raw fragment CRUD (AppConfigFragment) ──────────────────────────

    async def get(self, key: AppConfigFragmentKey) -> AppConfigFragmentRow | None:
        return await self._db_source.get(key)

    async def get_by_id(self, id: uuid.UUID) -> AppConfigFragmentRow | None:
        return await self._db_source.get_by_id(id)

    async def create(
        self, key: AppConfigFragmentKey, extra_config: Mapping[str, Any]
    ) -> AppConfigFragmentRow:
        return await self._db_source.create(key, extra_config)

    async def update(
        self, key: AppConfigFragmentKey, extra_config: Mapping[str, Any]
    ) -> AppConfigFragmentRow:
        return await self._db_source.update(key, extra_config)

    async def purge(self, key: AppConfigFragmentKey) -> AppConfigFragmentRow | None:
        return await self._db_source.purge(key)

    async def search(
        self,
        scope: AppConfigFragmentSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        # Scope-bound search. Cross-scope (admin) uses `admin_search`.
        return await self._db_source.search(scope=scope, querier=querier)

    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.admin_search(querier)

    # ── Merged view (AppConfig) — thin delegates to db_source ────

    async def get_app_config(
        self,
        user_id: uuid.UUID,
        config_name: str,
    ) -> AppConfigData:
        return await self._db_source.get_user_app_config(user_id, config_name)

    async def search_app_configs(
        self,
        scope: UserAppConfigSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        return await self._db_source.search_user_app_configs(
            scope, querier,
        )

    async def admin_search_app_configs(
        self,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        # Cross-user merged search (admin only). Thin delegate —
        # authorization is already enforced at the service layer.
        return await self._db_source.admin_search_app_configs(querier)
```

### Exposure

`AppConfig` exposes the contributing fragments + the deep-merge
result:

- `fragments` — ordered low → high (matches the chain). Empty only
  when no chain scope has a row, in which case the `name` itself
  doesn't appear in `myAppConfigs`. An individual fragment's `config`
  is `null` when the stored value is empty.
- `config` — deep-merge in order; `null` when every
  contributing row is empty (clients fall back to defaults).

Callers distinguish admin defaults (`scopeType = DOMAIN_USER_DEFAULTS`)
from user overrides (`scopeType = USER`) by inspecting each fragment's
`scopeType`. The REST `/v2/app-configs/my/{name}` response is the
snake_case projection of the same shape (§4).

---

## 6. Client Integration — WebUI bootstrap

The WebUI addresses configs by `(scope, scopeId, name)`. The
pre-login document set is hard-coded in the frontend — the server
publishes no bootstrap list.

### Bootstrap flow

1. **Pre-login (anonymous)** — per document, `publicAppConfigFragments`
   with a `name` filter. On no-edge / network error, fall back to
   built-in defaults. See S1 in §7.

2. **Post-login** — one `myAppConfigs` query fetches all of the
   caller's merged documents in one round trip (each entry carries
   `fragments` + `config`, §5). Admins use the same query for
   their personal settings. `DOMAIN`-scope admin UIs issue
   `DomainV2.appConfigFragments` / `adminAppConfigFragments` separately.
   See S2 in §7.

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
  publicAppConfigFragments(filter: { name: { equals: "theme" } }) {
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
        fragments { scopeType scopeId name config updatedAt }
        config
      }
    }
  }
  publicAppConfigFragments {
    edges { node { name config } }
  }
}
```

- Server: `myAppConfigs` returns one entry per `name` for which at
  least one fragment in the merge chain exists. Every such `name`
  is backed by a policy (§1 required-policy invariant), so the chain
  always comes from `AppConfigPolicy.scope_sources` — there is no
  implicit fallback chain. `fragments` carries the raw rows in chain
  order; `config` is their deep merge. See §5.
- The WebUI initializes UI state from `config` per document
  and keeps the `fragments` list around so the Settings page can
  distinguish user-changed (`scopeType = USER`) from admin-provided
  defaults (`scopeType = DOMAIN_USER_DEFAULTS`, etc.).

### S3. The user saves their own document

The user replaces their `preferences` document — e.g. language,
experimental-feature toggles, visible-column choices per table. They
call the self-service `bulkUpdateMyAppConfigFragments` — each item carries
only `name` + `config`, with `scopeType` / `scopeId` injected server-side
as `USER` + `current_user.user_id`. Even a single-item write goes
through the bulk path (1-element `items` array); the recomputed
`AppConfig` comes back as `updated[0]`, so no separate
`myAppConfigs` re-query is needed.

```graphql
mutation SaveMyConfig($input: BulkUpdateMyAppConfigFragmentInput!) {
  bulkUpdateMyAppConfigFragments(input: $input) {
    updated {
      name
      fragments { scopeType scopeId name config updatedAt }
      config
    }
    failed { index name message }
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
  `adminBulkUpdateAppConfigFragments`).
- The input `config` replaces the USER row's stored JSON wholesale.
  `AppConfig.config` is read-only computed and cannot
  be written.
- **Replace** semantics: anything the caller wants to keep must be
  sent in the same payload — there is no partial-merge or per-key
  patch.
- **Policy**: if an `AppConfigPolicy` exists for `name` and either
  `USER ∉ scope_sources` or `user_writable = False`, the item is
  appended to `failed` with a policy-violation message. Clients can
  discover this ahead of time by reading the policy via
  `appConfigPolicy(configName:)`.
- **First write vs. subsequent writes**: `bulkUpdateMyAppConfigFragments`
  places items with no USER row into `failed`. For the very first
  save of a given `name`, the client calls `bulkCreateMyAppConfigFragments`
  with the same shape. Clients can disambiguate by checking whether
  the `myAppConfigs` entry for that `name` already has a `USER` row
  in its `fragments` list.

### S4. Admin publishes an app-config policy

Before the `theme` document can be published (S8 below), an admin
establishes a policy for `theme` that restricts writes to an
admin-only scope and forbids per-user customization. The policy is
**required** (§1 required-policy invariant) — no AppConfigFragment row for
`theme` can be created until this step runs.

The choice of scope for the admin-owned value — `domain` vs
`domain_user_defaults` — is up to the admin; the two scopes carry
identical access rules and either can participate in the resolved
merge through the policy. The example below uses `domain`.

```graphql
mutation PublishThemePolicy(
  $input: AdminBulkCreateAppConfigPolicyInput!
) {
  adminBulkCreateAppConfigPolicies(input: $input) {
    created { id configName scopeSources userWritable }
    failed { index configName message }
  }
}
```

```json
{
  "input": {
    "items": [
      {
        "configName": "theme",
        "scopeSources": ["domain"],
        "userWritable": false
      }
    ]
  }
}
```

- Authorization: admin required.
- Effect:
  - Writes to `theme` at any scope other than `DOMAIN` are rejected
    at the service layer.
  - `bulk*MyAppConfigFragments` calls targeting `theme` are rejected because
    `user_writable = false`.
  - `myAppConfigs` entries for `theme` are resolved through the
    chain `[DOMAIN]` (single-scope — `fragments` has at most one
    element, and `config` equals that element's `config`
    or is `null` when the element's `config` is `null`, §3).
- Subsequent edits use `adminBulkUpdateAppConfigPolicies` with the
  same `configName`.

### S5. Varied policy shapes

Same mechanics as S4 with different `scopeSources` / `userWritable`
combinations. Each shape backs a different product decision:

- **`[user]`, `userWritable=true`** — purely user-local document.
  Admin seeding and domain defaults play no role; the resolved view
  is either the user's own row or nothing. Fits "this tab's column
  order", "editor keybindings", or other state the user alone
  authors.
- **`[domain]`, `userWritable=false`** — strict admin-owned document
  with no per-user override. Fits the default `theme` setup used in
  S4 / S8.
- **`[domain, user]`, `userWritable=true`** — admin establishes a
  baseline at `DOMAIN`, users may override it on their own `USER`
  row. The per-user merge produces the domain value plus whatever
  the user set on top. Site operators pick this shape when they want
  a default everyone starts with but individuals can customize.
- **`[domain, domain_user_defaults, user]`, `userWritable=true`** —
  three-layer chain. The admin can publish a domain-wide value
  (`DOMAIN`) as the strongest admin signal, a softer per-user seed
  (`DOMAIN_USER_DEFAULTS`) that newcomers inherit at boot, and then
  the user's own override (`USER`). Useful when the admin wants a
  "floor" (`DOMAIN`) separate from an "initial value" shipped to
  each user.

Any of the above may be switched live: an admin editing
`adminBulkUpdateAppConfigPolicies` for `theme` from `[domain]` +
`userWritable=false` to `[domain, user]` + `userWritable=true`
immediately loosens the document — existing admin rows remain, and
from the next `bulkUpdateMyAppConfigFragments` onward users can layer their
own customization on top (§7 S6).

### S6. Promoting a document from admin-only to user-customizable

A site operator initially published `theme` under the strict policy
from S4 (`scopeSources=["domain"]`, `userWritable=false`). After
user feedback, they decide individual users should be able to tweak
accent colors on top of the domain's theme.

```graphql
mutation PromoteThemePolicy(
  $input: AdminBulkUpdateAppConfigPolicyInput!
) {
  adminBulkUpdateAppConfigPolicies(input: $input) {
    updated { id configName scopeSources userWritable }
    failed { index configName message }
  }
}
```

```json
{
  "input": {
    "items": [
      {
        "configName": "theme",
        "scopeSources": ["domain", "user"],
        "userWritable": true
      }
    ]
  }
}
```

- Authorization: admin required.
- Effect:
  - No data migration — the existing `DOMAIN` row for `theme` stays
    as-is.
  - Users can now call `bulkCreate/UpdateMyAppConfigFragments` targeting
    `theme` and write their own `USER` row.
  - The next `myAppConfigs` call returns `theme` entries whose
    `fragments` is `[<DOMAIN row>, <USER row if present>]` and whose
    `config` is `domain ⊕ user`.
- Reversibility: flipping the policy back to
  `scopeSources=["domain"]` + `userWritable=false` blocks new user
  writes and excludes `USER` rows from the resolved view, but leaves
  any pre-existing `USER` rows untouched at the DB level (they
  simply stop being read). Admins who want those rows gone target
  them with `adminBulkPurgeAppConfigFragments` (see S7).

### S7. Admin fixes a misconfigured policy or config

Since `configName` is immutable (§1), a typo at policy-creation time
cannot be fixed by renaming. The admin's recovery path is a **purge
and rebuild** workflow. The mutations run in a specific order because
of the required-policy invariant:

1. If any AppConfigFragment rows already exist under the wrong `config_name`,
   purge them first — the policy cannot be purged while references
   exist.
2. Purge the wrong policy.
3. Create the correct policy.
4. Re-create any AppConfigFragment rows under the correct `config_name`.

```graphql
# Step 1 — purge the bad AppConfigFragment rows (keys identify them).
mutation PurgeBadConfigs($input: AdminBulkPurgeAppConfigFragmentInput!) {
  adminBulkPurgeAppConfigFragments(input: $input) {
    purged { scopeType scopeId name }
    failed { index scopeType scopeId name message }
  }
}

# Step 2 — purge the mis-named policy.
mutation PurgeBadPolicy($input: AdminBulkPurgeAppConfigPolicyInput!) {
  adminBulkPurgeAppConfigPolicies(input: $input) {
    purgedConfigNames
    failed { index configName message }
  }
}
```

```json
// Step 1 input
{
  "input": {
    "keys": [
      { "scopeType": "DOMAIN", "scopeId": "default", "name": "thmee" }
    ]
  }
}

// Step 2 input
{ "input": { "configNames": ["thmee"] } }
```

- Authorization: admin required on both mutations.
- Step 2 rejects the item if step 1 was skipped (or missed a row) —
  the service checks for remaining AppConfigFragment references under that
  `config_name` before purging.
- Purge is the only deletion verb in the BEP; day-to-day writes
  still flow through create / update and never remove rows on their
  own. Users cannot call purge.

### S8. Admin publishes a per-user default for a domain

The domain admin publishes the `preferences` document's per-user
default — every user in the domain inherits it at merge time as the
base for their own `USER` row. The policy for `preferences` (S5's
"`[domain_user_defaults, user]` + `userWritable=true`" shape) admits
both admin-written `DOMAIN_USER_DEFAULTS` entries and user overrides;
this scenario exercises the admin side. The first publish uses
`adminBulkCreateAppConfigFragments` with `key.scopeType =
DOMAIN_USER_DEFAULTS`; later edits use
`adminBulkUpdateAppConfigFragments` with the identical input shape.
Multiple domains can be seeded in one call by passing multiple items.

```graphql
mutation AdminCreateAppConfigFragments($input: AdminBulkCreateAppConfigFragmentInput!) {
  adminBulkCreateAppConfigFragments(input: $input) {
    created { id scopeType scopeId name config updatedAt }
    failed { index scopeType scopeId name message }
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
          "name": "preferences"
        },
        "config": { "language": "ko", "density": "comfortable" }
      }
    ]
  }
}
```

- Authorization: admin required — the service rejects non-admin
  calls on any admin-path mutation.
- Internally, the service forwards each item to
  `AppConfigFragmentRepository.create` (§2). Items whose key already
  has a row land in `failed` — the admin falls back to
  `adminBulkUpdateAppConfigFragments`.
- Policy: the write's `scope_type` must be in the policy's
  `scope_sources`. The `preferences`-style policy lists
  `DOMAIN_USER_DEFAULTS`, so this write passes. A stricter policy
  that omits the scope (e.g. the `theme` policy from S4, which
  lists only `["domain"]`) would reject the same write with a
  policy-violation message — in that case the admin would target
  `DOMAIN` instead.
- Effect: every user in the domain picks up the new defaults on the
  next `myAppConfigs` read (merged per §5).

### S9. Admin seeds a specific user's document on their behalf

For a support request, an admin seeds user A's `preferences` USER row
for the first time. Since the target is another user's row, this
must use the admin path — `adminBulkCreateAppConfigFragments` with
`key.scopeType = USER` and `key.scopeId = user A's user_id`, not the
self-service bulk path.
Items whose key already has a row land in `failed`, in which case
the admin falls back to `adminBulkUpdateAppConfigFragments`.

```graphql
mutation AdminCreateAppConfigsForUser($input: AdminBulkCreateAppConfigFragmentInput!) {
  adminBulkCreateAppConfigFragments(input: $input) {
    created { id scopeType scopeId name config updatedAt }
    failed { index scopeType scopeId name message }
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

- For `USER` scope the `config` input is stored as the user's
  customization for that `name`.
- `adminBulkCreateAppConfigFragments` fails the item if a row already exists
  for the key; use `adminBulkUpdateAppConfigFragments` instead to overwrite.
- Policy: if an `AppConfigPolicy` for `preferences` has `USER ∉
  scope_sources`, the admin path still rejects the item
  (`scope_sources` applies to both paths — admins just bypass
  `user_writable`, not the scope list). With the usual
  `preferences`-style policy (`scope_sources` includes `USER`) this
  write passes.
- The response is a list of raw `AppConfigFragment`; the target user's
  resolved view reflects the new USER row (merged with the matching
  domain defaults) on the next `myAppConfigs` read from that user's
  session.

### S10. Admin audits all AppConfigFragments (cross-scope search)

Cases such as "list every domain that touched `theme` in the last
week" or "every domain that customized the `menu` document":

```graphql
query AuditConfigs(
  $filter: AppConfigFragmentFilter!
  $orderBy: [AppConfigFragmentOrderBy!]
  $first: Int
  $after: String
) {
  adminAppConfigFragments(filter: $filter, orderBy: $orderBy, first: $first, after: $after) {
    edges {
      cursor
      node {
        id scopeType scopeId name config updatedAt
        policy { configName scopeSources userWritable }
      }
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
  mode the sort order is pinned to the cursor key.

---

## 8. Future Considerations

Items considered for this BEP but explicitly **out of scope**; each
may become a follow-up BEP if it earns its own motivation.

- **Policy seed migration** — operationally it may be useful to ship
  an initial set of policies (`theme`, `preferences`, `menu`, …) as
  part of a migration so the invariant-required policies exist on
  first deploy. This BEP does not prescribe a seed; the operational
  team picks whether to seed and with which values.
