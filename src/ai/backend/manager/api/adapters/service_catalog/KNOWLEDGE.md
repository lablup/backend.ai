---
name: service-catalog-adapter-scenarios
type: reference
description: what the service catalog adapter guarantees; the single search behind the global role that the monitor role also passes, the status filter conditions it accepts, and the cursor fields it ignores
scope: src/ai/backend/manager/api/adapters/service_catalog
keywords: [service catalog, scenario, adapter, superadmin, monitor, search, endpoints]
generated:
  by: claude-code/opus-5
  at: 2026-09-17
updated:
  by: claude-code/opus-5.5
  at: 2026-10-07
status: draft
---
# service_catalog adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

The only call this adapter provides is the search (`admin_search`). A service registers a catalog row itself, and the event handler records it when the service sends the service catalog heartbeat; no call lets an administrator create, update or delete a row. The search needs a global role, and since it is a read operation, a user with the monitor role passes the permission check too.

The only write spec in src that creates a row is the upsert spec the registration handler writes, and that spec always records the status as healthy. The deregistration handler and the handler that marks a service with a broken service catalog heartbeat as unhealthy update the row directly without a spec. A service in the unhealthy or deregistered status is therefore created with a spec the scenario tree defines itself, written from the registration spec with only the status changed. A service in the healthy status is built with the src spec.

## Search

The status filter accepts the four conditions `equals`, `in`, `not_equals` and `not_in`, and one scenario per condition checks it by searching for services whose status is the same as the specified one/different from it/in the list/not in it. All four scenarios place one service per status and check that only the services in the specified status remain.

The request type has `first`, `after`, `last` and `before` fields, but this search reads only the page size (`limit`) and `offset` values. If a cursor field is also specified, it is currently ignored without an error. The cursor scenario is written after settling whether to ignore or use these fields.
