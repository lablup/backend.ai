---
name: knowledge
description: Search and author KNOWLEDGE.md background-knowledge documents: frontmatter schema, search/check scripts, and the generated/verified lifecycle rules
disable-model-invocation: false
tags:
  - docs
  - knowledge
---

## Purpose

`KNOWLEDGE.md` files hold background knowledge, such as rationale, decision tables and constraints, with a fixed frontmatter schema so they can be **found without being read**. This skill covers finding them and writing them.

**When to use:** before designing or reviewing in an unfamiliar area (search first), or when a decision or rationale worth keeping has been settled (author).

## Search

```bash
python3 scripts/knowledge/search.py                # list all documents
python3 scripts/knowledge/search.py lookup rbac    # every term must match
```

Terms match name, type, keywords, description and path, case-insensitively. Judge by the printed description and open only the files you need.

## Frontmatter schema

| Field | Required | Value |
|---|---|---|
| `name` | yes | stable id, kebab-case, unique across the repo. Do not rename |
| `type` | yes | document kind: `design-rationale` / `decision-table` / `constraints` / `reference` (open vocabulary) |
| `description` | yes | noun-phrase list of what the document covers, the primary search signal. Not a sentence about the document |
| `scope` | yes | directory the knowledge applies to |
| `keywords` | no | 5 to 10 terms; include code identifiers (class and function names) |
| `sources` | no | file and directory paths the content is grounded in, not PR or issue numbers |
| `generated` | yes | `{by, at}`, the actor and date of the first version. Does not change |
| `updated` | no | `{by, at}`, the actor and date of the last meaningful change after generation |
| `verified` | no | list of `{by, at}`, human review sign-off for the current content |
| `status` | no | `draft` / `stable` (default) / `deprecated` |

Actor convention: `<producer>/<version>` for agents (for example `claude-code/fable-5`) and `human:<id>` for people (for example `human:hyeokjin`).

## Lifecycle rules

- A meaningful change (content, judgment, table) sets `updated` and **removes `verified`**, which applied to the old content. `generated` stays. Typo and formatting fixes touch none of them.
- `verified` is added only for a human review of the current content.
- Set `status: deprecated` before deleting a document, so inbound links get a window to migrate.
- When an `AGENTS.md` change shifts a base assumption, or a migration a document describes as in progress completes, update the affected document **in the same change**. Routine task-level edits are not a trigger; the test is whether the assumptions of the document still hold.

## Body structure

- **The document's job is the background knowledge of the package** - what a newcomer must assume before touching the package. Local curiosities without that frame do not stand alone.
- **Open with why the package exists** - the reason it is defined as its own package and the role it plays for its consumers, before any specific topic.
- **The heading is the claim** - each section heading states one claim and the body backs it with 2 to 4 single-sentence bullets. Comparisons and enumerations use tables or list syntax, not a long paragraph. Prose paragraphs are allowed only in the opening section, two sentences at most.
- A parent document does not restate knowledge a subpackage document owns. Link it from the header pointer or where the context needs it. Every section must be knowledge about this package itself.

## English and Korean

- English goes in `KNOWLEDGE.md`, Korean in `KNOWLEDGE.ko.md` in the same folder.
- Frontmatter goes only in `KNOWLEDGE.md`. Search and the schema check read only that file.
- Both files keep the same headings in the same order. Update both in the same change.
- Do not add Korean to `KNOWLEDGE.md`.
- Use the words in `GLOSSARY.md` and `glossary/<topic>.md`.

## Size and splitting

- **One `KNOWLEDGE.md` per package.** The document follows the package structure, with no per-topic knowledge files.
- Keep each language file under **about 200 lines** and on one topic cluster. The description is the test: when it reads as two unrelated lists, the package is carrying two concerns.
- An oversized `KNOWLEDGE.md` is a package-design signal, not a documentation problem. Split the package, or move the extra topic's knowledge into the `KNOWLEDGE.md` of the subpackage.

## References and links

- Code references go in `sources` as paths only. Document-to-document references go **in the body** as relative markdown links, where the surrounding sentence says why the link matters. There is no frontmatter link list.
- No dangling links: CI fails on links to missing files. Mention a planned document in plain text, without a link.

## Check before pushing

```bash
python3 scripts/knowledge/check.py
python3 scripts/knowledge/check_bilingual.py --base origin/main
python3 scripts/knowledge/check_words.py --base origin/main
```

These validate the schema, scope and sources path existence, body links, name uniqueness, and the verified-not-older-than-generated invariant. `check_bilingual.py` validates the `.md` and `.ko.md` pairs and rejects Korean added to a `.md` file. `check_words.py` finds the words the glossary rejects in added lines, and takes paths to check whole files. `knowledge-check.yml` runs all three on pull requests.

## What goes where

| Content | Home |
|---|---|
| Imperative rules | `AGENTS.md` |
| Rationale, decision tables, constraints, canonical examples | `KNOWLEDGE.md` |
| Human-facing component overview | `README.md` |
| Pointer to `AGENTS.md` | `CLAUDE.md` (symlink) |
| Words and writing style | `GLOSSARY.md`, `glossary/<topic>.md` |
| Scenario test results, generated and not edited by hand | `report.md`, `report.ko.md` |
| Issue-scoped working notes | outside the repo |
