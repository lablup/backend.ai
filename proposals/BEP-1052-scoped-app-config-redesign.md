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
>   and `userWritable=false`; see §7 S3.5).
> - `domain_user_defaults` — values positioned as per-user seeds the
>   user can override (e.g. a `preferences` policy with
>   `scope_sources=["domain_user_defaults", "user"]` and
>   `userWritable=true`; see §7 S3.6 and S4).
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
  verbs (`create` / `update` / `purge`) — `adminBulkCreateAppConfigSources`
  and siblings cover every scope, admin-only, return raw `AppConfigSource`
  lists. The self-service (my) path exposes two verbs
  (`create` / `update`) — `bulkCreateMyAppConfigSources` and siblings, with
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
- **Single source-of-truth table**: a single `app_config_sources` table holds
  every scope; only the exposure layer is split.
- **Relay style**: Input/Payload conventions and the Node interface.

---

## 1. DB Layer — `app_config_sources` table

### Schema changes

Add a `name` column to `app_config_sources`. The natural-key uniqueness
constraint becomes `(scope_type, scope_id, name)`.

```python
class AppConfigScopeType(enum.StrEnum):
    PUBLIC = "public"
    DOMAIN = "domain"
    DOMAIN_USER_DEFAULTS = "domain_user_defaults"   # per-domain defaults applied to users in that domain
    USER = "user"


@dataclass(frozen=True, slots=True)
class AppConfigSourceKey:
    """
    Natural-key identifier for a single app_config_sources row.
    Used everywhere the trio `(scope_type, scope_id, name)` would
    otherwise appear together as parameters.
    """
    scope_type: AppConfigScopeType
    scope_id: str
    name: str


class AppConfigSourceRow(Base):
    __tablename__ = "app_config_sources"

    id: Mapped[uuid.UUID]

    scope_type: Mapped[AppConfigScopeType] = mapped_column(
        StrEnumType(AppConfigScopeType, length=32), nullable=False, index=True
    )
    scope_id: Mapped[str]                     # public: literal "public"; otherwise domain_name / user_id
    name: Mapped[str] = mapped_column(        # NEW — config document name (e.g. "theme", "menu")
        sa.ForeignKey(                        # FK to `app_config_policies.config_name`.
            "app_config_policies.config_name",  # No `ON DELETE` / `ON UPDATE` specified →
        ),                                    # Postgres default `NO ACTION`, which forbids
                                              # deletion of a policy that still has
                                              # referencing rows. `config_name` is
                                              # immutable (see AppConfigPolicyRow), so
                                              # `ON UPDATE` would never fire.
        nullable=False,
    )

    extra_config: Mapped[dict[str, Any]]      # the only payload column; meaning per scope

    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    __table_args__ = (
        sa.UniqueConstraint(
            "scope_type", "scope_id", "name", name="uq_app_config_sources_scope_name"
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

`*Create*` errors if a row already exists for the natural key;
`*Update*` errors if no row exists. The only exposed deletion verb is
`*Purge*` (admin-only) — used for cleanup of misconfigured rows; see
§3. Outside of purge, rows persist once created, and callers "clear"
a document by `*Update*`-ing it to an empty JSON (`{}`). A cleared
row still exists in the DB; subsequent reads surface its `config`
as `null` (GQL/REST projections normalize empty to `null`, §3).

**A matching `app_config_policies` row is required for any write**
(see "App Config Policy table" below). The service layer enforces:

- If no policy row exists for `name`, the item is rejected with a
  policy-not-found message — `AppConfigRepository.{create,update}`
  is not called.
- `scope_type` must be in the policy's `scope_sources`; writes to
  other scopes are rejected as a per-item failure.
- When the write is on the `USER` scope via a `bulk*MyAppConfigSources`
  mutation, the policy's `user_writable` must be `True`; otherwise
  the item is rejected. The admin-path mutations are not gated by
  `user_writable` — admins may seed USER rows regardless of the
  flag.

Because every AppConfigSource row is created under a matching policy, the
resolved merge (§5) always has a chain to follow — there is no
"policy-less fallback" path.

### App Config Policy table

A separate `app_config_policies` table holds the rules per document
— which app-config rows get merged as sources into the resolved
view, and which scopes may be written. Configs and policies are
joined by `config_name` value, backed by a **FK** on
`app_config_sources.name → app_config_policies.config_name` with no
`ON DELETE` / `ON UPDATE` action (Postgres default `NO ACTION`).
The **service layer also enforces the required-policy invariant**
explicitly with friendly per-item errors; the FK is defense-in-depth
for raw SQL or any service code path that bypasses the orchestrator.

```python
class AppConfigPolicyRow(Base):
    __tablename__ = "app_config_policies"

    id: Mapped[uuid.UUID]
    config_name: Mapped[str]                  # UNIQUE — referenced by
                                              # `app_config_sources.name` via FK.
                                              # IMMUTABLE — rename is rejected
                                              # at the service layer. To "fix"
                                              # a wrongly-named policy, admins
                                              # purge the policy (and any
                                              # AppConfigSource rows that used it)
                                              # and create a new policy.
    scope_sources: Mapped[list[str]]          # Dual meaning:
                                              #   (1) which `app_config_sources` rows
                                              #       (by scope) are merged as
                                              #       sources into the resolved
                                              #       view, in order
                                              #   (2) the corresponding write
                                              #       allow-list — writes to
                                              #       scopes outside the list
                                              #       are rejected
                                              # Order is low → high priority
                                              # (later wins on deep merge).
                                              # Values align with
                                              # `AppConfigScopeType` but stored
                                              # as strings so that adding a new
                                              # scope does not require migrating
                                              # this column.
    user_writable: Mapped[bool]               # Whether the USER may write their
                                              # own USER-scope row via the
                                              # `bulk*MyAppConfigSources` path. Admin-
                                              # path writes are not gated by
                                              # this flag.
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    __table_args__ = (
        sa.UniqueConstraint("config_name", name="uq_app_config_policies_config_name"),
    )
```

**Integrity (FK + service layer)**:

- **Create**: the service layer rejects an item with a friendly
  policy-not-found message when no policy exists for `config_name`.
  If that check is ever bypassed, the FK `app_config_sources.name →
  app_config_policies.config_name` still raises a foreign-key
  violation at the DB level.
- **Policy rename**: not allowed. `config_name` is immutable —
  updates may change `scope_sources` / `user_writable` only. The
  immutability removes the "rename orphans configs" failure mode,
  and means the FK's `ON UPDATE NO ACTION` default never fires.
- **Policy deletion**: there is no `update`-level policy deletion.
  The only removal path is `adminBulkPurgeAppConfigPolicies` (§3),
  and the service rejects the purge with a per-item error unless no
  AppConfigSource row references the policy's `config_name`. If such rows
  exist, the admin purges them first via `adminBulkPurgeAppConfigSources`,
  then the policy. The FK's `ON DELETE NO ACTION` is a second line
  of defense that would raise at commit time if the service check
  were ever bypassed.
- **AppConfig deletion**: `adminBulkPurgeAppConfigSources` is an
  admin-only cleanup verb for misconfigured rows. It is **not** a
  general "delete" — the BEP's user-facing contract is still that
  rows persist once written; purge is the escape hatch for fixing
  mistakes.

The FK without cascade keeps the two tables weakly linked: the
schema forbids orphan AppConfigSource rows and refuses to drop a policy
while its configs live, but it never silently deletes data. Service
orchestration is still the primary enforcement point — the FK exists
to catch the paths that don't go through the orchestrator.

---

## 2. Repository Layer — single AppConfigSourceRepository

Keep `models/app_config_source/row.py`'s `AppConfigSourceRow` as a
single class, and use **a single `AppConfigSourceRepository`** for
all scopes. Prior drafts split the repository four ways (one per
scope); the split added surface without real benefit because each
scope variant was a thin `scope_type` / `scope_id` binding on the
same table. One scope-parameterized repository is simpler.

```
repositories/app_config_source/
├── db_source/
│   └── db_source.py                  # single db_source
├── app_config_source_repository.py   # all scopes; AppConfigSourceKey-addressed
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
| `AppConfigSourceRepository`  | Scope-parameterized CRUD (`get / get_by_id / create / update / purge`) taking an `AppConfigSourceKey`. `search(scope, querier)` for a bound scope (via `AppConfigSourceSearchScope`), `admin_search(querier)` for cross-scope (admin). Plus merge-specific reads that serve the merged view (`AppConfig`): `get_app_config(user_id, name, chain)`, `search_app_configs(scope, querier)` (`UserAppConfigSearchScope`; chain derived in SQL via policy join) — see §5. |
| `AppConfigPolicyRepository`  | `get(config_name)`, `get_by_id(id)`, `create(config_name, scope_sources, user_writable)`, `update(config_name, scope_sources, user_writable)`, `purge(config_name)`, `search(querier)`. Updates do not touch `config_name` (immutable — §1). The `purge` call rejects at the service layer if any `AppConfigSource` row still references the `config_name`. |

