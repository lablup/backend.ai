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
> tooling: use `domain` for values semantically owned by the domain,
> `domain_user_defaults` for values positioned as per-user seed
> defaults. Both can participate in any resolved chain when the
> policy says so.

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
  verbs (`create` / `update` / `purge`) — `adminBulkCreateAppConfigs`
  and siblings cover every scope, admin-only, return raw `AppConfig`
  lists. The self-service (my) path exposes two verbs
  (`create` / `update`) — `bulkCreateMyAppConfigs` and siblings, with
  `USER` + `current_user` implicit and merged `ResolvedAppConfig` in
  the response. `create` strictly inserts (per-item failure if any
  row exists for the key); `update` replaces the existing row's
  stored JSON wholesale; `purge` is an **admin-only cleanup verb**
  (§3) for removing misconfigured rows — users cannot purge. No
  partial update / deep-merge / key-level removal / upsert at the
  write boundary. Each item runs in its own transaction so one
  failure does not abort the rest. Identification uses the
  `(scope, scopeId, name)` natural key, never Relay `id` — my-path
  mutations have scope/scopeId injected by the server.
- **Single source-of-truth table**: a single `app_configs` table holds
  every scope; only the exposure layer is split.
- **Relay style**: Input/Payload conventions and the Node interface.

---

## 1. DB Layer — `app_configs` table

### Schema changes

Add a `name` column to `app_configs`. The natural-key uniqueness
constraint becomes `(scope_type, scope_id, name)`.

```python
class AppConfigScopeType(enum.StrEnum):
    PUBLIC = "public"
    DOMAIN = "domain"
    DOMAIN_USER_DEFAULTS = "domain_user_defaults"   # per-domain defaults applied to users in that domain
    USER = "user"


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

### `name` length constraint

`name` is bounded to `1 ≤ len ≤ 255` (non-empty, reasonable cap to
protect DB index / prevent oversized payloads). No character-set
restriction; any string within the length bound is legal.

Callers are expected to escape `name` when embedding it in transport
layers:
- **REST path segment**: standard URL encoding (`%20`, `%3A`, etc.).
- **`ResolvedAppConfig.id`**: the implementation encodes the
  `(user_id, name)` pair unambiguously (e.g., left-splitting on the
  fixed-length UUID part, or JSON-packing before base64) so `name`
  can contain any character.

Enforced by pydantic validation at the API layer.

### Write semantics

`*Create*` errors if a row already exists for the natural key;
`*Update*` errors if no row exists. The only exposed deletion verb is
`*Purge*` (admin-only) — used for cleanup of misconfigured rows; see
§3. Outside of purge, rows persist once created, and callers "clear"
a document by `*Update*`-ing it to an empty JSON (`{}`).

**A matching `app_config_policies` row is required for any write**
(see "App Config Policy table" below). The service layer enforces:

- If no policy row exists for `name`, the item is rejected with a
  policy-not-found message — `AppConfigRepository.{create,update}`
  is not called.
- `scope_type` must be in the policy's `scope_sources`; writes to
  other scopes are rejected as a per-item failure.
- When the write is on the `USER` scope via a `bulk*MyAppConfigs`
  mutation, the policy's `user_writable` must be `True`; otherwise
  the item is rejected. The admin-path mutations are not gated by
  `user_writable` — admins may seed USER rows regardless of the
  flag.

Because every AppConfig row is created under a matching policy, the
resolved merge (§5) always has a chain to follow — there is no
"policy-less fallback" path.

### App Config Policy table

A separate `app_config_policies` table holds the rules per document
— which app-config rows get merged as sources into the resolved
view, and which scopes may be written. Configs and policies are
joined by `config_name` value only at runtime; there is no foreign
key at the DB level. Instead, the **service layer enforces a
required-policy invariant**: an `AppConfigRow` can only be created
while a matching policy row exists (see "Write semantics" above).

```python
class AppConfigPolicyRow(Base):
    __tablename__ = "app_config_policies"

    id: Mapped[uuid.UUID]
    config_name: Mapped[str]                  # UNIQUE — joined to
                                              # `app_configs.name` by value only
                                              # (no FK).
                                              # IMMUTABLE — rename is rejected
                                              # at the service layer. To "fix"
                                              # a wrongly-named policy, admins
                                              # purge the policy (and any
                                              # AppConfig rows that used it)
                                              # and create a new policy.
    scope_sources: Mapped[list[str]]          # Dual meaning:
                                              #   (1) which `app_configs` rows
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
                                              # `bulk*MyAppConfigs` path. Admin-
                                              # path writes are not gated by
                                              # this flag.
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    __table_args__ = (
        sa.UniqueConstraint("config_name", name="uq_app_config_policies_config_name"),
    )
