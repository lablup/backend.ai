---
name: notification-service-shapes
type: decision-table
description: notification knowledge: why channels and rules are two entity types in one package, which three operations keep a service and why, what a rule read returns
scope: src/ai/backend/manager/services/notification
keywords: [CreateChannelAction, CreateRuleAction, ValidateChannelAction, ValidateRuleAction, ProcessNotificationAction, MatchingNotificationRuleData, global_create_ops, global_scope, NOTIFICATION_CHANNEL_ENTITY_TYPE, NOTIFICATION_RULE_ENTITY_TYPE]
sources:
  - src/ai/backend/manager/services/notification
  - src/ai/backend/manager/api/rest/v2/notification
generated:
  by: claude-code/opus-5
  at: 2026-08-14
status: stable
---

# Notification service — Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`.

A channel is somewhere a message can be sent; a rule says which events go to
which channel. They live in one package because a rule is meaningless without
the channel it names, and both are system-wide configuration rather than
anything a user owns.

## The processor fields

`backend.ai mgr ops list --concern notification_center` prints the wired list. Their output answers the entity type, shape,
operation, gate and backing.

Two `ProcessorGroup`s are wired, one per entity type. All thirteen REST routes
declare `superadmin_required`, so the global gate matches the surface.

## Global is the right shape here

- Neither table joins a scope: a channel is an endpoint the system owns,
  and a rule is a routing entry against it.
- Nothing is granted per channel or per rule, so there is no per-entity
  permission to express and nothing to share.

## Three operations keep a service because they leave the database

- `validate_channel` sends a real test message through the channel.
- `validate_rule` renders the rule's template against test data.
- `process_notification` matches an event against the rules and prepares the
  messages.
- None of the three is a write the ops layer could execute from a spec, which is
  the criterion for keeping a service method at all.

## A rule read answers with its channel

- The matching read returns `MatchingNotificationRuleData`, pairing each rule
  with the channel it names, because a caller that got rules alone would have to
  read the channels back one at a time.
- Callers that hold a rule and want its channel separately read it by id; the
  pair is for the send path.
