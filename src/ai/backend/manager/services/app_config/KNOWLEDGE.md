---
name: app-config-service-shapes
type: decision-table
description: app config as a value computed from the definition/allow-list/fragment tables with no row of its own, how the allow-list decides which scopes may fill a config_name and which of domain or user overrides the other, why an anonymous read yields public values, why both reads are scope operations
scope: src/ai/backend/manager/services/app_config
keywords: [SearchAppConfigsAction, AnonymousSearchAppConfigsAction, VisibleAppConfigFragmentOperationScope, PublicAppConfigFragmentOperationScope, app_config_definitions, app_config_allow_list, app_config_fragments]
sources:
  - src/ai/backend/manager/services/app_config
  - src/ai/backend/manager/repositories/app_config_fragment
  - src/ai/backend/manager/models/app_config_allow_list
  - src/ai/backend/manager/models/app_config_definition
generated:
  by: claude-code/opus-5
  at: 2026-08-18
status: stable
---

# App config service — Knowledge

> Rules: `../AGENTS.md`. Action shapes and the public gate: `../../actions/KNOWLEDGE.md`.

An app config is not stored. It is built on each read by merging the pieces held across
three tables, so no row corresponds to the value.

## An app config is built from these

| Table | What it settles | Who writes it |
|---|---|---|
| `app_config_definitions` | which `config_name`s exist | admin |
| `app_config_allow_list` | which scopes may fill a `config_name`, and the `rank` that orders the merge | admin |
| `app_config_fragments` | the value held at an allowed scope | that scope's owner |

- A read deep-merges the fragments of the allowed scopes in ascending `rank`.
- The action's `entity_type()` is `app_config` while the table it reads is
  `app_config_fragments`, and the result's `entity_ids()` is an empty tuple.

## The design and the values are separate

- `app_config_definitions` and `app_config_allow_list` are where a superadmin designs an
  app config; `app_config_fragments` holds the values written under that design.
- The design differs per `config_name`: one may take values from admins alone, another
  may be opened down to the user.
- Whether domain overrides user or the other way round is settled by that
  `config_name`'s `rank` too. The higher rank wins, and a value's owner cannot raise the
  priority of their own piece.

## Both reads are scope operations

Both carry the entity type `app_config`.

배선된 목록은 `backend.ai mgr ops list --concern app_config`이 낸다.

- Several names arrive at once, which is what makes it `SEARCH` rather than `GET`.
- The user-scope read's three query conditions (public, that user's domain, that user)
  are bound together as one `VisibleAppConfigFragmentOperationScope`. Left for the call
  site to assemble, a merge could be read with one of the three missing.
- The adapter fills the user and the domain from the session, so a caller cannot name
  someone else's.

## An anonymous read yields the public values

- An anonymous scope names no principal, so there is no scope to answer for access with.
  Its query axis is `PublicAppConfigFragmentOperationScope` alone, so only public
  fragments merge.
- `public` has no owner and therefore no `scope_id`. It is expressible on the query axis,
  which needs a condition and nothing else, but there is nothing to name where access is
  answered for.
