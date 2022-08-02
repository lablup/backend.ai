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
