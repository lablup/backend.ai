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

App configuration is redesigned as **scoped entities** — one row per
`(scope_type, scope_id, config_name)` — so access control and merge
semantics live at the scope level, not the field level. A single scope
(one domain, one user) can hold **multiple named configuration
documents** (`theme`, `menu`, `preferences`, …), each managed
independently.

Every document name is **explicitly registered** in `app_config_keys`,
and a config row cannot exist for an unregistered name. For each
registered name, `app_config_allow_list` enumerates — **one record per
(name, scope)** — which scopes may hold a fragment and in what **merge
order**.
A user's effective configuration for a name is the **deep merge of the
fragments that apply to them**, combined in the allow-list's order.

A user can read and modify their own `user`-scope config, but **only
where the name's allow-list admits the `user` scope**. Whether a value
is admin-fixed or user-overridable is therefore an explicit allow-list
decision — see [Write model](#write-model).

## User Stories

Three scopes cover the use cases (`public` for the pre-login shell):

| Use case                                         | Scope(s)          | Who writes                                  |
|--------------------------------------------------|-------------------|---------------------------------------------|
| Pre-login values (theme, branding)               | `public`          | Admin                                       |
| Domain-wide value the user **cannot** change     | `domain`          | Admin                                       |
| Per-domain **default** the user **can** override | `domain` + `user` | Admin sets the default; user writes their own copy |
| User value with **no** default                   | `user`            | User (admin may also write)                 |

- Admins set values that apply across a domain; a domain-fixed value
  cannot be changed by users.
- Some domain settings must be readable **before login** (theme).
- Where the allow-list admits `user`, users persist their own settings
  on the server (language, recently used sessions, visible/ordered
  table columns, experimental-feature toggles).
- The same scope may publish several independently-managed documents
  loaded by different parts of the WebUI.

## Design Principles

- **Schema-less JSON.** The backend is pure storage; the structure and
  meaning of each document are owned by the frontend.
- **Scope = entity.** Access control is expressed at the scope level,
  not per field. Three scopes: `public` (anonymous read / admin write),
  `domain` (same-domain read / admin write), `user` (owner+admin read /
  owner-modify + admin write).
- **Explicitly registered names.** Every document name lives in
  `app_config_keys`; fragments and allow-list entries reference it by
  foreign key. No fragment may exist for an unregistered name.
- **Allow-list = the merge chain and the write gate.** For each name,
  `app_config_allow_list` holds **one record per participating scope**,
  each carrying a `rank`. Those records — ordered by `rank` — are
  exactly the scopes that may be written and exactly the scopes merged
  into the effective view. This replaces the old
  `AppConfigPolicy.scope_sources` array with one row per entry.
- **Named documents within a scope.** Each fragment is identified by
  `(scope_type, scope_id, config_name)`. Clients address documents
  explicitly by name — no hierarchical fall-through lookup.
- **Single source-of-truth table.** One `app_config_fragments` table
  holds every scope; only the exposure layer is split.

---

## 1. Data model

Three tables, with `app_config_keys` as the hub both others reference.

### `app_config_keys` — the document-name registry

One row per document name. A name must be registered here before any
fragment or allow-list entry can reference it. **Explicitly managed by
admins** (`create` / `purge`) — registration is a deliberate step, not a
side effect of writing a fragment.

- `config_name` — the document name (unique). The foreign-key target for
  both other tables. Immutable (rename = purge + recreate).
- `created_at` / `updated_at`.

### `app_config_fragments` — the per-scope values

Keyed by the natural composite `(scope_type, scope_id, config_name)`
(unique). Columns of note:

- `scope_type` — `public | domain | user`.
- `scope_id` — the scope's identifier (see convention below).
- `config_name` — FK → `app_config_keys.config_name`.
- `config` — schema-less JSON payload.
- `created_at` / `updated_at`.

### `app_config_allow_list` — the per-name scope chain

One row per `(config_name, scope_type)` (unique) — the normalized
replacement for `AppConfigPolicy.scope_sources`. Each row is one entry
in the name's chain.

- `config_name` — FK → `app_config_keys.config_name`.
- `scope_type` — a scope that participates in this name
  (`public | domain | user`).
- `rank` — integer merge priority within the name (low → high; higher
  wins). Assigned on create (see §2).
- `created_at` / `updated_at`.

The set of `scope_type`s present for a `config_name` is **both** the
**write allow-list** (only these scopes may hold a fragment) **and** the
**merge chain** (these scopes, in `rank` order, are deep-merged). Adding
a scope to the chain is a single `create`; removing one is a single
`purge` — never a read-modify-write of an array.

### Scope-ID convention

| `scope_type` | `scope_id`              | Meaning of `config`              |
|--------------|-------------------------|----------------------------------|
| `public`     | literal `"public"`      | pre-login value of the document  |
| `domain`     | `domain_id`             | the domain's value / default     |
| `user`       | `user_id` (UUID string) | the user's own value             |

### Integrity

- A fragment write requires (a) a registered `config_name` (FK to
  `app_config_keys`) and (b) an allow-list entry for the write's
  `(config_name, scope_type)`. The service layer rejects per-row when
  either is missing, with a friendly error; the FK is defense-in-depth.
- `app_config_keys` purge is rejected while any fragment or allow-list
  entry still references the name (`ON DELETE NO ACTION`).
- `app_config_allow_list` purge removes a scope from the chain. Existing
  fragments at that scope are left in the DB but stop being read or
  written; an admin removes them with a fragment purge if desired.

<a id="write-model"></a>
### Write model

Two write paths:

- **Admin path** — `create` / `update` / `purge`, on any scope admitted
  by the allow-list. The only way an admin-owned (`public`, `domain`)
  row, or another user's `user` row, comes into existence.
- **Self-service (`my`) path** — `create` / `update` on the caller's own
  `user` row, **only when** the name's allow-list admits `user`. No
  `purge`.

`create` errors if the natural key already exists; `update` errors if it
does not; `purge` (admin-only) is the single deletion verb. A caller
"clears" a document by `update`-ing it with `{}`, which reads back as
`null` (null projection, §3). `update` replaces the stored JSON
wholesale — no partial/deep update at the write boundary.

**Overridability is an allow-list decision** — there is no admin-seeding
dance:

- **Fixed** (user cannot change): the name's allow-list omits `user`
  (e.g. `[domain]` or `[public]`). The `my` path is rejected, so the
  merged value is the admin's.
- **Overridable**: the allow-list includes `user` at a higher `rank`
  than `domain` (e.g. `[domain, user]`). The admin sets the `domain`
  default; the user creates/updates their own `user` fragment, which
  wins on merge.
- **User-only**: the allow-list is `[user]`; no domain default exists.

To promote a fixed value to user-customizable, the admin adds a single
`user` allow-list entry — no data migration, no schema change. Reverting
— purging that `user` entry — blocks new user writes and drops `user`
fragments from the merge, while leaving the rows in the DB (see §1
*Integrity*).

---

## 2. `rank` — merge priority

`rank` is the integer priority an **allow-list entry** carries within a
`config_name`; the merge applies the corresponding fragments in `rank`
order (low → high, higher wins).

- **Assignment.** A new allow-list entry is placed after the existing
  ones for the same name, so a later-added scope outranks earlier ones
  by default. Admins re-order by setting `rank` explicitly. (Adding
  `domain` before `user` naturally gives the `user` entry the higher
  rank, so the user value wins.)
- **No tier defaults.** Priority is the allow-list `rank`, not derived
  from `scope_type` — a `user` entry outranks a `domain` entry only
  because its `rank` is higher, not because `user` is "above" `domain`.

---

## 3. `AppConfig` — the merged view

Two read shapes exist:

- **`AppConfigFragment`** — one raw row, regardless of scope. Carries
  `scopeType`, `scopeId`, `configName`, and `config`. Callers
  disambiguate scope by reading `scopeType` (no per-scope wrapper
  types).
- **`AppConfig`** — the merged per-user view for a `config_name`: the
  ordered contributing `fragments` plus the deep-merged `config`.

### How a merge is resolved

For a user resolving `config_name`, the chain is the name's
`app_config_allow_list` entries ordered by `rank`. Each entry resolves
to one applicable `scope_id`:

- `public` → `"public"`,
- `domain` → the user's domain,
- `user` → the user's id.

The fragments that exist at those `(scope_type, scope_id, config_name)`
keys are ordered by `rank` (low → high) and deep-merged: nested objects
recurse, scalars and lists are wholesale-replaced, and the higher `rank`
wins on conflict. A single SQL statement joins `app_config_fragments`
with `app_config_allow_list ON config_name AND scope_type`, filtered to
each entry's resolved `scope_id`, and orders by `rank` — a plain
equi-join, with no array membership/position tricks.

**Null projection.** A stored `config` of `{}` reads back as `null`, and
a merged `config` that is empty after combining every fragment is
likewise `null` — clients fall back to their built-in defaults.

### Read variants

- **Single** — resolve one `(user, config_name)` to its `AppConfig`.
- **Search (self)** — paginate the user's own `AppConfig`s, grouped by
  `(user_id, config_name)`; each name's merge is evaluated
  independently.
- **Search (admin, cross-user)** — resolve any user's `AppConfig` for
  audit / support; admin-only.

---

## 4. Client integration (WebUI)

- **Before login**, the WebUI fetches `public` documents (theme,
  branding) anonymously so the shell can render.
- **After login**, it reads its merged `AppConfig`s (`theme`, `menu`,
  `preferences`, …) — already combining the public/domain/user fragments
  admitted by each name's allow-list — and persists user changes through
  the `my` **update** (allowed only where the allow-list admits `user`),
  which returns the recomputed merged view.

---

## 5. User scenarios

- **Register a document name** — admin creates the `app_config_keys` row
  for `theme` and its `app_config_allow_list` entries (the chain) before
  any fragment exists.
- **Pre-login public config** — anonymous read of `public` `theme`.
- **Bootstrap after login** — read merged `AppConfig`s in one round of
  queries; no per-scope stitching on the client.
- **User edits a document** — `my` create/update on the caller's own
  `user` row (only where the allow-list admits `user`); the response is
  the recomputed merge.
- **Admin publishes a fixed domain value** — register the name with
  allow-list `[domain]` (or `[public]`); with no `user` entry, users
  cannot override it.
- **Admin makes a value user-overridable** — add a `user` allow-list
  entry at a higher `rank`; users then create/update their own copy. No
  data migration.
- **Admin reorders contributions** — adjust allow-list `rank`s.
- **Admin retires a document name** — purge the fragments, then the
  allow-list entries, then the `app_config_keys` row (purge is rejected
  while references remain).
- **Admin audit** — cross-scope fragment search and cross-user merged
  search for support.
