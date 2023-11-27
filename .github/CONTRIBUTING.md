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

Before you make a contribution, ensure that which branch is the target you want to
contribute to.
Please take a look at [our versioning scheme
document](https://docs.backend.ai/en/latest/dev/version-management-and-upgrades.html#version-numbering)
to understand how we name branches and tags.
In short, we use "X.Y" in branch names for major releases, and "X.Y.Z" in tag names
for minor patch releases.
The master branch is for main development and it's the default recommended branch to
make a feature branch.

Our branch naming lies between
[GitFlow](https://danielkummer.github.io/git-flow-cheatsheet/index.html)
(we use `feature/`, `hotfix/`, `maintenance/` prefixed branch names) and
[GitHub Flow](https://guides.github.com/introduction/flow/).
We don't use a separate "develop" branch and just use PRs to take advantages
from both without complication that hurts agility.


Issue Management
----------------

The recommended place to make issues is [the meta repository](https://github.com/lablup/backend.ai).

We have two issue templates for bug reports and feature requests, but they are just guidelines.
It is not mandatory to use the templates, but please try to provide self-sufficient
information to track down your problems and/or ideas.
It is the best to provide concrete steps or a self-contained code example to reproduce
any problems.


Pull Requests
-------------

For those who have "write" access to the repositories, create a feature branch inside
the original repository to begin work with.  Otherwise, fork and create a feature
branch in your GitHub account.
The branch name should be prefixed with "feature/" and the rest should be hyphenated
slugs (words and numbers).  You may append the related issue number ("#xxx"), but
please include the issue number in the pull request's description instead, to avoid
potential misbehavior of shell commands and tools which may treat "#" as the comment
syntax.

Since Backend.AI consists of many sub-projects in separate GitHub repositories,
it is often required to make multiple PRs to multiple repositories to resolve a
single issue.
To get an integrated view, we recommend to pile an issue in the meta repository and
mention it like `refs lablup/backend.ai#xxx` in all related pull requests in
individual sub-projects.

Please keep the followings:

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
