resolves #NNN (BA-MMM)
<!-- replace NNN, MMM with the GitHub issue number and the corresponding Jira issue number. -->

<!--
Describe precisely, concisely and concretely what this PR changes, the rationale behind the code,
and how it affects users and other developers.
-->

**Checklist:** (if applicable)

- [ ] Backport targets: a `fix:` PR goes to every version in `.github/maintained-versions.yml` automatically.
      A `Backport:` line here names the targets instead: some of them, other ones, or `none`.
- [ ] Mention the original issue
- [ ] Installer updates including:
  - Fixtures for db schema changes
  - New mandatory config options
- [ ] Update of end-to-end CLI integration tests in `ai.backend.test`
- [ ] API server-client counterparts (for example, manager API → client SDK)
- [ ] Test case(s) to:
  - Demonstrate the difference of before and after
  - Demonstrate the flow of abstract and conceptual models with a concrete implementation
- [ ] Documentation
  - Contents in the `docs` directory
  - docstrings in public interfaces and type annotations
