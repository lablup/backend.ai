---
name: submit
description: Complete submission workflow - changelog generation, commit, push, PR creation, and CI watch with fixes. Use after finishing implementation work.
tags:
  - submit
  - pr
  - quality
  - changelog
---

# Submit Workflow

Automates the post-implementation submission pipeline: changelog, commit, push, PR creation, and CI watch.

## Parameters

- **jira_key** (optional): JIRA issue key (for example `BA-1234` or `BAI-1234`). Auto-detected from branch name if pattern `(BA|BAI)-\d+` exists.
- **changelog_type** (optional): One of `breaking`, `feature`, `enhance`, `deprecation`, `fix`, `doc`, `deps`, `misc`, `test`. If omitted, infer from the most significant change.
- **changelog_message** (optional): One-line English summary for the changelog fragment. If omitted, generate from the changes.
- **base_branch** (optional): Target branch for PR. Defaults to `main`.
- **draft** (optional): Open a draft PR. Commits with `--no-verify` to skip the pre-commit hook, and requires no approval.

## Workflow

### Phase 1: Pre-flight

1. **Detect JIRA key**
   - Check if user provided `jira_key`
   - Otherwise extract from current branch name (pattern: `(BA|BAI)-\d+`)
   - If not found, ask user; with `--draft`, continue without a key

2. **Review changes**
   - `git status` to see all changed and untracked files
   - `git diff` and `git diff --staged` to review content
   - `git log {base_branch}..HEAD` to see existing commits on branch
   - Summarize changes to user before proceeding

### Phase 2: Checks

No local checks run here. Checks follow the root `AGENTS.md` "Before committing": the git hooks run on commit and push, and the pants-based checks are confirmed from the CI results in Phase 6.

### Phase 3: Changelog Fragment

1. **Determine changelog type** (if not provided); see `changes/KNOWLEDGE.md` for valid types and the category mapping

2. **Generate changelog message** (if not provided)
   - Single-line English sentence
   - Imperative/commanding form: "Fix XXX", "Add YYY", "Support ZZZ"
   - Or complete sentence: "Now it does ZZZ"
   - Focus on what the change means to users and developers, not implementation details
   - Show the draft to the user for approval; with `--draft`, skip the approval

3. **Find the epic**
   - The `Epic` row of `hejo issue get {jira_key}` is the epic key. Without an issue key or an epic, leave out `--epic` and skip step 4

4. **Create the epic files if missing**
   - Write the pair `changes/epics/{epic_key}.md` (English) and `changes/epics/{epic_key}.ko.md` (Korean) in the format of the epic file section of `changes/README.md`
   - Draft them from the epic's English title, Korean title and body. Show the draft to the user for approval; with `--draft`, skip the approval

5. **Create the fragment**
   ```bash
   python3 scripts/new-changelog.py {changelog_type} "{changelog_message}" [--issue {jira_key}] [--epic {epic_key}]
   ```
   - Prints the path `changes/<YYYYMMDD>-<HHMMSS>-<6 chars>.{changelog_type}.md`; the release renames it to `<PR-number>.{changelog_type}.md`
   - Without an issue key, leave out `--issue`
   - Stage it with the code in Phase 4, so it goes into the first push

### Phase 4: Commit

1. **Stage changes**
   - `git add` specific files, including the changelog fragment from Phase 3 (avoid `-A` to prevent accidental inclusion of secrets)
   - Do not stage `.env`, credentials or other sensitive files

2. **Generate commit message**
   - Use conventional commit style: `type({jira_key}): description`
   - Types: `fix`, `feat`, `refactor`, `test`, `doc`, `ci`, `chore`, `perf`
   - **When a JIRA key is available, always use it as the conventional commit scope. Do not use component names like `manager`, `client` or `client-sdk` as the scope.**
   - Example: `fix(BAI-1234): resolve session cleanup race condition`
   - Keep first line under 80 characters
   - Add detailed body if multiple significant changes

3. **Create commit**
   - Default: present the draft message to the user for approval, then commit
   - `--draft`: commit without approval: `git commit --no-verify -m "..."`

### Phase 5: PR Creation

1. **Push branch**
   - `git push -u origin {branch_name}`

2. **Generate PR content**
   - **Title**: Conventional commit style with JIRA key as scope
     - Format: `type({jira_key}): description`
     - Example: `fix(BAI-1234): resolve session cleanup race condition`
     - See `changes/KNOWLEDGE.md` for the category-to-prefix and changelog-type mapping, including same-release fixes (`chore`, not `fix`)
   - **Body**: Use this template:

   ```markdown
   ## Summary
   <1-3 bullet points describing what changed and why>

   ## Test plan
   - [ ] <test items>

   Resolves {jira_key}
   ```

   - **Do not mention a JIRA issue other than the assigned one** in the title or the body.

