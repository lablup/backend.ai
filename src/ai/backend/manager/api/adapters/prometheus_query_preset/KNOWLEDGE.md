---
name: prometheus-query-preset-adapter-scenarios
type: reference
description: what the prometheus query preset adapter guarantees; the catalog reads open to every authenticated caller, the superadmin role on create and preview, and the entity gate on execute, update and purge that no role reaches
scope: src/ai/backend/manager/api/adapters/prometheus_query_preset
keywords: [prometheus query preset, scenario, adapter, superadmin, public, template, time window, prometheus]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# prometheus_query_preset adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A `prometheus_query_preset` (preset below) stores a query template that reads metrics. A row belongs to both global and public. Getting and searching a stored preset checks READ in public: every account automatically receives the public membership role, so every signed-in user can see it. Create and preview check whether the caller is superadmin. The permission that update and delete need comes from global only, so only superadmin passes. Execute asks for the same permission as get. The point of this adapter is that the path that reads a stored preset differs from the path that queries Prometheus with that preset. A scenario that shares a preset into a scope is not in this document. It belongs to the sharing adapter document.

Execute and preview receive their response from Prometheus. The scenarios in the execute and preview sections run with a mock Prometheus. The mock server responds to every query with one sample and puts the received query into that sample value as it is. A scenario uses that value to check how the `time_window` value was reflected into the query. It responds to a range query in the range query response format and an instant query in the instant query response format, and rejects an empty query as the real Prometheus does. Create, get, search, several id get, update, delete, bulk update and bulk delete run with the database alone.

The whole metric search, the metric name list and the metric get of one user, which are the paths that read container metrics themselves, have no adapter and the legacy GraphQL calls the processor directly, so they are not in this document.

## Create

The renderer checks the template before storing, and a rejected template creates no row. That check is not a scenario. The adapter and the database do not change the result; the unit tests of the renderer cover each rejection case, and the unit tests of the service check that a rejected template is not stored. The template check of update and preview is the same.

The preset name has no unique constraint. "create again with the same name" checks it. The category name is the opposite.

A non-existent category is rejected by the reference constraint of the repository and is not converted to a domain error. The same scenario of update is the same.

A request whose name is only whitespace, a request with a negative `rank` value and a request with a malformed `time_window` value are not scenarios. The request type already rejects them, so the adapter does not guarantee them.

"a monitor role user creates" checks that the superadmin check allows a monitor for reads only. Its result is the opposite of "a monitor role user previews" in the preview section.

## Get

Get checks READ in public. So the requester of "a user who reads in public gets" is a user who received only that permission. The permission check runs first and a missing row has no granted permission either, so a non-existent id and an unreachable id are rejected for the same reason.

## Search

## Getting by several ids

This is the search called with an id condition, so its permission path is the same as the search. Only the rows the scope responds with come back, so a missing id becomes an empty entry.

## Update

The `filter_labels` and `group_labels` values are stored together in the one `options` column. A scenario checks that changing one does not delete the other.

The template is checked only when the request specifies a template, and a stored template is not validated again. The service unit tests check this too.

## Execute

Execute asks for the same permission as get. A user who can read in public can therefore execute too, and only a user without any permission is rejected. The requester of "a user without any permission executes" is a user who did not receive that permission.

The `time_window` value and the `time_range` value are different. The `time_window` value is a string that goes into a placeholder of the template, and the `time_range` value decides whether the query is an instant query or a range query. Both can be specified together and neither overrides the other.

Whether the `time_window` value comes from the request, the preset or the server default, and the check of the label allowance list of the `options` column, are not scenarios. Neither changes the result in the adapter or the database, and the service unit tests check them. The reason is the same as the template check in the create section.

The scenario where Prometheus rejects uses an empty query. A template with only label placeholders passes the renderer, but rendering it without labels makes an empty query, and Prometheus rejects an empty query as a syntax error.

A non-existent id is rejected for different reasons for superadmin and for other users. The permission check runs first and a missing row has no granted permission either, so only superadmin, who passes that check, sees "missing target". The "missing target" of execute comes from the service reading the preset directly and is not the same kind as the "missing target" of update and delete.

Execute propagates the Prometheus error as it is, and preview converts it to an evaluation failure before propagating. So "Prometheus rejects the query" in the execute and preview sections is rejected with different errors.

## Preview

Preview reads only the template from the request. It accepts neither labels nor a `time_window` value, so the query the mock server receives always has empty labels and the server default `time_window` value. The scenario does not check that no row is created. Preview does not pass through the write path of the repository.

Preview is the only read in this adapter that checks whether the caller is superadmin, so the scenario where a monitor role user succeeds is here only.

## Delete

This adapter has no delete that keeps the row. Deleting makes the row disappear, and there is no call that brings it back. The delete call runs purge. The old GraphQL mutation and REST path are deprecated and lead to the same call.

The auto-scaling rule of a deployment may reference a preset. Deleting the preset keeps that rule with `prometheus_query_preset_id` set to NULL. Preparing the rule requires creating the deployment too, so that scenario belongs in `../deployment/KNOWLEDGE.md` when the auto-scaling rules section appears there.

## Bulk update

The template check runs per entry. Only the entries caught by the check enter the failure list and the rest are updated.

## Bulk delete

A bulk operation does not reject the whole call. Processed presets go into the processed list, and failures are recorded in the failure list with the id and the reason.
