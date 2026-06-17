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
named configuration documents** (`theme`, `menu`, `preferences`, …),
each managed independently.

**Reads are the hot path.** A user's effective configuration for a name
is the **deep merge of every fragment that applies to them**, taken
straight from `app_config_fragments` in `rank` order — a single-table
query with **no joins and no permission lookup**.

**Write authorization is set up ahead of time.** Every document name is
**explicitly registered** in `app_config_keys`, and `app_config_allow_list`
records — **pre-configured by admins** — enumerate the
`(config_name, scope_type)` pairs at which a fragment may be written.
**Every** fragment write, admin or user, requires a matching record;
admins additionally own the allow-list and the `app_config_keys` registry themselves
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
  meaning of each document are owned by the frontend.
- **Scope = entity.** Access control is expressed at the scope level,
  not per field. Three scopes: `public` (anonymous read / admin write),
  `domain` (same-domain read / admin write), `user` (owner+admin read /
  owner-modify + admin write).
- **Explicitly registered names.** Every document name lives in
  `app_config_keys`; fragments and allow-list entries reference it by
  foreign key. No fragment may exist for an unregistered name.
- **Reads are join-free and unconditional.** The merge reads
  `app_config_fragments` alone, ordering the existing fragments by
  `rank`. No allow-list or policy is consulted at read time — the hot
  path stays a single indexed scan.
- **Allow-list = the write gate for every fragment.** `app_config_allow_list`
  holds **one record per `(config_name, scope_type)`**; a fragment at
  that scope may be created/updated/purged **only if** the record exists
  — for the admin path and the self-service path alike. What sets admins
  apart is that they alone manage the allow-list (and the
  `app_config_keys` registry) itself. It governs **writes only** — never reads.
- **`rank` lives on the fragment.** A fragment's `rank` is its merge
  priority within a `config_name`; the read merge orders fragments by it.
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

### `app_config_fragments` — the per-scope values (read hot path)

Keyed by the natural composite `(scope_type, scope_id, config_name)`
(unique). The read merge scans this table alone. Columns of note:

- `scope_type` — `public | domain | user`.
- `scope_id` — the scope's identifier (see convention below).
- `config_name` — FK → `app_config_keys.config_name`.
- `config` — schema-less JSON payload.
- `rank` — integer merge priority within the `config_name` (low → high;
  higher wins). Assigned on create (see §2).
- `created_at` / `updated_at`.

### `app_config_allow_list` — the per-`(name, scope)` write gate

One row per `(config_name, scope_type)` (unique) — a normalized,
single-purpose table: **the write gate**. A fragment at `(config_name, scope_type)`
may be written only if its row exists here. Admins set these up in
advance.

- `config_name` — FK → `app_config_keys.config_name`.
- `scope_type` — a scope at which fragments may be written
  (`public | domain | user`). A user-overridable document carries a
  `(config_name, user)` row; an admin-only value carries
  `(config_name, domain)` and/or `(config_name, public)`.
- `created_at` / `updated_at`.

A row's **presence** is the entire signal — there is no `rank` here,
because the allow-list never participates in the merge. It gates **both**
write paths; admins, unlike users, may also create/update/purge the
allow-list rows themselves.

### Scope-ID convention

| `scope_type` | `scope_id`              | Meaning of `config`              |
|--------------|-------------------------|----------------------------------|
| `public`     | literal `"public"`      | pre-login value of the document  |
| `domain`     | `domain_id`             | the domain's value / default     |
| `user`       | `user_id` (UUID string) | the user's own value             |

### Integrity

