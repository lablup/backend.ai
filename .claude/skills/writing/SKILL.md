---
name: writing
description: Follow when writing or changing a document (AGENTS.md, KNOWLEDGE.md, BEP, skill, README, PR description, long code comment). Holds the role of each document, the language pairs, the style and notation rules, and the document lint after writing.
tags:
  - docs
  - lint
  - writing
---

> Step 5 of the workflow (the "Workflow" table in AGENTS.md).

# Writing documents

## Use when

- Writing or changing a document (`AGENTS.md`, `KNOWLEDGE.md`, BEP, skill, `README.md`, PR description)
- A code comment or docstring grows long and moves into a document
- Before requesting the review of a document people review

## Role of each document

| Document | Role |
|---|---|
| `AGENTS.md` | Holds only rules. Concise and imperative. Always loaded automatically (`CLAUDE.md` is a symlink to this file) |
| `KNOWLEDGE.md` | Holds background knowledge (assumptions, rationale, decision tables, caveats) with a fixed frontmatter schema. Read on demand. Find and write it with `/knowledge` |
| `README.md` | A document for humans to understand the composition. Does not change often. Does not duplicate AGENTS or KNOWLEDGE |
| `glossary/registry/` | The rules of the words check of the document lint: the words to avoid, the word to write and the reason. Do not read it in advance; read the output when the check catches a word |

- A change that shifts a base assumption (an `AGENTS.md` rule rewrite, a migration completing) updates the affected `KNOWLEDGE.md` in the same change. A routine task-level edit does not.
- Place a rule **only once, at the highest level** of its scope. Put a repository-wide rule in the root `AGENTS.md` and a component-wide rule at the top level of that component. Do not repeat an upper-level rule lower down.

## Languages and pairs

- `KNOWLEDGE.md` and BEPs come in pairs in the same folder: English in `<name>.md`, Korean in `<name>.ko.md`.
- Keep the same sections and update both in the same change.
- `AGENTS.md` is English only.
- Korean goes only in `.ko.md`. Do not add Korean to a `.md` file.

## Writing style

Applies to every generated text: documents, code comments, BEPs, PR descriptions.

- Do not write a fact the body does not refer to. Put measurement conditions and the investigation in the report or the PR.
- Lead with the conclusion; keep background short.
- Put implementation details in the code and the PR. Describe interfaces and contracts in documents, not line-by-line steps.
- Prefer tables and lists over prose.
- Show only the interface and the contract in a code example, not the internal implementation.
- State a rule once at its highest scope; link instead of repeating it.
- Add no asides. Write the rule and the fact.
- Never restate the previous sentence in different words.
- Leave out how an individual value is composed and why a choice reads as natural.
- Do not coin a term to group things. Name what is there and say how many. A term invented for one document spreads before anyone agrees on it.
- Refer to a layer or a value by its name in the code. Do not replace it with a descriptive word.
- A comment or docstring stops at three lines. Anything longer is background: put it in `KNOWLEDGE.md` and link it.

## Notation

- Write a rule document (`AGENTS.md`, `KNOWLEDGE.md`, skill, prompt) in the imperative or the present tense in English and with the plain ending (-da) in Korean. Write a text people read (BEP explanation, report, issue, review) with the polite ending (-hamnida) in Korean. Fragments are fine in lists and table cells.
- One concept, one word. Write a term in the exact form the term files give, including capitalization.
- Operation verbs: create (a new item), add (into an existing set), register (make an external thing known), remove (out of a set), fix (a defect), update (a value), check (look at it), verify (run a scenario and read the result), get (read a value).
- Status labels are adjectives or past participles (active, failed, deleted), nouns in Korean.
- Spell out an abbreviation or explain it. Instead of SSOT, say what the reference value is.
- Qualify a generic word with where it applies (storage namespace). Prefix the service name when two services share a word. Write owner as `{target} owner`.
- Use parentheses only to explain a term. Use the arrow (→) only for flows, state changes and lists. Do not join sentences with a dash (` — `, ` -- `).
- Lists: a comma for like values, a slash to contrast 3-4 different ones. Do not use the middle dot (·) or `&`.
- Write a prohibition as `Do not`, not `Do NOT` or `NEVER`. Use status symbols (✅, ❌) only in tables.
- Do not end with a question. Name what it is instead of a placeholder (A, B). Write a rule as a sentence instead of an invented label.
- Use only issue keys and PR numbers as internal keys, always with a description. Refer to a section by describing it, not by its number, and to a skill by one name (`/test-guide`).
- In Korean, put a space between an English word and the particle after it. Keep a word left in English in lower case. Do not mix in English verbs. Do not stack alternative particles.
- A closing summary does not list the earlier sections again.

## Steps

### 1. Before writing

- Write the Korean draft in the real file first, and after the review move the same file into English.
- Do not read the glossary in advance. After writing, the lint names the words it catches.

### 2. Document lint after writing

```bash
go run ./tools/doclint check <file>              # the changed files
go run ./tools/doclint check --base origin/v2    # the lines the branch adds
```

- Fix each line as the output `<file>:<line>: "<word>" -> "<word to write>": <reason>` says, and run it again.
- The `build` job of `ci.yml` and pre-commit (`--staged`) run the same check.
- A `review:` line is not a failure. The word has other valid meanings, so decide by context.
- The criteria (line counts, BEP limits, frontmatter) are in `doclint.yaml`, the words to avoid in `glossary/registry/`. Add an entry there to reject a new word.

### 3. Items a person checks

The lint finds only registered words. Before requesting the review of a document people review (`KNOWLEDGE.md`, BEP, `AGENTS.md`, skill, `README.md`, PR description), check these by hand.

| Item | Rule |
|---|---|
| Term form | Use the term form of the document's language. Code identifiers stay in English inside backticks |
| Coined terms | Do not name a group that the term files and the code do not name |
| Notation | Follow the "Notation" section |
| Headings, table headers | Use concrete nouns, not a nominalized clause |

- The words to avoid are in `glossary/registry/rules.yaml`, and the lint finds them.
- Report a word the document uses repeatedly and the registry lacks as a registration candidate.
- Report the locations and words you changed.

Next: `/local-review`
