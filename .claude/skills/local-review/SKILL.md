---
name: local-review
description: Review work in a session separate from the working session - input bundle, review criteria (direction, structure and consistency, implementation, missing pieces, follow-up work, severity, finding format), checking the returned findings. Use when work needs a review from another session.
tags:
  - review
  - local
---

# Local Review

Review the work.

## Run

- Review in a session separate from the working session. A different model is fine
- Start it the way the user has set. If the user has set no way, ask the user
- The review session uses read tools, `git diff` and `git show` only. It does not edit files
- Pass the review session the input below and the "Review criteria" section

## Input

| Include | How |
|---|---|
| Work context | Issue body, task instruction file, decisions made during the work |
| Changed code | `git diff $(git merge-base origin/main HEAD)` (shows committed and uncommitted changes together) |
| New files not added to git | For each file in `git ls-files --others --exclude-standard`, `git diff --no-index /dev/null <file>` |

- Do not include secrets: env files, tokens, keys, passwords, local config holding credentials
- If such a file is in the change, exclude it and list the excluded path in the input

## Review criteria

### Documents to read

- Root `AGENTS.md`
- Every `AGENTS.md` from the directory of a changed file up to the root
- Related `KNOWLEDGE.md` when a judgment needs background (find with `python3 scripts/knowledge/search.py <term>`)
- For a change to docs or comments, `GLOSSARY.md` and the topic's `glossary/<topic>.md`

These documents set the rules. Report a place that breaks a rule as a finding on its axis, with the location of the rule in the document as evidence.

### Review axes

Go through the five axes in order. Write what an earlier axis catches first.

| Axis | What to check |
|---|---|
| Direction | Whether the work is needed and the approach is right |
| Structure and consistency | Whether the code sits in the right place with the right split, and follows existing patterns |
| Implementation | Defects, security, performance, implementation details |
| Missing from this change | What belongs in the same change but is not there |
| Follow-up work | What needs separate work outside this scope |

#### Direction

- Trace whether the problem the issue or task instruction states (a bug, a missing behavior) actually occurs in the code before the change. If it does not, write that first, with the evidence that the change is not needed
- Whether it fixes the cause, not the symptom
- Whether it builds something new where an existing mechanism already does the same job
- Whether it changes things beyond the issue scope: unrequested refactoring, renames, behavior changes
- Whether it changes behavior the issue or task instruction does not mention: API responses, defaults, errors, state transitions

#### Structure and consistency

Write broken structure or patterns before implementation findings.

Check structure against what the changed layer's `AGENTS.md` and that layer's guide skill set. Read the rules from those documents.

- Whether the code sits in the right layer and location
- Whether responsibilities are split between layers
- Whether it hand-writes what an existing base class or framework already does
- Whether it creates a new abstraction with only one user

Check consistency by comparing with existing code that does the same job.

- Compare with: other operations of the same service, the same module, the same layer of sibling entities (repository, service, adapter, GQL resolver, CLI and so on)
- Compare: names, file and directory locations, call path between layers, class structure and base classes, error types, how events are emitted, argument order, return types, test layout
- Check that operations of the same service follow the same flow
- Also report places in the same change that do the same job differently
- If precedents split two or more ways, state which one the change follows. If a document (`AGENTS.md`, `KNOWLEDGE.md`) sets one, use it as the reference
- If the issue or task instruction decided to change a pattern, that is not a problem. Then check that the new pattern is applied evenly across the change
- Attach the precedent path as evidence

#### Implementation

Do not check what lint, the type checker or the formatter catches.

| Aspect | What to check |
|---|---|
| Correctness | Logic errors, boundary conditions (input that is an empty list, 0, None) |
| Concurrency | Races between transactions: another request slipping in between reading, deciding and writing, updating the same row without a lock |
| Security | Missing permission checks or a scope that is too wide, external input validation, secret exposure |
| Compatibility | Breaking changes to APIs, DB schemas, events, migrations |
| Performance | N+1 queries, queries that read everything at once with no limit |
| Error handling | Places that swallow an exception or convert it so the cause is lost |
| Tests | Whether changed logic has tests, and whether they cover failure paths and boundary values |

#### Missing from this change

- Updates that document rules require in the same change (`AGENTS.md`, `KNOWLEDGE.md`, the paired English and Korean documents)
- Tests for the changed logic
- SDK, CLI, GQL and REST parts that must follow an API change
- Migrations for a schema change, the version record for a new field
- The changelog fragment
- Places where a pattern the change touched is applied to only part of the code

#### Follow-up work

- Sibling entities or other services that need the same change
- Problems that existed before the change and remain. Write them only when they connect to the problem this change fixes
- Code the change left unused
- Work deliberately deferred this time

Tell a problem that existed before the change by comparing with the code before the change.

- Read the code before the change with `git show $(git merge-base origin/main HEAD):<path>`
- If the same input gave the same result before the change, it is follow-up work. If this change caused it or made it worse, it is a finding on an earlier axis
- If you cannot tell, write it as new and add that you could not check the code before the change

### Questions

- Write only choices that actually split and that the user must decide. If there is only one answer, write it as a finding on its axis
- Write what must be decided and what happens if it is left as is

### Severity

| Severity | Covers |
|---|---|
| Must fix | Wrong direction, broken structure or pattern, an implementation defect to fix before the PR, something missing from this change |
| Should fix | Implementation findings that do not block the PR |
| Follow-up | Follow-up work |

### Finding format

Write five things for each finding.

- Axis
- `file:line`
- Severity
- Reproducing input: the input or situation where it occurs. For follow-up work, write a one-line issue title instead
- Result: one sentence on what goes wrong then. Do not end with words that state no result, such as "needs checking"

If there is no problem, say so briefly. Do not write praise, background or generalities.

## Checking returned findings

- The working session checks each finding in the code: run the reproducing input, or read the flagged code and its callers
- Report confirmed findings and findings that did not reproduce to the user separately. For the ones that did not reproduce, give the reason
- Do not pass on a finding without checking it