`AppConfigSourceRepository` plays a **dual role** — raw row CRUD
across every scope (served to GQL as `AppConfigSource`) + read-side
merged view (served as `AppConfig`, see §5). It takes a single
`AppConfigSourceDBSource`; the user → domain_name resolution needed
by the merge is done inside the merge-specific DB method via a
`users` subquery in a single SQL, so no separate `UserDBSource` is
injected. The GraphQL schema exposes raw `AppConfigSource` rows
(regardless of scope) and the merged `AppConfig` as separate types,
but internally they share this one repository — there is no separate
`AppConfigRepository`.


### `db_source` is a single module

The underlying table is the same, so the ORM query builder is managed
in one place.

```python
class AppConfigSourceDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get(self, key: AppConfigSourceKey) -> AppConfigSourceRow | None:
        async with self._db.begin_readonly_session() as db_sess:
            ...

    async def get_by_id(self, id: uuid.UUID) -> AppConfigSourceRow | None:
        # ID-based lookup for Actions that have already resolved the
        # natural key to a row id (see §3 "Name → ID resolution").
        async with self._db.begin_readonly_session() as db_sess:
            ...

    async def create(
        self,
        key: AppConfigSourceKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigSourceRow:
        # Strict insert. Errors if any row already exists for the
        # natural key.
        async with self._db.begin_session() as db_sess:
            ...

    async def update(
        self,
        key: AppConfigSourceKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigSourceRow:
        # Replace the existing row's value with `extra_config`.
        # Errors if no row exists for the natural key.
        async with self._db.begin_session() as db_sess:
            ...

    async def search(
        self,
        scope: AppConfigSourceSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSourceSearchResult:
        # Within-scope search — binds (scope_type, scope_id) via the
        # `scope`'s `to_condition()` and delegates the rest to the
        # shared `execute_batch_querier` helper (conditions, orders,
        # and pagination). Cross-scope search is `admin_search` below.
        # The merge-specific search lives in §5.
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigSourceRow)
            result = await execute_batch_querier(
                db_sess, query, querier, scope=scope,
            )
            items = [row.AppConfigSourceRow.to_data() for row in result.rows]
            return AppConfigSourceSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigSourceSearchResult:
        # Cross-scope admin search — no scope binding. Authorization
        # is enforced at the service layer before this is reached.
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigSourceRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.AppConfigSourceRow.to_data() for row in result.rows]
            return AppConfigSourceSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
```

Listing is expressed via the `search` primitive — callers build a
`AppConfigSourceSearchScope(scope_type, scope_id)` plus a
`BatchQuerier` and pass both in. Permission checks and scope
validation are performed in the service layer; the db_source only
runs the resulting SQL.

**Bulk mutation orchestration**: all AppConfigSource bulk mutations
(`adminBulk{Create,Update,Purge}AppConfigSources`,
`bulk{Create,Update}MyAppConfigSources`) follow the same service-layer
orchestration — each item runs in its own DB transaction so a
single failure doesn't abort the rest (partial success), successes
and failures collected into `BulkActionResult(success_list,
failed_list)`. The service preserves each item's original position
in the input list so the GQL/REST adapters can populate the
per-verb error type's `index` field (see §3 error types), matching
the existing `BulkCreateUserV2Error` / `BulkPurgeUserV2Error`
convention elsewhere in the codebase. Admin bulk dispatches each
item on `item.key` to `AppConfigSourceRepository.{create,update,purge}`;
my bulk does the same with `item.key.scopeType = USER` +
`scopeId = current_user.user_id` injected server-side. Not optimized
as a single SQL batch: items split by scope can fail for
heterogeneous reasons (unique-key violations, authorization errors,
…), and representing partial success in one SQL statement is
awkward.

The admin policy bulk mutations
(`adminBulk{Create,Update,Purge}AppConfigPolicies`) follow the same
per-item / partial-success pattern against `AppConfigPolicyRepository`.
`Update` rejects items that attempt to change `configName`
(immutable, §1). `Purge` rejects items whose `configName` still has
referencing `AppConfigSource` rows, preserving the required-policy
invariant for the rows that remain.

Search inputs align with the shared **BatchQuerier** pattern used
by other repositories (`repositories/base/querier.py`):

- `AppConfigSourceSearchScope(SearchScope)` — a
  `@dataclass(frozen=True)` carrying `scope_type` + `scope_id`; its
  `to_condition()` emits the `(AppConfigSourceRow.scope_type == … AND
  AppConfigSourceRow.scope_id == …)` predicate, and
  `existence_checks` is empty (no FK lookup to validate).
  Lives alongside `AppConfigSourceSearchResult` in
  `repositories/app_config_source/types.py`.
- `BatchQuerier` — shared container for `conditions` (derived from
  the GraphQL `AppConfigSourceFilter` at the adapter boundary),
  `orders`, and `pagination`. Built by the service/adapter before
  calling the repository; the db_source passes it through to
  `execute_batch_querier`.
- `AppConfigSourceSearchResult` — `@dataclass` with `items`,
  `total_count`, `has_next_page`, `has_previous_page`, matching the
  shape used by `GroupSearchResult` / `UserSearchResult`.

The GraphQL `AppConfigSourceFilter` (§3) remains the wire-format
input; the adapter translates it into `BatchQuerier.conditions`
plus `AppConfigSourceSearchScope` for per-scope reads, or
into `BatchQuerier.conditions` alone for `admin_search`. Concrete
filter-to-condition translation is left to the implementation
phase.

### Policy repository

`AppConfigPolicyRepository` lives under
`repositories/app_config_policy/` with its own
`AppConfigPolicyDBSource`. It is intentionally kept separate from
`AppConfigSourceDBSource` — the tables share no FK and no joined query
surface, so collapsing them would bind two independent lifecycles
together. The policy repository exposes the same six-operation shape
(`get` / `get_by_id` / `create` / `update` / `search`; `delete` /
`purge` omitted per the BEP-1052 write policy).

Write orchestration for `app_config_sources` consults the policy repository
at the **service layer**, not inside `AppConfigRepository`. For each
batch, the service collects the distinct `name`s, calls
`AppConfigPolicyRepository.get(config_name)` (caching within the
batch so a single policy is read once), and threads the result into
per-item validation:

- If no policy row exists for `config_name`, the item is rejected
  with a policy-not-found message — this enforces the
  required-policy invariant (§1).
- If the policy row is present and `item.key.scopeType ∉
  scope_sources`, the item is appended to `failed_list` with a
  policy-violation message.
- If the item is on the `bulk*MyAppConfigSources` path, the policy is
  present, and `user_writable` is `False`, the item is likewise
  rejected without touching `AppConfigRepository`.

The policy repository's own `update` method refuses to change
`config_name` (immutable per §1). `AppConfigPolicyRepository.purge`
first runs a reference check via `AppConfigSourceDBSource` — if any
`app_config_sources` row exists with matching `name`, the purge is rejected
so the required-policy invariant cannot be broken retroactively.

Reads do not consult the policy repository from within
`AppConfigRepository`. The merge service (§5) performs its own policy
lookup when assembling a `AppConfig` because the chain order
depends on it; per-scope raw reads do not.

---

## 3. GraphQL Schema — per-entity exposure

### Types

There are two GQL types for app-config data:

- `AppConfigSource` — one raw row from `app_config_sources`, regardless of scope.
  Carries `scopeType` + `scopeId` + `name` + `config` + `policy` so
  callers can disambiguate across scopes at read time. Defined
  further below (after the inputs/payloads that also reference it).
- `AppConfig` — the merged per-user view backed by the
  matching `AppConfigPolicy.scope_sources` chain (§5).

Per-scope wrapper types (historical `PublicAppConfig`,
`DomainAppConfig`, `UserAppConfig`) are **not** defined — they offered
no information a single `AppConfigSource` type doesn't and added three
Connection / Edge / filter triples of boilerplate. Callers
disambiguate scope by reading `AppConfigSource.scopeType` instead.

```graphql
"""
Resolved app-config view from the current user's perspective —
accessible via `myAppConfigs` or `node(id)`. Deep-merges same-`name`
source rows in the order prescribed by the matching
`AppConfigPolicy.scope_sources`. Every `name` that appears here is
backed by a policy (§1 required-policy invariant), so the chain is
always defined by data. An entry appears whenever at least one
source row exists.

Although derived, `AppConfig` implements `Node` — the
`(user_id, name)` composite is encoded as a server-side global ID
(`base64("AppConfig:{user_id}:{name}")`). The `node(id)`
resolver decodes the id and returns the merged view only when
`decoded.user_id == current_user.id`. There is no admin override:
`AppConfig` is strictly the *current user's* resolved view,
and admins do not get a path to see another user's resolved
configuration through this type.
"""
type AppConfig implements Node {
  """
  Server-encoded global ID — `base64("AppConfig:{user_id}:{name}")`.
  """
  id: ID!

  """Document name (unique within this user)."""
  name: String!

  """
  Raw source rows that contributed to `mergedConfig`, in merge order
  (low → high priority; later wins). The list matches the order of
  the matching policy's `scope_sources` — every `name` returned
  through `myAppConfigs` has a policy (§1). Each element is a raw
  `AppConfigSource` so callers can distinguish
  "admin-provided per-user default" from "what the user changed" by
  inspecting `scopeType`.
  """
  sources: [AppConfigSource!]!

  """
  Effective applied value: deep merge of `sources` in order (left =
  lowest priority, right = highest). Clients render the UI from this
  value. `null` when the merge result is empty — every contributing
  `sources` row has an empty stored `config`, so there is no applied
  value. Clients treat `null` identically to "no value configured"
  and fall back to their built-in defaults.
  """
  mergedConfig: JSON
}
```

