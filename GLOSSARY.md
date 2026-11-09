# Glossary

Sets the words and writing style for Backend.AI documents, code comments, BEPs and PRs. One concept, one word.
Code identifiers stay in English. A name under `Do not write` can remain in code until it is renamed.

Korean: [GLOSSARY.ko.md](GLOSSARY.ko.md)

## Term files

Read this document before writing, then the term file for the topic. To find one word, search `glossary/`.

- [Product and domain concepts](glossary/domain.md): concepts the product handles, such as sessions, deployments, vfolders and resources
- [Layers and components](glossary/architecture.md): components and code layers
- [Permissions](glossary/permissions.md): RBAC, scopes, roles and operation prefixes
- [Operations](glossary/operations.md): operations such as delete, create and get
- [Status sets](glossary/statuses.md): sets of status values
- [Process and documents](glossary/process.md): development process and document kinds
- [Infrastructure](glossary/infrastructure.md): installation and operating environment
- [Technology and tool names](glossary/tools.md): external technology and tool names

## Style rules

- Rule documents (AGENTS.md, KNOWLEDGE.md, skills, prompts): use the imperative or the present tense
- One concept, one word. Do not reuse a word for a different concept
- Spell out abbreviations or explain them
- Do not write SSOT. Say what the reference value is
- Qualify generic words with where they apply (storage namespace)
- Write owner as {target} owner
- Fragments are fine in lists and table cells
- Status labels are adjectives or past participles (active, failed, deleted)
- Use one verb per operation: create, update, delete, change, run, get, call
- create = new item, add = into an existing set, register = make an external thing known
- remove = out of a set. The glossary defines delete and purge
- fix = correct a defect, update = change a value
- check = look at it, verify = run a scenario and read the result, get = read a value
- No nominalized filler. Prefer active voice. Avoid regarding, with respect to
- Do not end with a question
- Use parentheses only to explain a term
- Use arrows only for flows, state changes and lists, not inside sentences
- Do not join sentences with a dash
- Comma for like items, slash for 3-4 contrasting items, no middle dot
- Avoid placeholder examples (A, B). Name what it is
- Use only issue keys and PR numbers, always with a description
- Prefix the service name when two services share a word
- Write a term in the exact form the term files give, including capitalization

## Document templates and notation

- Do not join sentences with a dash (` — `, ` -- `). Split the sentence or use a colon or parentheses
- Write arrows as →. Use them only for flows, state changes and lists. Inside a sentence, state the direction in words
- Use commas for lists of values and slashes for contrasts. Do not use the middle dot
- Write and, not &
- Write prohibitions as Do not, not Do NOT or NEVER use
- Use status symbols (✅, ❌) only in limited places such as tables
- Inside a list item, separate an explanation with a hyphen (-)
- Refer to a section by describing it, not by its number
- Refer to a skill by one name (/test-guide)
- Use one heading template for KNOWLEDGE.md
- KNOWLEDGE.md holds only background and rationale, and does not repeat AGENTS.md
- State an explanation once per document
- A closing summary does not list earlier sections again
- Title the related documents section Related documents
- Introduce examples with See and supplementary input with Secondary
- Write a rule as a sentence instead of an invented label (Forward direction and the like)
- AGENTS.md rule documents keep Guardrails

## Expressions to avoid

The term files set the terms. This list covers verbs and predicates. Korean wording is in [GLOSSARY.ko.md](GLOSSARY.ko.md).

| Do not write | Write |
|---|---|
| bring up, brought up, Brings up | start |
| refuse | reject |
| tell apart, keep apart, split apart | distinguish |
| is answered for by | active voice: the owning entity answers for it |
| outgoing pattern, parent-fixed variants are the outgoing pattern | legacy pattern, marked as deprecated |
| stand for | represent |
| which is why | so |
| line (of a table) | row |
