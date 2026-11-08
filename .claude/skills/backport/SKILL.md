---
name: backport
description: Fix a failing backport pull request (branch backport/<PR>-to-<version>) - find the conflict markers the backport workflow committed, resolve them or reapply the change on the release branch, verify, commit and push. Use when CI fails on a backport pull request.
tags:
  - backport
  - release
  - conflict
---

# Backport Fix Workflow

Fixes a backport pull request whose CI fails. Runs five phases: find the cause → classify the conflicts → fix → verify → commit and push.

`.github/workflows/backport.yml` cherry-picks the merged commit onto each target release branch. When the cherry-pick conflicts, the workflow:

- commits the conflict markers as they are
- creates the pull request without auto-merge
- comments the conflicted files on the original pull request

CI fails on that branch until someone resolves the markers by hand.

## Parameters

- **branches** (required): one or more backport branches (`backport/16488-to-26.9`), or the original pull request number.
- **jira_key** (optional): taken from the backport commit headline (`feat(BA-8229): ...`).

## Phase 1: Find the cause

1. Find the pull request for each branch, then list the failed checks:
   ```bash
   gh pr list --repo lablup/backend.ai --head backport/<PR>-to-<ver> --state all --json number,title,state
   gh pr checks <number> --repo lablup/backend.ai
   ```
2. Read the lint and typecheck logs first. They fail fastest and point at the failing file:
   ```bash
   gh run view --repo lablup/backend.ai --job <job-id> --log-failed
   ```
   - A committed conflict marker shows up as a syntax error (`Invalid decimal literal`) or a broken import statement.
3. Fetch the backport branch and its release branch into tracking refs:
   ```bash
   git fetch origin "backport/<PR>-to-${ver}:refs/remotes/bp/${ver}" "${ver}:refs/remotes/bp/base-${ver}"
   ```
4. List the committed markers:
   ```bash
   git grep -n -E '^(<<<<<<<|=======$|>>>>>>>)' "bp/${ver}" -- src tests
   ```
   - The original pull request's backport comment lists the same files.

If no marker exists, the backported change itself breaks on the release branch. Skip to Phase 3 and fix it as an ordinary change.

## Phase 2: Classify the conflicts

For each branch, compare the two sides of every hunk: `HEAD` is the release branch, the incoming side is the `main` commit.

1. Find where the release branch differs from `main`:

   | Difference | Example |
   |---|---|
   | Import path | `models.project` vs `models.project.row` |
   | Config key | etcd `"addr"` vs `"addrs"` |
   | Logger | `BraceStyleAdapter` vs `StructuredLogger` |
   | Action name | `ListMountsAction` vs `GlobalListMountsAction` |
   | Constructor argument | `own_check` present or absent |
   | Class, module or test present only on `main` | an error class the release branch does not have |

2. Check the code that applied without a conflict too. It can still break on the release branch, for example a test helper that uses a config key the release branch does not read.
3. Pick the fix:

   | Situation | Fix |
   |---|---|
   | Few hunks, and each hunk resolves by picking one side | Resolve the markers, then patch the differences |
   | The cherry-pick pulled in code that exists only on `main` | Restore the conflicted files from the release branch and reapply the change |

4. Do not change the code when a conflict needs a human decision instead of a mechanical fix. Report the conflict and the options to the user, then wait. Examples:
   - The change behaves differently on the release branch.
   - The change depends on a feature or a schema the release branch does not have.
   - Resolving it means choosing which behavior the release branch keeps.

## Phase 3: Fix

1. Work in a separate worktree per branch so the current worktree stays untouched:
   ```bash
   git worktree add -B "backport/<PR>-to-${ver}" "<scratchpad>/bp-${ver}" "bp/${ver}"
   ```
2. **Resolve the markers** (few hunks):
   - Edit each hunk by hand: keep one side, or merge both, then delete the three conflict markers.
   - For an import conflict, keep the release branch's path and add only the new import.
3. **Reapply the change** (code from `main` pulled in):
   - Restore the conflicted files: `git checkout "bp/base-${ver}" -- <files>`.
   - Apply the final change from the squash commit on `main`, review fixes included, using the release branch's names and structure.
   - Leave out the classes, imports and tests that exist only on `main`.
4. Patch the differences from Phase 2: config keys, imports left unused, fixture names.

## Phase 4: Verify

Run every check inside the worktree.

1. No marker remains:
   ```bash
   git grep -n -E '^(<<<<<<<|=======$|>>>>>>>)' -- src tests
   ```
2. Check that each fixture and constructor argument the new tests use exists on the release branch (`grep`). CI runs the pants-based checks (root `AGENTS.md` "Before committing").
3. Compare `git diff --stat "bp/base-${ver}"` with the change on `main`. A backport much larger than the original pulled in `main`-only code.

## Phase 5: Commit and push

1. Add a commit on top of the workflow's commit. Do not amend it. The pre-commit hook checks the staged files:
   ```bash
   git add <files>
   git commit -m "fix(BA-XXXX): resolve backport conflicts for <ver>"
   ```
   - The body states what was kept from the release branch and what `main`-only code was dropped.
2. Push. The pre-push hook checks for rejected words:
   ```bash
   git push origin "backport/<PR>-to-${ver}"
   ```
3. Check that the pull request head moved to the new commit, then remove the worktree:
   ```bash
   gh pr view <number> --repo lablup/backend.ai --json headRefOid --jq .headRefOid
   git worktree remove "<scratchpad>/bp-${ver}"
   ```
4. Merge by hand once CI passes. The workflow does not enable auto-merge on a conflicted backport. If CI fails again, go back to Phase 1 and find the cause in the failed job's log.

## Related documents

- `/submit` - choosing the backport targets (`Backport:` trailer) when creating the original pull request
- `.github/workflows/backport.yml` - the cherry-pick and conflict handling
- `.github/maintained-versions.yml` - the maintained release branches
