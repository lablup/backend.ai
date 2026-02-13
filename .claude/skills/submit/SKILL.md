---
name: submit
description: Complete submission workflow - quality checks, commit, PR creation, changelog generation, and final push. Use after finishing implementation work.
---

# Submit Workflow

Automates the post-implementation submission pipeline: quality enforcement, commit, PR creation, changelog, and push.

## Parameters

- **jira_key** (optional): JIRA issue key (e.g., `BA-1234`). Auto-detected from branch name if pattern `BA-\d+` exists.
- **changelog_type** (optional): One of `breaking`, `feature`, `enhance`, `deprecation`, `fix`, `doc`, `deps`, `misc`, `test`. If omitted, infer from the most significant change.
- **changelog_message** (optional): One-line English summary for the news fragment. If omitted, generate from PR description.
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

### Phase 2: Quality Enforcement

**MANDATORY - never skip.**

Run sequentially, stop on first failure:

```bash
pants fmt ::
pants fix ::
pants lint --changed-since=origin/{base_branch}
pants check --changed-since=origin/{base_branch}
pants test --changed-since=origin/{base_branch} --changed-dependents=transitive
```

- If `fmt` or `fix` produce changes, stage them automatically
- If `lint` or `check` fails, fix the issues and re-run
- If `test` fails, report failures and **stop** - ask user how to proceed
- After all pass, continue to next phase

### Phase 3: Commit

1. **Stage changes**
   - `git add` specific files (avoid `-A` to prevent accidental inclusion of secrets)
   - Never stage `.env`, credentials, or other sensitive files

2. **Generate commit message**
   - Use conventional commit style: `type(scope): description`
   - Types: `fix`, `feat`, `refactor`, `test`, `doc`, `ci`, `chore`, `perf`
   - Include JIRA key in description if available: `fix(manager): resolve session cleanup (BA-1234)`
   - Keep first line under 80 characters
   - Add detailed body if multiple significant changes

3. **Create commit**
   - Present draft message to user for approval
   - Commit with approved message

### Phase 4: PR Creation

1. **Push branch**
   - `git push -u origin {branch_name}`

2. **Generate PR content**
   - **Title**: Conventional commit style with JIRA key prefix
     - Format: `type(scope): description (BA-XXXX)`
     - Example: `fix(manager): resolve session cleanup race condition (BA-1234)`
   - **Body**: Use this template:

   ```markdown
   ## Summary
   <1-3 bullet points describing what changed and why>

   ## Test plan
   - [ ] <test items>

   Resolves BA-XXXX
   ```

3. **Create PR**
   ```bash
   gh pr create --title "..." --body "..."
   ```

4. **Extract PR number** from `gh pr create` output

### Phase 5: Changelog (News Fragment)

1. **Determine changelog type** (if not provided)
   - Map from PR content:
     - New functionality → `feature`
     - Bug fix → `fix`
     - Performance/refactoring → `enhance`
     - Breaking API change → `breaking`
     - Test-only change → `test`
     - Documentation → `doc`
     - Dependency update → `deps`

   Valid types (from `pyproject.toml`):
   | Type | Category |
   |------|----------|
   | `breaking` | Breaking Changes |
   | `feature` | Features |
   | `enhance` | Improvements |
   | `deprecation` | Deprecations |
   | `fix` | Fixes |
   | `doc` | Documentation Updates |
   | `deps` | External Dependency Updates |
   | `misc` | Miscellaneous |
   | `test` | Test Updates |

2. **Generate changelog message** (if not provided)
   - Single-line English sentence
   - Imperative/commanding form: "Fix XXX", "Add YYY", "Support ZZZ"
   - Or complete sentence: "Now it does ZZZ"
   - Focus on what the change means to users/developers, not implementation details

3. **Create file**
   - Path: `changes/{pr_number}.{changelog_type}.md`
   - Content: single-line changelog message
   - Show draft to user for approval

4. **Commit and push**
   ```bash
   git add changes/{pr_number}.{changelog_type}.md
   git commit -m "changelog: add news fragment for PR #{pr_number}"
   git push
   ```

### Phase 6: Summary

Report final status:

```
Submission Complete

  PR:        #{pr_number} - {title}
  URL:       https://github.com/lablup/backend.ai/pull/{pr_number}
  JIRA:      BA-XXXX
  Branch:    {branch_name}
  Changelog: changes/{pr_number}.{changelog_type}.md

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
2. Create new issue: /jira-issue
3. Continue without JIRA key (not recommended)
```

## Examples

### Basic usage (auto-detect everything)
```
User: /submit
Agent: [Detects BA-1234 from branch, runs quality checks, commits, creates PR, generates changelog]
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

### After jira-issue skill
```
User: /jira-issue → creates BA-9999
User: [implements feature]
User: /submit BA-9999
Agent: [Full submission with BA-9999 reference]
```

## Related Skills

- `/jira-issue` - Create JIRA issue before starting work
- `/tdd-guide` - TDD workflow (run before /submit)

## Implementation Notes

- Quality checks use `--changed-since=origin/{base_branch}` to cover all PR changes, not just the last commit
- Changelog follows [towncrier](https://github.com/twisted/towncrier) format configured in `pyproject.toml`
- PR number is only available after `gh pr create`, so changelog is always a second commit
- A single PR may have multiple news fragments (e.g., both `feature` and `fix`)
- News fragment content should be a single-line sentence per `changes/README.md` guidelines
