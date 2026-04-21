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
- **Write mutations split admin/user, update and delete as separate
  operations.** `admin_update_app_config` / `update_my_app_config`
  apply a **deep-merge partial update** (JSON Merge Patch with `null`
  interpreted as a plain JSON value, *not* as a deletion sentinel). To
  remove keys explicitly, callers use the dedicated
  `admin_delete_app_config_keys` / `delete_my_app_config_keys`
  mutations that take a list of JSON key paths. Rows themselves are
  never deleted — only key-level removals.
- **Single source-of-truth table**: a single `app_configs` table holds
  every scope; only the exposure layer is split.
- **Relay style**: Input/Payload conventions, the Node interface, and
  `clientMutationId`.

---

## 1. DB Layer — `app_configs` table

### Schema changes

Add a `user_app_config_defaults` column to `app_configs` that is
meaningful only on the domain scope.

`scope_type` is **stored as a plain `String` at the DB column level**
and converted to the `AppConfigScopeType` enum only when materializing
the row at the data layer. We deliberately avoid the Postgres ENUM
type because adding/removing enum members would otherwise require an
alembic migration every time, and `scope_type` values for this table
are only ever set by server code (no direct external input). New
scopes (e.g. `project`, future `team`, etc.) become usable with a
code-only change.

```python
class AppConfigScopeType(enum.StrEnum):
    GLOBAL = "global"
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"


class AppConfigRow(Base):
    __tablename__ = "app_configs"

    id: Mapped[uuid.UUID]

    # Stored as plain str — no migration needed when the enum changes.
    # Cast to AppConfigScopeType at the data-layer conversion boundary.
    scope_type: Mapped[str] = mapped_column(sa.String(length=32), nullable=False, index=True)

    scope_id: Mapped[str]                     # global: literal "global"; otherwise domain_name / user_id
    extra_config: Mapped[dict[str, Any]]      # shared across all scopes

    created_at: Mapped[datetime]
    modified_at: Mapped[datetime]

    # NEW — used only on DOMAIN rows; left empty otherwise.
    user_app_config_defaults: Mapped[dict[str, Any]] = mapped_column(
        pgsql.JSONB, nullable=False, default=dict
    )

    __table_args__ = (sa.UniqueConstraint("scope_type", "scope_id", name="uq_app_configs_scope"),)

    def to_data(self) -> AppConfigData:
        return AppConfigData(
            id=self.id,
            scope_type=AppConfigScopeType(self.scope_type),  # str → enum
            scope_id=self.scope_id,
            ...
        )
```

### Scope ID convention

| `scope_type` | `scope_id` value          | Row count    |
|--------------|---------------------------|--------------|
| `global`     | literal string `"global"` | at most 1    |
| `domain`     | `domain_name`             | 1 per domain |
| `user`       | `user_id` (UUID string)   | 1 per user   |

The `UniqueConstraint` on `(scope_type, scope_id)` guarantees a single
row per scope.

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
├── user_app_config_repository.py
└── repositories.py                    # exports all three repos
```

### Repository responsibility split

| Repository                  | Methods                                                                                |
|-----------------------------|----------------------------------------------------------------------------------------|
| `GlobalAppConfigRepository` | `get()`, `upsert(extra_config)`                                                        |
| `DomainAppConfigRepository` | `get(domain_name)`, `upsert(domain_name, extra_config, user_app_config_defaults)`      |
| `UserAppConfigRepository`   | `get(user_id)`, `upsert(user_id, extra_config)`, `get_merged(user_id, domain_name)`    |

### `db_source` is a single module

The underlying table is the same, so the ORM query builder is managed
in one place.

```python
class AppConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get(
        self, scope_type: AppConfigScopeType, scope_id: str
    ) -> AppConfigRow | None:
        async with self._db.begin_readonly_session() as db_sess:
            ...

    async def upsert(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
        extra_config: Mapping[str, Any],
        user_app_config_defaults: Mapping[str, Any] | None = None,  # DOMAIN only
    ) -> AppConfigRow:
        async with self._db.begin_session() as db_sess:
            ...