### Added/extended fields (Relationship)

| Location      | Field                                                                                  |
|---------------|----------------------------------------------------------------------------------------|
| `DomainV2` | `appConfigs(filter, orderBy, ...pagination): AppConfigSourceConnection!` (`scopeType = DOMAIN`, `scopeId = domain_name` pinned) |
| `UserV2`   | `appConfigs(filter, orderBy, ...pagination): AppConfigSourceConnection!` (`scopeType = USER`, `scopeId = user_id` pinned)       |

### Permissions

Each `appConfigSources` child field enforces its own access rule (not
simply inherited from the parent node) — see the permission matrix
below. In short: `DomainV2.appConfigSources` is same-domain users or
admin; `UserV2.appConfigSources` is owner or admin. Writes (mutations) on
both are admin-only.

```graphql
extend type DomainV2 {
  """
  App config documents owned by this domain (DOMAIN scope rows).
  Read access: same-domain users or admin. Write (via mutations) is
  admin only. Filter by `name` (or any combination) to retrieve a
  single document. `filter.scopeType` / `filter.scopeId` are ignored —
  already pinned to this domain.
  """
  appConfigSources(
    filter: AppConfigSourceFilter = null
    orderBy: [AppConfigSourceOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigSourceConnection!
}

extend type UserV2 {
  """
  App config documents owned by this user. Owner or admin only.
  Filter by `name` to retrieve a single document. `filter.scopeType` /
  `filter.scopeId` are ignored — already pinned to this user.
  """
  appConfigSources(
    filter: AppConfigSourceFilter = null
    orderBy: [AppConfigSourceOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigSourceConnection!
}
```

A root field `myAppConfigs` (Connection) returns the current user's
**merged view** (`AppConfig`) — different from the raw USER rows
exposed by `UserV2.appConfigSources` (raw `AppConfigSource`). Merging only
happens on this path (§5).

### Queries

```graphql
type Query {
  """
  Public config documents (no auth). Filter by `name` to retrieve a
  single document.
  """
  publicAppConfigSources(
    filter: AppConfigSourceFilter = null
    orderBy: [AppConfigSourceOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigSourceConnection!

  """
  Current user's merged app-config view (auth required). Deep-merges
  `(DOMAIN_USER_DEFAULTS, user.domain_name)` + `(USER, user.user_id)`
  per `name` (see §5). `DOMAIN` scope is not a merge input — domain
  policy is exposed only through admin paths. Filter by `name` to
  retrieve a single document. `filter.scopeType` / `filter.scopeId`
  are ignored here — the scope is pinned.
  """
  myAppConfigs(
    filter: AppConfigSourceFilter = null
    orderBy: [AppConfigSourceOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigSourceConnection!

  """
  Cross-scope AppConfigSource search (Admin only). Returns a Relay
  Connection with filter / order / pagination applied.
  """
  adminAppConfigSources(
    filter: AppConfigSourceFilter = null
    orderBy: [AppConfigSourceOrderBy!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigSourceConnection!

  """
  Single app-config policy by the governed document's `configName`.
  Any authenticated user may read; policies are advisory and not
  secret.
  """
  appConfigPolicy(configName: String!): AppConfigPolicy

  """
  Relay Connection over app-config policies. Any authenticated user
  may read.
  """
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

Filter and orderBy types are unified — a single `AppConfigSourceFilter`
and `AppConfigSourceOrderBy` are reused across all Connections. With the
per-scope types collapsed into one, the same `AppConfigSourceConnection`
backs every raw-row query — `publicAppConfigSources`, `adminAppConfigSources`,
`DomainV2.appConfigSources`, and `UserV2.appConfigSources`. Each call pins the
relevant `scopeType` / `scopeId` internally and returns the same
Edge / node shape.

```graphql
# ── Connections ───────────────────────────────────────────────

