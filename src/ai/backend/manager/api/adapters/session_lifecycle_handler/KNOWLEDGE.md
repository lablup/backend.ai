---
name: session-lifecycle-handler-adapter-scenarios
type: reference
description: what the session lifecycle handler adapter guarantees: the single list call, the handlers registered on the sokovan coordinator with the name and description each handler defines, and no permission check of its own
scope: src/ai/backend/manager/api/adapters/session_lifecycle_handler
keywords: [session lifecycle handler, scenario, adapter, handler options, schedule coordinator]
generated:
  by: claude-code/opus-5.5
  at: 2026-10-12
updated:
  by: claude-code/opus-5.5
  at: 2026-10-22
status: draft
---
# session_lifecycle_handler adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt this document first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

The adapter provides one call, the list get.

That call returns the session lifecycle handlers registered on the sokovan coordinator.

The default session options of a resource group refer to a per-handler setting by handler name. A request that replaces those options is rejected when it contains a name not registered on the sokovan coordinator. This call returns the handlers of the same sokovan coordinator, so a name obtained here is not rejected by that replacement request.

The adapter runs no permission check. The REST handler middleware and the GQL resolver run the superadmin check. This document therefore does not pair the with-permission and without-permission cases.

## List get
