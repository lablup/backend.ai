# Testing guidelines — Contexts

> For the rules, see `AGENTS.md` in this directory. For the workflow, patterns, and code examples, see the `/tdd-guide` skill.

## Rationale for the strategy distinction (real DB vs mocked)

- Repository/Model is an integration point where actual behavior matters, so it is verified with a real DB.
- For the other layers, logic verification is the key, so isolation improves speed and clarity.

## "Behavior, not implementation" — examples of what NOT to do

- Asserting on internal call wiring: spying on whether `savepoint()` calls `session.begin_nested()`, whether `write_ops()` opens a particular session method, or which delegation function was called — these break on harmless refactors and verify things callers do not actually depend on.
- Re-asserting delegation logic already verified by a lower layer's own tests (e.g., a thin wrapper forwarding to an already-tested `execute_*`).

## Running tests

```bash
pants test tests/manager::                                   # whole directory
pants test tests/manager/repositories/test_fair_share.py     # specific file
```

Leave the scope of change impact to CI, and locally target the directly related tests
(avoid broad `--changed-dependents=transitive` sweeps).