3. **Decide backport targets** (before creating the PR; the trailer lives in the PR body)

   Backporting is automatic. There is no milestone to set; the target release branches are
   decided from the PR title prefix, the PR body and the labels.

   The title prefix picks the default; a `Backport:` line in the PR body replaces it.

   | Situation | What to do |
   |---|---|
   | `fix:` PR going to every maintained version | Nothing |
   | Any PR going to particular versions | Add `Backport: 26.8, 26.4` to the PR body, comma- or space-separated |
   | `fix:` PR that must not be backported | Add `Backport: none` to the PR body |
   | Non-`fix:` PR that stays on `main` | Nothing |
   | A target realized only after the merge | Comment `/backport <version>` on the merged PR |

   - Valid versions are exactly the entries of `.github/maintained-versions.yml`; read that file
     rather than guessing. A trailer naming anything else fails the backport job and backports
     nothing, so get it right or leave the trailer out.
   - Writing a `Backport:` trailer is a release decision: ask the user before adding one.
     With `--draft`, do not ask and leave the trailer out.

4. **Create PR**
   ```bash
   gh pr create --title "..." --body "..."
   gh pr create --draft --title "..." --body "..."   # with --draft
   ```

5. **Extract PR number** from `gh pr create` output

### Phase 6: CI

Skip this phase with `--draft`.

1. Wait for CI with a time limit, not indefinitely:
   ```bash
   timeout 1500 gh pr checks {pr_number} --watch --fail-fast
   ```
2. Act on the result:

   | Result | Action |
   |---|---|
   | All pass | Phase 7 |
   | Failure | Find the failed job with `gh pr checks {pr_number}` and the cause with `gh run view --job <job-id> --log-failed`. Fix it, commit (Phase 4), push and go back to step 1 |
   | Timeout | Stop waiting and report CI as pending in Phase 7 |

   - If the same failure remains after two fixes, stop and report the cause and the log to the user
   - Report, without fixing, a failure unrelated to the change (one that also fails on other PRs, a runner error)

### Phase 7: Summary

Report final status:

```
Submission Complete

  PR:        #{pr_number} - {title}
  URL:       https://github.com/lablup/backend.ai/pull/{pr_number}
  JIRA:      {jira_key}
  Branch:    {branch_name}
  Changelog: {changelog_path}

CI: {passed | failed: <job> | pending: gh pr checks {pr_number}}
Commits: {count} commit(s)
```

With `--draft`, print `CI: not watched (draft)` instead.

## Error Handling

### Hook or CI failure
```
Failed at: {pre-commit | pre-push | CI job name}

Cause:
{cause found from the hook output or the job log}

Error:
{error_output}
```

### No changes to commit
```
No changes detected.

Working tree is clean. Nothing to submit.
```

### PR creation failure
```
PR creation failed: {error}

Possible causes:
- Branch not pushed (will auto-push)
- PR already exists for this branch
- Authentication issue with gh CLI

Check: gh auth status
```

### Branch has no JIRA key
```
No JIRA issue key found.

Options:
1. Provide JIRA key: /submit BA-1234
2. Continue without JIRA key (not recommended)
```

## Examples

### Basic usage (auto-detect everything)
```
User: /submit
Agent: [Detects BA-1234 from branch, generates changelog, commits, creates PR, watches CI]
```

### With explicit JIRA key
```
User: /submit BA-5678
Agent: [Uses BA-5678, runs full workflow]
```

### With all parameters
```
User: /submit BA-5678 --type=fix --message="Fix session cleanup race condition when agent disconnects"
Agent: [Uses provided parameters, runs full workflow]
```

### Draft PR without waiting for approval
```
User: /submit --draft
Agent: [Adds the changelog fragment, commits with --no-verify, opens a draft PR, does not watch CI]
```

## Related documents

- `/test-guide` - Scenario-first testing (run before /submit)

## Implementation Notes

- `--draft` commits with `--no-verify` to skip the pre-commit hook and does not wait for CI
- Changelog follows [towncrier](https://github.com/twisted/towncrier) format configured in `pyproject.toml`
- The changelog fragment is named without a PR number and goes into the first push; the release renames it (`changes/README.md`). A `<PR-number>.<type>.md` fragment added after `gh pr create` is still accepted
- A single PR may have multiple changelog fragments (for example both `feature` and `fix`)
- Changelog fragment content should be a single-line sentence per `changes/README.md` guidelines
