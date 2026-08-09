---
name: knowledge
description: Search and author KNOWLEDGE.md background-knowledge documents - frontmatter schema, search/check scripts, and the generated/verified lifecycle rules
disable-model-invocation: false
tags:
  - docs
  - knowledge
---

## Purpose

`KNOWLEDGE.md` files hold background knowledge — rationale, decision tables,
constraints — with a fixed frontmatter schema so they can be **found without
being read**. This skill covers finding them and writing them.

**When to use:** before designing or reviewing in an unfamiliar area (search
first) / when a decision or rationale worth keeping has been settled (author).

## Search

```bash
python3 scripts/knowledge/search.py                # list all documents
python3 scripts/knowledge/search.py lookup rbac    # every term must match
```

Terms match name, type, keywords, description, and path (case-insensitive).
Judge by the printed description; open only the files you actually need.

## Frontmatter schema

| Field | Required | Value |
|---|---|---|
| `name` | yes | stable id, kebab-case, unique across the repo. Never rename |
| `type` | yes | document kind: `design-rationale` / `decision-table` / `constraints` / `reference` (open vocabulary) |
| `description` | yes | noun-phrase list of what the document covers — the primary search signal. Not a sentence about the document |
| `scope` | yes | directory the knowledge applies to |
| `keywords` | no | 5-10 terms; include code identifiers (class/function names) |
| `sources` | no | file/directory paths the content is grounded in — never PR or issue numbers |
| `generated` | yes | `{by, at}` — actor and date of the last meaningful change |
| `verified` | no | list of `{by, at}` — human review sign-off for the current content |
| `status` | no | `draft` / `stable` (default) / `deprecated` |

Actor convention: `<producer>/<version>` for agents (e.g. `claude-code/fable-5`),
`human:<id>` for people (e.g. `human:hyeokjin`).

## Lifecycle rules

- A meaningful change (content, judgment, table) updates `generated` and
  **removes `verified`** — the sign-off applied to the old content. Typo and
  formatting fixes touch neither.
- `verified` is added only for a human review of the current content.
- Set `status: deprecated` before deleting a document, so inbound links get a
  window to migrate.
- Knowledge follows the rules: when an `AGENTS.md` change shifts a base
  assumption, or a migration a document describes as in-progress completes,
  update the affected document **in the same change**. Routine task-level edits
  are not a trigger — the test is whether the document's assumptions still hold.

## Size and splitting

- **One `KNOWLEDGE.md` per package.** The document follows the package
  structure — there are no per-topic knowledge files.
- Keep a document under **~200 lines** and on one topic cluster. The
  description is the test: when it reads as two unrelated lists, the package
  is carrying two concerns.
- An oversized `KNOWLEDGE.md` is a package-design signal, not a documentation
  problem — split the package, or move the extra topic's knowledge into the
  subpackage's own `KNOWLEDGE.md`.

## References and links

- Code references go in `sources` (paths only). Document-to-document
  references go **in the body** as relative markdown links, where the
  surrounding sentence says why the link matters. There is no frontmatter
  link list.
- No dangling links: CI fails on links to missing files. Mention a planned
  document in plain text, without a link.

## Check before pushing

```bash
python3 scripts/knowledge/check.py
```

Validates the schema, scope/sources path existence, body links, name
uniqueness, and the verified-not-older-than-generated invariant.
`knowledge-check.yml` runs the same script on pull requests.

## What goes where

| Content | Home |
|---|---|
| Imperative rules | `AGENTS.md` |
| Rationale, decision tables, constraints, canonical examples | `KNOWLEDGE.md` |
| Human-facing component overview | `README.md` |
| Issue-scoped working notes | outside the repo |
