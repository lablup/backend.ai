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

A reader's effective configuration for a given `name` is the **deep
merge of the fragments that apply to them**, combined in **`rank`
order**. There is no separate policy object: every fragment carries its
own merge priority, and which fragments participate is decided by scope
matching alone.

## User Stories

| Story                                          | Scope                  | Read                          | Write       |
|------------------------------------------------|------------------------|-------------------------------|-------------|
| Theme / branding (must work before login)      | `public`               | Anyone                        | Admin       |
| UI hide/show, menu config                      | `domain`               | Logged-in users (same domain) | Admin       |
| Per-user preference defaults (per-domain)      | `domain_user_defaults` | Logged-in users (same domain) | Admin       |
| Per-user personal settings                     | `user`                 | Owner / Admin                 | Owner / Admin |

- Admins set values that apply across a domain and that users cannot
  override (theme, menus, hidden UI elements).
- Some domain settings must be readable **before login** (theme).
- Admins seed the **initial values** of a user's personal settings on a
  per-domain basis (matching today's `extraConfig` behavior).
- Users persist their own settings on the server (language, recently used
  sessions, visible/ordered table columns, experimental-feature toggles).
- The same scope may publish several independently-managed documents
  loaded by different parts of the WebUI.

> `domain` vs `domain_user_defaults`: both are admin-write and
> domain-readable with identical row-level rules. The split is an
> organizing convention — `domain` for values the domain owns outright,
> `domain_user_defaults` for values positioned as per-user seeds the user
> can override. Both contribute to a merge whenever a fragment exists for
> the reader; their relative weight is expressed through `rank`, not a
> separate allow-list.

## Design Principles

- **Schema-less JSON.** The backend is pure storage; the structure and
  meaning of each document are owned by the frontend.
- **Scope = entity.** Access control is expressed at the scope level, not
  per field: `public` (anonymous read / admin write), `domain` and
  `domain_user_defaults` (same-domain read / admin write), `user`
  (owner+admin read / owner-self+admin write).
- **Named documents within a scope.** Each row is identified by the
  natural key `(scope_type, scope_id, name)`. Clients address documents
  explicitly by name — no hierarchical fall-through lookup.
- **Merge by `rank`, not by policy.** A fragment's `rank` is its merge
  priority within a `name`. Participation in a reader's merge is decided
  by scope matching; ordering is decided by `rank`. There is no
  `AppConfigPolicy` table, no required-policy invariant, and no per-name
  allow-list of scopes.
- **Bulk-only writes.** No single-item mutations: callers pass a list
  (even of length one) and get a partial-success payload. Each item runs
  in its own transaction, so one failure does not abort the rest. Verbs:
  `create` (strict insert), `update` (wholesale JSON replacement),
  `purge` (admin-only cleanup). Rows are addressed by natural key, never
  by Relay id; the self-service path injects `scope`/`scopeId` server-side.
- **Single source-of-truth table.** One `app_config_fragments` table
  holds every scope; only the exposure layer is split.
- **Relay conventions.** Node interface, Connection/Edge, Input/Payload.

---

## 1. Data model

A single `app_config_fragments` table, keyed by the natural composite
`(scope_type, scope_id, name)` (unique). Columns of note:

- `scope_type` — `public | domain | domain_user_defaults | user`.
- `scope_id` — the scope's identifier (see convention below).
- `name` — the document name (unique within the scope).
- `rank` — integer merge priority within a `name` (low → high; higher
  wins). Assigned by next-value on insert (see §2).
- `config` — schema-less JSON payload (PostgreSQL `jsonb`).
- `created_at` / `updated_at`.

A composite index on `(name, rank)` backs the "fetch a name's fragments
in merge order" access pattern.

### Scope-ID convention

| `scope_type`           | `scope_id`              | Meaning of `config`                        |
|------------------------|-------------------------|--------------------------------------------|
| `public`               | literal `"public"`      | pre-login value of the document            |
| `domain`               | `domain_name`           | the domain's own value                     |
| `domain_user_defaults` | `domain_name`           | per-user seed for users in that domain     |
| `user`                 | `user_id` (UUID string) | the user's own value                       |

### Write semantics

- `create` errors if the natural key already exists; `update` errors if
  it does not; `purge` (admin-only) is the single deletion verb, for
  cleaning up misconfigured rows.
- Otherwise rows persist: a caller "clears" a document by `update`-ing it
  with `{}`, which reads back as `null` (null projection, §3).
- No partial update / deep-merge / key-level removal / upsert at the
  write boundary — `update` replaces the stored JSON wholesale.

There is **no policy table and no FK**: a fragment can be created in any
allowed scope for any `name` without a pre-registered policy. The merge
(§3) always resolves from whatever fragments exist.

---

## 2. `rank` — merge priority

`rank` orders the fragments that share a `name` when they are merged.
It replaces the earlier `AppConfigPolicy.scope_sources` chain: instead of
an admin-curated, per-name ordered list of scopes, each fragment simply
carries an integer priority.

- **Assignment.** On create, a fragment gets the **next value** —
  `MAX(rank) + gap` among existing fragments of the same `name` —
  computed race-free inside the write transaction. This mirrors how
  `DeploymentRevisionPreset` assigns its rank. Insertion order thus
  determines priority by default; admins re-order by setting `rank`
  explicitly or via `update`.
- **Gaps.** Ranks are spaced (e.g. steps of 100) so a fragment can be
  inserted between two existing ones without renumbering.
- **No tier defaults.** Priority is not derived from `scope_type`; a
  `USER` fragment does not automatically outrank a `DOMAIN` fragment. The
  relative weight is whatever `rank` was assigned. (This is a deliberate
  change from an earlier draft that hard-coded per-scope tiers.)

---

## 3. `AppConfig` — the merged view

Two read shapes exist:

- **`AppConfigFragment`** — one raw row, regardless of scope. Carries
  `scopeType`, `scopeId`, `name`, `rank`, and `config`. Callers
  disambiguate scope by reading `scopeType` (no per-scope wrapper types).
- **`AppConfig`** — the merged per-user view for a `name`: the ordered
  contributing `fragments` plus the deep-merged `config`.

### How a merge is resolved

For a reader resolving `name`, the **applicable** fragments are those
whose scope applies to them:

- every `public` fragment (`scope_id = "public"`),
- the reader's `domain` / `domain_user_defaults` fragments
  (`scope_id = the reader's domain`),
- the reader's `user` fragment (`scope_id = the reader's id`).

Those fragments are ordered by `rank` (low → high) and deep-merged: nested
objects recurse, scalars and lists are wholesale-replaced, and the higher
`rank` wins on conflict. The whole set is gathered in a single SQL query
(scope matching expressed as a CASE over the reader's domain/id); the
chain is **not** pre-computed in service code.

### Null projection

When every contributing fragment is empty, the merged `config` projects
to `null` (never a bare `{}`), so clients can fall back to built-in
defaults. Each raw fragment's `config` follows the same rule.

### Read variants

- **Single** — resolve one `(reader, name)` to its `AppConfig`.
- **Search (self)** — paginate the reader's own `AppConfig`s, grouped by
  `(user_id, name)`; each name's merge is evaluated independently in SQL.
- **Search (admin, cross-user)** — the same query joined against `users`
  to resolve any user's `AppConfig` for audit / support; scoped by the
  search filter and gated admin-only at the service layer.

---

## 4. Exposure — GraphQL

Two GQL types only: `AppConfigFragment` (raw row, any scope) and
`AppConfig` (merged per-user view, implementing `Node`). No per-scope
wrapper types.

**Queries**

- `publicAppConfigFragments` — public documents, no auth.
- Scoped fragment reads — a domain's or a user's fragments, gated to
  same-domain users / the owner (admin always).
- `adminAppConfigFragments` — cross-scope admin search.
- Merged view — the caller's own `AppConfig`s, and an admin cross-user
  variant for any user.

**Mutations** (all bulk-only, partial-success):

- **Admin path** — `create` / `update` / `purge` across any scope. Items
  carry the full `(scopeType, scopeId, name)` key, so scopes may be mixed
  in one call.
- **Self-service (`my`) path** — `create` / `update` on the caller's own
  `USER` rows; `scope = USER` and `scopeId = current_user` are injected
  server-side. Responses return the recomputed merged `AppConfig`. No
  purge (cleanup is admin-only).

**Permission matrix**

| Operation                                | Anonymous | User             | Admin |
|------------------------------------------|-----------|------------------|-------|
| `publicAppConfigFragments`               | ✅        | ✅               | ✅    |
| merged `AppConfig` (own)                 | ❌        | ✅ (self)        | ✅    |
| domain fragments                         | ❌        | ✅ (same domain) | ✅    |
| user fragments                           | ❌        | ✅ (self)        | ✅    |
| `adminAppConfigFragments` / admin merged | ❌        | ❌               | ✅    |
| admin bulk write (any scope)             | ❌        | ❌               | ✅    |
| `my` bulk write (own USER rows)          | ❌        | ✅ (self)        | ✅    |

Admins acting on another user's `USER` row use the admin path with an
explicit key — the `my` path can only target the caller.

---

## 5. Exposure — REST v2

REST mirrors the GraphQL surface under two prefix trees:

- `/v2/app-config-fragments/…` — raw fragment operations (admin CRUD,
  cross-scope and per-scope search, single reads, `my` writes).
- `/v2/app-config/…` — the **merged `AppConfig` view** (read-only; writes
  go through the fragment prefix).

Conventions: lists are `POST …/search` with a typed body (filter + order
+ `limit`/`offset`, cursor for admin cross-scope) — no `GET` list
endpoints, no unbounded pages. Single-resource reads stay `GET …/{name}`.
Bulk writes are `POST …/bulk-create | bulk-update | bulk-purge`. Bodies
are the snake_case projection of the GraphQL inputs/payloads.

---

## 6. Caching

The merged-view read path is fronted by a Valkey cache keyed per
`(user, name)`. Writes invalidate the affected scope so stale merges are
not served; cache failures fall through to the database transparently
(never break a request). The cache stores the merged `config`; raw
per-scope reads are uncached.

---

## 7. Client integration (WebUI)

- **Before login**, the WebUI fetches `public` documents (theme,
  branding) anonymously so the shell can render.
- **After login**, it reads its merged `AppConfig`s (`theme`, `menu`,
  `preferences`, …) — already combining public + domain + user fragments
  in `rank` order — and persists user changes through the `my` bulk
  writes, which return the recomputed merged view.

---

## 8. User scenarios

- **Pre-login public config** — anonymous read of `public` `theme`.
- **Bootstrap after login** — read merged `AppConfig`s in one round of
  queries; no per-scope stitching on the client.
- **User saves a document** — `my` bulk update on the caller's `USER`
  row; the response is the recomputed merge.
- **Admin publishes a domain document** — admin bulk create/update a
  `domain` (or `public`) fragment.
- **Admin seeds per-user defaults** — admin bulk create a
  `domain_user_defaults` fragment; it merges under each user's own `user`
  fragment by `rank`.
- **Promote admin-only → user-customizable** — no schema change: the user
  adds a higher-`rank` `USER` fragment that overrides the admin value.
- **Admin reorders contributions** — adjust fragment `rank`s (or insert
  one in a gap) instead of editing a policy's scope list.
- **Admin audit** — cross-scope fragment search and cross-user merged
  search for support.

---

## 9. Future considerations

- Optional read-through caching of the full merged view (fragments +
  config), not just `config`.
- Per-`name` schema/validation hooks if document shapes need server-side
  guarantees (currently fully frontend-owned).
- Bulk export/import of a scope's documents for environment promotion.
