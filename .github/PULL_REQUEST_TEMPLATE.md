<!--
Please precisely, concisely, and concretely describe what this PR changes, the rationale behind codes,
and how it affects the users and other developers.
-->

**Checklist:** (if applicable)

- [ ] Milestone metadata specifying the target backport version
- [ ] Mention to the original issue
- [ ] Installer updates including:
  - Fixtures for db schema changes
  - New mandatory config options
- [ ] Update of end-to-end CLI integration tests in `ai.backend.test`
- [ ] API server-client counterparts (e.g., manager API -> client SDK)
- [ ] Test case(s) to:
  - Demonstrate the difference of before/after
  - Demonstrate the flow of abstract/conceptual models with a concrete implementation
- [ ] Documentation
  - Contents in the `docs` directory
  - docstrings in public interfaces and type annotations