- **Every** fragment write (admin or self-service) requires (a) a
  registered `config_name` (FK to `app_config_keys`) and (b) an
  `app_config_allow_list` row for the write's `(config_name,
  scope_type)`. The service layer rejects per-row when either is missing.
- The self-service path is further restricted to the caller's own `user`
  row; the admin path may target any scope (still gated by the
  allow-list) and is the only path that may write the allow-list and
  `app_config_keys`.
- `app_config_keys` purge is rejected while any fragment or allow-list
  entry still references the name (`ON DELETE NO ACTION`).
- `app_config_allow_list` purge **revokes future writes** at that
  `(config_name, scope_type)`. Because reads never consult the
  allow-list, **existing fragments are untouched and keep merging** — to
  actually drop a value, an admin purges the fragments themselves.

<a id="write-model"></a>
### Write model

Two write paths:

- **Admin path** — `create` / `update` / `purge` a fragment at any scope
  whose `(config_name, scope_type)` is in the allow-list. The only path
  that may write another user's `user` row, and the only path that may
  manage the allow-list and `app_config_keys` themselves.
- **Self-service (`my`) path** — `create` / `update` / `purge` on the
  caller's own `user` row, **only when** an allow-list row exists for
  `(config_name, user)`.

`create` errors if the natural key already exists; `update` errors if it
does not; `purge` removes the row (and thus its contribution to the
merge). A caller "clears" a document without deleting it by `update`-ing
with `{}`, which reads back as `null` (null projection, §3). `update`
replaces the stored JSON wholesale — no partial/deep update at the write
boundary.

**Overridability is a write-grant decision** — there is no admin-seeding
dance:

- **Fixed** (user cannot change): no `(config_name, user)` row exists in
  the allow-list. The `my` path is rejected, so the merged value is the
  admin's (`public` / `domain` fragments only).
- **Overridable**: the admin grants `(config_name, user)`. The admin
  sets the `domain` default; the user freely creates/updates/purges
  their own `user` fragment, which (higher `rank`) wins on merge.
- **User-only**: the grant exists and no admin fragment is published.

To promote a fixed value to user-customizable, the admin adds a single
`(config_name, user)` grant — no data migration. To lock it back down,
the admin removes the grant **and** purges any existing `user` fragments
(removing the grant alone only blocks new writes; reads still merge what
is already stored).

---

## 2. `rank` — merge priority

`rank` is the integer priority a **fragment** carries within a
`config_name`; the read merge applies fragments in `rank` order (low →
high, higher wins).

- **Assignment.** A new fragment is placed after the existing ones for
  the same name, so a later-created fragment outranks earlier ones by
  default. Admins re-order by setting `rank` explicitly. (Publishing the
  `domain` default before a user writes their own copy naturally gives
  the `user` fragment the higher rank, so the user value wins.)
- **No tier defaults.** Priority is the fragment's `rank`, not derived
  from `scope_type` — a `user` fragment outranks a `domain` fragment
  only because its `rank` is higher, not because `user` is "above"
  `domain`.

---

## 3. `AppConfig` — the merged view

Two read shapes exist:

- **`AppConfigFragment`** — one raw row, regardless of scope. Carries
  `scopeType`, `scopeId`, `configName`, `rank`, and `config`. Callers
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
user's domain is known from the session — **no join, no allow-list
lookup**), orders them by `rank` (low → high), and deep-merges: nested
objects recurse, scalars and lists are wholesale-replaced, and the
higher `rank` wins on conflict.

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
  `preferences`, …) — a fast, join-free merge of every public/domain/user
  fragment that exists for the caller — and persists user changes through
  the `my` path (allowed only where the admin has granted it), which
  returns the recomputed merged view.

---

## 5. User scenarios

- **Register a document name and open its scopes** — admin creates the
  `app_config_keys` row for `theme`, then the `app_config_allow_list`
  rows for every scope it will use — e.g. `(theme, domain)` for the admin
  default, plus `(theme, user)` if users may customize it. A fragment can
  be written only after its scope's row exists.
- **Pre-login public config** — anonymous read of `public` `theme`.
- **Bootstrap after login** — read merged `AppConfig`s in one round of
  queries; each is a single-table rank merge, no per-scope stitching.
- **User edits a document** — `my` create/update/purge on the caller's
  own `user` row (only where the grant exists); the response is the
  recomputed merge.
- **Admin publishes a fixed domain value** — add the `(config_name,
  domain)` allow-list row, write the `domain` fragment, and add no
  `(config_name, user)` row; users cannot override it.
- **Admin makes a value user-overridable** — add the `(config_name,
  user)` grant; users then create/update/purge their own copy. No data
  migration.
- **Admin locks a value back down** — remove the `(config_name, user)`
  grant **and** purge existing `user` fragments (the grant gates writes,
  not reads).
- **Admin reorders contributions** — adjust fragment `rank`s.
- **Admin retires a document name** — purge the fragments, then the
  allow-list entries, then the `app_config_keys` row (purge is rejected
  while references remain).
- **Admin audit** — cross-scope fragment search and cross-user merged
  search for support.
