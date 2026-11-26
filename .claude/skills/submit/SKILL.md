---
name: submit
description: Submission workflow of v2. Checks before the commit, the changelog fragment, the commit, a PR with base v2, and checking the CI result and finding the cause of a failure. Use after finishing the implementation.
tags:
  - submit
  - pr
  - changelog
---

> Step 7 of the workflow (the "Workflow" table in AGENTS.md).

# Submission workflow

After the implementation is done, go through the checks, the changelog fragment, the commit, the PR and the CI result in order.

## Parameters

- **issue_key** (optional): The issue key (`BAI-1234`, `BA-1234`). If missing, find it in the branch name with the pattern `(BA|BAI)-\d+`. If it is not found, ask the user.
- **kind** (optional): The fragment kind, one of `breaking`, `feature`, `deprecation`, `fix`, `doc`, `misc`. If missing, set it from the most significant change.
- **message** (optional): The description to write in the fragment. If missing, make it from the changes.
- **draft** (optional): Open the PR as a draft PR.

## 1. Review the changes

1. See the changed and untracked files with `git status`.
2. See the content with `git diff` and `git diff --staged`.
3. See the existing commits of the branch with `git log origin/v2..HEAD`.
4. Summarize the changes to the user.

## 2. Checks before the commit

pre-commit runs the following when you commit.

| Target | Run |
|---|---|
| A staged `.go` file | `go tool golangci-lint fmt`, `go tool golangci-lint run --fast-only --new-from-rev HEAD` |
| A staged file under `changes/unreleased/` | `go run ./tools/changelog check` |

- To run them before the commit, use the same commands. The full lint is `go tool golangci-lint run`, the build is `go build ./...` and the unit tests are `go test -short ./...`. For tests that need a database, follow `/test-guide` and `/halfstack`.
- The vulnerability check is `go tool govulncheck ./...`. A failure does not block a PR; it blocks a release.
- When a hook fails, find the cause in its output, fix it and commit again. Do not bypass it with `--no-verify`.
- There is no pre-push.

## 3. Changelog fragment

Add a fragment for a change users see. The kinds, the name and the content rules follow `changes/README.md`.

1. The file name is `changes/unreleased/<issue key>.<kind>.md`. One issue can have several files, one per kind.
2. The content is a description for users, not for developers. An empty file is rejected.
3. Show the draft to the user and get approval.
4. Check the format.

```bash
go run ./tools/changelog check
```

- Put the fragment in the first commit of the same PR.
- To check that the PR has a fragment, use `go run ./tools/changelog check --require --base origin/v2`. There is no CI check yet that requires a fragment in a PR.
- A change users do not see (tests, CI, internal cleanup) gets no fragment.

## 4. Commit

1. Name each file with `git add` (do not use `-A`). Do not add `.env` or credential files.
2. The commit message follows the conventional commit format: `type(<issue key>): description`.
   - The type is one of `feat`, `fix`, `doc`, `docs`, `refactor`, `ci`, `chore`, `release`, `test`, `deps`. The PR title check (`.github/workflows/pr-prefix.yml`) uses the same list.
   - The scope is the issue key. Do not use a component name.
   - The first line is 80 characters or fewer.
3. Show the message draft to the user and commit after approval.

## 5. Create the PR

1. Push the branch: `git push -u origin <branch>`.
2. The title has the same format as the commit (`type(<issue key>): description`). Do not write an issue key other than the assigned issue in the title or the body.
3. The body template:

```markdown
## Summary
<1-3 lines on what changed and why>

## Test plan
- [ ] <verification item>

Resolves <issue key>
```

4. The base is `v2`.

```bash
gh pr create --base v2 --title "..." --body "..."
gh pr create --base v2 --draft --title "..." --body "..."   # draft
```

## 6. Check the CI result

A draft PR skips this step.

1. The required check of a PR is `ci-gate` (fmt, lint, build). `test-short`, `generate-diff` and `vuln` only report. The full test (`-race`, Postgres) runs on a push to `v2` and on a release (`.github/AGENTS.md`).
2. Look at the result. To wait, do not repeat `gh pr checks <PR>`; wait with one `gh run watch <run id> -i 60`.

```bash
gh pr checks <PR>
```

3. Find the cause of a failed job. The job id is the last segment of the `link` in `gh pr checks <PR> --json name,bucket,link`.

```bash
gh run view --job <job-id> --log-failed
```

4. Fix the cause, commit (step 4) and push. If the same failure remains after two fixes, stop and report the cause and the log to the user.
5. Report a failure unrelated to the change (another PR fails too, a runner error) without fixing it.

## 7. Report

```
Submission complete

  PR:        #<number> - <title>
  URL:       https://github.com/lablup/backend.ai/pull/<number>
  Issue:     <issue key>
  Branch:    <branch>
  Fragment:  <path>

CI: <passed | failed: <job> | pending: gh pr checks <number>>
```

For a draft PR, write `CI: not checked (draft)`.

## Error handling

| Situation | Handling |
|---|---|
| A hook fails | Fix the cause in the output and commit again |
| No change to commit | Report "No changes" and stop |
| PR creation fails | Check `gh auth status`, whether a PR already exists and whether the branch is pushed |
| No issue key | Ask the user for the key |

## Related documents

- `changes/README.md`: the fragment kinds and how to write them
- `/test-guide`: writing and running tests (do this before `/submit`)
- `/local-review`: a review from another session before the submission

Next: none. The workflow ends when `ci-gate` passes.
