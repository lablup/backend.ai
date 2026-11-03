---
name: app-config-adapter-scenarios
type: reference
description: merged app config read contract, a value with no row of its own built by merging fragments in allow-list rank order, read at the caller's own scope or anonymously from the public fragments alone
scope: src/ai/backend/manager/api/adapters/app_config
keywords: [app config, scenario, adapter, merge, rank, anonymous, rbac]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# app_config adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

`app_config` has no row of its own. Each read builds the value by merging rows of `app_config_definitions`, `app_config_allow_list` and `app_config_fragments`, and no row corresponds to the value. `../../../services/app_config/KNOWLEDGE.md` settles the role of the three tables and the merge rules, so this document does not repeat them.

The adapter exposes two calls. `my_app_configs` reads with the session's user and domain and checks the read permission granted on that user's own scope. `public_app_configs` reads with no scope and runs no check. What protects this call is the read method itself, not a check: with no scope, only public `app_config_fragment` rows are merged.

With no row to create and read back, the success scenario takes another shape: an `app_config_definition`, an `app_config_allow_list` entry and a `fragment` are prepared beforehand, and the read returns the merge result. The response holds only the `config_name` field and the merged `config` field, with no id and no timestamp, and `config` is compared as a whole. There are no create, get or delete scenarios. The delete sections of the `app_config_fragment` and `app_config_allow_list` adapter documents cover how deleting a `fragment` or an `allow_list` entry changes the merge.

## Reading one's own config

The scenario that reverses `rank` values pins that the `allow_list` entry decides the merge order and the owner of the value cannot change it. The `rank` value is on the `allow_list` entry, not on the `fragment`.

How the values of two `fragment` rows combine (recursion into `dict` only, `list` and empty values replaced as a whole) is not a scenario. The adapter and the database do not change the result, and a service unit test checks it. Scenarios check only which `fragment` rows enter the merge and in what order.

A name with no `definition` receives the same response as a name with no `fragment`. This read never checks `definition`; it reads `fragment` only.

There is no scenario where a `fragment` of a scope without an `allow_list` entry enters the merge. Such a `fragment` cannot be used, and deleting the `allow_list` entry deletes the `fragment` with it, so the situation does not arise. The `app_config_fragment` document holds the scenario that writes a `fragment` in a scope with no `allow_list` entry, and the `app_config_allow_list` document the one where deleting the entry deletes the `fragment` too.

When two `allow_list` entries of the same name carry the same `rank` value, which `fragment` wins is not settled. Settle it before writing the scenario.

An empty `config_names` field is not a scenario. The request type already rejects it, so the adapter does not guarantee it.

## Reading public config

No check runs. Neither authentication nor permission is checked. Write calls cannot be connected to this path, so only the read is called without a check.

A name with no public `fragment` and a name with no `definition` receive the same response. This read therefore cannot tell which names are registered. That is the ground for the unchecked path exposing nothing, so the scenario of a name with no public `fragment` sits beside the scenario of a name with no `definition`.

The scenario of a signed-in user pins that this read uses no caller information at all. With permission, the user's own `fragment` is not merged; without permission, the user is not rejected.
