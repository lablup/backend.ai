---
name: glossary-review
description: Review a document people review (KNOWLEDGE.md, BEP, AGENTS.md, skill, README, PR description) against the glossary - the glossary of the document's language, check_words.py, and the items the script does not find
disable-model-invocation: false
tags:
  - docs
  - glossary
---

## Scope

Every document people review: `KNOWLEDGE.md`, BEP, `AGENTS.md`, skill, `README.md`, PR description.
Run it after writing or changing one, before requesting the review.

## Glossary by document language

| Document | Glossary | Term form |
|---|---|---|
| Korean (`.ko.md`, a Korean draft) | `GLOSSARY.ko.md`, `glossary/<topic>.ko.md` | The Korean column of the term files |
| English (`.md`, an English-only document) | `GLOSSARY.md`, `glossary/<topic>.md` | The English column of the term files |

After translating a Korean draft into English, review it again with the English glossary.

## Steps

1. Read the style rules and expressions to avoid in the glossary of the document's language, and the term file for the topic.
2. Run `python3 scripts/knowledge/check_words.py <file>`. Check the `review:` lines too.
3. Read the document again for the items below.
4. Fix, run step 2 again, and report the locations and words changed.

## Items to check

`check_words.py` finds only registered words. Check these by hand.

| Item | Rule |
|---|---|
| Term form | Use the term form of the document's language. Code identifiers stay in English inside backticks |
| Coined terms | Do not name a group that the glossary and the code do not name |
| Notation | Arrows, dashes, parentheses and list separators follow the notation rules of the document's glossary |
| Headings, table headers | Use concrete nouns, not a nominalized clause |

Verbs to avoid are registered in the expressions-to-avoid table of each glossary, so `check_words.py` finds them. A match with a qualifier prints as `review:`: decide it by the qualifier.

Report a word the glossary lacks as a registration candidate when the document uses it repeatedly.
