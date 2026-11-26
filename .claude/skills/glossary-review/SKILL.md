---
name: glossary-review
description: Review a document people review (KNOWLEDGE.md, BEP, AGENTS.md, skill, README, PR description) for words and writing - the doclint words check and the items it does not find
disable-model-invocation: false
tags:
  - docs
  - glossary
---

## Scope

Every document people review: `KNOWLEDGE.md`, BEP, `AGENTS.md`, skill, `README.md`, PR description.
Run it after writing or changing one, before requesting the review.

## Steps

1. Run `go run ./tools/doclint check <file>`. Fix what it prints. Check the `review:` lines too.
2. Read the document again for the items below.
3. Fix, run step 1 again, and report the locations and words changed.

The rules are in `glossary/registry/`. After translating a Korean draft into English, run the
check on the English file.

## Items to check

The `words` check finds only registered words. Check these by hand.

| Item | Rule |
|---|---|
| Term form | Use the term the registry gives for the document's language. Code identifiers stay in English inside backticks |
| Coined terms | Do not name a group that the registry and the code do not name |
| Headings, table headers | Use concrete nouns, not a nominalized clause |

A `review:` line is a word with other valid meanings. Decide it by the reason it prints, or by
the `qualifier` of its entry in `glossary/registry/rules.yaml`.

Report a word the registry lacks as a registration candidate when the document uses it repeatedly.
Register a word in `glossary/registry/`.