```

- `_db` is kept as a field on `AppConfigDBSource`.
- Each public method opens its own transaction boundary via
  `async with self._db.begin_readonly_session()` /
  `begin_session()`.
- Callers (repository / service) never pass a session in —
  matches `repositories/CLAUDE.md`'s
  "NEVER accept a DB session from the caller" rule.

Permission checks and scope validation are performed in the service
layer.

---

## 3. GraphQL Schema — per-entity exposure

Two exposure strategies depending on the scope:

- **`global_app_config`**: no parent entity, so it is exposed as a
  standalone root field `globalAppConfig` (no auth required).
- **`domain_app_config` / `user_app_config`**: exposed as a child field
  (`appConfig`) on the `Domain` / `User` nodes so they can be queried
  in the same round trip as the parent entity — no separate root field.
  The Relay `Node` interface still supports direct access by ID
  (`node(id: $id)`).

### Types

```graphql
"""Global config. Readable without authentication."""
type GlobalAppConfig implements Node {
  id: ID!

  """Stored config value (global-scope)."""
  config: JSON!

  createdAt: DateTime!
  modifiedAt: DateTime!
}

"""Domain config. Admin read & write."""
type DomainAppConfig implements Node {
  id: ID!

  """Owning domain (back-reference). Lookup only."""
  domain: Domain!

  """Stored config value for the domain."""
  config: JSON!

  """Per-user preference defaults — merge base for users in the domain."""
  userAppConfigDefaults: JSON!

  createdAt: DateTime!
  modifiedAt: DateTime!
}

"""User personal config. Owner/Admin read; owner or admin can write."""
type UserAppConfig implements Node {
  id: ID!

  """Owning user (back-reference)."""
  user: User!

  """Raw value the user customized (pre-merge)."""
  userCustomizedConfig: JSON!

  """
  Effective applied value: deep merge of userAppConfigDefaults (domain)
  ⊕ userCustomizedConfig (user) — clients render the UI from this value.
  """
  config: JSON!

  createdAt: DateTime!
  modifiedAt: DateTime!
}
```

### Added/extended fields (Relationship)

To make the types above naturally traversable from their parent
entities (`Domain` / `User`), the following fields are added to the
existing nodes. No separate root queries — **access via the parent
node**.

| Location   | Field                          | Access path                                                          |
|------------|--------------------------------|----------------------------------------------------------------------|
| `Domain`   | `appConfig: DomainAppConfig`   | `domain(name) { appConfig }`                                         |
| `UserNode` | `appConfig: UserAppConfig`     | `user_node(id) { appConfig }`                                        |

### Permissions

The rule is simple — **if you have access to the parent entity, you
can access its `appConfig`**.

- `UserNode.appConfig`: the user can reach their own `UserNode` (via
  `user_node(id)`), so they can read their own `appConfig`. Admins
  can reach any `UserNode`, so they can read any user's `appConfig`.
- `Domain.appConfig`: only admins can read `Domain` nodes per the
  existing policy, so only admins can read it.
- `globalAppConfig`: no parent → no permission constraints; anyone,
  including anonymous callers, can access.

There is no separate permission check on the `appConfig` field; it
inherits the parent resolver's policy.

Schema definition:

```graphql
extend type Domain {
  """
  Domain app config. Admin only — returns null for non-admin callers
  who reach this through their own domain without sufficient privilege.
  """
  appConfig: DomainAppConfig
}

extend type UserNode {
  """
  User app config. Owner or admin only. Null when no row exists.
  Both the merged effective value (`config`) and the raw user-customized
  value (`userCustomizedConfig`) are exposed on the same node.
  """
  appConfig: UserAppConfig
}

```

A self-fetch shortcut root field `myAppConfig` is added so callers
can pull their own `UserAppConfig` directly without going through
`user_node(id)`.

### Queries

```graphql
type Query {
  """Global config (no auth). Readable before login."""
  globalAppConfig: GlobalAppConfig

  """
  Current user's app config (auth required). Resolves the current user
  internally and returns their UserAppConfig.
  """
  myAppConfig: UserAppConfig

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
  #                                — admin → user_node(id: ...) { appConfig { ... } }
  # domain(name: String!): Domain  — admin → domain(name: ...) { appConfig { ... } }
  # node(id: ID!): Node            — Relay standard, direct access by global ID
}
```

#### `adminAppConfigs` — Connection / Filter / OrderBy

```graphql
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