```

**Integrity without FK**:

- **Create**: rejected at the service layer unless a policy exists
  for `config_name`. This is the primary guarantee that every
  AppConfig row has a matching policy.
- **Policy rename**: not allowed. `config_name` is immutable —
  updates may change `scope_sources` / `user_writable` only. The
  immutability removes the "rename orphans configs" failure mode.
- **Policy deletion**: there is no `update`-level policy deletion.
  The only removal path is `adminBulkPurgeAppConfigPolicies` (§3),
  and the service rejects the purge unless no AppConfig row
  references the policy's `config_name`. If such rows exist, the
  admin purges them first via `adminBulkPurgeAppConfigs`, then the
  policy.
- **AppConfig deletion**: `adminBulkPurgeAppConfigs` is an
  admin-only cleanup verb for misconfigured rows. It is **not** a
  general "delete" — the BEP's user-facing contract is still that
  rows persist once written; purge is the escape hatch for fixing
  mistakes.

This is the only coupling between the two tables — enforced outside
the schema so future changes to one table's DB shape don't cascade
through FK machinery.

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
├── user_app_config_repository.py     # USER row CRUD + merged view (ResolvedAppConfig)
└── repositories.py                   # exports all four repos

repositories/app_config_policy/
├── db_source/
│   └── db_source.py                  # separate db_source (different table)
├── app_config_policy_repository.py
└── repositories.py
```

### Repository responsibility split

| Repository                              | Methods                                                                                                              |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| `PublicAppConfigRepository`             | `get(name)`, `get_by_id(id)`, `create(name, extra_config)`, `update(name, extra_config)`, `purge(name)`, `search(filter, pagination)`                                             |
| `DomainAppConfigRepository`             | `get(domain_name, name)`, `get_by_id(id)`, `create(domain_name, name, extra_config)`, `update(domain_name, name, extra_config)`, `purge(domain_name, name)`, `search(domain_name, filter, pagination)` |
| `DomainUserDefaultsAppConfigRepository` | `get(domain_name, name)`, `get_by_id(id)`, `create(domain_name, name, extra_config)`, `update(domain_name, name, extra_config)`, `purge(domain_name, name)`, `search(domain_name, filter, pagination)` |
| `UserAppConfigRepository`               | CRUD: `get / get_by_id / create / update / purge / search` (all take `user_id` + `name`; `search` additionally takes `filter` + `pagination`). Plus merge-specific: `get_merged(user_id, name)`, `search_merged(user_id, filter, pagination)` — see the note below for roles. |
| `AppConfigPolicyRepository`             | `get(config_name)`, `get_by_id(id)`, `create(config_name, scope_sources, user_writable)`, `update(config_name, scope_sources, user_writable)`, `purge(config_name)`, `search(filter, pagination)`. Updates do not touch `config_name` (immutable — §1). The `purge` call rejects at the service layer if any AppConfig row still references the `config_name`. |

`DomainUserDefaultsAppConfigRepository` mirrors
`DomainAppConfigRepository` (admin write + same-domain user read,
same call shape) but operates on
`(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name)` rows.
Splitting it from `DomainAppConfigRepository` keeps each repository
mapped to exactly one scope, matching the rest of the layout.

