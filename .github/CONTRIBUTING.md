# Contribution Guides for Backend.AI

## CLA (Contributor License Agreement)

A first code patch or documentation update requires explicit consent to follow the CLA.

Backend.AI is covered by [the Lablup
CLA](https://gist.github.com/achimnol/f53015b30af7b045fdd01c0cc3b18c96), like other
open source projects managed by Lablup Inc.


## Versioning Scheme

Backend.AI uses a sprint-based versioning system.

**Version Number Format**: `{Year}.{Sprint}.{Patch}`

See these examples:
- `25.16.0`: Official release of the 16th sprint in 2025
- `25.16.1`: First patch release for the 25.16.0 version

**LTS (Long-Term Support) versions**:
- Sprint releases in March and September are supported for 1 year
- See: the `25.6` release (released in March 2025) is supported as LTS until March 2026

Before you contribute, determine the target branch.
See [our versioning scheme
document](https://docs.backend.ai/en/latest/dev/version-management-and-upgrades.html#version-numbering)
for how we name branches and tags.

**Branch and tag naming conventions**:
- **Major release branches**: `YY.SS` (for example, `25.16`)
  - These branches are created when a sprint release is designated as an LTS version
  - They serve LTS backporting and maintenance
  - Patch releases (for example, `25.16.1`, `25.16.2`) are created from these branches
- **Patch release tags**: `YY.SS.P` (for example, `25.16.0`, `25.16.1`)
  - Tags are created for each patch release on the corresponding branch
  - If there are backported changes for a sprint, patch release tags are created from the sprint branch
- **`main` branch**: Main development branch, the default recommended branch for creating feature branches

Our branch naming sits between
[GitFlow](https://danielkummer.github.io/git-flow-cheatsheet/index.html)
and [GitHub Flow](https://guides.github.com/introduction/flow/); we use branch names
prefixed with `feature/`, `hotfix/` and `maintenance/`.
We do not keep a separate "develop" branch and use PRs instead to get the
advantages of both without the complication that hurts agility.


## Issue Management

**Issue registration location**:
- **Open Source Contributions**: [GitHub Issues](https://github.com/lablup/backend.ai/issues)
- **Internal Development**: Lablup JIRA (BA-XXXX)
  - Internal issues should be created in JIRA
  - JIRA mirrors its issues to GitHub Issues automatically for visibility

### Feature Issue Guidelines

**For small features**:
- Simple features that can be completed in a single PR may only require a **Story issue**
  - "Single PR" here means a reasonably-sized PR (200-400 lines); large PRs over 500 lines should be split into multiple PRs
- Even if a feature spans just **2-3 PRs**, we recommend the Epic/Story structure

**Recommended Epic/Story structure**:

We recommend organizing features with **Epics** and **Story** issues:

1. **Create an Epic**
   - Write an Epic issue for the larger feature
   - The Epic should specify the overall goals and scope

2. **Break into Stories**
   - Decompose the Epic into concrete Stories
   - Each Story should be independently implementable and testable
   - Stories should be completable within 1-2 sprints

### Bug Report Requirements

Bug reports **must** include the following information:

- **Version**: The Backend.AI version where the issue occurred (for example, 25.16.0)
- **Reproduction Steps**: Specific steps to reproduce the issue
- **Expected Result**: What should happen in normal operation
- **Actual Result**: What actually happened
- **Frequency**: Always occurs or intermittent (for example, 100%, 50%, 10%)
- **Environment**: OS, browser, deployment environment and others (if applicable)

Two issue templates exist for bug reports and feature requests, but they are guidelines.
Using them is not mandatory, but try to provide self-sufficient information to track down your
problem or idea.

### Bug Fix PR Requirements

Bug fix PRs **must** include:

- **Test Code**: Add test cases that reproduce the bug and verify the fix
  - The tests should fail before the fix and pass after it
  - They are essential for preventing regressions

**For hotfixes**:
- If urgent deployment is required, merging without test code is acceptable
- Even then, you **must create a follow-up issue** to add test code and proceed with it


## Pull Request Guidelines

## PR Workflow

Follow this workflow when submitting a PR:

### 1. Create an Issue (Recommended)

We recommend creating a related issue before submitting a PR.

- **Internal Development**: Create an issue in Lablup JIRA (BA-XXXX)
- **Open Source Contributions**: Create a GitHub Issue
- Clearly define the problem and proposed solution in the issue
- For large work, discuss in the issue before starting implementation

### 2. Create Branch and Implement

With "write" access to the repositories, create a feature branch in
the original repository.
Otherwise, fork the repository and create a feature branch in your GitHub account.

**Branch Naming Convention** (recommended):

These conventions are not strictly enforced but improve clarity and organization:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring

For example, `feature/add-pr-guidelines` and `fix/session-memory-leak`.

### 3. Create PR

When implementation is complete, create a pull request.

**Tip**: For work still in progress, create a draft PR.

## PR Title Format

PR titles must follow this format:

### For JIRA Issues (Internal Development)
```
<type>(BA-XXXX): Summary of changes

Examples:
feat(BA-2814): Add comprehensive PR guidelines
fix(BA-2790): Resolve memory leak in session scheduler
docs(BA-2800): Add component architecture documentation
```

### For GitHub Issues Only (Open Source)
```
<type>: Summary of changes

Examples:
feat: Add user profile management
fix: Resolve race condition in agent registration
```

**Note**: For open source contributions, do not include issue numbers in the PR title.
Link the issue in the PR description with the `resolves #1234` format.

### Type list
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `refactor`: Code refactoring (no functionality change)
- `test`: Test additions and changes
- `chore`: Build, configuration, dependency updates and others
- `perf`: Performance improvements
- `style`: Code formatting (no logic changes)

## PR Description

Backend.AI consists of many sub-projects in separate GitHub repositories,
so resolving a single issue often requires multiple PRs in multiple repositories.
For an integrated view, we recommend filing an issue in the meta repository and
mention it as `refs lablup/backend.ai#xxx` in every related pull request in the
individual sub-projects.

Use the PR template to include the following:

```markdown
resolves #<issue-number> (BA-<jira-number>)

## Changes
- Specific description of what was changed
- Rationale for implementation approach
```

## Changelog Fragment

A user-facing change adds `changes/unreleased/<issue key>.<kind>.md` with a short description for users.
Kinds, format and the check: `changes/README.md`.

## PR Size Guidelines

**Ideal size**
- Ideal: 200-400 lines changed
- Size reviewable in 30 minutes

**Large PRs (over 500 lines) must be split**

PRs over 500 lines cause the following issues:
- **Exponential review time**: Review time increases exponentially
- **Degraded review quality**: Detailed reviews become difficult, reducing bug detection rates
- **Bottlenecks**: Excessive burden on a single reviewer

**If you have changes over 500 lines**:
- **Must** split them into multiple smaller PRs
- Each PR should be independently reviewable and mergeable
- If a large PR is unavoidable, discuss with the team in advance

**Exceptions for large PRs**:
- Simple replace operations (for example, renaming across the codebase)
- Auto-formatting changes (for example, running code formatters)
- **Important**: These operations must be isolated in a dedicated PR
- **Do not** mix these operations with other implementation changes

**Separate refactoring**
- Separate structural changes (refactoring) and feature additions into different PRs
- Tidy First principle: Structural changes first, feature additions later

## PR Structure Strategy

### Flat PRs Recommended (Avoid Stack PRs)

**Problems with stack PRs**:
- Delays in one PR cause delays in all dependent PRs (bottleneck)
- Changes needed in the base PR affect all dependent PRs
- Fixed review priority reduces flexibility
- Enforced merge order prevents parallel work
- **Squash merge conflicts**: Because we use squash merge, stack PRs create serious issues:
  - Merging from top to bottom: All commits get squashed into one, losing the intended PR separation
  - Merging from bottom to top: Each merge requires time-consuming rebases on all dependent PRs

**Advantages of flat PRs**:
- Each PR can be reviewed and merged independently
- Multiple PRs can be worked on in parallel
- Merge order can be flexibly adjusted based on priority
- Delays in one PR do not affect other PRs

For large work:

1. **Merge foundational work first**
   - Common types, utilities, infrastructure changes and others
   - Base code that other PRs depend on

2. **Create implementation PRs in a flat structure**
   - Independent PR for each feature or module
   - Designed with no interdependencies
   - Reviewable and mergeable in parallel

**Example:**
```
Wrong approach (Stack):
PR1 (base) ← PR2 (feature A) ← PR3 (feature B) ← PR4 (feature C)
→ Changes to PR1 affect all PRs, causing bottleneck

Correct approach (Flat):
PR1 (base) merged
  ├── PR2 (feature A)
  ├── PR3 (feature B)
  └── PR4 (feature C)
→ Each can be reviewed/merged independently
```

**When stack PRs are necessary**
- Allow stack PRs only when features have strong interdependencies
- In that case, adjust review priority so the base PR can be merged quickly

## Reviewer Assignment

### Reviewer assignment principles

Assign the following as reviewers:

1. **Previous contributors**: Developers who previously wrote or modified the code
2. **Maintainers**: Maintainers of the component or module
3. **Domain experts**: Domain experts for complex changes

### How to find previous contributors

Commands to find previous contributors to the code:

```bash
# Find recent contributors to a file
git log --follow <file-path>

# Find who worked on specific lines
git blame <file-path>

# Find major contributors to a specific directory
git log --format='%an' <directory> | sort | uniq -c | sort -rn | head -5
```

**Minimum requirements**
- At least one approval is required
- Tag domain experts for complex changes

## Commit Guidelines

**Commit Message Format**
```
<type>(<scope>): Commit title

Detailed description (optional)
```

**Commit rules**

Squash merge means individual commit messages can be written relatively freely.

At review time, we recommend **separating commits into logical units** so changes are easier to understand:
- Separate feature additions and refactoring into different commits
- Keep each commit in a buildable state
- State what changed in the commit message

Pay more attention to the PR title: it becomes the final commit message on squash merge.

## Draft PR Usage

**When to use a draft PR**:
- When work is in progress but early feedback is needed
- When CI checks are needed
- When you want to share the architecture or design direction in advance

**What a draft PR means**:
- Draft status means "work still in progress"
- Draft PRs without assigned reviewers may not be reviewed
- If feedback is needed, assign reviewers to the draft PR explicitly

**When to convert to ready for review**:
- Removing draft status signals that **implementation is complete**
- Reviewers then review the PR
- Checklist before converting:
  - [ ] All CI checks pass
  - [ ] Self-review completed
  - [ ] Documentation and tests written

## Pre-Review Checklist

### 1. Self-review
- [ ] Reviewed all changes yourself
- [ ] Removed debug code and unnecessary comments
- [ ] Checked formatting and linting

### 2. CI/CD checks
The git hook (pre-commit) runs the low-cost checks. When a hook or CI fails, find the cause in its output or the failed job's log and fix it.

- [ ] All lint passes
- [ ] Related tests pass

### 3. Conflict resolution

Resolve conflicts with either `rebase` or `merge`:

**Using Rebase:**
```bash
# Update main branch to latest state
git fetch origin
git rebase origin/main

# After resolving conflicts
git push --force-with-lease
```

**Using Merge:**
```bash
# Update main branch to latest state
git fetch origin
git merge origin/main

# After resolving conflicts
git push
```

**Conflict resolution checklist**:
- [ ] Conflicts with main branch resolved
- [ ] All conflicts resolved
- [ ] Tests re-run after resolution

## Review Process

### PR description writing principles

**Feature description**:
- Write detailed feature descriptions in the **issue**
- Keep the PR description concise but reference the issue

**Implementation details**:
- Focus on **implementation details** in the PR description
- Add code comments or PR comments for complex logic
- Specify design decisions or trade-offs

**Reference**: See the [PR Description](#pr-description) section.

### As the author

1. **Provide clear descriptions**
   - Provide sufficient context in the PR description
   - Add code comments for complex logic

2. **Respond to feedback**
   - Respond to all comments
   - When applying review feedback, add changes as new commits to preserve review history
   - Avoid force-pushing after reviews, because it makes it difficult for reviewers to see what changed
   - Request re-review after changes are complete

### As a reviewer

**Review timing**:
- Review PRs marked "Ready for Review" as quickly as possible
- Target: Complete the initial review within 48 hours
- Prioritize PRs that are blocking other work

1. **Constructive feedback**
   - Provide specific, actionable suggestions
   - Explain why the changes are needed
   - Provide positive feedback too

2. **Complete the review**
   - **Approve**: Ready to merge
   - **Request Changes**: Needs modification before re-review
   - **Comment**: Providing opinions only

## Troubleshooting

### CI failures
- Check GitHub Actions logs
- Reproduce the same command locally
- Request help through a PR comment if unresolved

### Review delays
- Remind the reviewer through Teams or a GitHub comment
- Escalate to the team lead if urgent

## Mandatory Requirements

Ensure the following:

* Mandatory:
  - Code naming and style must follow our editorconfig settings and stay consistent with the existing codebase. Watch the lint and typecheck results generated automatically for every push and pull request.
  - The contributor must sign the CLA.
* Highly recommended:
  - Provide one or more test cases that yield different results before and after the
    contribution.
  - Include patches for documentation or attach a link to a follow-up PR that updates
    related documents.
