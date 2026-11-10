---
name: notification-adapter-scenarios
type: reference
description: what the notification adapter guarantees; channels and rules are global rows only the superadmin reaches, a rule names its channel by id with nothing holding the two together, and the two validations send through the channel or render the template
scope: src/ai/backend/manager/api/adapters/notification
keywords: [notification, channel, rule, scenario, adapter, superadmin, monitor, webhook, email, validate]
generated:
  by: claude-code/opus-5
  at: 2026-09-17
status: draft
---
# notification adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

This adapter handles two entities, `notification_channel` and `notification_rule`. Both are created outside every scope. Create and search check whether the calling user is superadmin (a monitor passes the search too), and the get, update, delete and validate by id check the permission granted on that row, but there is no way to receive that permission. Every call therefore passes only for superadmin, with different rejection reasons.

A rule refers to its channel by the `channel_id` value only. No foreign key joins the two tables, so a rule can be created with a missing channel id, and deleting the channel a rule refers to keeps the rule.

The caller gives a `created_by` value separately from the request. The `created_by` value of the created row is that value.

## Create a channel

When `spec` carries both `webhook` and `email`, the adapter uses `webhook`. The adapter reads `spec` first and stores the `channel_type` value separately. A request where the two disagree writes the row, and the spec format validation rejects it where the row is read back to build the response. The write is in the same transaction and is rolled back.

A request whose name is empty or exceeds the length limit is not a scenario. The request type already rejects it.

"a monitor creates" is paired with "a monitor searches" in the search section. The same user can search and cannot create.

## Get a channel

A monitor passes the search but cannot get one by id. The superadmin check of the search passes a monitor for reads, while the get by id is a permission check and a monitor has no granted permission either.

A non-existent id is rejected for different reasons for superadmin and for other users. The permission check runs first and a missing row has no granted permission either, so only superadmin, who passes that check, is rejected for a missing target. The missing id scenarios in the sections below are all the same.

In a get of several at once, a missing id comes as an empty entry and an id without permission as an entry carrying the rejection. The two are distinguished, so the adapter does not tell a user without permission that the row is missing.

## Search channels

## Update a channel

The `channel_type` value cannot be changed. Only `spec` can be changed, so giving an `email` `spec` to a `webhook` channel is rejected through the same path as the disagreeing request in the create section.

## Delete a channel

Delete is a purge that removes the row. There is no delete that keeps the row. Deleting the channel a rule refers to is not blocked because no foreign key joins the two tables.

Update and purge default to the names without prefix (`updateNotificationChannel`, `purgeNotificationChannel`) and pass the permission check only. The old names (`adminUpdateNotificationChannel`, `adminDeleteNotificationChannel`, `deleteNotificationChannel`) and the old REST delete path that carries the id in the body are deprecated aliases leading to the same call, and still pass the superadmin check. Rules are the same.

## Bulk update channels

## Bulk purge channels

A bulk operation does not reject the whole call. Processed channels go into the processed list, and failures carry the id and the reason in the failure list. Rules are the same.

## Validate a channel

Validation actually sends a test message through that channel. The scenario runs with the sending side replaced by a mock that only records. A rejection for a failed send cannot be produced by the mock, so it is not a scenario.

## Create a rule

The `message_template` value is not checked when created. A broken template is stored too and rejected only at validation.

## Get a rule

## Search rules

## Update a rule

The `rule_type` and `channel_id` values cannot be changed. The request type has no field for them.

## Delete a rule

## Bulk update rules

## Bulk purge rules

## Validate a rule

Validation reads the rule and its channel, checks the test data in the format of the `rule_type`, then renders the template and sends it through the channel. The scenario replaces only the sending side with a mock. A rejection for test data that does not match the format and for a template that cannot be rendered is not a scenario. The adapter and the database do not change the result, and the service unit tests check it.