`UserAppConfigRepository` plays a **dual role** — raw `USER` row CRUD
(serving `UserAppConfig`) + read-side merged view (serving
`ResolvedAppConfig`, see §5). It takes a single `AppConfigDBSource` like
the other scope repositories; the user → domain_name resolution
needed by the merge is done inside the merge-specific DB method via a
`users` subquery in a single SQL, so no separate `UserDBSource` is
injected at the repository level. The GraphQL schema exposes
`UserAppConfig` (raw) and `ResolvedAppConfig` (merged) as separate types,
but internally they share one repository — there is no
`ResolvedAppConfigRepository`.


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
            ...

    async def get_by_id(self, id: uuid.UUID) -> AppConfigRow | None:
        # ID-based lookup for Actions that have already resolved the
        # natural key to a row id (see §3 "Name → ID resolution").
        async with self._db.begin_readonly_session() as db_sess:
            ...

    async def create(
        self,
        key: AppConfigKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigRow:
        # Strict insert. Errors if any row already exists for the
        # natural key.
        async with self._db.begin_session() as db_sess:
            ...

    async def update(
        self,
        key: AppConfigKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigRow:
        # Replace the existing row's value with `extra_config`.
        # Errors if no row exists for the natural key.
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
            ...
```

Listing is expressed via the `search` primitive — each scope
repository's `search(...)` is a thin-delegate that binds
`scope_type` / `scope_id`. Permission checks and scope validation
are performed in the service layer.

**Bulk mutation orchestration**: all AppConfig bulk mutations
(`adminBulk{Create,Update,Purge}AppConfigs`,
`bulk{Create,Update}MyAppConfigs`) follow the same service-layer
orchestration — each item runs in its own DB transaction so a
single failure doesn't abort the rest (partial success), successes
and failures collected into `BulkActionResult(success_list,
failed_list)`. Admin bulk dispatches each item on
`item.key.scopeType` to the matching scope repository; my bulk
dispatches directly to `UserAppConfigRepository`. Not optimized as
a single SQL batch: items split by scope can fail for heterogeneous
reasons (unique-key violations, authorization errors, …), and
representing partial success in one SQL statement is awkward.

The admin policy bulk mutations
(`adminBulk{Create,Update,Purge}AppConfigPolicies`) follow the same
per-item / partial-success pattern against `AppConfigPolicyRepository`.
`Update` rejects items that attempt to change `configName`
(immutable, §1). `Purge` rejects items whose `configName` still has
referencing `AppConfig` rows, preserving the required-policy
invariant for the rows that remain.

`AppConfigFilter` / `AppConfigPage` / `Pagination` are internal
containers at the repository / service layer — Python dataclasses
corresponding 1:1 to the GraphQL `AppConfigFilter` (§3) at the
adapter boundary. Same name on purpose: GraphQL input is the wire
format, the Python dataclass is the in-process DTO. Concrete
definitions are intentionally left to the implementation phase
(expected location: a small companion module under
`repositories/app_config/`).

### Policy repository

`AppConfigPolicyRepository` lives under
`repositories/app_config_policy/` with its own
`AppConfigPolicyDBSource`. It is intentionally kept separate from
`AppConfigDBSource` — the tables share no FK and no joined query
surface, so collapsing them would bind two independent lifecycles
together. The policy repository exposes the same six-operation shape
(`get` / `get_by_id` / `create` / `update` / `search`; `delete` /
`purge` omitted per the BEP-1052 write policy).

Write orchestration for `app_configs` consults the policy repository
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
- If the item is on the `bulk*MyAppConfigs` path, the policy is
  present, and `user_writable` is `False`, the item is likewise
  rejected without touching `AppConfigRepository`.

The policy repository's own `update` method refuses to change
`config_name` (immutable per §1). `AppConfigPolicyRepository.purge`
first runs a reference check via `AppConfigDBSource` — if any
`app_configs` row exists with matching `name`, the purge is rejected
so the required-policy invariant cannot be broken retroactively.

Reads do not consult the policy repository from within
`AppConfigRepository`. The merge service (§5) performs its own policy
lookup when assembling a `ResolvedAppConfig` because the chain order
depends on it; per-scope raw reads do not.

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

For the merged view, use `myAppConfigs` (returns `ResolvedAppConfig`) —
see §5.

Read: owner or admin. Writes go through the bulk paths —
`bulk*MyAppConfigs` (owner writing their own row) or
`adminBulk*AppConfigs` with `key.scopeType = USER` (admin writing
another user's row). There is no single-item write mutation.
"""
type UserAppConfig implements Node {
  id: ID!

  """Owning user (back-reference)."""
  user: UserV2!

  """Document name (unique within this user)."""
  name: String!

  """Raw stored value — the user's customized config for this `name`."""
  config: JSON!

  createdAt: DateTime!
  updatedAt: DateTime!
}

"""
Resolved app-config view from the current user's perspective —
accessible via `myAppConfigs` or `node(id)`. Deep-merges same-`name`
source rows in the order prescribed by the matching
`AppConfigPolicy.scope_sources`. Every `name` that appears here is
backed by a policy (§1 required-policy invariant), so the chain is
always defined by data. An entry appears whenever at least one
source row exists.

Although derived, `ResolvedAppConfig` implements `Node` — the
`(user_id, name)` composite is encoded as a server-side global ID
(`base64("ResolvedAppConfig:{user_id}:{name}")`). The `node(id)`
resolver decodes the id and returns the merged view only when
`decoded.user_id == current_user.id`. There is no admin override:
`ResolvedAppConfig` is strictly the *current user's* resolved view,
and admins do not get a path to see another user's resolved
configuration through this type.
"""
type ResolvedAppConfig implements Node {
  """
  Server-encoded global ID — `base64("ResolvedAppConfig:{user_id}:{name}")`.
  """
  id: ID!

  """Document name (unique within this user)."""
  name: String!

  """
  Raw source rows that contributed to `mergedConfig`, in merge order
  (low → high priority; later wins). The list matches the order of
  the matching policy's `scope_sources` — every `name` returned
  through `myAppConfigs` has a policy (§1). Each element is a raw
  `AppConfig` so callers can distinguish
  "admin-provided per-user default" from "what the user changed" by
  inspecting `scopeType`.
  """
  sources: [AppConfig!]!

  """
  Effective applied value: deep merge of `sources` in order (left =
  lowest priority, right = highest). Clients render the UI from this
  value.
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
below. In short: `DomainV2.appConfigs` is same-domain users or
admin; `UserV2.appConfigs` is owner or admin. Writes (mutations) on
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

A root field `myAppConfigs` (Connection) returns the current user's
**merged view** (`ResolvedAppConfig`) — different from the raw USER rows
exposed by `UserV2.appConfigs` (`UserAppConfig`). Merging only
happens on this path (§5).

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
  retrieve a single document. `filter.scopeType` / `filter.scopeId`
  are ignored here — the scope is pinned.
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
  ): ResolvedAppConfigConnection!

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
type ResolvedAppConfigConnection {
  edges: [ResolvedAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type ResolvedAppConfigEdge {
  cursor: String!
  node: ResolvedAppConfig!
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

input AppConfigOrderBy {
  field: AppConfigOrderField!
  direction: OrderDirection! = ASC
}

"""
`SCOPE_TYPE` / `SCOPE_ID` are only useful on `adminAppConfigs`; on
per-scope Connections they degenerate to a constant and have no
effect. `UPDATED_AT` / `CREATED_AT` apply to raw-row Connections
only — `myAppConfigs` returns `ResolvedAppConfig` (derived) which does
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

- `adminBulk{Create,Update,Purge}AppConfigs`: each item carries an
  `AppConfigKey { scopeType, scopeId, name }` — covers every scope.
  **Admin-only**. `Create` / `Update` return a list of raw
  `AppConfig`; `Purge` returns the purged key list. All three
  return per-item failures.
- `bulk{Create,Update}MyAppConfigs`: each item carries only `name`
  (scope is `USER` + `scopeId = current_user.user_id` injected
  server-side). Callable by any authenticated user for their own
  documents. Returns a list of recomputed `ResolvedAppConfig` + a
  list of per-item failures. **No `Purge` on the my-path** — users
  cannot delete rows; only admins do cleanup.
- `adminBulk{Create,Update,Purge}AppConfigPolicies`: each item
  carries `configName` (+ policy fields on create/update).
  **Admin-only**. `Update` rejects any attempt to change
  `configName` (immutable — §1). `Purge` rejects any item whose
  `configName` still has AppConfig rows referencing it.

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
  strict insert — if any row already exists for the natural key,
  that item fails. Items may target any scope; admin-side seeding
  of a `USER`-scope row is also done via this mutation.
  """
  adminBulkCreateAppConfigs(input: AdminBulkCreateAppConfigInput!): AdminBulkCreateAppConfigsPayload!

  """
  Bulk-update app config documents (admin-only). Each item replaces
  the existing row's stored JSON wholesale. If no row exists for
  the natural key, that item fails.
  """
  adminBulkUpdateAppConfigs(input: AdminBulkUpdateAppConfigInput!): AdminBulkUpdateAppConfigsPayload!

  """
  Bulk-purge app config documents (admin-only). Each item is
  identified by `AppConfigKey`; if no row exists for the key, the
  item is no-oped (returned in `purged` with the key alone). Purge
  is the only deletion verb for AppConfig — intended for cleaning up
  misconfigured rows; day-to-day writes should use create / update.
  """
  adminBulkPurgeAppConfigs(input: AdminBulkPurgeAppConfigInput!): AdminBulkPurgeAppConfigsPayload!

  # ── Self-service (my) path — USER + current_user implicit ────

  """
  Bulk-create the current user's `USER`-scope documents (auth
  required). Each item has `name` + `config`;
  `scopeId = current_user.user_id` is injected server-side. Strict
  insert — if a USER row already exists for a `name`, that item
  fails.
  """
  bulkCreateMyAppConfigs(input: BulkCreateMyAppConfigInput!): BulkCreateMyAppConfigsPayload!

  """
  Bulk-replace the current user's `USER`-scope documents (auth
  required). Items whose USER row is missing fail.
  """
  bulkUpdateMyAppConfigs(input: BulkUpdateMyAppConfigInput!): BulkUpdateMyAppConfigsPayload!

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
  `AppConfig` row still references its `configName` (the
  required-policy invariant must hold for the remaining rows);
  admins clean such rows up first via `adminBulkPurgeAppConfigs`.
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
  - `USER`: that user's customized value for this `name` (the
    `ResolvedAppConfig` merged view is read-only computed).
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

"""
Per-item input for `adminBulkPurgeAppConfigs`. Identified by key
alone — there is no `config` payload.
"""
input AdminBulkPurgeAppConfigInput {
  """Keys identifying the rows to purge."""
  keys: [AppConfigKey!]!
}

# ── My Inputs — scope=USER, scopeId=current_user.user_id implicit ──

"""Per-item input for my bulk create/update (name + config)."""
input MyAppConfigItemInput {
  """Document name (unique within the current user)."""
  name: String!

  """
  Value to store on the caller's `USER` row for this `name` —
  initial on create, wholesale replacement on update. Pass `{}` to
  clear. `ResolvedAppConfig.mergedConfig` is read-only computed and
  cannot be written.
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

# ── Admin Payloads — return lists of raw AppConfig ───────────

"""
Per-item error info for a failed item in an admin bulk write.
Shared by all admin AppConfig bulk mutations (create / update /
purge).
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

"""Result of `adminBulkPurgeAppConfigs`. Partial success."""
type AdminBulkPurgeAppConfigsPayload {
  """Keys of rows actually removed (or already absent → no-op)."""
  purged: [AppConfigKey!]!

  """Per-item errors for entries that failed to purge."""
  failed: [AdminAppConfigError!]!
}

# ── My Payloads — return lists of resolved ResolvedAppConfig ────

"""
Per-item error info for a failed item in a my bulk write. Shared by
the my bulk mutations (create / update). (scope / scopeId are
server-injected, so `name` is the only identifier.)
"""
type MyAppConfigError {
  """Name of the failed item."""
  name: String!

  """Error message describing the failure."""
  message: String!
}

"""Result of `bulkCreateMyAppConfigs`. Partial success."""
type BulkCreateMyAppConfigsPayload {
  """Recomputed `ResolvedAppConfig` list after the writes."""
  created: [ResolvedAppConfig!]!

  """Per-item errors for entries that failed to create."""
  failed: [MyAppConfigError!]!
}

"""Result of `bulkUpdateMyAppConfigs`. Partial success."""
type BulkUpdateMyAppConfigsPayload {
  """Recomputed `ResolvedAppConfig` list after the writes."""
  updated: [ResolvedAppConfig!]!

  """Per-item errors for entries that failed to update."""
  failed: [MyAppConfigError!]!
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

"""
Per-item error info for a failed item in an admin policy bulk write.
Shared by all admin policy bulk mutations (create / update / purge).
"""
type AdminAppConfigPolicyError {
  """`configName` of the failed item."""
  configName: String!

  """Error message describing the failure."""
  message: String!
}

"""Result of `adminBulkCreateAppConfigPolicies`. Partial success."""
type AdminBulkCreateAppConfigPoliciesPayload {
  """Successfully created policies."""
  created: [AppConfigPolicy!]!

  """Per-item errors for entries that failed to create."""
  failed: [AdminAppConfigPolicyError!]!
}

"""Result of `adminBulkUpdateAppConfigPolicies`. Partial success."""
type AdminBulkUpdateAppConfigPoliciesPayload {
  """Policies after replacement."""
  updated: [AppConfigPolicy!]!

  """Per-item errors for entries that failed to update."""
  failed: [AdminAppConfigPolicyError!]!
}

"""Result of `adminBulkPurgeAppConfigPolicies`. Partial success."""
type AdminBulkPurgeAppConfigPoliciesPayload {
  """`configName`s of policies actually removed."""
  purgedConfigNames: [String!]!

  """Per-item errors for entries that failed to purge."""
  failed: [AdminAppConfigPolicyError!]!
}

"""
Generic AppConfig type shared by the admin-path payloads,
`adminAppConfigs`, and `node(id)`. Exposes the raw stored value.
Thin by design — no back-references to the parent `DomainV2` /
`UserV2`; callers that need the parent object re-query
`domain_v2(name:)` / `admin_user_v2(user_id:)` explicitly.
"""
type AppConfig implements Node {
  """
  Relay global ID — `base64("AppConfig:<row_uuid>")`. The distinct
  prefix lets `node(id)` dispatch correctly between `AppConfig` and
  `ResolvedAppConfig`.
  """
  id: ID!

  scopeType: AppConfigScopeType!
  scopeId: String!
  name: String!

  """
  Raw stored value (`extra_config`). For USER scope this is the
  user-customized value, not the merged result.
  """
  config: JSON!

  createdAt: DateTime!
  updatedAt: DateTime!
}

# ── App Config Policy ────────────────────────────────────────

"""
Advisory policy for an app-config document — controls which scopes'
rows are merged as sources into `ResolvedAppConfig` (§5) and which
scopes may be written. Policies are decoupled from `AppConfig` rows
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
  Joined to `AppConfig.name` by value only — no FK. **Immutable** —
  `update` cannot change this field. A wrongly-named policy is fixed
  by purging (along with any referencing rows) and recreating — see
  §7 S3.8.
  """
  configName: String!

  """
  Dual meaning: (1) which `AppConfig` rows (by `scopeType`) are
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
  document via the `bulk*MyAppConfigs` path. The admin path is not
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
| `publicAppConfigs`                 | ✅        | ✅                               | ✅    |
| `myAppConfigs`                     | ❌        | ✅ (self)                        | ✅    |
| `DomainV2.appConfigs`              | ❌        | ✅ (same domain only)            | ✅    |
| `UserV2.appConfigs`                | ❌        | ✅ (self)                        | ✅    |
| `adminAppConfigs`                  | ❌        | ❌                               | ✅    |
| `appConfigPolicy` / `appConfigPolicies` | ❌   | ✅                               | ✅    |
| `node(id)` → `AppConfig`           | ❌        | ❌                               | ✅    |
| `node(id)` → `ResolvedAppConfig`   | ❌        | ✅ (id's `user_id` is self)      | ✅ (id's `user_id` is self) |
| `node(id)` → `PublicAppConfig`     | ✅        | ✅                               | ✅    |
| `node(id)` → `DomainAppConfig`     | ❌        | ✅ (same-domain rows only)       | ✅    |
| `node(id)` → `UserAppConfig`       | ❌        | ✅ (self)                        | ✅    |
| `node(id)` → `AppConfigPolicy`     | ❌        | ✅                               | ✅    |

Write mutations split into two paths with distinct rules. All
bulk-only.

**Admin path** — `adminBulkCreateAppConfigs`,
`adminBulkUpdateAppConfigs`. Admin regardless of each item's
`key.scopeType`:

| Operation                                  | Anonymous | User | Admin |
|--------------------------------------------|-----------|------|-------|
| `adminBulk{Create,Update,Purge}AppConfigs` | ❌        | ❌   | ✅    |

**Self-service (my) path** — `bulkCreateMyAppConfigs`,
`bulkUpdateMyAppConfigs`. Imply `scope = USER` +
`scopeId = current_user.user_id`:

| Operation              | Anonymous | User (self) | Admin (self) |
|------------------------|-----------|-------------|--------------|
| `bulk*MyAppConfigs`    | ❌        | ✅          | ✅           |

> Admins operating on another user's `USER` row must use the admin
> path with an explicit `AppConfigKey { scopeType: USER, scopeId:
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
  `UserAppConfigRepository.{create|update}` —
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
3. Dispatch the ID-based Action (`update`) to the repository. A
   failure on this item lands in `failed` while the remaining items
   continue.

My-path mutations (`bulkCreateMyAppConfigs`, etc.) **skip this step**:
scope / scopeId are fixed server-side (`USER`,
`current_user.user_id`), RBAC only needs to confirm "authenticated
self", and each item calls
`UserAppConfigRepository.{create|update}` with
`user_id` + `item.name` directly.

The result: admin-path Actions stay uniform (ID-only) while the API
surface still accepts natural-key identification — clients never
need to know row IDs.

The `adminBulk*AppConfigPolicies` mutations follow the same
ID-resolve pattern using `AppConfigPolicyRepository.get(name)` to
look up the policy row's id before dispatching the update Action.

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
| GET    | `/v2/app-configs/{scope_type}/{scope_id}`        | List documents in a scope                   |
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

Response body is the **resolved ResolvedAppConfig** (snake_case
projection of the GQL `ResolvedAppConfig`):

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
exists for this `(user, name)`.

#### Admin writes (bulk-only)

| Method | Path                              | Access | Maps to                         |
|--------|-----------------------------------|--------|---------------------------------|
| POST   | `/v2/app-configs/bulk-create`     | Admin  | `adminBulkCreateAppConfigs`     |
| POST   | `/v2/app-configs/bulk-update`     | Admin  | `adminBulkUpdateAppConfigs`     |
| POST   | `/v2/app-configs/bulk-purge`      | Admin  | `adminBulkPurgeAppConfigs`      |

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

#### My writes (bulk-only)

| Method | Path                                 | Access | Maps to                       |
|--------|--------------------------------------|--------|-------------------------------|
| POST   | `/v2/app-configs/my/bulk-create`     | User   | `bulkCreateMyAppConfigs`      |
| POST   | `/v2/app-configs/my/bulk-update`     | User   | `bulkUpdateMyAppConfigs`      |

Response bodies are the snake_case projection of the corresponding
GQL `Bulk*MyAppConfigsPayload` (a success list plus `failed`).

#### Admin cross-scope search

| Method | Path                        | Access | Description                                                |
|--------|-----------------------------|--------|------------------------------------------------------------|
| POST   | `/v2/app-configs/search`    | Admin  | Cross-scope search — same body schema as `adminAppConfigs` |

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

## 5. `ResolvedAppConfig` — Merge policy

> The merge semantics here apply **only to `ResolvedAppConfig`**. Other
> scope types (`PublicAppConfig` / `DomainAppConfig` /
> `UserAppConfig`) expose the raw `extra_config` as a single
> `config` field.

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
   AppConfig rows.
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

Merge is owned by `UserAppConfigRepository`; DB access is performed
by `AppConfigDBSource`'s merge-specific method — a single SQL that
pulls every row the chain needs in one snapshot. The method receives
the chain as a parameter (a list of `(scope_type, scope_id_expr)`
pairs) derived from the policy:

1. The service resolves the chain for `name` via the policy lookup.
2. `AppConfigDBSource.get_user_resolved_config(user_id, name, chain)`
   — single SQL resolves `domain_name` via a `users` subquery once
   and pulls one row per scope in the chain where it exists.
3. The resulting rows are ordered per the chain (absent rows contribute
   `{}` to the deep merge) and deep-merged: nested objects recursively,
   leaf values replaced by the higher-priority scope, lists treated as
   leaves and replaced wholesale.
4. The ordered rows become `ResolvedAppConfig.sources`; the deep-merge
   result becomes `ResolvedAppConfig.mergedConfig`.

The Connection query (`myAppConfigs`) is backed by the search-specific
method on `AppConfigDBSource` — the same single-SQL approach,
generalized to return one resolved entry per `name` for which at
least one row in the chain exists. When the caller's filter pins a
specific `name`, the resolver consults the policy for that name to
derive the chain; otherwise each resulting `name` is resolved
independently (policies may differ across `name`s).

`MergedAppConfig` / `MergedAppConfigPage` are service-layer return
dataclasses — 1:1 mappings to the GraphQL `ResolvedAppConfig` /
`ResolvedAppConfigConnection`. `AppConfigFilter` / `Pagination` are the
same internal containers introduced for `db_source.search` in §2.

```python
class AppConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_user_resolved_config(
        self,
        user_id: str,
        name: str,
        chain: list[AppConfigScopeType],
    ) -> MergedAppConfig:
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
                AppConfigRow.scope_type == scope_type,
                AppConfigRow.scope_id == scope_id_for[scope_type],
            )
            for scope_type in chain
        ]
        async with self._db.begin_readonly_session() as db_sess:
            rows = (await db_sess.execute(
                sa.select(AppConfigRow).where(
                    AppConfigRow.name == name,
                    sa.or_(*scope_predicates),
                )
            )).scalars().all()

        by_scope = {row.scope_type: row for row in rows}
        ordered_sources = [
            by_scope[scope_type] for scope_type in chain if scope_type in by_scope
        ]
        merged = {}
        for row in ordered_sources:
            merged = deep_merge(merged, row.extra_config)

        return MergedAppConfig(
            user_id=user_id,
            name=name,
            sources=ordered_sources,                # ResolvedAppConfig.sources
            merged_config=merged,                   # ResolvedAppConfig.mergedConfig
        )

    async def search_user_resolved_configs(
        self,
        user_id: str,
        filter: AppConfigFilter,
        pagination: Pagination,
        chain_for_name: Callable[[str], list[AppConfigScopeType]],
    ) -> MergedAppConfigPage:
        # Connection-shaped counterpart — derives the chain per
        # `name` via `chain_for_name` (service-provided closure that
        # reads the policy cache; every `name` is guaranteed to have
        # a policy). Pagination uses `name` as a stable cursor key
        # applied in SQL. Full implementation lives in the §3
        # Connection resolver.
        ...


class UserAppConfigRepository:
    """
    Dual role: `USER` row CRUD (serving `UserAppConfig`) + read-side
    merged view (serving `ResolvedAppConfig`). The merge path delegates to
    `AppConfigDBSource`'s merge-specific method, which reads two
    source rows in a single SQL while never touching DOMAIN. No
    separate `ResolvedAppConfigRepository` — both roles live here.
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

    # ── Resolved view (ResolvedAppConfig) ──────────────────────────
    # `AppConfigDBSource`'s merge-specific method already performs
    # the users-subquery resolution inside a single SQL, so the
    # repository here is a thin delegate.

    async def get_resolved(
        self,
        user_id: str,
        name: str,
        chain: list[AppConfigScopeType],
    ) -> MergedAppConfig:
        return await self._db_source.get_user_resolved_config(
            user_id, name, chain
        )

    async def search_resolved(
        self,
        user_id: str,
        filter: AppConfigFilter,
        pagination: Pagination,
        chain_for_name: Callable[[str], list[AppConfigScopeType]],
    ) -> MergedAppConfigPage:
        return await self._db_source.search_user_resolved_configs(
            user_id, filter, pagination, chain_for_name
        )
```

### Exposure

`ResolvedAppConfig` exposes the raw source rows that contributed to
the resolution plus the deep-merge result:

- `sources` — the ordered list of `AppConfig` source rows (low → high
  priority, matching the chain). Absent scopes simply do not appear.
  The list is empty only when no scope in the chain has a row, in
  which case the `name` would not appear in `myAppConfigs` at all.
- `mergedConfig` — the deep-merge of `sources` in order; the value
  the UI actually applies.

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
   before login, it issues a `publicAppConfigs` query with a `name`
   filter (no auth). The `theme` / `branding` shapes are pulled via
   a single document fetch each — see S1 in §7. On no-edge /
   network error the WebUI falls back to its built-in defaults for
   that document.

2. **Post-login** — the WebUI issues a single `myAppConfigs` query
   to fetch *all* of the caller's resolved documents in one round
   trip. Each entry carries `sources` (raw `AppConfig` rows per scope
   in merge order) and the deep-merged `mergedConfig` (§5). Admins
   use the same query for their own session (admins are also users
   for the purpose of personal settings). `DOMAIN` scope does not
   participate in the default merge chain, so an admin UI that needs
   to manage domain policy issues a separate `DomainV2.appConfigs` /
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
        sources { scopeType scopeId name config updatedAt }
        mergedConfig
      }
    }
  }
  publicAppConfigs {
    edges { node { name config } }
  }
}
```

- Server: `myAppConfigs` returns one entry per `name` for which at
  least one source row in the merge chain exists. The chain comes
  from the matching `AppConfigPolicy.scope_sources` when present,
  and defaults to `[DOMAIN_USER_DEFAULTS, USER]` (caller / caller's
  domain) otherwise. `sources` carries the raw rows in chain order;
  `mergedConfig` is their deep merge. See §5.
- The WebUI initializes UI state from `mergedConfig` per document
  and keeps the `sources` list around so the Settings page can
  distinguish user-changed (`scopeType = USER`) from admin-provided
  defaults (`scopeType = DOMAIN_USER_DEFAULTS`, etc.).

### S3. The user saves their own document

The user replaces their `preferences` document — e.g. language,
experimental-feature toggles, visible-column choices per table. They
call the self-service `bulkUpdateMyAppConfigs` — each item carries
only `name` + `config`, with `scopeType` / `scopeId` injected server-side
as `USER` + `current_user.user_id`. Even a single-item write goes
through the bulk path (1-element `items` array); the recomputed
`ResolvedAppConfig` comes back as `updated[0]`, so no separate
`myAppConfigs` re-query is needed.

```graphql
mutation SaveMyConfig($input: BulkUpdateMyAppConfigInput!) {
  bulkUpdateMyAppConfigs(input: $input) {
    updated {
      name
      sources { scopeType scopeId name config updatedAt }
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
- The input `config` replaces the USER row's stored JSON wholesale.
  `ResolvedAppConfig.mergedConfig` is read-only computed and cannot
  be written.
- **Replace** semantics: anything the caller wants to keep must be
  sent in the same payload — there is no partial-merge or per-key
  patch.
- **Policy**: if an `AppConfigPolicy` exists for `name` and either
  `USER ∉ scope_sources` or `user_writable = False`, the item is
  appended to `failed` with a policy-violation message. Clients can
  discover this ahead of time by reading the policy via
  `appConfigPolicy(name:)`.
- **First write vs. subsequent writes**: `bulkUpdateMyAppConfigs`
  places items with no USER row into `failed`. For the very first
  save of a given `name`, the client calls `bulkCreateMyAppConfigs`
  with the same shape. Clients can disambiguate by checking whether
  the `myAppConfigs` entry for that `name` already has a `USER` row
  in its `sources` list.

### S3.5. Admin publishes an app-config policy

Before the `theme` document can be published (S4 below), an admin
establishes a policy for `theme` that restricts writes to an
admin-only scope and forbids per-user customization. The policy is
**required** (§1 required-policy invariant) — no AppConfig row for
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
    failed { configName message }
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
  - `bulk*MyAppConfigs` calls targeting `theme` are rejected because
    `user_writable = false`.
  - `myAppConfigs` entries for `theme` are resolved through the
    chain `[DOMAIN]` (single-scope — `sources` has at most one
    element and `mergedConfig` equals that element's `config`).
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
from the next `bulkUpdateMyAppConfigs` onward users can layer their
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
    failed { configName message }
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
  - Users can now call `bulkCreate/UpdateMyAppConfigs` targeting
    `theme` and write their own `USER` row.
  - The next `myAppConfigs` call returns `theme` entries whose
    `sources` is `[<DOMAIN row>, <USER row if present>]` and whose
    `mergedConfig` is `domain ⊕ user`.
- Reversibility: flipping the policy back to
  `scopeSources=["domain"]` + `userWritable=false` blocks new user
  writes and excludes `USER` rows from the resolved view, but leaves
  any pre-existing `USER` rows untouched at the DB level (they
  simply stop being read). Admins who want those rows gone target
  them with `adminBulkPurgeAppConfigs` (see S3.8).

### S3.8. Admin fixes a misconfigured policy or config

Since `configName` is immutable (§1), a typo at policy-creation time
cannot be fixed by renaming. The admin's recovery path is a **purge
and rebuild** workflow. The mutations run in a specific order because
of the required-policy invariant:

1. If any AppConfig rows already exist under the wrong `config_name`,
   purge them first — the policy cannot be purged while references
   exist.
2. Purge the wrong policy.
3. Create the correct policy.
4. Re-create any AppConfig rows under the correct `config_name`.

```graphql
# Step 1 — purge the bad AppConfig rows (keys identify them).
mutation PurgeBadConfigs($input: AdminBulkPurgeAppConfigInput!) {
  adminBulkPurgeAppConfigs(input: $input) {
    purged { scopeType scopeId name }
    failed { scopeType scopeId name message }
  }
}

# Step 2 — purge the mis-named policy.
mutation PurgeBadPolicy($input: AdminBulkPurgeAppConfigPolicyInput!) {
  adminBulkPurgeAppConfigPolicies(input: $input) {
    purgedConfigNames
    failed { configName message }
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
  the service checks for remaining AppConfig references under that
  `config_name` before purging.
- Purge is the only deletion verb in the BEP; day-to-day writes
  still flow through create / update and never remove rows on their
  own. Users cannot call purge.

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
    created { id scopeType scopeId name config updatedAt }
    failed { scopeType scopeId name message }
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
  to the matching repository (§2) and strictly inserts a new row.
  Items whose key already has a row land in `failed` — the admin
  falls back to `adminBulkUpdateAppConfigs`.
- Policy: if an `AppConfigPolicy` exists for `theme` and
  `DOMAIN_USER_DEFAULTS ∉ scope_sources`, the item is rejected with
  a policy-violation message. The typical setup for a document like
  `theme` — as shown in S3.5 — lists
  `scope_sources=["domain_user_defaults"]`, which admits this
  write.
- Effect: every user in the domain picks up the new defaults on the
  next `myAppConfigs` read (merged per §5).

### S5. Admin seeds a specific user's document on their behalf

For a support request, an admin seeds user A's `preferences` USER row
for the first time. Since the target is another user's row, this
must use the admin path — `adminBulkCreateAppConfigs` with
`key.scopeType = USER` and `key.scopeId = user A's user_id`, not the
self-service bulk path.
Items whose key already has a row land in `failed`, in which case
the admin falls back to `adminBulkUpdateAppConfigs`.

```graphql
mutation AdminCreateAppConfigsForUser($input: AdminBulkCreateAppConfigInput!) {
  adminBulkCreateAppConfigs(input: $input) {
    created { id scopeType scopeId name config updatedAt }
    failed { scopeType scopeId name message }
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
- `adminBulkCreateAppConfigs` fails the item if a row already exists
  for the key; use `adminBulkUpdateAppConfigs` instead to overwrite.
- Policy: if an `AppConfigPolicy` for `preferences` has `USER ∉
  scope_sources`, the admin path still rejects the item
  (`scope_sources` applies to both paths — admins just bypass
  `user_writable`, not the scope list). With the usual
  `preferences`-style policy (`scope_sources` includes `USER`) this
  write passes.
- The response is a list of raw `AppConfig`; the target user's
  resolved view reflects the new USER row (merged with the matching
  domain defaults) on the next `myAppConfigs` read from that user's
  session.

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
      node { id scopeType scopeId name config updatedAt }
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
- **Policy `description`** — intentionally dropped from the initial
  table. A human-readable summary is useful for admin UIs listing
  policies; adding it later is a non-breaking column addition.
- **Policy deprecation** — because there is no lifecycle coupling
  (§1), the only way to "retire" a policy today is to update it so
  nothing can satisfy its constraints or to simply delete it and
  accept that existing rows become policy-less. A `deprecated` flag
  is a reasonable future extension.
- **Policy audit trail** — history of changes to an
  `AppConfigPolicy` (who changed `scope_sources` from X to Y, when)
  is not modelled here. If audit becomes important, a paired
  `app_config_policy_audit_log` table is the natural fit.
- **Invariant: `user_writable = True` requires `USER ∈
  scope_sources`** — not enforced today; the two fields are kept
  independent. A future BEP may add the invariant if the combination
  is shown to confuse operators.
