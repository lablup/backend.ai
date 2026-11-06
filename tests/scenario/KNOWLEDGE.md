---
name: scenario-tests-rationale
type: design-rationale
description: why the scenario tree has no shared background, seeds through write specs rather than adapters, checks only representative rows over ops, and what the template database holds
scope: tests/scenario
keywords: [scenario, seeder, rbac, template-database, adapter]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
updated:
  by: claude-code/opus-5-5
  at: 2026-11-06
status: draft
---
# Scenario tests: background

Rules are in `AGENTS.md` in this directory, the layout in `README.md`. Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## What the template database holds

The schema and nothing else. It holds no rows.

The DDL of 131 tables is expensive and a copy is cheap, so the template exists. Each test copies it with
`CREATE DATABASE ... TEMPLATE`. It has no other purpose and must not gain one.

A single row in it raises the question of where the common background ends and the scenario premise begins. That line always
blurs, and scenarios end up depending on what they believe they do not depend on.

## Why the shared background was removed

The template first held four users, one domain, one project and three policies. That caused four problems.

- One persona name meant four unrelated things at once: which user row, the legacy role column of that row,
  which project member list it is on, and which RBAC permissions it received. The table showed only the last.
- A scenario could not change its own premise. Needing a different role meant changing the background, and
  other scenarios moved with it.
- Rows no scenario used became dependencies of every scenario.
- The background provided things silently, so the table did not say what a request needs.

The last was the largest. Creating one vfolder needed four more things, and nobody knew while the background
provided them.

## Why rows are seeded through write specs rather than adapters

Setting up a situation is work for the ops layer. The adapter is the test target, not a setup tool.

Defining a situation as earlier adapter calls was proposed but rejected. A session scenario that needs a
vfolder would have to assemble the vfolder adapter too, and the dependencies of one scenario would spread
outside the test target.

Scenarios create rows only through `TestSeeder` methods (`creating`, `adding` and others). Every one of these
methods takes a write spec from src (`Creator`, `Upserter` and others). Test code therefore cannot create rows
directly with SQL or the ORM, and rows are created only on the paths the Manager actually writes through. The
method list is in `AGENTS.md`.

## Why creating a user is different

Creating a user is not one row. The manager writes the user row, the graph position of that row, the role the
preset names, the keypair used for authentication, and the personal project together.

Imitating this in pieces diverges silently later. A personal vfolder finds the personal project through its
owner, and without that project the vfolder has nowhere to attach. So tests use the whole operation.

## Why role presets are not used

This tree verifies whether a request passes with the permission and is rejected without it. What a shipped role
preset gives an administrator is a different question. Mixing them makes tests of the former break when the
latter changes.

The four shipped role presets are all `deleted: true`, so they do not work as they are. Reviving them bypasses
the product state.

## Why scenarios check only representative rows over ops

The ops tests check every case of the ops a call uses. Every ops factory src uses has processor or service tests
(checked 2026-11-06). Repeating those cases in each entity's scenarios adds rows without checking anything new.

What ops does not see, the adapter decides: which permission it checks, how it maps the request and response, and
what it does outside ops. The defects found while writing scenarios were all there. An id found by name was looked
up by another column, an empty domain name was passed on, and fields were dropped from a response.

A rejection row whose user has no permission at all passes even when the adapter puts the wrong entity type or
operation in the Action. Only a user with one permission removed from the success user tells them apart.

## Some entities cannot carry permissions

The domain is one. It is created outside every scope and has no child entities under it. Projects, users and
their vfolders attach to a domain.

A scenario such as a user granted domain read permission therefore cannot exist. Reading a domain depends on
the global superadmin role, not on the permission graph.

Before writing scenarios for a new component, look at the branches of its entity creator spec. A branch outside
every scope cannot have permission scenarios.

## Isolation has three layers

| Layer | Range |
|---|---|
| postgres container | One per test process. The pool runs one per slot |
| template database | One per container |
| working database | One per test. Deleted at the end |

This is the reason rows are named with a per-scenario counter instead of random values. Names must be unique
within one test, so a counter is enough, and being deterministic it keeps failure messages the same across runs.

## There are two clocks

The database server writes timestamps and the test process compares them. The check runs right after the write,
so a small skew between the clocks produces a time that has not arrived yet. Time conditions therefore allow a
tolerance.

The lower bound of the condition is the time the scenario started being built, not an arbitrary time window.
`TestSeeder` holds that time and `since_started` builds the condition from it. Whether a timestamp falls within
a few minutes says nothing about whether the value is correct.
