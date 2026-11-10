# Writing changelogs

## Most microscopic: Commit messages

When writing commit messages, we use [the conventional commit style](https://www.conventionalcommits.org/en/v1.0.0/) and describe "what I did".
Note that we not only use the 'meaning of action' prefixes such as `fix:`, `feat:` but also the 'area of change' prefixes such as `ci:`, `repo:`, `setup:`, etc.
Optionally you may include a parenthesized mention on the primarily changed component like `fix(install-dev):`, `refactor(client.cli):`, etc.
When mentioning component names, use the Python module name or the file name without its extension.

A commit message may contain multiple lines of detailed description on individual code changes and any related background contexts in either list items or just a bunch of plain text paragraphs.
When squash-merging a PR, maintainers should revise the commit message auto-generated as a mere concatenation of all commit messages in the way that it highlights significant changes and technical details without noise.

The target audience is the code reviewers and future developers who dig in the history and background of code lines.

Please refer the commit histories of several PRs as standard examples:
* [lablup/backend.ai#501](https://github.com/lablup/backend.ai/pull/501/commits)
* [lablup/backend.ai#480](https://github.com/lablup/backend.ai/pull/480/commits)

Please refer the commit message of squash-merged PRs as standard examples:
* [76f933ac2a3a (#605)](https://github.com/lablup/backend.ai/commit/76f933ac2a3a64fce03c9b185fcd14c350b11816)

## In the middle: News fragments

The changelog (aka news fragment) is different.
It is automatically included in the release notes via [towncrier](https://github.com/twisted/towncrier) and include a collective summary of an entire pull request (i.e., "sum" and "summary" of the commit messages).
It should focus on "what the problem this PR resolves" and "how it affects the target audience".

The target audience is the users and/or fellow developers.

A news fragment should be a single-line single English sentence, either as an imperative (aka "commanding") form with no subjective (e.g., "Fix XXX bug", "Support YYY feature") or a complete sentence with a full subjective, verb, and objectives (e.g., "Now it does ZZZ").
There are a few exceptions historically, but it is always recommended to keep multi-line details in the commit message of the squash-merge commit and/or in the pull request body.

[Please refer the existing release notes as standard examples.](https://github.com/lablup/backend.ai/releases)

Note: maintainers may modify the news fragment without notice before merge.

### Filename convention

News fragments live in `changes/`. `<type>` is one of the `directory` values of the `[[tool.towncrier.type]]` entries in `pyproject.toml` (`fix`, `feature`, `breaking`, `misc` and so on). Two names are allowed:

| Name | Status | Made by |
|---|---|---|
| `<YYYYMMDD>-<HHMMSS>-<6 lowercase letters or digits>.<type>.md` | Recommended. Goes into the same push as the code, before the pull request exists | `python3 scripts/new-changelog.py <type> "<sentence>" [--issue <key>] [--epic <key>]`, which prints the path |
| `<PR-number>.<type>.md` | Previous convention, still accepted. Only possible after the pull request exists | By hand |

A fragment with the new name starts with front matter when it has an issue key:

```markdown
---
issue: BA-1234
epic: BA-1200
---
Fix the session cleanup race when an agent disconnects
```

- `issue` and `epic` are each optional. A value is a Jira key (`BA-N`) or a hejo key (`BAI-N`). Without either, the file holds only the sentence
- With `epic`, `changes/epics/<epic>.md` must exist
- The number in `<PR-number>.<type>.md` is the **pull request number**, not an issue number, a Jira key or any other identifier
- Backport PRs keep the original fragment name, so release notes link back to the original change

#### Epic files

Each epic has a pair: `changes/epics/<epic key>.md` (English) and `<epic key>.ko.md` (Korean).

```markdown
---
title: Session groups for spread and concentrate placement
---
Sessions can now be grouped so the scheduler places them together or apart.
```

- `title` is the epic's heading in the release notes, the body a 1-2 sentence summary for users
- The first PR of the epic's issues that finds no epic file creates it. The PR that closes the epic deletes it
- A release does not consume epic files

#### Checks and release

- CI checks the names, types, front matter and epic file pairs with `scripts/validate-changelog-fragments.py`
- Before running towncrier, `scripts/release.sh` renames each new-style fragment to `<PR-number>.<type>.md` with `git mv` and drops its front matter (`scripts/rename-changelog-fragments.py`)
  - The PR number is the first `(#N)` in the subject of the first-parent commit that added the file. A backport commit `... (#N) (#M)` gives the original PR number `N`
  - When `<PR-number>.<type>.md` already exists, the name takes towncrier's counter: `<PR-number>.<type>.1.md`, `.2.md`
  - A file that breaks these rules, or a fragment without `(#N)`, stops the release before anything is renamed

## In the middle: Pull request titles

The title of a pull request is a *conventional commit stylization of the news fragment*, usually as a shorter and more brief version, because it will **become a commit message in the main branch**.

Since a single pull request may contain multiple different commit message prefixes (e.g., `fix:`, `feat:`, `doc:`, ...), it should take the prefix from the most significant and meaningful commit, or the overall intention and purpose of the PR.
When the pull request is about a high-level (user-perceived) change and its change cross multiple component boundaries (e.g., it has multiple commits with different component names), it is better to omit the component name in the prefix or take the common ancestor name of the package hierarchy.
For example, when changed both `client.func` and `client.cli` with the same significance, you could mention `client` as the component name.

[Please refer the PR list as standard examples.](https://github.com/lablup/backend.ai/pulls)

Note: maintainers may modify the PR title without notice during reviews.

## Most macroscopic: Release highlights

The release highlights included in our news letters and the technical blog have more abstract and high-level user-centric descriptions.
We write a release highlight based on the release notes, which is based on news fragments, and which is based on commit messages.

The target audience is end-users, potential and current customers, decision makers &amp; IT administrators of them, conference booth participants, and so on, where their backgrounds may not be technical.

Please refer the our blogs as standard examples (in Korean):
* [2022년 7월 업데이트](https://blog.lablup.com/posts/2022/07/29/backend.ai-202207-update)
* [2022년 5월 업데이트](https://blog.lablup.com/posts/2022/05/31/backend.ai-202205-update)
* [2022년 3월 업데이트](https://blog.lablup.com/posts/2022/03/31/backend.ai-22.03-updates)
