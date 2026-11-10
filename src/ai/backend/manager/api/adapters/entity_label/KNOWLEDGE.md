---
name: entity-label-adapter-scenarios
type: reference
description: what the entity label adapter guarantees; every call is authorized by the labeled entity, the single writes reject as a whole, the two bulk writes answer per entity or per label, and the reads are rejected whole when one specified entity is unreadable
scope: src/ai/backend/manager/api/adapters/entity_label
keywords: [entity label, scenario, adapter, upsert, purge, partial bulk upsert, partial bulk purge, search, owner lookup]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
updated:
  by: claude-code/opus-5.5
  at: 2026-10-16
status: draft
---
# entity_label adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A label is one `key=value` pair attached to any entity. A label holds no permission of its own, and every call answers under the permission of the entity the label is attached to. A write uses that entity's update permission and a read its get permission. Superadmin passes every check.

There are six calls: set one, set several, delete one, delete several, search the labels of specified entities, and search the labels of one entity already held. A single write answers whole or is rejected whole, and a bulk write answers per entity or per label.

Set several and delete several are called by the plural-named GQL mutation and the REST path starting with `partial-bulk-`. The singular-named mutation and the `bulk-` path are deprecated and lead to the same call.

Only entity types handled by the connection and call path can be specified. A request carrying a type the path does not handle is rejected whole as a bad request in every call. A bulk write is no exception, because that is a fault of the request itself, not the result of one entity.

## Set one

The call does not check whether the entity exists. A label row does not refer to the entity row by a foreign key, so a call that passes the permission check writes a label even for a missing id. The call where superadmin attaches a label to a missing id succeeds for that reason. A user who is not superadmin cannot be granted a permission on a missing entity and is rejected for insufficient permission.

A request whose key or value is empty or exceeds the length limit is not a scenario. The request type already rejects it, so the adapter does not guarantee the rejection.

## Set several

One request carries several entities and several keys. The response is one entry per entity. The keys attached to one entity are written together or rejected together. The failure list is per request item. For each key that was to be attached to a rejected entity, one entry carries the entity, the key and the reason. The call itself is not rejected.

The reason in the failure list is a string, and a string may change. The scenario checks only that a reason is present.

## Delete one

A label is specified by its own id. The adapter reads the row first to learn which entity answers, and that read requires the entity's get permission. A missing id and the label of an entity without get permission are rejected for the same reason, so the response does not reveal whether an id exists. Superadmin does not pass through this merge, so a missing id is rejected for a missing target.

## Delete several

Several label IDs are specified at once. The response is one entry per label. The entities are read at once and the update permission is required per entity. The labels of rejected entities and missing ids enter the failure list with a reason, and the rest enter the success list separated from the rejected ones. The call itself is not rejected.

When every specified ID is missing, the lower layer rejects the call whole because it has no entity to answer for. The adapter turns that back into one failure entry per id, so the caller reads every case the same way. The scenario "every id is missing" proves it.

## Search

The labels of specified entities are read as one page. The adapter requires the get permission per entity, and one rejection rejects the whole read. The read succeeds whole or fails whole.

The call that reads the labels of one entity already held is the same read called with one entity. It differs only in that the node specifies itself instead of specifying the entity again. The scenario is the one-entity row of the search section, so it is not described as a separate scenario.
