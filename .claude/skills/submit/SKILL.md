---
name: submit
description: Complete submission workflow: quality checks, commit, PR creation, changelog generation, and final push. Use after finishing implementation work.
tags:
  - submit
  - pr
  - quality
  - changelog
---

# Submit workflow

Run the post-implementation submission pipeline: quality enforcement, commit, PR creation, changelog and push.

## Parameters

- **jira_key** (optional): issue key, for example `BA-1234`. Detected from the branch name when the pattern `BA-\d+` exists.
- **changelog_type** (optional): one of `breaking`, `feature`, `enhance`, `deprecation`, `fix`, `doc`, `deps`, `misc`, `test`. When omitted, infer it from the most significant change.
- **changelog_message** (optional): one-line English summary for the changelog fragment. When omitted, generate it from the PR description.
- **base_branch** (optional): target branch for the PR. Defaults to `main`.

## Workflow

### Phase 1: Pre-flight

1. **Detect the issue key**
   - Check whether the user provided `jira_key`
   - Otherwise extract it from the current branch name (pattern `BA-\d+`)
   - When not found, ask the user

2. **Review changes**
   - `git status` to see all changed and untracked files
   - `git diff` and `git diff --staged` to review the content
   - `git log {base_branch}..HEAD` to see the existing commits on the branch
   - Summarize the changes to the user before proceeding

### Phase 2: Quality enforcement

**Do not skip this phase.**

Run these sequentially and stop on the first failure:

```bash
pants fmt ::
pants fix ::
pants lint --changed-since=origin/{base_branch}
```

- When `fmt` or `fix` produce changes, stage them automatically
- When `lint` fails, fix the issues and run it again
- After all pass, continue to the next phase

Type checking (`pants check`) and tests (`pants test`) are enforced by CI only. Do not run them locally; they consume excessive resources when multiple workers run concurrently.

### Phase 3: Commit

1. **Stage changes**
   - `git add` specific files. Avoid `-A` so secrets are not included by accident
   - Do not stage `.env`, credentials or other sensitive files

2. **Generate the commit message**
   - Use conventional commit style: `type(BA-XXXX): description`
   - Types: `fix`, `feat`, `refactor`, `test`, `doc`, `ci`, `chore`, `perf`
   - **When an issue key is available, always use it as the conventional commit scope. Do not use component names such as `manager`, `client` or `client-sdk` as the scope.**
   - Example: `fix(BA-1234): resolve session cleanup race condition`
   - Keep the first line under 80 characters
   - Add a detailed body when there are multiple significant changes

3. **Create the commit**
   - Present the draft message to the user for approval
   - Commit with the approved message

### Phase 4: PR creation

1. **Push the branch**
   - `git push -u origin {branch_name}`

2. **Generate the PR content**
   - **Title** - conventional commit style with the issue key as scope
     - Format: `type(BA-XXXX): description`
     - Example: `fix(BA-1234): resolve session cleanup race condition`
     - See `changes/KNOWLEDGE.md` for the category-to-prefix and changelog-type mapping, including same-release fixes (`chore`, not `fix`)
   - **Body** - use this template:

   ```markdown
   ## Summary
   <1-3 bullet points describing what changed and why>

   ## Test plan
   - [ ] <test items>

   Resolves BA-XXXX
   ```

   - **Do not mention a JIRA issue other than the assigned one** in the title or the body.

3. **Decide the backport targets** before creating the PR, because the trailer lives in the PR body

   Backporting is automatic. There is no milestone to set; the target release branches are decided from the PR title prefix, the PR body and the labels.

   The title prefix picks the default, and a `Backport:` line in the PR body replaces it.

   | Situation | What to do |
   |---|---|
   | `fix:` PR going to every maintained version | Nothing |
   | Any PR going to particular versions | Add `Backport: 26.8, 26.4` to the PR body, comma- or space-separated |
   | `fix:` PR that must not be backported | Add `Backport: none` to the PR body |
   | Non-`fix:` PR that stays on `main` | Nothing |
   | A target realized only after the merge | Comment `/backport <version>` on the merged PR |

   - Valid versions are exactly the entries of `.github/maintained-versions.yml`. Read that file instead of guessing. A trailer naming anything else fails the backport job and backports nothing, so get it right or leave the trailer out.
   - Writing a `Backport:` trailer is a release decision. Ask the user before adding one.

4. **Create the PR**

   ```bash
   gh pr create --title "..." --body "..."
   ```

5. **Extract the PR number** from the `gh pr create` output

### Phase 5: Changelog fragment

1. **Determine the changelog type** when not provided. See `changes/KNOWLEDGE.md` for the valid types and the category mapping.

2. **Generate the changelog message** when not provided
   - Single-line English sentence
   - Imperative form: "Fix XXX", "Add YYY", "Support ZZZ", or a complete sentence such as "Now it does ZZZ"
   - Focus on what the change means to users and developers, not implementation details

3. **Create the file**
   - Path: `changes/{pr_number}.{changelog_type}.md`
   - Content: the single-line changelog message
   - Show the draft to the user for approval

4. **Commit and push**

   ```bash
   git add changes/{pr_number}.{changelog_type}.md
   git commit -m "changelog: add changelog fragment for PR #{pr_number}"
   git push
   ```

### Phase 6: Summary

Report the final status:

```
Submission Complete

  PR:        #{pr_number} - {title}
  URL:       https://github.com/lablup/backend.ai/pull/{pr_number}
  Issue:     BA-XXXX
  Branch:    {branch_name}
  Changelog: changes/{pr_number}.{changelog_type}.md

Quality checks: All passed
Commits: {count} commit(s)
```

## Error handling

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

### Branch has no issue key

```
No issue key found.

Options:
1. Provide the issue key: /submit BA-1234
2. Continue without an issue key (not recommended)
```

## Examples

Basic usage, with everything detected automatically:

```
User: /submit
Agent: [Detects BA-1234 from branch, runs quality checks, commits, creates PR, generates changelog]
```

With an explicit issue key:

```
User: /submit BA-5678
Agent: [Uses BA-5678, runs full workflow]
```

With all parameters:

```
User: /submit BA-5678 --type=fix --message="Fix session cleanup race condition when agent disconnects"
Agent: [Uses provided parameters, runs full workflow]
```

## Related documents

- `/test-guide` - Scenario-first testing, run before `/submit`

## Implementation notes

- Local quality checks (`fmt`, `fix`, `lint`) use `--changed-since=origin/{base_branch}` to cover all PR changes, not only the last commit
- The changelog follows the [towncrier](https://github.com/twisted/towncrier) format configured in `pyproject.toml`
- The PR number is available only after `gh pr create`, so the changelog is always a second commit
- A single PR may have multiple changelog fragments, for example both `feature` and `fix`
- The changelog fragment is a single-line sentence, per `changes/README.md`
