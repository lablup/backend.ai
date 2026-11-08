---
name: submit
description: Complete submission workflow - quality checks, commit, PR creation, changelog generation, and final push. Use after finishing implementation work.
tags:
  - submit
  - pr
  - quality
  - changelog
---

# Submit Workflow

Automates the post-implementation submission pipeline: quality enforcement, changelog, commit, PR creation, and push.

## Parameters

- **jira_key** (optional): JIRA issue key (e.g., `BA-1234`). Auto-detected from branch name if pattern `BA-\d+` exists.
- **changelog_type** (optional): One of `breaking`, `feature`, `enhance`, `deprecation`, `fix`, `doc`, `deps`, `misc`, `test`. If omitted, infer from the most significant change.
- **changelog_message** (optional): One-line English summary for the changelog fragment. If omitted, generate from the changes.
- **base_branch** (optional): Target branch for PR. Defaults to `main`.

## Workflow

### Phase 1: Pre-flight

1. **Detect JIRA key**
   - Check if user provided `jira_key`
   - Otherwise extract from current branch name (pattern: `BA-\d+`)
   - If not found, ask user

2. **Review changes**
   - `git status` to see all changed/untracked files
   - `git diff` and `git diff --staged` to review content
   - `git log {base_branch}..HEAD` to see existing commits on branch
   - Summarize changes to user before proceeding

### Phase 2: Quality Enforcement (Local)

**MANDATORY - never skip.**

Run sequentially, stop on first failure:

```bash
pants fmt ::
pants fix ::
pants lint --changed-since=origin/{base_branch}
```

- If `fmt` or `fix` produce changes, stage them automatically
- If `lint` fails, fix the issues and re-run
- After all pass, continue to next phase

**Note:** Type checking (`pants check`) and tests (`pants test`) are enforced by CI only. Do NOT run them locally — they consume excessive resources when multiple workers run concurrently.

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
   - Use conventional commit style: `type(BA-XXXX): description`
   - Types: `fix`, `feat`, `refactor`, `test`, `doc`, `ci`, `chore`, `perf`
   - **When a JIRA key is available, ALWAYS use it as the conventional commit scope. Never use component names like `manager`, `client`, `client-sdk` as the scope.**
   - Example: `fix(BA-1234): resolve session cleanup race condition`
   - Keep first line under 80 characters
   - Add detailed body if multiple significant changes

3. **Create commit**
   - Present draft message to user for approval
   - Commit with approved message

### Phase 5: PR Creation

1. **Push branch**
   - `git push -u origin {branch_name}`

2. **Generate PR content**
   - **Title**: Conventional commit style with JIRA key as scope
     - Format: `type(BA-XXXX): description`
     - Example: `fix(BA-1234): resolve session cleanup race condition`
     - See `changes/KNOWLEDGE.md` for the category-to-prefix/changelog-type mapping, including same-release fixes (`chore`, not `fix`)
   - **Body**: Use this template:

   ```markdown
   ## Summary
   <1-3 bullet points describing what changed and why>

   ## Test plan
   - [ ] <test items>

   Resolves BA-XXXX
   ```

3. **Decide backport targets** (before creating the PR — the trailer lives in the PR body)

   Backporting is automatic. There is no milestone to set; the target release branches are
   decided from the PR title prefix, the PR body and the labels.

   The title prefix picks the default; a `Backport:` line in the PR body replaces it.

   | Situation | What to do |
   |---|---|
   | `fix:` PR going to every maintained version | Nothing |
   | Any PR going to particular versions | Add `Backport: 26.8, 26.4` to the PR body — comma- or space-separated |
   | `fix:` PR that must NOT be backported | Add `Backport: none` to the PR body |
   | Non-`fix:` PR that stays on `main` | Nothing |
   | A target realized only after the merge | Comment `/backport <version>` on the merged PR |

   - Valid versions are exactly the entries of `.github/maintained-versions.yml` — read that file
     rather than guessing. A trailer naming anything else fails the backport job and backports
     nothing, so get it right or leave the trailer out.
   - Writing a `Backport:` trailer is a release decision: ask the user before adding one.

4. **Create PR**
   ```bash
   gh pr create --title "..." --body "..."
   ```

5. **Extract PR number** from `gh pr create` output

### Phase 6: Summary

Report final status:

```
Submission Complete

  PR:        #{pr_number} - {title}
  URL:       https://github.com/lablup/backend.ai/pull/{pr_number}
  JIRA:      BA-XXXX
  Branch:    {branch_name}
  Changelog: {changelog_path}

Quality checks: All passed
Commits: {count} commit(s)
```

## Error Handling

### Quality check failure
```
Quality check failed at: {step}

Error:
{error_output}

Options:
1. Fix issues and re-run /submit
2. Address specific failures manually
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
Agent: [Detects BA-1234 from branch, runs quality checks, generates changelog, commits, creates PR]
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

## Related Skills

- `/test-guide` - Scenario-first testing (run before /submit)

## Implementation Notes

- Local quality checks (`fmt`, `fix`, `lint`) use `--changed-since=origin/{base_branch}` to cover all PR changes, not just the last commit
- Type checking and tests run in CI only — do not run them locally
- Changelog follows [towncrier](https://github.com/twisted/towncrier) format configured in `pyproject.toml`
- The changelog fragment is named without a PR number and goes into the first push; the release renames it (`changes/README.md`). A `<PR-number>.<type>.md` fragment added after `gh pr create` is still accepted
- A single PR may have multiple changelog fragments (for example both `feature` and `fix`)
- Changelog fragment content should be a single-line sentence per `changes/README.md` guidelines
