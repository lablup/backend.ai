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
`(scope_type, scope_id, config_name)` — so storage and merge live at the
scope level. A single scope (one domain, one user) can hold **multiple
named configs** (`theme`, `menu`, `preferences`, …),
each managed independently.

**Reads are the hot path.** A user's effective configuration for a
`config_name` is the **deep merge of every fragment that applies to
them**, taken from `app_config_fragments` ordered by the `rank` of each
fragment's allow-list entry — one indexed join, **no permission
lookup**.

**Write authorization is set up ahead of time.** Every config name is
**explicitly registered** in `app_config_definitions`, and `app_config_allow_list`
records — **pre-configured by admins** — enumerate the
`(config_name, scope_type)` pairs at which a fragment may be written.
**Every** fragment write, admin or user, requires a matching record;
admins additionally own the allow-list and `app_config_definitions` themselves
(users cannot). So the cost of permission lives entirely on the
(infrequent) write path and the (one-time) admin setup, never on read.

Whether a value is admin-fixed or user-overridable is therefore a matter
of whether an allow-list grant exists — see [Write model](#write-model).

## User Stories

Three scopes cover the use cases (`public` for the pre-login shell):

| Use case                                         | Scope(s)          | Who writes                                       |
|--------------------------------------------------|-------------------|--------------------------------------------------|
| Pre-login values (theme, branding)               | `public`          | Admin                                            |
| Domain-wide value the user **cannot** change     | `domain`          | Admin                                            |
| Per-domain **default** the user **can** override | `domain` + `user` | Admin sets the default; user writes their own copy (where granted) |
| User value with **no** default                   | `user`            | User (where granted); admin may also write       |

- Admins set values that apply across a domain; a domain-fixed value
  cannot be changed by users (no `user` write grant exists).
- Some domain settings must be readable **before login** (theme).
- Where the admin has granted it, users persist their own settings on
  the server (language, recently used sessions, visible/ordered table
  columns, experimental-feature toggles).
- A single `config_name` can hold a different value at each scope: an
  admin manages the `public` / `domain` value, and the user changes only
  their own `user`-scope fragment. This one mechanism — per-scope
  fragments combined by the merge — covers every use case above.

## Design Principles

- **Schema-less JSON.** The backend is pure storage; the structure and
  meaning of each config are owned by the frontend.
- **Scope = entity.** Access control is expressed at the scope level,
  not per field. Three scopes: `public` (anonymous read / admin write),
  `domain` (same-domain read / admin write), `user` (owner+admin read /
  owner-modify + admin write).
- **Explicitly registered names.** Every config name lives in
  `app_config_definitions`; allow-list entries reference it by foreign key,
  and fragments reference it transitively through their allow-list entry (a
  fragment requires an entry, and the entry requires a registered name — so
  no direct fragment FK is needed). No fragment may exist for an
  unregistered `config_name`.
- **Reads are unconditional.** The merge **must** join
  `app_config_fragments` to `app_config_allow_list` — `rank` lives only on
  the allow-list entry, so the ordering cannot be computed without it (an
  indexed `(config_name, scope_type)` join). The join is for `rank` alone;
  no permission or policy is evaluated at read time.
- **Allow-list = the write gate and the merge order.** `app_config_allow_list`
  holds **one record per `(config_name, scope_type)`**; a fragment at
  that scope may be created **only if** the record exists — through the
  admin mutations and the regular ones alike. Fragments reference their
  entry by FK (`ON DELETE CASCADE`), so removing an entry removes its
  fragments. What sets admins apart is that they alone manage the
  allow-list (and the `app_config_definitions`) itself.
- **`rank` lives on the allow-list entry.** Merge priority is an
  admin-owned policy: it sits on the (admin-managed) allow-list entry,
  not on the fragment — a fragment owner editing their own fragment can
  never re-order the merge (see §2).
- **Single source-of-truth table.** One `app_config_fragments` table
  holds every scope; only the exposure layer is split.

---

## 1. Data model

Three tables, with `app_config_definitions` as the hub both others reference.

### `app_config_definitions` — the registered configs

One row per config name. A name must be registered here before any
fragment or allow-list entry can reference it. **Explicitly managed by
admins** (`create` / `purge`) — registration is a deliberate step, not a
side effect of writing a fragment.

- `config_name` — the config name (unique). The foreign-key target for
  both other tables. Immutable (rename = purge + recreate).
- `created_at` / `updated_at`.

### `app_config_fragments` — the per-scope values (read hot path)

Keyed by the natural composite `(scope_type, scope_id, config_name)`
(unique). The read merge scans this table alone. Columns of note:

- `scope_type` — `public | domain | user`.
- `scope_id` — the scope's identifier (see convention below).
- `config_name` — FK → `app_config_definitions.config_name`.
- `(config_name, scope_type)` — composite FK →
  `app_config_allow_list` with `ON DELETE CASCADE`: a fragment exists
  only while its allow-list entry does, and carries no rank of its own —
  its merge priority is the entry's `rank` (see §2).
- `config` — schema-less JSON payload.
- `created_at` / `updated_at`.

### `app_config_allow_list` — the per-`(config_name, scope_type)` write gate

One row per `(config_name, scope_type)` (unique) — a normalized,
single-purpose table: **the write gate**. A fragment at `(config_name, scope_type)`
may be written only if its row exists here. Admins set these up in
advance.

- `config_name` — FK → `app_config_definitions.config_name`.
- `scope_type` — a scope at which fragments may be written
  (`public | domain | user`). A user-overridable config carries a
  `(config_name, user)` row; an admin-only value carries
  `(config_name, domain)` and/or `(config_name, public)`.
- `rank` — the merge priority every fragment under this entry carries
  (low → high; higher wins). Defaults per scope type (see §2); admins
  may set it explicitly.
- `created_at` / `updated_at`.

A row's **presence** is the write grant, and its `rank` is the merge
order of its fragments. It gates **both** write paths; admins, unlike
users, may also create/purge the allow-list rows themselves — and
purging one cascades to its fragments.

### Scope-ID convention

| `scope_type` | `scope_id`              | Meaning of `config`              |
|--------------|-------------------------|----------------------------------|
| `public`     | literal `"public"`      | pre-login value of the config  |
| `domain`     | `domain_id`             | the domain's value / default     |
| `user`       | `user_id` (UUID string) | the user's own value             |

### Integrity

- **Every** fragment create (admin or regular) requires an
  `app_config_allow_list` row for the write's `(config_name,
  scope_type)` — enforced both by the write gate (domain error) and by
  the composite FK. That entry references a registered `config_name`, so
  registration is guaranteed transitively; the fragment needs no direct
  FK to `app_config_definitions`. Updates and purges of an existing
  fragment need no gate: the FK guarantees the entry exists while the
  fragment does.
- A regular (non-admin) mutation is further restricted to the caller's
  own `user` row; admin mutations may target any scope (still gated by
  the allow-list) and are the only writes that may touch the allow-list
  and `app_config_definitions`.
- `app_config_definitions` purge **cascades down the whole subtree**: its
  allow-list entries are removed by the `config_name` FK (`ON DELETE
  CASCADE`), and their fragments cascade from those entries in turn — so
  retiring a config name clears its allow-list and fragments in one
  statement.
- `app_config_allow_list` purge **revokes the grant and drops its data**:
  the fragments at that `(config_name, scope_type)` are removed by the
  `ON DELETE CASCADE` FK, so a revoked value disappears from the merge
  in the same statement — no orphaned fragments to clean up separately.

<a id="write-model"></a>
### Write model

Two kinds of mutation:

- **Admin mutations** (admin-only) — `create` / `update` / `purge` a
  fragment at any scope whose `(config_name, scope_type)` is in the
  allow-list. The only mutations that may write another user's `user`
  row, and the only ones that may manage the allow-list and
  `app_config_definitions` themselves.
- **Regular mutations** (any authenticated user) — `create` / `update` /
  `purge` the caller's own `user` row, **only when** an allow-list row
  exists for `(config_name, user)`.

`create` errors if the natural key already exists; `update` errors if it
does not; `purge` removes the row (and thus its contribution to the
merge). A caller "clears" a config without deleting it by `update`-ing
with `{}`, which reads back as `null` (null projection, §3). `update`
replaces the stored JSON wholesale — no partial/deep update at the write
boundary.

**Overridability is a write-grant decision:**

- **Fixed** (user cannot change): no `(config_name, user)` row exists in
  the allow-list, so a regular `user`-scope write is rejected and the
  merged value is the admin's (`public` / `domain` fragments only).
- **Overridable**: the admin grants `(config_name, user)`. The admin
  sets the `domain` default; the user freely creates/updates/purges
  their own `user` fragment, which wins on merge (the `user` entry's
  default `rank` is the highest).
- **User-only**: the grant exists and no admin fragment is published.

To promote a fixed value to user-customizable, the admin adds a single
`(config_name, user)` grant — no data migration. To lock it back down,
the admin removes the grant: the cascade drops the existing `user`
fragments with it, so the admin value applies again immediately.

---

## 2. `rank` — merge priority

`rank` is the integer priority an **allow-list entry** carries; every
fragment written under the entry merges at that priority (low → high,
higher wins). It lives on the allow-list — not the fragment — because
merge order is admin policy: fragment writes are partly user-owned, and
a rank on the fragment would let a user re-order the merge by editing
their own row.

- **Scope-type defaults.** A new entry defaults its `rank` from its
  `scope_type`: `public` = 100, `domain` = 200, `user` = 300. The
  defaults order the scopes so a user's own fragment overrides the
  domain default, which overrides the public value; the 100 gap leaves
  room for custom placement in between.
- **Admin override.** The admin may set `rank` explicitly when creating
  the entry — e.g. a `domain` entry ranked above `user` yields a
  domain-enforced value that user fragments cannot beat even where a
  user grant exists.
- **Per-caller totality.** For one caller and one `config_name`, at most
  one fragment applies per scope type (§3), so the entry ranks totally
  order every merge input.

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

For a user resolving `config_name`, the **applicable** fragments are
those whose scope applies to them:

- every `public` fragment (`scope_id = "public"`),
- the user's `domain` fragment (`scope_id = the user's domain`),
- the user's `user` fragment (`scope_id = the user's id`).

A single `app_config_fragments` query selects exactly those rows (the
user's domain is known from the session — no permission check), joins
each to its allow-list entry for the `rank`, orders by it (low → high),
and deep-merges: nested objects recurse, scalars and lists are
wholesale-replaced, and the higher `rank` wins on conflict.

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

- **Before login**, the WebUI fetches `public` configs (theme,
  branding) anonymously so the shell can render.
- **After login**, it reads its merged `AppConfig`s (`theme`, `menu`,
  `preferences`, …) — a fast, join-free merge of every public/domain/user
  fragment that exists for the caller — and persists user changes through
  a regular mutation on its own `user` fragment (allowed only where the
  admin has granted it), which returns the recomputed merged view.

---

## 5. User scenarios

- **Register a config name and open its scopes** — admin creates the
  `app_config_definitions` row for `theme`, then the `app_config_allow_list`
  rows for every scope it will use — e.g. `(theme, domain)` for the admin
  default, plus `(theme, user)` if users may customize it. A fragment can
  be written only after its scope's row exists.
- **Pre-login public config** — anonymous read of `public` `theme`.
- **Bootstrap after login** — read merged `AppConfig`s in one round of
  queries; each is a rank merge over the fragments joined to their
  allow-list entries, no per-scope stitching.
- **User edits a config** — a regular create/update/purge on the
  caller's own `user` row (only where the grant exists); the response is
  the recomputed merge.
- **Admin publishes a fixed domain value** — add the `(config_name,
  domain)` allow-list row, write the `domain` fragment, and add no
  `(config_name, user)` row; users cannot override it.
- **Admin makes a value user-overridable** — add the `(config_name,
  user)` grant; users then create/update/purge their own copy. No data
  migration.
- **Admin locks a value back down** — remove the `(config_name, user)`
  grant; the cascade drops the existing `user` fragments with it.
- **Admin reorders contributions** — set the allow-list entries'
  `rank`s (per `(config_name, scope_type)`, not per fragment).
- **Admin retires a config name** — purge the `app_config_definitions`
  row; the allow-list entries and their fragments cascade with it, so no
  prior cleanup is needed.
- **Admin audit** — cross-scope fragment search and cross-user merged
  search for support.
