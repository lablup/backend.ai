---
name: common-membership-criterion
type: design-rationale
description: membership criterion for common — things shared by two or more components, or needed to keep the import direction downward
scope: src/ai/backend/common
keywords: [dependency-direction, shared, upward-import, stage, resilience, schema]
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Common — Knowledge

> Rules: `AGENTS.md` in the same directory. Event/queue semantics:
> [message_queue/KNOWLEDGE.md](message_queue/KNOWLEDGE.md) and
> [events/KNOWLEDGE.md](events/KNOWLEDGE.md).

## Why this package exists

It is the shared foundation every component depends on. The criterion for which
types belong here is the core of this document.

## The membership criterion has two parts

- The stated criterion: things **shared by two or more components**.
- The second criterion: types that, if placed in a higher layer, **would force an upward import** (`common/schema/` states this explicitly and is used only by the manager).
- Single-consumer subpackages (`stage/` — agent-only, `resilience/` — manager-only) are not defects.
- "It is convenient to put it somewhere neutral" is not a membership reason.