"""AppConfig search filter. All fields are AND-combined."""
input AppConfigFilterGQL {
  """Filter by scope type (`global` / `domain` / `user`)."""
  scope: AppConfigScopeEnumFilter

  """Exact match on `scope_id` (e.g. a specific domain_name or user_id)."""
  scopeId: StringFilter

  """`modified_at` range filter."""
  modifiedAt: DateTimeFilter
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

enum AppConfigOrderField {
  SCOPE
  SCOPE_ID
  MODIFIED_AT
  CREATED_AT
}
```


### Mutations

Write mutations come in two flavors that match the access model, and
each flavor has separate **update** and **delete** operations:

- Admin:
  - `admin_update_app_config` — partial update of any scope (by row id).
  - `admin_delete_app_config_keys` — remove specified keys from any
    scope (by row id).
- Self:
  - `update_my_app_config` — partial update of the caller's
    `user_app_config`. The server fixes the target to
    `scope_id = current_user.user_id`.
  - `delete_my_app_config_keys` — remove specified keys from the
    caller's `user_app_config`.

Rows themselves are never deleted; only key-level removals are
supported.

**Update mutations** apply a **deep-merge partial update** onto the
existing stored JSON:

- Keys present in the input are merged into the existing value at the
  same path. Nested objects merge recursively.
- Keys absent from the input are left unchanged.
- A `null` leaf value is written **as a JSON null** — it does *not*
  delete the key. Use the delete mutation when you want to remove
  keys explicitly.
- Arrays are treated as leaves — replaced wholesale, not
  element-merged (same rule used by the user/domain read-merge in §5).
- Supplying `{}` is a no-op.

**Delete mutations** take a list of **JSON key paths** (dot-notation,
e.g. `"sectionA.optionX"`). Each path is removed from the target
JSON. Non-existent paths are silently ignored (idempotent). Removing
a non-leaf path removes the entire subtree.

```graphql
type Mutation {
  """
  App config update (Admin only). Identifies an existing row of any
  scope (global/domain/user) by id and deep-merges the provided
  JSON into it.
  """
  adminUpdateAppConfig(input: AdminUpdateAppConfigInput!): UpdateAppConfigPayload!

  """
  Remove specified keys from an app config row (Admin only).
  Identified by row id. Takes a list of JSON key paths
  (dot-notation).
  """
  adminDeleteAppConfigKeys(input: AdminDeleteAppConfigKeysInput!): UpdateAppConfigPayload!

  """Self user_app_config partial update. Target is the caller."""
  updateMyAppConfig(input: UpdateMyAppConfigInput!): UpdateMyAppConfigPayload!

  """Remove specified keys from the caller's user_app_config."""
  deleteMyAppConfigKeys(input: DeleteMyAppConfigKeysInput!): UpdateMyAppConfigPayload!
}

enum AppConfigScopeGQL {
  GLOBAL
  DOMAIN
  USER
}

# ── Admin input ───────────────────────────────────────────────

input AdminUpdateAppConfigInput {
  clientMutationId: String

  """ID of the app_config row to update (Relay global ID)."""
  id: ID!

  """
  Partial update. The provided JSON is deep-merged into the existing
  stored value — keys present in the input are merged in, keys absent
  are left unchanged, and leaf `null` values are written as JSON null
  (not deletions). Use `adminDeleteAppConfigKeys` to remove keys.
  Omit the field entirely to leave `config` untouched.
  - GLOBAL/DOMAIN scope: patches the scope's `config` field.
  - USER scope: patches that user's `userCustomizedConfig`
    (the merged `config` is read-only computed and cannot be written
    directly).
  """
  config: JSON

  """
  DOMAIN scope rows only — partial update of `userAppConfigDefaults`
  via the same deep-merge semantics as `config`. Omit to leave
  `userAppConfigDefaults` untouched.
  """
  userAppConfigDefaults: JSON
}

input AdminDeleteAppConfigKeysInput {
  clientMutationId: String

  """ID of the app_config row to delete from (Relay global ID)."""
  id: ID!

  """
  JSON key paths to remove from `config` (dot-notation, e.g.
  `"sectionA.optionX"`). Missing paths are silently ignored.
  Removing a non-leaf path removes the entire subtree.
  """
  configKeys: [String!]

  """
  DOMAIN scope rows only — key paths to remove from
  `userAppConfigDefaults`.
  """
  userAppConfigDefaultsKeys: [String!]
}

# Both `config` and `userAppConfigDefaults` are optional on
# AdminUpdateAppConfigInput; whatever is provided is patched into the
# existing value. Omitting both is a no-op. Same optionality applies
# to the two key lists on AdminDeleteAppConfigKeysInput.

# ↑ Identification is by row id, so the row must exist. Creating new
# scope rows (a new global / new domain / new user row) belongs to a
# separate flow — typically by seeding an empty row when the
# domain/user is created, or via a future `adminCreateAppConfig`
# mutation.

# ── My (self) input ──────────────────────────────────────────

input UpdateMyAppConfigInput {
  clientMutationId: String

  """
  Partial update of UserAppConfig.userCustomizedConfig. Deep-merged
  into the caller's existing value; keys absent from the input are
  preserved; leaf `null` values are written as JSON null (not
  deletions). Use `deleteMyAppConfigKeys` to remove keys.
  """
  userCustomizedConfig: JSON!
}

input DeleteMyAppConfigKeysInput {
  clientMutationId: String

  """
  JSON key paths to remove from the caller's `userCustomizedConfig`
  (dot-notation). Missing paths are silently ignored.
  """
  keys: [String!]!
}

# ── Payload ──────────────────────────────────────────────────

type UpdateAppConfigPayload {
  clientMutationId: String
  appConfig: AppConfig!
}

type UpdateMyAppConfigPayload {
  clientMutationId: String
  """The updated self config (includes the merged `config`)."""
  appConfig: UserAppConfig!
}

"""Generic AppConfig type used in the admin mutation payload — exposes the raw stored value."""
type AppConfig implements Node {
  id: ID!
  scope: AppConfigScopeGQL!
  scopeId: String!

  """Raw stored value. For USER scope, equivalent to `userCustomizedConfig`."""
  config: JSON!

  """Populated only on DOMAIN scope rows."""
  userAppConfigDefaults: JSON

  createdAt: DateTime!
  modifiedAt: DateTime!
}
```

### Permission matrix

| Operation                            | Anonymous | User       | Admin |
|--------------------------------------|-----------|------------|-------|
| `globalAppConfig`                    | ✅        | ✅         | ✅    |
| `myAppConfig`                        | ❌        | ✅ (self)  | ✅    |
| `Domain.appConfig`                   | ❌        | ❌         | ✅    |
| `UserNode.appConfig`                 | ❌        | ✅ (self)  | ✅    |
| `adminAppConfigs`                    | ❌        | ❌         | ✅    |
| `adminUpdateAppConfig`               | ❌        | ❌         | ✅    |
| `adminDeleteAppConfigKeys`           | ❌        | ❌         | ✅    |
| `updateMyAppConfig`                  | ❌        | ✅ (self)  | ✅    |
| `deleteMyAppConfigKeys`              | ❌        | ✅ (self)  | ✅    |

Where the checks live:
- `admin*` mutation resolver: `check_admin_only()` at entry.
- `user*` mutation resolver: `current_user()` for auth, then the server
  hard-fixes `scope_id` to `current_user.user_id` — there is literally
  no input field that can target another user.
- `Domain.appConfig` field resolver: `check_admin_only()`; returns null
  (or raises) for non-admin callers.
- `UserNode.appConfig` field resolver: returns null (or raises) when
  the parent node's `user_id` differs from `current_user` and the
  caller is not an admin.

---

## 4. REST Schema — `/app_config/{scope_type}/{scope_id}`

Scope is expressed as URL path segments, consistent with the v2
routing convention `api/rest/v2/{entity}/{scope_type}/{scope_id}/...`.

### Endpoints

REST splits along the same Admin/User axis as GraphQL. Admin handles
arbitrary scopes via `/v2/app_config/{scope_type}/{scope_id}`; users
have a self-service path `/v2/app_config/user/me`.

DELETE is not provided. To clear, PUT with `extra_config = {}`.

| Method | Path                                      | Access     | Description                                     |
|--------|-------------------------------------------|------------|-------------------------------------------------|
| GET    | `/v2/app_config/global`                         | Anonymous  | Read global config                              |
| GET    | `/v2/app_config/domain/{domain_name}`           | Admin      | Read domain config                              |
| GET    | `/v2/app_config/user/{user_id}`                 | Admin      | Read any user's config                          |
| POST   | `/v2/app_config/admin/search`                   | Admin      | Cross-scope search (filter / order / paginate)  |
| PATCH  | `/v2/app_config/{scope_type}/{scope_id}`        | Admin      | Partial update (deep merge) of any scope        |
| POST   | `/v2/app_config/{scope_type}/{scope_id}/delete` | Admin      | Remove specified key paths from any scope       |
| GET    | `/v2/app_config/user/me`                        | User       | Read own config (includes merged result)        |
| PATCH  | `/v2/app_config/user/me`                        | User       | Partial update of own config                    |
| POST   | `/v2/app_config/user/me/delete`                 | User       | Remove specified key paths from own config      |

`POST /v2/app_config/admin/search` accepts the same input schema as
the GQL `adminAppConfigs` field (`filter` / `orderBy` / pagination
arguments) in the request body and returns the same result.

> `/v2/app_config/user/me` follows the `my_` self-service convention —
> the adapter resolves `current_user()` internally and fixes
> `scope_id` to the caller's `user_id`. The body accepts only
> `userCustomizedConfig` (snake-case `user_customized_config` in REST);
> there is no input field that can target another user.

---

## 5. `user_app_config` semantics — Merge policy

### Storage

- `user_app_config.extra_config` (the DB column, exposed as
  `userCustomizedConfig` in GQL) stores **only the values the user has
  explicitly set**.
- Domain-provided defaults (`user_app_config_defaults`) are *not*
  copied into user rows — to avoid having to rewrite every user row
  whenever the domain admin changes a default.

### Read (Merge)

`UserAppConfigRepository.get_merged(user_id)` performs the following
in a single transaction:

1. Look up the `domain_name` for `user_id` from `users`.
2. Read the `(scope_type=domain, scope_id=domain_name)` row from
   `app_configs` to get `user_app_config_defaults`.
3. Read the `(scope_type=user, scope_id=user_id)` row from
   `app_configs` to get `extra_config` (= `userCustomizedConfig`).
4. **Deep merge**: nested objects are merged recursively per key; at
   leaf keys, the user value wins over the domain default. Lists are
   treated as leaves and replaced wholesale by the user value
   (element-level merge of arrays has no unambiguous semantics). The
   result is exposed as `UserAppConfig.config`.

```python
# db_source owns session and queries. Repository only delegates.

class AppConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_merged(self, user_id: str) -> MergedAppConfig:
        async with self._db.begin_readonly_session() as db_sess:
            user_row = (await db_sess.execute(
                sa.select(UserRow.domain_name).where(UserRow.uuid == user_id)
            )).one_or_none()
            if not user_row:
                raise UserNotFound(f"User {user_id} not found")
            domain_name = user_row.domain_name

            rows = (await db_sess.execute(
                sa.select(AppConfigRow).where(
                    sa.or_(
                        sa.and_(
                            AppConfigRow.scope_type == AppConfigScopeType.DOMAIN,
                            AppConfigRow.scope_id == domain_name,
                        ),
                        sa.and_(
                            AppConfigRow.scope_type == AppConfigScopeType.USER,
                            AppConfigRow.scope_id == user_id,
                        ),
                    )
                )
            )).scalars().all()

        domain_row = next((r for r in rows if r.scope_type == AppConfigScopeType.DOMAIN), None)
        user_row = next((r for r in rows if r.scope_type == AppConfigScopeType.USER), None)

        domain_defaults = domain_row.user_app_config_defaults if domain_row else {}
        user_customized = user_row.extra_config if user_row else {}
        return MergedAppConfig(
            domain_name=domain_name,
            user_id=user_id,
            user_customized_config=user_customized,
            config=deep_merge(domain_defaults, user_customized),  # GQL: UserAppConfig.config
        )


class UserAppConfigRepository:
    _db_source: AppConfigDBSource

    def __init__(self, db_source: AppConfigDBSource) -> None:
        self._db_source = db_source

    async def get_merged(self, user_id: str) -> MergedAppConfig:
        # Repository only delegates — session and query logic live in db_source.
        return await self._db_source.get_merged(user_id)
```

This follows the rules in `manager/repositories/CLAUDE.md`:
- `_db` is a field on `AppConfigDBSource`. Every public db_source method
  opens its own transaction boundary
  (`async with self._db.begin_readonly_session()`).
- All SQLAlchemy query code lives in `db_source/db_source.py`.
  `repository.py` only delegates.
- The caller (service layer) never passes a session in.

### Exposure

The merged value is returned in the GQL `UserAppConfig.config` field
and the REST `GET /v2/app_config/user/me` response. The same node also
exposes `userCustomizedConfig` (the raw user-customized value), so the
WebUI can distinguish "what the user explicitly changed" from "what
will actually be applied".

---

## 6. User Scenarios — end-to-end caller flows

Each scenario describes *who* calls *when* and *what they want to
achieve*, paired with the actual call spec. Intended as a reference
for client-side implementation.

### S1. Pre-login global config loading (anonymous)

The WebUI fetches the global config before rendering the login
screen. (The JSON shape inside `config` is owned by the frontend;
backend stores it opaquely.)

```graphql
query LoadGlobalAppConfig {
  globalAppConfig {
    config
    modifiedAt
  }
}
```

- No auth token.
- Response: `{ globalAppConfig: { config: { ... opaque JSON ... }, modifiedAt: "..." } }`
- On failure (row missing, network error) the WebUI falls back to its
  built-in defaults.

### S2. Bootstrapping right after login

Right after a successful login, the WebUI fetches everything it needs
to initialize the UI state for this user in a single round trip.

```graphql
query BootstrapMe {
  myAppConfig {
    userCustomizedConfig
    config
    modifiedAt
  }
  globalAppConfig { config }
}
```

- Server: `myAppConfig` resolver identifies the caller via
  `current_user()`, deep-merges the domain's
  `userAppConfigDefaults` with the user's `userCustomizedConfig`, and
  returns the merged result in `config`.
- The WebUI initializes UI state from `config`, and keeps
  `userCustomizedConfig` around separately so the Settings page can
  show only "what the user explicitly changed" in the edit form.

### S3. The user patches part of their own config

The user updates a subset of keys in their `userCustomizedConfig`.

```graphql
mutation SaveMyConfig($input: UpdateMyAppConfigInput!) {
  updateMyAppConfig(input: $input) {
    appConfig {
      userCustomizedConfig
      config
      modifiedAt
    }
  }
}
```

```json
{
  "input": {
    "userCustomizedConfig": {
      "sectionA": { "optionX": "value-1" },
      "sectionB": "value-2"
    }
  }
}
```

- `scope_id` is absent from the input — the server fixes it to
  `current_user.user_id`.
- **Partial update** semantics: other keys the user previously saved
  (e.g. `sectionC.*`) are preserved. Key removal uses
  `deleteMyAppConfigKeys` separately.
- `appConfig.config` in the response already reflects the re-computed
  read-merge of the patched `userCustomizedConfig` with the domain
  defaults. (The JSON shape itself is not defined by this BEP — it is
  owned by the frontend.)

### S4. Admin patches part of a domain's config and user defaults

An admin patches a specific subtree of the domain `config` and a
specific key of `userAppConfigDefaults`.

Step 1 — look up the target row id:

```graphql
query GetDomainAppConfigId($name: String!) {
  domain(name: $name) {
    appConfig { id config userAppConfigDefaults }
  }
}
```

Step 2 — update (deep-merge partial update):

```graphql
mutation UpdateDomainConfig($input: AdminUpdateAppConfigInput!) {
  adminUpdateAppConfig(input: $input) {
    appConfig { id scope scopeId config userAppConfigDefaults modifiedAt }
  }
}
```

```json
{
  "input": {
    "id": "QXBwQ29uZmlnOmRvbWFpbi1kZWZhdWx0",
    "config": { "sectionA": { "optionX": "new-value" } },
    "userAppConfigDefaults": { "sectionB": "default-value" }
  }
}
```

- Server: `check_admin_only()` → locates the DOMAIN row by id →
  deep-merges the input into the existing `config` and
  `userAppConfigDefaults` independently.
- **Partial**: unrelated keys (`sectionA.optionY`, `sectionC.*`, …)
  are left untouched.
- Effect: on the next `myAppConfig` call, every user in that domain
  receives the updated defaults merged with their own
  `userCustomizedConfig`.

### S5. Admin patches a specific user's config on their behalf

For a support request, an admin patches a subset of keys in user A's
`userCustomizedConfig`.

```graphql
query GetUserAppConfigId($userId: String!) {
  user_node(id: $userId) {
    appConfig { id userCustomizedConfig }
  }
}
```

```graphql
mutation OverrideUserConfig($input: AdminUpdateAppConfigInput!) {
  adminUpdateAppConfig(input: $input) {
    appConfig { id scope scopeId config modifiedAt }
  }
}
```

```json
{
  "input": {
    "id": "QXBwQ29uZmlnOnVzZXItMDAwMTIz",
    "config": { "sectionA": { "flag": true } }
  }
}
```

- For the USER scope, the `config` input is deep-merged into that
  user's `userCustomizedConfig` (the merged `config` is a read-only
  computed field and cannot be written directly).
- The next time that user calls `myAppConfig`, the updated
  `userCustomizedConfig` is merged with the domain defaults in the
  response.

### S6. Admin audits all AppConfigs (search / filter / pagination)

Operational cases such as "list every user config in a given domain"
or "show everything modified in the last week".

```graphql
query AuditUserConfigs(
  $filter: AppConfigFilterGQL!
  $orderBy: [AppConfigOrderByGQL!]
  $first: Int
  $after: String
) {
  adminAppConfigs(filter: $filter, orderBy: $orderBy, first: $first, after: $after) {
    edges {
      cursor
      node { id scope scopeId config modifiedAt }
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
    "modifiedAt": { "gte": "2026-04-14T00:00:00Z" }
  },
  "orderBy": [{ "field": "MODIFIED_AT", "direction": "DESC" }],
  "first": 50
}
```

- Server: `check_admin_only()` → Connection search. In cursor mode
  the sort order is pinned to the cursor key.
- Useful when auditing "what settings users are actively overriding
  after a global/domain default change".

### S7. Operator clears specific keys (or subtrees)

Key removal is explicit via the dedicated delete mutation — update
never deletes. An admin removing a subtree and a specific leaf from
a domain's `config`:

```graphql
mutation ClearDomainKeys($input: AdminDeleteAppConfigKeysInput!) {
  adminDeleteAppConfigKeys(input: $input) {
    appConfig { id scope scopeId config modifiedAt }
  }
}
```

```json
{
  "input": {
    "id": "QXBwQ29uZmlnOmRvbWFpbi1kZWZhdWx0",
    "configKeys": ["sectionA", "sectionB.optionX"]
  }
}
```

- `sectionA` — full subtree removed from the domain's `config`.
- `sectionB.optionX` — only that leaf removed; sibling keys under
  `sectionB` are preserved.
- Missing paths are silently ignored (idempotent).
- The row itself is never deleted — it always exists for the lifetime
  of the parent entity.

The self-service equivalent for a user is `deleteMyAppConfigKeys`,
which takes a flat `keys: [String!]!` array targeting their own
`userCustomizedConfig`.