"""Relay Connection holding raw `AppConfigSource` rows from any scope."""
type AppConfigSourceConnection {
  edges: [AppConfigSourceEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type AppConfigSourceEdge {
  cursor: String!
  node: AppConfigSource!
}

"""Relay Connection holding the current user's merged view — backs `myAppConfigs`."""
type AppConfigSourceConnection {
  edges: [AppConfigSourceEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type AppConfigSourceEdge {
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
AppConfigSource search filter. Scalar fields at the top level are
AND-combined. For arbitrary boolean shapes, nest predicates under
`AND` / `OR` / `NOT`.
"""
input AppConfigSourceFilter {
  """
  Filter by scope type. Meaningful only on `adminAppConfigSources`; on
  per-scope Connections (`publicAppConfigSources`, `DomainV2.appConfigSources`,
  `UserV2.appConfigSources`, `myAppConfigs`) the scope
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

  """All sub-filters must match (AND combination)."""
  AND: [AppConfigSourceFilter!] = null

  """At least one sub-filter must match (OR combination)."""
  OR: [AppConfigSourceFilter!] = null

  """None of the sub-filters may match (NOT combination)."""
  NOT: [AppConfigSourceFilter!] = null
}

"""EnumFilter for AppConfigScopeType (equals / in / notEquals / notIn)."""
input AppConfigScopeTypeEnumFilter {
  equals: AppConfigScopeType
  in: [AppConfigScopeType!]
  notEquals: AppConfigScopeType
  notIn: [AppConfigScopeType!]
}

input AppConfigSourceOrderBy {
  field: AppConfigSourceOrderField!
  direction: OrderDirection! = ASC
}

"""
`SCOPE_TYPE` / `SCOPE_ID` are only useful on `adminAppConfigSources`; on
per-scope Connections they degenerate to a constant and have no
effect. `UPDATED_AT` / `CREATED_AT` apply to raw-row Connections
only — `myAppConfigs` returns `AppConfig` (derived) which does
not expose timestamps, so these order keys fall back to `NAME`
internally in that context.
"""
enum AppConfigSourceOrderField {
  SCOPE_TYPE
  SCOPE_ID
  NAME
  UPDATED_AT
  CREATED_AT
}

"""Filter for `appConfigPolicies`."""
input AppConfigPolicyFilter {
  """Filter on `config_name` (the governed document's name)."""
  configName: StringFilter = null

  """Filter on `user_writable`."""
  userWritable: BooleanFilter = null

  """`created_at` range filter."""
  createdAt: DateTimeFilter = null

  """`updated_at` range filter."""
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

All write mutations are **bulk-only** — there are no single-item
variants (pass a 1-element array if you only need one). Split into an
**admin path** (create / update / purge) and a **self-service (my)
path** (create / update only), plus an admin-only policy path
(create / update / purge), for a total of eight mutations:

- `adminBulk{Create,Update,Purge}AppConfigSources`: each item carries an
  `AppConfigSourceKey { scopeType, scopeId, name }` — covers every scope.
  **Admin-only**. `Create` / `Update` return a list of raw
  `AppConfigSource`; `Purge` returns the purged key list. All three
  return per-item failures.
- `bulk{Create,Update}MyAppConfigSources`: each item carries only `name`
  (scope is `USER` + `scopeId = current_user.user_id` injected
  server-side). Callable by any authenticated user for their own
  documents. Returns a list of recomputed `AppConfig` + a
  list of per-item failures. **No `Purge` on the my-path** — users
  cannot delete rows; only admins do cleanup.
- `adminBulk{Create,Update,Purge}AppConfigPolicies`: each item
  carries `configName` (+ policy fields on create/update).
  **Admin-only**. `Update` rejects any attempt to change
  `configName` (immutable — §1). `Purge` rejects any item whose
  `configName` still has AppConfigSource rows referencing it.

**Partial success**: every bulk mutation runs each item in its own
DB transaction — a single failure does not abort the rest, and the
payload separates successes from failures. Single-item callers get
the same shape, so error handling is uniform.

Routing:
- Admin-path: the service forwards each item's `key` to
  `AppConfigSourceRepository` — a single scope-parameterized
  repository (§2). Items across different scopes may be mixed in
  one call.
- My-path: the server synthesizes
  `(USER, current_user.id, item.name)` and calls the same
  `AppConfigSourceRepository`.

Authorization is enforced in the **service layer** (see permission
matrix below).

```graphql
type Mutation {
  # ── Admin path — every scope, admin-only ─────────────────────

  """
  Bulk-create app config documents (admin-only). Each item is a
  strict insert — if any row already exists for the natural key,
  that item fails. Items may target any scope; admin-side seeding
  of a `USER`-scope row is also done via this mutation.
  """
  adminBulkCreateAppConfigSources(input: AdminBulkCreateAppConfigSourceInput!): AdminBulkCreateAppConfigSourcesPayload!

  """
  Bulk-update app config documents (admin-only). Each item replaces
  the existing row's stored JSON wholesale. If no row exists for
  the natural key, that item fails.
  """
  adminBulkUpdateAppConfigSources(input: AdminBulkUpdateAppConfigSourceInput!): AdminBulkUpdateAppConfigSourcesPayload!

  """
  Bulk-purge app config documents (admin-only). Each item is
  identified by `AppConfigSourceKey`; if no row exists for the key, the
  item is no-oped (returned in `purged` with the key alone). Purge
  is the only deletion verb for AppConfigSource — intended for cleaning up
  misconfigured rows; day-to-day writes should use create / update.
  """
  adminBulkPurgeAppConfigSources(input: AdminBulkPurgeAppConfigSourceInput!): AdminBulkPurgeAppConfigSourcesPayload!

  # ── Self-service (my) path — USER + current_user implicit ────

  """
  Bulk-create the current user's `USER`-scope documents (auth
  required). Each item has `name` + `config`;
  `scopeId = current_user.user_id` is injected server-side. Strict
  insert — if a USER row already exists for a `name`, that item
  fails.
  """
  bulkCreateMyAppConfigSources(input: BulkCreateMyAppConfigSourceInput!): BulkCreateMyAppConfigSourcesPayload!

  """
  Bulk-replace the current user's `USER`-scope documents (auth
  required). Items whose USER row is missing fail.
  """
  bulkUpdateMyAppConfigSources(input: BulkUpdateMyAppConfigSourceInput!): BulkUpdateMyAppConfigSourcesPayload!

  # ── Admin policy path — admin-only ─────────────────────────

  """
  Bulk-create app-config policies (admin-only). Each item is a strict
  insert keyed on `name`; if a policy already exists for that `name`
  the item fails.
  """
  adminBulkCreateAppConfigPolicies(
    input: AdminBulkCreateAppConfigPolicyInput!
  ): AdminBulkCreateAppConfigPoliciesPayload!

  """
  Bulk-update app-config policies (admin-only). Each item replaces
  the matching policy row by `configName`; items whose `configName`
  has no policy row fail. `configName` itself is immutable (§1) —
  service rejects any attempt to change it.
  """
  adminBulkUpdateAppConfigPolicies(
    input: AdminBulkUpdateAppConfigPolicyInput!
  ): AdminBulkUpdateAppConfigPoliciesPayload!

  """
  Bulk-purge app-config policies (admin-only). An item fails if any
  `AppConfigSource` row still references its `configName` (the
  required-policy invariant must hold for the remaining rows);
  admins clean such rows up first via `adminBulkPurgeAppConfigSources`.
  """
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
Mirrors the Python `AppConfigSourceKey` dataclass used by the repository /
db_source layer.
- `PUBLIC`:               `scopeId` is the literal string `"public"`.
- `DOMAIN`:               `scopeId` is `domain_name`.
- `DOMAIN_USER_DEFAULTS`: `scopeId` is `domain_name`.
- `USER`:                 `scopeId` is `user_id` (UUID string).
- `name` is the document name (unique within the scope).
"""
input AppConfigSourceKey {
  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
}

# ── Admin Inputs — per-item + bulk wrappers ──────────────────

"""Per-item input for admin bulk create/update (key + config)."""
input AdminAppConfigSourceItemInput {
  """Target row identifier."""
  key: AppConfigSourceKey!

  """
  Stored value — initial on create, wholesale replacement on update.
  Pass `{}` to clear.
  - `PUBLIC` / `DOMAIN` / `DOMAIN_USER_DEFAULTS`: the document's `config`.
  - `USER`: that user's customized value for this `name` (the
    `AppConfig` merged view is read-only computed).
  """
  config: JSON!
}

input AdminBulkCreateAppConfigSourceInput {
  """Items to create. No schema-level cap; service applies a reasonable one."""
  items: [AdminAppConfigSourceItemInput!]!
}

input AdminBulkUpdateAppConfigSourceInput {
  """Items to update."""
  items: [AdminAppConfigSourceItemInput!]!
}

"""
Per-item input for `adminBulkPurgeAppConfigSources`. Identified by key
alone — there is no `config` payload.
"""
input AdminBulkPurgeAppConfigSourceInput {
  """Keys identifying the rows to purge."""
  keys: [AppConfigSourceKey!]!
}

# ── My Inputs — scope=USER, scopeId=current_user.user_id implicit ──

"""Per-item input for my bulk create/update (name + config)."""
input MyAppConfigSourceItemInput {
  """Document name (unique within the current user)."""
  name: String!

  """
  Value to store on the caller's `USER` row for this `name` —
  initial on create, wholesale replacement on update. Pass `{}` to
  clear. `AppConfig.mergedConfig` is read-only computed and
  cannot be written.
  """
  config: JSON!
}

input BulkCreateMyAppConfigSourceInput {
  """Items to create."""
  items: [MyAppConfigSourceItemInput!]!
}

input BulkUpdateMyAppConfigSourceInput {
  """Items to update."""
  items: [MyAppConfigSourceItemInput!]!
}

# ── Admin Payloads — return lists of raw AppConfigSource ───────────

"""Per-item error info for `adminBulkCreateAppConfigSources`."""
type AdminBulkCreateAppConfigSourceError {
  """Original position in the input list."""
  index: Int!
  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
  message: String!
}

"""Per-item error info for `adminBulkUpdateAppConfigSources`."""
type AdminBulkUpdateAppConfigSourceError {
  """Original position in the input list."""
  index: Int!
  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
  message: String!
}

"""Per-item error info for `adminBulkPurgeAppConfigSources`."""
type AdminBulkPurgeAppConfigSourceError {
  """Original position in the input list."""
  index: Int!
  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!
  message: String!
}

"""Result of `adminBulkCreateAppConfigSources`. Partial success."""
type AdminBulkCreateAppConfigSourcesPayload {
  """Successfully created rows."""
  created: [AppConfigSource!]!

  """Per-item errors for entries that failed to create."""
  failed: [AdminBulkCreateAppConfigSourceError!]!
}

"""Result of `adminBulkUpdateAppConfigSources`. Partial success."""
type AdminBulkUpdateAppConfigSourcesPayload {
  """Rows after replacement."""
  updated: [AppConfigSource!]!

  """Per-item errors for entries that failed to update."""
  failed: [AdminBulkUpdateAppConfigSourceError!]!
}

"""Result of `adminBulkPurgeAppConfigSources`. Partial success."""
type AdminBulkPurgeAppConfigSourcesPayload {
  """Keys of rows actually removed (or already absent → no-op)."""
  purged: [AppConfigSourceKey!]!

  """Per-item errors for entries that failed to purge."""
  failed: [AdminBulkPurgeAppConfigSourceError!]!
}

# ── My Payloads — return lists of resolved AppConfig ────

"""
Per-item error info for `bulkCreateMyAppConfigSources`. (scope / scopeId
are server-injected, so `name` is the only identifier.)
"""
type BulkCreateMyAppConfigSourceError {
  """Original position in the input list."""
  index: Int!
  name: String!
  message: String!
}

"""Per-item error info for `bulkUpdateMyAppConfigSources`."""
type BulkUpdateMyAppConfigSourceError {
  """Original position in the input list."""
  index: Int!
  name: String!
  message: String!
}

"""Result of `bulkCreateMyAppConfigSources`. Partial success."""
type BulkCreateMyAppConfigSourcesPayload {
  """Recomputed `AppConfig` list after the writes."""
  created: [AppConfig!]!

  """Per-item errors for entries that failed to create."""
  failed: [BulkCreateMyAppConfigSourceError!]!
}

"""Result of `bulkUpdateMyAppConfigSources`. Partial success."""
type BulkUpdateMyAppConfigSourcesPayload {
  """Recomputed `AppConfig` list after the writes."""
  updated: [AppConfig!]!

  """Per-item errors for entries that failed to update."""
  failed: [BulkUpdateMyAppConfigSourceError!]!
}

# ── Admin Policy Inputs / Payloads ──────────────────────────

"""Per-item input for `adminBulkCreate/UpdateAppConfigPolicies`."""
input AdminAppConfigPolicyItemInput {
  """Governed document's `configName` (unique across the policies table)."""
  configName: String!

  """
  Scopes whose rows are merged as sources into the resolved view,
  in order (low → high priority). Also acts as the write allow-list.
  """
  scopeSources: [String!]!

  """Whether the owner may write their own `USER`-scope row."""
  userWritable: Boolean!
}

input AdminBulkCreateAppConfigPolicyInput {
  items: [AdminAppConfigPolicyItemInput!]!
}

input AdminBulkUpdateAppConfigPolicyInput {
  items: [AdminAppConfigPolicyItemInput!]!
}

"""
Per-item input for `adminBulkPurgeAppConfigPolicies`. Identified by
`configName` alone.
"""
input AdminBulkPurgeAppConfigPolicyInput {
  configNames: [String!]!
}

"""Per-item error info for `adminBulkCreateAppConfigPolicies`."""
type AdminBulkCreateAppConfigPolicyError {
  """Original position in the input list."""
  index: Int!
  configName: String!
  message: String!
}

"""Per-item error info for `adminBulkUpdateAppConfigPolicies`."""
type AdminBulkUpdateAppConfigPolicyError {
  """Original position in the input list."""
  index: Int!
  configName: String!
  message: String!
}

"""Per-item error info for `adminBulkPurgeAppConfigPolicies`."""
type AdminBulkPurgeAppConfigPolicyError {
  """Original position in the input list."""
  index: Int!
  configName: String!
  message: String!
}

"""Result of `adminBulkCreateAppConfigPolicies`. Partial success."""
type AdminBulkCreateAppConfigPoliciesPayload {
  """Successfully created policies."""
  created: [AppConfigPolicy!]!

  """Per-item errors for entries that failed to create."""
  failed: [AdminBulkCreateAppConfigPolicyError!]!
}

"""Result of `adminBulkUpdateAppConfigPolicies`. Partial success."""
type AdminBulkUpdateAppConfigPoliciesPayload {
  """Policies after replacement."""
  updated: [AppConfigPolicy!]!

  """Per-item errors for entries that failed to update."""
  failed: [AdminBulkUpdateAppConfigPolicyError!]!
}

"""Result of `adminBulkPurgeAppConfigPolicies`. Partial success."""
type AdminBulkPurgeAppConfigPoliciesPayload {
  """`configName`s of policies actually removed."""
  purgedConfigNames: [String!]!

  """Per-item errors for entries that failed to purge."""
  failed: [AdminBulkPurgeAppConfigPolicyError!]!
}

"""
Generic AppConfigSource type shared by the admin-path payloads,
`adminAppConfigSources`, and `node(id)`. Exposes the raw stored value.
Thin by design — no back-references to the parent `DomainV2` /
`UserV2`; callers that need the parent object re-query
`domain_v2(name:)` / `admin_user_v2(user_id:)` explicitly.
"""
type AppConfigSource implements Node {
  """
  Relay global ID — `base64("AppConfigSource:<row_uuid>")`. The distinct
  prefix lets `node(id)` dispatch correctly between `AppConfigSource` and
  `AppConfig`.
  """
  id: ID!

  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!

  """
  Raw stored value (`extra_config`). For USER scope this is the
  user-customized value, not the merged result. `null` when the
  stored value is empty — e.g. a row that was cleared via `*Update*`
  with an empty payload (see §1 "Write semantics"). The DB still
  holds the row; the GraphQL projection normalizes "empty" to
  `null` so clients never see a bare `{}`.
  """
  config: JSON

  """
  The matching `AppConfigPolicy` (joined by `name` = `config_name`).
  Non-null because the required-policy invariant (§1) guarantees a
  policy exists for every AppConfigSource row. Resolved via a per-request
  `DataLoader` keyed on `name`, so selecting this field inside a
  Connection does not N+1 — a single batched lookup covers the page.
  Callers that just want the raw row can omit the selection.
  """
  policy: AppConfigPolicy!

  createdAt: DateTime!
  updatedAt: DateTime!
}

# ── App Config Policy ────────────────────────────────────────

"""
Advisory policy for an app-config document — controls which scopes'
rows are merged as sources into `AppConfig` (§5) and which
scopes may be written. Policies are decoupled from `AppConfigSource` rows
at the schema level (§1 "App Config Policy table"): there is no FK,
and configs and policies are joined by `configName` value only at
runtime.

Read: any authenticated user. Write: admin only, via
`adminBulkCreate/UpdateAppConfigPolicies`.
"""
type AppConfigPolicy implements Node {
  """
  Relay global ID — `base64("AppConfigPolicy:<row_uuid>")`.
  """
  id: ID!

  """
  The governed document's `name` (unique across the policies table).
  Joined to `AppConfigSource.name` by value only — no FK. **Immutable** —
  `update` cannot change this field. A wrongly-named policy is fixed
  by purging (along with any referencing rows) and recreating — see
  §7 S3.8.
  """
  configName: String!

  """
  Dual meaning: (1) which `AppConfigSource` rows (by `scopeType`) are
  merged as sources into the resolved view, in order, and (2) the
  corresponding write allow-list — writes to scopes outside the list
  are rejected. Order is low → high priority; the last element wins
  on deep merge. Values align with `AppConfigScopeType` but are
  stored as strings so that adding a new scope does not require
  migrating this column.
  """
  scopeSources: [String!]!

  """
  Whether the owner may write their own `USER`-scope row for this
  document via the `bulk*MyAppConfigSources` path. The admin path is not
  gated by this flag — admins may seed USER rows regardless.
  """
  userWritable: Boolean!

  createdAt: DateTime!
  updatedAt: DateTime!
}
```

### Permission matrix

Queries:

| Operation                          | Anonymous | User                             | Admin |
|------------------------------------|-----------|----------------------------------|-------|
| `publicAppConfigSources`                 | ✅        | ✅                               | ✅    |
| `myAppConfigs`                     | ❌        | ✅ (self)                        | ✅    |
| `DomainV2.appConfigSources`              | ❌        | ✅ (same domain only)            | ✅    |
| `UserV2.appConfigSources`                | ❌        | ✅ (self)                        | ✅    |
| `adminAppConfigSources`                  | ❌        | ❌                               | ✅    |
| `appConfigPolicy` / `appConfigPolicies` | ❌   | ✅                               | ✅    |
| `node(id)` → `AppConfigSource`           | ✅ iff row `scopeType = PUBLIC` | ✅ (PUBLIC always; DOMAIN / DOMAIN_USER_DEFAULTS same-domain only; USER self only) | ✅ |
| `node(id)` → `AppConfig`   | ❌        | ✅ (id's `user_id` is self)      | ✅ (id's `user_id` is self) |
| `node(id)` → `AppConfigPolicy`     | ❌        | ✅                               | ✅    |

Write mutations split into two paths with distinct rules. All
bulk-only.

**Admin path** — `adminBulkCreateAppConfigSources`,
`adminBulkUpdateAppConfigSources`. Admin regardless of each item's
`key.scopeType`:

| Operation                                  | Anonymous | User | Admin |
|--------------------------------------------|-----------|------|-------|
| `adminBulk{Create,Update,Purge}AppConfigSources` | ❌        | ❌   | ✅    |

**Self-service (my) path** — `bulkCreateMyAppConfigSources`,
`bulkUpdateMyAppConfigSources`. Imply `scope = USER` +
`scopeId = current_user.user_id`:

| Operation              | Anonymous | User (self) | Admin (self) |
|------------------------|-----------|-------------|--------------|
| `bulk*MyAppConfigSources`    | ❌        | ✅          | ✅           |

> Admins operating on another user's `USER` row must use the admin
> path with an explicit `AppConfigSourceKey { scopeType: USER, scopeId:
> target_user_id, name }` on each item — the my path cannot target
> another user.

**Admin policy path** — `adminBulkCreateAppConfigPolicies`,
`adminBulkUpdateAppConfigPolicies`,
`adminBulkPurgeAppConfigPolicies`:

| Operation                                           | Anonymous | User | Admin |
|-----------------------------------------------------|-----------|------|-------|
| `adminBulk{Create,Update,Purge}AppConfigPolicies`   | ❌        | ❌   | ✅    |

Where the checks live:
- Admin-path resolvers: `check_admin_only()` at entry, then dispatch
  each item on `item.key.scopeType` to the matching repository (§2). No
  silent reinterpretation of `scopeId` — partial-success means some
  items may succeed while others fail, but non-admin callers are
  rejected up-front.
- My-path resolvers: reject anonymous callers, then resolve
  `current_user` and delegate each item to
  `AppConfigSourceRepository.{create|update}` —
  `scopeId` is not part of the input and is injected server-side.
- `DomainV2.appConfigSources` field resolver: if the caller is not admin
  and the parent `DomainV2.domain_name` differs from
  `current_user.domain_name`, raise a permission error (helper in
  `src/ai/backend/manager/api/gql/utils.py` raises
  `web.HTTPForbidden`). Same-domain users and admins are allowed
  through. Writes (mutations) remain admin-only.
- `UserV2.appConfigSources` field resolver: raises a permission error
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
3. Dispatch the ID-based Action (`update`) to the repository. A
   failure on this item lands in `failed` while the remaining items
   continue.

My-path mutations (`bulkCreateMyAppConfigSources`, etc.) **skip this step**:
scope / scopeId are fixed server-side (`USER`,
`current_user.user_id`), RBAC only needs to confirm "authenticated
self", and each item calls
`AppConfigSourceRepository.{create|update}` with
`user_id` + `item.name` directly.

The result: admin-path Actions stay uniform (ID-only) while the API
surface still accepts natural-key identification — clients never
need to know row IDs.

The `adminBulk*AppConfigPolicies` mutations follow the same
ID-resolve pattern using `AppConfigPolicyRepository.get(name)` to
look up the policy row's id before dispatching the update Action.

---

## 4. REST Schema

REST exposes three prefix trees that mirror the GQL surface:

- `/v2/app-config-sources/...` — raw source row operations (admin
  CRUD, cross-scope search, per-scope reads, my-path writes).
- `/v2/app-configs/my[/{name}]` — **merged `AppConfig` view** per
  user (read-only; writes go through the source prefix).
- `/v2/app-config-policies/...` — policy CRUD + reads.

Mounted via `RouteRegistry.create("app-config-sources", ...)`,
`RouteRegistry.create("app-configs", ...)`, and
`RouteRegistry.create("app-config-policies", ...)` respectively,
matching the project-wide v2 conventions in
`src/ai/backend/manager/api/rest/v2/CLAUDE.md`.

### App Config Source endpoints

REST mirrors the GQL admin / my split — the scope-parameterized
path handles **admin writes + per-scope reads** (maps to GQL
`adminBulk*AppConfigSources` mutations and the scoped queries), and
the `/my` path is **self-only** (maps to GQL
`bulk*MyAppConfigSources` mutations).

#### Scope-parameterized path — admin writes / per-scope reads

```
/v2/app-config-sources/{scope_type}/{scope_id}[/{name}]
```

- `{scope_type}` ∈ `public | domain | domain_user_defaults | user`
  (matches `AppConfigScopeType` in §1).
- `{scope_id}` follows the §1 Scope ID convention — the literal
  `"public"` for `public`, `domain_name` for `domain` /
  `domain_user_defaults`, `user_id` (UUID) for `user`.
- `{name}` is the document name.

Reads (`GET`) go through the scope-parameterized path — writes are
handled exclusively via the bulk endpoints (see "Admin bulk" / "My
bulk" below).

| Method | Path                                                    | Description                |
|--------|---------------------------------------------------------|----------------------------|
| GET    | `/v2/app-config-sources/{scope_type}/{scope_id}`        | List source rows in a scope |
| GET    | `/v2/app-config-sources/{scope_type}/{scope_id}/{name}` | Read one source row         |

Read permissions per-scope match the GQL permission matrix:
- `/v2/app-config-sources/public/public[/{name}]` — anonymous allowed.
- `/v2/app-config-sources/domain/{domain_name}[/{name}]` — admin or the
  caller whose `current_user.domain_name == {domain_name}`.
- `/v2/app-config-sources/domain_user_defaults/{domain_name}[/{name}]` —
  same.
- `/v2/app-config-sources/user/{user_id}[/{name}]` — admin or the caller
  whose `current_user.user_id == {user_id}`.

### Resolved view endpoint — `/v2/app-configs/my`

The merged per-user `AppConfig` lives at a **separate prefix** to
make the "this is a resolved view, not a raw row" framing explicit
in the URL. The adapter resolves `current_user()` internally and
pins `scope=USER` + `scope_id = current_user.user_id` when reading.
There is no input field capable of targeting another user, and
there are no writes on this prefix — writing goes through
`/v2/app-config-sources/my/bulk-*`.

| Method | Path                                | Description                             |
|--------|-------------------------------------|-----------------------------------------|
| GET    | `/v2/app-configs/my[/{name}]`       | List / read own documents (merged view) |

Response body is the **resolved AppConfig** (snake_case
projection of the GQL `AppConfig`):

```json
{
  "name": "preferences",
  "sources": [
    { "scope_type": "domain_user_defaults",
      "scope_id": "default", "name": "preferences",
      "config": { ... }, "created_at": "...", "updated_at": "..." },
    { "scope_type": "user",
      "scope_id": "<user_uuid>", "name": "preferences",
      "config": { ... }, "created_at": "...", "updated_at": "..." }
  ],
  "merged_config": { ... }
}
```

The `sources` list is ordered low → high priority (same order as the
matching policy's `scope_sources`, or `[DOMAIN_USER_DEFAULTS, USER]`
when no policy exists). Elements appear only for scopes whose row
exists for this `(user, name)`. Each source's `config` and the
top-level `merged_config` are `null` when the corresponding value
is empty — the REST projection mirrors the GraphQL nullability
(§3) so clients never see a bare `{}`.

#### Admin writes (bulk-only)

| Method | Path                                       | Access | Maps to                             |
|--------|--------------------------------------------|--------|-------------------------------------|
| POST   | `/v2/app-config-sources/bulk-create`       | Admin  | `adminBulkCreateAppConfigSources`   |
| POST   | `/v2/app-config-sources/bulk-update`       | Admin  | `adminBulkUpdateAppConfigSources`   |
| POST   | `/v2/app-config-sources/bulk-purge`        | Admin  | `adminBulkPurgeAppConfigSources`    |

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
  "created": [ /* AppConfigSource objects */ ],
  "failed": [
    { "scope_type": "USER", "scope_id": "...",
      "name": "...", "message": "..." }
  ]
}
```

#### My writes (bulk-only)

| Method | Path                                          | Access | Maps to                          |
|--------|-----------------------------------------------|--------|----------------------------------|
| POST   | `/v2/app-config-sources/my/bulk-create`       | User   | `bulkCreateMyAppConfigSources`   |
| POST   | `/v2/app-config-sources/my/bulk-update`       | User   | `bulkUpdateMyAppConfigSources`   |

Response bodies are the snake_case projection of the corresponding
GQL `Bulk*MyAppConfigSourcesPayload` (a success list plus `failed`).

#### Admin cross-scope search

| Method | Path                        | Access | Description                                                |
|--------|-----------------------------|--------|------------------------------------------------------------|
| POST   | `/v2/app-config-sources/search`    | Admin  | Cross-scope search — same body schema as `adminAppConfigSources` |

### App Config Policy endpoints

Mounted at a sibling prefix (`/v2/app-config-policies/...`). Reads
are available to any authenticated user; writes are admin-only.

| Method | Path                                         | Access | Maps to                               |
|--------|----------------------------------------------|--------|---------------------------------------|
| GET    | `/v2/app-config-policies`                    | User   | `appConfigPolicies` (Connection)      |
| GET    | `/v2/app-config-policies/{config_name}`      | User   | `appConfigPolicy(configName)`         |
| POST   | `/v2/app-config-policies/bulk-create`        | Admin  | `adminBulkCreateAppConfigPolicies`    |
| POST   | `/v2/app-config-policies/bulk-update`        | Admin  | `adminBulkUpdateAppConfigPolicies`    |
| POST   | `/v2/app-config-policies/bulk-purge`         | Admin  | `adminBulkPurgeAppConfigPolicies`     |

Request / response bodies are the snake_case projection of the
corresponding GQL input / payload — `items[]` for writes, a
`{ data: [...], page_info: {...}, count: N }` envelope for list
reads, and a single policy object for the `{config_name}` GET.

---

## 5. `AppConfig` — Merge policy

> The merge semantics here apply **only to `AppConfig`**. The
> raw `AppConfigSource` type (returned from `publicAppConfigSources`,
> `adminAppConfigSources`, `DomainV2.appConfigSources`, `UserV2.appConfigSources`)
> exposes `extra_config` as a single `config` field — no merge.

### Storage

Each scope holds its **own** row for a given `name`; rows are never
copied between scopes. Editing an admin-provided default never
requires rewriting every user row — the merge materializes the final
value at read time.

- `(scope_type=USER, scope_id=user_id, name=N)` stores the values
  the user has explicitly set for document `N`.
- `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name, name=N)`
  stores the per-domain default value admins publish for document
  `N`.
- Other scopes (`PUBLIC`, `DOMAIN`, or any future scope) hold one
  row each for `N` when admissible.

Different `name`s are independent — the merge for `preferences` is
unaffected by whatever rows exist for `theme`.

### Chain order (policy-driven)

The merge chain for a given `(user_id, name)` is determined at read
time by the matching `AppConfigPolicy.scope_sources` (§1):

1. Service looks up the policy by `name` —
   `AppConfigPolicyRepository.get(name)`. The required-policy
   invariant (§1) guarantees a hit for every `name` that has
   AppConfigSource rows.
2. The chain is exactly the policy's `scope_sources` in order
   (low → high priority; later elements win on deep merge). Each
   scope contributes its natural `scope_id` — `PUBLIC` uses the
   literal `"public"`, `DOMAIN` / `DOMAIN_USER_DEFAULTS` use the
   caller's `domain_name`, and `USER` uses the caller's `user_id`.

A policy may therefore define chains of any length — a single-scope
policy (`scope_sources=["domain"]` for admin-owned documents like
`theme`), a 2-chain (`[domain, user]` for values the user can layer
on top of an admin baseline), or wider chains that pull in additional
scopes when the use case calls for it.

### Read (Merge)

Merge is owned by `AppConfigSourceRepository`; DB access is performed
by `AppConfigSourceDBSource`'s merge-specific method — a single SQL that
pulls every row the chain needs in one snapshot. The method receives
the chain as a parameter (a list of `(scope_type, scope_id_expr)`
pairs) derived from the policy:

1. The service resolves the chain for `name` via the policy lookup.
2. `AppConfigSourceDBSource.get_user_app_config(user_id, name, chain)`
   — single SQL resolves `domain_name` via a `users` subquery once
   and pulls one row per scope in the chain where it exists.
3. The resulting rows are ordered per the chain (absent rows contribute
   `{}` to the deep merge) and deep-merged: nested objects recursively,
   leaf values replaced by the higher-priority scope, lists treated as
   leaves and replaced wholesale.
4. The ordered rows become `AppConfig.sources`; the deep-merge
   result becomes `AppConfig.mergedConfig`.

The Connection query (`myAppConfigs`) is backed by the search-specific
method on `AppConfigSourceDBSource` — the same single-SQL approach,
generalized to return one resolved entry per `name` for which at
least one row in the user-readable set exists. The chain per `name`
is resolved **inside SQL** by joining `app_config_sources` with
`app_config_policies` on `name = config_name`: the scope filter
becomes `scope_type = ANY(policy.scope_sources)` and the merge
order is `array_position(policy.scope_sources, scope_type)`.
Policies may differ across `name`s, but the join evaluates each
`name`'s chain independently without the service having to precompute
a per-name chain map.

`AppConfigData` is the service-layer return dataclass for a
single resolved document; `AppConfigSearchResult` is its
search counterpart with the standard `items` / `total_count` /
`has_next_page` / `has_previous_page` shape (same as every other
repository's `*SearchResult`, §2). Search inputs reuse the shared
**BatchQuerier** — conditions on `name`, orders, and pagination —
plus a `UserAppConfigSearchScope(SearchScope)` pinning
`user_id` (its `to_condition()` scopes the underlying SELECT to
rows readable for that user: PUBLIC, user's DOMAIN /
DOMAIN_USER_DEFAULTS, and USER rows). No Python callable is
threaded through — chain derivation lives entirely in SQL.

```python
class AppConfigSourceDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_user_app_config(
        self,
        user_id: str,
        name: str,
        chain: list[AppConfigScopeType],
    ) -> AppConfigData:
        # `chain` is the ordered list of scopes — derived by the
        # service from the matching policy's `scope_sources`
        # (required-policy invariant, §1).
        # A single SQL resolves the caller's domain_name via a `users`
        # subquery and pulls one row per scope in `chain` where it
        # exists. Bounded to `len(chain)` rows by the natural-key
        # UniqueConstraint.
        user_domain_sq = (
            sa.select(UserRow.domain_name)
            .where(UserRow.id == sa.cast(user_id, sa.UUID))
            .scalar_subquery()
        )
        scope_id_for = {
            AppConfigScopeType.PUBLIC: sa.literal("public"),
            AppConfigScopeType.DOMAIN: user_domain_sq,
            AppConfigScopeType.DOMAIN_USER_DEFAULTS: user_domain_sq,
            AppConfigScopeType.USER: sa.literal(user_id),
        }
        scope_predicates = [
            sa.and_(
                AppConfigSourceRow.scope_type == scope_type,
                AppConfigSourceRow.scope_id == scope_id_for[scope_type],
            )
            for scope_type in chain
        ]
        async with self._db.begin_readonly_session() as db_sess:
            rows = (await db_sess.execute(
                sa.select(AppConfigSourceRow).where(
                    AppConfigSourceRow.name == name,
                    sa.or_(*scope_predicates),
                )
            )).scalars().all()

        by_scope = {row.scope_type: row for row in rows}
        ordered_sources = [
            by_scope[scope_type] for scope_type in chain if scope_type in by_scope
        ]
        merged: dict = {}
        for row in ordered_sources:
            merged = deep_merge(merged, row.extra_config)

        return AppConfigData(
            user_id=user_id,
            name=name,
            sources=ordered_sources,                # AppConfig.sources
            # Normalize empty merge to None — `AppConfig.mergedConfig`
            # and `AppConfigSource.config` both surface empty as `null`
            # (§3 types) so clients never have to distinguish `{}` from
            # "no value configured".
            merged_config=merged or None,           # AppConfig.mergedConfig
        )

    async def search_user_app_configs(
        self,
        scope: UserAppConfigSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        # Connection-shaped counterpart — `scope.user_id` pins the
        # reader; `querier` applies conditions / orders / pagination
        # over `name`. The chain per `name` is derived **in SQL** by
        # joining with `app_config_policies`:
        #
        #   SELECT s.*, p.scope_sources
        #   FROM app_config_sources AS s
        #   JOIN app_config_policies AS p ON s.name = p.config_name
        #   WHERE <scope.to_condition()>   -- user-readable rows
        #     AND s.scope_type::text = ANY(p.scope_sources)
        #   ORDER BY s.name,
        #     array_position(p.scope_sources, s.scope_type::text)
        #
        # Rows come back grouped by `name`, each group already sorted
        # low→high priority. `execute_batch_querier` paginates at the
        # distinct-`name` level (using `name` as the stable cursor
        # key). For each group the deep-merge runs in Python; each
        # group becomes one `AppConfigData`. No service-side callable
        # is needed — the required-policy invariant (§1) guarantees
        # the join always resolves.
        ...


class AppConfigSourceRepository:
    """
    Scope-parameterized CRUD for `app_config_sources` rows (served
    to GQL as raw `AppConfigSource`) plus merge-specific reads that
    back the resolved view (`AppConfig`, §5). Single repository for
    every scope — items are addressed by `AppConfigSourceKey`.

    Merge path delegates to `AppConfigSourceDBSource`'s merge-specific
    method, which reads all rows on the policy-defined chain in a
    single SQL. No separate `AppConfigRepository` — both roles live
    here.
    """

    _db_source: AppConfigSourceDBSource

    def __init__(self, db_source: AppConfigSourceDBSource) -> None:
        self._db_source = db_source

    # ── Raw source CRUD (AppConfigSource) ──────────────────────────

    async def get(self, key: AppConfigSourceKey) -> AppConfigSourceRow | None:
        return await self._db_source.get(key)

    async def get_by_id(self, id: uuid.UUID) -> AppConfigSourceRow | None:
        return await self._db_source.get_by_id(id)

    async def create(
        self, key: AppConfigSourceKey, extra_config: Mapping[str, Any]
    ) -> AppConfigSourceRow:
        return await self._db_source.create(key, extra_config)

    async def update(
        self, key: AppConfigSourceKey, extra_config: Mapping[str, Any]
    ) -> AppConfigSourceRow:
        return await self._db_source.update(key, extra_config)

    async def purge(self, key: AppConfigSourceKey) -> AppConfigSourceRow | None:
        return await self._db_source.purge(key)

    async def search(
        self,
        scope: AppConfigSourceSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSourceSearchResult:
        # Scope-bound search. Cross-scope (admin) uses `admin_search`.
        return await self._db_source.search(scope=scope, querier=querier)

    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigSourceSearchResult:
        return await self._db_source.admin_search(querier)

    # ── Resolved view (AppConfig) ──────────────────────────
    # `AppConfigSourceDBSource`'s merge-specific method performs the
    # users-subquery resolution inside a single SQL, so the
    # repository here is a thin delegate.

    async def get_app_config(
        self,
        user_id: str,
        name: str,
        chain: list[AppConfigScopeType],
    ) -> AppConfigData:
        return await self._db_source.get_user_app_config(
            user_id, name, chain
        )

    async def search_app_configs(
        self,
        scope: UserAppConfigSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        return await self._db_source.search_user_app_configs(
            scope, querier,
        )
```

### Exposure

`AppConfig` exposes the raw source rows that contributed to
the resolution plus the deep-merge result:

- `sources` — the ordered list of `AppConfigSource` source rows (low → high
  priority, matching the chain). Absent scopes simply do not appear.
  The list is empty only when no scope in the chain has a row, in
  which case the `name` would not appear in `myAppConfigs` at all.
  Each source's `config` is `null` when the stored value is empty
  (a row cleared via `*Update*` with `{}`); callers treat `null` as
  "this scope contributes nothing".
- `mergedConfig` — the deep-merge of `sources` in order; the value
  the UI actually applies. `null` when every contributing row is
  empty and the merge result collapses to `{}` — clients fall back
  to their built-in defaults in that case.

Clients that need to distinguish "admin-provided per-user default"
from "what the user changed" do so by inspecting each source row's
`scopeType` (e.g. a row with `scopeType = DOMAIN_USER_DEFAULTS` is
the admin-provided default; a row with `scopeType = USER` is the
user's customization). This replaces the previous fixed
`domainDefaultConfig` / `userCustomizedConfig` fields.

The REST `GET /v2/app-configs/my/{name}` response carries the same
shape (snake_case `sources` + `merged_config`) — see §4.

---

## 6. Client Integration — WebUI bootstrap

The WebUI requests configs by addressing them explicitly with
`(scope, scopeId, name)`. The list of public documents the WebUI
must load before login is owned entirely by the frontend
(hard-coded or shipped in the WebUI bundle) — the server does not
publish a bootstrap list.

### Bootstrap flow

1. **Pre-login (anonymous)** — for each document the WebUI wants
   before login, it issues a `publicAppConfigSources` query with a `name`
   filter (no auth). The `theme` / `branding` shapes are pulled via
   a single document fetch each — see S1 in §7. On no-edge /
   network error the WebUI falls back to its built-in defaults for
   that document.

2. **Post-login** — the WebUI issues a single `myAppConfigs` query
   to fetch *all* of the caller's resolved documents in one round
   trip. Each entry carries `sources` (raw `AppConfigSource` rows per scope
   in merge order) and the deep-merged `mergedConfig` (§5). Admins
   use the same query for their own session (admins are also users
   for the purpose of personal settings). `DOMAIN` scope does not
   participate in the default merge chain, so an admin UI that needs
   to manage domain policy issues a separate `DomainV2.appConfigSources` /
   `adminAppConfigSources` query. See S2 in §7.

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
  publicAppConfigSources(filter: { name: { equals: "theme" } }) {
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
        sources { scopeType scopeId name config updatedAt }
        mergedConfig
      }
    }
  }
  publicAppConfigSources {
    edges { node { name config } }
  }
}
```

- Server: `myAppConfigs` returns one entry per `name` for which at
  least one source row in the merge chain exists. Every such `name`
  is backed by a policy (§1 required-policy invariant), so the chain
  always comes from `AppConfigPolicy.scope_sources` — there is no
  implicit fallback chain. `sources` carries the raw rows in chain
  order; `mergedConfig` is their deep merge. See §5.
- The WebUI initializes UI state from `mergedConfig` per document
  and keeps the `sources` list around so the Settings page can
  distinguish user-changed (`scopeType = USER`) from admin-provided
  defaults (`scopeType = DOMAIN_USER_DEFAULTS`, etc.).

### S3. The user saves their own document

The user replaces their `preferences` document — e.g. language,
experimental-feature toggles, visible-column choices per table. They
call the self-service `bulkUpdateMyAppConfigSources` — each item carries
only `name` + `config`, with `scopeType` / `scopeId` injected server-side
as `USER` + `current_user.user_id`. Even a single-item write goes
through the bulk path (1-element `items` array); the recomputed
`AppConfig` comes back as `updated[0]`, so no separate
`myAppConfigs` re-query is needed.

```graphql
mutation SaveMyConfig($input: BulkUpdateMyAppConfigSourceInput!) {
  bulkUpdateMyAppConfigSources(input: $input) {
    updated {
      name
      sources { scopeType scopeId name config updatedAt }
      mergedConfig
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
  `adminBulkUpdateAppConfigSources`).
- The input `config` replaces the USER row's stored JSON wholesale.
  `AppConfig.mergedConfig` is read-only computed and cannot
  be written.
- **Replace** semantics: anything the caller wants to keep must be
  sent in the same payload — there is no partial-merge or per-key
  patch.
- **Policy**: if an `AppConfigPolicy` exists for `name` and either
  `USER ∉ scope_sources` or `user_writable = False`, the item is
  appended to `failed` with a policy-violation message. Clients can
  discover this ahead of time by reading the policy via
  `appConfigPolicy(configName:)`.
- **First write vs. subsequent writes**: `bulkUpdateMyAppConfigSources`
  places items with no USER row into `failed`. For the very first
  save of a given `name`, the client calls `bulkCreateMyAppConfigSources`
  with the same shape. Clients can disambiguate by checking whether
  the `myAppConfigs` entry for that `name` already has a `USER` row
  in its `sources` list.

### S3.5. Admin publishes an app-config policy

Before the `theme` document can be published (S4 below), an admin
establishes a policy for `theme` that restricts writes to an
admin-only scope and forbids per-user customization. The policy is
**required** (§1 required-policy invariant) — no AppConfigSource row for
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
  - `bulk*MyAppConfigSources` calls targeting `theme` are rejected because
    `user_writable = false`.
  - `myAppConfigs` entries for `theme` are resolved through the
    chain `[DOMAIN]` (single-scope — `sources` has at most one
    element, and `mergedConfig` equals that element's `config`
    or is `null` when the element's `config` is `null`, §3).
- Subsequent edits use `adminBulkUpdateAppConfigPolicies` with the
  same `configName`.

### S3.6. Varied policy shapes

Same mechanics as S3.5 with different `scopeSources` / `userWritable`
combinations. Each shape backs a different product decision:

- **`[user]`, `userWritable=true`** — purely user-local document.
  Admin seeding and domain defaults play no role; the resolved view
  is either the user's own row or nothing. Fits "this tab's column
  order", "editor keybindings", or other state the user alone
  authors.
- **`[domain]`, `userWritable=false`** — strict admin-owned document
  with no per-user override. Fits the default `theme` setup used in
  S3.5 / S4.
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
from the next `bulkUpdateMyAppConfigSources` onward users can layer their
own customization on top (§7 S3.7).

### S3.7. Promoting a document from admin-only to user-customizable

A site operator initially published `theme` under the strict policy
from S3.5 (`scopeSources=["domain"]`, `userWritable=false`). After
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
  - Users can now call `bulkCreate/UpdateMyAppConfigSources` targeting
    `theme` and write their own `USER` row.
  - The next `myAppConfigs` call returns `theme` entries whose
    `sources` is `[<DOMAIN row>, <USER row if present>]` and whose
    `mergedConfig` is `domain ⊕ user`.
- Reversibility: flipping the policy back to
  `scopeSources=["domain"]` + `userWritable=false` blocks new user
  writes and excludes `USER` rows from the resolved view, but leaves
  any pre-existing `USER` rows untouched at the DB level (they
  simply stop being read). Admins who want those rows gone target
  them with `adminBulkPurgeAppConfigSources` (see S3.8).

### S3.8. Admin fixes a misconfigured policy or config

Since `configName` is immutable (§1), a typo at policy-creation time
cannot be fixed by renaming. The admin's recovery path is a **purge
and rebuild** workflow. The mutations run in a specific order because
of the required-policy invariant:

1. If any AppConfigSource rows already exist under the wrong `config_name`,
   purge them first — the policy cannot be purged while references
   exist.
2. Purge the wrong policy.
3. Create the correct policy.
4. Re-create any AppConfigSource rows under the correct `config_name`.

```graphql
# Step 1 — purge the bad AppConfigSource rows (keys identify them).
mutation PurgeBadConfigs($input: AdminBulkPurgeAppConfigSourceInput!) {
  adminBulkPurgeAppConfigSources(input: $input) {
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
  the service checks for remaining AppConfigSource references under that
  `config_name` before purging.
- Purge is the only deletion verb in the BEP; day-to-day writes
  still flow through create / update and never remove rows on their
  own. Users cannot call purge.

### S4. Admin publishes a per-user default for a domain

The domain admin publishes the `preferences` document's per-user
default — every user in the domain inherits it at merge time as the
base for their own `USER` row. The policy for `preferences` (S3.6's
"`[domain_user_defaults, user]` + `userWritable=true`" shape) admits
both admin-written `DOMAIN_USER_DEFAULTS` entries and user overrides;
this scenario exercises the admin side. The first publish uses
`adminBulkCreateAppConfigSources` with `key.scopeType =
DOMAIN_USER_DEFAULTS`; later edits use
`adminBulkUpdateAppConfigSources` with the identical input shape.
Multiple domains can be seeded in one call by passing multiple items.

```graphql
mutation AdminCreateAppConfigSources($input: AdminBulkCreateAppConfigSourceInput!) {
  adminBulkCreateAppConfigSources(input: $input) {
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
  `AppConfigSourceRepository.create` (§2). Items whose key already
  has a row land in `failed` — the admin falls back to
  `adminBulkUpdateAppConfigSources`.
- Policy: the write's `scope_type` must be in the policy's
  `scope_sources`. The `preferences`-style policy lists
  `DOMAIN_USER_DEFAULTS`, so this write passes. A stricter policy
  that omits the scope (e.g. the `theme` policy from S3.5, which
  lists only `["domain"]`) would reject the same write with a
  policy-violation message — in that case the admin would target
  `DOMAIN` instead.
- Effect: every user in the domain picks up the new defaults on the
  next `myAppConfigs` read (merged per §5).

### S5. Admin seeds a specific user's document on their behalf

For a support request, an admin seeds user A's `preferences` USER row
for the first time. Since the target is another user's row, this
must use the admin path — `adminBulkCreateAppConfigSources` with
`key.scopeType = USER` and `key.scopeId = user A's user_id`, not the
self-service bulk path.
Items whose key already has a row land in `failed`, in which case
the admin falls back to `adminBulkUpdateAppConfigSources`.

```graphql
mutation AdminCreateAppConfigsForUser($input: AdminBulkCreateAppConfigSourceInput!) {
  adminBulkCreateAppConfigSources(input: $input) {
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
- `adminBulkCreateAppConfigSources` fails the item if a row already exists
  for the key; use `adminBulkUpdateAppConfigSources` instead to overwrite.
- Policy: if an `AppConfigPolicy` for `preferences` has `USER ∉
  scope_sources`, the admin path still rejects the item
  (`scope_sources` applies to both paths — admins just bypass
  `user_writable`, not the scope list). With the usual
  `preferences`-style policy (`scope_sources` includes `USER`) this
  write passes.
- The response is a list of raw `AppConfigSource`; the target user's
  resolved view reflects the new USER row (merged with the matching
  domain defaults) on the next `myAppConfigs` read from that user's
  session.

### S6. Admin audits all AppConfigSources (cross-scope search)

Cases such as "list every domain that touched `theme` in the last
week" or "every domain that customized the `menu` document":

```graphql
query AuditConfigs(
  $filter: AppConfigSourceFilter!
  $orderBy: [AppConfigSourceOrderBy!]
  $first: Int
  $after: String
) {
  adminAppConfigSources(filter: $filter, orderBy: $orderBy, first: $first, after: $after) {
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
- **Invariant: `user_writable = True` requires `USER ∈
  scope_sources`** — not enforced today; the two fields are kept
  independent. A future BEP may add the invariant if the combination
  is shown to confuse operators.
