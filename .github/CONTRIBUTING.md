Contribution Guides for Backend.AI
==================================

CLA (Contributor License Agreement)
-----------------------------------

If you contribute code patches and documentation updates for the first time, you must
make an explicit consent to follow our CLA.

Backend.AI is covered by [the Lablup
CLA](https://gist.github.com/achimnol/f53015b30af7b045fdd01c0cc3b18c96) like other
open source projects managed by Lablup Inc.


Versioning Scheme
-----------------

Backend.AI uses a sprint-based versioning system.

**Version Number Format**: `{Year}.{Sprint}.{Patch}`

Examples:
- `25.16.0`: Official release of the 16th sprint in 2025
- `25.16.1`: First patch release for the 25.16.0 version

**LTS (Long-Term Support) Versions**:
- Sprint releases in March and September are supported for 1 year
- Example: The `25.6` release (released in March 2025) is supported as LTS until March 2026

Before you make a contribution, ensure which branch is the target you want to
contribute to.
Please take a look at [our versioning scheme
document](https://docs.backend.ai/en/latest/dev/version-management-and-upgrades.html#version-numbering)
to understand how we name branches and tags.

**Branch and Tag Naming Conventions**:
- **Major release branches**: `YY.SS` (e.g., `25.16`)
  - These branches are created when a sprint release is designated as an LTS version
  - Used for LTS backporting and maintenance
  - Patch releases (e.g., `25.16.1`, `25.16.2`) are created from these branches
- **Patch release tags**: `YY.SS.P` (e.g., `25.16.0`, `25.16.1`)
  - Tags are created for each patch release on the corresponding branch
  - If there are backported changes for a sprint, patch release tags are created from the sprint branch
- **`main` branch**: Main development branch, the default recommended branch for creating feature branches

Our branch naming lies between
[GitFlow](https://danielkummer.github.io/git-flow-cheatsheet/index.html)
(we use `feature/`, `hotfix/`, `maintenance/` prefixed branch names) and
[GitHub Flow](https://guides.github.com/introduction/flow/).
We don't use a separate "develop" branch and just use PRs to take advantages
from both without complication that hurts agility.


Issue Management
----------------

**Issue Registration Location**:
- **Open Source Contributions**: [GitHub Issues](https://github.com/lablup/backend.ai/issues)
- **Internal Development**: Lablup JIRA (BA-XXXX)
  - Internal issues should be created in JIRA
  - JIRA issues are automatically mirrored to GitHub Issues for visibility

### Feature Issue Guidelines

**For Small Features**:
- Simple features that can be completed in a single PR may only require a **Story issue**
  - "Single PR" here means a reasonably-sized PR (200-400 lines); large PRs over 500 lines should be split into multiple PRs
- Even if a feature spans just **2-3 PRs**, we recommend using the Epic/Story structure

**Recommended Epic/Story Structure**:

We recommend organizing features using **Epics** with **Story** issues:

1. **Create an Epic**
   - Write an Epic issue for the larger feature
   - The Epic should specify the overall goals and scope

2. **Break Down into Stories**
   - Decompose the Epic into concrete Stories
   - Each Story should be independently implementable and testable
   - Stories should be completable within 1-2 sprints

### Bug Report Requirements

Bug reports **must** include the following information:

- **Version**: The Backend.AI version where the issue occurred (e.g., 25.16.0)
- **Reproduction Steps**: Specific steps to reproduce the issue
- **Expected Result**: What should happen in normal operation
- **Actual Result**: What actually happened
- **Frequency**: Does it always occur, or is it intermittent? (e.g., 100%, 50%, 10%)
- **Environment**: OS, browser, deployment environment, etc. (if applicable)

We have two issue templates for bug reports and feature requests, but they are just guidelines.
It is not mandatory to use the templates, but please try to provide self-sufficient
information to track down your problems and/or ideas.

### Bug Fix PR Requirements

Bug fix PRs **must** include:

- **Test Code**: Add test cases that reproduce the bug and verify the fix
  - Tests should fail before the fix and pass after
  - Essential for preventing regressions

**For Hotfixes**:
- If urgent deployment is required, merging without test code is acceptable
- However, you **must create a follow-up issue** to add test code and proceed with it


Pull Request Guidelines
-----------------------

## PR Workflow

Follow this workflow when submitting a PR:

### 1. Create an Issue (Recommended)

We recommend creating a related issue before submitting a PR.

- **Internal Development**: Create an issue in Lablup JIRA (BA-XXXX)
- **Open Source Contributions**: Create a GitHub Issue
- Clearly define the problem and proposed solution in the issue
- For large work, discuss in the issue before starting implementation

### 2. Create Branch and Implement

For those who have "write" access to the repositories, create a feature branch inside
the original repository to begin work with.
Otherwise, fork and create a feature branch in your GitHub account.

**Branch Naming Convention** (Recommended):

While not strictly enforced, following these conventions improves clarity and organization:

- `feature/` - New feature additions
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring

Examples: `feature/add-pr-guidelines`, `fix/session-memory-leak`

### 3. Create PR

Once implementation is complete, create a Pull Request.
Once the PR number is assigned, proceed to the next step.

**Tip**: If work is still in progress, you can create a Draft PR.

### 4. Write Changelog Fragment (Towncrier)

After the PR is created and you have the **PR number**, write a changelog fragment.
Backend.AI uses [Towncrier](https://towncrier.readthedocs.io/) to automatically generate release notes.

**Important**: These fragments are used to generate [CHANGELOG.md](/CHANGELOG.md) for each release.
Write clearly and concisely about what you changed and its impact, as this will be read by users and other developers.

**Create Fragment File**:
```bash
# Create a file in the changes/ directory
# Format: {PR#}.{type}.md
# Examples: 6424.feature.md, 6469.fix.md
```

**Fragment Types**:
- `breaking` - Breaking changes
- `feature` - New features
- `enhance` - Enhancements to existing features (refactoring, optimization, performance improvements, etc.)
- `deprecation` - Deprecation notices
- `fix` - Bug fixes
- `doc` - Documentation updates
- `deps` - External dependency updates
- `misc` - Other changes
- `test` - Test updates

**Fragment Writing Guidelines**:
- Write changes **concisely and clearly** in one sentence
- Focus on **user-facing changes** rather than technical details
- Include **Before/After situations** or **key changes** if necessary

**Examples**:

```bash
# changes/6469.fix.md
Resolve deadlock occurring due to incorrect use of semaphore in specific image rescan scenarios

# changes/6449.doc.md
Add comprehensive README documentation for Actions, Services, and Repositories layers in the manager, covering architecture patterns, design principles, and best practices for each layer.
```

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
Instead, link the issue in the PR description using `resolves #1234` format.

### Type List
- `feat`: New feature additions
- `fix`: Bug fixes
- `docs`: Documentation changes
- `refactor`: Code refactoring (no functionality change)
- `test`: Test additions/modifications
- `chore`: Build, configuration, dependency updates, etc.
- `perf`: Performance improvements
- `style`: Code formatting (no logic changes)

## PR Description

Since Backend.AI consists of many sub-projects in separate GitHub repositories,
it is often required to make multiple PRs to multiple repositories to resolve a
single issue.
To get an integrated view, we recommend to pile an issue in the meta repository and
mention it like `refs lablup/backend.ai#xxx` in all related pull requests in
individual sub-projects.

Use the PR template to include the following:

```markdown
resolves #<issue-number> (BA-<jira-number>)

## Changes
- Specific description of what was changed
- Rationale for implementation approach
```

## PR Size Guidelines

**Ideal Size**
- Ideal: 200-400 lines changed
- Size reviewable in 30 minutes

**⚠️ Large PRs (>500 lines) - Must Be Split**

PRs over 500 lines cause the following issues:
- **Exponential review time**: Review time increases exponentially
- **Degraded review quality**: Difficult to conduct detailed reviews, reducing bug detection rates
- **Bottlenecks**: Excessive burden on a single reviewer

**If you have changes over 500 lines**:
- **Must** split into multiple smaller PRs
- Each PR should be independently reviewable and mergeable
- If a large PR is unavoidable, discuss with the team in advance

**Exceptions for Large PRs**:
- Simple replace operations (e.g., renaming across codebase)
- Auto-formatting changes (e.g., running code formatters)
- **Important**: These operations must be isolated in a dedicated PR
- **Never** mix these operations with other implementation changes

**Separate Refactoring**
- Separate structural changes (refactoring) and feature additions into different PRs
- Tidy First principle: Structural changes first, feature additions later

## PR Structure Strategy

### Flat PRs Recommended (Avoid Stack PRs)

**Problems with Stack PRs**:
- Delays in one PR cause delays in all dependent PRs (bottleneck)
- Changes needed in the base PR affect all dependent PRs
- Fixed review priority reduces flexibility
- Enforced merge order prevents parallel work
- **Squash Merge Conflicts**: Since we use squash merge, Stack PRs create serious issues:
  - Merging from top to bottom: All commits get squashed into one, losing the intended PR separation
  - Merging from bottom to top: Each merge requires time-consuming rebases on all dependent PRs

**Advantages of Flat PRs**:
- Each PR can be reviewed and merged independently
- Multiple PRs can be worked on in parallel
- Merge order can be flexibly adjusted based on priority
- Delays in one PR don't affect other PRs

For large work:

1. **Merge foundational work first**
   - Common types, utilities, infrastructure changes, etc.
   - Base code that other PRs will depend on

2. **Create implementation PRs in a flat structure**
   - Independent PR for each feature/module
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

**When Stack PRs Are Necessary**
- Only allow Stack PRs when there are strong interdependencies between features
- In this case, adjust review priority so the base PR can be merged quickly

## Reviewer Assignment

### Reviewer Assignment Principles

Assign the following as reviewers:

1. **Previous Contributors**: Developers who previously wrote or modified the code
2. **Maintainers**: Maintainers of the component/module
3. **Domain Experts**: Domain experts for complex changes

### How to Find Previous Contributors

Commands to find previous contributors to the code:

```bash
# Find recent contributors to a file
git log --follow <file-path>

# Find who worked on specific lines
git blame <file-path>

# Find major contributors to a specific directory
git log --format='%an' <directory> | sort | uniq -c | sort -rn | head -5
```

**Minimum Requirements**
- At least 1 approval required
- Tag domain experts for complex changes

## Commit Guidelines

**Commit Message Format**
```
<type>(<scope>): Commit title

Detailed description (optional)
```

**Commit Rules**

Since we use squash merge when merging PRs, individual commit messages can be written relatively freely.

However, **at review time**, we recommend **separating commits into logical units** to make changes easier to understand:
- Separate feature additions and refactoring into different commits
- Keep each commit in a buildable state
- Clearly express "what" was changed in the commit message

Pay more attention to the PR title, as it becomes the final commit message when squash merged.

## Draft PR Usage

**When to Use Draft PR**:
- When work is in progress but early feedback is needed
- When CI checks are needed
- When you want to share architecture/design direction in advance

**What Draft PR Means**:
- Draft status means "work still in progress"
- Draft PRs without reviewers assigned may not be reviewed
- If feedback is needed, explicitly assign reviewers to the Draft PR

**When to Convert to Ready for Review**:
- Removing Draft status signals that **implementation is complete**
- At this point, reviewers should review the PR
- Checklist before converting:
  - [ ] All CI checks pass
  - [ ] Self-review completed
  - [ ] Changelog fragment written
  - [ ] Documentation and tests written

## Pre-Review Checklist

### 1. Self-Review
- [ ] Reviewed all changes yourself
- [ ] Removed debug code and unnecessary comments
- [ ] Checked formatting and linting

### 2. CI/CD Checks
```bash
# Run locally first
pants lint ::
pants check ::
pants test <changed-tests>
```

- [ ] All lint passes
- [ ] All typechecks pass
- [ ] Related tests pass

### 3. Conflict Resolution

You can resolve conflicts using either `rebase` or `merge`:

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

**Conflict Resolution Checklist**:
- [ ] Conflicts with main branch resolved
- [ ] All conflicts resolved
- [ ] Tests re-run after resolution

## Review Process

### PR Description Writing Principles

**Feature Description**:
- Write detailed feature descriptions in the **issue**
- Keep PR description concise but reference the issue

**Implementation Details**:
- Focus on **implementation details** in the PR description
- Add code comments or PR comments for complex logic
- Specify design decisions or trade-offs

**Reference**: See the [PR Description](#pr-description) section.

### As the Author

1. **Provide Clear Descriptions**
   - Provide sufficient context in the PR description
   - Add code comments for complex logic

2. **Respond to Feedback**
   - Respond to all comments
   - When applying feedback from reviews, add changes as new commits to preserve review history
   - Avoid force-pushing after receiving reviews, as it makes it difficult for reviewers to see what changed
   - Request re-review after changes are complete

### As a Reviewer

**Review Timing**:
- PRs marked as "Ready for Review" should be reviewed as quickly as possible
- Target: Complete initial review within 48 hours
- Prioritize PRs that are blocking other work

1. **Constructive Feedback**
   - Provide specific, actionable suggestions
   - Explain "why" changes are needed
   - Also provide positive feedback

2. **Complete Review**
   - **Approve**: Ready to merge
   - **Request Changes**: Needs modification before re-review
   - **Comment**: Just providing opinions

## Troubleshooting

### CI Failures
- Check GitHub Actions logs
- Reproduce the same command locally
- Request help via PR comment if unresolved

### Review Delays
- Remind reviewer via Teams or GitHub comment
- Escalate to team lead if urgent

## Mandatory Requirements

Please ensure the following:

* Mandatory:
  - The code's naming and styles must follow our flake8 and editorconfig settings,
    with honors to existing codebase.  Please keep eyes on the lint/typecheck results
    automatically generated for every push and pull request.
  - The contributor must sign the CLA.
* Highly recommended:
  - Provide one or more test cases that yield different results before/after applying
    the contribution.
  - Include patches for documentation or attach a link to a follow-up PR to update
    related documents.


Documentation
-------------

There are two documentations in this project.

* [API and server-side docs](https://docs.backend.ai)
  - Source of documentation: https://github.com/lablup/backend.ai/tree/master/docs
* [Python client SDK docs](https://client-py.docs.backend.ai)
  - Source of documentation: https://github.com/lablup/backend.ai-client-py/tree/master/docs
* Javascript client SDK docs
  - It uses JSDoc-style comments to generate documentation.
  - Source: https://github.com/lablup/backend.ai-client-js/

To build the documentation, prepare a Python environment for the cloned repositories
and run:
```console
$ pip install -U -e '.[docs]'
$ cd docs
$ make html
$ open _build/html/index.html
```

We use [Sphinx](http://sphinx-doc.org/) to write the documentation, so please be
familiar with
[RestructuredText](http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
and Sphinx's common and cross-reference directives.

Since `docs` directories are part of the project repositories, they also follow
the X.Y version branch and X.Y.Z release tag policy.

Send pull requests to add/modify documentation contents and fix typos.
To distinguish documentation-related PRs easily, please prefix the PR title with
"docs:" or apply the "docs" label.

### Coding Style for Docs

We wrap the sentences by 75 characters (configured via editorconfig) but always break
the line after the end of sentences (periods).
The purpose of this extra convention is to keep the translations in the sentence
level instead of paragraphs.

For example:
```text
This is the first long long ... long (75 chars here) long sentence.
This is the second long long ... long (75 chars here) long sentence.
```
should be
```text
This is the first long long ... long
long sentence.
This is the second long long ... long
long sentence.
```
but *NOT*
```text
This is the first long long long long ... long
long sentence.  This is the second long ... long
long ... long sentence.
```


Translation
-----------

We write the docs in English first, and then translate it to other languages such as
Korean.

Currently only the Python client SDK docs has [the Korean
translation](https://client-py.docs.backend.ai/ko/latest/).


### How to add a new translation for a new language

Add a new project in readthedocs.org with the "-xx" suffix where "xx" is an ISO 639-1
language code (e.g., "ko" for Korean), which targets the same GitHub address to the
original project.

Then configure the main project in readthedocs.org to have the new project as a
specific language translation.
Each readthedocs.org project should have the same set of active/public branch builds
to be consistent.

Example:

* https://readthedocs.org/projects/backendai-client-sdk-for-python
* https://readthedocs.org/projects/backendai-client-sdk-for-python-ko

Please ask the documentation maintainers for help.


### How to update the translation maps when the English version is updated

Update the po message templates (generating/updating `.po` files):
```console
$ make gettext
$ sphinx-intl update -p _build/gettext -l xx
```


### How to write translations

Edit the po messages (editing `.po` files):
```console
$ edit locales/xx/LC_MESSAGES/...
```

`git push` here to let readthedocs update the online docs.

Rebuild the compiled po message (compiling `.po` into `.mo` files) and preview the local build:
```console
$ sphinx-intl build
$ make -e SPHINXOPTS="-D language='xx'" html
$ open _build/html/index.html
```
