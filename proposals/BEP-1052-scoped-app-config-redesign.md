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
`(scope_type, scope_id, name)` — so access control and merge semantics
live at the scope level, not at the field level. A single scope (e.g. one
domain, one user) can hold **multiple named configuration documents**
(`theme`, `menu`, `preferences`, …), each managed independently.

A user's effective configuration for a given `name` is the **deep
merge of the fragments that apply to them**, combined in **`rank`
order**. Every fragment carries its
own merge priority, and which fragments participate is decided by scope
matching alone.

A user can **read and modify** their app config, but **only an admin can
create** fragments (in any scope). This is what lets an admin decide
whether a domain value is fixed or user-overridable — see [Write model](#write-model).

## User Stories

Three scopes cover the use cases (plus `public` for the pre-login shell):

| Use case                                         | Scope(s)          | Who writes                                  |
|--------------------------------------------------|-------------------|---------------------------------------------|
| Pre-login values (theme, branding)               | `public`          | Admin                                       |
| Domain-wide value the user **cannot** change     | `domain`          | Admin                                       |
| Per-domain **default** the user **can** override | `domain` + `user` | Admin sets the default + seeds the user copy; user modifies their copy |
| User value with **no** default                   | `user`            | Admin seeds; user modifies                  |

- Admins set values that apply across a domain; a domain-fixed value
  cannot be changed by users.
- Some domain settings must be readable **before login** (theme).
- Admins seed the initial value of a user's personal settings; the user
  then edits their own copy.
- Users persist their own settings on the server (language, recently used
  sessions, visible/ordered table columns, experimental-feature toggles).
- The same scope may publish several independently-managed documents
  loaded by different parts of the WebUI.

## Design Principles

- **Schema-less JSON.** The backend is pure storage; the structure and
  meaning of each document are owned by the frontend.
- **Scope = entity.** Access control is expressed at the scope level, not
  per field. Three scopes: `public` (anonymous read / admin write),
  `domain` (same-domain read / admin write), `user` (owner+admin read /
  owner-modify + admin write).
- **Named documents within a scope.** Each row is identified by the
  natural key `(scope_type, scope_id, name)`. Clients address documents
  explicitly by name — no hierarchical fall-through lookup.
- **Merge by `rank`.** A fragment's `rank` is its merge priority within a
  `name`. Every fragment whose scope applies to the user participates;
  their order is decided by `rank`.
- **Users read and modify; admins create.** All `create` (including
  `user` scope) is admin-only; the self-service path is **update-only**.
  See [Write model](#write-model).
- **Single source-of-truth table.** One `app_config_fragments` table
  holds every scope; only the exposure layer is split.

---

## 1. Data model

A single `app_config_fragments` table, keyed by the natural composite
`(scope_type, scope_id, name)` (unique). Columns of note:

- `scope_type` — `public | domain | user`.
- `scope_id` — the scope's identifier (see convention below).
- `name` — the document name (unique within the scope).
- `rank` — integer merge priority within a `name` (low → high; higher
  wins). Assigned by next-value on insert (see §2).
- `config` — schema-less JSON payload (PostgreSQL `jsonb`).
- `created_at` / `updated_at`.

A composite index on `(name, rank)` backs the "fetch a name's fragments
in merge order" access pattern.

### Scope-ID convention

| `scope_type` | `scope_id`              | Meaning of `config`              |
|--------------|-------------------------|----------------------------------|
| `public`     | literal `"public"`      | pre-login value of the document  |
| `domain`     | `domain_name`           | the domain's value / default     |
| `user`       | `user_id` (UUID string) | the user's own value             |

A fragment can be created in any allowed scope for any `name` — no
pre-registration step is required. The merge (§3) always resolves from
whatever fragments exist.

<a id="write-model"></a>
### Write model

Two write paths:

- **Admin path** — `create` / `update` / `purge`, **any scope**. This is
  the *only* way a row comes into existence, including `user`-scope rows.
- **Self-service (`my`) path** — **`update` only**, on the caller's own
  `user` rows. No `create`, no `purge`.

`create` errors if the natural key already exists; `update` errors if it
does not; `purge` (admin-only) is the single deletion verb, for cleaning
up misconfigured rows. A caller "clears" a document by `update`-ing it
with `{}`, which reads back as `null` (null projection, §3). `update`
replaces the stored JSON wholesale — no partial/deep update at the write
boundary.

**Why users cannot create.** A user fragment overrides the domain value
(higher `rank`). If users could freely create their own fragment, they
could shadow a domain value the admin meant to be fixed. By restricting
users to *modifying existing* rows, the admin controls overridability:

- **Fixed** (user cannot change): admin creates only a `domain` fragment.
  No `user` fragment exists and the user cannot create one, so the merged
  value is the domain value.
- **Overridable**: admin creates the `domain` default **and seeds a
  `user` fragment** (at a higher `rank`). The user then `update`s that
  seeded fragment to override.
- **User-only**: admin seeds a `user` fragment with no `domain` default;
  the user `update`s it.

---

## 2. `rank` — merge priority

`rank` orders the fragments that share a `name` when they are merged:
each fragment carries an integer priority, and the merge applies them in
that order.

- **Assignment.** On create, a fragment gets the **next value** —
  `MAX(rank) + gap` among existing fragments of the same `name` —
  computed race-free inside the write transaction. This mirrors how
  `DeploymentRevisionPreset` assigns its rank. Insertion order thus
  determines priority by default; admins re-order by setting `rank`
  explicitly or via `update`. (Seeding the `domain` default before the
  `user` copy naturally gives the user copy the higher rank.)
- **Gaps.** Ranks are spaced (e.g. steps of 100) so a fragment can be
  inserted between two existing ones without renumbering.
- **No tier defaults.** Priority is not derived from `scope_type`; a
  `user` fragment does not *automatically* outrank a `domain` fragment —
  it outranks because it is created later (higher next-value rank).

---

## 3. `AppConfig` — the merged view

Two read shapes exist:

- **`AppConfigFragment`** — one raw row, regardless of scope. Carries
  `scopeType`, `scopeId`, `name`, `rank`, and `config`. Callers
  disambiguate scope by reading `scopeType` (no per-scope wrapper types).
- **`AppConfig`** — the merged per-user view for a `name`: the ordered
  contributing `fragments` plus the deep-merged `config`.

### How a merge is resolved

For a user resolving `name`, the **applicable** fragments are those
whose scope applies to them:

- every `public` fragment (`scope_id = "public"`),
- the user's `domain` fragment (`scope_id = the user's domain`),
- the user's `user` fragment (`scope_id = the user's id`).

Those fragments are ordered by `rank` (low → high) and deep-merged: nested
objects recurse, scalars and lists are wholesale-replaced, and the higher
`rank` wins on conflict. The whole set is gathered in a single SQL query
(scope matching expressed as a CASE over the user's domain/id); the
chain is **not** pre-computed in service code.

### Null projection

When every contributing fragment is empty, the merged `config` projects
to `null` (never a bare `{}`), so clients can fall back to built-in
defaults. Each raw fragment's `config` follows the same rule.

### Read variants

- **Single** — resolve one `(user, name)` to its `AppConfig`.
- **Search (self)** — paginate the user's own `AppConfig`s, grouped by
  `(user_id, name)`; each name's merge is evaluated independently in SQL.
- **Search (admin, cross-user)** — the same query joined against `users`
  to resolve any user's `AppConfig` for audit / support; scoped by the
  search filter and gated admin-only at the service layer.

---

## 4. Client integration (WebUI)

- **Before login**, the WebUI fetches `public` documents (theme,
  branding) anonymously so the shell can render.
- **After login**, it reads its merged `AppConfig`s (`theme`, `menu`,
  `preferences`, …) — already combining public + domain + user fragments
  in `rank` order — and persists user changes through the `my`
  **update**, which returns the recomputed merged view. (A user only sees
  an editable value where the admin has seeded a `user` fragment.)

---

## 5. User scenarios

- **Pre-login public config** — anonymous read of `public` `theme`.
- **Bootstrap after login** — read merged `AppConfig`s in one round of
  queries; no per-scope stitching on the client.
- **User edits a document** — `my` update on the caller's seeded
  `user` row; the response is the recomputed merge.
- **Admin publishes a fixed domain value** — admin create/update a
  `domain` (or `public`) fragment; no `user` fragments seeded, so users
  cannot override it.
- **Admin makes a value user-overridable** — admin keeps the `domain`
  default and seeds each user a `user` fragment (higher `rank`); users
  then edit their own copy.
- **Promote fixed → user-customizable** — no schema change: the admin
  seeds the missing `user` fragments; users can now modify them.
- **Admin reorders contributions** — adjust fragment `rank`s (or insert
  one in a gap).
- **Admin audit** — cross-scope fragment search and cross-user merged
  search for support.

---

## 6. Future considerations

- Automatic seeding of `user` fragments for overridable documents (e.g.
  on first read or at user creation) to avoid per-user admin seeding.
